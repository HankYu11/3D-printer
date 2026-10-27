"""
VERTEX-1 launcher interface -- the GROUND TRUTH boundary of this project.

=========================== READ THIS FIRST ===============================
Every dimension in RAIL_NOMINAL is an UNVERIFIED PLACEHOLDER.

They were chosen to be geometrically plausible for a Beyblade X winder
launcher grip boss and to exercise the generator end to end. They have NOT
been measured off a physical launcher, and they MUST NOT be used to cut a
production part.

Before the first saleable unit ships, somebody has to put calipers on a
real launcher, fill in RAIL_MEASURED, and set RAIL_VERIFIED = True.
Until then build.py prints a banner on every run and the STEP is stamped
PROTOTYPE.

This file is deliberately the ONLY place in the codebase where launcher
geometry appears. Everything downstream consumes `rail()` and never
reasons about the launcher directly. When the real numbers arrive, one
dict changes and every size, rake and preset re-cuts correctly.
===========================================================================
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

# --------------------------------------------------------------------------
# Ground truth
# --------------------------------------------------------------------------
RAIL_VERIFIED = False

RAIL_NOMINAL = {
    # Male dovetail boss on the launcher, which our shoe swallows.
    "boss_width_bottom": 24.0,   # widest point of the launcher dovetail
    "boss_width_top": 19.6,      # narrowest point, at the launcher body
    "boss_height": 5.2,          # vertical extent of the dovetail
    "slide_length": 32.0,        # engagement travel along the launch-axis
    # Our shoe
    "wall": 3.0,                 # material outboard of the dovetail
    "floor": 4.8,                # material below the dovetail
    "stop_thick": 2.0,           # closed end the launcher bottoms against
}

RAIL_MEASURED: dict[str, float] = {}   # <- populate from a physical sample

# Fit control. `fit_clearance` is the value the calibration coupon resolves
# (see cad/calibration/). It is a per-face offset applied to the female
# dovetail: positive makes the pocket larger, i.e. the fit looser.
FIT_CLEARANCE_DEFAULT = 0.15

# Preload features. These are what actually deliver "zero wobble" -- NOT the
# clearance number. Clearance gets the parts together; taper and the leaf
# spring take the slack back out, and they keep working across the +/-0.15 mm
# spread you get between printers, filaments and humidity.
WEDGE_TAPER_DEG = 1.2     # dovetail narrows toward the closed end
LEAF_LIFT = 0.8           # how far the compliant floor leaf stands proud
LEAF_THICK = 1.0
LEAF_LEN = 16.0
LEAF_WIDTH = 8.0

# Tournament Lock: M3 nylon-tipped grub screw in a brass heat-set insert,
# bearing on the dovetail flank through the shoe wall.
LOCK_INSERT_DIA = 4.2
LOCK_INSERT_DEPTH = 6.0


def rail() -> dict[str, float]:
    """Return the launcher geometry in force for this build.

    Measured values win over nominal ones, key by key, so a partial
    measuring session is still useful.
    """
    out = dict(RAIL_NOMINAL)
    out.update(RAIL_MEASURED)
    return out


def provenance() -> str:
    if RAIL_VERIFIED and RAIL_MEASURED:
        return "VERIFIED"
    if RAIL_MEASURED:
        return "PARTIAL"
    return "UNVERIFIED-NOMINAL"


# --------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------
@dataclass
class Shoe:
    """The interface shoe, exploded into build steps.

    The caller assembles as::

        (block + grip + leaf).cut(cutter)

    The dovetail pocket therefore gets cut AFTER the grip has been blended
    in. That ordering is deliberate: it makes it structurally impossible for
    a blend fillet, a neck flare or a future grip revision to intrude into
    the mating geometry. The interface cannot be broken from downstream.
    """
    block: cq.Workplane     # solid outer shoe, no pocket yet
    leaf: cq.Workplane | None   # additive compliant spring; None when skipped
    cutter: cq.Workplane    # pocket + lock bore + above-mating-plane trim
    width: float
    length: float
    height: float
    underside_z: float


def build_shoe(grip_width: float,
               fit_clearance: float = FIT_CLEARANCE_DEFAULT,
               tournament_lock: bool = True,
               leaf: bool = True,
               floor_override: float | None = None) -> Shoe:
    """Build the interface shoe.

    Part frame: origin at the centre of the mating face, +Z toward the
    launcher, +X forward (the direction the blader points), +Y lateral.
    The shoe occupies z in [-height, 0].

    The dovetail is lofted between two trapezoids so the pocket narrows by
    WEDGE_TAPER_DEG toward the closed end. The launcher enters from the aft
    end and wedges solid before it bottoms out, which is what removes
    lateral and rotational play -- the clearance number alone never could.
    """
    r = rail()
    c = fit_clearance

    depth = r["boss_height"] + c
    floor = r["floor"] if floor_override is None else floor_override
    height = depth + floor
    length = r["slide_length"] + r["stop_thick"]
    width = grip_width

    block = (cq.Workplane("XY")
             .box(length, width, height, centered=(True, True, False))
             .translate((0, 0, -height)))

    def trapezoid(scale: float) -> cq.Sketch:
        wb = (r["boss_width_bottom"] + 2 * c) * scale
        wt = (r["boss_width_top"] + 2 * c) * scale
        return (cq.Sketch()
                .polygon([(-wt / 2, 0), (wt / 2, 0),
                          (wb / 2, -depth), (-wb / 2, -depth)]))

    shrink = 1.0 - 2 * math.tan(math.radians(WEDGE_TAPER_DEG)) * \
        r["slide_length"] / r["boss_width_bottom"]

    open_end_x = length / 2
    closed_end_x = -length / 2 + r["stop_thick"]

    pocket = (cq.Workplane("YZ")
              .placeSketch(trapezoid(1.0).moved(cq.Location(cq.Vector(0, 0, open_end_x))),
                           trapezoid(shrink).moved(cq.Location(cq.Vector(0, 0, closed_end_x))))
              .loft())

    # Lead-in flare at the open end so the grip self-aligns when a blader
    # slams it on between matches.
    lead = 1.2
    flare = 1.0 + 2 * lead / r["boss_width_bottom"]
    pocket = pocket.union(
        cq.Workplane("YZ")
        .placeSketch(trapezoid(flare).moved(cq.Location(cq.Vector(0, 0, open_end_x + 0.1))),
                     trapezoid(1.0).moved(cq.Location(cq.Vector(0, 0, open_end_x - lead))))
        .loft())

    # Relief that turns the pocket floor into a cantilever root. Skipped
    # with leaf=False: the fit gauge does not measure preload, and the
    # relief is the one feature on this part that forces support.
    cutter = pocket
    if leaf:
        relief = (cq.Workplane("XY")
                  .box(LEAF_LEN + 2.0, LEAF_WIDTH + 2.0, LEAF_LIFT + 0.6,
                       centered=(True, True, False))
                  .translate((0, 0, -depth - 0.3)))
        cutter = cutter.union(relief)

    # Trim anything that tries to rise above the mating plane.
    cutter = cutter.union(
        cq.Workplane("XY").box(length + 60, width + 60, 40,
                               centered=(True, True, False)))

    if tournament_lock:
        cutter = cutter.union(
            cq.Workplane("XZ")
            .circle(LOCK_INSERT_DIA / 2)
            .extrude(LOCK_INSERT_DEPTH)
            .translate((0, -width / 2, -depth / 2 - 0.4)))

    # --- compliant floor leaf ---------------------------------------------
    # A printed cantilever in the pocket floor. The launcher squashes it and
    # it pushes the boss up into the dovetail flanks, taking out vertical
    # slack whatever the clearance did. Printed on its side (docs/04) the
    # leaf's bending stress runs in-plane, so it flexes for thousands of
    # cycles instead of snapping along a layer boundary.
    if leaf:
        leaf_solid = (cq.Workplane("XY")
                      .box(LEAF_LEN, LEAF_WIDTH, LEAF_THICK,
                           centered=(True, True, False))
                      .translate((0, 0, -depth + LEAF_LIFT)))
        leaf_solid = leaf_solid.union(
            cq.Workplane("XY")
            .box(3.0, LEAF_WIDTH, LEAF_LIFT + 0.9, centered=(True, True, False))
            .translate((-LEAF_LEN / 2 - 1.5, 0, -depth - 0.3)))
    else:
        leaf_solid = None

    return Shoe(block=block, leaf=leaf_solid, cutter=cutter, width=width,
                length=length, height=height, underside_z=-height)
