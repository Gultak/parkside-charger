# Electronics

## 1. System overview

```
 230 V AC ─[switched fused spur, 3 A]─ flex ─[M20 gland, Wago]─[KSD301 70 °C cut-out, NC]─► Mean Well LOP-400-24 (in the controller box)
                                                                            │ 24 V
   ┌─────────────────────────────────── CONTROLLER BOARD ──────────────────┴──────────────────────────┐
   │ J1 ─ 10 A fuse ─┬─ always on ─► TSR 1-2450 5 V ─┬─► ESP32-C6 D1 (Dupont sockets) ─ 3V3 ─► I2C side │
   │                 │                              └─► 0.5 A PTC ─► 5V_SLOT (slot logic + pull-ups)   │
   │                 └─► P-MOSFET bus switch (GPIO19, soft start) ─► J2 OUT A / J3 OUT B (24 V)         │
   │ GPIO22/23 I2C ─► TCA9548A 0x70 (slots 1-8) + TCA9548A 0x71 (slots 9-16), RESET GPIO4             │
   │ GPIO0/1: PSU / bus voltage   GPIO18: buzzer   headers: SHT21, Qwiic, expansion                    │
   └──────┬───────────────────────────────┬────────────────────────────────┬───────────────────────────┘
          │ OUT A: 24 V daisy chain        │ OUT B: 24 V daisy chain         │ 16 × 4-wire cable (5V GND SDA SCL)
          ▼                                ▼                                 │ one per slot, star topology
   SLOT 1 J1 IN ─ J6 OUT ─► SLOT 2 … ─► SLOT 8      SLOT 9 … ─► SLOT 16 ◄─────┘
   (each slot board: LTC4162-L charger @0x68 + PCA9554 @0x20; battery B+, B−, ID/BMS signal)
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
  effect, all slot boards are identical and any I²C wiring fault stays within one slot.

## 2. Parkside X20V battery interface: check this first

X20V packs are 5S Li-ion: 18 V nominal, **21.0 V charge voltage**, about 15 V empty. Before you
build ten boards, check on one pack:

1. **Contacts.** Seen from the front (tongue pointing away): **+, ID, T, −**. The pack's PCB
   calls them P+, CS, DS, P− ([Hackaday.io: LIDL PARKSIDE Battery hacks](https://hackaday.io/project/188089-lidl-parkside-battery-hacks)).
   - **+ / −** go straight to the cells (through a fuse). **Checked: the pack charges directly on
     + / −**; there are no MOSFETs in the pack.
   - **ID (CS)** is the BMS status line. Inside the pack it goes to − through a **~10 kΩ NTC in
     series with a transistor** (measured 12 kΩ). While the pack is OK the transistor is on. On
     under-voltage (about 2.6 V/cell) and other faults it switches off and the line floats.
     Parkside's charger (pin labelled "ID") and soldering iron pull it up to 5 V through 7–10 kΩ;
     the pack then sends a short open-drain data frame on it (1 kbit/s, about 4 times a second),
     and it also releases the line briefly a few times a second. Without a pull-up the pack's
     MCU goes to sleep and releases the line
     ([positron96: PARKSIDE battery protection board](https://positron96.gitlab.io/projects/parkside-battery-protection/),
     [mmame/parkside-x20](https://github.com/mmame/parkside-x20)).
   - **T (DS)** measures about 512 kΩ to − on an idle pack and shows no activity. **Not used.**
   - **Confirmed by Julian Ilett's teardown** ([video, 11:54](https://www.youtube.com/watch?v=CN0q4wZBnBo&t=714s)):
     the **charger uses ID**, the **tools use T**. So CS = *charge status*, DS = *discharge
     status*. Inside the pack: 5 × INR18650, a thermistor bonded to the cells, an LGT8P22A
     microcontroller (programming header 5 V/RST/GND/CLK/DATA), **five transistor + resistor
     cell-balancing bleeders**, a current-sense resistor in the negative lead that doubles as a
     fuse, **no cut-off MOSFET** (under-voltage/over-current cut-off is the tool's job, via T),
     and a separate 3-LED voltage gauge. The balancing only works near full at low current, so
     the firmware does a periodic balancing charge (`docs/firmware.md`).
   - **Pack PCB silkscreen** (2 Ah pack, board "LY758BX V1.1", screenshot from the same video):
     next to the connector, top to bottom, **+ / CS (pad P1) / DS (pad P10) / −**, which confirms
     + ID T −. CS has its own transistor (Q13) with diode D2, and DS its own (Q12, R15/C15): both
     are open-collector outputs switched by the LGT8P22A, which runs from a Zener-regulated 5 V. The
     balancers are a row of identical transistor + resistor pairs on the cell taps (CELL1–CELL5).
     Because CS is a transistor output, its "OK" level sits well below the slot board's 4.55 V
     comparator threshold. positron96's "10 kΩ NTC + transistor, released on under-voltage"
     was measured with a tool-style 10 kΩ pull-up and may describe the tool pin (T/DS). Either way
     the slot board reads ID (CS), the pin the Parkside charger uses, with the same pull-up and
     threshold. That works whether ID is an NTC or a fixed resistor: OK ≈ 2.5–3 V, data frames pull
     it to 0 V, a released line reads 5 V.
   - **Bring-up check:** with 10 kΩ from 5 V to ID, ID should sit at about 2.5–3 V (or pulse) on a
     healthy pack and go to 5 V on an empty one. If ID instead stays at 5 V on a healthy pack, wire
     J3 pin 3 to the T contact instead (no board change needed).
   - **Wiring:** J3 pin 3 goes to the **ID/CS contact, second from +**.
2. **What the slot board does with it** (§3.1): it pulls ID up to 5 V through 10 kΩ, like the
   Parkside charger, filters out the short releases (RC about 0.5 s) and compares the result with
   4.55 V. Above that = line released = **BMS fault, deep discharge or no pack**: the firmware does
   not charge (status *Pack BMS blocks charging*). Because the pack's NTC is pulsed and in series
   with the BMS transistor, it is **not** used as the charger's thermistor. The LTC4162 reads a
   10 kΩ NTC on the slot board next to the battery contacts instead; the pack protects its own
   cells through the BMS signal.
3. **Deeply discharged packs** (BMS released) are not charged. Wake them in the original
   charger first.
4. Measure the contact slot geometry for the 3D model (see `docs/mechanical.md`).

## 3. Slot board (×16 max), 72 × 47.5 mm, 4 layers

**The complete KiCad 7 design (schematic, routed PCB, Gerbers, BOM, pick-and-place) is in
[`slot-board/`](slot-board/README.md).** This section summarises the design decisions.

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
| NTCBIAS → NTC | **10 kΩ 0.1 %** bias to **RT1, a 10 kΩ NTC on the board** (Murata NCP18XH103F03RB, B 3380) at the front edge next to the battery contacts | Firmware converts using `ntc_bias_resistor`, `ntc_r25`, `ntc_beta: 3380` |
| Pack ID contact | R15 10 kΩ pull-up to 5V_SLOT → R16 100 kΩ / C15 4.7 µF (τ ≈ 0.5 s) → U4 TLV7031 comparator against 4.55 V (R17/R18) → PCA9554 IO6 | High = ID released = BMS fault / no pack. The pull-up also keeps the pack's BMS awake |
| DVCC (I²C supply) | **5V_SLOT** | Datasheet: DVCC 1.8–5.5 V operating, 5.5 V absolute maximum, and SDA/SCL must stay ≤ DVCC. A 5 V rail (±5 %) with the slot bus pulled up to the same rail is within spec. Don't use a buck that overshoots above 5.5 V |
| SDA/SCL | 100 Ω series + ESD diode (e.g. PESD5V0S2UT) | The cable comes from outside the board |
| SMBALERT | to PCA9554 IO5 (optional) | Not used by the firmware yet |
| VOUT (PowerPath system output) | only the datasheet's minimum capacitance, no load | |

Leave **JEITA** enabled. The firmware also enforces its own 5–45 °C charge window, using the
same (board) NTC. Battery cell temperature is the pack's own job: its BMS releases the ID line on
faults, and the firmware stops charging when it does.

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
| IO6 | Pack BMS fault (U4 comparator on the ID contact) | High = ID line released for more than ~0.5 s |
| IO7 | spare | |

**Bleed resistor (optional but recommended):** 2 × 100 Ω / 2 W in series from B+ (after F_BAT) to
the MOSFET drain. That draws about 0.1 A and about 2 W at 21 V. The firmware uses it to bring a
full pack down to the storage voltage (about 1 Ah takes about 10 h). Mount the resistors standing
off the PCB and away from plastic. If you don't fit them, delete `bleed_output:` in `slot.yaml`.

### 3.4 Connectors

| Connector | Type | Pins |
|---|---|---|
| J1 24 V IN / J6 24 V OUT | Amass **XT30PW-M** (IN, male) / **XT30PW-F** (OUT, female), right angle, sticking out of the rear edge | Connected straight through, so the slots **daisy-chain**. Polarised and gendered: a chain cable (1.5 mm², XT30 plug at each end) only fits OUT → IN, the right way round. Pin 1 GND, pin 2 +24 V on every XT30. Both sit in one row at the rear edge; seen from the top, + is on the right of IN and on the left of OUT, because a male and a female facing the same way are mirror images. 15 A |
| J2 I²C | JST-XH 4-pin | 5V_SLOT, GND, SDA, SCL |
| J3 battery | 5.0 mm screw terminal, 3-pin | B+, B−, ID (the pack's BMS contact; the T contact is not used). The wires come straight from the crimp tabs in the contact block: 0.75 mm² (18 AWG) silicone, keep them short |
| J4 switch | 2.54 mm pin header, 2-pin (Dupont cable) | IO0, GND |
| J5 LED | 2.54 mm pin header, 4-pin (Dupont cable) | GND (common cathode), R, G, B |

## 4. Controller board, 112 × 64 mm, 4 layers

**The complete KiCad 7 design is in [`controller-board/`](controller-board/README.md).** It covers
up to **16 slots**.

| Function | Part | Connection |
|---|---|---|
| MCU | **xyzroe ESP32-C6 D1** (ESP32-C6-MINI-1-N4, Wemos D1 form factor), plugged into **2 × 1×8 female Dupont headers** soldered into the board (holes 1.0 mm, rows 22.86 mm apart). USB-C points at the box wall | 5 V pin from the regulator. Its own 3.3 V LDO feeds the I²C side |
| 24 V input | J1 (**JST B6P-VH**: pins 1-3 +V, 4-6 −V, the same pinout as the LOP-300 output), **10 A mini blade fuse**, SMBJ26A, 47 µF | From the PSU: with a LOP-300 a 1:1 VH cable; with a LOP-400 (screw output) a VH plug on this end and ring lugs on the PSU end, 3 × 0.75 mm² per pole |
| 24 V bus switch | AOD4185 P-MOSFET (−40 V/−40 A, TO-252). 12 V gate zener, 100 k gate pull-up, 2N7002 driver from **GPIO19**, 47 k + 1 µF soft start (about 50 ms) | Default off. Switches **OUT A (J2)** and **OUT B (J3)**, vertical XT30 females (XT30UPB-F): two slot daisy chains, e.g. one per shelf row |
| 5 V | TRACO TSR 1-2450 (or RECOM R-78E5.0-1.0), 3-pin SIP, 1 A | Always on. Feeds the ESP and, via a 500 mA PTC, the **5V_SLOT** rail |
| I²C | GPIO22 = SDA, GPIO23 = SCL, 4.7 k to 3.3 V | |
| Muxes | 2 × TCA9548APWR: **0x70** (slots 1–8) and **0x71** (slots 9–16). VCC = 3.3 V, RESET on **GPIO4** (10 k pull-up) | Channel → slot order follows the layout; ESPHome uses the same table |
| Slot bus pull-ups | 8 × 4.7 k ×4 resistor arrays to 5V_SLOT | The TCA9548A shifts the level between 3.3 V and 5 V |
| Slot connectors | 16 × JST-XH 4 (5V, GND, SDA, SCL): slots 1–8 on the left edge, 9–16 on the right | Same pin order as the slot board's J2, so cables are wired 1:1 |
| Supply sensing | 100 k / 10 k dividers: PSU voltage → **GPIO0**, switched bus voltage → **GPIO1** | Firmware entities *PSU voltage* and *Slot bus voltage* |
| Buzzer | 12 mm 5 V active buzzer, 2N7002 from **GPIO18** | Sounds on any slot fault or enclosure > 50 °C |
| Headers | SHT21 breakout (3V3 GND SCL SDA, on a cable near the PSU), Qwiic (spare I²C), 7-pin expansion (3V3 GND IO5 IO6 IO7 TX RX) | |

**Why the slot side runs at 5 V:** the green and blue chips of a typical RGB LED have
V_F ≈ 3.0–3.4 V. At 3.3 V they would barely light, whichever way the LED is wired. At 5 V the PCA9554
can source the LED current directly into a common-cathode LED with no extra transistors. The ESP32
never sees 5 V: the TCA9548A does the level shifting. Alternative if you prefer 3.3 V logic on the
slot board: keep the bus at 3.3 V, power only the LED from 5 V, and switch each colour with a
high-side transistor. That takes 6 extra parts per slot.

The ESP32-C6 D1 breaks out only GPIO 0, 1, 4–7, 16–19, 22 and 23, so GPIO20/21 (used in the
first draft) are not available. The bus switch and buzzer therefore use GPIO19/18.

## 5. Power budget

| | |
|---|---|
| PSU (recommended) | Mean Well **LOP-400-24**, open frame 127 × 76.2 × 27.5 mm, built into the controller box. **250 W by convection** (no fan), 400 W only with 23 CFM forced air. Trim to 24.5 V (adjustable 22.8–25.2 V). Leave the remote-sense / PG connector CN3 open. `max_total_current: 10A` (10 A × 21 V / 0.94 ≈ 225 W, plus ~5 W for the electronics) |
| PSU, smaller | Mean Well **LOP-300-24**, 101.6 × 50.8 × 25.4 mm: **180 W by convection**. `max_total_current: 7A` |
| PSU, external | Mean Well LRS-200-24 (8 A) or LRS-350-24 / HLG-320H-24 (14 A), with `psu = "none"` in the 3D model |
| Why no fan | The 400 W rating needs 23 CFM, which only a 60 mm fan delivers, and that doesn't fit the 44 mm box. A 250 W budget still keeps 6 packs charging at 1.5 A at once; the others wait their turn |
| Battery-side current budget | The firmware shares `max_total_current` between the slots. 8 A × 21 V = 168 W, plus about 6 % charger loss |
| Per slot | 0.3–3.0 A, set in Home Assistant. Default 1.5 A (0.37C on 4 Ah, 0.75C on 2 Ah) |
| Typical | 6 packs (10 A, LOP-400) charging at 1.5 A at once (5 with 8 A, 9 with 14 A). The rest wait: "charge to 100 %" requests first, then the emptiest pack |
| Chain wiring | Two chains (OUT A/B) of up to 8 slots each. Use 1.5 mm² jumpers: worst case each chain carries the whole budget (≤ 14 A, terminals rated 13.5 A, so set ≤ 13 A when running a single chain of 16) |
| Idle consumption | About 2 W (ESP + 16 × LTC4162 quiescent) |

## 6. Safety: Li-ion charging under a shelf

- The **hardware thermal cut-out** (KSD301, 70 °C, normally closed) is in the AC line of the PSU.
  Mount it touching the PSU case or the bus wiring. It works without software.
- **Per-slot fuses** on both the input and the battery side.
- **Default-off** 24 V bus switch, a software ambient limit (45 °C), the pack's BMS signal (no
  charging while it reports a fault), the slot NTC window (5–45 °C), and the LTC4162's JEITA
  control and timers.
- **Fault latching:** a pack that shorts, fails detection or hits the 10 h charge timeout is not
  charged again until you take it out.
- Print the holders in **PETG or ASA**, not PLA, which softens near 55 °C. If the shelf is wood
  or chipboard, screw a 0.5–1 mm **steel or aluminium sheet** between the shelf and the modules.
  Keep nothing flammable directly below the rack. In a hot press or other closed space, fit a
  **heat alarm** (smoke alarms false-trigger on steam). Ambient up to about 30 °C is fine; the
  firmware stops charging when the box itself goes above 45 °C.
- Never charge packs that are swollen, dropped hard, or have been below 0 °C.
- The AC side (fused spur, flex, gland, thermal cut-out, PSU) must be built by a qualified person, with PE
  connected to the PSU's earth-marked mounting hole. The LOP is an **open-frame** supply: it must
  sit in the closed mains compartment of the controller box (lid screwed on, only finger-safe
  2.5 mm vents), never open on the shelf. Print that box in ASA, PC or V-0 rated PETG.
