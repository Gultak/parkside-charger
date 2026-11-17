# Parkside X20V under-shelf charger, up to 16 slots (ESP32-C6 / ESPHome)

![Assembly preview](docs/img/assembly_rear.png)

The rack screws to the underside of a shelf. Up to 16 Parkside X20V packs slide in from the front
and hang from rails, as they do on a tool. Each slot has its **own CC/CV charger IC**. An
**ESP32-C6 running ESPHome** controls all of them: it charges to a **battery-friendly level**
(92 % "ready", 60 % "storage", 100 % on demand). It reports **presence, charge state,
temperature, internal resistance, estimated capacity, self-discharge and an overall health
verdict** for every slot to Home Assistant.

| | |
|---|---|
| Slots | 1–16 printed modules, 88 mm pitch, one per battery. They **slot into each other** with a full-length sliding dovetail. 16 slots = two rows of 8 (70.4 cm each) |
| Slot board | 72 × 47.5 mm, 4 layers. LTC4162-LAD: 5S Li-ion, I²C-programmable 3.81–4.20 V/cell, 0.1–3.2 A, telemetry and battery-resistance measurement. PCA9554 for switch, LED and bleed resistor. **KiCad design + Gerbers in `electronics/slot-board/`** |
| Controller board | 112 × 64 mm, 4 layers. ESP32-C6 D1 in Dupont sockets, 2 × TCA9548A (16 I²C channels), switched 24 V to two slot chains, 5 V regulator, voltage sensing, buzzer. **KiCad design + Gerbers in `electronics/controller-board/`** |
| Wiring | 24 V **daisy-chained** slot to slot (IN/OUT screw terminals), plus one 4-wire JST-XH I²C cable per slot to the controller. Every cable can be plugged in with the enclosures closed |
| Power | Mean Well **LOP-400-24** open-frame PSU (250 W fanless), built into the controller box in its own mains compartment. The battery-side budget (10 A) is shared across the slots |
| Presence | Microswitch per slot, with the pack's BMS signal (ID contact) and voltage as a fallback |
| Safety | Per-slot fuses on both sides, the pack's BMS signal gates charging, slot NTC window 5–45 °C plus JEITA, charge timeout, fault latching, ambient limit, default-off soft-start bus switch, **70 °C thermal cut-out in the AC line** |
| Estimated cost | about €24 per slot plus about €156 fixed: about €400 for 10 slots, about €545 for 16 ([BOM.md](BOM.md)) |

## Contents

| Path | What |
|---|---|
| `mechanical/parkside_shelf_charger.scad` | Parametric OpenSCAD model: slot module (interlocking), end modules, clip-on bay cover, rail and joint test gauges, controller box |
| `mechanical/stl/` | STLs exported with the measured rail dimensions. Test-fit the gauges first |
| `docs/mechanical.md` | How to measure the pack, test prints, printing, mounting, cabling |
| `electronics/electronics.md` | Architecture, design decisions, pin maps, power budget, safety |
| `electronics/slot-board/` | KiCad 7 project, Gerbers, BOM and pick-and-place for the slot board |
| `electronics/controller-board/` | KiCad 7 project, Gerbers, BOM and pick-and-place for the controller board |
| `electronics/kicadgen/` | The generator that builds both boards from `tools/design.py` + `tools/layout.py` |
| `BOM.md` | Bill of materials with rough prices and vendor links (DigiKey Ireland, Amazon.ie) |
| `esphome/` | ESPHome config + external component (`parkside_charger`, `parkside_slot`) |
| `esphome/tests/sim/` | Host simulation of the charging logic (fake LTC4162 + battery model) |
| `docs/firmware.md` | Charging strategy, entities, LED legend, health heuristics, bring-up |

## Using the ESPHome components

`esphome/parkside-charger.yaml` loads the custom components from the local `esphome/components`
folder. To use them from GitHub instead (for example from your Home Assistant ESPHome add-on),
replace the `external_components` block with:

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/Gultak/parkside-charger
      ref: main
      path: esphome/components
    components: [parkside_charger, parkside_slot]
```

## Build order

1. **Check a pack** (electronics.md §2): confirm which contact reads about 10–12 kΩ to B− (the
   BMS/ID line). Charging on B+/B− is confirmed.
2. **Measure the pack and print the gauges**, then adjust the `.scad` parameters until they fit.
   Print one module.
3. **Order the boards:** one controller board, plus a few slot boards to start.
4. **Bring up** the controller, then one slot, with a lab supply (firmware.md, checklist).
5. Test one complete slot end to end. Then build the rest.

## Open items you need to verify

- **Contact height** (`contact_z`) is still an estimate, and the front end/latch pocket are
  copied from a reference holder. Print
  `gauge.stl` and `end_gauge.stl` and test them on a pack before printing full modules.
- **Board review:** a custom router routed both PCBs automatically. They pass KiCad's DRC with no
  errors, but have a look in KiCad before ordering. Each board's README lists what to check.
- **The LTC4162-L register map and scaling** have been checked against the datasheet (Rev A)
  and the Linux driver. Still compare the voltage and current readings with a meter during
  bring-up, because sense-resistor tolerances apply.
