# Bill of materials

Prices are rough unit prices in EUR (small quantities, without VAT and shipping); use them for
budgeting only. Links go to **DigiKey Ireland** where DigiKey stocks the part (most of them are
searches for the exact manufacturer part number, which open the product page directly), and to
**Amazon.ie** for generic hardware. Only two parts need another vendor: the ESP32-C6 D1 module
(Tindie) and the PCBs (JLCPCB, Gerbers in `electronics/*/fab`).

The per-board BOMs with every passive and the pick-and-place files are generated with the boards:
[`electronics/slot-board/fab/slot_board_bom.csv`](electronics/slot-board/fab/slot_board_bom.csv) and
[`electronics/controller-board/fab/controller_board_bom.csv`](electronics/controller-board/fab/controller_board_bom.csv).
DigiKey's BOM Manager can import those files directly.

## Per slot: slot board

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 1 | Li-ion step-down charger 1-8 cells I2C | Analog Devices LTC4162EUFD-LAD#PBF | 9.50 | must be the -LAD (I2C adjustable) version | [DigiKey](https://www.digikey.ie/en/products/result?keywords=LTC4162EUFD-LAD%23PBF) |
| 1 | Power inductor 6.8 uH Isat>=4.5A shielded | Coilcraft XAL6060-682MEC | 1.00 | L >= 0.3*Vin(max)/1.5MHz = 5 uH | [DigiKey](https://www.digikey.ie/en/products/result?keywords=XAL6060-682MEC) |
| 2 | Current sense resistor 10 mOhm 1% 1 W 2512 | Vishay WSL2512R0100FEA | 0.40 | RSNSB + RSNSI (2512 footprint) | [DigiKey](https://www.digikey.ie/en/products/result?keywords=WSL2512R0100FEA) |
| 2 | N-channel MOSFET 40 V Power33 (INFET + BATFET) | onsemi FDMC8327L | 0.50 | check the land pattern (VSON-8 NexFET footprint) | [DigiKey](https://www.digikey.ie/en/products/result?keywords=FDMC8327L) |
| 1 | NTC 10k 0603 B3380 1% (board temperature) | Murata NCP18XH103F03RB | 0.15 | RT1 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=NCP18XH103F03RB) |
| 1 | Resistor 10k 0.1% 25 ppm 0603 (NTC bias) | Panasonic ERA-3AEB103V | 0.30 | R3 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=ERA-3AEB103V) |
| 1 | Passives set (caps 50 V X7R + polymer 47 uF; 0603 resistors) | see fab/slot_board_bom.csv | 1.20 |  | [DigiKey BOM Manager (upload the CSV)](https://www.digikey.ie/en/mylists/bom-manager) |
| 1 | Comparator push-pull rail-to-rail input SOT-23-5 | TI TLV7031DBVR | 0.60 | pack BMS / ID input | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TLV7031DBVR) |
| 1 | I/O expander 8-bit I2C | NXP PCA9554PW,118 (or TI TCA9554PWR) | 0.80 | address 0x20 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PCA9554PW%2C118) |
| 2 | Fuse 5 A fast SMD 1206 | Littelfuse 0466005.NR | 0.50 | input + battery side | [DigiKey](https://www.digikey.ie/en/products/result?keywords=0466005.NR) |
| 1 | TVS 26 V SMB | Littelfuse SMBJ26A | 0.20 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=SMBJ26A) |
| 1 | ESD diode I2C (5 V) SOT-23 | Nexperia PESD5V0S2UT,215 | 0.10 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PESD5V0S2UT%2C215) |
| 1 | N-MOSFET SOT-23 (bleed switch) | onsemi 2N7002KT1G | 0.10 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=2N7002KT1G) |
| 2 | Resistor 100 Ohm 2 W axial | Vishay PR02000201000JR500 | 0.25 | bleed (optional) | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PR02000201000JR500) |
| 2 | Screw terminal 2p 5.08 mm | Phoenix MKDS 1,5/2-5,08 (1715721) | 0.60 | 24 V IN + OUT (daisy chain) | [DigiKey](https://www.digikey.ie/en/products/result?keywords=1715721) |
| 1 | Screw terminal 3p 3.5 mm | Phoenix PT 1,5/3-3,5-H (1984620) | 0.70 | battery B+ GND ID | [DigiKey](https://www.digikey.ie/en/products/result?keywords=1984620) |
| 1 | JST-XH 4p vertical header | JST B4B-XH-A(LF)(SN) | 0.10 | I2C cable | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B4B-XH-A%28LF%29%28SN%29) |
| 1 | JST-PH 2p vertical header | JST B2B-PH-K-S(LF)(SN) | 0.10 | microswitch | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B2B-PH-K-S%28LF%29%28SN%29) |
| 1 | JST-PH 4p vertical header | JST B4B-PH-K-S(LF)(SN) | 0.10 | LED | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B4B-PH-K-S%28LF%29%28SN%29) |
| 1 | JST-PH housings 2p + 4p with crimp contacts | JST PHR-2 + PHR-4 + SPH-002T-P0.5S | 0.30 | switch + LED cables | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PHR-4) |
| 1 | PCB 72x47.5 4-layer 1oz (electronics/slot-board/fab) | JLCPCB/PCBWay | 1.00 | per board in a 10-20 pcs order | [JLCPCB](https://jlcpcb.com/) |

Subtotal: **≈ €21** per slot

## Per slot: printed module

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 1 | Microswitch with lever | Omron D2F-01L | 1.50 | clones ~0.30 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=D2F-01L) |
| 1 | LED 5 mm RGB common cathode diffused | Kingbright L-154A4SUREQBFZGEW | 0.60 | standard T-1 3/4: 5.8 mm flange; driven from PCA9554 at 5 V | [DigiKey](https://www.digikey.ie/en/products/result?keywords=L-154A4SUREQBFZGEW) |
| 3 | Contact blade 0.8 x 6.3 x 50 mm, brass (+, ID, −) | QUARKZMAN brass plate 100 x 100 x 0.8 mm, cut into strips | 0.27 | one plate = about 30 blades (two rows of 15): 16 slots need 2 plates (€8 each, free delivery). Cut with tin snips or score and snap, file the edges, round the tip; Faston tabs are too short for the contact block + end wall + bevel | [Amazon.ie](https://www.amazon.ie/dp/B0CMJ9V6R9) |
| 1 | Wood screw 4x25 countersunk (flat head) |  | 0.03 | front - centre of the channel ceiling | [Amazon.ie](https://www.amazon.ie/s?k=wood%20screws%204x25%20countersunk) |
| 1 | Wood screw 4x25 pan head |  | 0.03 | rear - inside the bay, through the hole in the slot PCB | [Amazon.ie](https://www.amazon.ie/s?k=wood%20screws%204x25%20pan%20head) |
| 1 | 2-wire jumper 1.5 mm2 with ferrules (24 V daisy chain) |  | 0.50 | slot J6 OUT -> next slot J1 IN | [Amazon.ie (wire)](https://www.amazon.ie/s?k=1.5mm2%20silicone%20wire%20red%20black)<br>[Amazon.ie (ferrules)](https://www.amazon.ie/s?k=ferrule%20crimp%20kit%201.5mm2) |

Subtotal: **≈ €3** per slot

## Controller (once)

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 1 | ESP32-C6 D1 dev board | xyzroe ESP32_C6_D1 (Tindie / Elecrow / Lectronz) | 12.00 | plugs into the female headers (module needs male pin headers); not sold by DigiKey | [Tindie (xyzroe)](https://www.tindie.com/search/?q=ESP32-C6+D1)<br>[Project page](https://github.com/xyzroe/ESP32_C6_D1) |
| 2 | Female header 1x8 2.54 mm | Sullins PPTC081LFBN-RC | 0.30 | socket for the ESP32-C6 D1 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=PPTC081LFBN-RC) |
| 1 | Controller PCB 4-layer | electronics/controller-board/fab | 4.00 | per board in a 5 pcs order | [JLCPCB](https://jlcpcb.com/) |
| 2 | I2C mux 8 ch | TI TCA9548APWR | 1.50 | 0x70 + 0x71 | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TCA9548APWR) |
| 8 | Resistor array 4x4.7k 0603 | Yageo YC164-JR-074K7L | 0.05 | slot bus pull-ups | [DigiKey](https://www.digikey.ie/en/products/result?keywords=YC164-JR-074K7L) |
| 1 | 5 V regulator SIP-3 1 A | TRACO TSR 1-2450 (or RECOM R-78E5.0-1.0) | 5.50 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=TSR%201-2450) |
| 1 | P-MOSFET -40 V -40 A TO-252 | AOS AOD4185 (or Vishay SQD40P06-15L) | 0.80 | 24 V bus switch | [DigiKey](https://www.digikey.ie/en/products/result?keywords=AOD4185) |
| 1 | Mini blade fuse holder PCB | Keystone 3568 | 1.00 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=3568) |
| 1 | Mini blade fuse 10 A | Littelfuse 0297010.WXNV | 0.30 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=0297010.WXNV) |
| 1 | PTC 0.5 A 1206 | Littelfuse 1206L050YR | 0.20 | 5 V slot rail | [DigiKey](https://www.digikey.ie/en/products/result?keywords=1206L050YR) |
| 3 | Screw terminal 2p 5.08 mm | Phoenix MKDS 1,5/2-5,08 (1715721) | 0.60 | PSU in, OUT A, OUT B | [DigiKey](https://www.digikey.ie/en/products/result?keywords=1715721) |
| 16 | JST-XH 4p vertical header | JST B4B-XH-A(LF)(SN) | 0.10 | slot connectors | [DigiKey](https://www.digikey.ie/en/products/result?keywords=B4B-XH-A%28LF%29%28SN%29) |
| 32 | JST-XH 4p housing (cable ends) + 4 crimp contacts each | JST XHP-4 + SXH-001T-P0.6 | 0.15 | slot cables 1:1, 4 x 0.14 mm2, up to 1.5 m; or buy ready-made | [DigiKey](https://www.digikey.ie/en/products/result?keywords=XHP-4)<br>[Amazon.ie (ready-made XH cables)](https://www.amazon.ie/s?k=JST%20XH%202.54%204%20pin%20cable%20double%20ended) |
| 1 | Buzzer 12 mm 5 V internally driven | Same Sky CMI-1275-05TH | 1.00 | check the pin pitch against the 7.6 mm footprint | [DigiKey](https://www.digikey.ie/en/products/detail/same-sky-formerly-cui-devices/CMI-1275-05TH/25577239) |
| 1 | SHT40 breakout | Adafruit 4885 or clone | 4.00 | on a cable in the low-voltage compartment | [DigiKey](https://www.digikey.ie/en/products/result?keywords=Adafruit%204885)<br>[Amazon.ie (clone)](https://www.amazon.ie/s?k=SHT40%20breakout%20module) |
| 1 | Passives / small parts (2N7002K, BZT52C12, SMBJ26A, caps, resistors) | see fab/controller_board_bom.csv | 2.00 |  | [DigiKey BOM Manager (upload the CSV)](https://www.digikey.ie/en/mylists/bom-manager) |
| 14 | M3 heat-set insert + M3x8 screw |  | 0.10 | controller box: 4 board standoffs, 4 PSU standoffs, 6 lid ears | [Amazon.ie](https://www.amazon.ie/s?k=M3%20heat%20set%20inserts%20brass%20kit) |

Subtotal: **≈ €44**

## Power supply (once)

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 1 | PSU 24 V open frame | Mean Well LOP-400-24 (250 W fanless; LOP-300-24 = 180 W) | 40.00 | in the controller box; trim to 24.5 V; 4x M3 heat-set inserts + screws | [DigiKey](https://www.digikey.ie/en/products/detail/mean-well-usa-inc/LOP-400-24/22040935) |
| 1 | IEC C14 inlet with fuse holder and switch | Schurter DD11.0121.1111 | 12.00 | panel cut-out 47.1 x 28.1 mm (the box is drawn for it) | [DigiKey](https://www.digikey.ie/en/products/detail/schurter-inc/DD11-0121-1111/1646868) |
| 1 | Fuse 5x20 mm T3.15 A | Littelfuse 02183.15MXP | 0.50 | in the inlet | [DigiKey](https://www.digikey.ie/en/products/result?keywords=02183.15MXP) |
| 1 | VH 3p housing + 2 crimp contacts (PSU AC input) | JST VHR-3N + SVH-21T-P1.1 | 0.30 |  | [DigiKey](https://www.digikey.ie/en/products/result?keywords=VHR-3N) |
| 1 | Ring lug M3 (PE to the PSU) + ferrules |  | 0.50 |  | [DigiKey (ring lug)](https://www.digikey.ie/en/products/result?keywords=ring%20terminal%20M3%201.5mm2)<br>[Amazon.ie (ferrules)](https://www.amazon.ie/s?k=ferrule%20crimp%20kit%201.5mm2) |
| 1 | Thermal cut-out NC 70 C 250 V AC | KSD301 70C | 1.50 | in AC line - hardware failsafe; not sold by DigiKey | [Amazon.ie](https://www.amazon.ie/s?k=KSD301%2070C%20normally%20closed) |
| 2 | m wire 1.5 mm2 red/black |  | 1.00 | PSU -> controller -> chains | [Amazon.ie](https://www.amazon.ie/s?k=1.5mm2%20silicone%20wire%20red%20black) |

Subtotal: **≈ €57**

## Filament

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 2 | kg PETG (V-0) or ASA filament; bay covers in PETG (flexible tabs); controller box ASA/PC/V-0 PETG |  | 20.00 | 16 slots + controller box | [Amazon.ie (PETG V-0)](https://www.amazon.ie/s?k=PETG%20V0%20flame%20retardant%20filament)<br>[Amazon.ie (ASA)](https://www.amazon.ie/s?k=ASA%20filament%201.75) |

Subtotal: **≈ €40**

## Safety

| Qty | Part | Example / MPN | ≈ € each | Notes | Buy |
|---:|---|---|---:|---|---|
| 1 | Steel/alu sheet 0.5-1 mm for shelf underside |  | 15.00 | recommended on wooden shelves | [Amazon.ie](https://www.amazon.ie/s?k=aluminium%20sheet%201mm) |

Subtotal: **≈ €15**

## Totals

| | ≈ € |
|---|---:|
| Per slot (board + module) | 24 |
| Fixed (controller, power supply, filament, safety) | 156 |
| 8 slots | 350 |
| 16 slots | 544 |
