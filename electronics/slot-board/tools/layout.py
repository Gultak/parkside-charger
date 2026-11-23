"""Slot board layout: placement, copper pours, routing priorities, silkscreen and
schematic sheet placement. Board coordinates in mm, y = 0 is the FRONT edge
(towards the battery / end stop), y = 47.5 the REAR edge (bay lid)."""

PROJECT = "slot_board"
REV = "C"
ROOT_UUID = "5a1c0b0a-7d1e-4c3a-9a47-2f6f3c0b0001"
BW, BH = 72.0, 47.5     # rides in the card guides of the printed bay with its 72 mm edges
EDGE_KEEP = 2.0         # keep parts this far from the long (guide) edges
GND_VIA_SKIP = {("U1", str(n)) for n in range(1, 30)}   # EP has thermal vias, PGND sits in the pour

# ref: (x, y, rotation)  board coordinates, y = 0 is the FRONT edge (towards the
# battery / end stop), y = 47.5 the REAR edge (bay lid)
PLACE = {
    # input: J1/J6 rear-left; TVS, bulk cap and fuse in the (otherwise empty) left column
    "J1": (5.35, 36.4, 180), "J6": (44.0, 36.4, 180), "F1": (12.2, 32.95, 0), "D1": (4.6, 27.5, 90), "C1": (11.0, 27.05, 90),
    "Q1": (17.0, 33.0, 90), "R1": (17.0, 25.5, 90),
    # LTC4162 + hot loop + LDO caps
    "U1": (26.0, 30.0, 0), "C3": (26.0, 24.6, 0), "C4": (26.0, 21.9, 0), "C6": (24.6, 19.9, 0),
    "L1": (27.2, 15.4, 0), "R2": (33.6, 15.4, 90), "C7": (36.9, 15.0, 270), "C8": (39.4, 15.0, 270),
    "Q2": (31.5, 25.0, 0),
    "C9": (21.4, 27.4, 180), "C5": (21.4, 29.05, 180), "C2": (21.4, 31.9, 180), "C10": (22.5, 34.5, 270),
    # bottom-row parts kept ~4 mm below the pins so pins 9..14 can fan out
    "R3": (26.5, 37.2, 0), "R4": (29.6, 37.2, 0), "R5": (32.7, 37.2, 0), "C11": (30.4, 32.6, 0),
    # battery output, front edge
    "F2": (44.5, 12.4, 0), "J3": (44.0, 5.4, 180),
    # board NTC at the front edge, next to the battery contacts
    "RT1": (28.5, 3.5, 0),
    # pack ID / BMS input: pull-up, RC filter, reference, comparator
    # (front left, next to the ID contact of J3, where the board had room to spare)
    "R15": (6.0, 6.0, 0), "R16": (10.5, 6.0, 0), "R17": (15.0, 6.0, 0), "R18": (19.5, 6.0, 0),
    "C15": (6.0, 10.5, 0), "U4": (12.0, 11.0, 0), "C16": (18.0, 11.0, 0),
    # logic, right half
    "U2": (52.85, 34.0, 0), "C13": (56.8, 29.6, 0), "J2": (60.0, 42.5, 180), "U3": (65.0, 35.5, 0),
    "R6": (60.0, 32.0, 0), "R7": (60.0, 35.0, 0), "C12": (69.0, 36.0, 90),
    "J4": (54.0, 4.0, 270), "C14": (54.0, 10.5, 0), "J5": (66.5, 4.0, 270),
    "R8": (61.0, 10.5, 90), "R9": (63.6, 10.5, 90), "R10": (66.2, 10.5, 90),
    # bleed resistors (2 x 1 W dissipation) lying flat in the right half, driver beside them
    "R11": (65.0, 27.0, 90), "R12": (68.0, 27.0, 90), "Q3": (62.0, 27.0, 0),
    "R13": (50.5, 15.5, 0), "R14": (50.5, 21.0, 0),
}

# screwdriver hole for the module's rear mounting screw (centred across the board;
# must match pcb_hole in mechanical/parkside_shelf_charger.scad)
CUTOUTS = [(40.5, 25.0, 10.0)]

# the XT30 bodies reach past the rear edge into the cable cut-out of the bay cover
OVERHANG = {"J1", "J6"}

# copper pours on F.Cu: (net, priority, polygon)
POURS = [
    ("+24V", 2, [(9.6, 32.0), (11.9, 32.0), (11.9, 34.4), (14.2, 34.4), (14.2, 39.4), (36.8, 39.4),
                 (36.8, 34.6), (41.2, 34.6), (41.2, 47.0), (8.8, 47.0), (8.8, 34.4), (9.6, 34.4)]),
    ("VIN", 2, [(2.3, 28.4), (14.9, 28.4), (14.9, 33.95), (17.25, 33.95), (17.25, 34.0), (12.4, 34.0),
                (12.4, 31.6), (2.3, 31.6)]),
    ("CLP", 3, [(15.1, 27.6), (18.9, 27.6), (18.9, 33.75), (15.1, 33.75)]),
    ("VOUT", 3, [(15.1, 20.9), (25.4, 20.9), (25.4, 28.05), (24.5, 28.05), (24.5, 26.45), (15.1, 26.45)]),
    ("GND", 3, [(26.65, 20.9), (28.6, 20.9), (28.6, 27.4), (27.45, 27.4), (27.45, 28.0), (26.6, 28.0)]),
    ("CSP", 3, [(28.6, 12.6), (31.6, 12.6), (31.6, 16.9), (35.4, 16.9), (35.4, 19.1), (28.6, 19.1)]),
    ("BAT", 3, [(31.8, 10.3), (40.35, 10.3), (40.35, 10.9), (44.2, 10.9), (44.2, 14.5), (31.8, 14.5)]),
    ("BAT_F", 3, [(42.3, 3.9), (47.6, 3.9), (47.6, 13.6), (45.2, 13.6), (45.2, 9.0), (42.3, 9.0)]),
]
# hand-placed copper: (net, layer, width, [points])
FIXED_TRACKS = [
    ("SW", "F", 0.75, [(26.0, 27.5), (26.0, 18.0), (25.0, 17.0)]),   # SW pins 25/26 -> between C3/C4 pads -> L1
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
    ("PARKSIDE X20V SLOT rev C", 57.0, 46.6, 1.0), ("FRONT (battery side)", 20.0, 1.3, 0.9),
    ("24V IN", 10.0, 45.6, 0.8), ("24V OUT", 41.0, 45.6, 0.8),
    ("ID", 34.0, 1.9, 0.8), ("GND", 39.0, 1.9, 0.8), ("B+", 44.0, 1.9, 0.8), ("SCL SDA GND 5V", 56.2, 37.6, 0.8),
    ("GND SW", 53.0, 6.6, 0.8), ("G GND R B", 63.5, 6.6, 0.8),
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
    # board NTC, pack ID / BMS input
    "RT1": (212, 118),
    "R15": (320, 105), "R16": (335, 115), "C15": (347, 125), "R17": (362, 100), "R18": (362, 122),
    "U4": (385, 112), "C16": (400, 125),
}

SCH_TEXTS = [
        ("INPUT 24 V, reverse-blocking INFET, input current sense", 20, 30),
        ("LTC4162-LAD CHARGER (datasheet typ. application, 5 cells)", 150, 30),
        ("BATTERY", 295, 30),
        ("I2C (5 V slot bus via TCA9548A channel), PCA9554 @0x20, LTC4162 @0x68", 20, 150),
        ("PRESENCE SWITCH / RGB LED (common cathode)", 220, 150),
        ("BLEED-DOWN TO STORAGE VOLTAGE (~0.1 A)", 220, 200),
        ("PACK ID CONTACT = BMS STATUS (low = OK, released = fault)", 312, 90),
]
