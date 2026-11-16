"""Compare the netlist KiCad derives from a schematic with the design's PARTS."""
import re


def check(netfile, PARTS):
    nets = {}
    for ref, (_v, _s, _f, pins, _m) in PARTS.items():
        for pin, net in pins.items():
            nets.setdefault(net, []).append((ref, pin))
    txt = open(netfile).read()
    got = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', txt, re.S):
        name = m.group(1).lstrip("/")
        nodes = re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2))
        if (name.startswith("unconnected-") or name.startswith("Net-(")) and len(nodes) <= 1:
            continue
        got[name] = sorted(nodes)
    want = {n: sorted(c) for n, c in nets.items()}
    comps = set(re.findall(r'\(comp \(ref "([^"]+)"\)', txt))
    problems = []
    if comps != set(PARTS):
        problems.append(f"component mismatch: {comps ^ set(PARTS)}")
    for n in sorted(set(got) | set(want)):
        if got.get(n) != want.get(n):
            problems.append(f"NET {n}: schematic {got.get(n)} / design {want.get(n)}")
    fps = dict(re.findall(r'\(comp \(ref "([^"]+)"\).*?\(footprint "([^"]+)"\)', txt, re.S))
    for r, p in PARTS.items():
        if fps.get(r) != p[2]:
            problems.append(f"footprint mismatch {r}: {fps.get(r)} / {p[2]}")
    return problems, len(comps), len(want)
