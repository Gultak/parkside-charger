// Host simulation of the parkside_charger component: fake LTC4162-L + Li-ion pack model.
// Build: g++ -std=gnu++20 -O2 -Istubs -I../../components sim.cpp ../../components/parkside_charger/parkside_charger.cpp -o sim
#include <cassert>
#include <cmath>
#include <cstdio>
#include <memory>
#include <vector>
#include "parkside_charger/parkside_charger.h"

namespace esphome { uint32_t g_millis = 1; }
bool g_verbose = false;
double g_sim_hours = 0;
using namespace esphome;
using namespace esphome::parkside_charger;

static float ocv_cell(float soc) {  // slightly different curve than the firmware's table on purpose
  static const float t[][2] = {{0, 3.0f}, {5, 3.42f}, {10, 3.53f}, {20, 3.61f}, {30, 3.665f}, {40, 3.715f},
                               {50, 3.775f}, {60, 3.85f}, {70, 3.935f}, {80, 4.005f}, {90, 4.085f}, {100, 4.2f}};
  soc = std::fmin(100, std::fmax(0, soc));
  for (int i = 1; i < 12; i++)
    if (soc <= t[i][0]) return t[i - 1][1] + (soc - t[i - 1][0]) / (t[i][0] - t[i - 1][0]) * (t[i][1] - t[i - 1][1]);
  return 4.2f;
}

struct Pack { bool present = false; float cap = 4.0f, soc = 30, r_cell = 0.025f, temp = 22; };

struct FakeLTC : i2c::FakeBus {
  uint16_t reg[0x50] = {};
  Pack pack;
  float i = 0, vin = 24.5f;
  bool term = false, online = true;
  output::BinaryOutput *bleed = nullptr;
  int bsr_countdown = -1;
  FakeLTC() { reg[0x43] = 5; reg[0x14] = 1 << 5; reg[0x1C] = 682; reg[0x29] = 1; }
  float vpack() const { return pack.present ? (ocv_cell(pack.soc) * 5 + i * pack.r_cell * 5) : 0; }
  i2c::ErrorCode rd(uint8_t r, uint8_t *d, size_t) override {
    if (!online) return i2c::ERROR_NOT_ACKNOWLEDGED;
    uint16_t v = reg[r];
    bool susp = reg[0x14] & (1 << 5);
    switch (r) {
      case 0x3A: v = (uint16_t) (vpack() / 5 / 192.4e-6f); break;
      case 0x3B: v = (uint16_t) (vin / 1.649e-3f); break;
      case 0x3D: v = (uint16_t) (int16_t) (i * 0.01f / 1.466e-6f); break;
      case 0x3E: v = (uint16_t) (int16_t) (vpack() * i / 0.94f / vin * 0.01f / 1.466e-6f); break;
      case 0x3F: v = (uint16_t) (12010 + 35 * 45.6f); break;
      case 0x40: {
        if (!pack.present) { v = 21829; break; }
        float tk = pack.temp + 273.15f, rn = 10000 * expf(3435 * (1 / tk - 1 / 298.15f));
        v = (uint16_t) (21829 * rn / (rn + 10000)); break;
      }
      case 0x34: v = !pack.present ? (1 << 1) : susp ? (1 << 8) : term ? (1 << 3) : (1 << 6); break;
      case 0x35: {
        float iset = (reg[0x1A] + 1) * 0.1f;
        v = (!susp && i > 0) ? (i < iset - 0.05f ? 1 : 2) : 0; break;
      }
    }
    d[0] = v & 0xFF; d[1] = v >> 8;
    return i2c::ERROR_OK;
  }
  i2c::ErrorCode wr(uint8_t r, const uint8_t *d, size_t) override {
    if (!online) return i2c::ERROR_NOT_ACKNOWLEDGED;
    uint16_t v = d[0] | (d[1] << 8);
    if (r == 0x14) {
      if (v & (1 << 5)) term = false;  // suspend clears termination
      if (v & (1 << 4)) bsr_countdown = 3;
    }
    reg[r] = v;
    return i2c::ERROR_OK;
  }
  void step(float dt) {
    bool susp = reg[0x14] & (1 << 5);
    i = 0;
    if (pack.present && !susp && !term && vin > 20) {
      float vt = 3.8125f + reg[0x1B] * 0.0125f, iset = (reg[0x1A] + 1) * 0.1f;
      float icv = (vt - ocv_cell(pack.soc)) / pack.r_cell;
      i = std::fmax(0, std::fmin(iset, icv));
      float iterm = reg[0x1C] * 1.466e-6f / 0.01f;
      if (icv < iset && i < iterm) { term = true; i = 0; }
    }
    if (bsr_countdown >= 0 && --bsr_countdown < 0) {
      reg[0x41] = (uint16_t) (pack.r_cell * 500 / 0.01f);
      reg[0x14] &= ~(1 << 4);
    }
    if (pack.present) {
      float ib = (bleed && bleed->on) ? vpack() / 200.0f : 0;
      pack.soc += (i - ib) * dt / 3600 / pack.cap * 100;
      pack.soc -= 0.03f / 86400 * dt;  // ~1 %/month self-discharge
    }
  }
};

struct Rig {
  ParksideCharger hub;
  std::vector<std::unique_ptr<ParksideSlot>> slots;
  std::vector<std::unique_ptr<FakeLTC>> chips;
  std::vector<std::unique_ptr<binary_sensor::BinarySensor>> sw;
  std::vector<std::unique_ptr<output::BinaryOutput>> bleed;
  std::vector<std::unique_ptr<select::Select>> mode;
  std::vector<std::unique_ptr<number::Number>> imax, nominal;
  std::vector<std::unique_ptr<text_sensor::TextSensor>> status, health;
  std::vector<std::unique_ptr<sensor::Sensor>> ir, capest, soc, sd;
  number::Number days;
  Rig(int n, float budget) {
    hub.set_max_total_current(budget);
    days.state = 14;
    hub.set_storage_after_days_number(&days);
    for (int k = 0; k < n; k++) {
      auto s = std::make_unique<ParksideSlot>();
      chips.push_back(std::make_unique<FakeLTC>());
      sw.push_back(std::make_unique<binary_sensor::BinarySensor>());
      bleed.push_back(std::make_unique<output::BinaryOutput>());
      mode.push_back(std::make_unique<select::Select>());
      imax.push_back(std::make_unique<number::Number>());
      nominal.push_back(std::make_unique<number::Number>());
      status.push_back(std::make_unique<text_sensor::TextSensor>());
      health.push_back(std::make_unique<text_sensor::TextSensor>());
      ir.push_back(std::make_unique<sensor::Sensor>());
      capest.push_back(std::make_unique<sensor::Sensor>());
      soc.push_back(std::make_unique<sensor::Sensor>());
      sd.push_back(std::make_unique<sensor::Sensor>());
      imax[k]->state = 1.5f;
      nominal[k]->state = 4.0f;
      chips[k]->bleed = bleed[k].get();
      s->set_fake_bus(chips[k].get());
      s->set_slot_number(k + 1);
      s->set_charger(&hub);
      s->set_presence_switch(sw[k].get());
      s->set_bleed_output(bleed[k].get());
      s->set_mode_select(mode[k].get());
      s->set_max_current_number(imax[k].get());
      s->set_nominal_capacity_number(nominal[k].get());
      s->set_status_text_sensor(status[k].get());
      s->set_health_text_sensor(health[k].get());
      s->set_internal_resistance_sensor(ir[k].get());
      s->set_capacity_estimate_sensor(capest[k].get());
      s->set_state_of_charge_sensor(soc[k].get());
      s->set_self_discharge_sensor(sd[k].get());
      hub.register_slot(s.get());
      slots.push_back(std::move(s));
    }
    for (auto &s : slots) s->setup();
    hub.setup();
  }
  void insert(int k, float soc_, float cap = 4.0f, float r = 0.025f, float temp = 22) {
    chips[k]->pack = {true, cap, soc_, r, temp};
    sw[k]->publish_state(true);
  }
  void remove(int k) { chips[k]->pack.present = false; sw[k]->publish_state(false); }
  int charging() { int c = 0; for (auto &s : slots) c += s->is_charging(); return c; }
  float total_i() { float t = 0; for (auto &c : chips) t += c->i; return t; }
  float max_total_seen = 0;
  void run(double hours) {
    long steps = (long) (hours * 3600 / 2);
    for (long n = 0; n < steps; n++) {
      g_millis += 2000;
      g_sim_hours += 2.0 / 3600;
      for (auto &c : chips) c->step(2);
      for (auto &s : slots) s->update();
      hub.update();
      max_total_seen = std::fmax(max_total_seen, total_i());
    }
  }
};

#define CHECK(cond, ...) do { if (cond) printf("  PASS  " __VA_ARGS__); else { printf("  FAIL  " __VA_ARGS__); fails++; } printf("\n"); } while (0)

int main(int argc, char **argv) {
  g_verbose = argc > 1;
  int fails = 0;

  printf("Scenario 1: 4 Ah pack at 30 %% in Auto -> Ready (4.10 V/cell)\n");
  {
    Rig r(1, 8);
    r.insert(0, 30);
    r.run(0.0017);
    CHECK(r.slots[0]->phase() == Phase::SETTLING, "settles after insertion (%s)", r.status[0]->state.c_str());
    r.run(0.1);
    CHECK(r.slots[0]->is_charging(), "starts charging at %.2f A", r.chips[0]->i);
    r.run(4);
    CHECK(r.slots[0]->phase() == Phase::DONE, "done: %s", r.status[0]->state.c_str());
    float v = ocv_cell(r.chips[0]->pack.soc);
    CHECK(v > 4.05f && v < 4.11f, "rested cell voltage %.3f V (SoC %.0f %%)", v, r.chips[0]->pack.soc);
    CHECK(fabsf(r.ir[0]->state - 125) < 5, "internal resistance %.0f mOhm (expected 125)", r.ir[0]->state);
    CHECK(fabsf(r.capest[0]->state - 4.0f) < 0.5f, "capacity estimate %.2f Ah (true 4.0)", r.capest[0]->state);
    printf("        health: %s\n", r.health[0]->state.c_str());

    printf("Scenario 2: untouched 15 days in Auto -> bleeds down to storage\n");
    r.run(15 * 24 + 12);
    float vc = ocv_cell(r.chips[0]->pack.soc);
    CHECK(vc < 3.87f && vc > 3.80f, "cell voltage %.3f V after storage drop (%s)", vc, r.status[0]->state.c_str());
    CHECK(!r.bleed[0]->on, "bleed resistor off again");
    CHECK(!std::isnan(r.sd[0]->state), "self-discharge measured: %.2f mV/day", r.sd[0]->state);

    printf("Scenario 3: 'charge to 100%%' button\n");
    r.slots[0]->request_full_charge();
    r.run(5);
    float vf = ocv_cell(r.chips[0]->pack.soc);
    CHECK(vf > 4.17f, "cell voltage %.3f V (%s)", vf, r.status[0]->state.c_str());
    r.remove(0);
    r.run(0.01);
    CHECK(r.slots[0]->phase() == Phase::EMPTY, "removed -> %s", r.status[0]->state.c_str());
  }

  printf("Scenario 4: 10 empty packs, 8 A budget, 1.5 A each\n");
  {
    Rig r(10, 8);
    for (int k = 0; k < 10; k++) r.insert(k, 5 + k * 2);
    r.run(0.2);
    CHECK(r.charging() >= 5 && r.total_i() <= 8.01f, "%d slots charging at once, %.1f A total (5 x 1.5 A + remainder)",
          r.charging(), r.total_i());
    r.run(20);
    int done = 0;
    for (auto &s : r.slots) done += s->phase() == Phase::DONE;
    CHECK(done == 10, "%d/10 done after ~20 h", done);
    CHECK(r.max_total_seen <= 8.05f, "peak total charge current %.2f A <= 8 A", r.max_total_seen);
  }

  printf("Scenario 5: protections\n");
  {
    Rig r(3, 8);
    r.insert(0, 30, 4, 0.025f, 52);  // hot pack straight from the grinder
    r.chips[1]->online = false;      // slot board missing
    r.insert(2, 30);
    r.mode[2]->idx = (size_t) SlotMode::OFF;
    r.run(0.1);
    CHECK(r.slots[0]->phase() == Phase::TEMP_PAUSE, "hot pack: %s", r.status[0]->state.c_str());
    CHECK(r.slots[1]->phase() == Phase::NO_BOARD, "missing board: %s", r.slots[1]->phase() == Phase::NO_BOARD ? "No charger board" : "?");
    CHECK(r.slots[2]->phase() == Phase::DISABLED, "mode Off: %s", r.status[2]->state.c_str());
    r.chips[0]->pack.temp = 30;
    r.run(0.1);
    CHECK(r.slots[0]->is_charging(), "cooled down -> charging");
    r.hub.set_enabled(false);
    r.run(0.01);
    CHECK(r.charging() == 0, "global disable stops all");
    r.hub.set_enabled(true);
    r.chips[1]->online = true;
    r.insert(1, 50, 2.0f, 0.12f);  // old, worn 2 Ah pack
    r.nominal[1]->state = 2.0f;
    r.run(6);
    CHECK(r.health[1]->state.rfind("Worn", 0) == 0 || r.health[1]->state.rfind("Replace", 0) == 0,
          "worn pack health: %s (IR %.0f mOhm)", r.health[1]->state.c_str(), r.ir[1]->state);
  }
  printf(fails ? "\n%d FAILED\n" : "\nALL PASSED\n", fails);
  return fails != 0;
}
