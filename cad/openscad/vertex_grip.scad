// =====================================================================
// VERTEX-1 launcher grip -- OpenSCAD reference implementation
// =====================================================================
//
// A dependency-free port of the CadQuery generator in ../vertex/.
//
// WHICH ONE IS AUTHORITATIVE
//   The CadQuery model is. It exports STEP (B-Rep, editable downstream),
//   computes real mass properties, and is what the build pipeline runs.
//   This file exists so that anyone with nothing but OpenSCAD installed
//   can open, read, tweak and print the design -- the whole competitive
//   modding scene lives on OpenSCAD and Thingiverse-style customisers,
//   and shutting them out to save a file would be a bad trade.
//
// WHAT IS DIFFERENT
//   OpenSCAD has no loft. The stem is built as hull() between adjacent
//   cross-sections, which is a piecewise-linear approximation of the
//   CadQuery B-spline loft: visually and ergonomically equivalent,
//   geometrically not identical. Do not mix a shoe from one and a stem
//   from the other.
//
// STATUS: NOT EXECUTED. OpenSCAD could not be installed in the
// environment this was authored in, so unlike the CadQuery model -- which
// was built, measured and rendered -- this port has never been run.
// Render it and compare against out/adult_mid_PROTOTYPE.stl before
// trusting it. Treat it as a reviewed transcription, not a tested build.
//
// INTERFACE GEOMETRY IS UNVERIFIED PLACEHOLDER DATA -- see
// ../vertex/interface.py. Calibrate before printing anything you intend
// to put on a real launcher.
// =====================================================================

/* [Fit] */
hand_breadth = 90;      // [80:1:100] palm width across the knuckles
rake_deg     = 18;      // [10:1:32]  grip rake aft of the launch axis

/* [Identity] */
player_id    = "VORTEX-07";
texture      = "knurl"; // [knurl, ribs, none]

/* [Ballast] */
ballast_nuts = 3;       // [0:1:6] M8 hex nuts carried in the butt

/* [Interface -- GROUND TRUTH, calibrate before printing] */
boss_width_bottom = 24.0;
boss_width_top    = 19.6;
boss_height       = 5.2;
slide_length      = 32.0;
fit_clearance     = 0.15;   // set from the printed fit gauge
shoe_wall         = 3.0;
shoe_floor        = 4.8;
stop_thick        = 2.0;

/* [Hidden] */
$fn = 48;
EPS = 0.01;

// ---------------------------------------------------------------------
// Derived -- these mirror params.py exactly. Change them there first.
// ---------------------------------------------------------------------
grip_width   = 30.0;                                 // constant by design
grip_depth   = 40.0 + 0.45 * (hand_breadth - 80);
corner_r     = 9.0  + 0.05 * (hand_breadth - 80);
finger_pitch = 0.205 * hand_breadth;
grip_length  = 4 * finger_pitch + 16;
neck_offset_x = -6.0;
tang_zone    = 16.0;

pocket_depth = boss_height + fit_clearance;
shoe_height  = pocket_depth + shoe_floor;
shoe_length  = slide_length + stop_thick;

// Profile stations: [u, w_scale, d_scale, r_scale, x_off]
// u = 0 at the neck, 1 at the butt face. Same table as grip.py PROFILE.
PROFILE = [
  [0.00, 1.000, 0.780, 0.80,  0.0],
  [0.06, 1.000, 0.860, 0.90,  0.6],
  [0.20, 1.000, 0.970, 1.00,  1.2],
  [0.40, 1.000, 1.000, 1.00,  1.0],
  [0.62, 1.000, 0.960, 1.00,  0.0],
  [0.82, 0.987, 0.880, 0.95, -1.4],
  [0.94, 1.013, 0.900, 0.90, -2.6],
  [1.00, 0.947, 0.840, 0.80, -3.2],
];

function st_w(i) = grip_width * PROFILE[i][1];
function st_d(i) = grip_depth * PROFILE[i][2];
function st_r(i) = min(corner_r * PROFILE[i][3],
                       min(st_w(i), st_d(i)) / 2 - 0.1);
function st_x(i) = PROFILE[i][4];
function st_z(i) = grip_length * (1 - PROFILE[i][0]);

// Linear interpolation of the fore-aft depth / offset at arbitrary u,
// used to seat the finger cuts on the real frontstrap surface.
function seg(u) = let (n = len(PROFILE) - 1)
    [for (i = [0:n-1]) if (PROFILE[i][0] <= u && u <= PROFILE[i+1][0]) i][0];
function lerp(a, b, t) = a + (b - a) * t;
function tt(u) = let (i = seg(u))
    (u - PROFILE[i][0]) / (PROFILE[i+1][0] - PROFILE[i][0]);
function depth_at(u) = let (i = seg(u))
    grip_depth * lerp(PROFILE[i][2], PROFILE[i+1][2], tt(u));
function xoff_at(u)  = let (i = seg(u))
    lerp(PROFILE[i][4], PROFILE[i+1][4], tt(u));
function front_x(u)  = xoff_at(u) + depth_at(u) / 2;
function back_x(u)   = xoff_at(u) - depth_at(u) / 2;
function u_at_z(z)   = max(0, min(1, (grip_length - z) / grip_length));

// ---------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------
// Rounded rectangle: fore-aft depth on X, lateral width on Y. Getting
// these the wrong way round silently builds the grip rotated 90 degrees
// about its own axis -- it still renders, and every surface-referenced
// cut then misses.
module rrect(d, w, r, h = EPS) {
  linear_extrude(height = h)
    offset(r = r) square([d - 2 * r, w - 2 * r], center = true);
}

module stem() {
  for (i = [0 : len(PROFILE) - 2])
    hull() {
      translate([st_x(i),   0, st_z(i)])   rrect(st_d(i),   st_w(i),   st_r(i));
      translate([st_x(i+1), 0, st_z(i+1)]) rrect(st_d(i+1), st_w(i+1), st_r(i+1));
    }
  // Carry the neck up into the shoe so the union has material to blend.
  hull() {
    translate([st_x(0), 0, st_z(0)])           rrect(st_d(0), st_w(0), st_r(0));
    translate([st_x(0), 0, grip_length + 7])   rrect(st_d(0), st_w(0), st_r(0));
  }
}

// Index scallop + three finger grooves. The cutter centre sits OUTSIDE
// the frontstrap so exactly `depth` of it is buried.
module finger_registers() {
  specs = [
    [grip_length - tang_zone - 0.5 * finger_pitch, 12.0, 2.2],
    [grip_length - tang_zone - 1.5 * finger_pitch,  9.0, 1.5],
    [grip_length - tang_zone - 2.5 * finger_pitch,  9.0, 1.5],
    [grip_length - tang_zone - 3.5 * finger_pitch,  9.0, 1.5],
  ];
  for (s = specs)
    translate([front_x(u_at_z(s[0])) + s[1] - s[2], 0, s[0]])
      rotate([90, 0, 0])
        cylinder(h = grip_width + 12, r = s[1], center = true);
}

module texture_grooves() {
  if (texture != "none") {
    r = 1.1; pitch = 4.2; depth = 0.75; ang = 35;
    angles = (texture == "knurl") ? [ang, -ang] : [0];
    over = (grip_width / 2 + 6) * tan(ang);
    span = (grip_width + 14) / cos(ang);
    n = floor((grip_length + 2 * over + 2 * pitch) / pitch);
    for (a = angles)
      for (i = [0 : n]) {
        z = -over - pitch + i * pitch;
        u = u_at_z(z);
        for (sx = [[front_x(u), 1], [back_x(u), -1]])
          translate([sx[0] + sx[1] * (r - depth), 0, z])
            rotate([90 - a, 0, 0])
              cylinder(h = span, r = r, center = true);
      }
  }
}

// Hex socket for M8 ballast nuts. Oriented FLATS-to-cheeks so that, when
// the part is printed lying on a cheek, the socket roof is a flat ~7.7 mm
// bridge approached by 60 degree walls: self-supporting, and no internal
// support to dig out of a blind pocket.
module ballast_bay() {
  af = 13.0 + 0.35;
  // cylinder($fn=6) places vertices at 0/60/120... so the flats already
  // sit normal to Y, matching CadQuery's polygon(). Do NOT add a 30 deg
  // rotation "to line the flats up" -- that turns them corner-to-cheek and
  // the socket roof stops being a flat bridge.
  translate([-5, 0, -0.1])
    cylinder(h = 46, r = af / sqrt(3), $fn = 6);
  translate([11, 0, -0.1]) cylinder(h = 6, r = 4.2 / 2);
}

module cheek_panels() {
  panel_recess = 0.8; panel_len = 56; panel_w = 24;
  z_mid = grip_length * 0.46;
  for (s = [1, -1])
    translate([0, s * (grip_width / 2 + 1 - panel_recess / 2), z_mid])
      cube([panel_w, panel_recess + 2, panel_len], center = true);

  // Player ID. rotate([90,0,0]) lays the glyphs in the XZ plane extruding
  // along -Y; rotate([0,90,0]) then turns the baseline down the grip axis
  // so a long tag runs along the 56 mm panel instead of off the 24 mm
  // width. The extrusion is NOT symmetric about y = 0, so each cheek gets
  // its own translation -- a mirrored sign puts the far copy outside the
  // part, where it cuts nothing and fails silently.
  text_depth = 0.6; over = 1.0;
  D = text_depth + over;
  surface = grip_width / 2 - panel_recess;
  if (len(player_id) > 0)
    for (s = [1, -1])
      translate([0, s > 0 ? surface - text_depth + D
                          : -(surface - text_depth), z_mid])
        mirror([s > 0 ? 1 : 0, 0, 0])      // read correctly from either side
          rotate([0, 90, 0]) rotate([90, 0, 0])
            linear_extrude(height = D)
              text(player_id, size = 8, halign = "center", valign = "center",
                   font = "DejaVu Sans");
}

module grip_local() {
  difference() {
    stem();
    finger_registers();
    texture_grooves();
    ballast_bay();
    cheek_panels();
  }
}

// ---------------------------------------------------------------------
// Interface shoe
// ---------------------------------------------------------------------
module dovetail_pocket(extra = 0) {
  c = fit_clearance + extra;
  wb = boss_width_bottom + 2 * c;
  wt = boss_width_top + 2 * c;
  // Trapezoid swept along X: narrow at the opening, wide at the floor, so
  // the launcher cannot lift straight out. rotate([0,90,0]) maps the
  // sketch's local +X onto global -Z, so the first polygon edge is the
  // OPENING at z = 0 and must carry the narrow width.
  rotate([0, 90, 0])
    linear_extrude(height = shoe_length + 2, center = true)
      polygon([[0, -wt/2], [0, wt/2],
               [pocket_depth, wb/2], [pocket_depth, -wb/2]]);
}

// OpenSCAD's cube() centres on all three axes or none, so the block is
// placed by an explicit translate rather than center=.
module shoe_block() {
  translate([-shoe_length/2, -grip_width/2, -shoe_height])
    cube([shoe_length, grip_width, shoe_height]);
}

// Lofted collar from the shoe footprint down onto the stem, used instead
// of a fillet: deterministic, and it cannot fail the way a fillet can.
module blend_collar(collar_len = 15) {
  u = collar_len / grip_length;
  hull() {
    translate([0, 0, -shoe_height + 1.5])
      rrect(shoe_length, grip_width, 5.0);
    translate([neck_offset_x, 0, -shoe_height])
      rotate([0, rake_deg, 0])
        translate([xoff_at(u), 0, -collar_len])
          rrect(depth_at(u), grip_width, corner_r * 0.9);
  }
}

// ---------------------------------------------------------------------
// Assembly. The dovetail pocket is cut LAST so that neither the stem nor
// the blend collar can ever intrude into the mating geometry.
// ---------------------------------------------------------------------
module vertex_grip() {
  difference() {
    union() {
      shoe_block();
      blend_collar();
      translate([neck_offset_x, 0, -shoe_height])
        rotate([0, rake_deg, 0])
          translate([0, 0, -grip_length])
            grip_local();
    }
    dovetail_pocket();
    // Trim anything that rises above the mating plane.
    translate([0, 0, 20]) cube([200, 200, 40], center = true);
  }
}

vertex_grip();
