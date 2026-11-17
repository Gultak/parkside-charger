"""Build a whole board: schematic -> netlist check -> project -> PCB (routing,
fill, DRC) -> fab outputs -> renders.  Usage (from a board's tools/ dir):
    /usr/bin/python3 build.py            # everything
    /usr/bin/python3 build.py sch        # schematic + netlist check only
Needs KiCad 7 (kicad-cli + the pcbnew python module)."""
import importlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main(tools_dir, steps=("sch", "pcb", "fab", "img")):
    tools_dir = Path(tools_dir).resolve()
    board_dir = tools_dir.parent
    sys.path[:0] = [str(tools_dir), str(HERE.parent)]
    design = importlib.import_module("design")
    layout = importlib.import_module("layout")
    from kicadgen import check_netlist, fab, footprints, pcb, project, render, schematic

    footprints.write_library(board_dir)
    if "sch" in steps:
        sch = schematic.build(design, layout, board_dir, layout.PROJECT, layout.ROOT_UUID)
        project.write_project(layout.PROJECT, board_dir, layout.ROOT_UUID)
        with tempfile.NamedTemporaryFile(suffix=".net") as t:
            subprocess.run(["kicad-cli", "sch", "export", "netlist", "-o", t.name, str(sch)],
                           check=True, capture_output=True)
            problems, ncomp, nnets = check_netlist.check(t.name, design.PARTS)
        if problems:
            sys.exit("SCHEMATIC NETLIST MISMATCH:\n  " + "\n  ".join(problems))
        print(f"schematic OK: {ncomp} parts, {nnets} nets match design.py")
    if "pcb" in steps:
        if not pcb.run(tools_dir, board_dir):
            sys.exit("routing failed")
        project.write_project(layout.PROJECT, board_dir, layout.ROOT_UUID)  # pcbnew rewrites it on save
    if "fab" in steps:
        fab.run_fab(design.PARTS, layout.PROJECT, board_dir, getattr(design, "NOT_IN_ORDER_BOM", {}))
    if "img" in steps:
        render.render(str(board_dir / f"{layout.PROJECT}.kicad_pcb"), str(board_dir / "img"))
        render.render_extra(layout.PROJECT, board_dir)
    for f in board_dir.glob("*.kicad_prl"):
        f.unlink()


if __name__ == "__main__":
    main(sys.argv[1], tuple(sys.argv[2:]) or ("sch", "pcb", "fab", "img"))
