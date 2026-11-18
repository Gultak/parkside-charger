# Firmware (ESPHome) and charging strategy

## Files

```
esphome/
  parkside-charger.yaml      main config: ESP32-C6 D1, I2C, 2x TCA9548A, SHT21, bus switch, ADCs, hub
  slot.yaml                  per-slot package (included up to 16x with vars: n; delete unused ones)
  secrets.yaml.example       copy to secrets.yaml
  components/
    parkside_charger/        C++: LTC4162-L driver, slot state machine, power-budget hub
    parkside_slot/           config schema for one slot
  tests/sim/                 host simulation: fake LTC4162 + battery model
```

Build:

```bash
cd esphome && cp secrets.yaml.example secrets.yaml && esphome run parkside-charger.yaml
```

The config was validated with ESPHome **2026.10.2** (`esphome config`). The code generation and a
C++ compile check against the real ESPHome headers pass. A full ESP32-C6 firmware build could not
run here because the ESP-IDF download server was blocked, so the first real build happens on your
machine.

Run the state-machine simulation:

```bash
cd esphome/tests/sim
g++ -std=gnu++20 -O2 -Istubs -I../../components sim.cpp ../../components/parkside_charger/parkside_charger.cpp -o sim
./sim
```

It covers 5 scenarios: charging to Ready, automatic drop to storage, the 100 % button, the
power budget with 10 empty packs, and the protections. All pass. Add `v` as an argument for a
log.

## Charging strategy ("optimal" for Li-ion longevity)

Li-ion ages fastest when it is **kept at 100 % and warm**. Lower voltage and no trickle charge
mean slower ageing. Each slot therefore has a **mode** (a select entity in Home Assistant):

| Mode | Target per cell | Pack | ≈ SoC | Use |
|---|---|---|---|---|
| **Auto** (default) | 4.10 V, then **3.85 V after N days untouched** | 20.5 V → 19.25 V | 92 % → 60 % | Packs are always ready, and drop to storage when you don't use them |
| Storage | 3.85 V | 19.25 V | 60 % | Long-term storage, winter |
| Ready | 4.10 V | 20.5 V | 92 % | Always ready, about 2× the cycle life of 4.2 V |
| Full | 4.20 V | 21.0 V | 100 % | Maximum runtime |
| Off | – | – | – | Holding only, no charging |

Plus:

- **"Slot n charge to 100 %"** and **"Charge all to 100 %"** buttons. They hold the pack at
  100 % until you remove it, and suit a Home Assistant automation such as "Friday 18:00 before a
  project weekend".
- **Storage after (days)**: the Auto-mode timer, 14 days by default, 0 = never.
- **No trickle or float charge.** Each charge ends at C/20 (CV phase). The charger is then
  suspended and restarts only when the rested voltage falls 40 mV/cell below the target.
- **Bleed-down:** if a pack is more than 50 mV/cell above the target (a full pack in Storage mode,
  or the Auto timer expiring), the slot switches in its 200 Ω bleed resistor (about 0.1 A) until
  it reaches the target.
- **Balancing charge.** The pack balances its five cells itself, with small transistor + resistor
  bleeders controlled by its microcontroller (Julian Ilett's teardown). They can only keep up
  near full and at low current, at the end of a charge. A pack that only ever sees 3.85–4.10 V and
  a C/20 stop would never be balanced. So every `balance_interval` (default **30 days** in the
  slot; 0 = off), and on every *charge to 100 %*, the slot:
  1. charges to 4.20 V/cell,
  2. switches the LTC4162's C/20 termination off and holds 4.20 V at **≤ 0.2 A**
     (`balance_current`) for `balance_tail` (default **120 min**), status *Balancing cells*,
  3. finishes, and returns to the mode's target (Auto/Storage bleed back down).
  The interval counts from insertion and restarts after a controller reboot.
- **Pack BMS:** the slot board watches the pack's ID contact (the BMS status line). While the
  BMS reports a fault or deep discharge (line released for more than ~3 s), the slot does not
  charge: status *Pack BMS blocks charging*, entity `Slot n pack BMS fault`.
- **Temperature:** charging only runs between 5 and 45 °C on the slot's NTC (next to the battery
  contacts), with 2 K hysteresis.
  The LTC4162's own JEITA control is on as well. If the enclosure is above 45 °C (SHT21; adjustable, see the safety interlock), all
  charging stops and the 24 V bus switch opens.
- **Power budget:** `max_total_current: 8A` is shared out every 2 s. "100 %" requests go first,
  then the emptiest packs. A pack in its CV phase only reserves what it actually draws plus
  0.3 A, so the next pack can start sooner. At most 1C per pack when the nominal capacity is set.
- **Fault latching:** battery short or deep discharge, failed detection, the LTC4162 max-time
  fault, or a 10 h timeout put the slot in "Fault". It stays there until the pack is removed,
  and the buzzer sounds.

## Safety interlock

The controller switches the 24 V bus off, and no slot charges, while any of these holds. It
overrides the "Charging enabled" switch and releases by itself once everything is fine again.

| | Condition | Limit (Home Assistant config entity) |
|---|---|---|
| A | Enclosure (SHT21) too hot, or no SHT21 reading for the grace period | "Safety: max enclosure temperature", 45 °C, 3 °C hysteresis |
| B | Room too hot (`room_temperature_entity`, default `sensor.hotpress_temperature_sensor_temperature`), or that value unknown / unavailable for the grace period | "Safety: max room temperature", 36 °C, 2 °C hysteresis |
| C | Home Assistant not connected for the grace period | "Safety: Home Assistant grace period", 120 s |

- After a boot nothing charges until Home Assistant has connected and sent the room temperature.
- **"Safety: allow charging without Home Assistant"** (off by default) skips C and the
  room-temperature-unknown check, e.g. while Home Assistant is down for maintenance. The
  enclosure check stays.
- **Entities:** "Safety interlock" (problem binary sensor) and "Safety interlock reason" (text);
  the charger status shows "Stopped: <reason>" as well.
- The component's own `max_ambient_temperature: 50` stays as a hard backstop, and the buzzer
  sounds above 50 °C.
- Change the room sensor with the `room_temperature_entity` substitution at the top of
  `parkside-charger.yaml`.

## Home Assistant entities (per slot)

| Entity | Meaning |
|---|---|
| `Slot n battery present` | Microswitch. Without one, falls back to the pack's BMS signal / voltage |
| `Slot n pack BMS fault` | On while the pack's BMS releases its ID contact (fault, deep discharge, or no pack) |
| `Slot n contact temperature` | NTC on the slot board next to the battery contacts |
| `Slot n status` | Empty / Battery detected / Waiting for power budget / Charging (target 92 %) / Ready / Full / Holding storage level / Discharging to storage level / Paused: temperature / No thermistor reading / No 24 V input / Fault: … / No charger board |
| `Slot n voltage`, `charge current`, `battery temperature` | Live telemetry |
| `Slot n state of charge` | From the rested voltage (compensated for I·R while charging) |
| `Slot n internal resistance` | **Battery series resistance**, measured by the LTC4162 once per charge in the CC phase (button to repeat) |
| `Slot n capacity (estimated)` | Ah charged ÷ SoC swing, when a charge covers ≥ 30 % SoC |
| `Slot n health (capacity)` | Estimated ÷ nominal capacity (set "Slot n nominal capacity" to 2/4/6/8 Ah) |
| `Slot n self-discharge` | mV/day/cell, measured after ≥ 24 h of rest. More than 5 is suspicious, more than 15 means a bad cell |
| `Slot n health` | **Good / Aged / Worn / Replace**, with reasons, combined from the three metrics above |
| Config: `charge mode`, `max charge current`, `nominal capacity` | Kept across reboots |

Global: `Charger status`, `Total charging power`, `Batteries charging`, `Batteries present`,
`Enclosure temperature`, `PSU voltage`, `Slot bus voltage`, the `Charging enabled` switch,
`Auto mode: storage after (days)`, `Charge all to 100 %`, and (diagnostic) `Reset I2C multiplexers`.

### Controller GPIOs (controller board, ESP32-C6 D1)

| GPIO | Function |
|---|---|
| 22 / 23 | I²C SDA / SCL (3.3 V side) |
| 19 | 24 V bus switch (high = on; pulled low while the ESP boots) |
| 18 | Buzzer |
| 4 | TCA9548A reset, active low |
| 0 / 1 | PSU voltage / switched slot-bus voltage, through 100 k / 10 k dividers (×11) |
| 5, 6, 7, 16, 17 | Spare, on the 7-pin expansion header |

Channel-to-slot mapping follows the board layout. On 0x70, slots 1–8 are channels 0–7. On 0x71,
slots 9–12 are channels 7–4 and slots 13–16 are channels 3–0. `parkside-charger.yaml` already
contains the right table.

### Health heuristics: please calibrate

- Internal resistance is normalised to capacity (mΩ·Ah per cell group), so 1P/2P and
  18650/21700 packs compare fairly: < 140 Good, < 200 Aged, < 300 Worn, otherwise Replace.
  Measure your **new** packs first and adjust the thresholds in `update_health_()` if needed.
  The value includes contacts and wiring.
- Packs have **no readable ID**. All health values belong to the battery that is currently
  inserted and reset when it is removed. Home Assistant's history shows the trend per slot. For
  per-pack history, put the same pack back in the same slot, or add NFC tags later.
- Cell balance cannot be seen: only the pack voltage is accessible.

## LED legend

| Colour | Meaning |
|---|---|
| off | empty |
| blue | battery detected / holding at storage level / mode Off |
| yellow | charging |
| yellow, blinking | waiting for power budget |
| green | ready (≥ 80 %) |
| magenta | discharging to storage level |
| magenta, blinking | paused: temperature / no NTC / no 24 V / pack BMS blocks charging |
| red, blinking | fault, or slot board not responding |

## Example Home Assistant automation

```yaml
alias: Parkside battery needs attention
trigger:
  - platform: state
    entity_id: [sensor.parkside_charger_slot_1_health, sensor.parkside_charger_slot_2_health] # ... all slots
condition:
  - "{{ trigger.to_state.state.startswith(('Worn', 'Replace', 'Faulty')) }}"
action:
  - service: notify.mobile_app_phone
    data:
      message: "{{ trigger.to_state.name }}: {{ trigger.to_state.state }}"
```

## Bring-up checklist

1. Controller board only, no slots, SHT21 plugged in: the `i2c scan` must show 0x40, 0x70 and
   0x71. *PSU voltage* should read about 24.5 V. *Slot bus voltage* should read 0 V, then about
   24.5 V after *Charging enabled* is switched on.
2. One slot board **without a battery**: the log shows the slot's LTC4162 and PCA9554, with no
   "strap" or "wrong charger IC" error. `cell_count` only reads 5 while the charger is running
   and 0 otherwise, so the strapping check takes effect during the first charge.
3. Put a **lab supply in place of the battery** (20 V, 0.5 A limit, with a 10 kΩ resistor from ID to
   B− standing in for the pack's BMS line). Check the voltage reading against a multimeter, and adjust
   `sense_resistor` if the current reading is off.
4. Use a real pack in **Storage** mode first: it charges only briefly, at low risk. Then try Ready.
5. Watch the first full charges from start to finish, including temperatures.
