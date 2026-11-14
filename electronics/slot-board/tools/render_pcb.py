"""Render the slot board copper layers coloured by net (PNG) for review/docs.
Usage: /usr/bin/python3 render_pcb.py ../slot_board.kicad_pcb out_dir"""
import colorsys
import sys
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

SCALE = 20  # px per mm
FIXED = {"GND": (60, 60, 70), "+24V": (220, 50, 50), "VIN": (240, 120, 40), "CLP": (240, 170, 60),
         "VOUT": (230, 210, 60), "SW": (200, 60, 200), "CSP": (90, 200, 90), "BAT": (60, 160, 240),
         "BAT_F": (40, 110, 200), "+5V": (255, 140, 140)}


def color(net):
    if net in FIXED:
        return FIXED[net]
    h = (hash(net) % 997) / 997.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.55, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)


def main(pcb, outdir):
    board = pcbnew.LoadBoard(pcb)
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0 = pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY())
    W, H = pcbnew.ToMM(bb.GetWidth()), pcbnew.ToMM(bb.GetHeight())

    def px(v):
        return ((pcbnew.ToMM(v.x) - x0) * SCALE, (pcbnew.ToMM(v.y) - y0) * SCALE)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    for lname, layer in (("top", pcbnew.F_Cu), ("bottom", pcbnew.B_Cu), ("inner1", pcbnew.In1_Cu)):
        img = Image.new("RGB", (int(W * SCALE) + 1, int(H * SCALE) + 1), (15, 15, 20))
        d = ImageDraw.Draw(img)
        for z in board.Zones():
            if not z.IsOnLayer(layer):
                continue
            net = z.GetNetname().lstrip("/")
            polys = z.GetFilledPolysList(layer)
            for k in range(polys.OutlineCount()):
                o = polys.Outline(k)
                d.polygon([px(o.CPoint(i)) for i in range(o.PointCount())], fill=color(net))
                for h in range(polys.HoleCount(k)):
                    ho = polys.Hole(k, h)
                    d.polygon([px(ho.CPoint(i)) for i in range(ho.PointCount())], fill=(15, 15, 20))
        for t in board.GetTracks():
            if not t.IsOnLayer(layer):
                continue
            net = t.GetNetname().lstrip("/")
            if t.GetClass() == "PCB_VIA":
                cx, cy = px(t.GetPosition())
                r = pcbnew.ToMM(t.GetWidth()) / 2 * SCALE
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color(net), outline=(255, 255, 255))
                continue
            w = max(1, int(pcbnew.ToMM(t.GetWidth()) * SCALE))
            a, b = px(t.GetStart()), px(t.GetEnd())
            d.line([a, b], fill=color(net), width=w)
            for p in (a, b):
                d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=color(net))
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if not pad.IsOnLayer(layer):
                    continue
                net = pad.GetNetname().lstrip("/")
                poly = pad.GetEffectivePolygon()
                for k in range(poly.OutlineCount()):
                    o = poly.Outline(k)
                    d.polygon([px(o.CPoint(i)) for i in range(o.PointCount())],
                              fill=color(net) if net else (120, 120, 120), outline=(255, 255, 255))
            if layer == pcbnew.F_Cu:
                cx, cy = px(fp.GetPosition())
                d.text((cx + 4, cy - 16), fp.GetReference(), fill=(255, 255, 255), font=font)
        # legend
        ly = 6
        for net in sorted({p.GetNetname().lstrip("/") for f in board.GetFootprints() for p in f.Pads()} - {""}):
            if net in FIXED:
                d.rectangle([6, ly, 18, ly + 12], fill=color(net))
                d.text((22, ly - 1), net, fill=(255, 255, 255), font=font)
                ly += 16
        img.save(out / f"pcb_{lname}.png")
        print("wrote", out / f"pcb_{lname}.png")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
