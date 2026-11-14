"""One battery slot: LTC4162-L charger (+ optional PCA9554 for switch/LED/bleed)."""

import esphome.codegen as cg
from esphome.components import (
    binary_sensor,
    i2c,
    number,
    output,
    select,
    sensor,
    text_sensor,
)
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_CURRENT,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_PRESENCE,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_VOLTAGE,
    ENTITY_CATEGORY_DIAGNOSTIC,
    STATE_CLASS_MEASUREMENT,
    STATE_CLASS_TOTAL_INCREASING,
    UNIT_AMPERE,
    UNIT_CELSIUS,
    UNIT_PERCENT,
    UNIT_VOLT,
    UNIT_WATT,
)

from ..parkside_charger import CONF_CHARGER_ID, ParksideCharger, ParksideSlot

DEPENDENCIES = ["i2c", "parkside_charger"]
AUTO_LOAD = ["sensor", "text_sensor", "binary_sensor"]
MULTI_CONF = True

CONF_SLOT_NUMBER = "slot_number"
CONF_CELLS = "cells"
CONF_SENSE_RESISTOR = "sense_resistor"
CONF_INPUT_SENSE_RESISTOR = "input_sense_resistor"
CONF_INPUT_CURRENT_LIMIT = "input_current_limit"
CONF_MAX_CHARGE_CURRENT = "max_charge_current"
CONF_MAX_CHARGE_HOURS = "max_charge_hours"
CONF_NTC_R25 = "ntc_r25"
CONF_NTC_BETA = "ntc_beta"
CONF_NTC_BIAS = "ntc_bias_resistor"
CONF_REQUIRE_NTC = "require_ntc"
CONF_MIN_CHARGE_TEMPERATURE = "min_charge_temperature"
CONF_MAX_CHARGE_TEMPERATURE = "max_charge_temperature"
CONF_PRESENCE_SWITCH = "presence_switch"
CONF_BLEED_OUTPUT = "bleed_output"
CONF_BLEED_RESISTANCE = "bleed_resistance"
CONF_LED_RED = "led_red"
CONF_LED_GREEN = "led_green"
CONF_LED_BLUE = "led_blue"
CONF_MODE_SELECT = "mode_select"
CONF_MAX_CURRENT_NUMBER = "max_current_number"
CONF_NOMINAL_CAPACITY_NUMBER = "nominal_capacity_number"
# entities
CONF_PRESENT = "present"
CONF_STATUS = "status"
CONF_HEALTH_STATUS = "health_status"
CONF_BATTERY_VOLTAGE = "battery_voltage"
CONF_CHARGE_CURRENT = "charge_current"
CONF_INPUT_POWER = "input_power"
CONF_BATTERY_TEMPERATURE = "battery_temperature"
CONF_CHARGER_TEMPERATURE = "charger_temperature"
CONF_STATE_OF_CHARGE = "state_of_charge"
CONF_INTERNAL_RESISTANCE = "internal_resistance"
CONF_CHARGED_CAPACITY = "charged_capacity"
CONF_CAPACITY_ESTIMATE = "capacity_estimate"
CONF_HEALTH = "health"
CONF_SELF_DISCHARGE = "self_discharge"

MODE_OPTIONS = ["Auto", "Storage", "Ready", "Full", "Off"]

SENSORS = {
    CONF_BATTERY_VOLTAGE: sensor.sensor_schema(
        unit_of_measurement=UNIT_VOLT,
        accuracy_decimals=2,
        device_class=DEVICE_CLASS_VOLTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_CHARGE_CURRENT: sensor.sensor_schema(
        unit_of_measurement=UNIT_AMPERE,
        accuracy_decimals=2,
        device_class=DEVICE_CLASS_CURRENT,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_INPUT_POWER: sensor.sensor_schema(
        unit_of_measurement=UNIT_WATT,
        accuracy_decimals=1,
        device_class=DEVICE_CLASS_POWER,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_BATTERY_TEMPERATURE: sensor.sensor_schema(
        unit_of_measurement=UNIT_CELSIUS,
        accuracy_decimals=1,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_CHARGER_TEMPERATURE: sensor.sensor_schema(
        unit_of_measurement=UNIT_CELSIUS,
        accuracy_decimals=0,
        device_class=DEVICE_CLASS_TEMPERATURE,
        state_class=STATE_CLASS_MEASUREMENT,
        entity_category=ENTITY_CATEGORY_DIAGNOSTIC,
    ),
    CONF_STATE_OF_CHARGE: sensor.sensor_schema(
        unit_of_measurement=UNIT_PERCENT,
        accuracy_decimals=0,
        device_class=DEVICE_CLASS_BATTERY,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_INTERNAL_RESISTANCE: sensor.sensor_schema(
        unit_of_measurement="mΩ",
        accuracy_decimals=0,
        icon="mdi:omega",
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_CHARGED_CAPACITY: sensor.sensor_schema(
        unit_of_measurement="Ah",
        accuracy_decimals=2,
        icon="mdi:battery-plus",
        state_class=STATE_CLASS_TOTAL_INCREASING,
    ),
    CONF_CAPACITY_ESTIMATE: sensor.sensor_schema(
        unit_of_measurement="Ah",
        accuracy_decimals=2,
        icon="mdi:battery-heart-variant",
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_HEALTH: sensor.sensor_schema(
        unit_of_measurement=UNIT_PERCENT,
        accuracy_decimals=0,
        icon="mdi:heart-pulse",
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    CONF_SELF_DISCHARGE: sensor.sensor_schema(
        unit_of_measurement="mV/d",
        accuracy_decimals=1,
        icon="mdi:battery-minus-variant",
        state_class=STATE_CLASS_MEASUREMENT,
    ),
}

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(ParksideSlot),
            cv.GenerateID(CONF_CHARGER_ID): cv.use_id(ParksideCharger),
            cv.Required(CONF_SLOT_NUMBER): cv.int_range(min=1, max=99),
            cv.Optional(CONF_CELLS, default=5): cv.int_range(min=1, max=8),
            cv.Optional(CONF_SENSE_RESISTOR, default=0.010): cv.resistance,
            cv.Optional(CONF_INPUT_SENSE_RESISTOR, default=0.010): cv.resistance,
            cv.Optional(CONF_INPUT_CURRENT_LIMIT, default="3A"): cv.current,
            cv.Optional(CONF_MAX_CHARGE_CURRENT, default="1.5A"): cv.All(
                cv.current, cv.Range(min=0.1, max=3.2)
            ),
            cv.Optional(CONF_MAX_CHARGE_HOURS, default=10): cv.float_range(
                min=1, max=48
            ),
            cv.Optional(CONF_NTC_R25, default=10000): cv.resistance,
            cv.Optional(CONF_NTC_BETA, default=3435): cv.float_range(
                min=2000, max=6000
            ),
            cv.Optional(CONF_NTC_BIAS, default=10000): cv.resistance,
            cv.Optional(CONF_REQUIRE_NTC, default=True): cv.boolean,
            cv.Optional(CONF_MIN_CHARGE_TEMPERATURE, default=5): cv.float_range(
                min=0, max=20
            ),
            cv.Optional(CONF_MAX_CHARGE_TEMPERATURE, default=45): cv.float_range(
                min=30, max=50
            ),
            cv.Optional(CONF_PRESENCE_SWITCH): cv.use_id(binary_sensor.BinarySensor),
            cv.Optional(CONF_BLEED_OUTPUT): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_BLEED_RESISTANCE, default=200): cv.resistance,
            cv.Optional(CONF_LED_RED): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_LED_GREEN): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_LED_BLUE): cv.use_id(output.BinaryOutput),
            cv.Optional(CONF_MODE_SELECT): cv.use_id(select.Select),
            cv.Optional(CONF_MAX_CURRENT_NUMBER): cv.use_id(number.Number),
            cv.Optional(CONF_NOMINAL_CAPACITY_NUMBER): cv.use_id(number.Number),
            cv.Optional(CONF_PRESENT): binary_sensor.binary_sensor_schema(
                device_class=DEVICE_CLASS_PRESENCE, icon="mdi:battery"
            ),
            cv.Optional(CONF_STATUS): text_sensor.text_sensor_schema(
                icon="mdi:battery-charging"
            ),
            cv.Optional(CONF_HEALTH_STATUS): text_sensor.text_sensor_schema(
                icon="mdi:battery-heart"
            ),
            **{cv.Optional(k): v for k, v in SENSORS.items()},
        }
    )
    .extend(cv.polling_component_schema("2s"))
    .extend(i2c.i2c_device_schema(0x68))
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)

    hub = await cg.get_variable(config[CONF_CHARGER_ID])
    cg.add(var.set_charger(hub))
    cg.add(hub.register_slot(var))

    cg.add(var.set_slot_number(config[CONF_SLOT_NUMBER]))
    cg.add(var.set_cells(config[CONF_CELLS]))
    cg.add(var.set_rsnsb(config[CONF_SENSE_RESISTOR]))
    cg.add(var.set_rsnsi(config[CONF_INPUT_SENSE_RESISTOR]))
    cg.add(var.set_input_current_limit(config[CONF_INPUT_CURRENT_LIMIT]))
    cg.add(var.set_default_max_current(config[CONF_MAX_CHARGE_CURRENT]))
    cg.add(var.set_max_charge_hours(config[CONF_MAX_CHARGE_HOURS]))
    cg.add(
        var.set_ntc(config[CONF_NTC_R25], config[CONF_NTC_BETA], config[CONF_NTC_BIAS])
    )
    cg.add(var.set_require_ntc(config[CONF_REQUIRE_NTC]))
    cg.add(
        var.set_temperature_window(
            config[CONF_MIN_CHARGE_TEMPERATURE], config[CONF_MAX_CHARGE_TEMPERATURE]
        )
    )
    cg.add(var.set_bleed_resistance(config[CONF_BLEED_RESISTANCE]))

    if CONF_PRESENCE_SWITCH in config:
        cg.add(var.set_presence_switch(await cg.get_variable(config[CONF_PRESENCE_SWITCH])))
    if CONF_BLEED_OUTPUT in config:
        cg.add(var.set_bleed_output(await cg.get_variable(config[CONF_BLEED_OUTPUT])))
    leds = []
    for key in (CONF_LED_RED, CONF_LED_GREEN, CONF_LED_BLUE):
        leds.append(await cg.get_variable(config[key]) if key in config else cg.nullptr)
    cg.add(var.set_led_outputs(*leds))
    if CONF_MODE_SELECT in config:
        cg.add(var.set_mode_select(await cg.get_variable(config[CONF_MODE_SELECT])))
    if CONF_MAX_CURRENT_NUMBER in config:
        cg.add(var.set_max_current_number(await cg.get_variable(config[CONF_MAX_CURRENT_NUMBER])))
    if CONF_NOMINAL_CAPACITY_NUMBER in config:
        cg.add(
            var.set_nominal_capacity_number(
                await cg.get_variable(config[CONF_NOMINAL_CAPACITY_NUMBER])
            )
        )

    if conf := config.get(CONF_PRESENT):
        cg.add(var.set_present_binary_sensor(await binary_sensor.new_binary_sensor(conf)))
    if conf := config.get(CONF_STATUS):
        cg.add(var.set_status_text_sensor(await text_sensor.new_text_sensor(conf)))
    if conf := config.get(CONF_HEALTH_STATUS):
        cg.add(var.set_health_text_sensor(await text_sensor.new_text_sensor(conf)))
    setters = {
        CONF_BATTERY_VOLTAGE: var.set_battery_voltage_sensor,
        CONF_CHARGE_CURRENT: var.set_charge_current_sensor,
        CONF_INPUT_POWER: var.set_input_power_sensor,
        CONF_BATTERY_TEMPERATURE: var.set_battery_temperature_sensor,
        CONF_CHARGER_TEMPERATURE: var.set_charger_temperature_sensor,
        CONF_STATE_OF_CHARGE: var.set_state_of_charge_sensor,
        CONF_INTERNAL_RESISTANCE: var.set_internal_resistance_sensor,
        CONF_CHARGED_CAPACITY: var.set_charged_capacity_sensor,
        CONF_CAPACITY_ESTIMATE: var.set_capacity_estimate_sensor,
        CONF_HEALTH: var.set_health_sensor,
        CONF_SELF_DISCHARGE: var.set_self_discharge_sensor,
    }
    for key, setter in setters.items():
        if conf := config.get(key):
            cg.add(setter(await sensor.new_sensor(conf)))
