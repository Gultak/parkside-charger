# Bill of materials

Prices are rough unit prices in EUR (small quantities, without VAT and shipping), for
budgeting only. Links go to **DigiKey Ireland** where DigiKey stocks the part itself (no
Marketplace), otherwise to **Amazon.ie**. The ESP32 board, filament and cables are already at hand.

**Status column**

| | Meaning |
|---|---|
| ✅ at hand | You have it already: don't order |
| 📄 CSV | Board part that is in the **DigiKey order CSV** (see below): upload the CSV, don't order the row by hand |
| 🛒 order | Order separately, with the link in the row |

**The DigiKey order CSVs** are generated with the boards and list one board's parts, minus
everything marked at hand or bought elsewhere (XT30s):
[`electronics/slot-board/fab/slot_board_bom.csv`](electronics/slot-board/fab/slot_board_bom.csv) and
[`electronics/controller-board/fab/controller_board_bom.csv`](electronics/controller-board/fab/controller_board_bom.csv).
Upload them to DigiKey's [BOM Manager](https://www.digikey.ie/en/mylists/bom-manager) and set the build quantity: **number of slots**
for the slot board, **1** for the controller. (`*_bom_all.csv` beside them lists every part, with
where it comes from.)

## Per slot: slot board

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 1 | Li-ion step-down charger 1-8 cells I2C | Analog Devices LTC4162EUFD-LAD#PBF | 9.50 | must be the -LAD (I2C adjustable) version | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=LTC4162EUFD-LAD%23PBF) |
| 1 | Power inductor 6.8 uH Isat>=4.5A shielded | Coilcraft XAL6060-682MEC | 1.00 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=XAL6060-682MEC) |
| 2 | Current sense resistor 10 mOhm 1% 1 W 2512 | Vishay WSL2512R0100FEA | 0.40 | RSNSB + RSNSI | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=WSL2512R0100FEA) |
| 2 | N-channel MOSFET 40 V Power33 (INFET + BATFET) | onsemi FDMC8327L | 0.50 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=FDMC8327L) |
| 1 | NTC 10k 0603 B3380 1% (board temperature) | Murata NCP18XH103F03RB | 0.15 | RT1 | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=NCP18XH103F03RB) |
| 1 | Resistor 10k 0.1% 25 ppm 0603 (NTC bias) | Panasonic ERA-3AEB103V | 0.30 | R3 | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=ERA-3AEB103V) |
| 1 | Passives (caps 50 V X7R + polymer 47 uF; 0603 resistors) | see the CSV | 1.20 |  | 📄 CSV | [DigiKey BOM Manager](https://www.digikey.ie/en/mylists/bom-manager) |
| 1 | Comparator push-pull SOT-23-5 | TI TLV7031DBVR | 0.60 | pack BMS / ID input | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TLV7031DBVR) |
| 1 | I/O expander 8-bit I2C | NXP PCA9554PW,118 (or TI TCA9554PWR) | 0.80 | address 0x20 | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PCA9554PW%2C118) |
| 2 | Fuse 5 A fast SMD 1206 | Littelfuse 0466005.NR | 0.50 | input + battery side | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=0466005.NR) |
| 1 | TVS 26 V SMB | Littelfuse SMBJ26A | 0.20 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=SMBJ26A) |
| 1 | ESD diode I2C (5 V) SOT-23 | Nexperia PESD5V0S2UT,215 | 0.10 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PESD5V0S2UT%2C215) |
| 1 | N-MOSFET SOT-23 (bleed switch) | onsemi 2N7002KT1G | 0.10 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=2N7002KT1G) |
| 2 | Resistor 100 Ohm 2 W axial | Vishay PR02000201000JR500 | 0.25 | bleed | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PR02000201000JR500) |
| 1 | Screw terminal 3p 5.0 mm | your 5 mm terminals (or Phoenix MKDS 1,5/3-5,0) | 0.50 | J3 battery: ID GND B+ | ✅ at hand |  |
| 1 | JST-XH 4p vertical header | JST B4B-XH-A(LF)(SN) | 0.10 | J2 I2C cable | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B4B-XH-A%28LF%29%28SN%29) |
| 1 | XT30 PCB connector, right angle, **male** (24 V IN) | Amass XT30PW-M | 0.60 | J1; not at DigiKey. Buy as a set with the females | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=XT30PW%20male%20female%20PCB%20right%20angle) |
| 1 | XT30 PCB connector, right angle, **female** (24 V OUT) | Amass XT30PW-F | 0.60 | J6 | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=XT30PW%20male%20female%20PCB%20right%20angle) |
| 1 | Pin header 1x2 + 1x4, 2.54 mm |  | 0.05 | J4 switch, J5 LED (Dupont cables) | ✅ at hand |  |
| 1 | PCB 72x47.5 4-layer (electronics/slot-board/fab) | JLCPCB | 1.00 | per board in a 10-20 pcs order | 🛒 order | [JLCPCB](https://jlcpcb.com/) |

Subtotal: **≈ €20** per slot, of which to buy **≈ €20**

## Per slot: printed module and cables

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 1 | Microswitch with lever | Omron D2F-01L | 1.50 | clones ~0.30 | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/result?keywords=D2F-01L) |
| 1 | LED 5 mm RGB common cathode diffused | Kingbright L-154A4SUREQBFZGEW | 0.60 | 5.8 mm flange | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/result?keywords=L-154A4SUREQBFZGEW) |
| 2 | Dupont cables: 2-pin (switch) + 4-pin (LED), female housings + contacts |  | 0.10 |  | ✅ at hand |  |
| 3 | 6.3 mm male crimp tab with locking lance (+, ID, −) | the spade connectors | 0.10 | clicks into the contact block | ✅ at hand |  |
| 0.5 | m wire 0.75 mm², three colours |  | 0.80 | contact tabs to J3 | ✅ at hand |  |
| 2 | Wood screws 4x25 (1 countersunk, 1 pan head) |  | 0.03 |  | ✅ at hand |  |
| 1 | XT30 extension cable male-female, 16 AWG, 20 cm (10 cm only if that is the free wire length) | pre-made | 1.50 | chain cable OUT -> next slot's IN (about 8 cm of free wire needed) | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=XT30%20extension%20cable%20male%20female%2010cm) |

Subtotal: **≈ €5** per slot, of which to buy **≈ €4**

## Controller (once)

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 1 | ESP32-C6 D1 dev board | xyzroe ESP32_C6_D1 | 12.00 |  | ✅ at hand |  |
| 2 | Female header 1x8 2.54 mm (socket for the ESP32-C6 D1) + male pin headers on the module | Sullins PPTC081LFBN-RC | 0.30 | assumed covered by your pin headers; DigiKey link if not | ✅ at hand | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PPTC081LFBN-RC) |
| 1 | Controller PCB 4-layer | electronics/controller-board/fab | 4.00 | per board in a 5 pcs order | 🛒 order | [JLCPCB](https://jlcpcb.com/) |
| 2 | I2C mux 8 ch | TI TCA9548APWR | 1.50 | 0x70 + 0x71 | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TCA9548APWR) |
| 8 | Resistor array 4x4.7k 0603 | Yageo YC164-JR-074K7L | 0.05 | slot bus pull-ups | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=YC164-JR-074K7L) |
| 1 | 5 V regulator SIP-3 1 A | TRACO TSR 1-2450 (or RECOM R-78E5.0-1.0) | 5.50 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TSR%201-2450) |
| 1 | P-MOSFET -40 V TO-252 | AOS AOD4185 | 0.80 | 24 V bus switch | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=AOD4185) |
| 1 | Mini blade fuse holder PCB | Keystone 3568 | 1.00 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=3568) |
| 1 | Mini blade fuse 10 A | Littelfuse 0297010.WXNV | 0.30 | not on the board: order it with the CSV | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/result?keywords=0297010.WXNV) |
| 1 | PTC 0.5 A 1206 | Littelfuse 1206L050YR | 0.20 | 5 V slot rail | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=1206L050YR) |
| 1 | JST-VH 6p vertical header (24 V from the PSU) | JST B6P-VH | 0.40 | J1 | ✅ at hand |  |
| 2 | XT30 PCB connector, vertical, female (OUT A / OUT B) | Amass XT30UPB-F | 0.70 | J2, J3; not at DigiKey | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=XT30UPB%20female%20PCB) |
| 16 | JST-XH 4p vertical header | JST B4B-XH-A(LF)(SN) | 0.10 | slot connectors | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B4B-XH-A%28LF%29%28SN%29) |
| 32 | JST-XH 4p housing + 4 crimp contacts | JST XHP-4 + SXH-001T-P0.6 | 0.15 | both ends of the slot cables (28-22 AWG) | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/result?keywords=XHP-4)<br>[DigiKey](https://www.digikey.ie/en/products/result?keywords=SXH-001T-P0.6) |
| 16 | Slot cable, 4-core 22 AWG, up to 1.5 m |  | 0.50 |  | ✅ at hand |  |
| 1 | Buzzer 12 mm 5 V internally driven | Same Sky CMI-1275-05TH | 1.00 |  | 📄 CSV | [DigiKey](https://www.digikey.ie/en/products/result?keywords=CMI-1275-05TH) |
| 1 | SHT21 breakout (+ Dupont cable) |  | 4.00 | J4: VIN GND SCL SDA; check the order on your board | ✅ at hand |  |
| 1 | Passives / small parts (2N7002K, BZT52C12, SMBJ26A, caps, resistors) | see the CSV | 2.00 |  | 📄 CSV | [DigiKey BOM Manager](https://www.digikey.ie/en/mylists/bom-manager) |
| 2 | XT30 extension cable male-female, length to suit | pre-made | 3.00 | controller OUT A / OUT B -> first slot of each chain | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=XT30%20extension%20cable%20male%20female%2050cm) |
| 14 | M3 heat-set insert + M3x8 screw |  | 0.10 | 4 board, 4 PSU, 6 lid ears | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=M3%20heat%20set%20inserts%20brass%20kit) |
| 1 | Crimp tool (open barrel, for the tabs and VH/XH contacts) |  | 25.00 |  | ✅ at hand |  |

Subtotal: **≈ €83**, of which to buy **≈ €33**

## Power supply and mains side (once)

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 1 | PSU 24 V open frame | Mean Well LOP-400-24 (250 W fanless) or LOP-300-24 (180 W) | 40.00 | LOP-300: VH output, plugs 1:1 into J1. LOP-400: M3.5 screw output, use ring lugs on the PSU end | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/detail/mean-well-usa-inc/LOP-400-24/22040935) |
| 2 | JST-VHR-6N housing with 6 contacts, crimped | JST VHR-6N + SVH-21T-P1.1 | 0.40 | PSU -> J1 cable: 3 x 0.75 mm² per pole (LOP-400: one housing + 2 ring lugs) | ✅ at hand |  |
| 1 | Switched fused spur with flex outlet, 3 A fuse |  | 12.00 | wall side; replaces an inlet's switch and fuse. Fitted by an electrician | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=switched%20fused%20spur%20flex%20outlet) |
| 1 | Cable spur -> box, round 3-core (e.g. 3-core 1.5 mm² or H05VV-F 3G1.0), length to suit |  | 2.00 | round, so the gland seals and clamps it; solid or stranded both suit the Wagos | 🛒 order |  |
| 1 | Cable gland M20 nylon IP68 with locknut |  | 0.50 | for 6-12 mm cable; hole 20.5 mm in the box | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=M20%20cable%20gland%20nylon%20locknut) |
| 4 | Wago 221-412 lever connector (or 221-413) | Wago 221-412 | 0.40 | L: cable -> KSD301 -> PSU, N: cable -> PSU, PE: cable -> earth lead to the PSU | ✅ at hand |  |
| 1 | Heat alarm (for the hot press) |  | 20.00 | recommended | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=heat%20alarm%2010%20year) |
| 1 | VH 3p housing + 2 crimp contacts (PSU AC input) | JST VHR-3N + SVH-21T-P1.1 | 0.30 | your 2-pin VH plug does not fit the 3-pin input (pin 2 is left out) | 🛒 order | [DigiKey](https://www.digikey.ie/en/products/result?keywords=VHR-3N) |
| 1 | Insulated ring lugs M3 / M3.5 |  | 1.00 | on a short stranded green/yellow lead from the earth Wago to the PSU's earth hole; LOP-400 screw output | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=ring%20terminal%20kit%20insulated) |
| 1 | Thermal cut-out NC 70 C 250 V AC | KSD301 70C | 1.50 | in the AC line; not at DigiKey | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=KSD301%2070C%20normally%20closed) |
| 2 | m wire 1.5 mm² (blue / brown) |  | 1.00 | mains side inside the box | ✅ at hand |  |

Subtotal: **≈ €82**, of which to buy **≈ €77**

## Filament

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 2 | kg PETG / PETG V-0 filament |  | 20.00 | 16 slots + covers + controller box | ✅ at hand |  |

Subtotal: **≈ €40**, of which to buy **≈ €0**

## Safety

| Qty | Part | Example / MPN | ≈ € each | Notes | Status | Buy |
|---:|---|---|---:|---|---|---|
| 1 | Steel/alu sheet 0.5-1 mm for the shelf underside |  | 15.00 | recommended on wooden shelves | 🛒 order | [Amazon.ie](https://www.amazon.ie/s?k=aluminium%20sheet%201mm) |

Subtotal: **≈ €15**, of which to buy **≈ €15**

## Totals

| | Total ≈ € | To buy ≈ € |
|---|---:|---:|
| Per slot (board + module) | 25 | 23 |
| Fixed (controller, power supply, filament, safety) | 220 | 126 |
| 8 slots | 417 | 311 |
| 16 slots | 615 | 496 |
