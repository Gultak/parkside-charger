"""Regenerate the slot board (schematic, PCB, fab files, renders): /usr/bin/python3 build.py [sch|pcb|fab|img]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kicadgen.build import main  # noqa: E402

main(Path(__file__).resolve().parent, tuple(sys.argv[1:]) or ("sch", "pcb", "fab", "img"))
