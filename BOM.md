# Bill of materials

Taken from the procurement sheets (Google Drive: "Parkside Charger – Controller Parts" and
"Parkside Charger – 10 Slot Parts"), with the cheapest DigiKey alternative chosen per part. The
manufacturer and part number columns are the parts actually ordered.

| Status | Meaning |
|---|---|
| 🛒 DigiKey | Order from DigiKey Ireland. Upload [`procurement/digikey_all.csv`](procurement/digikey_all.csv) (everything, quantities merged), or [`procurement/digikey_controller.csv`](procurement/digikey_controller.csv) and [`procurement/digikey_10_slots.csv`](procurement/digikey_10_slots.csv) separately |
| ✅ at hand | Already there: don't order |
| 🏭 PCB fab | Gerbers in `electronics/*/fab` (JLCPCB / PCBWay) |
| ⚠️ resolve | The chosen part does not match the design yet: see the note |

Prices are DigiKey line totals including VAT, from the sheets. DigiKey ships free to Ireland from
€92.25 (€75 ex VAT).

## Controller, power supply and box (once)

| Qty | Part | Manufacturer | Part number | Status | DigiKey # | € (DigiKey, incl. VAT) | Used for / note |
|---:|---|---|---|---|---|---:|---|
| 1 | Controller PCB, 112 × 64 mm, 4 layers | JLCPCB | electronics/controller-board/fab | 🏭 PCB fab |  |  |  |
| 1 | ESP32-C6 module board | xyzroe | ESP32_C6_D1 | ✅ at hand |  |  | U2 |
| 2 | Female header 1×8, 2.54 mm (ESP32 socket) | Sullins | PPTC081LFBN-RC | ✅ at hand |  |  | U2 |
| 2 | I²C multiplexer, 8 channels, TSSOP-24 | NXP | PCA9548APW,118 | 🛒 DigiKey | 568-10297-1-ND | 3.32 | U3,U4 |
| 8 | Resistor array 4 × 4.7 kΩ, 0603 convex | Panasonic | EXB-38V472JV | 🛒 DigiKey | Y9472CT-ND | 0.89 | RN1-RN8 |
| 1 | 5 V regulator module, 1 A, SIP-3 | TRACO Power | TSR 1-2450E | 🛒 DigiKey | 1951-TSR1-2450E-ND | 4.11 | U1 |
| 1 | P-MOSFET −40 V, TO-252 | Alpha & Omega | AOD4185 | 🛒 DigiKey | 785-1222-1-ND | 1.51 | Q1 |
| 3 | N-MOSFET 60 V, SOT-23 | Diotec | 2N7002 | 🛒 DigiKey | 4878-2N7002CT-ND | 0.52 | Q2,Q3,Q4 |
| 1 | TVS 26 V, SMB | Vishay | SMB10J26A-E3/52 | 🛒 DigiKey | 112-SMB10J26A-E3/52CT-ND | 1.17 | D1 |
| 1 | Zener 12 V, SOD-123 | onsemi | MMSZ5242BT1G | 🛒 DigiKey | MMSZ5242BT1GOSCT-ND | 0.18 | D2 |
| 1 | Diode, SOD-123 | onsemi | MMSD4148T1G | 🛒 DigiKey | MMSD4148T1GOSCT-ND | 0.16 | D3 |
| 1 | Mini blade fuse holder, PCB | Keystone | 3568 | 🛒 DigiKey | 36-3568-ND | 1.65 | F1 |
| 3 | Mini blade fuse 10 A (1 + 2 spare) | Littelfuse | 0297010.WXNV | 🛒 DigiKey | F2561-ND | 1.29 | F1 |
| 1 | PTC fuse 0.5 A, 1206 | Littelfuse | NANOSMDC050F/13.2-2 | 🛒 DigiKey | NANOSMDC050F/13.2-2CT-ND | 0.66 | F2 |
| 1 | Buzzer 12 mm, 5 V, active | Same Sky | CMI-1275-05TH | 🛒 DigiKey | 2223-CMI-1275-05TH-ND | 1.51 | BZ1 |
| 1 | Capacitor 47 µF 35 V, aluminium electrolytic, 6.3 × 7.7 mm | Nichicon | UUD1V470MCL1GS | 🛒 DigiKey | 493-2287-1-ND | 0.63 | C1; electrolytic instead of hybrid polymer: fine (input bulk / damping) |
| 1 | Capacitor 1 µF 50 V X7R, 1206 | NIC Components | NMC1206X7R105K50TRPLPF | 🛒 DigiKey | 4988-NMC1206X7R105K50TRPLPFCT-ND | 0.43 | C2 |
| 1 | Capacitor 10 µF 50 V X7R, 1206 | Samsung | CL31B106KBHNNNE | 🛒 DigiKey | 1276-6767-1-ND | 0.46 | C5 |
| 2 | Capacitor 22 µF 10 V X7R, 1206 | Samsung | CL31B226KPHNNNE | 🛒 DigiKey | 1276-2769-1-ND | 1.08 | C6,C7 |
| 5 | Capacitor 100 nF 50 V X7R, 0603 | Murata | GRT188R71H104KE13D | 🛒 DigiKey | 490-GRT188R71H104KE13DCT-ND | 1.54 | C3,C4,C8,C9,C10 |
| 1 | NTC 10 kΩ B3380, 0603 (enclosure temperature) | Murata | NCP18XH103F03RB | 🛒 DigiKey | 490-4800-1-ND | 0.16 | RT1 |
| 6 | Resistor 100 kΩ 1%, 0603 | Yageo | RC0603FR-07100KL | 🛒 DigiKey | 311-100KHRCT-ND | 0.66 | R1,R4,R5,R7,R13,R15 |
| 5 | Resistor 10 kΩ 1%, 0603 | Panasonic | ERJ-3EKF1002V | 🛒 DigiKey | P10.0KHCT-ND | 0.55 | R6,R8,R11,R16,R18 |
| 2 | Resistor 4.7 kΩ 1%, 0603 | Vishay | CRCW06034K70FKEA | 🛒 DigiKey | 541-4.70KHCT-ND | 0.22 | R9,R10 |
| 3 | Resistor 100 Ω 1%, 0603 | KOA Speer | RK73H1JTTD1000F | 🛒 DigiKey | 2019-RK73H1JTTD1000FCT-ND | 0.33 | R3,R12,R14 |
| 1 | Resistor 47 kΩ 1%, 0603 | Yageo | RC0603FR-0747KL | 🛒 DigiKey | 311-47.0KHRCT-ND | 0.11 | R2 |
| 1 | Resistor 330 Ω 1%, 0603 | Yageo | RC0603FR-07330RL | 🛒 DigiKey | 311-330HRCT-ND | 0.11 | R17 |
| 16 | JST-XH header 4-pin, vertical | JST | B4B-XH-A(LF)(SN) | 🛒 DigiKey | 455-B4B-XH-A-ND | 2.52 | J101-J116 |
| 1 | 4-pin PC fan header | Molex | 0470531000 | 🛒 DigiKey | WM4330-ND | 0.55 | J7 |
| 1 | JST-VH header 6-pin | JST | B6P-VH | ✅ at hand |  |  | J1 |
| 2 | XT30 PCB socket, vertical, female | Amass | XT30UPB-F | ✅ at hand |  |  | J2,J3 |
| 1 | Pin header 1×7, 2.54 mm | generic | – | ✅ at hand |  |  | J6 |
| 1 | Pin header 1×2, 2.54 mm | generic | – | ✅ at hand |  |  | J8 |
| 1 | JST PH header 2-pin, vertical | JST | B2B-PH-K-S(LF)(SN) | 🛒 DigiKey | 455-1704-ND | 0.17 | J9 |
| 1 | Panel LED, red, snap-in | Lumex | SSI-LXMP059ID | 🛒 DigiKey | 67-1179-ND | 1.05 | on J8 |
| 1 | Fan 90/92 mm, 12 V, 4-pin PWM | generic | – | ✅ at hand |  |  | on J7 |
| 2 | JST PH housing 2-pin (PSU CN101 and J9 ends) | JST | PHR-2 | 🛒 DigiKey | 455-1165-ND | 0.20 | CN101 → J9 |
| 2 | JST PH pre-crimped lead, 24 AWG, 203 mm | JST | ASPHSPH24K203 | 🛒 DigiKey | 455-3359-ND | 0.72 | CN101 → J9, 1:1 |
| 1 | Power supply 24 V, open frame | Mean Well | LOP-300-24 | 🛒 DigiKey | 1866-LOP-300-24-ND | 44.65 | budget 7 A, 10 A with the fan |
| 2 | VH housing 6-pin | JST | VHR-6N | ✅ at hand |  |  |  |
| 14 | VH crimp contact | JST | SVH-21T-P1.1 | ✅ at hand |  |  |  |
| 1 | VH housing 3-pin | JST | VHR-3N | ✅ at hand |  |  |  |
| 1 | Thermal cut-out, 70 °C, normally closed | Honeywell | 2455R--00820195 | 🛒 DigiKey | 480-6788-ND | 22.32 |  |
| 4 | Lever connector 2-way | Wago | 221-412 | ✅ at hand |  |  |  |
| 1 | Cable gland M20 × 1.5 | LAPP | SKINTOP ST-M 20x1.5 (53111020) | 🛒 DigiKey | 1195-3042-ND | 5.57 |  |
| 1 | Locknut M20 × 1.5 | (see DigiKey) | 281-4710-ND | 🛒 DigiKey | 281-4710-ND | 1.98 |  |
| 1 | Switched fused spur with flex outlet | generic | – | ✅ at hand |  |  |  |
| 3 | Fuse 3 A, BS 1362 (1 + 2 spare) | generic | – | ✅ at hand |  |  |  |
| 1 | Round 3-core cable, 1.5 mm², length to suit | generic | – | ✅ at hand |  |  |  |
| 2 | XT30 male-to-female cable, 16 AWG, 30 cm | generic | – | ✅ at hand |  |  |  |
| 3 | Insulated ring lug M3/M3.5, 0.5–1.5 mm² | generic | – | ✅ at hand |  |  |  |
| 1 | Green/yellow wire 0.75 mm², about 15 cm | generic | – | ✅ at hand |  |  |  |
| 1 | Star washer M3 | generic | DIN 6798 A M3 | ✅ at hand |  |  |  |
| 14 | Heat-set insert M3 | generic | – | ✅ at hand |  |  |  |
| 14 | Screw M3 × 8 | generic | ISO 7380 | ✅ at hand |  |  |  |
| 4 | Screw M4 × 30 + nut | generic | ISO 7380 / DIN 934 | ✅ at hand |  |  |  |
| 1 | Steel or aluminium sheet, 0.5–1 mm | generic | – | ✅ at hand |  |  |  |
| – | Filament PETG / PETG V-0 | generic | – | ✅ at hand |  |  |  |

DigiKey total: **€102.98**

## 10 charger slots

| Qty | Part | Manufacturer | Part number | Status | DigiKey # | € (DigiKey, incl. VAT) | Used for / note |
|---:|---|---|---|---|---|---:|---|
| 10 | Slot PCB, 72 × 47.5 mm, 4 layers | JLCPCB | electronics/slot-board/fab | 🏭 PCB fab |  |  |  |
| 10 | Charger IC, QFN-28 4 × 5 | Analog Devices | LTC4162EUFD-LAD#PBF | 🛒 DigiKey | 505-LTC4162EUFD-LAD#PBF-ND | 76.49 | U1 |
| 10 | Inductor 6.8 µH, shielded | Vishay | IHLP2525CZER6R8M01 | 🛒 DigiKey | 541-1011-1-ND | 10.17 | L1 (IHLP-2525 footprint) |
| 20 | N-MOSFET 40 V, Power33 | onsemi | FDMC8327L | 🛒 DigiKey | FDMC8327LCT-ND | 21.18 | Q1,Q2 |
| 20 | Current-sense resistor 10 mΩ 1% 1 W, 2512 | Vishay | WSL2512R0100FEA | 🛒 DigiKey | WSLG-.01CT-ND | 7.97 | R1,R2 |
| 10 | Resistor 10 kΩ 0.1% 25 ppm, 0603 | Bourns | CRT0603-BY-1002ELF | 🛒 DigiKey | CRT0603-BY-1002ELFCT-ND | 0.85 | R3 |
| 10 | NTC 10 kΩ B3380, 0603 | Murata | NCP18XH103F03RB | 🛒 DigiKey | 490-4800-1-ND | 1.56 | RT1 |
| 10 | I/O expander, TSSOP-16, address 0x20 | Texas Instruments | TCA9554PWR | 🛒 DigiKey | 296-30135-1-ND | 13.70 | U2 |
| 10 | Comparator, SOT-23-5 | Texas Instruments | TLV7031DBVR | 🛒 DigiKey | 296-TLV7031DBVRCT-ND | 8.99 | U4 |
| 10 | ESD protection, SOT-23 | Nexperia | PESD5V2S2UT,215 | 🛒 DigiKey | 1727-PESD5V2S2UT,215CT-ND | 2.96 | U3 |
| 10 | N-MOSFET 60 V, SOT-23 | Diotec | 2N7002 | 🛒 DigiKey | 4878-2N7002CT-ND | 1.09 | Q3 |
| 10 | TVS 26 V, SMB | Vishay | SMB10J26A-E3/52 | 🛒 DigiKey | 112-SMB10J26A-E3/52CT-ND | 7.26 | D1 |
| 30 | Fuse 5 A fast, 1206 (20 + 10 spare) | Bel Fuse | C1Q 5 | 🛒 DigiKey | 5923-C1Q5CT-ND | 11.21 | F1,F2 |
| 20 | Resistor 100 Ω 2 W, axial | Vishay | PR02000201000JR500 | 🛒 DigiKey | 56-PR02000201000JR500CT-ND | 5.68 | R13,R14 |
| 10 | Capacitor 47 µF 35 V, aluminium electrolytic, 6.3 × 7.7 mm | Nichicon | UUD1V470MCL1GS | 🛒 DigiKey | 493-2287-1-ND | 3.95 | C1; electrolytic instead of hybrid polymer: fine (input bulk / damping) |
| 40 | Capacitor 10 µF 50 V X7R, 1206 | Samsung | CL31B106KBHNNNE | 🛒 DigiKey | 1276-6767-1-ND | 11.12 | C3,C4,C7,C8 |
| 60 | Capacitor 100 nF 50 V X7R, 0603 | Murata | GRT188R71H104KE13D | 🛒 DigiKey | 490-GRT188R71H104KE13DCT-ND | 7.65 | C2,C5,C11,C13,C14,C16 |
| 30 | Capacitor 4.7 µF 35 V X5R, 0603 | Murata | GRM188R6YA475KE15D | 🛒 DigiKey | 490-7205-1-ND | 4.91 | C9,C12,C15; X5R 35 V instead of X7R 10 V: fine (less DC-bias loss, rated to 85 °C) |
| 10 | Capacitor 1 µF 10 V X7R, 0603 | Samsung | CL10B105KP8NNNC | 🛒 DigiKey | 1276-1946-1-ND | 0.44 | C10 |
| 10 | Capacitor 22 nF 50 V X7R, 0603 | Samsung | CL10B223KB8NNNC | 🛒 DigiKey | 1276-1104-1-ND | 0.39 | C6 |
| 30 | Resistor 10 kΩ 1%, 0603 | Panasonic | ERJ-3EKF1002V | 🛒 DigiKey | P10.0KHCT-ND | 0.95 | R5,R15,R17 |
| 30 | Resistor 100 kΩ 1%, 0603 | Yageo | RC0603FR-07100KL | 🛒 DigiKey | 311-100KHRCT-ND | 0.60 | R12,R16,R18 |
| 30 | Resistor 100 Ω 1%, 0603 | KOA Speer | RK73H1JTTD1000F | 🛒 DigiKey | 2019-RK73H1JTTD1000FCT-ND | 0.65 | R6,R7,R11 |
| 20 | Resistor 270 Ω 1%, 0603 | Yageo | RC0603FR-07270RL | 🛒 DigiKey | 311-270HRCT-ND | 0.54 | R9,R10 |
| 10 | Resistor 560 Ω 1%, 0603 | Yageo | RC0603FR-07560RL | 🛒 DigiKey | 311-560HRCT-ND | 0.31 | R8 |
| 10 | Resistor 63.4 kΩ 1%, 0603 | Vishay | CRCW060363K4FKEA | 🛒 DigiKey | 541-63.4KHCT-ND | 0.34 | R4 |
| 10 | JST-XH header 4-pin, vertical | JST | B4B-XH-A(LF)(SN) | 🛒 DigiKey | 455-B4B-XH-A-ND | 1.57 | J2 |
| 20 | JST-XH housing 4-pin | JST | XHP-4 | 🛒 DigiKey | 455-2267-ND | 1.43 | slot cables |
| 90 | JST-XH crimp contact (80 + 10 spare), 22-28 AWG | JST | SXH-001T-P0.6 | 🛒 DigiKey | 455-1135-100-ND | 5.14 | slot cables |
| 10 | Microswitch with lever | Omron | D2F-01L | 🛒 DigiKey | SW154-ND | 12.98 | on J4 |
| 10 | LED 5 mm RGB, common cathode, diffused, 4 leads | Inolux | INL-5TB4URGB25 | 🛒 DigiKey | 1830-1015-ND | 6.46 | on J5 (header in its lead order: B, R, cathode, G) |
| 10 | XT30 PCB socket, right angle, male | Amass | XT30PW-M | ✅ at hand |  |  | J1 |
| 10 | XT30 PCB socket, right angle, female | Amass | XT30PW-F | ✅ at hand |  |  | J6 |
| 10 | Screw terminal 3-pole, 5.0 mm | Phoenix Contact | MKDS 1,5/3-5,0 (or KF301-5.0) | ✅ at hand |  |  | J3 |
| 10 | Pin header 1×2, 2.54 mm | generic | – | ✅ at hand |  |  | J4 |
| 10 | Pin header 1×4, 2.54 mm | generic | – | ✅ at hand |  |  | J5 |
| 10 | Cable 4-core 22 AWG, up to 1.5 m each | generic | – | ✅ at hand |  |  |  |
| 8 | XT30 male-to-female cable, 16 AWG, 20 cm | generic | – | ✅ at hand |  |  |  |
| 10 | Dupont cable 2-pin | generic | – | ✅ at hand |  |  |  |
| 10 | Dupont cable 4-pin | generic | – | ✅ at hand |  |  |  |
| 30 | 6.3 mm male crimp tab with locking lance | generic | – | ✅ at hand |  |  |  |
| – | Wire 0.75 mm², 3 colours | generic | – | ✅ at hand |  |  |  |
| 10 | Wood screw 4 × 25, countersunk | generic | – | ✅ at hand |  |  |  |
| 10 | Wood screw 4 × 25, pan head | generic | – | ✅ at hand |  |  |  |

DigiKey total: **€228.54** for 10 slots (€22.85 per slot)
