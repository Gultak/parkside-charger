# Mechanical design

![3 modules + controller box, seen from below/front](img/assembly_below.png)
![Rear view with dummy batteries, bay lids and controller box](img/assembly_rear.png)
![One slot module from the battery side: rails with lips, latch recess, contact slots, switch window, LED bezel](img/slot_from_front_below.png)

## Concept

- **One printed module per battery** (95 × 177 mm footprint, 34 mm tall). Modules sit side by
  side at a 96 mm pitch, so 10 slots need **96 cm** of shelf. If the shelf is narrower, mount two
  rows of 5 on two shelves, or put the 10th slot on the side wall. Every module stands alone.
- The battery **slides in from the front and hangs from two rails**, as it does on a tool. Its
  own latch clicks into the recess in the channel ceiling. Press the release button to pull it out.
- At the end of the rails, the **end stop holds the contact tabs** and the **presence
  microswitch**. Behind it, an **electronics bay** holds the slot PCB in card guides, closed by a
  rear lid with cable entries.
- A **5 mm RGB LED** sits in the front bezel. Its wires run in a groove on the shelf side of the
  plate, back to the bay.
- A separate **controller box** holds the ESP32-C6 main board. The Mean Well PSU mounts with its
  own screw holes, at least 5 cm away from the batteries.

## Step 1: measure your battery and calibrate the model

The rail geometry in `parkside_shelf_charger.scad` is a **placeholder**. Parkside has not published
it, and packs differ slightly between generations. With calipers, measure:

| Parameter | What to measure on the pack |
|---|---|
| `chan_w` | Width of the raised "tongue" on top of the pack, above the side grooves, **+ 0.6 mm** |
| `lip_in` | Depth of the side grooves (how far the tool's rail goes in), **− 0.3 mm** |
| `lip_t` | Height of the side grooves, **− 0.4 mm** |
| `lip_gap` | Top of the tongue down to the top edge of the groove, **+ 0.3 mm** |
| `rail_len` | Front of the tongue (latch end) to the terminal face |
| `latch_y`, `latch_w`, `latch_l`, `latch_d` | Position and size of the spring latch tooth when it is extended, + 1 mm clearance |
| `contact_x`, `contact_z` | Centre of each terminal slot: X from the pack's centre line, Z down from the top of the tongue |
| `tab_vertical` | Orientation of the terminal slots |

Then:

1. Print `stl/gauge.stl`. It is 20 mm long, takes about 15 min, and includes the lead-in and the
   latch recess. Slide it onto the pack. It should run smoothly without wobbling up and down, and
   the latch should click. Adjust, re-render, and repeat.
2. Print **one** full slot module and test it with the contacts in place before printing ten.

Export the parts:

```bash
openscad -D 'part="slot"' -o slot.stl parkside_shelf_charger.scad
```

The other parts work the same way: `slot_lid`, `gauge`, `controller`, `controller_lid`. Use
`part="assembly"` for a preview.

## Printing

| Part | Qty | Orientation | Notes |
|---|---|---|---|
| `slot.stl` | 10 | **Front face on the bed** (as exported) | Every layer then contains the full rail profile, so the lips that carry the battery are as strong as possible and need no support. Use a brim, 4 walls, 30–40 % gyroid, 0.2 mm layers |
| `slot_lid.stl` | 10 | flat | |
| `controller.stl` | 1 | open side up | |
| `controller_lid.stl` | 1 | flat | |

**Material: PETG or ASA** (PC-FR if you can). Do **not** use PLA: it creeps under the constant
1 kg load and softens near 55 °C.

## Hardware per slot module

| Qty | Part |
|---|---|
| 4 | Wood screws 4 × 12 mm, pan head. On an 18 mm shelf never go above 14 mm |
| 4 | M3 heat-set inserts (4.2 mm hole) for the rear lid + 4 × M3×8 screws |
| 3–4 | Contact tabs: **male 6.3 × 0.8 mm Faston tabs** (solder or crimp type), or strips cut from 0.8 mm brass, tinned. Push them in from the bay side, bend the tail 90° behind the end stop and glue with a drop of epoxy. **Check the blade thickness against your pack's terminals first.** |
| 1 | Microswitch Omron D2F-01L (or SS-5GL with lever) + 2 × M2 × 8 self-tapping screws |
| 1 | 5 mm RGB LED, common anode, 4-wire cable to the slot PCB |
| 1 | Slot PCB 72 × 60 mm (slides into the card guides from the rear) |

## Mounting

1. Shelf thickness: at least 16 mm of solid wood or chipboard. Ten 8 Ah packs weigh about 11 kg.
   Use 4 screws per module.
2. For fire protection on wooden shelves, first screw a 0.5–1 mm steel or aluminium sheet to the
   underside of the shelf, then mount the modules through it.
3. Align the modules at their front edges. The 1 mm gap between neighbours is intended.
4. Run the 24 V bus (2 × 2.5 mm²) behind the bays with one Wago 221 tap per slot. Run the 4-wire
   I²C cables to the controller box in a cable channel along the rear.
