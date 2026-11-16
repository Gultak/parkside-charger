#pragma once
#include <cstdint>
#include <cstddef>
namespace esphome { namespace i2c {
enum ErrorCode { ERROR_OK = 0, ERROR_NOT_ACKNOWLEDGED = 2 };
struct FakeBus {
  virtual ~FakeBus() = default;
  virtual ErrorCode rd(uint8_t reg, uint8_t *data, size_t len) = 0;
  virtual ErrorCode wr(uint8_t reg, const uint8_t *data, size_t len) = 0;
};
class I2CDevice {
 public:
  void set_fake_bus(FakeBus *b) { bus_ = b; }
  ErrorCode read_register(uint8_t reg, uint8_t *data, size_t len) { return bus_->rd(reg, data, len); }
  ErrorCode write_register(uint8_t reg, const uint8_t *data, size_t len) const { return bus_->wr(reg, data, len); }
 protected:
  FakeBus *bus_{nullptr};
};
}}
