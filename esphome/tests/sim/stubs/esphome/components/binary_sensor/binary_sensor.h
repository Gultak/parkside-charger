#pragma once
namespace esphome { namespace binary_sensor {
class BinarySensor { public: bool state{false}; bool hs{false}; bool has_state() const { return hs; }
  void publish_state(bool v) { state = v; hs = true; } };
}}
