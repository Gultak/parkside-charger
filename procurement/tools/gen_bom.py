"""Writes BOM.md and procurement/digikey_*.csv from bom_data.py.
Run from anywhere: python3 procurement/tools/gen_bom.py
bom_data.py mirrors the procurement Google Sheets (see HANDOFF.md): edit it, then rerun."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "agent-tools"))   # git submodule Gultak/agent-tools
from bom_data import CTL, SLOTS
from bom.bomgen import OrderList, eur, md_table
R = str(Path(__file__).resolve().parents[2]) + "/"
ISSUE = {
 "inductor": "⚠️ footprint: the board has the Coilcraft XAL6060 land pattern; the IHLP-2525 has different pads",
 "crimp": "⚠️ check the crimp contact against the wire (SXH-001T-P0.6N: 26-22 AWG, insulation 1.3-1.9 mm)",
 "minor": "electrolytic instead of hybrid polymer: fine (input bulk / damping)",
 "x5r": "X5R 35 V instead of X7R 10 V: fine (less DC-bias loss, rated to 85 °C)",
 "led": "check the lead order against the Kingbright when wiring; brightness may differ",
 "psu": "firmware budget still set for the LOP-400: change to 7 A / 10 A",
}
BLOCK = {"inductor", "crimp"}
def status(t, issue):
    if t == "pcb": return "🏭 PCB fab"
    if not t: return "✅ at hand"
    return "⚠️ resolve" if issue in BLOCK else "🛒 DigiKey"
def table(rows):
    return md_table(["Qty", "Part", "Manufacturer", "Part number", "Status", "DigiKey #", "€ (DigiKey, incl. VAT)", "Used for / note"],
                    [[q, part, man, mpn, status(t, issue), dk, eur(e), "; ".join(x for x in (refs, ISSUE.get(issue, "")) if x)]
                     for q, part, man, mpn, t, dk, e, refs, issue in rows], align="r-----r-")
def tot(rows): return sum(r[6] for r in rows if r[4] is True and r[6])
md = f"""# Bill of materials

Taken from the procurement sheets (Google Drive: "Parkside Charger – Controller Parts" and
"Parkside Charger – 10 Slot Parts"), with the cheapest DigiKey alternative chosen per part. The
manufacturer and part number columns are the parts actually ordered.

| Status | Meaning |
|---|---|
| 🛒 DigiKey | Order from DigiKey Ireland. Upload [`procurement/digikey_all.csv`](procurement/digikey_all.csv) (everything, quantities merged), or [`procurement/digikey_controller.csv`](procurement/digikey_controller.csv) and [`procurement/digikey_10_slots.csv`](procurement/digikey_10_slots.csv) separately |
| ✅ at hand | Already there: don't order |
| 🏭 PCB fab | Gerbers in `electronics/*/fab` (JLCPCB / PCBWay) |
| ⚠️ resolve | The chosen part does not match the design yet: see the note |

Prices are DigiKey line totals including VAT, from the sheets. DigiKey ships free to Ireland from
€92.25 (€75 ex VAT).

## Controller, power supply and box (once)

{table(CTL)}

DigiKey total: **€{tot(CTL):.2f}**

## 10 charger slots

{table(SLOTS)}

DigiKey total: **€{tot(SLOTS):.2f}** for 10 slots (€{tot(SLOTS)/10:.2f} per slot)
"""
open(R + 'BOM.md', 'w').write(md)
ALL = OrderList()
for name, rows in (("digikey_controller.csv", CTL), ("digikey_10_slots.csv", SLOTS)):
    one = OrderList()
    for q, part, man, mpn, t, dk, e, refs, issue in rows:
        if t is not True: continue
        dks = [d.strip() for d in dk.split("+")]
        qtys = [q] if len(dks) == 1 else [1, 2]       # PHR-2 housing + 2 SPH contacts
        for d, qq in zip(dks, qtys):
            ref = (refs + (" - CHECK BEFORE ORDERING: " + ISSUE[issue].replace("⚠️ ", "").replace("**", "") if issue in BLOCK else "")).strip(" -")
            one.add(qq, d, man, mpn, ref, merge=False)
            ALL.add(qq, d, man, mpn, ("CTL " if rows is CTL else "SLOTS ") + ref)
    one.write(R + 'procurement/' + name)
ALL.write(R + 'procurement/digikey_all.csv')
print(f"controller €{tot(CTL):.2f}, slots €{tot(SLOTS):.2f}")
