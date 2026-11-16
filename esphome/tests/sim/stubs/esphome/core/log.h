#pragma once
#include <cstdio>
extern bool g_verbose;
extern double g_sim_hours;
#define ESP_LOG_(lvl, tag, fmt, ...) do { if (g_verbose) printf("[%7.3fh][%s] " fmt "\n", g_sim_hours, lvl, ##__VA_ARGS__); } while (0)
#define ESP_LOGE(tag, fmt, ...) ESP_LOG_("E", tag, fmt, ##__VA_ARGS__)
#define ESP_LOGW(tag, fmt, ...) ESP_LOG_("W", tag, fmt, ##__VA_ARGS__)
#define ESP_LOGI(tag, fmt, ...) ESP_LOG_("I", tag, fmt, ##__VA_ARGS__)
#define ESP_LOGD(tag, fmt, ...) ESP_LOG_("D", tag, fmt, ##__VA_ARGS__)
#define ESP_LOGV(tag, fmt, ...) do {} while (0)
#define ESP_LOGCONFIG(tag, fmt, ...) do {} while (0)
#define LOG_I2C_DEVICE(x) do {} while (0)
#define LOG_UPDATE_INTERVAL(x) do {} while (0)
