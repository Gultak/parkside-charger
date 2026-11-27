"""Project library of the parkside-charger boards (nickname "pcl"), used by kicadgen from the
agent-tools submodule: custom symbols and footprints, PCBWay part numbers, render colours.
See tools/agent-tools/kicadgen/projlib.py for the format."""
from kicadgen.symbols import F, eff, pin, ic_symbol  # noqa: F401

LIB = "pcl"
DESCR = "parkside-charger"
COMPANY = "github.com/Gultak/parkside-charger"

# ---------------- symbols
SYMBOLS = {}

SYMBOLS["LTC4162-LAD"] = ic_symbol(
    "LTC4162-LAD", "U", "LTC4162-LAD",
    "Package_DFN_QFN:QFN-28-1EP_4x5mm_P0.5mm_EP2.65x3.65mm_ThermalVias",
    "https://www.analog.com/en/products/ltc4162-l.html",
    left=[("7", "VIN", "power_in"), ("6", "INFET", "output"), ("5", "CLP", "input"),
          ("4", "CLN", "input"), ("3", "VOUTA", "power_in"), ("27", "VOUT", "power_in"),
          ("28", "VOUT", "passive"), None, ("1", "BOOST", "passive"), ("2", "INTVCC", "power_out"),
          ("8", "VCC2P5", "power_out"), ("11", "RT", "passive"), None, ("16", "SYNC", "input"),
          ("17", "CELLS0", "input"), ("18", "CELLS1", "input")],
    right=[("22", "BATFET", "output"), ("25", "SW", "output"), ("26", "SW", "passive"),
           ("21", "CSP", "input"), ("20", "CSN", "input"), ("19", "BATSENS+", "input"), None,
           ("9", "NTCBIAS", "output"), ("10", "NTC", "input"), None, ("15", "DVCC", "power_in"),
           ("13", "SCL", "input"), ("14", "SDA", "bidirectional"), ("12", "~{SMBALERT}", "open_collector")],
    bottom=[("23", "PGND", "power_in"), ("24", "PGND", "passive"), ("29", "AGND", "power_in")],
    width=22.86, desc="35V/3.2A multicell Li-ion step-down charger, PowerPath, I2C telemetry (I2C adjustable)")

SYMBOLS["PCA9554"] = ic_symbol(
    "PCA9554", "U", "PCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
    "https://www.nxp.com/docs/en/data-sheet/PCA9554_9554A.pdf",
    left=[("16", "VDD", "power_in"), ("14", "SCL", "input"), ("15", "SDA", "bidirectional"),
          ("13", "~{INT}", "open_collector"), None, ("1", "A0", "input"), ("2", "A1", "input"),
          ("3", "A2", "input"), None, ("8", "VSS", "power_in")],
    right=[("4", "IO0", "bidirectional"), ("5", "IO1", "bidirectional"), ("6", "IO2", "bidirectional"),
           ("7", "IO3", "bidirectional"), ("9", "IO4", "bidirectional"), ("10", "IO5", "bidirectional"),
           ("11", "IO6", "bidirectional"), ("12", "IO7", "bidirectional")],
    width=15.24, desc="8-bit I2C I/O expander with interrupt")

SYMBOLS["ESD_2CH"] = ic_symbol(
    "ESD_2CH", "U", "PESD5V0S2UT", "Package_TO_SOT_SMD:SOT-23",
    "https://assets.nexperia.com/documents/data-sheet/PESD5V0S2UT.pdf",
    left=[("1", "IO1", "passive"), ("2", "IO2", "passive")], right=[], bottom=[("3", "GND", "passive")],
    width=7.62, desc="Double ESD protection diode array, common anode")

# TI TLV7031DBV: comparator, push-pull output, rail-to-rail input (SOT-23-5: 1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+)
SYMBOLS["COMP_SOT23_5"] = ic_symbol(
    "COMP_SOT23_5", "U", "TLV7031DBV", "Package_TO_SOT_SMD:SOT-23-5",
    "https://www.ti.com/lit/ds/symlink/tlv7031.pdf",
    left=[("3", "IN+", "input"), ("4", "IN-", "input")], right=[("1", "OUT", "output")],
    bottom=[("5", "V+", "power_in"), ("2", "V-", "power_in")],
    width=12.7, desc="Nanopower comparator, push-pull output, rail-to-rail input")

# ESP32-C6 D1 (xyzroe/ESP32_C6_D1, Wemos D1 form factor) plugged into 2x 1x8 female Dupont headers.
# Pin numbers = footprint pads: left row 1..8 top->bottom, right row 9..16 top->bottom
# (seen from the top, antenna up, USB down).
SYMBOLS["ESP32_C6_D1"] = ic_symbol(
    "ESP32_C6_D1", "U", "ESP32-C6-D1", "pcl:ESP32_C6_D1_Socket",
    "https://github.com/xyzroe/ESP32_C6_D1",
    left=[("1", "RST", "input"), ("2", "IO4", "bidirectional"), ("3", "IO5", "bidirectional"),
          ("4", "IO0/ADC", "bidirectional"), ("5", "IO1/ADC", "bidirectional"), ("6", "IO6", "bidirectional"),
          ("7", "IO7", "bidirectional"), ("8", "3V3", "power_out")],
    right=[("9", "TX/IO16", "bidirectional"), ("10", "RX/IO17", "bidirectional"), ("11", "IO23", "bidirectional"),
           ("12", "IO22", "bidirectional"), ("13", "IO19", "bidirectional"), ("14", "IO18", "bidirectional"),
           ("15", "GND", "power_in"), ("16", "5V", "power_in")],
    width=17.78, desc="ESP32-C6 dev board in Wemos D1 form factor (xyzroe), plugged into 2x 1x8 female Dupont headers")

SYMBOLS["DCDC_3PIN"] = ic_symbol(
    "DCDC_3PIN", "U", "TSR_1-2450", "Converter_DCDC:Converter_DCDC_RECOM_R-78E-0.5_THT",
    "https://www.tracopower.com/model/tsr-1-2450",
    left=[("1", "VIN", "power_in")], right=[("3", "VOUT", "power_out")], bottom=[("2", "GND", "power_in")],
    width=10.16, desc="3-pin SIP switching regulator (TRACO TSR 1 / RECOM R-78E pinout)")

SYMBOLS["NMOS_Power33"] = '''  (symbol "NMOS_Power33" (in_bom yes) (on_board yes)
    (property "Reference" "Q" (at 5.08 1.27 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "NMOS_Power33" (at 5.08 -1.27 0) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Footprint" "Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "ki_description" "N-MOSFET, Power33 / 3.3x3.3 SON, pins 1-3 S, 4 G, 5-8+EP D" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "NMOS_Power33_0_1"
      (polyline (pts (xy 0.254 0) (xy -2.54 0)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0.254 1.905) (xy 0.254 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 0.762 -1.27) (xy 0.762 -2.286)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 0.762 0.508) (xy 0.762 -0.508)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 0.762 2.286) (xy 0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 2.54 2.54) (xy 2.54 1.778)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 2.54 -2.54) (xy 2.54 0) (xy 0.762 0)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 0.762 -1.778) (xy 3.302 -1.778) (xy 3.302 1.778) (xy 0.762 1.778)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy 1.016 0) (xy 2.032 0.381) (xy 2.032 -0.381) (xy 1.016 0)) (stroke (width 0) (type default)) (fill (type outline)))
      (circle (center 1.651 0) (radius 2.794) (stroke (width 0.254) (type default)) (fill (type none)))
    )
    (symbol "NMOS_Power33_1_1"
      (pin input line (at -5.08 0 0) (length 2.54) (name "G" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 2.54 -5.08 90) (length 2.54) (name "S" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 2.54 -5.08 90) (length 2.54) hide (name "S" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 2.54 -5.08 90) (length 2.54) hide (name "S" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 2.54 5.08 270) (length 2.54) (name "D" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
    )
  )'''


# ---------------- footprints
def _esp32_c6_d1_socket():
    """xyzroe ESP32_C6_D1 plugged into two 1x8 female Dupont headers (2.54 mm).

    Hole positions from the board's own drill file (Drill_PTH_Through.DRL, 1.0 mm
    holes): rows 22.86 mm apart, 2.54 mm pitch. Origin = centre of the 2x8 grid.
    Module outline 27.0 x 36.0 mm; antenna at the top (-y), USB-C at the bottom (+y).
    """
    pads = []
    names_l = ["RST", "IO4", "IO5", "IO0", "IO1", "IO6", "IO7", "3V3"]
    names_r = ["TX", "RX", "IO23", "IO22", "IO19", "IO18", "GND", "5V"]
    for i in range(8):
        y = -8.89 + 2.54 * i
        shape = "rect" if i == 0 else "circle"
        pads.append(f'  (pad "{i + 1}" thru_hole {shape} (at -11.43 {y:.2f}) (size 1.8 1.8) (drill 1.0) '
                    f'(layers "*.Cu" "*.Mask"))')
        pads.append(f'  (pad "{i + 9}" thru_hole circle (at 11.43 {y:.2f}) (size 1.8 1.8) (drill 1.0) '
                    f'(layers "*.Cu" "*.Mask"))')
    labels = []
    for i in range(8):
        y = -8.89 + 2.54 * i
        labels.append(f'  (fp_text user "{names_l[i]}" (at -8.2 {y:.2f}) (layer "F.SilkS") '
                      f'(effects (font (size 0.8 0.8) (thickness 0.12))))')   # centred: stays clear of the pads when rotated
        labels.append(f'  (fp_text user "{names_r[i]}" (at 8.2 {y:.2f}) (layer "F.SilkS") '
                      f'(effects (font (size 0.8 0.8) (thickness 0.12))))')
    x0, y0, x1, y1 = -13.5, -18.1, 13.5, 17.9
    # the USB end overhangs the board edge by about 4 mm: no silkscreen there (outline on F.Fab only)
    return f'''(footprint "ESP32_C6_D1_Socket" (version 20221018) (generator kicadgen) (layer "F.Cu")
  (descr "xyzroe ESP32_C6_D1 (Wemos D1 form factor) in 2x 1x8 female Dupont headers, 2.54 mm, rows 22.86 mm apart. Antenna -y, USB +y. Keep copper out from under the antenna.")
  (tags "ESP32-C6 D1 mini socket dupont")
  (attr through_hole)
  (fp_text reference "REF**" (at 0 -19.3) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value "ESP32_C6_D1_Socket" (at 0 19.2) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_line (start {x0} {y0}) (end {x1} {y0}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start {x0} {y0}) (end {x0} {y1 - 4.5}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_line (start {x1} {y0}) (end {x1} {y1 - 4.5}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
  (fp_rect (start {x0} {y0}) (end {x1} {y1}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab"))
  (fp_rect (start {x0 - 0.25} {y0 - 0.25}) (end {x1 + 0.25} {y1 + 0.25}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd"))
  (fp_line (start {x0} -12.0) (end {x1} -12.0) (stroke (width 0.12) (type dash)) (layer "F.SilkS"))
  (fp_text user "ANTENNA - no copper below" (at 0 -15.0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
  (fp_text user "USB-C" (at 0 16.6) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
{chr(10).join(labels)}
{chr(10).join(pads)}
)
'''


FOOTPRINTS = {"ESP32_C6_D1_Socket": _esp32_c6_d1_socket}


# ---------------- PCBWay BOM
# (value, footprint name) -> (manufacturer, part number, description); value None = any value
MPN = {
    ("47u 35V", "CP_Elec_6.3x7.7"): ("Nichicon", "UUD1V470MCL1GS", "Capacitor aluminium electrolytic 47 uF 35 V, 6.3 x 7.7 mm"),
    ("100n 50V", "C_0603_1608Metric"): ("Murata", "GRT188R71H104KE13D", "Capacitor 100 nF 50 V X7R 0603"),
    ("100n", "C_0603_1608Metric"): ("Murata", "GRT188R71H104KE13D", "Capacitor 100 nF 50 V X7R 0603"),
    ("10u 50V", "C_1206_3216Metric"): ("Samsung", "CL31B106KBHNNNE", "Capacitor 10 uF 50 V X7R 1206"),
    ("1u 50V", "C_1206_3216Metric"): ("NIC Components", "NMC1206X7R105K50TRPLPF", "Capacitor 1 uF 50 V X7R 1206"),
    ("22u 10V", "C_1206_3216Metric"): ("Samsung", "CL31B226KPHNNNE", "Capacitor 22 uF 10 V X7R 1206"),
    ("22n", "C_0603_1608Metric"): ("Samsung", "CL10B223KB8NNNC", "Capacitor 22 nF 50 V X7R 0603"),
    ("4u7 10V", "C_0603_1608Metric"): ("Murata", "GRM188R6YA475KE15D", "Capacitor 4.7 uF 35 V X5R 0603"),
    ("1u 10V", "C_0603_1608Metric"): ("Samsung", "CL10B105KP8NNNC", "Capacitor 1 uF 10 V X7R 0603"),
    ("SMBJ26A", "D_SMB"): ("Vishay", "SMB10J26A-E3/52", "TVS diode 26 V unidirectional, SMB"),
    ("BZT52C12", "D_SOD-123"): ("onsemi", "MMSZ5242BT1G", "Zener 12 V SOD-123"),
    ("1N4148W", "D_SOD-123"): ("onsemi", "MMSD4148T1G", "Diode 1N4148W SOD-123"),
    ("5A fast", "Fuse_1206_3216Metric"): ("Bel Fuse", "C1Q 5", "Fuse 5 A fast 1206"),
    ("0.5A PTC", "Fuse_1206_3216Metric"): ("Littelfuse", "NANOSMDC050F/13.2-2", "PTC fuse 0.5 A 1206"),
    ("10A mini blade", "Fuseholder_Blade_Mini_Keystone_3568"): ("Keystone", "3568", "Mini blade fuse holder, PCB (fuse not included)"),
    (None, "AMASS_XT30PW-M_1x02_P2.50mm_Horizontal"): ("Amass", "XT30PW-M", "XT30 PCB connector, right angle, male"),
    (None, "AMASS_XT30PW-F_1x02_P2.50mm_Horizontal"): ("Amass", "XT30PW-F", "XT30 PCB connector, right angle, female"),
    (None, "AMASS_XT30UPB-F_1x02_P5.0mm_Vertical"): ("Amass", "XT30UPB-F", "XT30 PCB connector, vertical, female"),
    (None, "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"): ("JST", "B4B-XH-A(LF)(SN)", "JST-XH header 4-pin vertical"),
    (None, "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"): ("JST", "SM04B-SRSS-TB(LF)(SN)", "JST-SH header 4-pin (Qwiic)"),
    (None, "FanPinHeader_1x04_P2.54mm_Vertical"): ("Molex", "0470531000", "4-pin PC fan header"),
    (None, "TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"): ("Phoenix Contact", "1715035", "Screw terminal 3-pole 5.0 mm (MKDS 1,5/3)"),
    (None, "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical"): ("JST", "B2B-PH-K-S(LF)(SN)", "JST-PH header 2-pin vertical"),
    (None, "JST_VH_B6P-VH_1x06_P3.96mm_Vertical"): ("JST", "B6P-VH", "JST-VH header 6-pin vertical"),
    (None, "PinHeader_1x01_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x1 2.54 mm"),
    (None, "PinHeader_1x02_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x2 2.54 mm"),
    (None, "PinHeader_1x04_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x4 2.54 mm"),
    (None, "PinHeader_1x07_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x7 2.54 mm"),
    (None, "ESP32_C6_D1_Socket"): ("Sullins", "2x PPTC081LFBN-RC", "Socket for the ESP32-C6 D1: 2x female header 1x8 2.54 mm"),
    ("6.8u", "L_Vishay_IHLP-2525"): ("Vishay", "IHLP2525CZER6R8M01", "Power inductor 6.8 uH shielded, IHLP-2525"),
    ("FDMC8327L", None): ("onsemi", "FDMC8327L", "N-MOSFET 40 V Power33"),
    ("2N7002K", "SOT-23"): ("Diotec", "2N7002", "N-MOSFET 60 V SOT-23"),
    ("AOD4185", "TO-252-2"): ("Alpha & Omega", "AOD4185", "P-MOSFET -40 V TO-252"),
    ("10m 1%", "R_2512_6332Metric"): ("Vishay", "WSL2512R0100FEA", "Current-sense resistor 10 mOhm 1% 1 W 2512"),
    ("10k 0.1%", "R_0603_1608Metric"): ("Bourns", "CRT0603-BY-1002ELF", "Resistor 10 k 0.1% 25 ppm 0603"),
    ("63k4 1%", "R_0603_1608Metric"): ("Vishay", "CRCW060363K4FKEA", "Resistor 63.4 k 1% 0603"),
    ("10k", "R_0603_1608Metric"): ("Panasonic", "ERJ-3EKF1002V", "Resistor 10 k 1% 0603"),
    ("100k", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07100KL", "Resistor 100 k 1% 0603"),
    ("47k", "R_0603_1608Metric"): ("Yageo", "RC0603FR-0747KL", "Resistor 47 k 1% 0603"),
    ("4k7", "R_0603_1608Metric"): ("Vishay", "CRCW06034K70FKEA", "Resistor 4.7 k 1% 0603"),
    ("100", "R_0603_1608Metric"): ("KOA Speer", "RK73H1JTTD1000F", "Resistor 100 Ohm 1% 0603"),
    ("270", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07270RL", "Resistor 270 Ohm 1% 0603"),
    ("330", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07330RL", "Resistor 330 Ohm 1% 0603"),
    ("560", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07560RL", "Resistor 560 Ohm 1% 0603"),
    ("100 2W", None): ("Vishay", "PR02000201000JR500", "Resistor 100 Ohm 2 W metal film, axial; mount 2-3 mm above the board"),
    ("10k NTC B3380", None): ("Murata", "NCP18XH103F03RB", "NTC thermistor 10 k B3380 1% 0603"),
    ("4k7 x4", None): ("Panasonic", "EXB-38V472JV", "Resistor array 4 x 4.7 k 0603"),
    ("5V active", None): ("Same Sky", "CMI-1275-05TH", "Buzzer 12 mm 5 V active (7.6 mm pin pitch)"),
    ("TSR 1-2450", None): ("TRACO Power", "TSR 1-2450E", "5 V 1 A switching regulator, SIP-3"),
    ("LTC4162EUFD-LAD", None): ("Analog Devices", "LTC4162EUFD-LAD#PBF", "Li-ion charger, I2C, QFN-28 4x5 (must be the -LAD)"),
    ("PCA9554PW", None): ("Texas Instruments", "TCA9554PWR", "8-bit I2C I/O expander TSSOP-16"),
    ("PESD5V0S2UT", None): ("Nexperia", "PESD5V2S2UT,215", "ESD protection 5 V SOT-23"),
    ("TLV7031DBV", None): ("Texas Instruments", "TLV7031DBVR", "Comparator push-pull SOT-23-5"),
    ("TCA9548APWR", None): ("NXP", "PCA9548APW,118", "8-channel I2C mux TSSOP-24"),
}

PCBWAY_NOTES = {
    "3568": "Holder only; no fuse",
    "PR02000201000JR500": "Mount 2-3 mm above the board (heat)",
    "LTC4162EUFD-LAD#PBF": "Must be the -LAD version; no substitute",
}


# ---------------- copper renders
NET_COLORS = {"GND": (60, 60, 70), "+24V": (220, 50, 50), "VIN": (240, 120, 40), "CLP": (240, 170, 60),
         "VOUT": (230, 210, 60), "SW": (200, 60, 200), "CSP": (90, 200, 90), "BAT": (60, 160, 240),
         "BAT_F": (40, 110, 200), "+5V": (255, 140, 140)}
