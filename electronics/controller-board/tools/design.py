"""Controller board - single source of truth for parts and nets.

ESP32-C6 D1 (xyzroe) in female Dupont headers, 2x TCA9548A = 16 slot I2C channels (each with
4.7 k pull-ups to the 5 V slot rail - the TCA9548A at 3.3 V level-shifts), switched
24 V output to two slot daisy chains, 24 V -> 5 V SIP regulator, supply voltage
sensing, buzzer, SHT21 + Qwiic + expansion headers.
"""

# fmt: off
PARTS = {
    # ------------------------------------------------------------- 24 V in --
    # same pinout as the LOP-300 output (CN2, B6P-VH): a 1:1 cable with VHR-6N housings at
    # both ends; pins 1-3 +V, 4-6 -V, 10 A per contact with 18 AWG
    "J1": ("24V PSU IN", "Connector_Generic:Conn_01x06",
           "Connector_JST:JST_VH_B6P-VH_1x06_P3.96mm_Vertical",
           {"1": "+24V_IN", "2": "+24V_IN", "3": "+24V_IN", "4": "GND", "5": "GND", "6": "GND"},
           "JST B6P-VH (pins 1-3 +V, 4-6 -V, as on the LOP-300 CN2)"),
    "F1": ("10A mini blade", "Device:Fuse", "Fuse:Fuseholder_Blade_Mini_Keystone_3568",
           {"1": "+24V_IN", "2": "+24V"}, "Keystone 3568 holder + 10 A mini blade fuse"),
    "D1": ("SMBJ26A", "Device:D_Zener", "Diode_SMD:D_SMB", {"1": "+24V", "2": "GND"}, "TVS 26 V"),
    "C1": ("47u 35V", "Device:C_Polarized", "Capacitor_SMD:CP_Elec_6.3x7.7", {"1": "+24V", "2": "GND"}, ""),
    # ---------------------------------------------- switched 24 V for slots --
    "Q1": ("AOD4185", "Device:Q_PMOS_GDS", "Package_TO_SOT_SMD:TO-252-2",
           {"1": "PGATE", "2": "+24V_SW", "3": "+24V"}, "P-MOSFET -40 V / -40 A, 15 mOhm (or SQD40P06-15L)"),
    "R1": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+24V", "2": "PGATE"}, "gate pull-up (off)"),
    "D2": ("BZT52C12", "Device:D_Zener", "Diode_SMD:D_SOD-123", {"1": "+24V", "2": "PGATE"}, "Vgs clamp 12 V"),
    "C2": ("1u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric", {"1": "+24V", "2": "PGATE"},
           "soft start: slow turn-on into the slot capacitors"),
    "R2": ("47k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "PGATE", "2": "PG_DRV"}, ""),
    "Q2": ("2N7002K", "Device:Q_NMOS_GSD", "Package_TO_SOT_SMD:SOT-23",
           {"1": "BUS_EN", "2": "GND", "3": "PG_DRV"}, ""),
    "R3": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BUS_EN_IO", "2": "BUS_EN"}, ""),
    "R4": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BUS_EN", "2": "GND"},
           "default off while the ESP boots / resets"),
    # XT30 female, vertical: the chain cable plugs in from above. Same pin assignment on every
    # XT30 in the system: 1 = GND, 2 = +24V
    "J2": ("24V OUT A", "Connector_Generic:Conn_01x02",
           "Connector_AMASS:AMASS_XT30UPB-F_1x02_P5.0mm_Vertical",
           {"1": "GND", "2": "+24V_SW"}, "Amass XT30UPB-F: to the first slot of chain A (slot J1 IN)"),
    "J3": ("24V OUT B", "Connector_Generic:Conn_01x02",
           "Connector_AMASS:AMASS_XT30UPB-F_1x02_P5.0mm_Vertical",
           {"1": "GND", "2": "+24V_SW"}, "Amass XT30UPB-F: to the first slot of chain B"),
    # voltage sensing (24.5 V -> 2.2 V at the ADC)
    "R5": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+24V_SW", "2": "VS_OUT"}, ""),
    "R6": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "VS_OUT", "2": "GND"}, ""),
    "C3": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "VS_OUT", "2": "GND"}, ""),
    "R7": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+24V", "2": "VS_IN"}, ""),
    "R8": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "VS_IN", "2": "GND"}, ""),
    "C4": ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "VS_IN", "2": "GND"}, ""),
    # --------------------------------------------------------------- 5 V ---
    "U1": ("TSR 1-2450", "pcl:DCDC_3PIN", "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT",
           {"1": "+24V", "2": "GND", "3": "+5V"}, "TRACO TSR 1-2450 (6.5-36 V in, 5 V 1 A) or RECOM R-78E5.0-1.0"),
    "C5": ("10u 50V", "Device:C", "Capacitor_SMD:C_1206_3216Metric", {"1": "+24V", "2": "GND"}, ""),
    "C6": ("22u 10V", "Device:C", "Capacitor_SMD:C_1206_3216Metric", {"1": "+5V", "2": "GND"}, ""),
    "F2": ("0.5A PTC", "Device:Polyfuse", "Fuse:Fuse_1206_3216Metric",
           {"1": "+5V", "2": "+5V_SLOT"}, "Bourns MF-NSMF050 - slot 5 V rail"),
    "C7": ("22u 10V", "Device:C", "Capacitor_SMD:C_1206_3216Metric", {"1": "+5V_SLOT", "2": "GND"}, ""),
    # --------------------------------------------------------------- ESP ---
    "U2": ("ESP32-C6-D1", "pcl:ESP32_C6_D1", "pcl:ESP32_C6_D1_Socket",
           {"2": "MUX_RST", "3": "IO5", "4": "VS_IN", "5": "VS_OUT", "6": "IO6", "7": "IO7", "8": "+3V3",
            "9": "TX", "10": "RX", "11": "SCL", "12": "SDA", "13": "BUS_EN_IO", "14": "BUZ_IO",
            "15": "GND", "16": "+5V"},
           "xyzroe ESP32_C6_D1 in 2x 1x8 female Dupont headers (2.54 mm, rows 22.86 mm apart)"),
    "R9": ("4k7", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+3V3", "2": "SDA"}, ""),
    "R10": ("4k7", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+3V3", "2": "SCL"}, ""),
    "R11": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+3V3", "2": "MUX_RST"}, ""),
    # ------------------------------------------------------------- buzzer --
    "BZ1": ("5V active", "Device:Buzzer", "Buzzer_Beeper:Buzzer_12x9.5RM7.6",
            {"1": "+5V", "2": "BUZ_N"}, "12 mm active buzzer 5 V"),
    "Q3": ("2N7002K", "Device:Q_NMOS_GSD", "Package_TO_SOT_SMD:SOT-23",
           {"1": "BUZ", "2": "GND", "3": "BUZ_N"}, ""),
    "R12": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BUZ_IO", "2": "BUZ"}, ""),
    "R13": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "BUZ", "2": "GND"}, ""),
    "D3": ("1N4148W", "Device:D", "Diode_SMD:D_SOD-123", {"1": "+5V", "2": "BUZ_N"}, ""),
    # ------------------------------------------------------ headers --------
    "J4": ("SHT21", "Connector_Generic:Conn_01x04", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
           {"1": "+3V3", "2": "GND", "3": "SCL", "4": "SDA"}, "SHT21 breakout (VIN GND SCL SDA), on a Dupont cable; check the order on your board"),
    "J5": ("QWIIC", "Connector_Generic:Conn_01x04",
           "Connector_JST:JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal",
           {"1": "GND", "2": "+3V3", "3": "SDA", "4": "SCL"}, "Qwiic / STEMMA QT spare I2C"),
    "J6": ("EXP", "Connector_Generic:Conn_01x07", "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
           {"1": "+3V3", "2": "GND", "3": "IO5", "4": "IO6", "5": "IO7", "6": "TX", "7": "RX"},
           "spare GPIO (IO6 / IO7 are also the fan's PWM / tach)"),
    # --------------------------------------------------- PSU fan + power LED --
    # Standard 4-pin PC fan header (GND, +12V, TACH, PWM). 12 V comes from the PSU's own
    # +12 V aux fan output on a single Dupont pin (J9). PWM: open drain, 25 kHz from IO6;
    # tach: open collector from the fan, pulled up to 3.3 V, into IO7.
    "J7": ("FAN", "Connector_Generic:Conn_01x04", "Connector:FanPinHeader_1x04_P2.54mm_Vertical",
           {"1": "GND", "2": "+12V_FAN", "3": "IO7", "4": "FAN_PWM"}, "4-pin PC fan header (Molex 47053-1000 or KF2510-4A)"),
    "J9": ("12V FAN IN", "Connector_Generic:Conn_01x01", "Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
           {"1": "+12V_FAN"}, "1-pin header: +12 V aux from the PSU's fan connector"),
    "Q4": ("2N7002K", "Device:Q_NMOS_GSD", "Package_TO_SOT_SMD:SOT-23",
           {"1": "FAN_G", "2": "GND", "3": "FAN_PWM"}, "fan PWM, open drain"),
    "R14": ("100", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "IO6", "2": "FAN_G"}, ""),
    "R15": ("100k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "FAN_G", "2": "GND"}, ""),
    "R16": ("10k", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+3V3", "2": "IO7"}, "fan tach pull-up"),
    "J8": ("PWR LED", "Connector_Generic:Conn_01x02", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
           {"1": "LED_A", "2": "GND"}, "2-pin header: power LED (Lumex SSI-LXMP059ID), anode on pin 1"),
    "R17": ("330", "Device:R", "Resistor_SMD:R_0603_1608Metric", {"1": "+5V", "2": "LED_A"}, "power LED, about 9 mA"),
}
for i in range(1, 5):
    PARTS[f"H{i}"] = ("M3", "Mechanical:MountingHole", "MountingHole:MountingHole_3.2mm_M3", {}, "")

# -------------------------------------------------- I2C muxes + 16 slots --
# TCA9548APWR: SDn/SCn pins of channels 0..7
_SD = ["4", "6", "8", "10", "13", "15", "17", "19"]
_SC = ["5", "7", "9", "11", "14", "16", "18", "20"]
# mux channel -> slot. The muxes sit rotated 90 deg between their connector column
# and the middle of the board: the channel 4-7 pin row faces the upper four
# connectors, the channel 0-3 row the lower four, ordered so no pair has to cross.
# (ESPHome: esphome/parkside-charger.yaml uses the same table.)
CHANNEL_SLOT = {
    "U3": {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8},          # 0x70 (rotated 270 deg)
    "U4": {7: 9, 6: 10, 5: 11, 4: 12, 3: 13, 2: 14, 1: 15, 0: 16},   # 0x71
}
for k, (ref, a0) in enumerate((("U3", "GND"), ("U4", "+3V3"))):   # U3 = 0x70 (slots 1-8), U4 = 0x71 (9-16)
    pins = {"1": a0, "2": "GND", "21": "GND", "3": "MUX_RST", "22": "SCL", "23": "SDA", "24": "+3V3", "12": "GND"}
    for ch in range(8):
        slot = CHANNEL_SLOT[ref][ch]
        pins[_SD[ch]] = f"S{slot}_SDA"
        pins[_SC[ch]] = f"S{slot}_SCL"
    PARTS[ref] = ("TCA9548APWR", "Interface_Expansion:TCA9548APWR", "Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm",
                  pins, f"TI TCA9548APWR, address {'0x70' if k == 0 else '0x71'}")
    PARTS[f"C{8 + k}"] = ("100n", "Device:C", "Capacitor_SMD:C_0603_1608Metric", {"1": "+3V3", "2": "GND"}, "")
for n in range(1, 9):   # 8 x 4.7 k packs: slot 2n-1 and 2n, both lines, to the 5 V slot rail
    a, b = 2 * n - 1, 2 * n
    PARTS[f"RN{n}"] = ("4k7 x4", "Device:R_Pack04", "Resistor_SMD:R_Array_Convex_4x0603",
                       {"1": f"S{a}_SDA", "2": f"S{a}_SCL", "3": f"S{b}_SDA", "4": f"S{b}_SCL",
                        "5": "+5V_SLOT", "6": "+5V_SLOT", "7": "+5V_SLOT", "8": "+5V_SLOT"}, "slot bus pull-ups")
for s in range(1, 17):  # same pin order as the slot board's J2: 5V GND SDA SCL -> 1:1 cables
    PARTS[f"J{100 + s}"] = (f"SLOT {s}", "Connector_Generic:Conn_01x04",
                            "Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical",
                            {"1": "+5V_SLOT", "2": "GND", "3": f"S{s}_SDA", "4": f"S{s}_SCL"},
                            f"slot {s} I2C (JST B4B-XH-A)")

NO_CONNECT = {"U2": ["1"]}

DEFAULT_WIDTH = 0.2
NET_WIDTH = {"+5V": 0.6, "+5V_SLOT": 0.5, "+3V3": 0.4, "+24V": 0.6, "MUX_RST": 0.25, "+12V_FAN": 0.4}
# fmt: on


# left out of fab/controller_board_bom.csv (the DigiKey order list); listed in fab/controller_board_bom_all.csv
NOT_IN_ORDER_BOM = {
    "J1": "at hand (JST B6P-VH)", "U2": "at hand (ESP32-C6 D1 + headers)",
    "J4": "at hand (2.54 mm pin header)", "J6": "at hand (2.54 mm pin header)",
    "J8": "at hand (2.54 mm pin header)", "J9": "at hand (2.54 mm pin header)",
    "J2": "at hand (XT30UPB-F)", "J3": "at hand (XT30UPB-F)",
    "H1": "mounting hole", "H2": "mounting hole", "H3": "mounting hole", "H4": "mounting hole",
}
