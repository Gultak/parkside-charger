"""Fabrication outputs + PCB-vs-design consistency check."""
import csv
import subprocess
import sys
import zipfile
from pathlib import Path

import pcbnew



def run_fab(PARTS, project, board_dir, exclude=None):
  root = Path(board_dir).resolve()
  pcb = root / f"{project}.kicad_pcb"
  fab = root / "fab"
  fab.mkdir(exist_ok=True)

  # --- PCB pads vs design.py
  board = pcbnew.LoadBoard(str(pcb))
  bad = []
  for fp in board.GetFootprints():
      ref = fp.GetReference()
      pins = PARTS[ref][3]
      for p in fp.Pads():
          n = p.GetNumber()
          if n in pins and p.GetNetname().lstrip("/") != pins[n]:
              bad.append(f"{ref}.{n}: pcb {p.GetNetname()} vs design {pins[n]}")
  missing = set(PARTS) - {fp.GetReference() for fp in board.GetFootprints()}
  print("PCB vs design:", "OK" if not bad and not missing else f"MISMATCH {bad} {missing}")

  # --- gerbers, drill, positions
  layers = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
  gdir = fab / "gerbers"
  gdir.mkdir(exist_ok=True)
  for f in gdir.iterdir():
      f.unlink()
  run = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)
  run("kicad-cli", "pcb", "export", "gerbers", "--layers", layers, "--subtract-soldermask",
      "--no-x2", "-o", str(gdir) + "/", str(pcb))
  run("kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--excellon-separate-th",
      "--generate-map", "--map-format", "gerberx2", "-o", str(gdir) + "/", str(pcb))
  run("kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm", "--side", "front",
      "-o", str(fab / f"{project}_cpl.csv"), str(pcb))
  with zipfile.ZipFile(fab / f"{project}_gerbers.zip", "w", zipfile.ZIP_DEFLATED) as z:
      for f in sorted(gdir.iterdir()):
          z.write(f, f.name)
  print("gerbers:", len(list(gdir.iterdir())), "files ->", fab / f"{project}_gerbers.zip")

  write_bom(PARTS, project, fab, exclude or {})

  # --- schematic PDF
  run("kicad-cli", "sch", "export", "pdf", "-o", str(root / f"{project}_schematic.pdf"), str(root / f"{project}.kicad_sch"))


def write_bom(PARTS, project, fab, exclude):
  """Two grouped BOMs: <project>_bom.csv is the order list for DigiKey's BOM Manager (parts
  in `exclude` - at hand, or bought elsewhere - left out); <project>_bom_all.csv lists every
  part with a Source column."""
  def key(r):
      return (r.rstrip("0123456789"), int(r[len(r.rstrip("0123456789")):]))
  def groups(refs):
      g = {}
      for ref in refs:
          value, _s, fp, _p, mpn = PARTS[ref]
          g.setdefault((value, fp.split(":")[1], mpn, exclude.get(ref, "DigiKey (this CSV)")), []).append(ref)
      return sorted(g.items(), key=lambda kv: key(min(kv[1], key=key)))
  order = [r for r in PARTS if r not in exclude]
  with open(fab / f"{project}_bom.csv", "w", newline="") as f:
      w = csv.writer(f)
      w.writerow(["Qty", "References", "Value", "Footprint", "MPN / notes"])
      for (value, fp, mpn, _src), refs in groups(order):
          refs.sort(key=key)
          w.writerow([len(refs), " ".join(refs), value, fp, mpn])
  with open(fab / f"{project}_bom_all.csv", "w", newline="") as f:
      w = csv.writer(f)
      w.writerow(["Qty", "References", "Value", "Footprint", "MPN / notes", "Source"])
      for (value, fp, mpn, src), refs in groups(PARTS):
          refs.sort(key=key)
          w.writerow([len(refs), " ".join(refs), value, fp, mpn, src])
  print("BOM:", len(groups(order)), "lines to order,", len(PARTS) - len(order), "parts excluded")
