#pragma once
#include <cmath>
namespace esphome { namespace number {
class Number { public: float state{NAN}; bool has_state() const { return !std::isnan(state); } };
}}
