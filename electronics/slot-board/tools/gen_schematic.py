"""Generate slot_board.kicad_sch (KiCad 7) + the custom symbol library from design.py.

Wiring style: every pin gets a short wire stub and a net label (no long wires),
grouped by function. Run:  python3 gen_schematic.py <output_dir>
"""
import re
import sys
import uuid
from pathlib import Path

from design import NO_CONNECT, PARTS

STD_SYM = Path("/usr/share/kicad/symbols")
PROJECT = "slot_board"
ROOT_UUID = "5a1c0b0a-7d1e-4c3a-9a47-2f6f3c0b0001"


def uid():
    return str(uuid.uuid4())


def F(x):  # number formatting
    return f"{x:.2f}".rstrip("0").rstrip(".")


def eff(hide=False, justify=None, size=1.27):
    j = f" (justify {justify})" if justify else ""
    h = " hide" if hide else ""
    return f"(effects (font (size {size} {size})){j}{h})"


# --------------------------------------------------------------- custom lib --
def pin(num, name, x, y, ang, typ="passive", length=2.54, hide_name=False):
    return (f'(pin {typ} line (at {F(x)} {F(y)} {ang}) (length {length}) '
            f'(name "{name}" {eff()}) (number "{num}" {eff()}))')


def ic_symbol(name, ref, value, fp, ds, left, right, bottom=(), width=25.4, desc=""):
    """left/right: list of (num, name, type) top-to-bottom; None = gap."""
    rows = max(len(left), len(right))
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
      {chr(10).join("      " + p for p in pins)}
    )
  )'''


LTC = ic_symbol(
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
    width=22.86,
    desc="35V/3.2A multicell Li-ion step-down charger, PowerPath, I2C telemetry (I2C adjustable)",
)
PCA = ic_symbol(
    "PCA9554", "U", "PCA9554PW", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm",
    "https://www.nxp.com/docs/en/data-sheet/PCA9554_9554A.pdf",
    left=[("16", "VDD", "power_in"), ("14", "SCL", "input"), ("15", "SDA", "bidirectional"),
          ("13", "~{INT}", "open_collector"), None, ("1", "A0", "input"), ("2", "A1", "input"),
          ("3", "A2", "input"), None, ("8", "VSS", "power_in")],
    right=[("4", "IO0", "bidirectional"), ("5", "IO1", "bidirectional"), ("6", "IO2", "bidirectional"),
           ("7", "IO3", "bidirectional"), ("9", "IO4", "bidirectional"), ("10", "IO5", "bidirectional"),
           ("11", "IO6", "bidirectional"), ("12", "IO7", "bidirectional")],
    width=15.24, desc="8-bit I2C I/O expander with interrupt",
)
ESD = ic_symbol(
    "ESD_2CH", "U", "PESD5V0S2UT", "Package_TO_SOT_SMD:SOT-23",
    "https://assets.nexperia.com/documents/data-sheet/PESD5V0S2UT.pdf",
    left=[("1", "IO1", "passive"), ("2", "IO2", "passive")], right=[], bottom=[("3", "GND", "passive")],
    width=7.62, desc="Double ESD protection diode array, common anode",
)
NMOS = '''  (symbol "NMOS_Power33" (in_bom yes) (on_board yes)
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
CUSTOM_LIB = "(kicad_symbol_lib (version 20220914) (generator gen_schematic)\n" + "\n".join(
    [LTC, PCA, ESD, NMOS]) + "\n)\n"


# --------------------------------------------------------- symbol handling --
def extract_symbol(lib_text, name):
    """Return the raw s-expression of a top-level symbol in a .kicad_sym text."""
    m = re.search(r'\n  \(symbol "' + re.escape(name) + r'"', lib_text)
    if not m:
        raise KeyError(name)
    i, depth = m.start() + 3, 0
    for j in range(i, len(lib_text)):
        c = lib_text[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return lib_text[i:j + 1]
    raise ValueError(name)


_lib_cache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _lib_cache:
        _lib_cache[lib] = CUSTOM_LIB if lib == "slot_board" else (STD_SYM / f"{lib}.kicad_sym").read_text()
    txt = extract_symbol("\n" + _lib_cache[lib], name)
    if "(extends " in txt:
        raise NotImplementedError(f"{lib_id} extends another symbol")
    return txt


def pins_of(sym_text):
    """pin number -> (x, y, angle) in symbol (y-up) coordinates."""
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]+)"', sym_text, re.S):
        out[m.group(4)] = (float(m.group(1)), float(m.group(2)), int(m.group(3)))
    return out


# ------------------------------------------------------------------ layout --
# (x, y) placement on an A3 sheet, grouped by function. Units: mm, grid 2.54.
G = 2.54
PLACE = {
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
SNAP = lambda v: round(v / G) * G


def label_angle(pin_ang):
    return (pin_ang + 180) % 360


def build(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "slot_board.kicad_sym").write_text(CUSTOM_LIB)

    used_ids = sorted({p[1] for p in PARTS.values()})
    lib_syms = {}
    for lid in used_ids:
        raw = lib_symbol(lid)
        name = lid.split(":")[1]
        lib_syms[lid] = raw.replace(f'(symbol "{name}"', f'(symbol "{lid}"', 1)

    items = []
    for ref, (value, lid, fp, pinnets, mpn) in PARTS.items():
        X, Y = (SNAP(c) for c in PLACE[ref])
        sym_pins = pins_of(lib_syms[lid])
        rect = re.search(r"\(rectangle \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)", lib_syms[lid])
        if lid.startswith("slot_board:") and rect:  # ICs: ref/value above and below the body
            x0, top, _x1, bot = (float(v) for v in rect.groups())
            rpos, vpos = (X + x0, Y - top - 1.27), (X - x0 + 2.54, Y - bot + 5.08)
        else:
            rpos, vpos = (X + 2.54, Y - 6.35), (X + 2.54, Y + 6.35)
        props = [
            ("Reference", ref, rpos),
            ("Value", value, vpos),
            ("Footprint", fp, (X, Y)),
            ("Datasheet", "~", (X, Y)),
            ("MPN", mpn, (X, Y)),
        ]
        ptxt = []
        for k, v, (px, py) in props:
            hide = k not in ("Reference", "Value")
            v = v.replace('"', "'")
            ptxt.append(f'    (property "{k}" "{v}" (at {F(px)} {F(py)} 0) {eff(hide=hide, justify="left")})')
        pin_uuids = "\n".join(f'    (pin "{n}" (uuid {uid()}))' for n in sym_pins)
        items.append(f'''  (symbol (lib_id "{lid}") (at {F(X)} {F(Y)} 0) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced)
    (uuid {uid()})
{chr(10).join(ptxt)}
{pin_uuids}
    (instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))
  )''')
        # wires + labels / no-connects
        drawn = set()
        for num, (px, py, pa) in sym_pins.items():
            sx, sy = X + px, Y - py  # symbol y-up -> sheet y-down
            if (round(sx, 2), round(sy, 2)) in drawn:
                continue  # stacked pins (e.g. MOSFET sources)
            drawn.add((round(sx, 2), round(sy, 2)))
            net = pinnets.get(num)
            if net is None:
                if num in NO_CONNECT.get(ref, []):
                    items.append(f"  (no_connect (at {F(sx)} {F(sy)}) (uuid {uid()}))")
                    continue
                raise ValueError(f"{ref}.{num} has no net and is not marked no-connect")
            la = label_angle(pa)
            dx, dy = {0: (2.54, 0), 90: (0, -2.54), 180: (-2.54, 0), 270: (0, 2.54)}[la]
            ex, ey = sx + dx, sy + dy
            items.append(f"  (wire (pts (xy {F(sx)} {F(sy)}) (xy {F(ex)} {F(ey)})) "
                         f"(stroke (width 0) (type default)) (uuid {uid()}))")
            just = {0: "left", 90: "left", 180: "right", 270: "right"}[la]
            items.append(f'  (label "{net}" (at {F(ex)} {F(ey)} {la}) (fields_autoplaced) '
                         f'{eff(justify=just + " bottom")} (uuid {uid()}))')

    title = '''  (title_block
    (title "Parkside X20V slot charger board")
    (rev "A")
    (company "ha-esphome-projects / parkside-charger")
    (comment 1 "LTC4162-LAD 5S Li-ion charger, PCA9554 slot I/O")
    (comment 2 "Generated by tools/gen_schematic.py from tools/design.py - edit design.py, not this file")
  )'''
    texts = [
        ("INPUT 24 V, reverse-blocking INFET, input current sense", 20, 30),
        ("LTC4162-LAD CHARGER (datasheet typ. application, 5 cells)", 150, 30),
        ("BATTERY", 295, 30),
        ("I2C (5 V slot bus via TCA9548A channel), PCA9554 @0x20, LTC4162 @0x68", 20, 150),
        ("PRESENCE SWITCH / RGB LED (common cathode)", 220, 150),
        ("BLEED-DOWN TO STORAGE VOLTAGE (~0.1 A)", 220, 200),
    ]
    ttxt = "\n".join(f'  (text "{t}" (at {F(x)} {F(y)} 0) {eff(justify="left bottom", size=2)} (uuid {uid()}))'
                     for t, x, y in texts)
    sch = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A3")
{title}
  (lib_symbols
{chr(10).join(lib_syms.values())}
  )
{ttxt}
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
)
'''
    (outdir / "slot_board.kicad_sch").write_text(sch)
    (outdir / "sym-lib-table").write_text(
        '(sym_lib_table\n  (lib (name "slot_board")(type "KiCad")(uri "${KIPRJMOD}/slot_board.kicad_sym")'
        '(options "")(descr "Parkside slot board custom symbols"))\n)\n')
    print("schematic written:", outdir / "slot_board.kicad_sch")


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else ".."))
