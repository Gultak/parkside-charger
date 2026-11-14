#pragma once
// Parkside X20V shelf charger: one LTC4162-L charger per slot (each on its own
// TCA9548A channel), coordinated by a hub that shares the PSU power budget.

#include <vector>

#include "esphome/core/component.h"
#include "esphome/components/i2c/i2c.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/text_sensor/text_sensor.h"
#include "esphome/components/output/binary_output.h"
#include "esphome/components/select/select.h"
#include "esphome/components/number/number.h"

namespace esphome {
namespace parkside_charger {

// ---- LTC4162-L register map (SMBus word access, little endian) ----
// Source: LTC4162-L datasheet / Linux driver ltc4162-l-charger.c.
static const uint8_t REG_CONFIG_BITS = 0x14;          // b5 suspend_charger, b4 run_bsr, b2 force_telemetry_on
static const uint8_t REG_IIN_LIMIT_TARGET = 0x15;     // (n+1) * 500uV / RSNSI
static const uint8_t REG_CHARGE_CURRENT_SETTING = 0x1A;  // (n+1) * 1mV / RSNSB, n = 0..31
static const uint8_t REG_VCHARGE_SETTING = 0x1B;      // 3.8125 V + n * 12.5 mV per cell, n = 0..31
static const uint8_t REG_C_OVER_X_THRESHOLD = 0x1C;   // in IBAT LSBs
static const uint8_t REG_CHARGER_CONFIG_BITS = 0x29;  // b2 en_c_over_x_term, b0 en_jeita
static const uint8_t REG_CHARGER_STATE = 0x34;
static const uint8_t REG_CHARGE_STATUS = 0x35;
static const uint8_t REG_VBAT = 0x3A;                 // 192.4 uV per cell
static const uint8_t REG_VIN = 0x3B;                  // 1.649 mV
static const uint8_t REG_IBAT = 0x3D;                 // signed, 1.466 uV / RSNSB
static const uint8_t REG_IIN = 0x3E;                  // signed, 1.466 uV / RSNSI
static const uint8_t REG_DIE_TEMP = 0x3F;             // (n - 12010) / 45.6 degC
static const uint8_t REG_THERMISTOR_VOLTAGE = 0x40;   // R_ntc = R_bias * n / (21829 - n)
static const uint8_t REG_BSR = 0x41;                  // per cell: n * RSNSB / 500 ohm
static const uint8_t REG_CHEM_CELLS = 0x43;           // b11..8 chem, b3..0 cell count (pin strapped)

// CHARGER_STATE bits
static const uint16_t CS_BAT_DETECT_FAILED = 1 << 12;
static const uint16_t CS_BATTERY_DETECTION = 1 << 11;
static const uint16_t CS_SUSPENDED = 1 << 8;
static const uint16_t CS_PRECHARGE = 1 << 7;
static const uint16_t CS_CC_CV = 1 << 6;
static const uint16_t CS_NTC_PAUSE = 1 << 5;
static const uint16_t CS_TIMER_TERM = 1 << 4;
static const uint16_t CS_C_OVER_X_TERM = 1 << 3;
static const uint16_t CS_MAX_CHARGE_TIME_FAULT = 1 << 2;
static const uint16_t CS_BAT_MISSING = 1 << 1;
static const uint16_t CS_BAT_SHORT = 1 << 0;
// CHARGE_STATUS bits
static const uint16_t ST_CONSTANT_VOLTAGE = 1 << 0;
static const uint16_t ST_CONSTANT_CURRENT = 1 << 1;

// Per-cell charge targets (V). Kept on the LTC4162-L's 12.5 mV grid.
static const float V_STORAGE = 3.850f;  // ~55-60 % SoC, best for long-term storage
static const float V_READY = 4.100f;    // ~90 %, good compromise for "always ready"
static const float V_FULL = 4.200f;     // 100 %

enum class SlotMode : uint8_t { AUTO = 0, STORAGE = 1, READY = 2, FULL = 3, OFF = 4 };

enum class Phase : uint8_t {
  NO_BOARD,     // slot board does not answer on I2C
  EMPTY,        // no battery
  SETTLING,     // battery just inserted, waiting for readings to settle
  IDLE,         // at/above target, resting
  WAIT_POWER,   // needs charge, waiting for a share of the power budget
  CHARGING,
  DONE,         // reached target, resting (recharges when it drops by the hysteresis)
  BLEEDING,     // discharging to storage voltage through the bleed resistor
  TEMP_PAUSE,   // battery too cold/hot
  NO_INPUT,     // 24 V bus missing
  NO_NTC,       // no thermistor reading but one is required
  FAULT,
  DISABLED,     // mode Off or charger disabled globally
};

class ParksideCharger;

class ParksideSlot : public PollingComponent, public i2c::I2CDevice {
 public:
  void setup() override;
  void update() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA; }

  // ---- configuration ----
  void set_charger(ParksideCharger *c) { this->charger_ = c; }
  void set_slot_number(uint8_t n) { this->slot_number_ = n; }
  void set_cells(uint8_t n) { this->cells_ = n; }
  void set_rsnsb(float r) { this->rsnsb_ = r; }
  void set_rsnsi(float r) { this->rsnsi_ = r; }
  void set_input_current_limit(float a) { this->iin_limit_ = a; }
  void set_ntc(float r25, float beta, float rbias) { this->ntc_r25_ = r25; this->ntc_beta_ = beta; this->ntc_rbias_ = rbias; }
  void set_require_ntc(bool b) { this->require_ntc_ = b; }
  void set_temperature_window(float lo, float hi) { this->t_min_ = lo; this->t_max_ = hi; }
  void set_max_charge_hours(float h) { this->max_charge_hours_ = h; }
  void set_default_max_current(float a) { this->default_max_current_ = a; }
  void set_bleed_resistance(float r) { this->bleed_r_ = r; }

  void set_presence_switch(binary_sensor::BinarySensor *b) { this->presence_switch_ = b; }
  void set_bleed_output(output::BinaryOutput *o) { this->bleed_out_ = o; }
  void set_led_outputs(output::BinaryOutput *r, output::BinaryOutput *g, output::BinaryOutput *b) {
    this->led_r_ = r; this->led_g_ = g; this->led_b_ = b;
  }
  void set_mode_select(select::Select *s) { this->mode_select_ = s; }
  void set_max_current_number(number::Number *n) { this->max_current_number_ = n; }
  void set_nominal_capacity_number(number::Number *n) { this->nominal_capacity_number_ = n; }

  void set_present_binary_sensor(binary_sensor::BinarySensor *s) { this->present_bs_ = s; }
  void set_status_text_sensor(text_sensor::TextSensor *s) { this->status_ts_ = s; }
  void set_health_text_sensor(text_sensor::TextSensor *s) { this->health_ts_ = s; }
  void set_battery_voltage_sensor(sensor::Sensor *s) { this->voltage_s_ = s; }
  void set_charge_current_sensor(sensor::Sensor *s) { this->current_s_ = s; }
  void set_input_power_sensor(sensor::Sensor *s) { this->input_power_s_ = s; }
  void set_battery_temperature_sensor(sensor::Sensor *s) { this->batt_temp_s_ = s; }
  void set_charger_temperature_sensor(sensor::Sensor *s) { this->die_temp_s_ = s; }
  void set_state_of_charge_sensor(sensor::Sensor *s) { this->soc_s_ = s; }
  void set_internal_resistance_sensor(sensor::Sensor *s) { this->ir_s_ = s; }
  void set_charged_capacity_sensor(sensor::Sensor *s) { this->charged_ah_s_ = s; }
  void set_capacity_estimate_sensor(sensor::Sensor *s) { this->capacity_s_ = s; }
  void set_health_sensor(sensor::Sensor *s) { this->health_s_ = s; }
  void set_self_discharge_sensor(sensor::Sensor *s) { this->self_discharge_s_ = s; }

  // ---- actions (call from lambdas / buttons) ----
  void request_full_charge() { this->full_override_ = true; }
  void request_resistance_measurement() { this->bsr_requested_ = true; }

  // ---- hub interface ----
  bool wants_power() const { return this->wants_power_; }
  float requested_current() const { return this->requested_current_; }
  float priority() const;  // lower value is served first
  void set_allocation(float amps) { this->allocation_ = amps; }
  float input_power() const { return this->input_power_w_; }
  bool is_present() const { return this->present_; }
  bool is_charging() const { return this->phase_ == Phase::CHARGING; }
  Phase phase() const { return this->phase_; }

 protected:
  bool read16_(uint8_t reg, uint16_t &val);
  bool write16_(uint8_t reg, uint16_t val);
  bool configure_chip_();
  bool set_suspended_(bool suspend);
  bool program_charge_(float v_cell, float amps);
  SlotMode mode_() const;
  float target_cell_voltage_() const;
  float max_current_() const;
  float nominal_capacity_() const;
  float pack_resistance_() const;
  void on_inserted_();
  void on_removed_();
  void start_charging_(float amps, float ocv_cell);
  void stop_charging_(Phase next);
  void finish_charge_();
  void update_health_();
  void set_led_(bool r, bool g, bool b);
  void publish_all_();
  static float soc_from_ocv_(float v_cell);
  static const char *phase_str_(Phase p);

  ParksideCharger *charger_{nullptr};
  uint8_t slot_number_{0};
  uint8_t cells_{5};
  float rsnsb_{0.010f};
  float rsnsi_{0.010f};
  float iin_limit_{3.0f};
  float ntc_r25_{10000.0f};
  float ntc_beta_{3435.0f};
  float ntc_rbias_{10000.0f};
  bool require_ntc_{true};
  float t_min_{5.0f};
  float t_max_{45.0f};
  float max_charge_hours_{10.0f};
  float default_max_current_{1.5f};
  float bleed_r_{200.0f};

  binary_sensor::BinarySensor *presence_switch_{nullptr};
  output::BinaryOutput *bleed_out_{nullptr};
  output::BinaryOutput *led_r_{nullptr}, *led_g_{nullptr}, *led_b_{nullptr};
  select::Select *mode_select_{nullptr};
  number::Number *max_current_number_{nullptr};
  number::Number *nominal_capacity_number_{nullptr};

  binary_sensor::BinarySensor *present_bs_{nullptr};
  text_sensor::TextSensor *status_ts_{nullptr}, *health_ts_{nullptr};
  sensor::Sensor *voltage_s_{nullptr}, *current_s_{nullptr}, *input_power_s_{nullptr}, *batt_temp_s_{nullptr},
      *die_temp_s_{nullptr}, *soc_s_{nullptr}, *ir_s_{nullptr}, *charged_ah_s_{nullptr}, *capacity_s_{nullptr},
      *health_s_{nullptr}, *self_discharge_s_{nullptr};

  // ---- live state ----
  Phase phase_{Phase::NO_BOARD};
  std::string fault_text_;
  bool chip_ok_{false};
  uint32_t last_update_ms_{0};
  uint32_t last_config_ms_{0};
  uint16_t charger_state_{0}, charge_status_{0};
  float vbat_{NAN}, ibat_{NAN}, vin_{NAN}, iin_{NAN}, die_temp_{NAN}, batt_temp_{NAN};
  float input_power_w_{0};
  bool present_{false};
  bool suspended_{true};
  bool led_blink_{false};

  // power-budget handshake
  bool wants_power_{false};
  float requested_current_{0};
  float allocation_{0};
  float programmed_current_{-1};
  float programmed_vcell_{-1};

  // session (per inserted battery)
  float session_s_{0};        // seconds since insertion
  float rest_s_{0};           // seconds without current flowing
  float charge_s_{0};         // seconds in the current charge
  bool full_override_{false};
  bool bsr_requested_{false};
  bool bsr_done_this_charge_{false};
  bool bsr_pending_{false};
  float bsr_trigger_s_{0};
  bool charge_in_progress_{false};
  bool bleeding_{false};
  float soc_{NAN};
  float health_pct_{NAN};
  std::string health_text_;
  bool force_publish_{true};
  Phase published_phase_{Phase::NO_BOARD};
  uint32_t last_publish_ms_{0};
  bool was_done_{false};      // reached target at least once this session
  float bsr_cell_{NAN};       // ohm per cell
  float charged_ah_{0};       // total this session
  float charge_ah_{0};        // this charge only
  float soc_start_{NAN};
  float capacity_ah_{NAN};
  float sd_v0_{NAN};          // self-discharge reference voltage (per cell)
  float sd_elapsed_s_{0};
  float self_discharge_{NAN}; // mV / day / cell
};

class ParksideCharger : public PollingComponent {
 public:
  void setup() override;
  void update() override;
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::DATA - 1.0f; }

  void register_slot(ParksideSlot *s) { this->slots_.push_back(s); }
  void set_max_total_current(float a) { this->max_total_current_ = a; }
  void set_enable_output(output::BinaryOutput *o) { this->enable_out_ = o; }
  void set_ambient_sensor(sensor::Sensor *s) { this->ambient_ = s; }
  void set_max_ambient(float t) { this->max_ambient_ = t; }
  void set_storage_after_days_number(number::Number *n) { this->storage_after_days_number_ = n; }
  void set_storage_after_days(float d) { this->storage_after_days_ = d; }
  void set_total_power_sensor(sensor::Sensor *s) { this->total_power_s_ = s; }
  void set_charging_count_sensor(sensor::Sensor *s) { this->charging_s_ = s; }
  void set_present_count_sensor(sensor::Sensor *s) { this->present_s_ = s; }
  void set_status_text_sensor(text_sensor::TextSensor *s) { this->status_ts_ = s; }

  // actions
  void set_enabled(bool e) { this->enabled_ = e; }
  void request_full_all() {
    for (auto *s : this->slots_)
      s->request_full_charge();
  }

  bool is_enabled() const { return this->enabled_ && !this->overtemp_; }
  float storage_after_days() const;

 protected:
  std::vector<ParksideSlot *> slots_;
  float max_total_current_{8.0f};
  output::BinaryOutput *enable_out_{nullptr};
  sensor::Sensor *ambient_{nullptr};
  float max_ambient_{45.0f};
  number::Number *storage_after_days_number_{nullptr};
  float storage_after_days_{14.0f};
  sensor::Sensor *total_power_s_{nullptr}, *charging_s_{nullptr}, *present_s_{nullptr};
  text_sensor::TextSensor *status_ts_{nullptr};
  bool enabled_{true};
  bool overtemp_{false};
  std::string last_status_;
};

}  // namespace parkside_charger
}  // namespace esphome
