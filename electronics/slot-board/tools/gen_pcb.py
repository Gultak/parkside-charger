"""Generate slot_board.kicad_pcb (KiCad 7, 4 layers) from design.py.

  * placement follows the LTC4162 datasheet layout rules (p.34/35): VOUT bypass
    caps directly at pins 27/28 -> 23/24, SW leaves between their pads straight
    into the inductor, Kelvin sense traces to the sense resistor pads,
    In1/In2 = unbroken GND planes
  * power nets are copper pours on F.Cu, small signals are routed by a simple
    grid maze router (A*, F.Cu/B.Cu, 0.1 mm grid), every GND pad gets a via
  * finally zones are filled and the KiCad DRC is run

Run with the system python that has the pcbnew module:  /usr/bin/python3 gen_pcb.py ..
"""
import heapq
import math
import sys
from pathlib import Path

import numpy as np
import pcbnew

from design import DEFAULT_WIDTH, NET_WIDTH, PARTS

FPLIB = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board origin on the sheet (mm)
BW, BH = 72.0, 60.0            # board size: 72 wide (rides in the card guides), 60 long
EDGE_KEEP = 2.0                # card guides: keep parts this far from the long edges
CLEAR = 0.15                   # copper clearance (DRC rule)
RMARGIN = 0.03                 # extra margin the router keeps
VIA_D, VIA_DRILL = 0.6, 0.3
GRID = 0.1
DEBUG_DIR = "/tmp/claude-0/dbg"
PAD_HALO = 0.3
HW = 1.6                       # weighted A*: heuristic weight (>1 = faster, slightly longer paths)

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


def mm(v):
    return pcbnew.ToMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(float(OX + x)), pcbnew.FromMM(float(OY + y)))


LAYER = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}


class Router:
    """Grid maze router on F.Cu (0) and B.Cu (1)."""

    def __init__(self, board, nets):
        self.board, self.nets = board, nets
        self.nx, self.ny = int(BW / GRID) + 1, int(BH / GRID) + 1
        self.xs = np.arange(self.nx) * GRID
        self.ys = np.arange(self.ny) * GRID
        self.shapes = []   # (netname, layers(set of 0/1/'in'), kind, params)
        self.zones = []    # (netname, layer idx, polygon)
        self.added = 0
        self.net_cells = {}   # net -> cells of tracks already routed for it
        self.comps = {}       # net -> list of connected cell sets made by pad->pad routes
        self.vias = []

    # ---------------------------------------------------------- obstacles --
    def add_pad_shapes(self):
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                net = pad.GetNetname().lstrip("/")
                layers = set()
                if pad.IsOnLayer(pcbnew.F_Cu):
                    layers.add(0)
                if pad.IsOnLayer(pcbnew.B_Cu):
                    layers.add(1)
                if not layers:
                    continue
                pos = pad.GetPosition()
                cx, cy = mm(pos.x) - OX, mm(pos.y) - OY
                sx, sy = mm(pad.GetSize().x), mm(pad.GetSize().y)
                ang = round(pad.GetOrientationDegrees()) % 180
                if ang == 90:
                    sx, sy = sy, sx
                # halo: keep other nets a bit further from "big" pads so each
                # pad keeps an escape route and room for a via (not for
                # fine-pitch IC pins, where that would close the pin channels)
                halo = PAD_HALO if min(sx, sy) >= 0.55 else 0.0
                if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                    self.shapes.append((net, layers, "circle", (cx, cy, sx / 2 + halo)))
                else:
                    self.shapes.append((net, layers, "rect", (cx, cy, sx / 2 + halo, sy / 2 + halo)))
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or pad.GetDrillSize().x > 0:
                    # holes: keep vias / tracks of other nets away on both layers
                    self.shapes.append((net, {0, 1}, "circle", (cx, cy, max(sx, sy) / 2)))

    def add_track(self, net, layer, pts, w):
        for a, b in zip(pts, pts[1:]):
            self.shapes.append((net, {layer}, "seg", (a[0], a[1], b[0], b[1], w / 2)))

    def add_via(self, net, x, y):
        self.shapes.append((net, {0, 1}, "circle", (x, y, VIA_D / 2)))
        self.vias.append((x, y))

    def via_far(self, i, j, dmin=0.9):
        x, y = i * GRID, j * GRID
        return all((x - vx) ** 2 + (y - vy) ** 2 >= dmin * dmin for vx, vy in self.vias)

    def add_zone(self, net, layer, poly):
        self.zones.append((net, layer, poly))

    # ------------------------------------------------------ distance masks --
    def _window(self, x0, y0, x1, y1):
        i0 = max(0, int((x0) / GRID) - 1)
        i1 = min(self.nx, int((x1) / GRID) + 2)
        j0 = max(0, int((y0) / GRID) - 1)
        j1 = min(self.ny, int((y1) / GRID) + 2)
        return i0, i1, j0, j1

    def blocked(self, net, r):
        """per layer boolean arrays [ny, nx]: True = a track centre of half
        width r-CLEAR would violate clearance to other-net copper."""
        bl = [np.zeros((self.ny, self.nx), bool), np.zeros((self.ny, self.nx), bool)]
        for snet, layers, kind, p in self.shapes:
            if snet == net and net != "":
                continue
            if kind == "rect":
                cx, cy, hx, hy = p
                x0, y0, x1, y1 = cx - hx - r, cy - hy - r, cx + hx + r, cy + hy + r
            elif kind == "circle":
                cx, cy, rr = p
                x0, y0, x1, y1 = cx - rr - r, cy - rr - r, cx + rr + r, cy + rr + r
            else:
                ax, ay, bx, by, hw = p
                x0, y0 = min(ax, bx) - hw - r, min(ay, by) - hw - r
                x1, y1 = max(ax, bx) + hw + r, max(ay, by) + hw + r
            i0, i1, j0, j1 = self._window(x0, y0, x1, y1)
            if i0 >= i1 or j0 >= j1:
                continue
            X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
            if kind == "rect":
                dx = np.maximum(np.abs(X - cx) - hx, 0)
                dy = np.maximum(np.abs(Y - cy) - hy, 0)
                d = np.hypot(dx, dy)
            elif kind == "circle":
                d = np.hypot(X - cx, Y - cy) - rr
            else:
                vx, vy = bx - ax, by - ay
                L2 = vx * vx + vy * vy
                t = np.clip(((X - ax) * vx + (Y - ay) * vy) / L2, 0, 1) if L2 > 0 else 0
                d = np.hypot(X - (ax + t * vx), Y - (ay + t * vy)) - hw
            m = d < r
            for L in layers:
                bl[L][j0:j1, i0:i1] |= m
        # other-net pours (their area) and the board edge
        from PIL import Image, ImageDraw
        for znet, L, poly in self.zones:
            if znet == net:
                continue
            img = Image.new("1", (self.nx, self.ny), 0)
            ImageDraw.Draw(img).polygon([(x / GRID, y / GRID) for x, y in poly], fill=1)
            bl[L] |= np.array(img, bool)
        e = int(math.ceil((0.3 + r - CLEAR) / GRID))
        for L in (0, 1):
            bl[L][:e, :] = bl[L][-e:, :] = True
            bl[L][:, :e] = bl[L][:, -e:] = True
        return bl

    def cells_of_pad(self, pad):
        pos = pad.GetPosition()
        cx, cy = mm(pos.x) - OX, mm(pos.y) - OY
        sx, sy = mm(pad.GetSize().x), mm(pad.GetSize().y)
        if round(pad.GetOrientationDegrees()) % 180 == 90:
            sx, sy = sy, sx
        hx, hy = sx / 2 - 0.02, sy / 2 - 0.02
        if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
            hx = hy = sx / 2 * 0.6
        elif pad.GetShape() == pcbnew.PAD_SHAPE_OVAL:
            r0 = min(sx, sy) / 2
            hx, hy = sx / 2 - r0 + r0 * 0.6, sy / 2 - r0 + r0 * 0.6
        i0, i1, j0, j1 = self._window(cx - hx, cy - hy, cx + hx, cy + hy)
        cells = []
        for j in range(j0, j1):
            for i in range(i0, i1):
                if abs(self.xs[i] - cx) <= hx and abs(self.ys[j] - cy) <= hy:
                    for L in (0, 1):
                        if (L == 0 and pad.IsOnLayer(pcbnew.F_Cu)) or (L == 1 and pad.IsOnLayer(pcbnew.B_Cu)):
                            cells.append((L, i, j))
        if not cells:  # tiny pad: nearest grid point
            i, j = int(round(cx / GRID)), int(round(cy / GRID))
            cells = [(0, i, j)] if pad.IsOnLayer(pcbnew.F_Cu) else [(1, i, j)]
        return cells

    # -------------------------------------------------------------- A* -----
    def astar(self, net, width, sources, targets, via_ok=True, window=None, target_fn=None):
        r = CLEAR + width / 2 + RMARGIN
        bl = self.blocked(net, r)
        vb = self.blocked(net, CLEAR + VIA_D / 2 + RMARGIN)
        vblock = vb[0] | vb[1]
        tset = set(targets)
        for (L, i, j) in tset | set(sources):   # own pad cells are always allowed
            bl[L][j, i] = False
        tpts = np.array([(i, j) for (_L, i, j) in targets]) if targets else None

        def h(i, j):
            if tpts is None:
                return 0.0
            d = np.abs(tpts - (i, j))
            return HW * float(np.min(np.maximum(d[:, 0], d[:, 1]) + 0.414 * np.minimum(d[:, 0], d[:, 1])))

        if tpts is not None and len(tpts) > 400:
            tpts = tpts[:: max(1, len(tpts) // 400)]
        dirs = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
                (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        layer_cost = (1.0, 1.15)
        via_cost = 25.0
        openq, g, parent = [], {}, {}
        for s in sources:
            g[s] = 0.0
            parent[s] = None
            heapq.heappush(openq, (h(s[1], s[2]), 0.0, s, -1))
        best = None
        expanded = 0
        while openq:
            f, gc, cur, pdir = heapq.heappop(openq)
            if gc > g.get(cur, 1e18):
                continue
            L, i, j = cur
            if cur in tset or (target_fn is not None and target_fn(L, i, j)):
                best = cur
                break
            expanded += 1
            if expanded > 1500000:
                break
            for k, (di, dj, c) in enumerate(dirs):
                ni, nj = i + di, j + dj
                if not (0 <= ni < self.nx and 0 <= nj < self.ny):
                    continue
                if window and not (window[0] <= ni < window[1] and window[2] <= nj < window[3]):
                    continue
                if bl[L][nj, ni]:
                    continue
                if di and dj and (bl[L][j, ni] or bl[L][nj, i]):
                    continue  # no corner cutting
                ng = gc + c * layer_cost[L] + (0.6 if pdir not in (-1, k) else 0.0)
                nxt = (L, ni, nj)
                if ng < g.get(nxt, 1e18):
                    g[nxt] = ng
                    parent[nxt] = (cur, k)
                    heapq.heappush(openq, (ng + h(ni, nj), ng, nxt, k))
            if via_ok and not vblock[j, i] and not bl[1 - L][j, i] and self.via_far(i, j):
                nxt = (1 - L, i, j)
                ng = gc + via_cost
                if ng < g.get(nxt, 1e18):
                    g[nxt] = ng
                    parent[nxt] = (cur, -1)
                    heapq.heappush(openq, (ng + h(i, j), ng, nxt, -1))
        self.last_stats = (expanded, len(openq))
        if best is None:
            return None
        path = [best]
        while parent[path[-1]] is not None:
            path.append(parent[path[-1]][0])
        return path[::-1]

    # ------------------------------------------------------ commit to board -
    def commit(self, netobj, width, path):
        """turn a cell path into tracks + vias on the board."""
        net = netobj.GetNetname().lstrip("/")
        segs, vias = [], []
        cur_layer = path[0][0]
        run = [path[0]]
        for a in path[1:]:
            if a[0] != cur_layer:
                vias.append((self.xs[a[1]], self.ys[a[2]]))
                segs.append((cur_layer, run))
                run, cur_layer = [a], a[0]
            else:
                run.append(a)
        segs.append((cur_layer, run))
        for L, run in segs:
            pts = [(self.xs[i], self.ys[j]) for (_l, i, j) in run]
            # merge collinear points
            simp = [pts[0]]
            for k in range(1, len(pts) - 1):
                ax, ay = simp[-1]
                bx, by = pts[k]
                cx, cy = pts[k + 1]
                if abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) > 1e-9:
                    simp.append(pts[k])
            if len(pts) > 1:
                simp.append(pts[-1])
            for a, b in zip(simp, simp[1:]):
                t = pcbnew.PCB_TRACK(self.board)
                t.SetStart(P(*a))
                t.SetEnd(P(*b))
                t.SetWidth(pcbnew.FromMM(width))
                t.SetLayer(pcbnew.F_Cu if L == 0 else pcbnew.B_Cu)
                t.SetNet(netobj)
                self.board.Add(t)
                self.added += 1
            if len(simp) > 1:
                self.add_track(net, L, simp, width)
        for x, y in vias:
            if any(abs(x - vx) < 1e-6 and abs(y - vy) < 1e-6 for vx, vy in self.vias):
                continue
            add_via(self.board, netobj, x, y)
            self.add_via(net, x, y)
        cells = [(L, i, j) for (L, i, j) in path]
        self.net_cells.setdefault(net, set()).update(cells)
        return cells


def add_via(board, netobj, x, y):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetWidth(pcbnew.FromMM(VIA_D))
    v.SetDrill(pcbnew.FromMM(VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(netobj)
    board.Add(v)


def add_zone(board, netobj, layer, poly, priority, clearance=0.2, min_w=0.2):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(netobj)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
    z.SetAssignedPriority(priority)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetLocalClearance(pcbnew.FromMM(clearance))
    z.SetMinThickness(pcbnew.FromMM(min_w))
    z.SetIsFilled(False)
    board.Add(z)
    return z


# silkscreen labels: (text, x, y, size); pin labels read left to right as seen
# on the board (J2/J3/J4/J5 are rotated 180 deg)
LABELS = [
    ("PARKSIDE X20V SLOT rev A", 36.0, 58.6, 1.0), ("FRONT (battery side)", 20.0, 1.3, 0.9),
    ("IN: GND +24V", 8.0, 50.0, 0.8), ("OUT: +24V GND", 19.2, 50.0, 0.8),
    ("NTC GND B+", 40.5, 9.6, 0.8), ("SCL SDA GND 5V", 57.6, 50.9, 0.8),
    ("GND SW", 53.0, 7.6, 0.8), ("B G R GND", 63.5, 7.6, 0.8),
]


def place_references(fps, boxes, size=0.8):
    """put every reference designator next to its part where it overlaps nothing."""
    placed = [(x - 0.31 * sz * len(t) - 0.1, y - sz / 2 - 0.1, x + 0.31 * sz * len(t) + 0.1, y + sz / 2 + 0.1)
              for t, x, y, sz in LABELS]
    keep_out = list(boxes.values())

    def free(b, own):
        if b[0] < 0.4 or b[1] < 0.4 or b[2] > BW - 0.4 or b[3] > BH - 0.4:
            return False
        for o in keep_out:
            if o is own:
                continue
            if b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3]:
                return False
        return all(not (b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3]) for o in placed)

    for ref in sorted(fps, key=lambda r: (boxes[r][2] - boxes[r][0]) * (boxes[r][3] - boxes[r][1])):
        fp, bx = fps[ref], boxes[ref]
        w, h = 0.62 * size * len(ref) + 0.2, size + 0.2
        cx, cy = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        cands = [(cx, bx[1] - h / 2 - 0.05), (cx, bx[3] + h / 2 + 0.05),
                 (bx[0] - w / 2 - 0.05, cy), (bx[2] + w / 2 + 0.05, cy),
                 (bx[0] - w / 2, bx[1] - h / 2), (bx[2] + w / 2, bx[1] - h / 2),
                 (bx[0] - w / 2, bx[3] + h / 2), (bx[2] + w / 2, bx[3] + h / 2)]
        t = fp.Reference()
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(0.12))
        for x, y in cands:
            b = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
            if free(b, bx):
                t.SetTextAngleDegrees(0)
                t.SetPosition(P(x, y))
                placed.append(b)
                break
        else:   # no room: keep it on the fab layer only (assembly drawing)
            t.SetLayer(pcbnew.F_Fab)


def build(outdir: Path, promote=()):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = pcbnew.FromMM(0.15)
    ds.m_ViasMinSize = pcbnew.FromMM(0.5)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)   # U1 thermal vias (JLC 4-layer: 0.15 min)
    ds.m_CopperEdgeClearance = pcbnew.FromMM(0.3)
    ds.m_MinClearance = pcbnew.FromMM(0.127)    # footprint-inherent pin gaps (JLC 4-layer: 0.09 min)
    ds.m_HoleClearance = pcbnew.FromMM(0.2)
    nc = ds.m_NetSettings.m_DefaultNetClass
    nc.SetClearance(pcbnew.FromMM(0.13))      # router itself keeps CLEAR = 0.15
    nc.SetTrackWidth(pcbnew.FromMM(DEFAULT_WIDTH))
    nc.SetViaDiameter(pcbnew.FromMM(VIA_D))
    nc.SetViaDrill(pcbnew.FromMM(VIA_DRILL))

    # ---- nets
    netobjs = {}
    names = sorted({n for p in PARTS.values() for n in p[3].values()})
    for n in names:
        ni = pcbnew.NETINFO_ITEM(board, "/" + n)
        board.Add(ni)
        netobjs[n] = ni

    # ---- outline
    pts = [(0, 0), (BW, 0), (BW, BH), (0, BH)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)

    # ---- footprints
    fps = {}
    for ref, (value, _sym, fpid, pins, _mpn) in PARTS.items():
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(f"{FPLIB}/{lib}.pretty", name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(value)
        x, y, rot = PLACE[ref]
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)
        fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(0.8), pcbnew.FromMM(0.8)))
        fp.Reference().SetTextThickness(pcbnew.FromMM(0.12))
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in pins:
                pad.SetNet(netobjs[pins[num]])
            elif num == "" and pad.IsOnLayer(pcbnew.F_Cu) and "5" in pins:
                pad.SetNet(netobjs[pins["5"]])   # Power33 drain leads 5..8 are unnumbered
        board.Add(fp)
        fps[ref] = fp

    # ---- courtyard / edge check
    problems = []
    boxes = {}
    for ref, fp in fps.items():
        xs, ys = [], []
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_CrtYd:
                b = g.GetBoundingBox()
                xs += [mm(b.GetLeft()) - OX, mm(b.GetRight()) - OX]
                ys += [mm(b.GetTop()) - OY, mm(b.GetBottom()) - OY]
        boxes[ref] = (min(xs), min(ys), max(xs), max(ys))
        x0, y0, x1, y1 = boxes[ref]
        if x0 < EDGE_KEEP or x1 > BW - EDGE_KEEP or y0 < 0.25 or y1 > BH - 0.25:
            problems.append(f"{ref} courtyard outside keep-in: {boxes[ref]}")
    refs = list(boxes)
    for a in range(len(refs)):
        for b in range(a + 1, len(refs)):
            A, B = boxes[refs[a]], boxes[refs[b]]
            if A[0] < B[2] - 0.01 and B[0] < A[2] - 0.01 and A[1] < B[3] - 0.01 and B[1] < A[3] - 0.01:
                problems.append(f"courtyard overlap {refs[a]} / {refs[b]}")
    if problems:
        print("PLACEMENT PROBLEMS:\n  " + "\n  ".join(problems))

    place_references(fps, boxes)

    router = Router(board, netobjs)
    router.add_pad_shapes()

    # ---- pours, fixed copper
    for net, prio, poly in POURS:
        add_zone(board, netobjs[net], pcbnew.F_Cu, poly, prio)
        router.add_zone(net, 0, poly)
    for net, lay, w, pts in FIXED_TRACKS:
        for a, b in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(P(*a))
            t.SetEnd(P(*b))
            t.SetWidth(pcbnew.FromMM(w))
            t.SetLayer(LAYER[lay])
            t.SetNet(netobjs[net])
            board.Add(t)
        router.add_track(net, 0 if lay == "F" else 1, pts, w)
    for net, (x, y) in FIXED_VIAS:
        add_via(board, netobjs[net], x, y)
        router.add_via(net, x, y)

    def pad(ref, num):
        for p in fps[ref].Pads():
            if p.GetNumber() == num:
                return p
        raise KeyError(f"{ref}.{num}")

    def in_poly(x, y, poly):
        inside = False
        for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                inside = not inside
        return inside

    failures = []

    def route(net, src_cells, dst_cells, width, label):
        path = router.astar(net, width, src_cells, dst_cells)
        if path is None:
            failures.append(label)
            print("  FAILED", label, "expanded=%d open=%d" % router.last_stats)
            if DEBUG_DIR:
                from PIL import Image
                r = CLEAR + width / 2 + RMARGIN
                bl = router.blocked(net, r)
                L, i0, j0 = src_cells[0]
                win = (slice(max(0, j0 - 80), j0 + 80), slice(max(0, i0 - 80), i0 + 80))
                for Lx in (0, 1):
                    img = np.where(bl[Lx][win], 0, 255).astype(np.uint8)
                    rgb = np.stack([img] * 3, -1)
                    for (l2, i, j) in src_cells:
                        if l2 == Lx:
                            rgb[j - win[0].start, i - win[1].start] = (255, 0, 0)
                    Image.fromarray(rgb).resize((640, 640), Image.NEAREST).save(
                        f"{DEBUG_DIR}/fail_{len(failures)}_{net}_L{Lx}.png")
            return None
        return router.commit(netobjs[net], width, path)

    # ---- 1. Kelvin / sense connections (pad -> specific pad)
    for r1, p1, r2, p2 in KELVIN:
        a, b = pad(r1, p1), pad(r2, p2)
        net = a.GetNetname().lstrip("/")
        ca, cb = router.cells_of_pad(a), router.cells_of_pad(b)
        path = route(net, ca, cb, 0.2, f"{net}: {r1}.{p1}->{r2}.{p2}")
        if path:
            router.comps.setdefault(net, []).append(set(path) | set(ca) | set(cb))

    # ---- 2. all other non-GND nets: connect every pad to the growing tree
    netpads = {}
    for ref, fp in fps.items():
        for p in fp.Pads():
            n = p.GetNetname().lstrip("/")
            if n:
                netpads.setdefault(n, []).append(p)
    pour_of = {}
    for net, _pr, poly in POURS:
        pour_of.setdefault(net, []).append(poly)
    first = list(dict.fromkeys(list(promote) + ROUTE_ORDER_FIRST))
    order = first + sorted(n for n in netpads if n not in first and n not in ROUTE_ORDER_LAST and n != "GND")
    order += [n for n in ROUTE_ORDER_LAST if n not in first]
    for net in order:
        pads = netpads[net]
        width = NET_WIDTH.get(net, DEFAULT_WIDTH)
        tree_cells = set()
        todo = []
        for p in pads:
            pos = p.GetPosition()
            x, y = mm(pos.x) - OX, mm(pos.y) - OY
            if any(in_poly(x, y, poly) for poly in pour_of.get(net, [])):
                tree_cells |= set(router.cells_of_pad(p))
            else:
                todo.append(p)
        # pours themselves are part of the tree: sample cells well inside them
        for poly in pour_of.get(net, []):
            xs_ = [q[0] for q in poly]
            ys_ = [q[1] for q in poly]
            for x in np.arange(min(xs_) + 0.5, max(xs_) - 0.4, 0.3):
                for y in np.arange(min(ys_) + 0.5, max(ys_) - 0.4, 0.3):
                    if in_poly(x, y, poly) and in_poly(x - 0.4, y, poly) and in_poly(x + 0.4, y, poly) \
                            and in_poly(x, y - 0.4, poly) and in_poly(x, y + 0.4, poly):
                        tree_cells.add((0, int(round(x / GRID)), int(round(y / GRID))))
        # components: [main tree] + Kelvin components + single pads; merge overlaps
        comps = [set(c) for c in router.comps.get(net, [])] + [set(router.cells_of_pad(p)) for p in todo]
        if not tree_cells:
            tree_cells = comps.pop(0)
        merged = True
        while merged:
            merged = False
            for c in comps:
                if c & tree_cells:
                    tree_cells |= c
                    comps.remove(c)
                    merged = True
                    break
        while comps:
            sample = list(tree_cells)[:: max(1, len(tree_cells) // 1500)]
            def dist(c):
                L, i, j = next(iter(c))
                return min(abs(i - a) + abs(j - b) for (_l, a, b) in sample)
            comps.sort(key=dist)
            c = comps.pop(0)
            if c & tree_cells:
                tree_cells |= c
                continue
            path = route(net, list(c), list(tree_cells), width, f"{net}: component near {sorted(c)[0]}")
            tree_cells |= c
            if path:
                tree_cells |= set(path)

    # ---- 3. GND: a via (with a short stub) next to every SMD GND pad
    gnd = netobjs["GND"]
    gnd_poly = [poly for net, _p, poly in POURS if net == "GND"]
    for p in netpads["GND"]:
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or p.GetParent().GetReference() == "U1":
            continue  # through-hole pads reach the planes; U1 EP has thermal vias, PGND sits in the pour
        pos = p.GetPosition()
        x, y = mm(pos.x) - OX, mm(pos.y) - OY
        if any(in_poly(x, y, poly) for poly in gnd_poly):
            continue
        vb = router.blocked("GND", CLEAR + VIA_D / 2 + RMARGIN)
        vok = ~(vb[0] | vb[1])
        src = router.cells_of_pad(p)
        src = [c for c in src if c[0] == 0]
        i0, j0 = int(round(x / GRID)), int(round(y / GRID))
        win = (i0 - 30, i0 + 31, j0 - 30, j0 + 31)
        path = router.astar("GND", 0.3, src, [], via_ok=False, window=win,
                            target_fn=lambda L, i, j: L == 0 and vok[j, i] and math.hypot(i - i0, j - j0) > 6
                            and router.via_far(i, j))
        if path is None:
            failures.append(f"GND via for {p.GetParent().GetReference()}.{p.GetNumber()}")
            continue
        router.commit(gnd, 0.3, path)
        L, i, j = path[-1]
        add_via(board, gnd, router.xs[i], router.ys[j])
        router.add_via("GND", router.xs[i], router.ys[j])

    # ---- 4. GND everywhere else: inner planes + top/bottom fill
    full = [(0.0, 0.0), (BW, 0.0), (BW, BH), (0.0, BH)]
    # 24 V pass-through IN -> OUT also on B.Cu (chain current of all following slots)
    add_zone(board, netobjs["+24V"], pcbnew.B_Cu, POURS[0][2], 2)
    for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu, pcbnew.F_Cu):
        add_zone(board, gnd, lay, full, 0, clearance=0.25, min_w=0.25)

    # ---- silkscreen info
    def silk(text, x, y, size=1.0, layer=pcbnew.F_SilkS):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
        t.SetTextThickness(pcbnew.FromMM(size * 0.15))
        board.Add(t)
    for text, x, y, size in LABELS:
        silk(text, x, y, size)

    # ---- fill + DRC
    if failures:
        return None, failures
    out = outdir / "slot_board.kicad_pcb"
    board.Save(str(out))
    print("saved unfilled board, filling zones ...", flush=True)
    # filling a board built in memory crashes pcbnew 7; reload it from disk first
    board = pcbnew.LoadBoard(str(out))
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(str(out))
    rpt = outdir / "drc_report.txt"
    pcbnew.WriteDRCReport(board, str(rpt), pcbnew.EDA_UNITS_MILLIMETRES, True)
    import collections
    kinds = collections.Counter(ln.split("]")[0] + "]" for ln in rpt.read_text().splitlines() if ln.startswith("["))
    print("DRC:", dict(kinds))
    print(f"routed tracks: {router.added}, failures: {len(failures)}")
    for f in failures:
        print("   ", f)
    return out, failures


if __name__ == "__main__":
    import json
    import os
    import subprocess
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "..")
    if os.environ.get("GEN_PCB_CHILD"):
        out, failures = build(outdir, json.loads(os.environ["GEN_PCB_PROMOTE"]))
        print("RESULT " + json.dumps(failures))
        sys.exit(0)
    # pcbnew does not like a second board in one process: one attempt per child
    promote = []
    for attempt in range(int(os.environ.get("ATTEMPTS", 6))):
        env = dict(os.environ, GEN_PCB_CHILD="1", GEN_PCB_PROMOTE=json.dumps(promote))
        r = subprocess.run([sys.executable, __file__, str(outdir)], env=env, capture_output=True, text=True)
        print(r.stdout.replace("RESULT", "  result"), r.stderr[-2000:], end="")
        res = [ln for ln in r.stdout.splitlines() if ln.startswith("RESULT ")]
        if not res:
            sys.exit(f"attempt {attempt + 1} crashed (rc={r.returncode})")
        failures = json.loads(res[-1][7:])
        if not failures:
            print(f"attempt {attempt + 1}: all nets routed")
            break
        nets_failed = list(dict.fromkeys(f.split(":")[0] for f in failures))
        print(f"attempt {attempt + 1}: {len(failures)} failures -> promoting {nets_failed}")
        promote = list(dict.fromkeys(nets_failed + promote))
    else:
        sys.exit("routing failed")
