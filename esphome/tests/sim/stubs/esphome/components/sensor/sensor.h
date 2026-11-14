#pragma once
#include <cmath>
namespace esphome { namespace sensor {
class Sensor { public: float state{NAN}; bool has_state() const { return !std::isnan(state); }
  void publish_state(float v) { state = v; } };
}}
