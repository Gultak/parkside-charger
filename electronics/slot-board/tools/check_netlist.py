"""Compare the netlist KiCad derives from the schematic with design.py.
Usage: kicad-cli sch export netlist -o x.net ../slot_board.kicad_sch && python3 check_netlist.py x.net"""
import re
import sys

from design import PARTS, nets

txt = open(sys.argv[1]).read()
got = {}
for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', txt, re.S):
    name = m.group(1).lstrip("/")
    nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2))
    if name.startswith("unconnected-") or name.startswith("Net-("):
        if len(nodes) <= 1:
            continue
    got[name] = sorted(nodes)
want = {n: sorted(c) for n, c in nets().items()}
comps = set(re.findall(r'\(comp \(ref "([^"]+)"\)', txt))
ok = True
if comps != set(PARTS):
    ok = False
    print("component mismatch:", comps ^ set(PARTS))
for n in sorted(set(got) | set(want)):
    if got.get(n) != want.get(n):
        ok = False
        print(f"NET {n}:\n  schematic {got.get(n)}\n  design    {want.get(n)}")
fps = dict(re.findall(r'\(comp \(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', txt, re.S))
for r, p in PARTS.items():
    if fps.get(r) != p[2]:
        ok = False
        print("footprint mismatch", r, fps.get(r), p[2])
print("NETLIST OK: %d parts, %d nets match design.py" % (len(comps), len(want)) if ok else "NETLIST MISMATCH")
sys.exit(0 if ok else 1)
