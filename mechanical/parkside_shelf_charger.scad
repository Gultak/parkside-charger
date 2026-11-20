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
//    openscad -D 'part="slot_cover"'     -o slot_cover.stl      parkside_shelf_charger.scad
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

part = "assembly"; // [slot, slot_cover, gauge, end_gauge, joint_gauge, controller, controller_preview, controller_lid, assembly, single, joint_section, joint_check]

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
cblock_ch = 0.8;  // small 45 deg chamfer on the contact block's front corners (the original charger has a square block)
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

/* [Battery contacts: FASTON 250 male crimp tabs (TE 42475-4, 6.35 x 0.81 mm, 22-18 AWG)] */
// X positions of the contact tabs, measured from the channel centre line.
// Parkside X20V: B+, ID (BMS status, ~10k to B-), T (unused, ~512k), B-
contact_x   = [-12, -4, 4, 12];   // measured: 8 mm pitch; seen from the front: +, ID, T, - (T not used)
contact_z   = 5.5;  // tab centre below the plate face
contact_used = [true, true, false, true];   // + ID T -: T needs no tab
contact_len = 6.5;  // how far the tab tip sticks out of the contact face (battery slots are 9.8 deep)
tab_w       = 6.2;  // tab width            (measured on the user's 6.3 mm housing-lock tabs)
tab_t       = 0.7;  // tab thickness
tab_flat    = 14;   // flat tab length, tip to where the side ears widen it
ear_w       = 8.0;  // width across the side ears (the forward stop)  CHECK on your part
lance_root  = 9;    // locking lance: root, measured from the tip
lance_end   = 13;   // free end of the lance from the tip (measured 12.5-13: use the far value)
lance_h     = 2;    // how far the lance end stands off the blade
barrel_w    = 5.0;  // pocket for the crimped barrel + wire, across the tab plane (the tab is vertical);
                    // barrel and lance sit on the same side of the tab plane: fit them facing inwards
tab_vertical = true; // blade plane vertical (the pockets assume this)

/* [Module frame] */
pitch    = 86;    // module width = slot spacing (battery bodies measured <= 85 mm; grabbed from below)
plate_t  = 10;    // mounting plate thickness (carries the dovetail and the LED; as on the reference holder)
wall_t   = 5;     // rail wall thickness
stop_t   = 8;     // end wall thickness (behind the prong tips)
bay_l    = 4 + 47.5 + 0.5 + 1.8 + 0.8;   // electronics bay: 4 mm gap, PCB, 0.5 mm, cover back face, 0.8 mm rim
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
jt_clear = 0.15;      // clearance per side (0.2 test-fitted loose; raise to 0.2-0.25 if it binds)
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
sw_x    = -18.5;// switch window centre from channel centre (behind the left prong)
sw_z    = 3.5;
sw_win  = [8, 4];   // window through the end stop for the lever (X, Z)

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

/* [Clip-on bay cover (front + bottom + back in one U-shaped part)] */
cov_t      = 1.8;    // wall thickness
cov_cl     = 0.3;    // clearance to the side walls (per side)
tongue_h   = 2.5;    // the cover's front tongue goes this far up into a slot under the end wall
tongue_w   = 54;     // its width (the end wall is 2 * outer_x wide)
cov_notch_bot = 24;  // cable cut-outs in the back face reach down to this depth below the plate
cov_notch_l = [-34.9, 11];   // X range: 24 V IN/OUT XT30s (left; their noses reach through)
cov_notch_r = [14, 29];      // X range: I2C plug (right)
tab_z      = [-32, -24];     // spring tabs rising from the floor near the rear corners
tab_l      = 8;      // their length along Y
hook       = 0.8;    // hook height (into the side-wall grooves)

/* [Controller box (controller board 112 x 64 mm, rev B)] */
ctl_pcb  = [112, 64];
ctl_gap  = 4;             // PCB to inner wall
ctl_wall = 2.4;
ctl_standoff = 8;         // PCB above the base
ctl_holes = [[5.5, 60], [106.5, 60], [36.5, 4], [79.5, 4]];        // PCB mounting holes (board coords)
ctl_chan = 12;            // cable channel between the board's bottom edge and the PSU partition

/* [Built-in power supply (Mean Well LOP open frame)] */
psu = "LOP-300";          // [LOP-400, LOP-300, none]
psu_gap = 8;              // PSU board edge to the compartment walls (wiring, airflow)
psu_standoff = 6;         // M3 standoffs (datasheet: max 3 mm of pins below the PSU board)
part_t = 2.4;             // partition wall between the mains and the low-voltage compartment
mains_entry = "gland";    // [gland, iec] hard-wired flex through a cable gland, or an IEC C14 inlet
gland_d = 20.5;           // M20 cable gland: clearance hole (the nut goes inside)
mains_bay = 25;           // extra room between the PSU and the rear wall for the gland nut, the
                          // flex bend, the Wago connectors and the KSD301 (gland version only)
iec_cut = [47.2, 28.1];   // IEC C14 inlet with fuse + switch, 50 mm snap-in size: Schurter DD11.0121.1111 (47.1 x 28.1)
                          // or ISL MIS-I-80485 (47 x 27.9, flange 50 x 30.5) both fit
iec_panel_t = 2.0;        // wall thickness at the inlet for its snap-in clips (recessed from the inside; CHECK)
psu_fan = true;           // 90/92 mm 12 V PWM fan on the lid, blowing onto the PSU (finger-safe grille)
fan_size = 92;            // fan frame
fan_hole_pitch = 82.5;    // fan screw holes (92 mm fan: 82.5, 80 mm fan: 71.5)
fan_hole_d = 4.4;         // fan screws / M4
power_led = true;         // panel LED (Lumex SSI-LXMP059ID, snap-in) in the front wall (opposite the mains entry)
led_pos = [-36, 34];      // its centre: X in the box, Z above the base (above the slot cables)
led_cut = [6.6, 4.6];     // its rectangular cut-out (catalogue: 0.258 x 0.177 in)  CHECK against your part
led_panel_t = 1.6;        // lid thickness at the LED, for its snap-in clips (recessed from the inside)  CHECK
vent_w = 2.5;             // vent slot width (finger-safe)
// cable openings: notches open towards the lid, closed by fins on the lid down to a slot
cable_floor = 8;          // notch floor above the controller board's top face
cable_gap = 5;            // height of the slot the lid's fins leave for the cables
psu_lead_slot = 10;       // depth (from the top) of the slot for the PSU leads in the partition
// USB-C of the ESP32-C6 D1 in the front wall: the module sits with its USB-C mouth at the wall's
// inside face (controller board layout); the plug's overmold goes into a pocket from outside
esp_x = 56;               // module centre on the controller board (board X, as in layout.py)
usb_h = 14.2;             // USB-C centre above the controller board's top face  CHECK (measure)
usb_hole = [9.6, 4.0];    // through the wall: the receptacle (8.94 x 3.26) + clearance
usb_plug = [13.5, 7.5];   // pocket from outside for the plug's overmold
usb_skin = 0.8;           // wall left between the pocket and the inside face
// snap-in lid: tabs on the lid hook into windows through the walls (press in from outside to open)
lid_snap = true;
lid_mains_screws = true;  // keep 2 screws over the mains compartment (opening it then needs a tool)
snap_w = 10; snap_t = 1.8; snap_l = 12; snap_hook = 1.2;

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

// Groove / slot cutter for the upright print (rear face on the bed, so -Y is up):
// a box [x0..x0+w] x [y0..y1] x [z0..z0+h] that is open on one side ("open" = "-x", "+x",
// "-z" or "+z"); its upper end (y0) is a 45 deg slope that closes towards the open side, so the
// roof never overhangs into thin air.
module groove45(x0, w, y0, y1, z0, h, open) {
    d = (open == "-z" || open == "+z") ? h : w;   // depth measured from the open side
    hull() {
        if (open == "+z") {
            translate([x0, y0 - d, z0 + h - eps]) cube([w, y1 - y0 + d, eps]);
            translate([x0, y0, z0]) cube([w, y1 - y0, h]);
        } else if (open == "-z") {
            translate([x0, y0, z0]) cube([w, y1 - y0, eps]);            // open side starts at y0 - d
            translate([x0, y0 - d, z0]) cube([w, y1 - y0 + d, eps]);
            translate([x0, y0, z0 + h - eps]) cube([w, y1 - y0, eps]);
        } else {
            xo = open == "-x" ? x0 : x0 + w - eps;   // face on the open side
            translate([xo, y0 - d, z0]) cube([eps, y1 - y0 + d, h]);
            translate([x0, y0, z0]) cube([w, y1 - y0, h]);
        }
    }
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

        // crimp-tab pockets: a slot for the flat tab at the front, a wedge-shaped window
        // the locking lance springs into, then a 45 deg taper where the side ears sit
        // (forward stop) and the pocket for the barrel and wire straight back into the bay;
        // a slit in the tab plane lets the ears through.
        // Pushed in from the bay, the lance clicks in behind the ledge and holds the tab
        // against the battery pushing it back.
        for (i = [0 : len(contact_x) - 1]) if (contact_used[i]) let (x = contact_x[i], zc = -contact_z,
                ya = y_stop - contact_len + tab_flat, h = tab_w + 0.3, ts = tab_t + 0.15,
                he = ear_w + 0.4,
                sd = x < 0 ? 1 : -1,                                     // barrel/lance side: towards the centre
                xf = x + sd * ts / 2,                                    // blade face on that side
                x0 = sd > 0 ? x - ts / 2 - 0.15 : x + ts / 2 + 0.15 - barrel_w, // pocket [x0, x0 + barrel_w]
                yb = ya + barrel_w - ts - 0.15,                          // end of the 45 deg taper
                yl0 = y_stop - contact_len + lance_root - 0.3,           // lance window: root ...
                yl1 = y_stop - contact_len + lance_end + 0.15,           // ... to the ledge it catches on
                lw = lance_h + 0.4) {
            translate([x - ts / 2, y_stop - cblock_ch - eps, zc - h / 2]) cube([ts, ya - y_stop + cblock_ch + eps, h]);
            hull() {                                                       // lance window (wedge: no overhang)
                translate([xf - (sd > 0 ? eps : 0), yl0, zc - h / 2]) cube([eps, eps, h]);
                translate([sd > 0 ? xf - eps : xf - lw, yl1 - eps, zc - h / 2]) cube([lw + eps, eps, h]);
            }
            hull() {
                translate([x - ts / 2, ya - eps, zc - h / 2]) cube([ts, eps, h]);
                translate([x0, yb, zc - h / 2]) cube([barrel_w, eps, h]);
            }
            translate([x0, yb, zc - h / 2]) cube([barrel_w, y_bay0 + wall_h + 1 - yb, h]);
            // slit for the side ears in the tab plane, behind the stop; open at the bottom
            // (the ears reach to 0.4 mm above the block's underside: no skin worth keeping)
            translate([x - ts / 2 - 0.15, ya, -wall_h - 1]) cube([ts + 0.3, y_bay0 + wall_h + 1 - ya, wall_h + 1 - contact_z + he / 2]);
        }

        // microswitch lever window + 2x M2 pilot holes (switch screwed to the
        // rear face of the end stop, inside the bay)
        translate([sw_x - sw_win[0] / 2, y_wall - eps, -sw_z - sw_win[1] / 2])
            cube([sw_win[0], stop_t + 2 * eps, sw_win[1]]);
        for (dx = [-3.25, 3.25])
            translate([sw_x + dx, y_wall + 2, -sw_z - 5.5]) hole_y(1.8, stop_t);
        // pocket for the switch body in the end-wall bevel (its roof bridges 14 mm)
        translate([sw_x - sw_body[0] / 2, y_bay0 - eps, -wall_h - eps])
            cube([sw_body[0], wall_h + 1, wall_h + eps]);

        // bay cavity, open to the rear and the bottom (the clip-on cover closes both)
        difference() {
            translate([-bay_x, y_bay0 - 2 * eps, -bay_h - eps]) cube([2 * bay_x, cage_l + 3 * eps, bay_h + eps]);
            // 45 deg bevel behind the end wall: printed standing on the rear face, the
            // end wall's rear face would otherwise be a 10 mm overhang
            translate([bay_x + eps, 0, 0]) rotate([0, -90, 0]) linear_extrude(2 * bay_x + 2 * eps)   // (z, y)
                polygon([[eps, y_bay0 - 3 * eps], [eps, y_bay0 + wall_h], [-wall_h, y_bay0 - 3 * eps]]);
        }
        // slot in the end wall's underside for the cover's front tongue
        groove45(-tongue_w / 2 - 0.4, tongue_w + 0.8, y_bay0 - 1.7, y_bay0 - 0.1, -wall_h - eps, tongue_h + 0.3 + eps, "-z");
        // grooves in the side walls for the cover's spring-tab hooks
        for (m = [0, 1]) mirror([m, 0, 0])
            groove45(bay_x - eps, hook + 0.2, cov_tab_y() - 0.3, cov_tab_y() + tab_l + 0.3, tab_z[1] - 3.4, 3.9, "-x");
        // locating groove in the plate for the cover's back face
        groove45(-bay_x, 2 * bay_x, cov_back_y() - 0.2, cov_back_y() + cov_t + 0.2, -eps, 1.2, "-z");
        // card guides for the PCB (stop 4 mm short of the end stop)
        for (m = [0, 1]) mirror([m, 0, 0])
            groove45(bay_x - eps, 1.2, y_bay0 + 4.4, y_bay0 + cage_l + 1, -pcb_z - pcb_t - 0.2, pcb_t + 0.4, "-x");

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
        groove45(bay_x - col - 8, gx + wire_ch - (bay_x - col - 8), y_bay0 + 12, y_bay0 + 18, plate_t - wire_gd,
                 wire_gd + eps, "+z");
        translate([bay_x - col - 8, y_bay0 + 12, -bay_wall]) cube([wire_ch, wire_ch + 1, plate_t + bay_wall + eps]);
    }
}
function cov_back_y() = total_l - 0.8 - cov_t;          // inner face of the cover's back face
function cov_tab_y() = cov_back_y() - tab_l - 2;        // start of the spring tabs along Y

// Clip-on U-shaped bay cover: front face + floor + back face. Fit it after the module is
// screwed on and all cables are plugged in: put the front tongue up into the slot under the
// end wall, swing the rear up - the cables drop into the cut-outs, which are open at the top -
// until the two spring tabs click into the side walls. To remove it, push the tabs
// inwards through the cable cut-outs. Print with the floor on the bed.
module slot_cover() {
    w2 = bay_x - cov_cl;            // half width (fits between the side walls)
    yf = y_bay0 + 0.2;              // front face, just behind the end wall
    difference() {
        union() {
            // front face, a web forward under the end wall, and the tongue up into its slot
            translate([-w2, yf, -bay_h]) cube([2 * w2, cov_t, bay_h - wall_h - 0.2]);
            // web: its underside slopes at 45 deg from the front face (prints without overhang)
            translate([tongue_w / 2, 0, 0]) rotate([0, -90, 0]) linear_extrude(tongue_w)    // (z, y) polygon
                polygon([[-wall_h - 0.2, y_bay0 - 1.5], [-wall_h - 0.2, yf + cov_t],
                         [-wall_h - 0.6 - (yf + cov_t - y_bay0 + 1.5), yf + cov_t],
                         [-wall_h - 0.6 - (yf - y_bay0 + 1.5), yf], [-wall_h - 0.6, y_bay0 - 1.5]]);
            translate([-tongue_w / 2, y_bay0 - 1.5, -wall_h - 0.4]) cube([tongue_w, 1.2, tongue_h + 0.4]);
            // floor
            translate([-w2, yf, -bay_h]) cube([2 * w2, cov_back_y() + cov_t - yf, cov_t]);
            // back face, up into the plate groove
            translate([-w2, cov_back_y(), -bay_h]) cube([2 * w2, cov_t, bay_h + 1.0]);
            // spring tabs with hooks (lead-in on top, 45 deg latch face below: prints without
            // overhang, and lets go with a firm pull)
            for (m = [0, 1]) mirror([m, 0, 0]) {
                translate([w2 - cov_t, cov_tab_y(), -bay_h]) cube([cov_t, tab_l, tab_z[1] + bay_h]);
                translate([w2 - eps, cov_tab_y(), 0]) rotate([90, 0, 0]) mirror([0, 0, 1])
                    linear_extrude(tab_l) polygon([[0, tab_z[1] - 2 - cov_cl - hook], [cov_cl + hook, tab_z[1] - 2],
                                                   [cov_cl + hook, tab_z[1] - 1.4], [0, tab_z[1]]]);
            }
        }
        // gaps in the tongue where the contact blades pass through the end wall
        for (i = [0 : len(contact_x) - 1]) if (contact_used[i])
            translate([contact_x[i] - barrel_w - 0.5, y_bay0 - 2, -wall_h - 0.5]) cube([2 * barrel_w + 1, 2, tongue_h + 1]);
        // cable cut-outs, open at the top
        for (n = [cov_notch_l, cov_notch_r])
            translate([n[0], cov_back_y() - eps, -cov_notch_bot]) cube([n[1] - n[0], cov_t + 2 * eps, cov_notch_bot + 2]);
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
// Tray for the controller board, plus (optional) a separate mains compartment for a
// Mean Well LOP-300/400 open-frame PSU. Base on the shelf, boards on standoffs.
// Low-voltage compartment: every connector group gets a U-notch open towards the lid,
// so all cables can be plugged in first and the lid put on afterwards:
//   left/right walls: slot cables 1-8 / 9-16, and OUT A/B (they run along the cable
//   channel behind the board); top wall: ESP32 USB-C, SHT21 / Qwiic / expansion.
// Mains compartment: closed walls, M20 cable gland (or IEC C14 inlet) in the rear wall,
// finger-safe vent slots; the PSU's 24 V leads pass the partition in one small notch.
// PSU data [L, W, H], first hole from the corner [x, y], hole spacing [x, y] (datasheets)
function psu_spec() = psu == "LOP-300" ? [[101.6, 50.8, 25.4], [3.175, 3.175], [95.25, 44.45]]
                                       : [[127, 76.2, 27.5], [5.7, 5.7], [115.6, 64.8]];
function has_psu() = psu != "none";
function ctl_ix() = max(ctl_pcb[0] + 2 * ctl_gap, has_psu() ? psu_spec()[0][0] + 2 * psu_gap : 0);
function ctl_iz() = 48;   // room above the board for the vertical XT30 plugs (OUT A/B) and their cables
function ctl_y1() = ctl_wall + ctl_gap + ctl_pcb[1] + (has_psu() ? ctl_chan : ctl_gap);  // end of LV cavity
function psu_y0() = ctl_y1() + part_t;                                                   // start of PSU cavity
function psu_y1() = psu_y0() + psu_spec()[0][1] + 2 * psu_gap + (mains_entry == "gland" ? mains_bay : 0);
function ctl_o() = [ctl_ix() + 2 * ctl_wall, (has_psu() ? psu_y1() : ctl_y1()) + ctl_wall, ctl_iz() + ctl_wall];
function ctl_pcb_xy(p) = [p[0] - ctl_pcb[0] / 2, ctl_wall + ctl_gap + p[1]];   // board -> box coords
function psu_xy0() = [-psu_spec()[0][0] / 2, psu_y0() + psu_gap];              // PSU board corner
function psu_holes() = [for (i = [0, 1], j = [0, 1])
    psu_xy0() + psu_spec()[1] + [i * psu_spec()[2][0], j * psu_spec()[2][1]]];
// lid ears: [side, y of the ear's start]; mid pair at the partition for the long box
function ctl_ears() = let(o = ctl_o())
    lid_snap ? (lid_mains_screws ? [[-1, o[1] - 22], [1, o[1] - 22]] : [])
             : concat([[-1, 3], [1, 3], [-1, o[1] - 22], [1, o[1] - 22]], has_psu() ? [[-1, psu_y0() + 2], [1, psu_y0() + 2]] : []);
function ctl_pz() = ctl_wall + ctl_standoff + 1.6;      // controller board top face
function cable_z() = ctl_pz() + cable_floor;
// cable notches: [wall, from, to]; L/R side walls (along Y), F front wall / B rear wall (along X)
function ctl_notches() = concat(
    [["L", ctl_pcb_xy([0, 0.5])[1], ctl_y1() - 3], ["R", ctl_pcb_xy([0, 0.5])[1], ctl_y1() - 3]],
    [["F", ctl_pcb_xy([27, 0])[0], ctl_pcb_xy([43, 0])[0]],      // SHT21 + Qwiic
     ["F", ctl_pcb_xy([68.5, 0])[0], ctl_pcb_xy([77, 0])[0]]],   // expansion header
    has_psu() ? [] : [["B", ctl_pcb_xy([14, 0])[0], ctl_pcb_xy([92, 0])[0]]]);
// snaps: [wall, position along it]
function ctl_snaps() = let(o = ctl_o(), ym = (psu_y0() + psu_y1()) / 2)
    concat([["F", -46], ["F", 38], ["B", -30], ["B", 30]], has_psu() ? [["L", ym], ["R", ym]] : []);
// a block in the plane of a wall: along = [a, b], z = [z0, z1], inset = clearance off the
// along-ends, t = [t0, t1] depth into the wall from its outside face
module wall_block(w, a, b, z0, z1, inset = 0, t = [-0.01, 0]) {
    o = ctl_o(); tw = ctl_wall + t[1] - t[0];
    if (w == "L") translate([-o[0] / 2 + t[0], a + inset, z0]) cube([tw, b - a - 2 * inset, z1 - z0]);
    if (w == "R") translate([o[0] / 2 - ctl_wall - t[1], a + inset, z0]) cube([tw, b - a - 2 * inset, z1 - z0]);
    if (w == "F") translate([a + inset, t[0], z0]) cube([b - a - 2 * inset, tw, z1 - z0]);
    if (w == "B") translate([a + inset, o[1] - ctl_wall - t[1], z0]) cube([b - a - 2 * inset, tw, z1 - z0]);
}
// local frame of a wall's inside face: origin on the face at "pos", +Y into the box
module at_wall(w, pos) {
    o = ctl_o(); ix = ctl_ix();
    if (w == "F") translate([pos, ctl_wall, 0]) children();
    if (w == "B") translate([pos, o[1] - ctl_wall, 0]) mirror([0, 1, 0]) children();
    if (w == "L") translate([-ix / 2, pos, 0]) rotate([0, 0, -90]) children();
    if (w == "R") translate([ix / 2, pos, 0]) rotate([0, 0, 90]) children();
}
module controller_box() {
    o = ctl_o();
    top = o[2];
    ix = ctl_ix();
    pz = ctl_wall + ctl_standoff + 1.6;      // PCB top surface
    difference() {
        union() {
            translate([-o[0] / 2, 0, 0]) cube(o);
            // shelf mounting flanges
            for (sx = [-1, 1]) translate([sx * (o[0] / 2 + 6) - 6, 0, 0]) cube([12, o[1], 4]);
            // lid ears (outside the walls, on solid wall), each with a 45 deg gusset
            // down to the wall so it prints without support (box printed base down)
            for (e = ctl_ears())
                hull() {
                    translate([e[0] * (o[0] / 2 + 4) - 4, e[1], top - 10]) cube([8, 8, 10]);
                    translate([e[0] > 0 ? o[0] / 2 - eps : -o[0] / 2, e[1], top - 10 - 8.5]) cube([eps, 8, eps]);
                }
        }
        // low-voltage cavity
        translate([-ix / 2, ctl_wall, ctl_wall]) cube([ix, ctl_y1() - ctl_wall, ctl_iz() + eps]);
        // mains cavity
        if (has_psu()) translate([-ix / 2, psu_y0(), ctl_wall]) cube([ix, psu_y1() - psu_y0(), ctl_iz() + eps]);
        // shelf screws in the flanges (clear of the lid ears above)
        for (sx = [-1, 1]) for (y = has_psu() ? [25, ctl_y1() - 30, o[1] - 35] : [25, o[1] - 35])
            translate([sx * (o[0] / 2 + 6), y, -eps]) cylinder(d = screw_d, h = 5);
        for (e = ctl_ears())
            translate([e[0] * (o[0] / 2 + 4), e[1] + 4, top - 6]) cylinder(d = 4.2, h = 6 + eps);
        // ---- cable notches, open towards the lid; the lid's fins close them down to a slot
        for (n = ctl_notches()) wall_block(n[0], n[1], n[2], cable_z(), top + 1, 0, [-1, 1]);
        // ---- USB-C of the ESP32 module: hole for the receptacle, pocket for the plug from outside
        let(ux = ctl_pcb_xy([esp_x, 0])[0], uz = ctl_pz() + usb_h) {
            translate([ux, -1, uz]) rotate([-90, 0, 0])
                linear_extrude(ctl_wall + 2) offset(r = 1.6) offset(delta = -1.6) square(usb_hole, center = true);
            translate([ux, -1, uz]) rotate([-90, 0, 0])
                linear_extrude(1 + ctl_wall - usb_skin) offset(r = 1.5) offset(delta = -1.5) square(usb_plug, center = true);
        }
        // ---- power LED in the front wall, thinned from inside for its snap-in clips
        if (power_led) {
            translate([led_pos[0] - led_cut[0] / 2, -1, led_pos[1] - led_cut[1] / 2]) cube([led_cut[0], ctl_wall + 2, led_cut[1]]);
            if (led_panel_t < ctl_wall)
                translate([led_pos[0] - led_cut[0] / 2 - 3, led_panel_t, led_pos[1] - led_cut[1] / 2 - 3])
                    cube([led_cut[0] + 6, ctl_wall, led_cut[1] + 6]);
        }
        // ---- windows for the lid's snap hooks (through: press the hook in from outside to open)
        if (lid_snap) for (sn = ctl_snaps()) at_wall(sn[0], sn[1])
            translate([-(snap_w + 1) / 2, -ctl_wall - 1, top - snap_l - 0.2]) cube([snap_w + 1, ctl_wall + 1.01, snap_l - 8.7 + 0.2 + 0.2]);
        if (has_psu()) {
            // 24 V leads from the PSU output terminals (right end) through the partition
            translate([ix / 2 - psu_gap - 22, ctl_y1() - eps, top - psu_lead_slot]) cube([14, part_t + 2 * eps, psu_lead_slot + 1]);
            // mains entry in the rear wall, next to the PSU's AC input (left end): an M20 cable
            // gland for the hard-wired flex (default), or an IEC C14 inlet with fuse + switch
            if (mains_entry == "gland")
                translate([-ix / 2 + psu_gap + 4 + 14, o[1] + eps, ctl_wall + 5 + 14]) rotate([90, 0, 0])
                    cylinder(d = gland_d, h = ctl_wall + 2 * eps, $fn = 64);
            if (mains_entry == "iec")
                translate([-ix / 2 + psu_gap + 4, o[1] - ctl_wall - eps, ctl_wall + 5]) cube([iec_cut[0], ctl_wall + 2 * eps, iec_cut[1]]);
            if (mains_entry == "iec" && iec_panel_t < ctl_wall)   // thinner wall around the cut-out, for the snap-in clips
                translate([-ix / 2 + psu_gap + 4 - 2, o[1] - ctl_wall - eps, ctl_wall + 5 - 2])
                    cube([iec_cut[0] + 4, ctl_wall - iec_panel_t + eps, iec_cut[1] + 4]);
            // vent slots in both side walls of the mains compartment (low and high rows)
            for (sx = [-1, 1]) for (y = [psu_y0() + 14 : 6 : psu_y1() - 8]) for (z = [ctl_wall + 4, ctl_wall + 22])
                translate([sx > 0 ? o[0] / 2 - ctl_wall - eps : -o[0] / 2 - eps, y, z]) cube([ctl_wall + 2 * eps, vent_w, 14]);
        }
    }
    // board standoffs (M3 heat-set inserts)
    for (h = ctl_holes) translate([ctl_pcb_xy(h)[0], ctl_pcb_xy(h)[1], ctl_wall - eps])
        difference() { cylinder(d = 7, h = ctl_standoff); translate([0, 0, 1]) cylinder(d = 4.2, h = ctl_standoff); }
    // PSU standoffs (M3 heat-set inserts). The PSU's earth-marked hole gets PE (ring lug).
    if (has_psu())
        for (h = psu_holes()) translate([h[0], h[1], ctl_wall - eps])
            difference() { cylinder(d = 7.5, h = psu_standoff); translate([0, 0, 1]) cylinder(d = 4.2, h = psu_standoff); }
}
// lid as installed (on top of the box); controller_lid() turns it over for printing
module controller_lid_installed() {
    o = ctl_o();
    ix = ctl_ix();
    top = o[2];
    difference() {
        union() {
            translate([-o[0] / 2, 0, top]) cube([o[0], o[1], 2.4]);
            for (e = ctl_ears())
                translate([e[0] * (o[0] / 2 + 4) - 4, e[1], top]) cube([8, 8, 2.4]);
            // locating lips in the inside corners
            lips_y = has_psu() ? [ctl_wall + 0.3, psu_y0() + 0.3, o[1] - ctl_wall - 8.3]
                               : [ctl_wall + 0.3, o[1] - ctl_wall - 8.3];
            for (sx = [-1, 1]) for (y = lips_y)
                translate([sx > 0 ? ix / 2 - 8.3 : -ix / 2 + 0.3, y, top - 3]) cube([8, 8, 3 + eps]);
            // fins that close the cable notches down to a cable_gap slot
            for (n = ctl_notches()) wall_block(n[0], n[1], n[2], cable_z() + cable_gap, top + eps, 0.3, [0.15, -0.15]);
            // snap tabs with a hook at the tip (45 deg lead-in, flat catch)
            if (lid_snap) for (sn = ctl_snaps()) at_wall(sn[0], sn[1]) {
                translate([-snap_w / 2, 0.2, top - snap_l]) cube([snap_w, snap_t, snap_l + eps]);
                translate([snap_w / 2, 0, 0]) rotate([0, -90, 0]) linear_extrude(snap_w) polygon([
                    [top - snap_l, 0.2 + eps], [top - snap_l + snap_hook, 0.2 - snap_hook],
                    [top - 8.7, 0.2 - snap_hook], [top - 8.7, 0.2 + eps]]);
            }
        }
        for (e = ctl_ears())
            translate([e[0] * (o[0] / 2 + 4), e[1] + 4, top - 1]) cylinder(d = 3.4, h = 10);
        // vent slots above the regulator / bus switch area
        for (i = [0:7]) translate([-30 + i * 8, ctl_y1() - 26, top - 1]) cube([3, 18, 5]);
        // above the PSU: the fan's grille and screw holes, or plain vent slots (finger-safe width)
        if (has_psu() && psu_fan) {
            fc = [0, (psu_y0() + psu_y1()) / 2];                // fan centred over the mains compartment
            intersection() {
                translate([fc[0], fc[1], top - 1]) cylinder(d = fan_size - 6, h = 5, $fn = 96);
                for (y = [-fan_size / 2 : vent_w + 2.5 : fan_size / 2])
                    translate([fc[0] - fan_size / 2, fc[1] + y, top - 1]) cube([fan_size, vent_w, 5]);
            }
            for (dx = [-1, 1], dy = [-1, 1])
                translate([fc[0] + dx * fan_hole_pitch / 2, fc[1] + dy * fan_hole_pitch / 2, top - 1])
                    cylinder(d = fan_hole_d, h = 10, $fn = 24);
            // slot for the fan's 4-pin plug into the low-voltage side (to J7, right of the ESP32)
            translate([fan_size / 2 + 7 - 6, ctl_y1() - 7 - 3, top - 1]) cube([12, 6, 5]);
        } else if (has_psu())
            for (y = [psu_y0() + psu_gap + 6 : 6 : psu_y1() - psu_gap - 6])
                translate([-psu_spec()[0][0] / 2 + 12, y, top - 1]) cube([psu_spec()[0][0] - 24, vent_w, 5]);
    }
}
module controller_lid() rotate([0, 180, 0]) translate([0, 0, -(ctl_o()[2] + 2.4)]) controller_lid_installed();
// for previews: the PSU as a block
module dummy_psu() {
    if (has_psu()) color("darkgreen", 0.8)
        translate([psu_xy0()[0], psu_xy0()[1], ctl_wall + psu_standoff]) cube(psu_spec()[0]);
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
else if (part == "slot_cover") translate([0, 0, bay_h]) slot_cover();   // floor on the bed
else if (part == "gauge") rotate([-90, 0, 0]) translate([0, -(y_lip + 6), 0]) gauge();
else if (part == "end_gauge") rotate([-90, 0, 0]) translate([0, -y_bay0, 0]) end_gauge();
else if (part == "controller") controller_box();
else if (part == "controller_preview") { controller_box(); dummy_psu(); }
else if (part == "controller_lid") controller_lid();
else if (part == "controller_closed") { controller_box(); color("steelblue", 0.6) controller_lid_installed(); }
else if (part == "controller_lid_check") intersection() { controller_box(); translate([0, 0, 0.01]) controller_lid_installed(); }
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
        color("dimgray") slot_cover();
        if (i != 1) dummy_battery();
    }
    translate([2.4 * pitch, 0, plate_t]) mirror([0, 0, 1]) color("silver") controller_box();
    %translate([-1.6 * pitch, -10, plate_t]) cube([4.2 * pitch, mod_l + 40, 18]); // shelf
}
