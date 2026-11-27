# HANDOFF: state of the project, decisions, gotchas

This file is for an agent (or person) picking the project up **without the earlier conversation**.
It is a memory dump: what exists, how to build it, what was decided and why, what bit us, and
what is still open. The user-facing docs (README, `docs/`, `electronics/`, `BOM.md`) are the
reference; this file explains the history and the working conventions around them.

State as of 2026-11-27, commit after `b4aaa7d` (this file and `procurement/tools/` were added in
the same commit).

---

## 1. What this is

An under-shelf charger rack for **Parkside X20V** (Lidl, 20 V / 5S Li-ion) battery packs, for up
to 16 slots, in a hot press (airing cupboard) in Ireland.

- **Slot modules** (3D printed, PETG / PETG V-0): one per battery, screwed under a shelf, packs
  slide in from the front on rails like on a tool. Modules interlock with a sliding dovetail.
  86 mm pitch. Each has its own **slot board** (LTC4162-LAD charger, PCA9554 I/O expander).
- **Controller box** (printed): Mean Well **LOP-300-24** open-frame PSU in a mains compartment,
  plus the **controller board** (ESP32-C6 D1 module, 2 × TCA9548A I²C muxes, 24 V bus switch,
  5 V regulator, buzzer, fan driver, NTC).
- **Firmware**: ESPHome with two external components, `parkside_charger` (hub: power budget,
  interlock, totals) and `parkside_slot` (one per slot). Home Assistant integration.
- Wiring: 24 V daisy-chained slot to slot with pre-made XT30 cables; one 4-wire JST-XH I²C cable
  per slot to the controller.

Repository: **Gultak/parkside-charger** (GitHub), branch `main`. Other repositories that were
attached to the old session, for context only:
- `Gultak/ai-inbox`: has an issue template "Parkside charger task" that routes tasks to this
  repository (changes come back as PRs on `Gultak/parkside-charger`).
- `Gultak/ha-esphome-projects`: the project started there; it was moved out ("Move
  parkside-charger to its own repository"). Nothing to do there.
- `Gultak/esphome-parkside-charger`: attached but not used in the recent work; treat as obsolete
  unless the user says otherwise.

## 2. Working conventions (user preferences)

- **Commit directly to `main` and push.** No pull requests unless the user asks.
- The user is in **Ireland**: DigiKey Ireland (prices in €, incl. VAT), Amazon.ie, Irish mains
  (switched fused spur with flex outlet, BS 1362 fuses, 230 V).
- The user's e-mail address is private: never put it in requests to external services.
- The user iterates in small steps, test-prints parts and reports measurements. When they give
  a measurement, change the parameter, re-export the STL, update the docs, commit, push, report.
- Keep docs in sync with every change (README, `docs/*.md`, `electronics/*.md`, board READMEs,
  `BOM.md`, the DigiKey CSVs, the Google Sheets).
- Answers: plain, concrete, short. The user reads the board images and the KiCad files themselves.
- The user has **KiCad 9.0.6** on their machine.

## 3. Repository map

| Path | What |
|---|---|
| `README.md` | Overview, contents, cost |
| `HANDOFF.md` | This file |
| `BOM.md` | Bill of materials (generated, see §6) with status icons: 🛒 DigiKey, ✅ at hand, 🏭 PCB fab, ⚠️ resolve |
| `procurement/digikey_controller.csv`, `digikey_10_slots.csv`, `digikey_all.csv` | DigiKey BOM-upload CSVs (generated). `digikey_all.csv` merges both with summed quantities |
| `procurement/tools/bom_data.py`, `gen_bom.py` | Source data + generator for `BOM.md` and the CSVs |
| `mechanical/parkside_shelf_charger.scad` | One parametric OpenSCAD file for everything printed. `part = "..."` selects the output |
| `mechanical/stl/` | Exported STLs (re-export after every parameter change) |
| `docs/mechanical.md` | Measuring, test prints, printing, assembly, controller box, mains wiring |
| `docs/firmware.md` | Charging strategy, entities, LED legend, interlock, PSU fan, bring-up |
| `docs/components/parkside_charger.md`, `parkside_slot.md` | ESPHome-style component docs |
| `electronics/electronics.md` | Architecture, decisions, pin maps, power budget, safety |
| `tools/agent-tools/` | Git submodule [Gultak/agent-tools](https://github.com/Gultak/agent-tools), pinned: **our own generator `kicadgen`** (schematic + routed PCB + fab outputs from Python), `pcbtools/boardsig.py` (board comparison) and `bom/bomgen.py`. Shared with homelab-power-supply. Run `git submodule update --init` after cloning |
| `electronics/pcl_lib.py` | The boards' own library for kicadgen (nickname `pcl`): custom symbols and footprints, PCBWay part numbers, render net colours |
| `electronics/slot-board/`, `electronics/controller-board/` | Per board: `tools/design.py` (parts + nets), `tools/layout.py` (placement, pours, labels), generated KiCad project, `fab/` (Gerbers, BOM, PCBWay files), `img/` (layer renders), `drc_report.txt` |
| `esphome/parkside-charger.yaml` | The device config (controller + 16 slots). `slot.yaml` is the per-slot package |
| `esphome/components/parkside_charger/` | C++ for hub **and** slots (`parkside_slot/__init__.py` is the config schema only) |
| `esphome/tests/sim/` | Host simulation of the charging logic with a fake LTC4162 + battery model |

## 4. Environment setup (cloud container)

The container is rebuilt per session. What the work needs:

```bash
# KiCad 9 (the generator now targets KiCad 9; Ubuntu 24.04 ships 7.0.11). The PPA has 9.0.9.
curl -sS "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x245D5502FAD7A805" | gpg --dearmor > /etc/apt/trusted.gpg.d/kicad.gpg
echo "deb https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu noble main" > /etc/apt/sources.list.d/kicad9.list
apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends kicad kicad-footprints kicad-symbols
mkdir -p ~/.config/kicad/9.0 && cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table ~/.config/kicad/9.0/
git submodule update --init      # tools/agent-tools (kicadgen, bomgen)
```

`tools/agent-tools/env/setup-kicad9.sh` does all of this (plus `librsvg2-bin`); the project's
cloud environment runs the same script.

- Skip `kicad-packages3d` (several GB, not needed).
- Without the global lib tables, `kicad-cli pcb drc` reports every footprint as "library not
  configured".
- OpenSCAD (`openscad`) runs headless via `xvfb-run -a openscad ...`. It was already installed in
  the earlier container; if missing, use `apt-get install openscad xvfb`.
- Python for kicadgen: **`/usr/bin/python3`** (system Python, where `pcbnew` lives). Also needs
  `numpy`, `Pillow`, `openpyxl` (PCBWay xlsx).
- Image rendering of the silkscreen uses Node + the preinstalled Playwright Chromium
  (`render.py`, `NODE_PATH=$(npm root -g)`).
- ESPHome: `pip install esphome` in a venv, then `esphome config esphome/parkside-charger.yaml`.
  It was validated with ESPHome 2026.10.2. A full ESP32-C6 build never ran in the cloud (the
  ESP-IDF download host was blocked), so the first real firmware build happens on the user's
  machine.
- Simulator: see §7.

## 5. Building the boards (kicadgen)

kicadgen lives in the `tools/agent-tools` submodule (Gultak/agent-tools). Each board's
`tools/build.py` puts it on `sys.path` and passes `electronics/pcl_lib.py` as the project
library. Change the generator in agent-tools, push it there, then bump the submodule here
(`git -C tools/agent-tools pull origin main`, commit `tools/agent-tools`). After a generator
change, compare the rebuilt boards with the committed ones:
`/usr/bin/python3 tools/agent-tools/pcbtools/boardsig.py old.kicad_pcb new.kicad_pcb`. The
router is deterministic; only fill areas where two same-priority pours touch may move by a
fraction of a mm² (`--no-fill` hides that).

```bash
cd electronics/slot-board && /usr/bin/python3 tools/build.py          # all steps: sch pcb fab img
cd electronics/controller-board && /usr/bin/python3 tools/build.py
/usr/bin/python3 tools/build.py img                                     # only some steps: sch | pcb | fab | img
```

- `sch`: writes the schematic and the custom symbol and footprint libraries (`pcl.kicad_sym`,
  `pcl.pretty/`). It then exports the netlist with kicad-cli and **checks it against design.py**.
- `pcb`: places the parts and routes them with our own A* grid router. Routing runs in child
  processes; nets that fail are "promoted" (routed first) and the board is retried, up to 6
  attempts. It fills the zones and runs DRC through `kicad-cli pcb drc`.
  - **Time:** slot board about 5 min, controller about 20 min.
  - **Concurrency:** both boards can build in parallel in the background.
- `fab`: Gerbers + drill zip, `*_bom.csv` (order list without `NOT_IN_ORDER_BOM`),
  `*_bom_all.csv`, CPL, and PCBWay assembly files (`fab/pcbway/*.xlsx`; at-hand parts are DNP).
  It also checks that the PCB pads match design.py ("PCB vs design: OK").
- `img`: layer renders and the top silkscreen view for the READMEs.
- **Quick placement preview (no routing):** set `KICADGEN_PLACE_ONLY=<out.kicad_pcb>`. `pcb.build()`
  then places parts, references and labels and saves without routing. Render it with
  `kicad-cli pcb export svg --layers F.Cu,F.Mask,F.Silkscreen,Edge.Cuts --exclude-drawing-sheet
  --page-size-mode 2` and screenshot it with Playwright. Use this to iterate on placement and
  silkscreen in seconds instead of 20 minutes.
- **Check exactly as KiCad does:** `kicad-cli pcb drc --severity-all --schematic-parity -o r.rpt board.kicad_pcb`.
  - Must run in the board folder with the real file name, or the project's `pcl` library table
    isn't loaded.
  - **Current result:**
    - Controller: 0 violations, 0 unconnected, 0 parity issues.
    - Slot board: 0 parity issues, only 8 `silk_edge_clearance` warnings (the XT30 bodies of
      J1/J6 overhang the rear edge on purpose).
- Reference designators are placed automatically (`place_references`) next to each part where
  they overlap nothing (courtyards, labels, the part's own silkscreen). If no spot is free, the
  reference goes to F.Fab only. Currently that happens for J1, J108 and J109 on the controller.

### Board facts

**Slot board** (72 × 47.5 mm, 4 layers, rev C):
- **Main ICs:**
  - LTC4162-LAD (I²C 0x68)
  - PCA9554 @0x20, IO pins:
    - IO0 microswitch
    - IO1/2/3 LED R/G/B
    - IO4 bleed MOSFET
    - IO5 SMBALERT
    - IO6 BMS-fault comparator
    - IO7 spare
  - TLV7031 comparator on the pack ID contact (pull-up 10 k, 100 k / 4.7 µF filter, 4.55 V
    reference)
- **Connectors:**
  - J1 XT30PW-M (24 V IN) and J6 XT30PW-F (24 V OUT), in one row at y 36.4. Pin 1 is GND and
    pin 2 is +24 V on every XT30.
  - J3 3-pole 5.0 mm screw terminal (ID, GND, B+)
  - J2 JST-XH 4-pin I²C (SCL SDA GND 5V)
  - J4 2-pin header (switch)
  - J5 4-pin header for the Inolux INL-5TB4URGB25 RGB LED: 1 B, 2 R, 3 GND (common cathode), 4 G
- **Other parts:**
  - L1 Vishay IHLP-2525CZ 6.8 µH
  - Bleed resistors R13/R14: 100 Ω 2 W axial, mounted 2–3 mm above the board
  - Pack-ID circuit (R15–R18, C15, C16, U4): front-left corner next to J3's ID terminal
  - Screwdriver hole at (40.5, 25), which must match `pcb_hole` in the SCAD
- **Mechanical fit:** the board's long edges ride in card guides, so parts keep 2 mm away from
  them (`EDGE_KEEP`).

**Controller board** (112 × 64 mm, 4 layers, rev C):
- **ESP32-C6 D1 module** (xyzroe, D1-mini form factor) in two 1×8 female sockets.
  - Placement: header centre ESP_X 56, ESP_Y 13.9, rotated 180°. Its USB-C mouth sits at the box
    wall's inside face; the module overhangs the board edge by about 4 mm (`OVERHANG {"U2"}`).
  - GPIO map:
    - I²C SDA/SCL: GPIO22/23
    - Mux reset: GPIO4
    - Bus switch: GPIO19
    - Buzzer: GPIO18
    - PSU voltage / bus voltage ADC: GPIO0 / GPIO1
    - NTC: GPIO5
    - Fan PWM / tach: GPIO6 / GPIO7
  - The D1 only breaks out GPIO 0, 1, 4–7, 16–19, 22, 23.
- **I²C muxes:** 2 × TCA9548A, 0x70 (slots 1–8) and 0x71 (slots 9–16), with 4.7 k pull-ups to
  5V_SLOT (they double as level shifting).
- **Connectors:**
  - J1 JST B6P-VH: PSU in, pins 1–3 +V and 4–6 −V, the same pinout as the LOP-300's CN2 so a
    1:1 VH cable works.
  - J2/J3 XT30UPB-F vertical: OUT A / OUT B (two slot chains). They were moved 1 mm right for
    silkscreen clearance.
  - J7 4-pin PC fan header
  - J9 2-pin JST PH for +12 V aux from the PSU's CN101 (1 +12 V, 2 GND), wired 1:1
  - J8 2-pin header for the power LED (330 Ω from 5 V)
  - J6 7-pin expansion header
- **Power path:** 10 A mini blade fuse, SMBJ26A TVS, AOD4185 P-MOSFET bus switch with soft start
  (default off), TSR 1-2450 5 V regulator.
- **Enclosure NTC:** RT1, 10 k B3380, on GPIO5.

## 6. BOM and procurement

- **Source of truth for parts and prices:** the user's two Google Sheets in Drive, edited by the
  user with vendor columns.
  - **Controller:** spreadsheet `1bC-LlEoS5R09PtsnCYN4IFV48Wqbj8HMM9mQMDWpWPo`, tab "Controller",
    sheetId 1549666168.
  - **10 Slots:** spreadsheet `15q_BUGZPDNbwaG7l6sSY0JzlGfHPwvgiez01Ibf3i58`, tab "10 Slots",
    sheetId 792412737.
  - **Columns A–E are ours:** Qty, Part, Manufacturer, Part number, Include (checkbox). F–Y are
    the user's vendor columns (DigiKey IE, Farnell IE, RS, Mouser, Conrad: part #, stock, price
    €, link). **Never overwrite F–Y** except the DigiKey columns of a row whose part we change;
    say so when you do.
  - **Summary rows** at the bottom use formulas over the item rows. Insert new rows *above the
    last item row* (insertDimension with inheritFromBefore) so the ranges expand. Deleting rows
    is fine for parts that are no longer used.
  - **Ticked (Include) = buy at DigiKey; unticked = at hand.** The DigiKey part # column is the
    real part to buy, and may be an equivalent of the design's part number.
- **`procurement/tools/bom_data.py`** mirrors the sheets as Python tuples:
  `(qty, part, manufacturer, part number, ticked, DigiKey #, € line total, refs, issue)`.
  - **Workflow:** read the sheets, update `bom_data.py`, run
    `python3 procurement/tools/gen_bom.py`, which writes `BOM.md` and the three CSVs (table and
    CSV formatting from `tools/agent-tools/bom/bomgen.py`). Check that
    the € totals match the sheets' subtotal rows (currently €103.18 controller, €229.50 for 10
    slots).
- **Board-level BOM vs order BOM:** each board's `design.py` has `NOT_IN_ORDER_BOM` (parts at hand
  or mounting holes). `electronics/pcl_lib.py` (`MPN`, `PCBWAY_NOTES`) has the MPN map for the PCBWay assembly files.
- **Parts at hand** (don't order):
  - Wire, mechanics, tools:
    - PETG / PETG V-0
    - 1.5 mm² blue/brown wire, 0.75 mm² wire
    - 4-core 22 AWG cable
    - crimping tool
    - wood screws
    - M3 heat-set inserts and screws
  - Connectors:
    - B6P-VH header, VH housings and crimps
    - 6.3 mm spade tabs with locking lance (about 50)
    - Dupont headers and cables
    - Wago 221 lever connectors
    - XT30UPB-F and XT30PW-M/F (Amazon packs), pre-made XT30 extension cables (16 AWG)
    - 3-pole 5 mm screw terminals
  - Modules and other parts:
    - ESP32-C6 D1 module + its headers
    - 90/92 mm 12 V 4-pin PWM fan (with its own screws)
    - switched fused spur, BS 1362 fuses, 3-core cable, ring lugs, star washer, green/yellow wire
- **Chosen DigiKey equivalents** (examples; the sheets have all):
  - TI TCA9554PWR for the PCA9554
  - NXP PCA9548APW,118 for the TCA9548A
  - Bel Fuse C1Q 5 for the 5 A slot fuses
  - Nichicon UUD1V470MCL1GS 47 µF (electrolytic, not hybrid polymer: fine for input bulk)
  - Murata GRM188R6YA475KE15D 4.7 µF 35 V X5R
  - Honeywell 2455R--00820195 70 °C NC thermostat as the "KSD301" thermal cut-out
  - JST SXH-001T-P0.6N XH crimp: 26–22 AWG, insulation OD 1.3–1.9 mm; the user still has to
    check their cable's core insulation is ≥ 1.3 mm
  - JST ASPHSPH24K203 pre-crimped PH leads (2×) + 2× PHR-2 for the fan's +12 V lead, because
    the loose SPH-002T-P0.5S contacts were out of stock
- **Claude Sheets artifacts** "Parkside Charger – Controller Parts" / "– 10 Slot Parts" exist
  from early on, but the **Drive sheets are the live ones**.

## 7. Firmware

- `esphome/parkside-charger.yaml`:
  - Substitutions: `room_temperature_entity: sensor.hotpress_temperature_sensor_temperature`,
    `budget_no_fan: "7.0"`, `budget_with_fan: "10.0"`.
  - `esp32-c6-devkitc-1`, esp-idf, 4 MB.
- **Charging targets:** "ready" 92 %, "storage" 60 % (after `storage_after_days`, default 14),
  100 % on demand with a balancing tail at 4.20 V/cell (pack bleeders need a low-current tail).
  Per-slot modes. JEITA and an NTC window of 5–45 °C on the pack.
- **Power budget:** the hub shares `max_total_current` (battery side) between slots every 2 s.
  Priority goes to slots asked to charge to 100 %, then the emptiest packs. Allocations are in
  0.1 A steps, minimum 0.3 A, and constant-voltage slots reserve only their draw + 0.3 A.
  - LOP-300: 7 A by convection; 10 A only after the fan tach confirms 15 s of spin.
  - Fan fault (< 300 rpm for 10 s while switched on) drops the budget back to 7 A at once and
    sounds the buzzer.
- **Fan curve:** off below 100 W and 35 °C, then 30–100 % over 100–300 W or 35–45 °C. ledc on
  GPIO6 (inverted, 25 kHz), pulse_counter on GPIO7 (×0.5).
- **Safety interlock** (`set_interlock(active, reason)`, independent of the enable switch, fails
  safe at boot) stops charging and switches the 24 V bus off while:
  - A. Enclosure NTC above 45 °C (3 °C hysteresis) or invalid.
  - B. Room temperature from Home Assistant above 36 °C (2 °C hysteresis) or unknown.
  - C. Home Assistant not connected for longer than 120 s.

  Switch "allow without HA" overrides C. The hub's own `max_ambient_temperature: 50` is a backstop.
- **Enclosure temperature:** adc GPIO5 → resistance (DOWNSTREAM, 10 k, 3.3 V) → ntc (B 3380),
  id `enclosure_temp`.
- **Simulator:**
  ```bash
  cd esphome/tests/sim && g++ -std=gnu++20 -O2 -Istubs -I../../components sim.cpp ../../components/parkside_charger/parkside_charger.cpp -o sim && ./sim
  ```
  7 scenarios, **ALL PASSED** on 2026-11-27. Add `v` for a log. Stubs for ESPHome headers are in
  `tests/sim/stubs/`; when the component uses a new ESPHome API, extend the stubs.

## 8. Mechanics (OpenSCAD)

```bash
cd mechanical
xvfb-run -a openscad -D 'part="controller"' -o stl/controller.stl parkside_shelf_charger.scad
xvfb-run -a openscad -D 'part="controller_lid"' -o stl/controller_lid.stl parkside_shelf_charger.scad
xvfb-run -a openscad -D 'part="controller_lid_check"' -o /tmp/x.stl parkside_shelf_charger.scad   # must report "Current top level object is empty"
```

**Parts:**
- Slot side: `slot`, `slot_cover`, `gauge`, `end_gauge`, `joint_gauge`
- Controller box: `controller`, `controller_lid`, `controller_preview`, `controller_closed`,
  `controller_lid_check`
- Views: `assembly`, `single`, sections

**Measured and test-fitted values** (from the user's prints; don't change without a new
measurement):
- **Rail:** `chan_w` 46.9 (a narrower 46.8 was tried and reverted), `lip_in` 4.2, `lip_t` 5.0,
  `lip_gap` 5.1, `rail_len` 64.
- **Dovetail:** `jt_clear` 0.15 per side (0.2 printed loose; "the gap can easily be 0.1 mm
  smaller").
- **Contacts:** 6.3 mm FASTON-style male crimp tabs with a locking lance, pushed tip first into
  pockets in the contact block.
  - Tab: `tab_w` 6.2, `tab_t` 0.7, `tab_flat` 14, lance 9–13 mm standing 2 mm off the blade.
  - Placement: `contact_x` [-12, -4, 4, 12] (seen from the front: +, ID, T, −; T unused),
    `contact_z` 5.5, `contact_len` 6.5.
  - `ear_w` 8.0 is not measured (CHECK).
- **Contact block:** `cblock_ch` 0.8 mm chamfer (the original charger has a square block; 4 mm was
  too much).
- **Slot pitch** 86 mm (packs measured ≤ 85 mm): 8 slots = 68.8 cm. The user has 69.4 cm per row.
- **Slot module:** 132 mm deep (nose 9 to rear 141.1), 44 mm tall.

**Controller box** (124.8 × 179 × 50.4 mm with LOP-300 + gland):
- **Compartments:** low-voltage compartment (board on 8 mm standoffs) and mains compartment (PSU
  on 6 mm standoffs) behind a closed partition. The PSU leads pass through a 14 × 10 mm slot at
  the top of the partition.
- **Mains entry:** hard-wired through an M20 gland (`mains_entry "gland"`, `mains_bay` 25) into
  Wago 221s, with the KSD301 70 °C cut-out in L. Earth goes via a Wago and a short green/yellow
  lead with a ring lug + star washer to the PSU's earth-marked mounting hole. No ferrules (solid
  wire into Wagos).
- **Lid:** snap-in, no screws (`lid_snap`, `lid_mains_screws = false`).
  - Six tapered tabs (3.6 mm at the root, 1.8 mm at the hook): front −46/38, back −30/30, one in
    each mains-side wall.
  - The hooks catch in **blind pockets** with a 1 mm outer skin (`snap_skin`; 0 = through
    windows).
  - To open: push a screwdriver down through 8 mm pry slots in the lid edge onto a 45° wall
    chamfer.
- **Cable notches:** side walls for the slot cables, front wall for the expansion header. Lid fins
  close them down to a 5 mm slot (`cable_gap`); the fins slide in tongue-and-groove
  (`fin_groove`).
- **Front wall:**
  - USB-C hole 9.6 × 4 with a 13.5 × 7.5 plug pocket from outside, 0.8 mm skin.
  - `usb_h` 14.2: 8.5 socket + 2.5 pin spacer + 1.6 module + 1.6; confirmed by the user (USB-C
    centred, flush with the module edge, directly on the 1.6 mm board).
  - Power LED: Lumex SSI-LXMP059ID, centred above the USB-C at `led_pos` [0, 37] (moved from the
    left, where its inside recess hit the snap pocket).
- **Lid fan:** 90/92 mm fan over the PSU with a finger-safe grille, held by the **fan's own
  self-tapping screws** through 5.2 mm holes (`fan_hole_d`). No M4 screws.
- **Vents:** in the mains-side walls, kept clear of the snap pockets.

## 9. Decisions and why

**Mechanics**
- **Contacts: FASTON crimp tabs** instead of brass strip or plate. The user has about 50
  locking-lance tabs. Pocket geometry from their measurements.
- **Dovetail clearance 0.15 per side** from gauge prints. The user clarified the clearance meant
  the dovetail, not the rail channel; the channel narrowing was reverted.
- **86 mm pitch**, so 8 fit in the user's 69.4 cm.
- **Snap-in lid** with tapered tabs: the user asked for no screws. Tapering stops the tabs
  snapping off at the root. Pry slots + chamfers make it removable without breaking anything.
- **Blind snap pockets** for a smooth outside. Prying through the lid slots replaced pressing the
  hooks from outside.
- **USB-C exposed** through a small hole with the module moved to the wall, rather than a big
  opening.
- **Small cable openings:** notches with lid fins leaving 5 mm, rather than big openings.
- **LED in the front wall,** opposite the mains entry, where the user can see it. It is not in the
  lid.

**Power and safety**
- **Hard-wired mains** (it goes into the hot press): switched fused spur → flex → M20 gland →
  Wagos. An IEC inlet was considered and dropped.
- **No heat alarm:** the user's HA temperature sensor in the hot press covers it, and the firmware
  interlock uses it.
- **Earth kept (Class I):** the open-frame PSU's mounting hole is meant for PE. The user asked
  about Class II; plastic box or not, the PSU wants earth.
- **LOP-300-24** (cheaper) instead of LOP-400. Budget 7 A, or 10 A with the fan. The fan blows
  onto the PSU from above (not the datasheet direction), so stay well under 300 W.
- **Fan:** the user's 90 mm 4-pin PWM fan on a standard PC header; +12 V from the PSU's own aux
  fan output.

**Wiring and connectors**
- **XT30 for the 24 V chain:** polarised and gendered, so a cable can't be plugged in the wrong
  way. The user prefers "can't plug in wrong" over "doesn't cross".
  - Same polarity convention on every connector.
  - Pre-made 16 AWG male-female cables: 20 cm between slots, 30 cm controller to first slot.
- **5 mm screw terminal** for the battery wires: the user has many.
- **2.54 mm headers + Dupont cables** for switch and LED: the user has them.
- **JST PH for J9** (+12 V aux), so a 1:1 lead with pre-crimped wires works without crimping.
  Option chosen over cutting the lead and crimping Dupont.

**Electronics**
- **On-board NTC** (RT1) for the enclosure temperature. The SHT21 header and Qwiic connector were
  removed. The user's sensor turned out to be a BH1750 light sensor: ignore it.
- **4 layers** (asked "is 2 enough?"): the LTC4162's QFN with thermal vias, Kelvin sense lines,
  the hot loop and the 16-channel I²C fan-out route much more cleanly with two inner ground
  planes, and the price difference is small.
- **Slot board placement:** the pack-ID circuit moved to the free front-left area so the I²C
  corner's silkscreen is readable.

**Tooling**
- **KiCad 9:** the user runs 9.0.6. Boards generated with KiCad 7 libraries made KiCad 9 flag
  footprints as different from its library.
- **Footprints linked to symbols** via stable UUIDs (uuid5 of ROOT_UUID + reference). Without the
  link, KiCad's parity check reported "footprint errors".

## 10. Gotchas (things that bit us)

**KiCad generator (kicadgen)**
- **KiCad 9 Python API changes:**
  - `NET_SETTINGS.GetDefaultNetclass()` replaces `m_DefaultNetClass`.
  - Pads: `GetParentFootprint()` instead of `GetParent()`.
  - `PAD.GetEffectivePolygon(layer)` and `PCB_VIA.GetWidth(layer)` need a layer.
  - `WriteDRCReport` and `EDA_UNITS_MILLIMETRES` are gone, so DRC goes through `kicad-cli`.
  - Footprint text is `PCB_TEXT`/`PCB_FIELD`, not `FP_TEXT`.
  - **Text angles are absolute in KiCad 8+**, relative to the footprint in 7. The generator
    branches on the version.
  - The code keeps KiCad 7 fallbacks where cheap.
- **KiCad 9 libraries:**
  - Symbol files are tab-indented and multi-line, and the schematic extractor collapses the
    whitespace.
  - `Q_NMOS_GSD` / `Q_PMOS_GDS` moved from `Device` to `Transistor_FET`.
  - The schematic is still written with KiCad 7 header syntax; KiCad 9 reads it fine.
- **Filling zones on a board built in memory** crashes pcbnew, so save, reload, then fill
  (already done).
- **Parity:** unused symbol pins get nets named `unconnected-(REF-PIN-PadN)` in KiCad's netlist.
  The board pads must carry them (`assign_unconnected_nets`), or parity reports "Pad missing net
  given by schematic". Mounting-hole footprints are excluded from the BOM, so their schematic
  symbols must be too (`in_bom no`).
- **Text that flips when rotated:** left/right-justified footprint text swaps sides on a 180°
  rotation (the ESP socket's pin labels landed on the pads). Use centred text in generated
  footprints.
- **"Compare footprint with library"** always lists reference and value differences (position,
  size, hidden value). These are per-instance and expected, not errors.
- **Placement check:** our own bbox courtyard check flags F1/Q1 on the controller; KiCad's DRC
  is clean there. Harmless.
- **Board geometry:** the controller power band was shifted to make room for J1 (VH). Male XT30
  pegs near the slot-board edge needed the pads at y 36.4.
- **`kicad-cli pcb drc`** loads the project's own `pcl` library table only when the board has
  the real project file name, so test copies show a spurious "library pcl not configured".

**Mechanics**
- **`controller_lid_check`** must render empty, and the lid is raised by 0.01 in that check
  (coplanar contact would otherwise count). After any box or lid change, run it.
- **Snap pockets vs other cut-outs:** they collided with the upper vent row (the vents were
  lowered) and with the LED recess (the LED was moved). Check new cut-outs against
  `ctl_snaps()`.

**Procurement and sheets**
- **Sheets** can only be edited after the user connects the Google Sheets connector.
- **JST XH crimps:** SXH-001T-P0.6N is the low-insertion-force variant and needs insulation
  ≥ 1.3 mm. JST SPH contacts: 24–30 AWG only (22 AWG won't fit PH).
- **Marketplace sellers on DigiKey:** avoid them for parts (the user prefers stock shipped by
  DigiKey).

**Firmware and environment**
- **ESPHome YAML edits:** match anchors carefully (e.g. `"\nsensor:\n"`); `sensor:` appears more
  than once.
- **Cloud container:** it doesn't persist installs (KiCad 9, the ESPHome venv). Reinstall per
  session, or ask the user about saving a setup script in a dedicated environment. The default
  environment has unrestricted network, and a dedicated one would restrict hosts.

## 11. Open items / next steps

- **User to measure/check:**
  - Core insulation OD of the 4-core 22 AWG slot cable (≥ 1.3 mm for SXH-001T-P0.6N, else go back
    to SXH-001T-P0.6).
  - `ear_w` of the spade tabs.
  - `led_cut` / `led_panel_t` against the real Lumex LED.
  - Fan screw diameter (lid holes assume about 5 mm).
- **User to verify in KiCad 9.0.6** that the footprint errors are gone after
  `b4aaa7d`. If any remain, ask for 2–3 of the messages. The agent's container runs 9.0.9.
- **Test prints still pending:** contact-block end gauge and dovetail gauges with the new
  clearances.
- **First real firmware build and bring-up** on the user's machine (see `docs/firmware.md`,
  *Bring-up checklist*). A current-limited lab supply for the first slot board.
- **Human review of the routing** (both board READMEs list what to look at; slot board: the
  comparator output trace across the board, and the I²C pair).
- **Ordering:**
  - PCBs: JLCPCB or PCBWay. PCBWay assembly files are in `fab/pcbway/`; stencil explanation
    given earlier: a framework stencil with apertures from the paste layer.
  - DigiKey: upload `procurement/digikey_all.csv`.

## 12. How the previous session worked (useful habits)

- After a change: rebuild what's affected, check (DRC with `--schematic-parity`, or
  `controller_lid_check`, or the simulator), update docs and BOM, commit with a descriptive
  message, push, report in a few lines.
- For silkscreen or placement work: use the `KICADGEN_PLACE_ONLY` preview + a screenshot, iterate,
  then run one full build.
- Render pictures (OpenSCAD `--imgsize ... --camera ...`, board PNGs) and look at them before
  claiming a fit is fine.
