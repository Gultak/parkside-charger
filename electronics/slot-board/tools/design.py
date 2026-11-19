"""Parkside slot board - single source of truth for parts and nets.

Circuit = LTC4162-L datasheet (Rev A) typical application "9V to 35V 2-Cell 3.2A
Charger with PowerPath" adapted to 5 cells / 24 V input, plus the slot I/O:
PCA9554 (presence switch, RGB LED, bleed resistor), I2C connector with ESD,
input/battery fuses and a TVS.

Everything else (schematic, PCB, BOM) is generated from this file.
"""

# fmt: off
# ref: (value, symbol, footprint, {pin: net}, mpn/notes)
PARTS = {
    # ---------------------------------------------------------------- input --
    # 24 V daisy chain: J1 = IN, J6 = OUT, connected straight through (the
    # +24 V pins sit next to each other: GND +24V | +24V GND). Rated 13.5 A.
    # XT30: polarised and gendered, so a chain cable can only go OUT (female) -> IN (male),
    # the right way round. Same pin assignment on every XT30 in the system: 1 = GND, 2 = +24V.
    "J1": ("24V IN", "Connector_Generic:Conn_01x02",
           "Connector_AMASS:AMASS_XT30PW-M_1x02_P2.50mm_Horizontal",
           {"1": "GND", "2": "+24V"}, "Amass XT30PW-M (male, right angle): 24 V from the previous slot / controller"),
    "J6": ("24V OUT", "Connector_Generic:Conn_01x02",
           "Connector_AMASS:AMASS_XT30PW-F_1x02_P2.50mm_Horizontal",
           {"1": "GND", "2": "+24V"}, "Amass XT30PW-F (female, right angle): 24 V on to the next slot"),
    "F1": ("5A fast", "Device:Fuse", "Fuse:Fuse_1206_3216Metric",
           {"1": "+24V", "2": "VIN"}, "Littelfuse 0466005.NR (1206, 5 A, very fast)"),
    "D1": ("SMBJ26A", "Device:D_Zener", "Diode_SMD:D_SMB",
           {"1": "VIN", "2": "GND"}, "TVS 26 V unidirectional (K = pin 1)"),
    "C1": ("47u 35V", "Device:C_Polarized", "Capacitor_SMD:CP_Elec_6.3x7.7",
           {"1": "VIN", "2": "GND"}, "Aluminium-polymer/electrolytic, low-Q damping for hot plug"),
    "C2": ("100n 50V", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
           {"1": "VIN", "2": "GND"}, "X7R"),
    "Q1": ("FDMC8327L", "pcl:NMOS_Power33", "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET",
           {"1": "VIN", "2": "VIN", "3": "VIN", "4": "INFET", "5": "CLP"},
           "INFET, 40 V logic-level N-MOSFET (Power33). Check land pattern vs. part"),
    "R1": ("10m 1%", "Device:R", "Resistor_SMD:R_2512_6332Metric",
           {"1": "CLP", "2": "VOUT"}, "RSNSI, 1 W current sense"),
    # ------------------------------------------------------------- charger --
    "U1": ("LTC4162EUFD-LAD", "pcl:LTC4162-LAD",
           "Package_DFN_QFN:QFN-28-1EP_4x5mm_P0.5mm_EP2.65x3.65mm_ThermalVias",
           {"1": "BOOST", "2": "INTVCC", "3": "VOUT", "4": "VOUT", "5": "CLP", "6": "INFET",
            "7": "VIN", "8": "VCC2P5", "9": "NTCBIAS", "10": "NTC", "11": "RT", "12": "ALERT",
            "13": "SCL", "14": "SDA", "15": "+5V", "16": "GND", "17": "VCC2P5", "18": "VCC2P5",
            "19": "BAT", "20": "BAT", "21": "CSP", "22": "BATFET", "23": "GND", "24": "GND",
            "25": "SW", "26": "SW", "27": "VOUT", "28": "VOUT", "29": "GND"},
           "Analog Devices LTC4162EUFD-LAD#PBF (I2C adjustable!)"),
    "C3": ("10u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
           {"1": "VOUT", "2": "GND"}, "X7R, hot-loop cap: directly at pins 27/28 - 23/24"),
    "C4": ("10u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
           {"1": "VOUT", "2": "GND"}, "X7R"),
    "C5": ("100n 50V", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
           {"1": "VOUT", "2": "GND"}, "X7R, VOUTA bypass"),
    "C6": ("22n", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
           {"1": "BOOST", "2": "SW"}, "X7R >= 6.3 V, BOOST cap"),
    "L1": ("6.8u", "Device:L", "Inductor_SMD:L_Coilcraft_XAL6060-XXX",
           {"1": "SW", "2": "CSP"}, "Coilcraft XAL6060-682MEC (Isat 9 A)"),
    "R2": ("10m 1%", "Device:R", "Resistor_SMD:R_2512_6332Metric",
           {"1": "CSP", "2": "BAT"}, "RSNSB, 1 W current sense"),
    "C7": ("10u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
           {"1": "BAT", "2": "GND"}, "X7R, BATSENS+ bypass"),
    "C8": ("10u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric",
           {"1": "BAT", "2": "GND"}, "X7R, battery-side bulk"),
    "Q2": ("FDMC8327L", "pcl:NMOS_Power33", "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET",
           {"1": "BAT", "2": "BAT", "3": "BAT", "4": "BATFET", "5": "VOUT"},
           "BATFET, 40 V logic-level N-MOSFET (only powers the IC from the battery)"),
    "C9": ("4u7 10V", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
           {"1": "INTVCC", "2": "GND"}, "X7R"),
    "C10": ("1u 10V", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
            {"1": "VCC2P5", "2": "GND"}, "X7R"),
    "R4": ("63k4 1%", "Device:R", "Resistor_SMD:R_0603_1608Metric",
           {"1": "RT", "2": "GND"}, "1.5 MHz"),
    "R3": ("10k 0.1%", "Device:R", "Resistor_SMD:R_0603_1608Metric",
           {"1": "NTCBIAS", "2": "NTC"}, "NTC bias, low TC (25 ppm)"),
    "C11": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
            {"1": "+5V", "2": "GND"}, "DVCC bypass"),
    "R5": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric",
           {"1": "+5V", "2": "ALERT"}, "SMBALERT pull-up"),
    # ------------------------------------------------------------- battery --
    "F2": ("5A fast", "Device:Fuse", "Fuse:Fuse_1206_3216Metric",
           {"1": "BAT", "2": "BAT_F"}, "Littelfuse 0466005.NR - mandatory, battery side"),
    "J3": ("BATTERY", "Connector:Screw_Terminal_01x03",
           "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal",
           {"1": "BAT_F", "2": "GND", "3": "BMS"},
           "5.0 mm 3-pole screw terminal (e.g. Phoenix MKDS 1,5/3-5,0 or any KF301/DG301-5.0): B+, B-, pack ID contact"),
    # ---------------------------------------------- temperature / pack BMS --
    # The LTC4162 thermistor input reads a 10k NTC on this board, at the front edge
    # next to the battery contacts. The pack's own NTC sits in series with its BMS
    # transistor on the ID contact and is pulsed, so it is not usable for the LTC4162.
    "RT1": ("10k NTC B3380", "Device:Thermistor", "Resistor_SMD:R_0603_1608Metric",
            {"1": "NTC", "2": "GND"}, "Murata NCP18XH103F03RB (10k, B25/50 3380, 1%)"),
    # Pack ID contact: 5 V through 10k like the Parkside charger / soldering iron (keeps
    # the pack's BMS awake), RC filter ~0.5 s against its short releases, comparator at
    # 4.55 V: BMS_FAULT high = line released (fault, deep discharge, no pack).
    "R15": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+5V", "2": "BMS"}, "ID pull-up"),
    "R16": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BMS", "2": "BMS_F"}, ""),
    "C15": ("4u7 10V", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "BMS_F", "2": "GND"}, "X5R"),
    "R17": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+5V", "2": "BMS_REF"}, ""),
    "R18": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BMS_REF", "2": "GND"}, "-> 4.55 V"),
    "U4": ("TLV7031DBV", "pcl:COMP_SOT23_5", "Package_TO_SOT_SMD:SOT-23-5",
           {"1": "BMS_FAULT", "2": "GND", "3": "BMS_F", "4": "BMS_REF", "5": "+5V"},
           "TI TLV7031DBVR (push-pull, rail-to-rail input)"),
    "C16": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "+5V", "2": "GND"}, "U4 bypass"),
    # ---------------------------------------------------------- I2C / logic --
    "J2": ("I2C", "Connector_Generic:Conn_01x04", "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
           {"1": "+5V", "2": "GND", "3": "SDA_IN", "4": "SCL_IN"}, "JST B4B-XH-A: 5V, GND, SDA, SCL"),
    "U3": ("PESD5V0S2UT", "pcl:ESD_2CH", "Package_TO_SOT_SMD:SOT-23",
           {"1": "SDA_IN", "2": "SCL_IN", "3": "GND"}, "Nexperia PESD5V0S2UT"),
    "R6": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "SDA_IN", "2": "SDA"}, ""),
    "R7": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "SCL_IN", "2": "SCL"}, ""),
    "C12": ("4u7 10V", "Device:C", "Capacitor_SMD:C_0603_1608Metric",
            {"1": "+5V", "2": "GND"}, "5 V bulk"),
    "U2": ("PCA9554PW", "pcl:PCA9554", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
           {"1": "GND", "2": "GND", "3": "GND", "4": "SW_IN", "5": "IO1", "6": "IO2", "7": "IO3",
            "8": "GND", "9": "IO4", "10": "ALERT", "11": "BMS_FAULT", "16": "+5V", "14": "SCL", "15": "SDA"},
           "NXP PCA9554PW (or TCA9554PWR), address 0x20"),
    "C13": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "+5V", "2": "GND"}, ""),
    "J4": ("SWITCH", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
           {"1": "SW_IN", "2": "GND"}, "2.54 mm pin header (Dupont cable): presence microswitch, closes to GND"),
    "C14": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "SW_IN", "2": "GND"}, "debounce"),
    "R8": ("560", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "IO1", "2": "LED_R"}, "red"),
    "R9": ("270", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "IO2", "2": "LED_G"}, "green"),
    "R10": ("270", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "IO3", "2": "LED_B"}, "blue"),
    "J5": ("LED", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
           {"1": "GND", "2": "LED_R", "3": "LED_G", "4": "LED_B"}, "2.54 mm pin header (Dupont cable): RGB LED, common cathode on pin 1"),
    # ---------------------------------------------------------------- bleed --
    "R11": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "IO4", "2": "BLEED_G"}, ""),
    "R12": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BLEED_G", "2": "GND"}, ""),
    "Q3": ("2N7002K", "Device:Q_NMOS_GSD", "Package_TO_SOT_SMD:SOT-23",
           {"1": "BLEED_G", "2": "GND", "3": "BLEED_D"}, "60 V, 0.3 A"),
    "R13": ("100 2W", "Device:R", "Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal",
            {"1": "BAT_F", "2": "BLEED_M"}, "metal oxide 2 W, mount 2-3 mm above the board"),
    "R14": ("100 2W", "Device:R", "Resistor_THT:R_Axial_DIN0414_L11.9mm_D4.5mm_P15.24mm_Horizontal",
            {"1": "BLEED_M", "2": "BLEED_D"}, "metal oxide 2 W, mount 2-3 mm above the board"),
}

# pins that are intentionally unconnected (get a no-connect flag)
NO_CONNECT = {"U2": ["12", "13"]}

# copper widths (mm) for routed nets; nets not listed use DEFAULT_WIDTH
DEFAULT_WIDTH = 0.2
NET_WIDTH = {"+5V": 0.4, "BLEED_D": 0.4, "BLEED_M": 0.4, "BAT_F": 0.5, "NTC": 0.25}
# fmt: on


def nets():
    """net name -> list of (ref, pin)"""
    out = {}
    for ref, (_v, _s, _f, pins, _m) in PARTS.items():
        for pin, net in pins.items():
            out.setdefault(net, []).append((ref, pin))
    return out


if __name__ == "__main__":
    for n, conns in sorted(nets().items()):
        print(f"{n:10s} {len(conns):2d}  " + " ".join(f"{r}.{p}" for r, p in conns))


# left out of fab/slot_board_bom.csv (the DigiKey order list); listed in fab/slot_board_bom_all.csv
NOT_IN_ORDER_BOM = {
    "J1": "at hand (XT30PW-M)", "J6": "at hand (XT30PW-F)",
    "J4": "at hand (2.54 mm pin header)", "J5": "at hand (2.54 mm pin header)",
    "J3": "at hand (3-pole 5.0 mm screw terminal)",
}
