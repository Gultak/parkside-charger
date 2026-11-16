#pragma once
// Minimal stand-ins for the ESPHome API used by parkside_charger (host simulation only)
#include <cstdint>
#include <string>
namespace esphome {
namespace setup_priority { static const float DATA = 600.0f; }
class Component {
 public:
  virtual ~Component() = default;
  virtual void setup() {}
  virtual void dump_config() {}
  virtual float get_setup_priority() const { return 0; }
};
class PollingComponent : public Component {
 public:
  virtual void update() = 0;
};
}  // namespace esphome
