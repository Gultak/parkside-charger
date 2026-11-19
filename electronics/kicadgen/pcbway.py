"""PCBWay assembly files: BOM and centroid (pick & place) in PCBWay's column layout.

    fab/pcbway/<project>_pcbway_bom.xlsx / .csv
    fab/pcbway/<project>_pcbway_cpl.xlsx / .csv

Parts in the design's NOT_IN_ORDER_BOM that are "at hand" (or mounting holes) are listed
as DNP: the customer fits them. Everything else, SMD and through-hole, is for PCBWay to
source and place. Centroids are the centre of each part's pads, in mm from the board's
lower-left corner (Y up), top side, rotation as in KiCad.
Usage: python3 -m kicadgen.pcbway <board tools dir>   (also run by build.py)
"""
import csv
import importlib
import sys
from pathlib import Path

# (value, footprint name) -> (manufacturer, part number, description); value None = any value
MPN = {
    ("47u 35V", "CP_Elec_6.3x7.7"): ("Nichicon", "UUD1V470MCL1GS", "Capacitor aluminium electrolytic 47 uF 35 V, 6.3 x 7.7 mm"),
    ("100n 50V", "C_0603_1608Metric"): ("Murata", "GRT188R71H104KE13D", "Capacitor 100 nF 50 V X7R 0603"),
    ("100n", "C_0603_1608Metric"): ("Murata", "GRT188R71H104KE13D", "Capacitor 100 nF 50 V X7R 0603"),
    ("10u 50V", "C_1206_3216Metric"): ("Samsung", "CL31B106KBHNNNE", "Capacitor 10 uF 50 V X7R 1206"),
    ("1u 50V", "C_1206_3216Metric"): ("NIC Components", "NMC1206X7R105K50TRPLPF", "Capacitor 1 uF 50 V X7R 1206"),
    ("22u 10V", "C_1206_3216Metric"): ("Samsung", "CL31B226KPHNNNE", "Capacitor 22 uF 10 V X7R 1206"),
    ("22n", "C_0603_1608Metric"): ("Samsung", "CL10B223KB8NNNC", "Capacitor 22 nF 50 V X7R 0603"),
    ("4u7 10V", "C_0603_1608Metric"): ("Murata", "GRM188R6YA475KE15D", "Capacitor 4.7 uF 35 V X5R 0603"),
    ("1u 10V", "C_0603_1608Metric"): ("Samsung", "CL10B105KP8NNNC", "Capacitor 1 uF 10 V X7R 0603"),
    ("SMBJ26A", "D_SMB"): ("Vishay", "SMB10J26A-E3/52", "TVS diode 26 V unidirectional, SMB"),
    ("BZT52C12", "D_SOD-123"): ("onsemi", "MMSZ5242BT1G", "Zener 12 V SOD-123"),
    ("1N4148W", "D_SOD-123"): ("onsemi", "MMSD4148T1G", "Diode 1N4148W SOD-123"),
    ("5A fast", "Fuse_1206_3216Metric"): ("Bel Fuse", "C1Q 5", "Fuse 5 A fast 1206"),
    ("0.5A PTC", "Fuse_1206_3216Metric"): ("Littelfuse", "NANOSMDC050F/13.2-2", "PTC fuse 0.5 A 1206"),
    ("10A mini blade", "Fuseholder_Blade_Mini_Keystone_3568"): ("Keystone", "3568", "Mini blade fuse holder, PCB (fuse not included)"),
    (None, "AMASS_XT30PW-M_1x02_P2.50mm_Horizontal"): ("Amass", "XT30PW-M", "XT30 PCB connector, right angle, male"),
    (None, "AMASS_XT30PW-F_1x02_P2.50mm_Horizontal"): ("Amass", "XT30PW-F", "XT30 PCB connector, right angle, female"),
    (None, "AMASS_XT30UPB-F_1x02_P5.0mm_Vertical"): ("Amass", "XT30UPB-F", "XT30 PCB connector, vertical, female"),
    (None, "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"): ("JST", "B4B-XH-A(LF)(SN)", "JST-XH header 4-pin vertical"),
    (None, "JST_SH_SM04B-SRSS-TB_1x04-1MP_P1.00mm_Horizontal"): ("JST", "SM04B-SRSS-TB(LF)(SN)", "JST-SH header 4-pin (Qwiic)"),
    (None, "FanPinHeader_1x04_P2.54mm_Vertical"): ("Molex", "0470531000", "4-pin PC fan header"),
    (None, "TerminalBlock_Phoenix_MKDS-1,5-3_1x03_P5.00mm_Horizontal"): ("Phoenix Contact", "1715035", "Screw terminal 3-pole 5.0 mm (MKDS 1,5/3)"),
    (None, "JST_VH_B6P-VH_1x06_P3.96mm_Vertical"): ("JST", "B6P-VH", "JST-VH header 6-pin vertical"),
    (None, "PinHeader_1x01_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x1 2.54 mm"),
    (None, "PinHeader_1x02_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x2 2.54 mm"),
    (None, "PinHeader_1x04_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x4 2.54 mm"),
    (None, "PinHeader_1x07_P2.54mm_Vertical"): ("generic", "-", "Pin header 1x7 2.54 mm"),
    (None, "ESP32_C6_D1_Socket"): ("Sullins", "2x PPTC081LFBN-RC", "Socket for the ESP32-C6 D1: 2x female header 1x8 2.54 mm"),
    ("6.8u", "L_Coilcraft_XAL6060-XXX"): ("Coilcraft", "XAL6060-682MEC", "Power inductor 6.8 uH shielded (footprint is XAL6060)"),
    ("FDMC8327L", None): ("onsemi", "FDMC8327L", "N-MOSFET 40 V Power33"),
    ("2N7002K", "SOT-23"): ("Diotec", "2N7002", "N-MOSFET 60 V SOT-23"),
    ("AOD4185", "TO-252-2"): ("Alpha & Omega", "AOD4185", "P-MOSFET -40 V TO-252"),
    ("10m 1%", "R_2512_6332Metric"): ("Vishay", "WSL2512R0100FEA", "Current-sense resistor 10 mOhm 1% 1 W 2512"),
    ("10k 0.1%", "R_0603_1608Metric"): ("Bourns", "CRT0603-BY-1002ELF", "Resistor 10 k 0.1% 25 ppm 0603"),
    ("63k4 1%", "R_0603_1608Metric"): ("Vishay", "CRCW060363K4FKEA", "Resistor 63.4 k 1% 0603"),
    ("10k", "R_0603_1608Metric"): ("Panasonic", "ERJ-3EKF1002V", "Resistor 10 k 1% 0603"),
    ("100k", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07100KL", "Resistor 100 k 1% 0603"),
    ("47k", "R_0603_1608Metric"): ("Yageo", "RC0603FR-0747KL", "Resistor 47 k 1% 0603"),
    ("4k7", "R_0603_1608Metric"): ("Vishay", "CRCW06034K70FKEA", "Resistor 4.7 k 1% 0603"),
    ("100", "R_0603_1608Metric"): ("KOA Speer", "RK73H1JTTD1000F", "Resistor 100 Ohm 1% 0603"),
    ("270", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07270RL", "Resistor 270 Ohm 1% 0603"),
    ("330", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07330RL", "Resistor 330 Ohm 1% 0603"),
    ("560", "R_0603_1608Metric"): ("Yageo", "RC0603FR-07560RL", "Resistor 560 Ohm 1% 0603"),
    ("100 2W", None): ("Vishay", "PR02000201000JR500", "Resistor 100 Ohm 2 W metal film, axial; mount 2-3 mm above the board"),
    ("10k NTC B3380", None): ("Murata", "NCP18XH103F03RB", "NTC thermistor 10 k B3380 1% 0603"),
    ("4k7 x4", None): ("Panasonic", "EXB-38V472JV", "Resistor array 4 x 4.7 k 0603"),
    ("5V active", None): ("Same Sky", "CMI-1275-05TH", "Buzzer 12 mm 5 V active (7.6 mm pin pitch)"),
    ("TSR 1-2450", None): ("TRACO Power", "TSR 1-2450E", "5 V 1 A switching regulator, SIP-3"),
    ("LTC4162EUFD-LAD", None): ("Analog Devices", "LTC4162EUFD-LAD#PBF", "Li-ion charger, I2C, QFN-28 4x5 (must be the -LAD)"),
    ("PCA9554PW", None): ("Texas Instruments", "TCA9554PWR", "8-bit I2C I/O expander TSSOP-16"),
    ("PESD5V0S2UT", None): ("Nexperia", "PESD5V2S2UT,215", "ESD protection 5 V SOT-23"),
    ("TLV7031DBV", None): ("Texas Instruments", "TLV7031DBVR", "Comparator push-pull SOT-23-5"),
    ("TCA9548APWR", None): ("NXP", "PCA9548APW,118", "8-channel I2C mux TSSOP-24"),
}


def lookup(value, fp):
    for key in ((value, fp), (None, fp), (value, None)):
        if key in MPN:
            return MPN[key]
    raise KeyError(f"no part number for {value!r} / {fp!r}: add it to kicadgen/pcbway.py")


def write(rows, path):
    with open(path.with_suffix(".csv"), "w", newline="") as f:
        csv.writer(f).writerows(rows)
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        return
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDDDDD")
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(60, max(10, max(len(str(c.value or "")) for c in col) + 2))
    ws.freeze_panes = "A2"
    wb.save(path.with_suffix(".xlsx"))


def run(design, layout, board_dir):
    import pcbnew
    board_dir = Path(board_dir)
    out = board_dir / "fab" / "pcbway"
    out.mkdir(parents=True, exist_ok=True)
    project = layout.PROJECT
    exclude = getattr(design, "NOT_IN_ORDER_BOM", {})
    dnp = {r: why for r, why in exclude.items() if why.startswith("at hand") or why == "mounting hole"}

    def key(r):
        p = r.rstrip("0123456789")
        return (p, int(r[len(p):]))

    # ---- BOM, grouped by part number
    groups = {}
    for ref, (value, _sym, fp, _pins, _note) in design.PARTS.items():
        if ref.startswith("H") and dnp.get(ref) == "mounting hole":
            continue
        fpn = fp.split(":")[1]
        man, mpn, desc = lookup(value, fpn)
        smd = "SMD" if not any(t in fpn for t in ("THT", "PinHeader", "Terminal", "XT30", "JST_XH", "JST_VH", "Fan",
                                                       "Buzzer", "Fuseholder", "Socket", "Axial", "Converter")) else "THT"
        g = groups.setdefault((man, mpn, fpn, ref in dnp), {"refs": [], "desc": desc, "type": smd, "values": []})
        g["refs"].append(ref)
        if value not in g["values"]:
            g["values"].append(value)
    rows = [["Item #", "Designator", "Qty", "Manufacturer", "Mfg Part #", "Description / Value", "Package/Footprint",
             "Type", "Your Instructions / Notes"]]
    items = sorted(groups.items(), key=lambda kv: (kv[0][3], kv[1]["type"], key(min(kv[1]["refs"], key=key))))
    for i, ((man, mpn, fpn, is_dnp), g) in enumerate(items, 1):
        value = " / ".join(g["values"])
        refs = sorted(g["refs"], key=key)
        note = "DO NOT PLACE (customer fits it)" if is_dnp else ""
        if mpn == "3568":
            note = "Holder only; no fuse"
        if mpn == "PR02000201000JR500":
            note = "Mount 2-3 mm above the board (heat)"
        if mpn == "LTC4162EUFD-LAD#PBF":
            note = "Must be the -LAD version; no substitute"
        rows.append([i, ",".join(refs), len(refs), man, mpn, f"{g['desc']} ({value})", fpn, g["type"], note])
    write(rows, out / f"{project}_pcbway_bom")

    # ---- centroid: centre of the pads, mm from the lower-left board corner
    board = pcbnew.LoadBoard(str(board_dir / f"{project}.kicad_pcb"))
    bb = board.GetBoardEdgesBoundingBox()
    x0, y1 = pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetBottom())
    cpl = [["Designator", "Mid X (mm)", "Mid Y (mm)", "Layer", "Rotation", "Footprint"]]
    for fp in sorted(board.GetFootprints(), key=lambda f: key(f.GetReference())):
        ref = fp.GetReference()
        if ref in dnp or ref not in design.PARTS:
            continue
        pads = list(fp.Pads())
        if not pads:
            continue
        xs = [pcbnew.ToMM(p.GetPosition().x) for p in pads]
        ys = [pcbnew.ToMM(p.GetPosition().y) for p in pads]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        layer = "Top" if fp.GetLayer() == pcbnew.F_Cu else "Bottom"
        cpl.append([ref, round(cx - x0, 3), round(y1 - cy, 3), layer, round(fp.GetOrientationDegrees() % 360, 1),
                    str(fp.GetFPID().GetLibItemName())])
    write(cpl, out / f"{project}_pcbway_cpl")
    print(f"PCBWay: {len(rows) - 1} BOM lines, {len(cpl) - 1} placements -> {out}")


if __name__ == "__main__":
    tools = Path(sys.argv[1]).resolve()
    sys.path[:0] = [str(tools), str(Path(__file__).resolve().parent.parent)]
    run(importlib.import_module("design"), importlib.import_module("layout"), tools.parent)
