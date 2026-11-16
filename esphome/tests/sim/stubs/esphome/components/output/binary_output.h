#pragma once
namespace esphome { namespace output {
class BinaryOutput { public: bool on{false}; void turn_on() { on = true; } void turn_off() { on = false; }
  void set_state(bool s) { on = s; } };
}}
