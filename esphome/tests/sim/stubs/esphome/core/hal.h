#pragma once
#include <cstdint>
namespace esphome { extern uint32_t g_millis; inline uint32_t millis() { return g_millis; } }
