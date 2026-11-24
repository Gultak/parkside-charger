"""Write <project>.kicad_pro with the design rules / net class the PCB was made for.
(KiCad keeps net classes and board constraints in the project file.)"""
import json
import sys
from pathlib import Path

def write_project(project, board_dir, root_uuid):
  pro = {
      "board": {
          "design_settings": {
              "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                           "copper_text_size_v": 1.5, "silk_line_width": 0.12, "silk_text_size_h": 0.8,
                           "silk_text_size_v": 0.8, "silk_text_thickness": 0.12},
              "rules": {"min_clearance": 0.127, "min_connection": 0.0, "min_copper_edge_clearance": 0.3,
                        "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2,
                        "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0,
                        "min_text_height": 0.8, "min_text_thickness": 0.08, "min_through_hole_diameter": 0.2,
                        "min_track_width": 0.15, "min_via_annular_width": 0.1, "min_via_diameter": 0.5,
                        "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True},
              "track_widths": [0.0, 0.2, 0.3, 0.4, 0.5, 0.75],
              "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
          },
      },
      "meta": {"filename": "slot_board.kicad_pro", "version": 1},
      "net_settings": {
          "classes": [{"name": "Default", "clearance": 0.13, "track_width": 0.2, "via_diameter": 0.6,
                       "via_drill": 0.3, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                       "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                       "line_style": 0, "wire_width": 6, "bus_width": 12,
                       "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
          "meta": {"version": 3},
      },
      "sheets": [["5a1c0b0a-7d1e-4c3a-9a47-2f6f3c0b0001", ""]],
  }
  pro["meta"]["filename"] = f"{project}.kicad_pro"
  pro["sheets"] = [[root_uuid, ""]]
  out = Path(board_dir) / f"{project}.kicad_pro"
  out.write_text(json.dumps(pro, indent=2) + "\n")
  return out
