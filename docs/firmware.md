# Firmware (ESPHome) and charging strategy

## Files

```
esphome/
  parkside-charger.yaml      main config: ESP32-C6, I2C, 2x TCA9548A, SHT40, bus switch, hub
  slot.yaml                  per-slot package (included 10x with vars: n)
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
- **Temperature:** charging only runs between 5 and 45 °C on the pack's NTC, with 2 K hysteresis.
  The LTC4162's own JEITA control is on as well. If the enclosure is above 45 °C (SHT40), all
  charging stops and the 24 V bus switch opens.
- **Power budget:** `max_total_current: 8A` is shared out every 2 s. "100 %" requests go first,
  then the emptiest packs. A pack in its CV phase only reserves what it actually draws plus
  0.3 A, so the next pack can start sooner. At most 1C per pack when the nominal capacity is set.
- **Fault latching:** battery short or deep discharge, failed detection, the LTC4162 max-time
  fault, or a 10 h timeout put the slot in "Fault". It stays there until the pack is removed,
  and the buzzer sounds.

## Home Assistant entities (per slot)

| Entity | Meaning |
|---|---|
| `Slot n battery present` | Microswitch. Without one, falls back to NTC/voltage detection |
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
`Enclosure temperature`, the `Charging enabled` switch, `Auto mode: storage after (days)`, and
`Charge all to 100 %`.

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
| magenta, blinking | paused: temperature / no NTC / no 24 V |
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

1. Main board only, no slots: `i2c scan` must show 0x44, 0x70 and 0x71.
2. One slot board **without a battery**: the log shows the slot's LTC4162 and PCA9554, with no
   "strap" or "wrong charger IC" error. `cell_count` only reads 5 while the charger is running
   and 0 otherwise, so the strapping check takes effect during the first charge.
3. Put a **lab supply in place of the battery** (20 V, 0.5 A limit, with a 10 kΩ resistor from T to
   B− standing in for the NTC). Check the voltage reading against a multimeter, and adjust
   `sense_resistor` if the current reading is off.
4. Use a real pack in **Storage** mode first: it charges only briefly, at low risk. Then try Ready.
5. Watch the first full charges from start to finish, including temperatures.
