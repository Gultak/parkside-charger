// =====================================================================
//  Parkside X20V under-shelf charging rack: slot module + controller box
//  OpenSCAD 2021.01+   units: mm
//
//  One SLOT MODULE per battery (print 10). Modules are screwed side by
//  side to the underside of the shelf; the battery slides in from the
//  front and hangs from two rails, like on a tool.
//
//  Battery interface: measured on a real pack (see docs/mechanical.md);
//  contact_z is still an estimate.
//  Print part="gauge" and part="end_gauge" (short slices, ~15 min each)
//  and test-fit them on your pack before
//  printing the full modules. See docs/mechanical.md.
//
//  Export:
//    openscad -D 'part="slot"'           -o slot.stl            parkside_shelf_charger.scad
//    openscad -D 'part="slot_lid"'       -o slot_lid.stl        parkside_shelf_charger.scad
//    openscad -D 'part="gauge"'          -o gauge.stl           parkside_shelf_charger.scad
//    openscad -D 'part="end_gauge"'      -o end_gauge.stl       parkside_shelf_charger.scad
//    openscad -D 'part="joint_gauge"'    -o joint_gauge.stl     parkside_shelf_charger.scad
//  End modules: add -D joint_left=false (leftmost) or -D joint_right=false (rightmost).
//    openscad -D 'part="controller"'     -o controller.stl      parkside_shelf_charger.scad
//    openscad -D 'part="controller_lid"' -o controller_lid.stl  parkside_shelf_charger.scad
//  part="assembly" shows everything in mounted orientation (not for printing).
//
//  Coordinates (mounted orientation): X = across the shelf, Y = slide
//  direction (0 = front edge, where you insert the battery), Z = up.
//  Z = 0 is the channel ceiling (battery side of the mounting plate); the
//  plate occupies 0..plate_t and its top face touches the shelf.
// =====================================================================

part = "assembly"; // [slot, slot_lid, gauge, end_gauge, joint_gauge, controller, controller_lid, assembly, single, joint_section, joint_check]

/* [Battery interface: MEASURE YOUR PACK] */
chan_w   = 46.9;  // clear width between the rail walls, above the lips (tongue width 46.3 + 0.6)
lip_in   = 4.2;   // how far each lip sticks inward (groove depth 4.5 - 0.3)
lip_t    = 5.0;   // lip thickness (groove height 5.4 - 0.4)
lip_gap  = 5.1;   // plate face -> top face of lip (tongue top -> groove 4.8 + 0.3)
rail_len = 64;    // measured: tongue end (release button) -> contact face
// The tongue does not end square: two side prongs (left/right of the contact
// pocket) reach past the contact face, and the wide part above the grooves
// tapers off towards their tips. Taken from a reference holder model.
prong_l  = 14;    // prong tips -> this far beyond the contact face
prong_cl = 0.5;   // extra room in front of the prong tips
cblock_w = 29.6;  // contact block width (fills the pocket between the prongs, 30 on the reference)
cblock_ch = 4;    // 45 deg chamfer on the contact block's front corners
wing_l   = 7;     // the wide part tapers to the groove width over the last 7 mm
// Battery top surface: beside the tongue there is a trough (at least as wide as
// the reference holder, +-34.9 mm) down to below the grooves; further out the
// pack's top surface is only 4-5 mm below the tongue top (measured).
trough_x = 34.9;  // half-width of the free trough beside the tongue
body_top = 4;     // pack top surface outside the trough, below the tongue top (measured 4-5)
keep_z   = -(body_top - 0.5);   // nothing outside the trough may reach below this
// Front (latch) end, taken from the reference holder model; distances are measured
// FORWARD from the contact face. The grooves only start ~29 mm in front of the contact
// face; further forward the pack rises (45 deg up to the plate face, then higher), and
// only a narrow nose with the latch pocket reaches over the latch.
lip_l    = 28.6;  // lips (grooves) start
lead_in  = 4;     // 45 deg lead-in on the lip entry
slope_l  = 43;    // rail walls/edge bars slope away at 45 deg, reaching the plate face here
front_l  = 45.5;  // front edge of the frame (outside the nose)
nose_l   = 55;    // nose tip
nose_w   = 41;    // nose width at its root (tapers to ~25 at the tip)
latch_w  = 25;    // latch pocket width (reference holder)
// latch pocket profile in the nose: [distance forward of the contact face, depth]
latch_prof = [[nose_l + 0.2, 1.7], [52.9, 1.8], [50.5, 5], [49.5, 5], [front_l, 2]];

/* [Battery contacts (male 6.3 x 0.8 mm tabs or 0.8 mm brass)] */
// X positions of the contact tabs, measured from the channel centre line.
// Parkside X20V: B+, ID (BMS status, ~10k to B-), T (unused, ~512k), B-
contact_x   = [-12, -4, 4, 12];   // measured: 8 mm pitch; seen from the front: +, ID, T, - (T not used)
contact_z   = 5.5;  // tab centre below the plate face
contact_len = 8;    // how far the tab sticks out of the contact face (battery slots are 9.8 deep)
tab_w       = 6.3;
tab_t       = 0.8;
tab_vertical = true; // blade plane vertical (true) or horizontal (false)

/* [Module frame] */
pitch    = 88;    // module width = slot spacing (battery body 86 + 2, batteries are grabbed from below)
plate_t  = 10;    // mounting plate thickness (carries the dovetail and the LED; as on the reference holder)
wall_t   = 5;     // rail wall thickness
stop_t   = 8;     // end wall thickness (behind the prong tips)
bay_l    = 4 + 47.5 + 0.5;   // electronics bay: 4 mm gap, PCB, 0.5 mm to the lid
bay_h    = 34;    // electronics bay height below the plate (must clear the battery body)
bay_wall = 2.4;
screw_d  = 4.5;   // wood screws 4 x 25 (plate 10 + shelf, stay 2 mm short of the top)
screw_head_d = 9;
csk_d    = 8.6;   // countersink for the flat-head screws inside the channel
csk_recess = 0.4; // heads sit this far below the channel ceiling (battery slides over)

/* [Interlocking joint between neighbouring modules] */
// Sliding dovetail along the full length: tongue on the right (+X) edge,
// groove on the left (-X) edge. A new module slides on from the front;
// the groove is closed at the front so all front edges end up flush.
joint_left  = true;   // groove on the left edge  (false for the leftmost module)
joint_right = true;   // tongue on the right edge (false for the rightmost module)
jt_gap   = 0.4;       // gap between neighbouring plates
jt_d     = 5;         // dovetail depth
jt_root  = 5;         // dovetail height at the root (narrow end)
jt_tip   = 7;         // dovetail height at the tip (wide end)
jt_zc    = (keep_z + plate_t) / 2;   // dovetail centre height (0 = channel ceiling)
jt_clear = 0.2;       // clearance per side (raise to 0.25-0.3 if it binds)
jt_front = 3;         // closed front end of the groove (front-edge alignment stop)
jt_r     = 1.0;       // radius on the tongue's edges (groove follows with r + clearance)
// The tongue's front end and the groove's closed end are both bevelled at 45 deg
// (rising towards the back), so neither has a flat overhang when printed face-down.
bar_w    = 9;         // width of the edge bar carrying the joint
bar_bot  = keep_z;    // underside of the edge bar (must stay above the battery body)

/* [Slot PCB (slides into card guides from the rear)] */
pcb_w = 72;     // across (X); edges ride 0.8 mm deep in the card guides
pcb_l = 47.5;   // along (Y)
pcb_hole = [40.5, 25];   // screwdriver hole in the PCB (board coords: x from the left edge, y from the front edge)
pcb_t = 1.6;
pcb_z = 9;      // PCB bottom face below plate face

/* [Microswitch: Omron D2F-01L / similar, M2 holes 6.5 mm apart] */
sw_x    = -18;  // switch window centre from channel centre (between + contact and wall)
sw_z    = 3.5;
sw_win  = [9, 4];   // window through the end stop for the lever (X, Z)

/* [Status LED: 5 mm RGB (T-1 3/4) in the front face of the right edge bar, inserted FROM THE FRONT] */
// Standard 5 mm LED: 5.0 mm body, 5.8 mm flange, ~8.6 mm flange-to-dome-tip.
// Thread the wires out through the front, solder + heat-shrink them to the
// trimmed leads, pull them back and push the LED in until the flange seats.
led_cb_d   = 6.3;   // front counterbore for the LED body + flange
led_cb_l   = 8.6;   // its depth: the dome ends flush with the front face
led_lip_d  = 5.0;   // lip the flange stops against (wires + heat-shrink pass through)
led_lip_l  = 1;
led_bore_d = 7.0;   // bore behind the lip for the solder joints
bezel_l    = 18;    // LED bore length along Y
wire_ch    = 5;     // wire channel / groove width
wire_gd    = 3;     // depth of the wire groove on the shelf side of the plate

/* [Cable access, slot bay] */
// Rear part of the bay floor is open: 24 V IN/OUT screws and the I2C plug of the
// slot board (all facing down) are reachable from below with the bay closed.
floor_window_y = 36;   // window starts this far behind the PCB's front edge
lid_notch_top  = 12.0; // the lid's U-notch reaches up to this depth below the plate (PCB at 9..10.6)

/* [Controller box (controller board 110 x 100 mm)] */
ctl_pcb  = [110, 100];
ctl_gap  = 4;             // PCB to inner wall
ctl_in   = [ctl_pcb[0] + 2 * ctl_gap, ctl_pcb[1] + 2 * ctl_gap, 42];   // inner dims (X, Y, Z)
ctl_wall = 2.4;
ctl_standoff = 8;         // PCB above the base
ctl_holes = [[5, 78.5], [105, 78.5], [18, 3.8], [91.8, 3.8]];      // PCB mounting holes (board coords)

$fn = 48;
eps = 0.01;

// ---------------- derived ----------------
wall_h   = lip_gap + lip_t;          // rail wall height below the plate
inner_x  = chan_w / 2;               // inner face of a rail wall
outer_x  = inner_x + wall_t;         // outer face
mod_w    = pitch - jt_gap;           // neighbours interlock with a small gap
y_stop   = rail_len;                 // contact face (front of the contact block)
y_front  = rail_len - front_l;       // frame front edge
y_nose   = rail_len - nose_l;        // nose tip
y_lip    = rail_len - lip_l;         // lips start
y_slope  = rail_len - slope_l;       // nothing below the plate face in front of this
led_x    = mod_w / 2 - bar_w / 2;    // LED in the right edge bar, inside the plate
led_z    = plate_t / 2;
y_wall   = rail_len + prong_l + prong_cl;   // end wall front face (prong tips)
y_bay0   = y_wall + stop_t;          // start of bay
mod_l    = y_bay0 + bay_l;           // total length
bay_x    = pcb_w / 2 - 0.8;          // bay inner half-width
rear_tab = 0;                        // (no plate extension: the rear screw sits inside the bay)
total_l  = mod_l + rear_tab;
cage_l   = total_l - y_bay0;         // bay walls run to the rear edge (module prints standing on it)
sw_body  = [14, 9];                  // pocket for the microswitch body in the end-wall bevel (X, Z)
// One screw front, one rear, both on the centre line: the dovetail joint
// carries the sideways and twisting loads between neighbouring modules.
front_screw_y = y_lip + 2;           // flat-head screw in the channel ceiling
rear_screw_x  = pcb_hole[0] - pcb_w / 2;   // under the PCB's hole (PCB components face down: no mirroring)
rear_screw_y  = y_bay0 + 4 + pcb_hole[1];

module hole_y(d, l) {               // hole along Y: vertical when printed face-down, so plain round
    rotate([-90, 0, 0]) cylinder(d = d, h = l);
}
module hole_z(d, h) { translate([0, 0, -h]) cylinder(d = d, h = h + 2 * eps); }

// ------------------- interlocking dovetail (XZ profile, extruded along Y) --
// c = clearance; x = 0 is where the dovetail starts to widen.
// offset(r) offset(delta=-r) rounds the convex (tip) corners.
module dovetail_2d(c = 0, neck = 0) {
    offset(r = jt_r + c) offset(delta = -(jt_r + c)) polygon([
        [-neck - eps, jt_zc - jt_root / 2 - c], [0, jt_zc - jt_root / 2 - c],
        [jt_d + c, jt_zc - jt_tip / 2 - c], [jt_d + c, jt_zc + jt_tip / 2 + c],
        [0, jt_zc + jt_root / 2 + c], [-neck - eps, jt_zc + jt_root / 2 + c]
    ]);
}
// keeps the region behind a 45 deg plane: y >= y0 + (x - x0) * dir
module bevel_45(x0, y0, dir = 1) {
    translate([x0, y0, -60]) linear_extrude(120)
        polygon([[-100 * dir, -100], [100 * dir, 100], [100 * dir, 500], [-100 * dir, 500]]);
}
module joint_tongue() {     // on the right edge, reaches across the gap
    xm = mod_w / 2 + jt_gap;    // the neighbour's edge = groove mouth
    intersection() {
        translate([xm, total_l, 0]) rotate([90, 0, 0])
            linear_extrude(total_l) dovetail_2d(0, jt_gap + 0.5);
        bevel_45(xm, y_front + jt_front + jt_clear);
    }
}
module joint_groove() {     // cut into the left edge, open at the rear
    intersection() {
        translate([-mod_w / 2, total_l + 1, 0]) rotate([90, 0, 0])
            linear_extrude(total_l + 2) dovetail_2d(jt_clear, 1);
        bevel_45(-mod_w / 2, y_front + jt_front);
    }
}
module edge_bars() {
    for (sx = [-1, 1]) translate([sx > 0 ? mod_w / 2 - bar_w : -mod_w / 2, 0, bar_bot])
        cube([bar_w, total_l, plate_t - bar_bot]);
}

// ------------------- the rail profile (XZ), extruded along Y ----------
module rail_profile_2d() {
    // one side, mirrored. Origin = plate face (Z=0 is the plate underside here)
    for (m = [0, 1]) mirror([m, 0])
        polygon([
            [inner_x, 0], [outer_x, 0],
            [outer_x, -wall_h],
            [inner_x - lip_in, -wall_h],
            [inner_x - lip_in, -wall_h + lip_t],
            [inner_x, -wall_h + lip_t]
        ]);
}

module rails(len) {
    translate([0, len, 0]) rotate([90, 0, 0]) linear_extrude(len) rail_profile_2d();
}

// The lips start at y_lip with a 45 deg lead-in; in front of that the pack has no grooves.
module lip_front_cut() {
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([0, 0, -wall_h - eps]) linear_extrude(lip_t + 2 * eps) polygon([
            [inner_x - lip_in - eps, -1], [inner_x + eps, -1],
            [inner_x + eps, y_lip - lead_in], [inner_x - lip_in - eps, y_lip]]);
}
// Front envelope of the pack: below the plate face the walls/bars slope away at 45 deg
// towards the front; in front of y_front only the nose remains.
module front_cut() {
    translate([60, 0, 0]) rotate([0, -90, 0]) linear_extrude(120)     // (z, y) polygon
        polygon([[eps, -1], [eps, y_slope], [-60, y_slope + 60], [-60, -1]]);
    difference() {
        translate([-60, -1, -60]) cube([120, y_front + 1, 120]);
        nose_prism();
    }
}
function nose_pts() = let(h = nose_w / 2) [
    [-h, y_front + 1], [-h, y_front], [-16.6, y_nose + 1.4], [-12.5, y_nose + 0.5], [-5, y_nose],
    [5, y_nose], [12.5, y_nose + 0.5], [16.6, y_nose + 1.4], [h, y_front], [h, y_front + 1]];
module nose_prism() { translate([0, 0, -eps]) linear_extrude(plate_t + 2 * eps) polygon(nose_pts()); }

// Contact block: fills the battery's contact pocket between the two prongs and
// carries the contact tabs. Front corners chamfered 45 deg (prints without support
// face-down, and guides the pack in).
module contact_block() {
    h = cblock_w / 2;
    translate([0, 0, -wall_h]) linear_extrude(wall_h + eps) polygon([
        [-h + cblock_ch, y_stop], [h - cblock_ch, y_stop], [h, y_stop + cblock_ch],
        [h, y_wall + eps], [-h, y_wall + eps], [-h, y_stop + cblock_ch]]);
}
// The wide part of the tongue (above the grooves) narrows to the groove width
// over its last wing_l mm: fill the corners of the channel to match.
module wing_tapers() {
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([0, 0, -lip_gap - eps]) linear_extrude(lip_gap + 2 * eps) polygon([
            [inner_x + eps, y_wall - wing_l], [inner_x + eps, y_wall + eps],
            [inner_x - lip_in, y_wall + eps]]);
}

// ---------------------------- slot module -----------------------------
module slot_module() {
    col = 7;  // corner columns in the bay that take the lid inserts
    difference() {
        union() {
            // mounting plate (full module width, with a rear screw tab)
            translate([-mod_w / 2, 0, 0]) cube([mod_w, total_l, plate_t]);
            // edge bars carrying the interlocking joint
            edge_bars();
            if (joint_right) joint_tongue();
            // rails
            rails(y_wall + eps);
            // end wall across the channel (the prong tips stop against it)
            translate([-outer_x, y_wall, -wall_h]) cube([2 * outer_x, stop_t, wall_h + eps]);
            contact_block();
            wing_tapers();
            // electronics bay shell
            translate([-bay_x - bay_wall, y_bay0 - eps, -bay_h])
                cube([2 * (bay_x + bay_wall), cage_l + eps, bay_h + eps]);
            // full-length fillets from the rail walls to the plate (stiffening; inside the trough)
            for (m = [0, 1]) mirror([m, 0, 0])
                translate([outer_x - eps, 0, -wall_h])
                    hull() {
                        cube([eps, y_bay0, wall_h]);
                        translate([trough_x - 0.9 - outer_x, 0, wall_h - eps]) cube([eps, y_bay0, eps]);
                    }
        }

        // groove for the neighbour's tongue
        if (joint_left) joint_groove();

        // lips only where the pack has grooves; front envelope of the pack
        lip_front_cut();
        front_cut();

        // latch pocket in the nose (profile from the reference holder; open at the tip)
        translate([latch_w / 2, 0, 0]) rotate([0, -90, 0]) linear_extrude(latch_w)    // (z, y) polygon
            polygon(concat([[-eps, rail_len - latch_prof[0][0]]],
                           [for (q = latch_prof) [q[1], rail_len - q[0]]],
                           [[-eps, rail_len - front_l + eps]]));

        // contact tab slots through the end stop
        for (x = contact_x)
            translate([x, y_stop - cblock_ch - eps, -contact_z])
                if (tab_vertical) translate([-(tab_t + 0.15) / 2, 0, -(tab_w + 0.3) / 2])
                    cube([tab_t + 0.15, y_bay0 + wall_h - y_stop + cblock_ch + 2 * eps, tab_w + 0.3]);
                else translate([-(tab_w + 0.3) / 2, 0, -(tab_t + 0.15) / 2])
                    cube([tab_w + 0.3, y_bay0 + wall_h - y_stop + cblock_ch + 2 * eps, tab_t + 0.15]);

        // microswitch lever window + 2x M2 pilot holes (switch screwed to the
        // rear face of the end stop, inside the bay)
        translate([sw_x - sw_win[0] / 2, y_wall - eps, -sw_z - sw_win[1] / 2])
            cube([sw_win[0], stop_t + 2 * eps, sw_win[1]]);
        for (dx = [-3.25, 3.25])
            translate([sw_x + dx, y_wall + 2, -sw_z - 5.5]) hole_y(1.8, stop_t);
        // pocket for the switch body in the end-wall bevel (its roof bridges 14 mm)
        translate([sw_x - sw_body[0] / 2, y_bay0 - eps, -wall_h - eps])
            cube([sw_body[0], wall_h + 1, wall_h + eps]);

        // bay cavity, open to the rear; the end stop is its front wall
        difference() {
            translate([-bay_x, y_bay0 - 2 * eps, -bay_h + bay_wall]) cube([2 * bay_x, cage_l + 3 * eps, bay_h - bay_wall]);
            // corner columns for the lid inserts (full length -> no overhangs)
            for (sx = [-1, 1]) for (z = [-col, -bay_h + bay_wall])
                translate([sx > 0 ? bay_x - col : -bay_x, y_bay0, z]) cube([col, cage_l + eps, col]);
            // 45 deg bevel behind the end wall: printed standing on the rear face, the
            // end wall's rear face would otherwise be a 10 mm overhang
            translate([bay_x + eps, 0, 0]) rotate([0, -90, 0]) linear_extrude(2 * bay_x + 2 * eps)   // (z, y)
                polygon([[eps, y_bay0 - 3 * eps], [eps, y_bay0 + wall_h], [-wall_h, y_bay0 - 3 * eps]]);
        }
        // cable-access window in the bay floor (rear part, between the corner columns).
        // Its front edge is a 45 deg point, so the floor needs no bridge when printed upright.
        let (hw = bay_x - col, yw = y_bay0 + 4 + floor_window_y)
            translate([0, 0, -bay_h - eps]) linear_extrude(bay_wall + 2 * eps)
                polygon([[-hw, yw], [0, yw - hw], [hw, yw], [hw, total_l + 1], [-hw, total_l + 1]]);
        // card guides for the PCB (stop 4 mm short of the end stop)
        for (m = [0, 1]) mirror([m, 0, 0])
            translate([bay_x - eps, y_bay0 + 4, -pcb_z - pcb_t - 0.2])
                cube([1.2, cage_l, pcb_t + 0.4]);

        // rear lid screw holes (M3 heat-set inserts, along Y)
        for (p = bay_lid_holes()) translate([p[0], total_l - 8 + eps, p[1]]) hole_y(4.2, 8.1);

        // mounting screws (vertical). Front: flat-head, countersunk flush into the
        // channel ceiling (fit before the battery goes in). Rear: pan-head in the rear tab.
        translate([0, front_screw_y, plate_t + eps]) hole_z(screw_d, plate_t + 1);
        translate([0, front_screw_y, -csk_recess - 1]) cylinder(d = csk_d, h = 1 + eps);
        translate([0, front_screw_y, -csk_recess - eps]) cylinder(d1 = csk_d, d2 = 0, h = csk_d / 2);
        // rear screw: inside the bay, under the PCB's screwdriver hole
        translate([rear_screw_x, rear_screw_y, plate_t + eps]) hole_z(screw_d, plate_t + 1);

        // status LED in the front bezel: round holes (vertical when printed face-down).
        // Counterbore for body + flange from the front, a lip as flange stop, and a
        // wider bore behind for the solder joints.
        wy = y_front + bezel_l - wire_ch - 1;   // wire channel position along Y
        gx = led_x - wire_ch / 2;               // wire groove (shelf side) above the LED
        translate([led_x, y_front - eps, led_z]) rotate([-90, 0, 0]) cylinder(d = led_cb_d, h = led_cb_l + eps);
        translate([led_x, y_front + led_cb_l - eps, led_z]) rotate([-90, 0, 0]) cylinder(d = led_lip_d, h = led_lip_l + 2 * eps);
        translate([led_x, y_front + led_cb_l + led_lip_l, led_z]) rotate([-90, 0, 0])
            cylinder(d = led_bore_d, h = bezel_l - led_cb_l - led_lip_l - 1);
        // ... wires go straight up into a groove on the shelf side of the plate and back to the bay
        translate([led_x - wire_ch / 2, wy, led_z]) cube([wire_ch, wire_ch, plate_t - led_z + eps]);
        translate([gx, wy, plate_t - wire_gd]) cube([led_x + wire_ch / 2 - gx, wire_ch, wire_gd + eps]);
        translate([gx, wy, plate_t - wire_gd]) cube([wire_ch, y_bay0 + 18 - wy, wire_gd + eps]);
        hull() for (x = [gx, bay_x - col - 8])
            translate([x, y_bay0 + 12, plate_t - wire_gd]) cube([wire_ch, wire_ch + 1, wire_gd + eps]);
        translate([bay_x - col - 8, y_bay0 + 12, -bay_wall]) cube([wire_ch, wire_ch + 1, plate_t + bay_wall + eps]);
    }
}
function bay_lid_holes() = [
    [-bay_x + 3.5, -bay_h + bay_wall + 3.5], [bay_x - 3.5, -bay_h + bay_wall + 3.5],
    [-bay_x + 3.5, -3.5], [bay_x - 3.5, -3.5]
];

// Rear lid of the bay: power + I2C cable entries, vents
module slot_lid() {
    // Rear lid: a wide U-notch open at the bottom, so it slides on over the 24 V
    // chain jumpers and the I2C cable when they are already plugged in. It also
    // keeps the PCB from sliding out of the card guides (it sits 0.5 mm behind the board).
    lid_t = 2.4;
    col = 7;
    w = 2 * (bay_x + bay_wall);
    notch_w = 2 * (bay_x - col - 0.5);
    difference() {
        translate([-w / 2, 0, 0]) cube([w, lid_t, bay_h]);
        for (p = bay_lid_holes())
            translate([p[0], -eps, p[1] + bay_h]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = lid_t + 1);
        translate([-notch_w / 2, -eps, -eps]) cube([notch_w, lid_t + 2 * eps, bay_h - lid_notch_top + eps]);
    }
}

// Test print: 20 mm slice of the rail profile incl. lead-in and latch recess
module gauge() {
    intersection() {
        slot_module();
        translate([-outer_x - 1, y_nose - 1, -wall_h - 1]) cube([2 * outer_x + 2, y_lip + 6 - y_nose + 1, wall_h + plate_t + 2]);
    }
}

// Test print: the end of the channel (contact block, prong pockets, end wall,
// contact slots). Slide the pack in and check it seats against the contact face.
module end_gauge() {
    intersection() {
        slot_module();
        translate([-outer_x - 1, y_stop - 6, -wall_h - 1]) cube([2 * outer_x + 2, y_bay0 - y_stop + 6, wall_h + plate_t + 2]);
    }
}

// --------------------------- controller box ---------------------------
// Holds the main board (ESP32-C6 dev board + 2x TCA9548A + relay + DC/DC).
// Screws to the shelf next to the slots. Cable glands on the rear face.
// Tray for the controller board: base on the shelf, board on standoffs with its
// components facing the lid. Every connector group gets a U-notch open towards the
// lid, so all cables can be plugged in first and the lid put on afterwards:
//   left/right walls: slot cables 1-8 / 9-16; bottom wall: 24 V PSU in, OUT A/B;
//   top wall: ESP32 USB-C, SHT40 / Qwiic / expansion headers.
function ctl_o() = [ctl_in[0] + 2 * ctl_wall, ctl_in[1] + 2 * ctl_wall, ctl_in[2] + ctl_wall];
function ctl_pcb_xy(p) = [p[0] - ctl_pcb[0] / 2, ctl_wall + ctl_gap + p[1]];   // board -> box coords
function ctl_ears() = [[-1, 1], [1, 1], [-1, -1], [1, -1]];
module controller_box() {
    o = ctl_o();
    top = o[2];
    pz = ctl_wall + ctl_standoff + 1.6;      // PCB top surface
    difference() {
        union() {
            translate([-o[0] / 2, 0, 0]) cube(o);
            // shelf mounting flanges
            for (sx = [-1, 1]) translate([sx * (o[0] / 2 + 6) - 6, 0, 0]) cube([12, o[1], 4]);
            // lid ears (outside the walls, clear of the PCB), each with a 45 deg gusset
            // down to the wall so it prints without support (box printed base down)
            for (e = ctl_ears())
                hull() {
                    translate([e[0] * (o[0] / 2 + 4) - 4, (e[1] > 0 ? o[1] - 22 : 3), top - 10]) cube([8, 8, 10]);
                    translate([e[0] > 0 ? o[0] / 2 - eps : -o[0] / 2, (e[1] > 0 ? o[1] - 22 : 3), top - 10 - 8.5])
                        cube([eps, 8, eps]);
                }
        }
        translate([-ctl_in[0] / 2, ctl_wall, ctl_wall]) cube(ctl_in + [0, 0, eps]);
        for (sx = [-1, 1]) for (y = [25, o[1] - 35])   // clear of the lid ears above
            translate([sx * (o[0] / 2 + 6), y, -eps]) cylinder(d = screw_d, h = 5);
        for (e = ctl_ears())
            translate([e[0] * (o[0] / 2 + 4), (e[1] > 0 ? o[1] - 18 : 7), top - 6]) cylinder(d = 4.2, h = 6 + eps);
        // ---- cable notches, open towards the lid
        // left / right: slot connectors (board y 6..72)
        for (sx = [-1, 1]) translate([sx > 0 ? o[0] / 2 - ctl_wall - eps : -o[0] / 2 - eps,
                                      ctl_pcb_xy([0, 6])[1], pz + 2])
            cube([ctl_wall + 2 * eps, 66, top]);
        // bottom: PSU in, OUT A, OUT B, 5 V regulator (board x 2..96)
        translate([ctl_pcb_xy([2, 0])[0], o[1] - ctl_wall - eps, pz + 1]) cube([94, ctl_wall + 2 * eps, top]);
        // top: SHT40 / Qwiic / ESP USB-C / expansion (board x 15..92)
        translate([ctl_pcb_xy([15, 0])[0], -eps, pz + 1]) cube([77, ctl_wall + 2 * eps, top]);
    }
    // board standoffs (M3 heat-set inserts)
    for (h = ctl_holes) translate([ctl_pcb_xy(h)[0], ctl_pcb_xy(h)[1], ctl_wall - eps])
        difference() { cylinder(d = 7, h = ctl_standoff); translate([0, 0, 1]) cylinder(d = 4.2, h = ctl_standoff); }
}
module controller_lid() {
    o = ctl_o();
    difference() {
        union() {
            translate([-o[0] / 2, 0, 0]) cube([o[0], o[1], 2.4]);
            for (e = ctl_ears())
                translate([e[0] * (o[0] / 2 + 4) - 4, (e[1] > 0 ? o[1] - 22 : 3), 0]) cube([8, 8, 2.4]);
            // locating lip (inside the corners only, so the notches stay free)
            for (sx = [-1, 1]) for (y = [ctl_wall + 0.3, o[1] - ctl_wall - 8.3])
                translate([sx > 0 ? ctl_in[0] / 2 - 8.3 : -ctl_in[0] / 2 + 0.3, y, 2.4 - eps]) cube([8, 8, 3]);
        }
        for (e = ctl_ears())
            translate([e[0] * (o[0] / 2 + 4), (e[1] > 0 ? o[1] - 18 : 7), -eps]) cylinder(d = 3.4, h = 10);
        // vent slots above the regulator / bus switch area
        for (i = [0:7]) translate([-30 + i * 8, o[1] - 30, -eps]) cube([3, 20, 3]);
    }
}

// ------------------------------ output --------------------------------
// Print orientation for the slot module: REAR FACE ON THE BED (Y -> Z).
// Every layer then contains the complete rail profile, so the load-bearing
// lips are strong; the bay walls reach the bed, the end wall has a 45 deg bevel
// behind it and the floor window a pointed front edge, so nothing needs support. Use PETG/ASA, 4 walls, 30 % gyroid.

// generic 5 mm LED (T-1 3/4) for the previews: 5.0 body, 5.8 x 1 mm flange,
// 8.6 mm flange-to-tip, 4 leads 0.5 mm square trimmed to 5 mm
module dummy_led() {
    color("white", 0.9) rotate([90, 0, 0]) {
        cylinder(d = 5.8, h = 1);
        cylinder(d = 5, h = 8.6 - 2.5);
        translate([0, 0, 8.6 - 2.5]) sphere(d = 5);
    }
    color("silver") for (i = [0:3]) translate([-1.9 + i * 1.27, 0, -0.25]) cube([0.5, 5, 0.5]);
}
module dummy_battery() {
    color("forestgreen", 0.85) translate([-43, 3, -wall_h - 75]) cube([86, rail_len - 3, 75]);
    color("forestgreen", 0.85) for (m = [0, 1]) mirror([m, 0, 0])
        translate([trough_x + 0.5, 3, -wall_h - eps]) cube([43 - trough_x - 0.5, rail_len - 3, wall_h - body_top + eps]);
    color("darkgreen", 0.85) translate([-chan_w / 2 + 0.3, 3, -wall_h + 0.2])
        cube([chan_w - 0.6, rail_len - 3, wall_h - 0.5]);
}

if (part == "slot") rotate([-90, 0, 0]) translate([0, -total_l, 0]) slot_module();   // rear face on the bed
else if (part == "slot_lid") translate([0, 0, 2.4]) rotate([-90, 0, 0]) slot_lid();   // outer face on the bed
else if (part == "gauge") rotate([-90, 0, 0]) translate([0, -(y_lip + 6), 0]) gauge();
else if (part == "end_gauge") rotate([-90, 0, 0]) translate([0, -y_bay0, 0]) end_gauge();
else if (part == "controller") controller_box();
else if (part == "controller_lid") controller_lid();
else if (part == "single") slot_module();
// cut through the LED bezel with the LED in place
else if (part == "led_section") intersection() {
    union() { slot_module(); translate([led_x, y_front + led_cb_l, led_z]) dummy_led(); }
    translate([led_x - 30, y_front - 10, -20]) cube([30, 40, 40]);
}
// two neighbours overlapped: renders EMPTY if the joint does not collide
// cross-section through two neighbours at y = 60 (for checking the joint fit)
else if (part == "joint_section") projection(cut = true) rotate([-90, 0, 0]) translate([0, -60, 0])
    for (i = [0, 1]) translate([i * pitch, 0, 0]) slot_module();
// 20 mm test pieces of both edges (tongue + groove) to check the joint clearance
else if (part == "joint_gauge") rotate([90, 0, 0]) translate([0, -y_front, 0]) for (sx = [-1, 1])
    translate([-sx * (mod_w / 2 - 20), 0, 0]) intersection() {
        slot_module();
        translate([sx > 0 ? mod_w / 2 - bar_w - 2 : -mod_w / 2 - 1, y_front - 1, bar_bot - 1])
            cube([bar_w + 3 + jt_gap + jt_d + 1, 21, plate_t - bar_bot + 2]);
    }
else if (part == "joint_check") intersection() { slot_module(); translate([pitch, 0, 0]) slot_module(); }
else if (part == "assembly") {
    // the right-hand module is shown half slid on, to show the dovetail joint
    for (i = [0:2]) translate([(i - 1) * pitch, i == 2 ? -80 : 0, 0]) {
        color("lightgray") slot_module();
        color("dimgray") translate([0, total_l, -bay_h]) slot_lid();
        if (i != 1) dummy_battery();
    }
    translate([2.4 * pitch, 0, plate_t]) mirror([0, 0, 1]) color("silver") controller_box();
    %translate([-1.6 * pitch, -10, plate_t]) cube([4.2 * pitch, mod_l + 40, 18]); // shelf
}
