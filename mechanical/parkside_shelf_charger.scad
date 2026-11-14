// =====================================================================
//  Parkside X20V under-shelf charging rack: slot module + controller box
//  OpenSCAD 2021.01+   units: mm
//
//  One SLOT MODULE per battery (print 10). Modules are screwed side by
//  side to the underside of the shelf; the battery slides in from the
//  front and hangs from two rails, like on a tool.
//
//  !!! The battery-interface numbers below are PLACEHOLDERS. !!!
//  Measure your own pack with calipers, then print part="gauge" (a 20 mm
//  long slice of the rail profile, ~15 min print) and test-fit it before
//  printing the full modules. See docs/mechanical.md.
//
//  Export:
//    openscad -D 'part="slot"'           -o slot.stl            parkside_shelf_charger.scad
//    openscad -D 'part="slot_lid"'       -o slot_lid.stl        parkside_shelf_charger.scad
//    openscad -D 'part="gauge"'          -o gauge.stl           parkside_shelf_charger.scad
//    openscad -D 'part="controller"'     -o controller.stl      parkside_shelf_charger.scad
//    openscad -D 'part="controller_lid"' -o controller_lid.stl  parkside_shelf_charger.scad
//  part="assembly" shows everything in mounted orientation (not for printing).
//
//  Coordinates (mounted orientation): X = across the shelf, Y = slide
//  direction (0 = front edge, where you insert the battery), Z = up.
//  Z = 0 is the channel ceiling (battery side of the mounting plate); the
//  plate occupies 0..plate_t and its top face touches the shelf.
// =====================================================================

part = "assembly"; // [slot, slot_lid, gauge, controller, controller_lid, assembly, single]

/* [Battery interface: MEASURE YOUR PACK] */
chan_w   = 61.0;  // clear width between the rail walls, above the lips (tongue width + 0.6)
lip_in   = 3.5;   // how far each lip sticks inward (into the battery's side groove)
lip_t    = 3.0;   // lip thickness (groove height minus 0.4 clearance)
lip_gap  = 10.5;  // plate face -> top face of lip (tongue height above the groove + 0.3)
rail_len = 92;    // engaged rail length (front edge -> terminal/end-stop face)
lead_in  = 3;     // chamfer on the lip entry
// latch recess the battery's spring latch snaps into (in the channel ceiling)
latch_y  = 6;     // distance from front edge to the recess
latch_w  = 18;    // across
latch_l  = 9;     // along the slide direction
latch_d  = 4;     // depth into the plate

/* [Battery contacts (male 6.3 x 0.8 mm tabs or 0.8 mm brass)] */
// X positions of the contact tabs, measured from the channel centre line.
// Typical Parkside X20V: B+, (NTC/T), (data), B-  -> verify with a meter!
contact_x   = [-16.5, -5.5, 5.5, 16.5];
contact_z   = 5.5;  // tab centre below the plate face
contact_len = 9;    // how far the tab sticks out of the end-stop into the battery
tab_w       = 6.3;
tab_t       = 0.8;
tab_vertical = true; // blade plane vertical (true) or horizontal (false)

/* [Module frame] */
pitch    = 96;    // module width = slot spacing (battery body ~80 + finger room)
plate_t  = 5;     // mounting plate thickness
wall_t   = 5;     // rail wall thickness
stop_t   = 8;     // end-stop / contact block thickness
bay_l    = 66;    // electronics bay length (behind the end stop)
bay_h    = 34;    // electronics bay height below the plate (must clear the battery body)
bay_wall = 2.4;
screw_d  = 4.5;   // wood screws 4 x 12 (max 3/4 of shelf thickness!)
screw_head_d = 9;

/* [Slot PCB (slides into card guides from the rear)] */
pcb_w = 72;     // across (X); edges ride 0.8 mm deep in the card guides
pcb_l = 60;     // along (Y)
pcb_t = 1.6;
pcb_z = 9;      // PCB bottom face below plate face

/* [Microswitch: Omron D2F-01L / similar, M2 holes 6.5 mm apart] */
sw_x    = -24;  // switch window centre from channel centre
sw_z    = 6;
sw_win  = [9, 4];   // window through the end stop for the lever (X, Z)

/* [Status LED: 5 mm RGB in the front bezel] */
led_d = 5.1;

/* [Controller box] */
ctl_in = [120, 80, 36];   // inner dims (X, Y, Z)
ctl_wall = 2.4;

$fn = 48;
eps = 0.01;

// ---------------- derived ----------------
wall_h   = lip_gap + lip_t;          // rail wall height below the plate
inner_x  = chan_w / 2;               // inner face of a rail wall
outer_x  = inner_x + wall_t;         // outer face
mod_w    = pitch - 1;                // 1 mm gap between neighbours
y_stop   = rail_len;                 // end-stop front face
y_bay0   = rail_len + stop_t;        // start of bay
mod_l    = y_bay0 + bay_l;           // total length
bay_x    = pcb_w / 2 - 0.8;          // bay inner half-width
rear_tab = 15;                       // plate extension behind the bay for the rear screws

module teardrop_y(d, l) {           // horizontal hole along Y, printable without support
    rotate([-90, 0, 0]) linear_extrude(l)
        union() { circle(d = d); rotate(45) square(d / 2); }
}
module hole_z(d, h) { translate([0, 0, -h]) cylinder(d = d, h = h + 2 * eps); }

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

// lead-in chamfer cutter at the front of the lips
module lip_lead_in() {
    for (m = [0, 1]) mirror([m, 0, 0])
        translate([inner_x - lip_in, 0, -wall_h - eps])
            hull() {
                translate([-eps, -eps, 0]) cube([eps, eps, lip_t + 2 * eps]);
                translate([-eps, -eps, 0]) cube([lead_in + eps, eps, lip_t + 2 * eps]);
                translate([-eps, -eps, 0]) cube([eps, lead_in, lip_t + 2 * eps]);
            }
}

// ---------------------------- slot module -----------------------------
module slot_module() {
    col = 7;  // corner columns in the bay that take the lid inserts
    difference() {
        union() {
            // mounting plate (full module width, with a rear screw tab)
            translate([-mod_w / 2, 0, 0]) cube([mod_w, mod_l + rear_tab, plate_t]);
            // rails
            rails(y_stop + eps);
            // end stop / contact block across the channel
            translate([-outer_x, y_stop, -wall_h]) cube([2 * outer_x, stop_t, wall_h + eps]);
            // electronics bay shell
            translate([-bay_x - bay_wall, y_bay0 - eps, -bay_h])
                cube([2 * (bay_x + bay_wall), bay_l + eps, bay_h + eps]);
            // LED bezel at the front, beside the right rail
            translate([outer_x, 0, -12]) cube([10, 10, 12 + eps]);
            // stiffening ribs from rail walls to the plate flange
            for (m = [0, 1]) mirror([m, 0, 0])
                for (y = [rail_len * 0.45, rail_len * 0.8])
                    translate([outer_x - eps, y - 1.5, -wall_h])
                        hull() {
                            cube([eps, 3, wall_h]);
                            translate([7, 0, wall_h - eps]) cube([eps, 3, eps]);
                        }
        }

        // lip lead-in
        lip_lead_in();

        // latch recess in the channel ceiling (rear end chamfered: prints w/o support)
        translate([-latch_w / 2, latch_y, -eps])
            hull() {
                cube([latch_w, latch_l, eps]);
                cube([latch_w, max(latch_l - latch_d, 1), latch_d]);
            }

        // contact tab slots through the end stop
        for (x = contact_x)
            translate([x, y_stop - eps, -contact_z])
                if (tab_vertical) translate([-(tab_t + 0.15) / 2, 0, -(tab_w + 0.3) / 2])
                    cube([tab_t + 0.15, stop_t + 2 * eps, tab_w + 0.3]);
                else translate([-(tab_w + 0.3) / 2, 0, -(tab_t + 0.15) / 2])
                    cube([tab_w + 0.3, stop_t + 2 * eps, tab_t + 0.15]);

        // microswitch lever window + 2x M2 pilot holes (switch screwed to the
        // rear face of the end stop, inside the bay)
        translate([sw_x - sw_win[0] / 2, y_stop - eps, -sw_z - sw_win[1] / 2])
            cube([sw_win[0], stop_t + 2 * eps, sw_win[1]]);
        for (dx = [-3.25, 3.25])
            translate([sw_x + dx, y_stop + 2, -sw_z - 5.5]) teardrop_y(1.8, stop_t);

        // bay cavity, open to the rear; the end stop is its front wall
        difference() {
            translate([-bay_x, y_bay0, -bay_h + bay_wall]) cube([2 * bay_x, bay_l + eps, bay_h - bay_wall]);
            // corner columns for the lid inserts (full length -> no overhangs)
            for (sx = [-1, 1]) for (z = [-col, -bay_h + bay_wall])
                translate([sx > 0 ? bay_x - col : -bay_x, y_bay0, z]) cube([col, bay_l + eps, col]);
        }
        // card guides for the PCB (stop 4 mm short of the end stop)
        for (m = [0, 1]) mirror([m, 0, 0])
            translate([bay_x - eps, y_bay0 + 4, -pcb_z - pcb_t - 0.2])
                cube([1.2, bay_l, pcb_t + 0.4]);

        // rear lid screw holes (M3 heat-set inserts, along Y)
        for (p = bay_lid_holes()) translate([p[0], mod_l - 8 + eps, p[1]]) teardrop_y(4.2, 8.1);

        // mounting screw holes (vertical): 2 in the front flanges, 2 in the rear tab
        for (sx = [-1, 1]) for (y = [22, mod_l + rear_tab / 2 + 1]) {
            x = sx * (mod_w / 2 - 6.5);
            translate([x, y, plate_t + eps]) hole_z(screw_d, plate_t + 3);
            translate([x, y, -40]) cylinder(d = screw_head_d + 1, h = 40);   // head/driver room
        }

        // status LED hole in the front bezel ...
        translate([outer_x + 5, -eps, -6]) teardrop_y(led_d, 10 + 2 * eps);
        // ... wires go up into a groove on the shelf side of the plate and back to the bay
        translate([outer_x + 5 - 1.5, 7, -6]) cube([3, 3, plate_t + 6 + eps]);
        translate([outer_x - 2.5, 7, plate_t - 2]) cube([9.5, 3, 2 + eps]);
        translate([outer_x - 2.5, 7, plate_t - 2]) cube([4, y_bay0 - 7 + 10, 2 + eps]);
        hull() for (x = [outer_x - 2.5, bay_x - col - 6])
            translate([x, y_bay0 + 6, plate_t - 2]) cube([4, 4, 2 + eps]);
        translate([bay_x - col - 6, y_bay0 + 6, -bay_wall]) cube([4, 4, plate_t + bay_wall + eps]);
    }
}
function bay_lid_holes() = [
    [-bay_x + 3.5, -bay_h + bay_wall + 3.5], [bay_x - 3.5, -bay_h + bay_wall + 3.5],
    [-bay_x + 3.5, -3.5], [bay_x - 3.5, -3.5]
];

// Rear lid of the bay: power + I2C cable entries, vents
module slot_lid() {
    lid_t = 2.4;
    w = 2 * (bay_x + bay_wall);
    difference() {
        translate([-w / 2, 0, 0]) cube([w, lid_t, bay_h]);
        for (p = bay_lid_holes())
            translate([p[0], -eps, p[1] + bay_h]) rotate([-90, 0, 0]) cylinder(d = 3.4, h = lid_t + 1);
        // cable entries: 24 V bus (2 x 1.5 mm^2) and 4-wire I2C cable
        translate([-18, -eps, 12]) rotate([-90, 0, 0]) cylinder(d = 9, h = lid_t + 1);
        translate([12, -eps, 12]) rotate([-90, 0, 0]) cylinder(d = 6, h = lid_t + 1);
        // vents
        for (i = [0:5]) translate([-25 + i * 10, -eps, bay_h - 12]) cube([3, lid_t + 1, 8]);
    }
}

// Test print: 20 mm slice of the rail profile incl. lead-in and latch recess
module gauge() {
    intersection() {
        slot_module();
        translate([-outer_x - 1, -1, -wall_h - 1]) cube([2 * outer_x + 2, 21, wall_h + plate_t + 2]);
    }
}

// --------------------------- controller box ---------------------------
// Holds the main board (ESP32-C6 dev board + 2x TCA9548A + relay + DC/DC).
// Screws to the shelf next to the slots. Cable glands on the rear face.
module controller_box() {
    o = ctl_in + [2 * ctl_wall, 2 * ctl_wall, ctl_wall];
    difference() {
        union() {
            translate([-o[0] / 2, 0, 0]) cube(o);
            // mounting flanges
            for (sx = [-1, 1]) translate([sx * (o[0] / 2 + 6) - 6, 0, 0]) cube([12, o[1], 4]);
        }
        translate([-ctl_in[0] / 2, ctl_wall, ctl_wall]) cube(ctl_in + [0, 0, eps]);
        for (sx = [-1, 1]) for (y = [12, o[1] - 12])
            translate([sx * (o[0] / 2 + 6), y, -eps]) cylinder(d = screw_d, h = 5);
        // rear wall: 10 signal cables + 24 V in + 24 V bus out -> two slots with grommet strip
        translate([-50, o[1] - ctl_wall - eps, 8]) cube([100, ctl_wall + 2 * eps, 12]);
        translate([-50, o[1] - ctl_wall - eps, 24]) cube([100, ctl_wall + 2 * eps, 8]);
        // front: USB-C access for the dev board + LED window
        translate([-6, -eps, 10]) cube([12, ctl_wall + 2 * eps, 7]);
        translate([30, -eps, 20]) rotate([-90, 0, 0]) cylinder(d = 5.1, h = ctl_wall + 1);
        // side vents
        for (sx = [-1, 1]) for (i = [0:5])
            translate([sx * (ctl_in[0] / 2) - (sx > 0 ? 0 : ctl_wall) - eps, 15 + i * 10, 10])
                cube([ctl_wall + 2 * eps, 4, 18]);
    }
    // lid screw bosses (M3 inserts)
    for (p = ctl_bosses()) translate([p[0], p[1], ctl_wall - eps])
        difference() { cylinder(d = 8, h = ctl_in[2]); translate([0, 0, ctl_in[2] - 6]) cylinder(d = 4.2, h = 6 + eps); }
    // board standoffs (M3 inserts), 100 x 60 hole pattern
    for (x = [-50, 50]) for (y = [12, 72]) translate([x, y, ctl_wall - eps])
        difference() { cylinder(d = 7, h = 6); translate([0, 0, 1]) cylinder(d = 4.2, h = 5 + eps); }
}
function ctl_bosses() = [
    [-ctl_in[0] / 2 + 3.5, ctl_wall + 3.5], [ctl_in[0] / 2 - 3.5, ctl_wall + 3.5],
    [-ctl_in[0] / 2 + 3.5, ctl_in[1] + ctl_wall - 3.5], [ctl_in[0] / 2 - 3.5, ctl_in[1] + ctl_wall - 3.5]
];
module controller_lid() {
    o = ctl_in + [2 * ctl_wall, 2 * ctl_wall, 0];
    difference() {
        union() {
            translate([-o[0] / 2, 0, 0]) cube([o[0], o[1], 2.4]);
            translate([-ctl_in[0] / 2 + 0.3, ctl_wall + 0.3, 2.4 - eps]) difference() {
                cube([ctl_in[0] - 0.6, ctl_in[1] - 0.6, 3]);
                translate([2, 2, -eps]) cube([ctl_in[0] - 4.6, ctl_in[1] - 4.6, 3 + 2 * eps]);
            }
        }
        for (p = ctl_bosses()) translate([p[0], p[1], -eps]) cylinder(d = 3.4, h = 10);
    }
}

// ------------------------------ output --------------------------------
// Print orientation for the slot module: FRONT FACE ON THE BED (Y -> Z).
// Every layer then contains the complete rail profile, so the load-bearing
// lips are strong and nothing needs support. Use PETG/ASA, 4 walls, 30 % gyroid.

module dummy_battery() {
    color("forestgreen", 0.85) translate([-40, 3, -wall_h - 75]) cube([80, rail_len - 3, 75]);
    color("darkgreen", 0.85) translate([-chan_w / 2 + 0.3, 3, -wall_h + 0.2])
        cube([chan_w - 0.6, rail_len - 3, wall_h - 0.5]);
}

if (part == "slot") rotate([90, 0, 0]) slot_module();
else if (part == "slot_lid") rotate([90, 0, 0]) slot_lid();
else if (part == "gauge") rotate([90, 0, 0]) gauge();
else if (part == "controller") controller_box();
else if (part == "controller_lid") controller_lid();
else if (part == "single") slot_module();
else if (part == "assembly") {
    for (i = [0:2]) translate([(i - 1) * pitch, 0, 0]) {
        color("lightgray") slot_module();
        color("dimgray") translate([0, mod_l, -bay_h]) slot_lid();
        if (i != 1) dummy_battery();
    }
    translate([2 * pitch, 0, plate_t]) mirror([0, 0, 1]) color("silver") controller_box();
    %translate([-1.6 * pitch, -10, plate_t]) cube([4.2 * pitch, mod_l + 40, 18]); // shelf
}
