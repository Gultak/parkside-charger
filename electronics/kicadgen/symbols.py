"""Custom KiCad symbols shared by the parkside-charger boards (library nickname "pcl")."""

LIB = "pcl"


def F(x):
    return f"{x:.2f}".rstrip("0").rstrip(".")


def eff(hide=False, justify=None, size=1.27):
    j = f" (justify {justify})" if justify else ""
    h = " hide" if hide else ""
    return f"(effects (font (size {size} {size})){j}{h})"


def pin(num, name, x, y, ang, typ="passive", length=2.54, hide=False):
    hd = " hide" if hide else ""
    return (f'(pin {typ} line (at {F(x)} {F(y)} {ang}) (length {length}){hd} '
            f'(name "{name}" {eff()}) (number "{num}" {eff()}))')


def ic_symbol(name, ref, value, fp, ds, left, right, bottom=(), width=25.4, desc=""):
    """left/right: lists of (num, name, type) top-to-bottom; None = gap."""
    rows = max(len(left), len(right), 1)
    h = (rows + 1) * 2.54
    top = round(h / 2 / 2.54) * 2.54
    w2 = width / 2
    pins = []
    for side, lst in (("L", left), ("R", right)):
        for i, p in enumerate(lst):
            if p is None:
                continue
            y = top - 2.54 * (i + 1)
            x = -w2 - 2.54 if side == "L" else w2 + 2.54
            pins.append(pin(p[0], p[1], x, y, 0 if side == "L" else 180, p[2]))
    bot = top - h
    for i, p in enumerate(bottom):
        x = (i - (len(bottom) - 1) / 2) * 2.54
        pins.append(pin(p[0], p[1], x, bot - 2.54, 90, p[2]))
    body = "\n".join("      " + p for p in pins)
    return f'''  (symbol "{name}" (in_bom yes) (on_board yes)
    (property "Reference" "{ref}" (at {F(-w2)} {F(top + 1.27)} 0) {eff(justify="left bottom")})
    (property "Value" "{value}" (at {F(w2)} {F(top + 1.27)} 0) {eff(justify="right bottom")})
    (property "Footprint" "{fp}" (at 0 0 0) {eff(hide=True)})
    (property "Datasheet" "{ds}" (at 0 0 0) {eff(hide=True)})
    (property "ki_description" "{desc}" (at 0 0 0) {eff(hide=True)})
    (symbol "{name}_0_1"
      (rectangle (start {F(-w2)} {F(top)}) (end {F(w2)} {F(bot)}) (stroke (width 0.254) (type default)) (fill (type background)))
    )
    (symbol "{name}_1_1"
{body}
    )
  )'''


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


def library_text():
    return "(kicad_symbol_lib (version 20220914) (generator kicadgen)\n" + "\n".join(SYMBOLS.values()) + "\n)\n"
