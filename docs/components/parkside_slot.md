# Parkside Slot (LTC4162-L charging module)

The `parkside_slot` component drives one charging slot of the Parkside charger: an
[LTC4162-L](https://www.analog.com/en/products/ltc4162-l.html) (the I²C-adjustable `-LAD`
version) step-down Li-ion charger on a slot board, plus optional slot I/O (presence switch, RGB
LED, bleed resistor, pack BMS signal) usually on a PCA9554 I/O expander. It runs the whole charge
cycle for the inserted pack: detection, charging to the mode's target voltage, ending the charge,
recharge, bleed-down to storage level, periodic balancing, and battery health estimates.

The slot gets its charge current from the [`parkside_charger`](parkside_charger.md) hub, which
shares the power supply's budget between all slots. Each slot needs its own I²C bus, since every
LTC4162 has the fixed address `0x68`: use one [TCA9548A](https://esphome.io/components/tca9548a)
channel per slot.

```yaml
# Example configuration entry
parkside_slot:
  - id: slot1
    slot_number: 1
    i2c_id: slot1_bus
    address: 0x68
    cells: 5
    sense_resistor: 0.010
    input_sense_resistor: 0.010
    max_charge_current: 1.5A
    ntc_beta: 3380
    presence_switch: slot1_switch
    bms_fault_input: slot1_bms_fault
    led_red: slot1_led_r
    led_green: slot1_led_g
    led_blue: slot1_led_b
    bleed_output: slot1_bleed
    bleed_resistance: 200 ohm
    mode_select: slot1_mode
    max_current_number: slot1_max_current
    nominal_capacity_number: slot1_nominal_capacity
    present:
      name: "Slot 1 battery present"
    status:
      name: "Slot 1 status"
    battery_voltage:
      name: "Slot 1 voltage"
    charge_current:
      name: "Slot 1 charge current"
    state_of_charge:
      name: "Slot 1 state of charge"
```

The repository's `slot.yaml` is a complete package for one slot (PCA9554, inputs, outputs, select,
numbers, buttons and all sensors), included once per slot with `vars: { n: <slot number> }`.

## Configuration variables

### Hardware

- **id** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)): Manually
  specify the ID used for code generation and for `lambda` calls.
- **charger_id** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)): The
  `parkside_charger` hub. Only needed when there is more than one hub.
- **slot_number** (**Required**, int): The slot's number, 1–99. Used in log messages.
- **i2c_id** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)): The I²C
  bus of this slot, typically a TCA9548A channel.
- **address** (*Optional*, int): The LTC4162's I²C address. Defaults to `0x68` (fixed in the
  chip).
- **cells** (*Optional*, int): Cells in series, 1–8. Defaults to `5` (Parkside X20V).
- **sense_resistor** (*Optional*, resistance): The battery-side current sense resistor
  (R<sub>SNSB</sub>). Defaults to `0.010` (10 mΩ, up to 3.2 A).
- **input_sense_resistor** (*Optional*, resistance): The input-side sense resistor
  (R<sub>SNSI</sub>). Defaults to `0.010`.
- **input_current_limit** (*Optional*, current): The LTC4162's input current limit. Defaults to
  `3A`.
- **ntc_r25** (*Optional*, resistance): The thermistor's resistance at 25 °C. Defaults to `10000`.
- **ntc_beta** (*Optional*, float): The thermistor's B constant. Defaults to `3435`; the slot
  board's Murata NCP18XH103F03RB is `3380`.
- **ntc_bias_resistor** (*Optional*, resistance): The NTC bias resistor to the LTC4162's NTCBIAS
  pin. Defaults to `10000`.

### Slot I/O

- **presence_switch** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [binary sensor](https://esphome.io/components/binary_sensor/)): `ON` while a pack is
  seated. Without it, the slot detects a pack by the BMS signal and the battery voltage.
- **bms_fault_input** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a binary sensor): `ON` while the pack's BMS reports a fault or deep discharge (the pack's ID
  contact released). The slot does not charge then: status *Pack BMS blocks charging*.
- **led_red**, **led_green**, **led_blue** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [binary output](https://esphome.io/components/output/)): A common-cathode RGB LED that
  shows the slot's state (see [LED](#led)).
- **bleed_output** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a binary output): Switches a bleed resistor across the pack, to bring it down to the storage
  level. Leave it out if no bleed resistor is fitted.
- **bleed_resistance** (*Optional*, resistance): The bleed resistor, for the time and charge
  estimates. Defaults to `200` Ω.

### Charging

- **max_charge_current** (*Optional*, current): The slot's default maximum charge current,
  0.1–3.2 A. Defaults to `1.5A`. Overridden by `max_current_number`, and limited to 1C when the
  pack's nominal capacity is known.
- **max_charge_hours** (*Optional*, float): A charge that takes longer than this ends in *Fault*.
  Range 1–48. Defaults to `10`.
- **require_ntc** (*Optional*, boolean): Refuse to charge without a valid thermistor reading
  (status *No thermistor reading*). Defaults to `true`.
- **min_charge_temperature** (*Optional*, float): No charging below this temperature in °C, 0–20.
  Defaults to `5`.
- **max_charge_temperature** (*Optional*, float): No charging above this temperature in °C, 30–50.
  Defaults to `45`. Both limits have 2 °C hysteresis (status *Paused: temperature*).
- **balance_interval** (*Optional*, [Time](https://esphome.io/guides/configuration-types#config-time)):
  How often a balancing charge runs: up to 4.20 V/cell, then a low-current tail so the pack's own
  cell balancers can work. Counted from insertion. `0s` = only when charging to 100 % is
  requested. Defaults to `30d`.
- **balance_tail** (*Optional*, Time): How long the balancing tail holds 4.20 V/cell. Defaults
  to `120min`.
- **balance_current** (*Optional*, current): The maximum current during the tail, 0.1–1.0 A.
  Defaults to `0.2A`.

### Settings from Home Assistant

- **mode_select** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id) of a
  [select](https://esphome.io/components/select/)): The charge mode. The select's options must be
  `Auto`, `Storage`, `Ready`, `Full`, `Off`, in this order (see [Modes](#modes)). Without it the
  slot runs in *Auto*.
- **max_current_number** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a [number](https://esphome.io/components/number/)): The maximum charge current in A.
- **nominal_capacity_number** (*Optional*, [ID](https://esphome.io/guides/configuration-types#config-id)
  of a number): The pack's nominal capacity in Ah (`0` = unknown). Enables the 1C limit and the
  capacity-based health percentage.

### Entities

- **present** (*Optional*): `ON` while a battery is in the slot. All options from
  [Binary Sensor](https://esphome.io/components/binary_sensor/).
- **status** (*Optional*): The slot's state as text (see [Status](#status)). All options from
  [Text Sensor](https://esphome.io/components/text_sensor/).
- **health_status** (*Optional*): `Good`, `Aged`, `Worn` or `Replace` from the internal
  resistance, `Faulty: <reason>`, `Unknown (measured during the next charge)` or `No battery`.
  All options from Text Sensor.
- **battery_voltage** (*Optional*): Pack voltage in V.
- **charge_current** (*Optional*): Charge current in A.
- **input_power** (*Optional*): The charger's input power in W.
- **battery_temperature** (*Optional*): The thermistor's temperature in °C (on the slot board,
  next to the battery contacts).
- **charger_temperature** (*Optional*): The LTC4162's die temperature in °C (diagnostic).
- **state_of_charge** (*Optional*): Estimated state of charge in %, from the rested voltage,
  compensated for I·R while charging.
- **internal_resistance** (*Optional*): The battery's series resistance in mΩ, measured by the
  LTC4162 once per charge in the constant-current phase (includes contacts and wiring).
- **charged_capacity** (*Optional*): Ah charged since the pack was inserted.
- **capacity_estimate** (*Optional*): Estimated capacity in Ah: Ah charged ÷ state-of-charge
  swing, once a charge covers at least 30 %.
- **health** (*Optional*): Estimated capacity ÷ nominal capacity, in %.
- **self_discharge** (*Optional*): Voltage drop per cell in mV/day, measured after at least 24 h
  of rest. More than 5 is suspicious, more than 15 points to a bad cell.

All sensors take all options from [Sensor](https://esphome.io/components/sensor/). All values
belong to the pack that is inserted now and reset when it is removed: packs carry no readable ID.

- **update_interval** (*Optional*, [Time](https://esphome.io/guides/configuration-types#config-time)):
  How often the slot reads the charger and runs its state machine. Defaults to `2s`.

## Modes

| Mode | Target per cell | Pack (5S) | ≈ State of charge |
|---|---|---|---|
| **Auto** | 4.10 V, then 3.85 V after `storage_after_days` (hub) untouched | 20.5 V → 19.25 V | 92 % → 60 % |
| **Storage** | 3.85 V | 19.25 V | 60 % |
| **Ready** | 4.10 V | 20.5 V | 92 % |
| **Full** | 4.20 V | 21.0 V | 100 % |
| **Off** | no charging | | |

There is no trickle or float charge: a charge ends at C/20 in the constant-voltage phase, the
charger is suspended, and it only restarts when the rested voltage has fallen 40 mV/cell below
the target. A pack more than 50 mV/cell above the target (a full pack in *Storage*, or when the
*Auto* timer expires) is discharged through the bleed resistor until it reaches the target.

A *charge to 100 %* request (see [Lambda calls](#lambda-calls)) charges to 4.20 V/cell with a
balancing tail and holds that until the pack is removed.

## Status

| Status | Meaning |
|---|---|
| `Empty` | No battery |
| `Battery detected` | Just inserted, waiting for the readings to settle |
| `Charging`, `Balancing charge`, `Balancing cells` | Charging; *Balancing charge* is the run up to 4.20 V/cell, *Balancing cells* the low-current tail |
| `Waiting for power budget` | Needs charge, but the hub has no current left for it |
| `Ready`, `Full`, `Holding storage level` | At the mode's target (4.10 V, 4.20 V or 3.85 V per cell) and resting |
| `Discharging to storage level` | Bleed resistor on |
| `Paused: temperature` | Outside `min_charge_temperature`…`max_charge_temperature` |
| `No thermistor reading` | `require_ntc` is set and the NTC reads open or shorted |
| `No 24 V input` | The charger has no input voltage |
| `Pack BMS blocks charging` | `bms_fault_input` is `ON` |
| `Charging disabled` | Mode *Off*, or charging disabled on the hub |
| `Fault: <reason>` | Battery short or deep discharge, failed detection, the LTC4162's timer fault, or `max_charge_hours` exceeded. Latched until the pack is removed |
| `No charger board` | The LTC4162 does not answer on I²C |

While charging, waiting, discharging or resting, the status ends with the target, for example
`Charging (target 92 %)`.

## LED

| Colour | Meaning |
|---|---|
| off | empty |
| blue | battery detected / holding at storage level / mode *Off* |
| yellow | charging |
| yellow, blinking | waiting for power budget |
| green | ready (≥ 80 %) |
| magenta | discharging to storage level |
| magenta, blinking | paused: temperature, no NTC, no 24 V, or the pack's BMS blocks charging |
| red, blinking | fault, or the slot board does not answer |

## Lambda calls

From [lambdas](https://esphome.io/automations/templates#config-lambda), you can call these
methods on a slot (for example `id(slot1)`):

- `request_full_charge()`: Charge this pack to 100 % with a balancing tail, and hold it there
  until it is removed. Typically from a button:

  ```yaml
  button:
    - platform: template
      name: "Slot 1 charge to 100%"
      on_press:
        - lambda: id(slot1).request_full_charge();
  ```

- `request_resistance_measurement()`: Measure the internal resistance again during the next
  constant-current phase.
- `phase()`: The slot's state as `esphome::parkside_charger::Phase` (`EMPTY`, `CHARGING`,
  `FAULT`, …).
- `is_present()`, `is_charging()`, `is_balancing()`: State checks.
- `input_power()`: The input power in W.

## See also

- [Parkside Charger (hub)](parkside_charger.md)
- [Firmware overview](../firmware.md): charging strategy and health heuristics
- [TCA9548A I²C Multiplexer](https://esphome.io/components/tca9548a), [PCA9554 I/O Expander](https://esphome.io/components/pca9554)
- [LTC4162-L datasheet](https://www.analog.com/en/products/ltc4162-l.html)
