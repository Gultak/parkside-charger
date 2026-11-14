"""Slot board layout: placement, copper pours, routing priorities, silkscreen and
schematic sheet placement. Board coordinates in mm, y = 0 is the FRONT edge
(towards the battery / end stop), y = 60 the REAR edge (bay lid)."""

PROJECT = "slot_board"
ROOT_UUID = "5a1c0b0a-7d1e-4c3a-9a47-2f6f3c0b0001"
BW, BH = 72.0, 60.0     # rides in the card guides of the printed bay with its 72 mm edges
EDGE_KEEP = 2.0         # keep parts this far from the long (guide) edges
GND_VIA_SKIP = {("U1", str(n)) for n in range(1, 30)}   # EP has thermal vias, PGND sits in the pour

# ref: (x, y, rotation)  board coordinates, y = 0 is the FRONT edge (towards the
# battery / end stop), y = 60 the REAR edge (bay lid)
PLACE = {
    # input: J1 rear-left, fuse, TVS, bulk cap, reverse-blocking FET, RSNSI
    "J1": (5.5, 54.5, 0), "J6": (16.8, 54.5, 0), "F1": (13.6, 45.5, 90), "D1": (4.6, 34.5, 90), "C1": (11.7, 39.2, 0),
    "Q1": (17.0, 33.0, 90), "R1": (17.0, 25.5, 90),
    # LTC4162 + hot loop + LDO caps
    "U1": (26.0, 30.0, 0), "C3": (26.0, 24.6, 0), "C4": (26.0, 21.9, 0), "C6": (24.6, 19.9, 0),
    "L1": (28.0, 15.4, 0), "R2": (33.6, 15.4, 90), "C7": (36.9, 15.0, 270), "C8": (39.4, 15.0, 270),
    "Q2": (31.5, 25.0, 0),
    "C9": (21.4, 27.4, 180), "C5": (21.4, 29.05, 180), "C2": (21.4, 31.9, 180), "C10": (22.5, 34.5, 270),
    # bottom-row parts kept ~4 mm below the pins so pins 9..14 can fan out
    "R3": (24.0, 37.2, 0), "R4": (27.1, 37.2, 0), "R5": (30.2, 37.2, 0), "C11": (30.4, 32.6, 0),
    # battery output, front edge
    "F2": (40.0, 11.5, 0), "J3": (44.0, 5.5, 180),
    # logic, right half
    "U2": (52.0, 34.0, 0), "C13": (56.8, 29.6, 0), "J2": (60.0, 55.5, 180), "U3": (52.0, 49.0, 0),
    "R6": (47.0, 46.0, 90), "R7": (48.6, 46.0, 90), "C12": (65.0, 51.5, 90),
    "J4": (54.0, 4.0, 180), "C14": (54.0, 9.0, 0), "J5": (66.5, 4.0, 180),
    "R8": (63.5, 10.0, 90), "R9": (65.5, 10.0, 90), "R10": (67.5, 10.0, 90),
    # bleed resistor (2 x 1 W dissipation) along the right edge, away from the IC
    "R11": (52.5, 41.5, 0), "R12": (52.5, 43.3, 0), "Q3": (57.0, 42.5, 0),
    "R13": (67.0, 44.0, 90), "R14": (61.5, 28.76, 270),
}

# copper pours on F.Cu: (net, priority, polygon)
POURS = [
    ("+24V", 2, [(8.6, 46.0), (18.9, 46.0), (18.9, 57.0), (8.6, 57.0)]),
    ("VIN", 2, [(2.3, 33.9), (17.55, 33.9), (17.55, 35.2), (19.0, 35.2), (19.0, 37.6), (10.9, 37.6),
                (10.9, 41.0), (15.0, 41.0), (15.0, 44.7), (2.3, 44.7)]),
    ("CLP", 3, [(15.1, 27.6), (18.9, 27.6), (18.9, 33.75), (15.1, 33.75)]),
    ("VOUT", 3, [(15.1, 20.9), (25.4, 20.9), (25.4, 28.05), (24.5, 28.05), (24.5, 26.45), (15.1, 26.45)]),
    ("GND", 3, [(26.65, 20.9), (28.6, 20.9), (28.6, 27.4), (27.45, 27.4), (27.45, 28.0), (26.6, 28.0)]),
    ("CSP", 3, [(29.2, 12.5), (30.8, 12.5), (30.8, 16.9), (35.4, 16.9), (35.4, 19.1), (29.2, 19.1)]),
    ("BAT", 3, [(31.8, 10.3), (40.35, 10.3), (40.35, 14.5), (31.8, 14.5)]),
    ("BAT_F", 3, [(42.3, 3.9), (46.0, 3.9), (46.0, 12.6), (40.6, 12.6), (40.6, 9.0), (42.3, 9.0)]),
]
# hand-placed copper: (net, layer, width, [points])
FIXED_TRACKS = [
    ("SW", "F", 0.75, [(26.0, 27.5), (26.0, 17.6)]),   # SW pins 25/26 -> between C3/C4 pads -> L1
]
FIXED_VIAS = [("GND", (28.2, 23.25)), ("GND", (27.6, 26.3)), ("GND", (28.25, 26.3)),
              ("GND", (28.2, 20.95))]

# explicit Kelvin / priority connections: route pad -> specific pad
KELVIN = [
    # left pin column of U1, strictly top to bottom so every pin keeps its escape
    ("U1", "1", "C6", "1"),    # BOOST -> 22 nF (via B.Cu)
    ("U1", "2", "C9", "1"),    # INTVCC pin -> its 4.7 uF
    ("U1", "3", "C5", "1"),    # VOUTA pin -> its 100 nF
    ("U1", "4", "R1", "2"),    # CLN sense (VOUT side of RSNSI)
    ("U1", "5", "R1", "1"),    # CLP sense
    ("U1", "6", "Q1", "4"),    # INFET gate
    ("U1", "7", "C2", "1"),    # VIN pin -> its 100 nF
    ("U1", "8", "C10", "1"),   # VCC2P5 pin -> its 1 uF
    # right column: charge-current sense
    ("U1", "21", "R2", "1"),   # CSP sense
    ("U1", "20", "R2", "2"),   # CSN sense (BAT)
    ("U1", "19", "R2", "2"),   # BATSENS+
    ("U1", "22", "Q2", "4"),   # BATFET gate
]
# fine-pitch escapes first; nets that cross under the IC (VCC2P5 to CELLS0/1) last
ROUTE_ORDER_FIRST = ["SCL", "BOOST", "RT", "NTCBIAS", "NTC", "ALERT", "SCL", "SDA", "+5V", "INFET", "BATFET",
                     "INTVCC"]
ROUTE_ORDER_LAST = ["VCC2P5"]


# silkscreen labels: (text, x, y, size); pin labels read left to right as seen
# on the board (J2/J3/J4/J5 are rotated 180 deg)
LABELS = [
    ("PARKSIDE X20V SLOT rev A", 36.0, 58.6, 1.0), ("FRONT (battery side)", 20.0, 1.3, 0.9),
    ("IN: GND +24V", 8.0, 50.0, 0.8), ("OUT: +24V GND", 19.2, 50.0, 0.8),
    ("NTC GND B+", 40.5, 9.6, 0.8), ("SCL SDA GND 5V", 57.6, 50.9, 0.8),
    ("GND SW", 53.0, 7.6, 0.8), ("B G R GND", 63.5, 7.6, 0.8),
]


# pours on B.Cu as well: 24 V pass-through IN -> OUT carries the chain current
POURS.append(("+24V", 2, POURS[0][2], "B"))

# ------------------------------------------------------------------ schematic --
TITLE = "Parkside X20V slot charger board"
COMMENTS = ["LTC4162-LAD 5S Li-ion charger, PCA9554 slot I/O",
            "Generated by kicadgen from tools/design.py + tools/layout.py - edit those, not this file"]
SCH_PLACE = {
    # input
    "J1": (25, 45), "J6": (25, 62), "F1": (45, 45), "D1": (62, 58), "C1": (80, 50), "C2": (92, 50),
    "Q1": (110, 50), "R1": (126, 50),
    # charger
    "U1": (170, 85), "C3": (110, 85), "C4": (120, 85), "C5": (130, 85), "C6": (215, 50),
    "L1": (230, 50), "R2": (245, 50), "C7": (262, 50), "C8": (272, 50), "Q2": (250, 85),
    "C9": (110, 115), "C10": (120, 115), "R4": (130, 115), "R3": (225, 105), "C11": (240, 120),
    "R5": (250, 120),
    # battery
    "F2": (300, 50), "J3": (330, 60),
    # I2C / logic
    "J2": (40, 170), "U3": (65, 175), "R6": (85, 165), "R7": (95, 165), "C12": (105, 170),
    "U2": (170, 175), "C13": (130, 175), "J4": (250, 160), "C14": (262, 165),
    "R8": (225, 175), "R9": (235, 175), "R10": (245, 175), "J5": (275, 180),
    # bleed
    "R11": (225, 215), "R12": (237, 222), "Q3": (265, 215), "R13": (290, 205), "R14": (300, 205),
}

SCH_TEXTS = [
        ("INPUT 24 V, reverse-blocking INFET, input current sense", 20, 30),
        ("LTC4162-LAD CHARGER (datasheet typ. application, 5 cells)", 150, 30),
        ("BATTERY", 295, 30),
        ("I2C (5 V slot bus via TCA9548A channel), PCA9554 @0x20, LTC4162 @0x68", 20, 150),
        ("PRESENCE SWITCH / RGB LED (common cathode)", 220, 150),
        ("BLEED-DOWN TO STORAGE VOLTAGE (~0.1 A)", 220, 200),
]
