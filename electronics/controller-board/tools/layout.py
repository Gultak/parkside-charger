"""Controller board layout. Board coordinates in mm (x right, y down), 112 x 64.

Top edge: ESP32-C6 D1 with its USB-C at the edge (antenna points into the board,
with a copper-free keepout below it), headers left/right of it.
Left / right edges: slot connectors 1-8 / 9-16.  Bottom edge: 24 V power.
"""

PROJECT = "controller_board"
REV = "C"
ROOT_UUID = "6b2d1c1b-8e2f-4d4b-8b58-3a7a4d1c0002"
BW, BH = 112.0, 64.0
EDGE_KEEP = 0.5
GND_VIA_SKIP = {("U3", "12"), ("U3", "21"), ("U4", "12"), ("U4", "2")}   # these get the fixed vias below

ESP_X, ESP_Y = 56.0, 13.9          # header centre; rotated 180 deg: USB at the top edge. The
# module's USB-C mouth is 17.88 mm from its header centre (xyzroe Gerbers), so it ends at
# board y = -3.98: the inside face of the box wall (4 mm gap), and sits in the wall's hole

# Compact layout (rev B): slot connectors at a 7 mm pitch down both sides, the ESP32 at the
# top centre with the headers beside it, the 24 V power band along the bottom edge.
PLACE = {
    "U2": (ESP_X, ESP_Y, 180),
    # left of the module: mounting hole, enclosure NTC, I2C pull-ups, buzzer
    "H3": (36.5, 4.0, 0), "RT1": (33.0, 12.0, 0), "R18": (33.0, 14.5, 0), "C10": (33.0, 17.0, 0),
    "R9": (36.5, 23.4, 0), "R10": (36.5, 25.2, 0),
    "BZ1": (32.0, 34.5, 0), "Q3": (24.0, 38.0, 0), "R12": (20.5, 40.5, 0), "R13": (20.5, 42.3, 0),
    "D3": (20.5, 44.6, 0),
    # right of the module: mounting hole, expansion header, voltage dividers, mux reset pull-up
    "H4": (79.5, 4.0, 0), "J6": (72.6, 3.0, 0),
    "R7": (77.5, 10.0, 0), "R8": (77.5, 11.8, 0), "C4": (77.5, 13.6, 0),
    "R5": (77.5, 15.6, 0), "R6": (77.5, 17.4, 0), "C3": (77.5, 19.2, 0),
    "R11": (77.5, 21.6, 0),
    # PSU fan header + its PWM driver and tach pull-up, 12 V input pin, power LED header
    "J7": (82.4, 11.0, 0), "Q4": (84.0, 18.1, 0), "R16": (84.0, 21.3, 0),
    "R15": (84.0, 23.0, 0), "R14": (86.8, 17.0, 90), "J9": (94.0, 14.0, 90),
    "J8": (27.0, 9.0, 270), "R17": (27.0, 12.6, 0),   # power LED header, left of the module
    # muxes + pull-up packs
    "U3": (25.2, 28.0, 270), "C8": (25.2, 34.0, 0),
    "U4": (86.0, 28.0, 90), "C9": (81.0, 22.4, 0),
    # 24 V power band along the bottom edge (left -> right): PSU in, fuse, bus switch, OUT A, OUT B
    "J1": (17.5, 58.2, 0), "F1": (43.1, 53.4, 0), "D1": (37.5, 45.4, 0), "C1": (28.0, 44.9, 0),
    "Q1": (62.7, 57.4, 0),
    "R1": (48.0, 43.4, 0), "D2": (48.0, 45.8, 0), "C2": (48.0, 48.6, 0),
    "R2": (54.0, 43.4, 0), "Q2": (58.6, 44.8, 0), "R3": (64.0, 43.4, 0), "R4": (64.0, 45.4, 0),
    "J2": (76.0, 58.4, 180), "J3": (90.0, 58.4, 180),
    # 5 V regulator above OUT B
    "U1": (80.5, 46.0, 0), "C5": (78.5, 49.6, 0), "C6": (84.5, 49.6, 0), "F2": (91.5, 44.0, 0),
    "C7": (89.5, 49.6, 0),
    # mounting holes in the bottom corners
    "H1": (5.5, 60.0, 0), "H2": (106.5, 60.0, 0),
}
for i in range(8):
    PLACE[f"J{101 + i}"] = (4.0, 3.5 + 7.0 * i, 0)       # slots 1-8, left edge
    PLACE[f"J{109 + i}"] = (108.0, 4.5 + 7.0 * i, 180)   # slots 9-16, right edge
for n in range(1, 5):                                     # packs for slots 1-8 / 9-16
    PLACE[f"RN{n}"] = (18.5, 7.0 + 14.0 * (n - 1), 0)
    PLACE[f"RN{n + 4}"] = (93.5, 7.0 + 14.0 * (n - 1), 0)

# copper pours: (net, priority, polygon[, layer])
_IN = [(15.0, 51.4), (46.6, 51.4), (46.6, 58.6), (40.2, 58.6), (40.2, 55.3), (27.6, 55.3), (27.6, 61.5),
       (15.0, 61.5)]
_V24 = [(50.0, 51.4), (55.5, 51.4), (55.5, 58.4), (59.3, 58.4), (59.3, 63.0), (50.0, 63.0)]
_SW = [(59.6, 51.4), (87.6, 51.4), (87.6, 61.6), (78.4, 61.6), (78.4, 55.6), (73.6, 55.6), (73.6, 61.6),
       (59.6, 61.6)]
POURS = [("+24V_IN", 2, _IN), ("+24V_IN", 2, _IN, "B"),
         ("+24V", 2, _V24), ("+24V", 2, _V24, "B"),
         ("+24V_SW", 2, _SW), ("+24V_SW", 2, _SW, "B")]
# mux GND pins (pin 12) sit at the end of a busy pin row: reserve their GND via before routing
FIXED_TRACKS = [("GND", "F", 0.3, [(21.625, 25.14), (21.625, 23.4)]),    # U3 (rot 270) pin 12
                ("GND", "F", 0.3, [(89.575, 30.86), (89.575, 32.6)]),    # U4 (rot 90) pin 12
                ("GND", "F", 0.2, [(83.075, 30.86), (83.075, 33.4)]),    # U4 pin 2 (A1), between two signals
                ("GND", "F", 0.2, [(26.875, 30.913), (26.875, 32.7)])]   # U3 pin 21, between two signals
FIXED_VIAS = [("GND", (21.625, 23.4)), ("GND", (89.575, 32.6)), ("GND", (83.075, 33.4)), ("GND", (26.875, 32.7))]
# no copper under the ESP antenna (module rotated: antenna at y = ESP_Y + 12 .. + 18)
# the ESP module overhangs the top edge (its USB-C reaches into the box wall)
OVERHANG = {"U2"}
KEEPOUTS = [[(ESP_X - 15.0, ESP_Y + 11.0), (ESP_X + 15.0, ESP_Y + 11.0),
             (ESP_X + 15.0, ESP_Y + 21.0), (ESP_X - 15.0, ESP_Y + 21.0)]]
KELVIN = [("Q1", "1", "D2", "2")]
# slot pairs in physical order (outermost connector first), then the shared nets
ROUTE_ORDER_FIRST = [f"S{s}_{l}" for s in (1, 8, 2, 7, 3, 6, 4, 5, 9, 16, 10, 15, 11, 14, 12, 13)
                     for l in ("SDA", "SCL")] + ["SDA", "SCL", "MUX_RST", "+3V3", "+5V", "+5V_SLOT"]
ROUTE_ORDER_LAST = []

LABELS = [
    ("PARKSIDE CHARGER CONTROLLER rev C", ESP_X, 38.0, 1.0),
    ("PSU IN: +V +V +V -V -V -V", 27.4, 53.4, 0.8), ("OUT A: +24V GND", 73.5, 63.2, 0.8),
    ("OUT B: +24V GND", 87.5, 63.2, 0.8), ("10 A", 48.1, 50.2, 0.8),
    ("NTC", 33.0, 9.8, 0.8), ("FAN", 86.2, 7.6, 0.8), ("LED", 25.7, 6.4, 0.8),
    ("EXP: 3V3 GND IO5 IO6 IO7 TX RX", 88.0, 1.0, 0.8),
]
for i in range(8):
    LABELS.append((f"S{1 + i}", 15.2, 3.5 + 7.0 * i + 0.5, 0.9))
    LABELS.append((f"S{9 + i}", 96.6, 4.5 + 7.0 * i + 0.5, 0.9))
LABELS.append(("5V GND SDA SCL", 8.0, 57.2, 0.8))
LABELS.append(("SCL SDA GND 5V", 104.0, 57.2, 0.8))

# ------------------------------------------------------------------ schematic --
TITLE = "Parkside charger - controller board"
COMMENTS = ["ESP32-C6 D1 (Dupont sockets), 2x TCA9548A -> 16 slots, switched 24 V, 5 V regulator",
            "Generated by kicadgen from tools/design.py + tools/layout.py - edit those, not this file"]
PAPER = "A2"
SCH_PLACE = {
    "J1": (30, 50), "F1": (55, 45), "D1": (70, 55), "C1": (82, 55), "Q1": (115, 45),
    "R1": (100, 70), "D2": (112, 75), "C2": (124, 75), "R2": (140, 70), "Q2": (155, 80),
    "R3": (172, 82), "R4": (185, 92), "J2": (165, 40), "J3": (185, 40),
    "R5": (205, 45), "R6": (215, 55), "C3": (225, 55), "R7": (240, 45), "R8": (250, 55), "C4": (260, 55),
    "U1": (300, 50), "C5": (285, 60), "C6": (320, 60), "F2": (340, 45), "C7": (355, 60),
    "U2": (290, 150), "R9": (240, 135), "R10": (250, 135), "R11": (330, 130),
    "BZ1": (380, 140), "Q3": (400, 160), "R12": (370, 165), "R13": (385, 175), "D3": (405, 135),
    "RT1": (430, 50), "R18": (445, 40), "C10": (460, 50), "J6": (500, 50),
    "J7": (430, 90), "J9": (400, 90), "Q4": (455, 100), "R14": (470, 110), "R15": (480, 115), "R16": (445, 80),
    "J8": (500, 90), "R17": (515, 80),
    "U3": (150, 250), "C8": (115, 210), "U4": (380, 250), "C9": (345, 210),
    "H1": (520, 120), "H2": (535, 120), "H3": (550, 120), "H4": (565, 120),
}
for i in range(8):
    SCH_PLACE[f"J{101 + i}"] = (40, 200 + 22 * i)
    SCH_PLACE[f"J{109 + i}"] = (520, 200 + 22 * i)
for n in range(1, 5):
    SCH_PLACE[f"RN{n}"] = (90, 205 + 44 * (n - 1))
    SCH_PLACE[f"RN{n + 4}"] = (460, 205 + 44 * (n - 1))
SCH_TEXTS = [
    ("24 V INPUT, FUSE, SWITCHED 24 V FOR THE SLOT CHAINS (soft start), SUPPLY SENSING", 20, 25),
    ("5 V REGULATOR", 280, 25), ("HEADERS", 425, 25),
    ("ESP32-C6 D1 IN DUPONT SOCKETS, I2C 3.3 V", 220, 110), ("BUZZER", 365, 110),
    ("SLOTS 1-8: TCA9548A 0x70 + 4.7k PULL-UPS TO 5V_SLOT (level shift)", 20, 185),
    ("SLOTS 9-16: TCA9548A 0x71", 330, 185),
]
