#pragma once
#include <cstdarg>
#include <cstdio>
#include <string>
#include <algorithm>
namespace esphome {
inline std::string str_sprintf(const char *fmt, ...) {
  char buf[256]; va_list a; va_start(a, fmt); vsnprintf(buf, sizeof buf, fmt, a); va_end(a); return buf;
}
template<typename T> T clamp(T v, T lo, T hi) { return std::min(std::max(v, lo), hi); }
}
#define YESNO(b) ((b) ? "YES" : "NO")
