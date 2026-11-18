# Controller board (KiCad 7)

The controller board is the hub of the charger. It holds the **xyzroe ESP32-C6 D1** in female Dupont headers,
switches the 24 V for the slot chains, and runs one I²C channel to each of up to **16 slots**.
**112 × 64 mm (rev C), 4 layers** (In1/In2 = GND), all parts on one side.

| Top (parts side) with silkscreen | Bottom copper |
|---|---|
| ![Top side with silkscreen](img/pcb_top_silkscreen.png) | ![Bottom copper, coloured by net](img/pcb_bottom.png) |
| **Inner layer 1** (In1) | **Inner layer 2** (In2) |
| ![Inner layer 1](img/pcb_inner1.png) | ![Inner layer 2](img/pcb_inner2.png) |

**Why 4 layers?** This board has no switching converter (the 5 V regulator is a module), so
2 layers would do. It uses 4 because the 32 slot I²C lines fan out from two TSSOP muxes on a
compact board: with GND planes inside, they route on the outer layers without stitching a
ground pour around them, and the 24 V band stays separate. The extra cost is small.

| File | |
|---|---|
| `controller_board.kicad_pro / .kicad_sch / .kicad_pcb` | KiCad 7 project |
| `pcl.kicad_sym`, `pcl.pretty/` | Custom symbols and the ESP32-C6 D1 socket footprint (holes from the module's own drill file) |
| `controller_board_schematic.pdf` | Schematic |
| `fab/controller_board_gerbers.zip`, `fab/*_bom.csv`, `fab/*_cpl.csv` | Gerbers, BOM and pick-and-place positions |
| `drc_report.txt` | KiCad DRC result |
| `tools/design.py`, `tools/layout.py` | Source: **edit these, then run `/usr/bin/python3 tools/build.py`** |

## Layout and connectors

| Where | What |
|---|---|
| Top edge, centre | **ESP32-C6 D1** in 2 × 1×8 female Dupont headers (holes 1.0 mm, rows 22.86 mm apart). The USB-C faces the edge for flashing. The antenna points into the board, and the board has **no copper on any layer** below it |
| Beside the module | Left: **J8** power LED (2-pin), **J5** Qwiic, **J4** SHT21 breakout (3V3 GND SCL SDA, 2.54 mm), the I²C pull-ups and the buzzer. Right: **J6** expansion (3V3 GND IO5 IO6 IO7 TX RX, vertical), the voltage dividers, **J7** 4-pin PC fan header with its PWM driver, and **J9**, the +12 V input from the PSU's fan connector |
| Left / right edge | **J101–J108**: slots 1–8. **J109–J116**: slots 9–16, at a 7 mm pitch. All are JST-XH 4-pin, `5V GND SDA SCL`, the same order as the slot board's J2, so cables are wired 1:1 |
| Bottom edge | **J1** 24 V from the PSU (JST B6P-VH, pins 1-3 +V, 4-6 −V, as on the LOP-300 output) → **10 A mini blade fuse** → TVS → AOD4185 bus switch (soft start, GPIO19) → **J2 OUT A** and **J3 OUT B** (vertical XT30 females, two slot daisy chains). Above OUT B: the **TSR 1-2450** 5 V regulator and a 0.5 A PTC for the slot 5 V rail |
| Between module and connectors | 2 × TCA9548A (0x70 for slots 1–8, 0x71 for 9–16), rotated so each pin row faces its connectors, plus 8 × 4.7 kΩ pull-up arrays to 5V_SLOT |
| Corners | 4 × M3 mounting holes |

The 24 V input, the switched 24 V, and the PSU-to-switch section are pours on both outer layers
(fuse limit 10 A).

## Assembly notes

- **ESP socket:** solder two 1×8 female Dupont headers (2.54 mm pin sockets) into the U2
  position. Solder male pin headers to the ESP32-C6 D1 (it usually ships with them). Plug the
  module in with the USB towards the board edge.
- The silkscreen next to the socket holes shows the module's pin names, so you can check the
  orientation before plugging it in.
- **TSR 1-2450:** fit it upright (SIP-3). The footprint also takes a RECOM R-78E5.0-1.0.

## Before ordering: check these

1. **Review the routing in KiCad.** The custom router routed this board automatically, and
   the KiCad DRC shows **no errors or unconnected items**. What's left: silkscreen cosmetics, one
   0.3 mm dangling +3V3 stub (you can delete it), and `lib_footprint_issues`, which only appears
   because the generator runs without the global library table.
2. Standard 2.54 mm female headers fit the 1.0 mm holes; no special parts needed.
3. **Power connectors:** J1 (VH, from the PSU through the partition notch) and the vertical XT30
   females J2/J3 take their plugs from above; the chain cables then run along the cable channel
   to the side-wall notches. The box is 48 mm tall inside to leave room for the XT30 plugs.
