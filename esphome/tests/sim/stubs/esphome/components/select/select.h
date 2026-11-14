#pragma once
#include <cstddef>
#include <optional>
namespace esphome { template<typename T> using optional = std::optional<T>; namespace select {
class Select { public: size_t idx{0}; optional<size_t> active_index() const { return idx; } };
}}
