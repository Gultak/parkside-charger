#include "parkside_charger.h"

#include <algorithm>
#include <cmath>

#include "esphome/core/hal.h"
#include "esphome/core/helpers.h"
#include "esphome/core/log.h"

namespace esphome {
namespace parkside_charger {

static const char *const TAG = "parkside_charger";

static const uint16_t CFG_SUSPEND = 1 << 5;
static const uint16_t CFG_RUN_BSR = 1 << 4;
static const uint16_t CFG_FORCE_TELEMETRY = 1 << 2;
static const uint16_t CCFG_EN_C_OVER_X_TERM = 1 << 2;
static const uint16_t CCFG_EN_JEITA = 1 << 0;

static const float SETTLE_S = 10.0f;            // wait after insertion before acting
static const float PUBLISH_INTERVAL_S = 15.0f;  // sensor publish rate (control loop runs faster)

// ============================================================================
// Slot
// ============================================================================

bool ParksideSlot::read16_(uint8_t reg, uint16_t &val) {
  uint8_t b[2];
  if (this->read_register(reg, b, 2) != i2c::ERROR_OK)
    return false;
  val = uint16_t(b[0]) | (uint16_t(b[1]) << 8);
  return true;
}

bool ParksideSlot::write16_(uint8_t reg, uint16_t val) {
  uint8_t b[2] = {uint8_t(val & 0xFF), uint8_t(val >> 8)};
  return this->write_register(reg, b, 2) == i2c::ERROR_OK;
}

void ParksideSlot::setup() {
  this->set_led_(false, false, false);
  if (this->bleed_out_ != nullptr)
    this->bleed_out_->turn_off();
  this->chip_ok_ = this->configure_chip_();
  this->last_config_ms_ = millis();
  if (!this->chip_ok_)
    ESP_LOGW(TAG, "Slot %u: LTC4162 not responding (board missing?) - will keep retrying", this->slot_number_);
}

bool ParksideSlot::configure_chip_() {
  uint16_t cc;
  if (!this->read16_(REG_CHEM_CELLS, cc))
    return false;
  uint8_t cells = cc & 0x0F;
  uint8_t chem = (cc >> 8) & 0x0F;
  // cell_count reads 0 ("unknown") whenever the charger is not enabled, e.g. without
  // input power or while suspended (datasheet: CHEM_CELLS_REG) - only check real values.
  if (cells != 0 && cells != this->cells_) {
    this->fault_text_ = str_sprintf("CELLS pins strap %u cells, expected %u", cells, this->cells_);
    ESP_LOGE(TAG, "Slot %u: %s - charging blocked", this->slot_number_, this->fault_text_.c_str());
    this->phase_ = Phase::FAULT;
  }
  // chem 0 = LTC4162_LAD (adjustable LTC4162-L); 1..3 = fixed 4.2/4.1/4.0 V Li-ion
  // versions; 4+ = LiFePO4 / lead-acid variants which must never charge a Li-ion pack.
  if (chem > 3) {
    this->fault_text_ = str_sprintf("wrong charger IC variant (chem=%u, need LTC4162-L)", chem);
    ESP_LOGE(TAG, "Slot %u: %s - charging blocked", this->slot_number_, this->fault_text_.c_str());
    this->phase_ = Phase::FAULT;
  } else if (chem != 0) {
    ESP_LOGW(TAG, "Slot %u: fixed-voltage LTC4162-L variant (chem=%u); use the adjustable LTC4162-LAD for "
             "storage/ready levels", this->slot_number_, chem);
  }
  ESP_LOGV(TAG, "Slot %u: chem=%u cells=%u", this->slot_number_, chem, cells);

  bool ok = true;
  // Input current limit: (n+1) * 500 uV / RSNSI
  int n_iin = (int) lroundf(this->iin_limit_ * this->rsnsi_ / 500e-6f) - 1;
  ok &= this->write16_(REG_IIN_LIMIT_TARGET, (uint16_t) clamp(n_iin, 0, 63));
  // Termination current: C/20 of the nominal capacity, at least 100 mA
  float cap = this->nominal_capacity_();
  float i_term = std::max(0.1f, 0.05f * (cap > 0 ? cap : 2.0f));
  ok &= this->write16_(REG_C_OVER_X_THRESHOLD, (uint16_t) (i_term * this->rsnsb_ / 1.466e-6f));
  // Terminate on C/x (not only on the CV timer) - except during a balancing tail, where
  // the firmware ends the charge itself; keep JEITA temperature control on
  ok &= this->set_cx_termination_(!this->balancing_);
  // Suspend state as we believe it should be, telemetry always on
  uint16_t cfg;
  ok &= this->read16_(REG_CONFIG_BITS, cfg);
  if (ok) {
    cfg |= CFG_FORCE_TELEMETRY;
    cfg = this->suspended_ ? (cfg | CFG_SUSPEND) : (cfg & ~CFG_SUSPEND);
    cfg &= ~CFG_RUN_BSR;
    ok &= this->write16_(REG_CONFIG_BITS, cfg);
  }
  // restore the V/I targets (registers are lost if the chip lost power)
  if (ok && this->programmed_vcell_ > 0)
    ok &= this->program_charge_(this->programmed_vcell_, this->programmed_current_);
  return ok;
}

bool ParksideSlot::set_suspended_(bool suspend) {
  uint16_t cfg;
  if (!this->read16_(REG_CONFIG_BITS, cfg))
    return false;
  cfg |= CFG_FORCE_TELEMETRY;
  cfg = suspend ? (cfg | CFG_SUSPEND) : (cfg & ~CFG_SUSPEND);
  cfg &= ~CFG_RUN_BSR;
  if (!this->write16_(REG_CONFIG_BITS, cfg))
    return false;
  this->suspended_ = suspend;
  return true;
}

bool ParksideSlot::program_charge_(float v_cell, float amps) {
  int nv = clamp((int) lroundf((v_cell - 3.8125f) / 0.0125f), 0, 31);
  int ni = clamp((int) lroundf(amps * this->rsnsb_ / 0.001f) - 1, 0, 31);
  bool ok = this->write16_(REG_VCHARGE_SETTING, nv) && this->write16_(REG_CHARGE_CURRENT_SETTING, ni);
  if (ok) {
    this->programmed_vcell_ = 3.8125f + nv * 0.0125f;
    this->programmed_current_ = (ni + 1) * 0.001f / this->rsnsb_;
    ESP_LOGV(TAG, "Slot %u: target %.4f V/cell, %.1f A", this->slot_number_, this->programmed_vcell_,
             this->programmed_current_);
  }
  return ok;
}

SlotMode ParksideSlot::mode_() const {
  if (this->mode_select_ == nullptr)
    return SlotMode::AUTO;
  auto idx = this->mode_select_->active_index();
  if (!idx.has_value() || *idx > (size_t) SlotMode::OFF)
    return SlotMode::AUTO;
  return (SlotMode) *idx;
}

float ParksideSlot::target_cell_voltage_() const {
  SlotMode m = this->mode_();
  if (m == SlotMode::OFF)
    return NAN;
  if (this->full_override_ || this->balance_due_)
    return V_FULL;
  switch (m) {
    case SlotMode::STORAGE:
      return V_STORAGE;
    case SlotMode::READY:
      return V_READY;
    case SlotMode::FULL:
      return V_FULL;
    default: {  // AUTO: ready, drop to storage when untouched for N days
      float days = this->charger_ != nullptr ? this->charger_->storage_after_days() : 14.0f;
      if (days > 0 && this->session_s_ > days * 86400.0f)
        return V_STORAGE;
      return V_READY;
    }
  }
}

float ParksideSlot::max_current_() const {
  float a = this->default_max_current_;
  if (this->max_current_number_ != nullptr && this->max_current_number_->has_state())
    a = this->max_current_number_->state;
  float cap = this->nominal_capacity_();
  if (cap > 0)
    a = std::min(a, cap * 1.0f);  // never above 1C
  return clamp(a, 0.1f, 0.032f / this->rsnsb_);
}

float ParksideSlot::nominal_capacity_() const {
  if (this->nominal_capacity_number_ != nullptr && this->nominal_capacity_number_->has_state())
    return this->nominal_capacity_number_->state;
  return 0;
}

float ParksideSlot::pack_resistance_() const {
  if (!std::isnan(this->bsr_cell_))
    return this->bsr_cell_ * this->cells_;
  return 0.03f * this->cells_;  // conservative guess until measured
}

float ParksideSlot::priority() const {
  if (this->full_override_)
    return -1.0f;
  // lowest state of charge first
  return std::isnan(this->soc_start_) ? 50.0f : this->soc_start_;
}

// Typical rested open-circuit voltage of NMC/NCA 18650/21700 cells vs. SoC
float ParksideSlot::soc_from_ocv_(float v) {
  static const float tbl[][2] = {{3.00f, 0},  {3.45f, 5},  {3.55f, 10}, {3.62f, 20}, {3.67f, 30}, {3.72f, 40},
                                 {3.78f, 50}, {3.85f, 60}, {3.93f, 70}, {4.00f, 80}, {4.08f, 90}, {4.20f, 100}};
  const int n = sizeof(tbl) / sizeof(tbl[0]);
  if (v <= tbl[0][0])
    return 0;
  if (v >= tbl[n - 1][0])
    return 100;
  for (int i = 1; i < n; i++) {
    if (v < tbl[i][0]) {
      float f = (v - tbl[i - 1][0]) / (tbl[i][0] - tbl[i - 1][0]);
      return tbl[i - 1][1] + f * (tbl[i][1] - tbl[i - 1][1]);
    }
  }
  return 100;
}

void ParksideSlot::on_inserted_() {
  ESP_LOGI(TAG, "Slot %u: battery inserted", this->slot_number_);
  this->session_s_ = 0;
  this->rest_s_ = 0;
  this->charge_s_ = 0;
  this->full_override_ = false;
  this->balance_due_ = false;
  this->balancing_ = false;
  this->last_balance_s_ = 0;
  this->bsr_requested_ = false;
  this->bsr_pending_ = false;
  this->bsr_done_this_charge_ = false;
  this->was_done_ = false;
  this->charge_in_progress_ = false;
  this->bsr_cell_ = NAN;
  this->charged_ah_ = 0;
  this->charge_ah_ = 0;
  this->soc_start_ = NAN;
  this->soc_ = NAN;
  this->capacity_ah_ = NAN;
  this->sd_v0_ = NAN;
  this->sd_elapsed_s_ = 0;
  this->self_discharge_ = NAN;
  if (this->phase_ != Phase::FAULT || !this->static_fault_()) {
    this->phase_ = Phase::SETTLING;
    this->fault_text_.clear();
  }
  this->force_publish_ = true;
}

void ParksideSlot::on_removed_() {
  ESP_LOGI(TAG, "Slot %u: battery removed", this->slot_number_);
  this->set_suspended_(true);
  if (this->bleed_out_ != nullptr)
    this->bleed_out_->turn_off();
  this->bleeding_ = false;
  this->wants_power_ = false;
  this->allocation_ = 0;
  this->charge_in_progress_ = false;
  this->full_override_ = false;
  if (this->phase_ != Phase::FAULT || !this->static_fault_()) {
    this->phase_ = Phase::EMPTY;
    this->fault_text_.clear();
  }
  this->force_publish_ = true;
}

void ParksideSlot::start_charging_(float amps, float ocv_cell) {
  if (this->bleeding_ && this->bleed_out_ != nullptr)
    this->bleed_out_->turn_off();
  this->bleeding_ = false;
  if (!this->charge_in_progress_) {
    this->charge_in_progress_ = true;
    this->charge_s_ = 0;
    this->charge_ah_ = 0;
    this->bsr_done_this_charge_ = false;
    // starting SoC from the (current-free) pack voltage. A pack that was just used
    // reads a little low; the capacity estimate needs >= 30 % SoC swing anyway.
    this->soc_start_ = this->rest_s_ >= SETTLE_S - 2.5f ? soc_from_ocv_(ocv_cell) : NAN;
  }
  float target = this->target_cell_voltage_();
  if (this->program_charge_(target, amps) && this->set_suspended_(false)) {
    this->phase_ = Phase::CHARGING;
    this->sd_v0_ = NAN;
    ESP_LOGI(TAG, "Slot %u: charging to %.3f V/cell at %.1f A", this->slot_number_, target, amps);
  }
}

bool ParksideSlot::set_cx_termination_(bool on) {
  uint16_t ccfg;
  if (!this->read16_(REG_CHARGER_CONFIG_BITS, ccfg))
    return false;
  ccfg = on ? (ccfg | CCFG_EN_C_OVER_X_TERM) : (ccfg & ~CCFG_EN_C_OVER_X_TERM);
  return this->write16_(REG_CHARGER_CONFIG_BITS, ccfg | CCFG_EN_JEITA);
}

void ParksideSlot::stop_charging_(Phase next) {
  if (!this->suspended_)
    this->set_suspended_(true);
  if (this->balancing_) {
    this->set_cx_termination_(true);
    this->balancing_ = false;
  }
  if (this->bleeding_ && this->bleed_out_ != nullptr)
    this->bleed_out_->turn_off();
  this->bleeding_ = false;
  if (next != Phase::WAIT_POWER)
    this->charge_in_progress_ = false;
  this->phase_ = next;
}

void ParksideSlot::finish_charge_() {
  this->set_suspended_(true);
  if (this->balancing_ || this->programmed_vcell_ >= V_FULL - 0.001f) {
    if (this->balancing_)
      ESP_LOGI(TAG, "Slot %u: balancing charge complete", this->slot_number_);
    this->set_cx_termination_(true);
    this->balancing_ = false;
    this->balance_due_ = false;
    this->last_balance_s_ = this->session_s_;
  }
  this->phase_ = Phase::DONE;
  this->was_done_ = true;
  this->charge_in_progress_ = false;
  this->rest_s_ = 0;
  float v_end = this->programmed_vcell_;
  float soc_end = v_end >= 4.19f ? 100.0f : soc_from_ocv_(v_end);
  if (!std::isnan(this->soc_start_) && soc_end - this->soc_start_ >= 30.0f) {
    float cap = this->charge_ah_ / ((soc_end - this->soc_start_) / 100.0f);
    this->capacity_ah_ = std::isnan(this->capacity_ah_) ? cap : 0.5f * (this->capacity_ah_ + cap);
  }
  ESP_LOGI(TAG, "Slot %u: charge complete (%.2f Ah this charge)", this->slot_number_, this->charge_ah_);
}

void ParksideSlot::update() {
  uint32_t now = millis();
  float dt = this->last_update_ms_ == 0 ? 0.0f : (now - this->last_update_ms_) / 1000.0f;
  this->last_update_ms_ = now;
  this->led_blink_ = !this->led_blink_;

  // ---------- read the charger ----------
  uint16_t st = 0, cs = 0, vb = 0, vi = 0, ib = 0, ii = 0, dtemp = 0, th = 0, bsr = 0;
  bool ok = this->read16_(REG_CHARGER_STATE, st) && this->read16_(REG_CHARGE_STATUS, cs) &&
            this->read16_(REG_VBAT, vb) && this->read16_(REG_VIN, vi) && this->read16_(REG_IBAT, ib) &&
            this->read16_(REG_IIN, ii) && this->read16_(REG_DIE_TEMP, dtemp) &&
            this->read16_(REG_THERMISTOR_VOLTAGE, th) && this->read16_(REG_BSR, bsr);
  if (ok && (!this->chip_ok_ || now - this->last_config_ms_ > 60000)) {
    // (re)apply configuration: after hot-plug, chip power loss, or periodically
    ok = this->configure_chip_();
    this->last_config_ms_ = now;
  }
  if (!ok) {
    if (this->chip_ok_)
      ESP_LOGW(TAG, "Slot %u: lost contact with the charger board", this->slot_number_);
    this->chip_ok_ = false;
    this->phase_ = Phase::NO_BOARD;
    this->wants_power_ = false;
    this->allocation_ = 0;
    this->present_ = false;
    this->set_led_(this->led_blink_, false, false);
    this->publish_all_();
    return;
  }
  this->chip_ok_ = true;
  this->charger_state_ = st;
  this->charge_status_ = cs;
  this->vbat_ = vb * 192.4e-6f * this->cells_;
  this->vin_ = vi * 1.649e-3f;
  this->ibat_ = (int16_t) ib * 1.466e-6f / this->rsnsb_;
  this->iin_ = (int16_t) ii * 1.466e-6f / this->rsnsi_;
  this->die_temp_ = ((float) (int16_t) dtemp - 12010.0f) / 45.6f;
  this->input_power_w_ = std::max(0.0f, this->vin_ * this->iin_);

  this->batt_temp_ = NAN;
  if (th > 100 && th < 21000) {
    float r = this->ntc_rbias_ * th / (21829.0f - th);
    float t = 1.0f / (1.0f / 298.15f + logf(r / this->ntc_r25_) / this->ntc_beta_) - 273.15f;
    if (t > -30.0f && t < 90.0f)
      this->batt_temp_ = t;
  }

  // ---------- presence ----------
  bool present;
  if (this->presence_switch_ != nullptr && this->presence_switch_->has_state()) {
    present = this->presence_switch_->state;
  } else {
    // no switch: the pack's BMS pulling the ID line low, or a pack voltage
    bool bms_seen = this->bms_fault_ != nullptr && this->bms_fault_->has_state() && !this->bms_fault_->state;
    present = bms_seen || this->vbat_ > 8.0f;
  }
  if (present && !this->present_)
    this->on_inserted_();
  else if (!present && this->present_)
    this->on_removed_();
  this->present_ = present;

  if (!present) {
    if (this->phase_ != Phase::FAULT)
      this->phase_ = Phase::EMPTY;
    this->wants_power_ = false;
    this->allocation_ = 0;
    this->set_led_(false, false, false);
    this->publish_all_();
    return;
  }

  // ---------- bookkeeping ----------
  this->session_s_ += dt;
  if (this->balance_interval_days_ > 0 && !this->balance_due_ &&
      this->session_s_ - this->last_balance_s_ > this->balance_interval_days_ * 86400.0f) {
    this->balance_due_ = true;
    ESP_LOGI(TAG, "Slot %u: balancing charge due", this->slot_number_);
  }
  float i_bleed = this->bleeding_ ? this->vbat_ / this->bleed_r_ : 0.0f;
  bool resting = fabsf(this->ibat_) < 0.03f && !this->bleeding_;
  this->rest_s_ = resting ? this->rest_s_ + dt : 0.0f;
  float ocv_cell = (this->vbat_ - (this->ibat_ - i_bleed) * this->pack_resistance_()) / this->cells_;
  this->soc_ = soc_from_ocv_(ocv_cell);
  if (this->ibat_ > 0.02f) {
    float ah = this->ibat_ * dt / 3600.0f;
    this->charged_ah_ += ah;
    this->charge_ah_ += ah;
  }

  // internal-resistance (BSR) measurement result
  if (this->bsr_pending_) {
    uint16_t cfg = 0;
    bool busy = this->read16_(REG_CONFIG_BITS, cfg) && (cfg & CFG_RUN_BSR);
    if (!busy || this->session_s_ - this->bsr_trigger_s_ > 20.0f) {
      this->bsr_pending_ = false;
      if (bsr > 0) {
        this->bsr_cell_ = bsr * this->rsnsb_ / 500.0f;
        ESP_LOGI(TAG, "Slot %u: internal resistance %.0f mOhm (pack)", this->slot_number_,
                 this->bsr_cell_ * this->cells_ * 1000.0f);
        this->force_publish_ = true;
      }
    }
  }

  // ---------- control ----------
  float target = this->target_cell_voltage_();
  bool enabled = this->charger_ == nullptr || this->charger_->is_enabled();
  this->wants_power_ = false;
  this->requested_current_ = 0;
  const uint16_t fault_bits = CS_BAT_SHORT | CS_MAX_CHARGE_TIME_FAULT | CS_BAT_DETECT_FAILED;
  bool temp_bad;
  if (std::isnan(this->batt_temp_)) {
    temp_bad = false;
  } else if (this->phase_ == Phase::TEMP_PAUSE) {  // 2 K hysteresis
    temp_bad = this->batt_temp_ < this->t_min_ + 2.0f || this->batt_temp_ > this->t_max_ - 2.0f;
  } else {
    temp_bad = this->batt_temp_ < this->t_min_ || this->batt_temp_ > this->t_max_;
  }

  if (this->phase_ == Phase::FAULT) {
    // latched until the battery is removed
    if (!this->suspended_ || this->bleeding_)
      this->stop_charging_(Phase::FAULT);
  } else if (st & fault_bits) {
    this->fault_text_ = (st & CS_BAT_SHORT)               ? "battery short / deeply discharged"
                        : (st & CS_MAX_CHARGE_TIME_FAULT) ? "charge took too long"
                                                          : "battery detection failed";
    ESP_LOGW(TAG, "Slot %u: fault: %s", this->slot_number_, this->fault_text_.c_str());
    this->stop_charging_(Phase::FAULT);
  } else if (this->session_s_ < SETTLE_S) {
    this->stop_charging_(Phase::SETTLING);
  } else if (!enabled || std::isnan(target)) {
    this->stop_charging_(Phase::DISABLED);
  } else if (this->require_ntc_ && std::isnan(this->batt_temp_)) {
    this->stop_charging_(Phase::NO_NTC);
  } else if (this->bms_fault_ != nullptr && (!this->bms_fault_->has_state() || this->bms_fault_->state)) {
    // The Parkside charger only charges while the pack's BMS signals "OK" on its ID
    // contact; it releases the line on under-voltage (~2.6 V/cell) and other faults.
    this->stop_charging_(Phase::BMS_BLOCKED);
  } else if (temp_bad) {
    this->stop_charging_(Phase::TEMP_PAUSE);
  } else if (this->phase_ == Phase::CHARGING) {
    this->charge_s_ += dt;
    bool cv = this->charge_status_ & ST_CONSTANT_VOLTAGE;
    if (st & (CS_C_OVER_X_TERM | CS_TIMER_TERM)) {
      this->finish_charge_();
    } else if (this->charge_s_ > this->max_charge_hours_ * 3600.0f) {
      this->fault_text_ = "charge timeout - pack may be defective";
      this->stop_charging_(Phase::FAULT);
    } else if (ocv_cell > target + 0.02f && cv) {
      this->finish_charge_();  // target was lowered below the pack voltage
    } else if (this->balancing_ && this->tail_s_ >= this->balance_tail_s_) {
      this->finish_charge_();
    } else {
      this->wants_power_ = true;
      float imax = this->max_current_();
      // in CV phase the pack takes less than allowed: give the rest back to the pool
      this->requested_current_ = cv ? std::min(imax, std::max(0.1f, this->ibat_ + 0.3f)) : imax;
      // balancing tail: at 4.20 V/cell in CV, keep going at low current instead of
      // terminating at C/x, so the pack's balance bleeders can catch up
      if (cv && target >= V_FULL - 0.001f && this->balance_tail_s_ > 0) {
        if (!this->balancing_ && this->set_cx_termination_(false)) {
          this->balancing_ = true;
          this->tail_s_ = 0;
          ESP_LOGI(TAG, "Slot %u: balancing tail (%.0f min at <= %.1f A)", this->slot_number_,
                   this->balance_tail_s_ / 60.0f, this->balance_current_);
        }
        if (this->balancing_) {
          this->tail_s_ += dt;
          imax = std::min(imax, this->balance_current_);
          this->requested_current_ = std::min(this->requested_current_, imax);
        }
      }
      if (this->allocation_ < 0.1f) {
        this->stop_charging_(Phase::WAIT_POWER);
      } else if (fabsf(this->allocation_ - this->programmed_current_) > 0.05f ||
                 fabsf(target - this->programmed_vcell_) > 0.001f) {
        this->program_charge_(target, std::min(this->allocation_, imax));
      }
      // measure internal resistance once per charge, in CC phase with decent current
      bool want_bsr = this->bsr_requested_ || !this->bsr_done_this_charge_;
      if (want_bsr && !this->bsr_pending_ && this->charge_s_ > 120.0f && this->ibat_ > 0.4f &&
          (this->charge_status_ & ST_CONSTANT_CURRENT)) {
        uint16_t cfg;
        if (this->read16_(REG_CONFIG_BITS, cfg) && this->write16_(REG_CONFIG_BITS, cfg | CFG_RUN_BSR)) {
          this->bsr_pending_ = true;
          this->bsr_trigger_s_ = this->session_s_;
          this->bsr_requested_ = false;
          this->bsr_done_this_charge_ = true;
        }
      }
    }
  } else if (this->bleeding_) {
    if (ocv_cell <= target + 0.005f) {
      this->bleed_out_->turn_off();
      this->bleeding_ = false;
      this->rest_s_ = 0;
      this->phase_ = Phase::IDLE;
      ESP_LOGI(TAG, "Slot %u: reached storage voltage", this->slot_number_);
    } else {
      this->phase_ = Phase::BLEEDING;
    }
  } else {
    float hyst = this->was_done_ ? 0.040f : 0.015f;
    bool need_charge = ocv_cell < target - hyst;
    bool need_bleed = this->bleed_out_ != nullptr && ocv_cell > target + 0.05f && this->rest_s_ > 60.0f;
    if (need_charge) {
      if (this->vin_ < this->vbat_ + 1.5f) {
        this->stop_charging_(Phase::NO_INPUT);
      } else {
        this->wants_power_ = true;
        this->requested_current_ = this->max_current_();
        if (this->allocation_ >= 0.1f) {
          this->start_charging_(std::min(this->allocation_, this->requested_current_), ocv_cell);
        } else {
          this->phase_ = Phase::WAIT_POWER;
        }
      }
    } else if (need_bleed) {
      this->bleed_out_->turn_on();
      this->bleeding_ = true;
      this->phase_ = Phase::BLEEDING;
      this->sd_v0_ = NAN;
      ESP_LOGI(TAG, "Slot %u: discharging to %.2f V/cell", this->slot_number_, target);
    } else {
      this->phase_ = this->was_done_ ? Phase::DONE : Phase::IDLE;
    }
  }
  if (!this->wants_power_)
    this->allocation_ = 0;

  // ---------- self-discharge (only while truly resting) ----------
  if ((this->phase_ == Phase::DONE || this->phase_ == Phase::IDLE || this->phase_ == Phase::DISABLED) &&
      this->rest_s_ > 1800.0f) {
    if (std::isnan(this->sd_v0_)) {
      this->sd_v0_ = ocv_cell;
      this->sd_elapsed_s_ = 0;
    } else {
      this->sd_elapsed_s_ += dt;
      if (this->sd_elapsed_s_ >= 86400.0f)
        this->self_discharge_ =
            std::max(0.0f, (this->sd_v0_ - ocv_cell) * 1000.0f / (this->sd_elapsed_s_ / 86400.0f));
    }
  } else if (!resting) {
    this->sd_v0_ = NAN;
  }

  this->update_health_();

  // ---------- LED ----------
  switch (this->phase_) {
    case Phase::CHARGING:
      this->set_led_(true, true, false);  // yellow
      break;
    case Phase::WAIT_POWER:
      this->set_led_(this->led_blink_, this->led_blink_, false);  // yellow blinking
      break;
    case Phase::DONE:
    case Phase::IDLE:
      if (this->soc_ >= 80.0f)
        this->set_led_(false, true, false);  // green: ready to use
      else
        this->set_led_(false, false, true);  // blue: storage level
      break;
    case Phase::BLEEDING:
      this->set_led_(true, false, true);  // magenta
      break;
    case Phase::SETTLING:
    case Phase::DISABLED:
      this->set_led_(false, false, true);
      break;
    case Phase::TEMP_PAUSE:
    case Phase::NO_INPUT:
    case Phase::NO_NTC:
    case Phase::BMS_BLOCKED:
      this->set_led_(this->led_blink_, false, this->led_blink_);  // magenta blinking
      break;
    default:
      this->set_led_(this->led_blink_, false, false);  // red blinking
      break;
  }

  this->publish_all_();
}

void ParksideSlot::update_health_() {
  this->health_pct_ = NAN;
  float nominal = this->nominal_capacity_();
  if (nominal > 0 && !std::isnan(this->capacity_ah_))
    this->health_pct_ = std::min(120.0f, this->capacity_ah_ / nominal * 100.0f);

  if (this->phase_ == Phase::FAULT) {
    this->health_text_ = "Faulty: " + this->fault_text_;
    return;
  }
  int level = -1;  // -1 unknown, 0 good, 1 aged, 2 worn, 3 replace
  std::string why;
  // Internal resistance normalised to capacity (mOhm * Ah per cell group). Roughly
  // independent of 1P/2P and 18650/21700: new packs measure ~70-120 mOhm*Ah (DC,
  // incl. BMS, contacts and wiring). Heuristic thresholds - tune with your own packs.
  float cap = nominal > 0 ? nominal : this->capacity_ah_;
  if (!std::isnan(this->bsr_cell_) && !std::isnan(cap) && cap > 0) {
    float spec = this->bsr_cell_ * 1000.0f * cap;
    int l = spec < 140 ? 0 : spec < 200 ? 1 : spec < 300 ? 2 : 3;
    if (l > 0)
      why += " high resistance;";
    level = std::max(level, l);
  }
  if (!std::isnan(this->health_pct_)) {
    int l = this->health_pct_ >= 80 ? 0 : this->health_pct_ >= 70 ? 1 : this->health_pct_ >= 60 ? 2 : 3;
    if (l > 0)
      why += " reduced capacity;";
    level = std::max(level, l);
  }
  if (!std::isnan(this->self_discharge_)) {
    int l = this->self_discharge_ < 5 ? 0 : this->self_discharge_ < 15 ? 2 : 3;
    if (l > 0)
      why += " high self-discharge;";
    level = std::max(level, l);
  }
  static const char *const names[] = {"Good", "Aged", "Worn", "Replace"};
  if (level < 0) {
    this->health_text_ = "Unknown (measured during the next charge)";
  } else {
    this->health_text_ = names[level];
    if (!why.empty()) {
      why.pop_back();
      this->health_text_ += " -" + why;
    }
  }
}

void ParksideSlot::set_led_(bool r, bool g, bool b) {
  if (this->led_r_ != nullptr)
    this->led_r_->set_state(r);
  if (this->led_g_ != nullptr)
    this->led_g_->set_state(g);
  if (this->led_b_ != nullptr)
    this->led_b_->set_state(b);
}

const char *ParksideSlot::phase_str_(Phase p) {
  switch (p) {
    case Phase::NO_BOARD:
      return "No charger board";
    case Phase::EMPTY:
      return "Empty";
    case Phase::SETTLING:
      return "Battery detected";
    case Phase::IDLE:
      return "Idle";
    case Phase::WAIT_POWER:
      return "Waiting for power budget";
    case Phase::CHARGING:
      return "Charging";
    case Phase::DONE:
      return "Charged";
    case Phase::BLEEDING:
      return "Discharging to storage level";
    case Phase::TEMP_PAUSE:
      return "Paused: temperature";
    case Phase::NO_INPUT:
      return "No 24 V input";
    case Phase::NO_NTC:
      return "No thermistor reading";
    case Phase::BMS_BLOCKED:
      return "Pack BMS blocks charging";
    case Phase::FAULT:
      return "Fault";
    case Phase::DISABLED:
      return "Charging disabled";
  }
  return "?";
}

void ParksideSlot::publish_all_() {
  uint32_t now = millis();
  bool phase_changed = this->phase_ != this->published_phase_;
  if (!phase_changed && !this->force_publish_ && now - this->last_publish_ms_ < PUBLISH_INTERVAL_S * 1000.0f)
    return;
  this->last_publish_ms_ = now;
  this->force_publish_ = false;
  this->published_phase_ = this->phase_;

  bool p = this->present_;
  if (this->present_bs_ != nullptr)
    this->present_bs_->publish_state(p);
  if (this->status_ts_ != nullptr) {
    std::string s = phase_str_(this->phase_);
    if (this->phase_ == Phase::FAULT && !this->fault_text_.empty())
      s += ": " + this->fault_text_;
    if (this->phase_ == Phase::CHARGING && this->balancing_)
      s = "Balancing cells";
    else if (this->phase_ == Phase::CHARGING && this->balance_due_ && !this->full_override_)
      s = "Balancing charge";
    float t = this->phase_ == Phase::CHARGING ? this->programmed_vcell_ : this->target_cell_voltage_();
    if ((this->phase_ == Phase::DONE || this->phase_ == Phase::IDLE) && !std::isnan(t))
      s = t <= V_STORAGE + 0.001f ? "Holding storage level" : t >= V_FULL - 0.001f ? "Full" : "Ready";
    if ((this->phase_ == Phase::CHARGING || this->phase_ == Phase::DONE || this->phase_ == Phase::IDLE ||
         this->phase_ == Phase::BLEEDING || this->phase_ == Phase::WAIT_POWER) &&
        !std::isnan(t) && t > 0)
      s += str_sprintf(" (target %.0f %%)", soc_from_ocv_(t));
    this->status_ts_->publish_state(s);
  }
  auto pub = [](sensor::Sensor *s, float v) {
    if (s != nullptr)
      s->publish_state(v);
  };
  pub(this->voltage_s_, p ? this->vbat_ : NAN);
  pub(this->current_s_, p ? std::max(0.0f, this->ibat_) : NAN);
  pub(this->input_power_s_, this->chip_ok_ ? this->input_power_w_ : NAN);
  pub(this->batt_temp_s_, p ? this->batt_temp_ : NAN);
  pub(this->die_temp_s_, this->chip_ok_ ? this->die_temp_ : NAN);
  pub(this->soc_s_, p ? this->soc_ : NAN);
  pub(this->ir_s_, p && !std::isnan(this->bsr_cell_) ? this->bsr_cell_ * this->cells_ * 1000.0f : NAN);
  pub(this->charged_ah_s_, p ? this->charged_ah_ : NAN);
  pub(this->capacity_s_, p ? this->capacity_ah_ : NAN);
  pub(this->health_s_, p ? this->health_pct_ : NAN);
  pub(this->self_discharge_s_, p ? this->self_discharge_ : NAN);
  if (this->health_ts_ != nullptr)
    this->health_ts_->publish_state(p ? this->health_text_ : std::string("No battery"));
}

void ParksideSlot::dump_config() {
  ESP_LOGCONFIG(TAG, "Parkside slot %u:", this->slot_number_);
  LOG_I2C_DEVICE(this);
  ESP_LOGCONFIG(TAG, "  Cells: %u, RSNSB: %.4f ohm, RSNSI: %.4f ohm", this->cells_, this->rsnsb_, this->rsnsi_);
  ESP_LOGCONFIG(TAG, "  Charge window: %.0f..%.0f degC, NTC required: %s", this->t_min_, this->t_max_,
                YESNO(this->require_ntc_));
  ESP_LOGCONFIG(TAG, "  Presence switch: %s, bleed resistor: %s, BMS input: %s",
                YESNO(this->presence_switch_ != nullptr), YESNO(this->bleed_out_ != nullptr),
                YESNO(this->bms_fault_ != nullptr));
  if (!this->chip_ok_)
    ESP_LOGCONFIG(TAG, "  LTC4162 not responding");
  LOG_UPDATE_INTERVAL(this);
}

// ============================================================================
// Hub
// ============================================================================

float ParksideCharger::storage_after_days() const {
  if (this->storage_after_days_number_ != nullptr && this->storage_after_days_number_->has_state())
    return this->storage_after_days_number_->state;
  return this->storage_after_days_;
}

void ParksideCharger::set_interlock(bool active, const std::string &reason) {
  this->interlock_reason_ = reason;
  if (active == this->interlock_)
    return;
  this->interlock_ = active;
  if (active) {
    ESP_LOGW(TAG, "Safety interlock: %s - charging stopped", reason.c_str());
    for (auto *s : this->slots_)
      s->set_allocation(0);
    if (this->enable_out_ != nullptr)
      this->enable_out_->turn_off();
  } else {
    ESP_LOGI(TAG, "Safety interlock released");
  }
}

void ParksideCharger::setup() {
  if (this->enable_out_ != nullptr)
    this->enable_out_->turn_on();
}

void ParksideCharger::update() {
  if (this->ambient_ != nullptr && this->ambient_->has_state() && !std::isnan(this->ambient_->state)) {
    float t = this->ambient_->state;
    if (!this->overtemp_ && t > this->max_ambient_) {
      ESP_LOGW(TAG, "Ambient %.1f degC above %.1f degC - charging stopped", t, this->max_ambient_);
      this->overtemp_ = true;
    } else if (this->overtemp_ && t < this->max_ambient_ - 3.0f) {
      this->overtemp_ = false;
    }
  }
  if (this->enable_out_ != nullptr)
    this->enable_out_->set_state(this->is_enabled());

  // ---- share the PSU budget: priority first (100 % requests, then emptiest) ----
  std::vector<ParksideSlot *> want;
  for (auto *s : this->slots_) {
    if (s->wants_power() && this->is_enabled())
      want.push_back(s);
    else
      s->set_allocation(0);
  }
  std::stable_sort(want.begin(), want.end(),
                   [](ParksideSlot *a, ParksideSlot *b) { return a->priority() < b->priority(); });
  float remaining = this->max_total_current_;
  for (auto *s : want) {
    float a = std::min(s->requested_current(), remaining);
    a = floorf(a * 10.0f + 0.001f) / 10.0f;  // LTC4162 has 100 mA steps with 10 mOhm sense
    // not worth starting a charge with a trickle - unless a trickle is all the slot asks
    // for (balancing tail)
    if (a < std::min(0.3f, s->requested_current() - 0.001f))
      a = 0;
    s->set_allocation(a);
    remaining -= a;
  }

  float power = 0;
  int charging = 0, present = 0;
  for (auto *s : this->slots_) {
    power += s->input_power();
    charging += s->is_charging();
    present += s->is_present();
  }
  if (this->total_power_s_ != nullptr)
    this->total_power_s_->publish_state(power);
  if (this->charging_s_ != nullptr)
    this->charging_s_->publish_state(charging);
  if (this->present_s_ != nullptr)
    this->present_s_->publish_state(present);
  if (this->status_ts_ != nullptr) {
    std::string s;
    if (this->interlock_)
      s = "Stopped: " + this->interlock_reason_;
    else if (this->overtemp_)
      s = "Stopped: enclosure too hot";
    else if (!this->enabled_)
      s = "Disabled";
    else if (charging > 0)
      s = str_sprintf("Charging %d of %d", charging, present);
    else
      s = str_sprintf("Idle, %d batteries", present);
    if (s != this->last_status_) {
      this->last_status_ = s;
      this->status_ts_->publish_state(s);
    }
  }
}

void ParksideCharger::dump_config() {
  ESP_LOGCONFIG(TAG, "Parkside charger hub:");
  ESP_LOGCONFIG(TAG, "  Slots: %u, max total charge current: %.1f A", (unsigned) this->slots_.size(),
                this->max_total_current_);
  ESP_LOGCONFIG(TAG, "  Max ambient: %.0f degC", this->max_ambient_);
  LOG_UPDATE_INTERVAL(this);
}

}  // namespace parkside_charger
}  // namespace esphome
