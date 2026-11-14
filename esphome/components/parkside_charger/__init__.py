"""Hub: shares the PSU power budget between the Parkside slots."""

import esphome.codegen as cg
from esphome.components import number, output, sensor, text_sensor
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    ICON_FLASH,
    STATE_CLASS_MEASUREMENT,
    DEVICE_CLASS_POWER,
    UNIT_WATT,
)

CODEOWNERS = []
DEPENDENCIES = ["i2c"]
AUTO_LOAD = ["sensor", "text_sensor", "binary_sensor"]

parkside_charger_ns = cg.esphome_ns.namespace("parkside_charger")
ParksideCharger = parkside_charger_ns.class_("ParksideCharger", cg.PollingComponent)
ParksideSlot = parkside_charger_ns.class_("ParksideSlot", cg.PollingComponent)

CONF_CHARGER_ID = "charger_id"
CONF_MAX_TOTAL_CURRENT = "max_total_current"
CONF_ENABLE_OUTPUT = "enable_output"
CONF_AMBIENT_TEMPERATURE = "ambient_temperature"
CONF_MAX_AMBIENT_TEMPERATURE = "max_ambient_temperature"
CONF_STORAGE_AFTER_DAYS = "storage_after_days"
CONF_STORAGE_AFTER_DAYS_NUMBER = "storage_after_days_number"
CONF_TOTAL_INPUT_POWER = "total_input_power"
CONF_CHARGING_COUNT = "charging_count"
CONF_PRESENT_COUNT = "present_count"
CONF_STATUS = "status"

CONFIG_SCHEMA = cv.Schema(
    {
        cv.GenerateID(): cv.declare_id(ParksideCharger),
        cv.Optional(CONF_MAX_TOTAL_CURRENT, default="8A"): cv.All(
            cv.current, cv.Range(min=0.3, max=60)
        ),
        cv.Optional(CONF_ENABLE_OUTPUT): cv.use_id(output.BinaryOutput),
        cv.Optional(CONF_AMBIENT_TEMPERATURE): cv.use_id(sensor.Sensor),
        cv.Optional(CONF_MAX_AMBIENT_TEMPERATURE, default=45): cv.float_range(
            min=20, max=70
        ),
        cv.Optional(CONF_STORAGE_AFTER_DAYS, default=14): cv.float_range(
            min=0, max=45
        ),
        cv.Optional(CONF_STORAGE_AFTER_DAYS_NUMBER): cv.use_id(number.Number),
        cv.Optional(CONF_TOTAL_INPUT_POWER): sensor.sensor_schema(
            unit_of_measurement=UNIT_WATT,
            accuracy_decimals=1,
            device_class=DEVICE_CLASS_POWER,
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_CHARGING_COUNT): sensor.sensor_schema(
            accuracy_decimals=0, icon=ICON_FLASH, state_class=STATE_CLASS_MEASUREMENT
        ),
        cv.Optional(CONF_PRESENT_COUNT): sensor.sensor_schema(
            accuracy_decimals=0,
            icon="mdi:battery-multiple",
            state_class=STATE_CLASS_MEASUREMENT,
        ),
        cv.Optional(CONF_STATUS): text_sensor.text_sensor_schema(
            icon="mdi:battery-charging"
        ),
    }
).extend(cv.polling_component_schema("2s"))


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    cg.add(var.set_max_total_current(config[CONF_MAX_TOTAL_CURRENT]))
    cg.add(var.set_max_ambient(config[CONF_MAX_AMBIENT_TEMPERATURE]))
    cg.add(var.set_storage_after_days(config[CONF_STORAGE_AFTER_DAYS]))
    if CONF_ENABLE_OUTPUT in config:
        cg.add(var.set_enable_output(await cg.get_variable(config[CONF_ENABLE_OUTPUT])))
    if CONF_AMBIENT_TEMPERATURE in config:
        cg.add(var.set_ambient_sensor(await cg.get_variable(config[CONF_AMBIENT_TEMPERATURE])))
    if CONF_STORAGE_AFTER_DAYS_NUMBER in config:
        cg.add(
            var.set_storage_after_days_number(
                await cg.get_variable(config[CONF_STORAGE_AFTER_DAYS_NUMBER])
            )
        )
    if conf := config.get(CONF_TOTAL_INPUT_POWER):
        cg.add(var.set_total_power_sensor(await sensor.new_sensor(conf)))
    if conf := config.get(CONF_CHARGING_COUNT):
        cg.add(var.set_charging_count_sensor(await sensor.new_sensor(conf)))
    if conf := config.get(CONF_PRESENT_COUNT):
        cg.add(var.set_present_count_sensor(await sensor.new_sensor(conf)))
    if conf := config.get(CONF_STATUS):
        cg.add(var.set_status_text_sensor(await text_sensor.new_text_sensor(conf)))
