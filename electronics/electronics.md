# Electronics

## 1. System overview

```
 230 V AC ──[IEC inlet, switch, 2 A fuse]──[KSD301 70 °C thermal cut-out, NC]──► Mean Well LRS-200-24 (trim to 24.5 V)
                                                                                     │ 24 V
                                                         ┌───────────────────────────┴──────────────── MAIN BOARD ───┐
                                                         │  F1 10 A ── always-on ──► 24→5 V buck ─┬─► ESP32-C6 (5V pin)│
                                                         │                                        └─► polyfuse ─► "5V_SLOT"│
                                                         │  F1 ──► Q1 P-MOSFET bus switch (GPIO21, soft-start) ──► 24 V BUS
                                                         │  ESP32-C6 GPIO22/23 (I2C, 100 kHz) ──► TCA9548A @0x70 ch0..7  │
                                                         │                                   └──► TCA9548A @0x71 ch0..1  │
                                                         │                                   └──► SHT40 @0x44 (enclosure)│
                                                         │  GPIO20 ──► buzzer                                            │
                                                         └──────┬──────────────────────────┬────────────────────────────┘
                                24 V BUS: 2 × 2.5 mm², Wago 221 tap per slot │             │ 10 × 4-wire cable (5V, GND, SDA, SCL)
                           ┌──────────────┬──────────────┬──────── … ───────┘             │  one per slot, star topology
                           ▼              ▼              ▼                                 ▼
                     SLOT BOARD 1   SLOT BOARD 2   …  SLOT BOARD 10   (each: LTC4162-L charger @0x68 + PCA9554 @0x20)
                           │
                     Parkside battery: B+, B−, T (NTC)
```

**Why one charger IC per slot, and why the LTC4162-L?**

- Each pack gets real CC/CV charging with its own current and voltage target. No battery waits for
  a shared charger, and each pack has its own protection.
- The LTC4162-L sets its charge voltage **by I²C**, from 3.8125 V to 4.2 V per cell in 12.5 mV
  steps. Charging to a storage level or to 90 % therefore needs no hardware change.
- It reports battery voltage, charge current, input V/I, die temperature and NTC voltage over
  telemetry. It also measures **battery series resistance (BSR)**, which is the main health
  metric used here.
- It works with 1–8 cells (5 cells for X20V), takes inputs up to 35 V and charges at up to
  3.2 A with integrated switches. JEITA temperature control is built in.
- Its I²C address is fixed (0x68). Every slot therefore gets its own TCA9548A channel. As a side
  effect, all ten slot boards are identical and any I²C wiring fault stays within one slot.

## 2. Parkside X20V battery interface: check this first

X20V packs are 5S Li-ion: 18 V nominal, **21.0 V charge voltage**, about 15 V empty. Before you
build ten boards, check on one pack:

1. **Identify the contacts.** B+/B− show the pack voltage. The **T** contact reads about **10 kΩ to B−
   at 25 °C**, and the value falls when you warm the pack in your hand. That contact is the NTC.
   Some packs have another signal contact (data/ID). Leave it unconnected.
2. **Measure the NTC beta.** Read R at room temperature and again after 30 min in the fridge, then
   compute B = ln(R1/R2) / (1/T1 − 1/T2), with T in kelvin. Enter the result as `ntc_beta`
   (default 3435).
3. **Check that the pack accepts charge on B+/B−.** Use a lab supply set to 21.0 V / 0.5 A for a
   few minutes. Packs with "smart" charge enables are rare in the X20V line, but newer
   "Performance" packs should be checked.
4. Measure the blade/slot geometry for the 3D model (see `docs/mechanical.md`).

## 3. Slot board (×10), about 72 × 60 mm, 2 layers, 2 oz copper recommended

The board slides into the card guides of the printed bay. Components go on the top side. The
connectors face the rear lid.

### 3.1 Charger: LTC4162EUFD-LAD#PBF (I²C-adjustable version)

Order the **-LAD** version. The -L40, -L41 and -L42 versions charge to a fixed 4.0/4.1/4.2 V,
which breaks the storage and ready modes. The -xxM versions run MPPT by default. The firmware
reads the chemistry code and refuses to charge with a non-Li-ion variant.

Build the **typical application circuit from the LTC4162-L datasheet** (front page, plus
"Applications Information"). Better still, copy the schematic and layout of the
**DC2038A demo board**, whose design files are on analog.com. A buck converter at 3 A only works
with a good layout, so reuse the proven one. Make these choices:

| Item | Value | Notes |
|---|---|---|
| Cell count pins | **CELLS1 = VCC2P5, CELLS0 = VCC2P5** → 5 cells (datasheet Table 5) | Firmware reads `cell_count` back and blocks charging on a mismatch. It reads 0 while the charger isn't running, which is normal |
| R_SNSB (battery current) | **10 mΩ**, 1 %, ≥ 0.5 W, 1206/2512 | 0.1 A steps, max 3.2 A. Firmware default limit is 1.5 A per slot |
| R_SNSI (input current) | **10 mΩ**, 1 % | Firmware limits input to 3 A |
| RT | **63.4 kΩ** 1 % | 1.5 MHz switching frequency (f = 94 / RT[kΩ]) |
| Inductor | **6.8 µH**, I_sat ≥ 4.5 A, low DCR, shielded | Datasheet formula: L = 0.3 × V_IN(max) / f = 0.3 × 25 V / 1.5 MHz = 5 µH minimum. 6.8 µH is also what the datasheet's application circuits use. e.g. Coilcraft XAL6060-682 or Würth WE-XHMI |
| BOOST capacitor | 22 nF, ≥ 6.3 V, X7R | |
| Input FET (INFET) | **N-channel** MOSFET, ≥ 40 V, per datasheet "INFET and BATFET MOSFET Selection" | Blocks back-feed from the battery into the 24 V bus |
| Battery FET (BATFET) | **N-channel** MOSFET, ≥ 30 V, low R_DS(on) | Same section of the datasheet |
| NTCBIAS → NTC | **10 kΩ 0.1 %** bias to the pack's T contact | Firmware converts using `ntc_bias_resistor`, `ntc_r25`, `ntc_beta` |
| DVCC (I²C supply) | **5V_SLOT** | Datasheet: DVCC 1.8–5.5 V operating, 5.5 V absolute maximum, and SDA/SCL must stay ≤ DVCC. A 5 V rail (±5 %) with the slot bus pulled up to the same rail is within spec. Don't use a buck that overshoots above 5.5 V |
| SDA/SCL | 100 Ω series + ESD diode (e.g. PESD5V0S2UT) | The cable comes from outside the board |
| SMBALERT | to PCA9554 IO5 (optional) | Not used by the firmware yet |
| VOUT (PowerPath system output) | only the datasheet's minimum capacitance, no load | |

Leave **JEITA** enabled. The firmware also enforces its own 5–45 °C charge window, using the
same NTC.

### 3.2 Protection

| Ref | Part | Purpose |
|---|---|---|
| F_IN | 5 A fast SMD fuse (Littelfuse 0451005 / 1206 type) | Slot input from the 24 V bus |
| D_TVS | SMBJ26A | Input transient clamp |
| F_BAT | **5 A fast fuse right at the B+ wire** | A Li-ion pack can supply hundreds of amps into a fault. This fuse is mandatory |
| C_in | 2 × 10 µF/50 V X7R + 47 µF/35 V polymer | Per datasheet. The main-board bus switch soft-starts to limit inrush |

### 3.3 I/O expander: PCA9554 (or PCA9554A / TCA9554) at 0x20

| Pin | Function | Circuit |
|---|---|---|
| IO0 | Battery-present microswitch (Omron D2F-01L or similar) | Switch to GND; uses the internal 100 k pull-up plus 100 nF to GND |
| IO1 | LED red (anode) | 5 mm RGB LED, **common cathode to GND** (e.g. Kingbright L-154A4SUREQBFZGEW). PCA9554 runs on 5V_SLOT and **sources** the current (push-pull outputs, active high). Series resistors: **560 Ω** red (V_F ≈ 2.0 V), **270 Ω** green and blue (V_F ≈ 3.3 V), about 5 mA each, which is plenty for a diffused LED indoors |
| IO2 | LED green (anode) | |
| IO3 | LED blue (anode) | |
| IO4 | Bleed-resistor MOSFET gate | 2N7002K or AO3422 (≥ 55 V), 100 k gate pull-down |
| IO5 | LTC4162 SMBALERT (optional) | |
| IO6/7 | spare, to a test header | |

**Bleed resistor (optional but recommended):** 2 × 100 Ω / 2 W in series from B+ (after F_BAT) to
the MOSFET drain. That draws about 0.1 A and about 2 W at 21 V. The firmware uses it to bring a
full pack down to the storage voltage (about 1 Ah takes about 10 h). Mount the resistors standing
off the PCB and away from plastic. If you don't fit them, delete `bleed_output:` in `slot.yaml`.

### 3.4 Connectors

| Connector | Type | Pins |
|---|---|---|
| J1 power | 5.08 mm screw terminal, 2-pin | +24 V, GND (from the Wago tap, 1.0 mm² wire) |
| J2 I²C | JST-XH 4-pin | 5V_SLOT, GND, SDA, SCL |
| J3 battery | 3.5 mm screw terminal, 3-pin (+1 spare) | B+, B−, T. Use 1.0 mm² silicone wire for B+/B− and keep it short |
| J4 switch | JST-PH 2-pin | IO0, GND |
| J5 LED | JST-PH 4-pin | GND (common cathode), R, G, B |

## 4. Main board (perfboard is fine, or a simple 2-layer PCB, 100 × 60 mm holes)

| Function | Part | Connection |
|---|---|---|
| MCU | **ESP32-C6-DevKitC-1** on headers (or Seeed XIAO ESP32C6) | 5 V from the buck |
| 5 V supply | 24→5 V buck module **≥ 1.5 A** (e.g. Pololu D24V22F5) | always on. Feeds the ESP board and, via a 500 mA polyfuse, the **5V_SLOT** rail |
| 5V_SLOT | from the 5 V buck through a 500 mA polyfuse | Feeds the slot-side I²C pull-ups, the PCA9554s, the LTC4162 DVCC and the LEDs (≤ 15 mA per slot) |
| I²C | GPIO22 = SDA, GPIO23 = SCL, 4.7 k pull-ups to **3.3 V** (ESP side) | |
| Mux A | TCA9548A, A0..A2 = 000 → **0x70**, channels 0–7 → slots 1–8 | RESET pulled high |
| Mux B | TCA9548A, A0 = 1 → **0x71**, channels 0–1 → slots 9–10 | |
| TCA9548A supply | **VCC = 3.3 V** | The TCA9548A's pass switches translate levels: with VCC at 3.3 V the ESP side stays at 3.3 V while each slot channel is pulled up to 5 V |
| Pull-ups per mux channel | 2 × 4.7 kΩ to **5V_SLOT** per channel | Cheap TCA9548A breakouts often lack downstream pull-ups, and some have them to VCC (3.3 V). Remove those |
| Enclosure temperature | SHT40 breakout, **0x44** | Mount it in the controller box, near the PSU |
| 24 V bus switch | P-MOSFET (e.g. SQD40P06-15L or AOD4185, ≥ 40 V, ≥ 20 A), 12 V gate zener, 100 k gate–source, NPN/2N7002 driver from **GPIO21**, 100 nF + 47 k on the gate for about 10 ms soft-start | Default off: if the ESP is in reset or crashes, nothing charges |
| Buzzer | 5 V active buzzer + 2N7002 from **GPIO20** | Sounds on any slot fault or enclosure > 50 °C |
| Main fuse | 10 A blade fuse after the PSU | |
| Slot cables | 10 × JST-XH 4-pin | 4-wire cable such as LiYY 4 × 0.14 mm², ≤ 1.5 m |

**Why the slot side runs at 5 V:** the green and blue chips of a typical RGB LED have
V_F ≈ 3.0–3.4 V. At 3.3 V they would barely light, whichever way the LED is wired. At 5 V the PCA9554
can source the LED current directly into a common-cathode LED with no extra transistors. The ESP32
never sees 5 V: the TCA9548A does the level shifting. Alternative if you prefer 3.3 V logic on the
slot board: keep the bus at 3.3 V, power only the LED from 5 V, and switch each colour with a
high-side transistor. That takes 6 extra parts per slot.

GPIO choice for the ESP32-C6: avoid the strapping pins 8, 9 and 15, USB pins 12/13, and the JTAG
pins 4–7. Pins 20–23 are free on both suggested boards.

## 5. Power budget

| | |
|---|---|
| PSU | Mean Well LRS-200-24 (fanless, 200 W, 8.8 A). Trim to 24.5 V |
| Battery-side current budget | `max_total_current: 8A` (8 A × 21 V = 168 W + about 6 % charger loss, roughly 180 W) |
| Per slot | 0.3–3.0 A, set in Home Assistant. Default 1.5 A (0.37C on 4 Ah, 0.75C on 2 Ah) |
| Typical | 5 packs charging at 1.5 A at once. The rest wait, served in order: "charge to 100 %" requests first, then the emptiest pack |
| Idle consumption | About 1.5 W (ESP + 10 × LTC4162 quiescent) |

Bigger budget: use an LRS-350-24 (it has a fan) or an HLG-320H-24 (sealed, fanless) and raise
`max_total_current`.

## 6. Safety: Li-ion charging under a shelf

- The **hardware thermal cut-out** (KSD301, 70 °C, normally closed) is in the AC line of the PSU.
  Mount it touching the PSU case or the bus wiring. It works without software.
- **Per-slot fuses** on both the input and the battery side.
- **Default-off** 24 V bus switch, a software ambient limit (45 °C), the battery NTC window
  (5–45 °C), and the LTC4162's JEITA control and timers.
- **Fault latching:** a pack that shorts, fails detection or hits the 10 h charge timeout is not
  charged again until you take it out.
- Print the holders in **PETG or ASA**, not PLA, which softens near 55 °C. If the shelf is wood
  or chipboard, screw a 0.5–1 mm **steel or aluminium sheet** between the shelf and the modules.
  Keep nothing flammable directly below the rack, and put a smoke detector in the room.
- Never charge packs that are swollen, dropped hard, or have been below 0 °C.
- The AC side (inlet, fuse, thermal cut-out, PSU) must be built by a qualified person, with PE
  connected to the PSU case.
