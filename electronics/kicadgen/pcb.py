"""Generic PCB generator (KiCad 7) driven by a board's design + layout modules.

  * places footprints, adds copper pours / fixed copper / keepouts from the layout
  * routes pad->pad priority connections (Kelvin etc.), then every other net with
    a grid maze router (A*, F.Cu/B.Cu, 0.1 mm grid), gives every SMD GND pad a via
  * GND planes on the inner layers + GND fill on the outer layers, zone fill, DRC

design module: PARTS, NET_WIDTH, DEFAULT_WIDTH
layout module: PROJECT, BW, BH, EDGE_KEEP, PLACE, POURS, FIXED_TRACKS, FIXED_VIAS,
               KELVIN, ROUTE_ORDER_FIRST, ROUTE_ORDER_LAST, LABELS, [KEEPOUTS], [CUTOUTS]
Run with the system python that has the pcbnew module.
"""
import heapq
import math
import os
import sys
from pathlib import Path

import numpy as np
import pcbnew


FPLIB = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0          # board origin on the sheet (mm)
BW, BH, EDGE_KEEP = 0.0, 0.0, 2.0   # set by configure()
OVERHANG = set()   # refs whose body may stick out over the board edge (e.g. horizontal connectors)
CLEAR = 0.15                   # copper clearance (DRC rule)
RMARGIN = 0.03                 # extra margin the router keeps
VIA_D, VIA_DRILL = 0.6, 0.3
GRID = 0.1
DEBUG_DIR = __import__("os").environ.get("KICADGEN_DEBUG")  # dump router maps on failure
PAD_HALO = 0.3
HW = 1.6                       # weighted A*: heuristic weight (>1 = faster, slightly longer paths)

PARTS, NET_WIDTH, DEFAULT_WIDTH = {}, {}, 0.2
PLACE, POURS, FIXED_TRACKS, FIXED_VIAS, KELVIN = {}, [], [], [], []
ROUTE_ORDER_FIRST, ROUTE_ORDER_LAST, LABELS, KEEPOUTS = [], [], [], []
CUTOUTS = []                   # round holes in the board: (x, y, diameter); copper keeps 0.5 mm away
PROJECT, BOARD_DIR = "board", Path(".")
GND_VIA_SKIP = set()


def configure(design, layout, board_dir):
    """inject the board-specific design/layout into this module."""
    g = globals()
    g.update(PARTS=design.PARTS, NET_WIDTH=getattr(design, "NET_WIDTH", {}),
             DEFAULT_WIDTH=getattr(design, "DEFAULT_WIDTH", 0.2), BOARD_DIR=Path(board_dir))
    for k in ("PROJECT", "BW", "BH", "EDGE_KEEP", "PLACE", "POURS", "FIXED_TRACKS", "FIXED_VIAS", "KELVIN",
              "ROUTE_ORDER_FIRST", "ROUTE_ORDER_LAST", "LABELS", "KEEPOUTS", "GND_VIA_SKIP", "CUTOUTS",
              "OVERHANG"):
        if hasattr(layout, k):
            g[k] = getattr(layout, k)


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
    if priority == 0:   # background GND fills: drop isolated fragments
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
    return z


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
                t.SetTextAngleDegrees(-fp.GetOrientationDegrees())   # horizontal on the board, as its box assumes
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
    for cx, cy, d in CUTOUTS:          # round cutout (e.g. screwdriver access)
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_CIRCLE)
        s.SetCenter(P(cx, cy))
        s.SetEnd(P(cx + d / 2, cy))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(pcbnew.FromMM(0.1))
        board.Add(s)

    # ---- footprints
    fps = {}
    for ref, (value, _sym, fpid, pins, _mpn) in PARTS.items():
        lib, name = fpid.split(":")
        libdir = BOARD_DIR / f"{lib}.pretty" if lib == "pcl" else Path(FPLIB) / f"{lib}.pretty"
        fp = pcbnew.FootprintLoad(str(libdir), name)
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
        if ref not in OVERHANG and (x0 < EDGE_KEEP or x1 > BW - EDGE_KEEP or y0 < 0.25 or y1 > BH - 0.25):
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
    if os.environ.get("KICADGEN_PLACE_ONLY"):     # quick look at placement + silkscreen, no routing
        for text, x, y, size in LABELS:
            t = pcbnew.PCB_TEXT(board); t.SetText(text); t.SetPosition(P(x, y)); t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(size), pcbnew.FromMM(size)))
            t.SetTextThickness(pcbnew.FromMM(size * 0.15)); board.Add(t)
        out = Path(os.environ["KICADGEN_PLACE_ONLY"])
        board.Save(str(out))
        return out, []

    router = Router(board, netobjs)
    router.add_pad_shapes()

    # ---- pours, fixed copper
    for pour in POURS:
        net, prio, poly = pour[:3]
        lay = pour[3] if len(pour) > 3 else "F"
        add_zone(board, netobjs[net], LAYER[lay], poly, prio)
        router.add_zone(net, 0 if lay == "F" else 1, poly)
    def octagon16(cx, cy, r):           # 16-gon circumscribing a circle of radius r
        return [(cx + r / math.cos(math.pi / 16) * math.cos(2 * math.pi * k / 16),
                 cy + r / math.cos(math.pi / 16) * math.sin(2 * math.pi * k / 16)) for k in range(16)]
    cut_keepouts = [octagon16(cx, cy, d / 2 + 0.5) for cx, cy, d in CUTOUTS]
    for cx, cy, d in CUTOUTS:          # the router keeps a track width further away
        router.add_zone("<keepout>", 0, octagon16(cx, cy, d / 2 + 1.0))
        router.add_zone("<keepout>", 1, octagon16(cx, cy, d / 2 + 1.0))

    def grow(poly, m):                 # miter offset of a simple polygon by m (either winding)
        n = len(poly)
        area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
        sgn = 1.0 if area > 0 else -1.0
        out = []
        for i in range(n):
            (x0, y0), (x1, y1), (x2, y2) = poly[i - 1], poly[i], poly[(i + 1) % n]
            def nrm(ax, ay, bx, by):
                dx, dy = bx - ax, by - ay
                ln = math.hypot(dx, dy) or 1.0
                return sgn * dy / ln, -sgn * dx / ln
            n1, n2 = nrm(x0, y0, x1, y1), nrm(x1, y1, x2, y2)
            bx, by = n1[0] + n2[0], n1[1] + n2[1]
            k = m / max(0.2, (1 + n1[0] * n2[0] + n1[1] * n2[1]))
            out.append((x1 + bx * k, y1 + by * k))
        return out
    for poly in KEEPOUTS:              # same margin for the layout's own keepouts
        router.add_zone("<keepout>", 0, grow(poly, 0.5))
        router.add_zone("<keepout>", 1, grow(poly, 0.5))
    for poly in list(KEEPOUTS) + cut_keepouts:   # no copper at all (antenna, board cutouts)
        z = pcbnew.ZONE(board)
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False)
        ls = pcbnew.LSET()
        for lay in (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
            ls.AddLayer(lay)
        z.SetLayerSet(ls)
        o = z.Outline()
        o.NewOutline()
        for x, y in poly:
            o.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + y))
        board.Add(z)
        router.add_zone("<keepout>", 0, poly)
        router.add_zone("<keepout>", 1, poly)
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
    for pour in POURS:
        if len(pour) == 3 or pour[3] == "F":
            pour_of.setdefault(pour[0], []).append(pour[2])
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
    gnd_poly = [pour[2] for pour in POURS if pour[0] == "GND" and (len(pour) == 3 or pour[3] == "F")]
    for p in netpads["GND"]:
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH or (p.GetParent().GetReference(), p.GetNumber()) in GND_VIA_SKIP:
            continue  # through-hole pads reach the planes; exposed pads have thermal vias
        pos = p.GetPosition()
        x, y = mm(pos.x) - OX, mm(pos.y) - OY
        if any(in_poly(x, y, poly) for poly in gnd_poly):
            continue
        vb = router.blocked("GND", CLEAR + VIA_D / 2 + RMARGIN)
        vok = ~(vb[0] | vb[1])
        src = router.cells_of_pad(p)
        src = [c for c in src if c[0] == 0]
        i0, j0 = int(round(x / GRID)), int(round(y / GRID))
        win = (i0 - 60, i0 + 61, j0 - 60, j0 + 61)
        path = router.astar("GND", 0.3, src, [], via_ok=False, window=win,
                            target_fn=lambda L, i, j: L == 0 and vok[j, i] and math.hypot(i - i0, j - j0) > 6
                            and router.via_far(i, j))
        if path is None:   # not fatal: the GND fill usually reaches it; the DRC checks connectivity
            print(f"  warning: no GND via next to {p.GetParent().GetReference()}.{p.GetNumber()}")
            continue
        router.commit(gnd, 0.3, path)
        L, i, j = path[-1]
        add_via(board, gnd, router.xs[i], router.ys[j])
        router.add_via("GND", router.xs[i], router.ys[j])

    # ---- 4. GND everywhere else: inner planes + top/bottom fill
    full = [(0.0, 0.0), (BW, 0.0), (BW, BH), (0.0, BH)]
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
    out = outdir / f"{PROJECT}.kicad_pcb"
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


def run(tools_dir, board_dir, attempts=6):
    """route in child processes (pcbnew dislikes a 2nd board per process), promoting failed nets."""
    import json
    import os
    import subprocess
    tools_dir, board_dir = Path(tools_dir).resolve(), Path(board_dir).resolve()
    promote = []
    code = ("import sys, json, os; sys.path[:0] = [%r, %r]; import design, layout; from kicadgen import pcb; "
            "pcb.configure(design, layout, %r); out, f = pcb.build(pcb.BOARD_DIR, json.loads(os.environ['P'])); "
            "print('RESULT ' + json.dumps(f))") % (str(tools_dir), str(Path(__file__).resolve().parents[1]),
                                                   str(board_dir))
    for attempt in range(attempts):
        r = subprocess.run([sys.executable, "-c", code], env=dict(os.environ, P=json.dumps(promote)),
                           capture_output=True, text=True)
        print(r.stdout.replace("RESULT", "  result"), r.stderr[-3000:], end="")
        res = [ln for ln in r.stdout.splitlines() if ln.startswith("RESULT ")]
        if not res:
            sys.exit(f"attempt {attempt + 1} crashed (rc={r.returncode})")
        failures = json.loads(res[-1][7:])
        if not failures:
            print(f"attempt {attempt + 1}: all nets routed")
            return True
        nets_failed = list(dict.fromkeys(f.split(":")[0] for f in failures if not f.startswith("GND via")))
        print(f"attempt {attempt + 1}: {len(failures)} failures -> promoting {nets_failed}")
        promote = list(dict.fromkeys(nets_failed + promote))
    return False
