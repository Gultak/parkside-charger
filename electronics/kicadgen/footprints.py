"""Custom footprints (library nickname "pcl"), written to <board>/pcl.pretty."""
from pathlib import Path

LIB = "pcl"


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


def write_library(board_dir):
    d = Path(board_dir) / f"{LIB}.pretty"
    d.mkdir(parents=True, exist_ok=True)
    for name, fn in FOOTPRINTS.items():
        (d / f"{name}.kicad_mod").write_text(fn())
    (Path(board_dir) / "fp-lib-table").write_text(
        f'(fp_lib_table\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")'
        f'(options "")(descr "parkside-charger custom footprints"))\n)\n')
    return d
