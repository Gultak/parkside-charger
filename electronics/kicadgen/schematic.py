"""Generate <project>.kicad_sch (KiCad 7) from a board's design module.

design module:  PARTS {ref: (value, lib_id, footprint, {pin: net}, mpn)}, NO_CONNECT {ref: [pins]}
layout module:  SCH_PLACE {ref: (x, y)}, SCH_TEXTS [(text, x, y)], TITLE, COMMENTS, PAPER
Wiring style: every pin gets a short wire stub and a net label.
"""
import re
import uuid
from pathlib import Path

from . import symbols

STD_SYM = Path("/usr/share/kicad/symbols")
G = 2.54


def uid():
    return str(uuid.uuid4())


F = symbols.F
eff = symbols.eff


def extract_symbol(lib_text, name):
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
        _lib_cache[lib] = symbols.library_text() if lib == symbols.LIB else (STD_SYM / f"{lib}.kicad_sym").read_text()
    txt = extract_symbol("\n" + _lib_cache[lib], name)
    if "(extends " in txt:
        raise NotImplementedError(f"{lib_id} extends another symbol")
    return txt


def pins_of(sym_text):
    out = {}
    for m in re.finditer(r'\(pin \w+ \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\).*?\(number "([^"]+)"', sym_text, re.S):
        out[m.group(4)] = (float(m.group(1)), float(m.group(2)), int(m.group(3)))
    return out


def snap(v):
    return round(v / G) * G


def build(design, layout, outdir: Path, project: str, root_uuid: str):
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"{symbols.LIB}.kicad_sym").write_text(symbols.library_text())

    used = sorted({p[1] for p in design.PARTS.values()})
    lib_syms = {}
    for lid in used:
        raw = lib_symbol(lid)
        name = lid.split(":")[1]
        lib_syms[lid] = raw.replace(f'(symbol "{name}"', f'(symbol "{lid}"', 1)

    items = []
    for ref, (value, lid, fp, pinnets, mpn) in design.PARTS.items():
        X, Y = (snap(c) for c in layout.SCH_PLACE[ref])
        sym_pins = pins_of(lib_syms[lid])
        rect = re.search(r"\(rectangle \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\)", lib_syms[lid])
        if lid.startswith(symbols.LIB + ":") and rect:
            x0, top, _x1, bot = (float(v) for v in rect.groups())
            rpos, vpos = (X + x0, Y - top - 1.27), (X - x0 + 2.54, Y - bot + 5.08)
        else:
            rpos, vpos = (X + 2.54, Y - 6.35), (X + 2.54, Y + 6.35)
        props = [("Reference", ref, rpos), ("Value", value, vpos), ("Footprint", fp, (X, Y)),
                 ("Datasheet", "~", (X, Y)), ("MPN", mpn, (X, Y))]
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
    (instances (project "{project}" (path "/{root_uuid}" (reference "{ref}") (unit 1))))
  )''')
        drawn = set()
        for num, (px, py, pa) in sym_pins.items():
            sx, sy = X + px, Y - py
            if (round(sx, 2), round(sy, 2)) in drawn:
                continue
            drawn.add((round(sx, 2), round(sy, 2)))
            net = pinnets.get(num)
            if net is None:
                if num in design.NO_CONNECT.get(ref, []):
                    items.append(f"  (no_connect (at {F(sx)} {F(sy)}) (uuid {uid()}))")
                    continue
                raise ValueError(f"{ref}.{num} has no net and is not marked no-connect")
            la = (pa + 180) % 360
            dx, dy = {0: (2.54, 0), 90: (0, -2.54), 180: (-2.54, 0), 270: (0, 2.54)}[la]
            ex, ey = sx + dx, sy + dy
            items.append(f"  (wire (pts (xy {F(sx)} {F(sy)}) (xy {F(ex)} {F(ey)})) "
                         f"(stroke (width 0) (type default)) (uuid {uid()}))")
            just = {0: "left", 90: "left", 180: "right", 270: "right"}[la]
            items.append(f'  (label "{net}" (at {F(ex)} {F(ey)} {la}) (fields_autoplaced) '
                         f'{eff(justify=just + " bottom")} (uuid {uid()}))')

    comments = "\n".join(f'    (comment {i + 1} "{c}")' for i, c in enumerate(layout.COMMENTS))
    title = f'''  (title_block
    (title "{layout.TITLE}")
    (rev "{getattr(layout, "REV", "A")}")
    (company "github.com/Gultak/parkside-charger")
{comments}
  )'''
    ttxt = "\n".join(f'  (text "{t}" (at {F(x)} {F(y)} 0) {eff(justify="left bottom", size=2)} (uuid {uid()}))'
                     for t, x, y in layout.SCH_TEXTS)
    sch = f'''(kicad_sch (version 20230121) (generator eeschema)
  (uuid {root_uuid})
  (paper "{getattr(layout, "PAPER", "A3")}")
{title}
  (lib_symbols
{chr(10).join(lib_syms.values())}
  )
{ttxt}
{chr(10).join(items)}
  (sheet_instances (path "/" (page "1")))
)
'''
    (outdir / f"{project}.kicad_sch").write_text(sch)
    (outdir / "sym-lib-table").write_text(
        f'(sym_lib_table\n  (lib (name "{symbols.LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{symbols.LIB}.kicad_sym")'
        '(options "")(descr "parkside-charger custom symbols"))\n)\n')
    return outdir / f"{project}.kicad_sch"
