"""
VERTEX-1 grip body.

Built in a LOCAL frame whose +Z runs from the butt face (z = 0) up to the
neck (z = grip_length), then raked aft and hung off the underside of the
interface shoe.

The cross-section everywhere is a rounded rectangle of CONSTANT lateral
width and varying fore-aft depth. That is a load-path and DFM decision
before it is a styling one, and it buys three things at once:

  * flat parallel cheeks print support-free when the part lies on a cheek,
    which is also the orientation that puts the neck's bending stress
    in-plane instead of across layer boundaries (docs/04);
  * all ergonomic volume moves to the front and back strap, which is where
    a power grip actually wants it (1911 / Glock practice);
  * the cheeks become a flat uninterrupted canvas for the customisation
    panel -- the DFM constraint and the branding surface are the same face.
"""

from __future__ import annotations

import math
from typing import NamedTuple

import cadquery as cq

from .params import Params


class Station(NamedTuple):
    """One lofted cross-section along the local grip axis."""
    u: float        # 0.0 at the neck, 1.0 at the butt face
    w_scale: float  # lateral width, fraction of params.grip_width
    d_scale: float  # fore-aft depth, fraction of params.grip_depth
    r_scale: float  # corner radius, fraction of params.corner_r
    x_off: float    # section centre, fore(+)/aft(-) of the local grip axis


# The profile that makes it a grip rather than a stick. Girth peaks under
# the middle finger, tapers through ring and little finger, then flares at
# the butt so the hand cannot slide off under a snap load.
PROFILE: list[Station] = [
    Station(0.00, 1.000, 0.780, 0.80,  0.0),   # neck pad, under the shoe
    Station(0.06, 1.000, 0.860, 0.90,  0.6),   # tang zone
    Station(0.20, 1.000, 0.970, 1.00,  1.2),   # index register
    Station(0.40, 1.000, 1.000, 1.00,  1.0),   # middle finger - palm swell
    Station(0.62, 1.000, 0.960, 1.00,  0.0),   # ring finger
    Station(0.82, 0.987, 0.880, 0.95, -1.4),   # little finger
    Station(0.94, 1.013, 0.900, 0.90, -2.6),   # butt flare
    Station(1.00, 0.947, 0.840, 0.80, -3.2),   # butt face
]

TANG_ZONE = 12.0   # mm of grip above the index finger, reserved for the web


def _section(p: Params, st: Station) -> cq.Sketch:
    w = p.grip_width * st.w_scale
    d = p.grip_depth * st.d_scale
    r = min(p.corner_r * st.r_scale, min(w, d) / 2 - 0.1)
    # rect(X, Y): fore-aft depth on X, lateral width on Y. Getting these the
    # wrong way round builds the whole grip rotated 90 deg about its own
    # axis, which still lofts and still reports a plausible volume -- every
    # surface-referenced cutter downstream then quietly misses.
    return cq.Sketch().rect(d, w).reset().vertices().fillet(r)


def _interp(p: Params, u: float) -> tuple[float, float, float]:
    """Linearly interpolate (width, depth, x_offset) at local parameter u."""
    pts = PROFILE
    u = max(pts[0].u, min(pts[-1].u, u))
    a, b, t = pts[0], pts[0], 0.0
    for lo, hi in zip(pts, pts[1:]):
        if lo.u <= u <= hi.u:
            a, b = lo, hi
            t = 0.0 if hi.u == lo.u else (u - lo.u) / (hi.u - lo.u)
            break

    def lerp(x: float, y: float) -> float:
        return x + (y - x) * t

    return (p.grip_width * lerp(a.w_scale, b.w_scale),
            p.grip_depth * lerp(a.d_scale, b.d_scale),
            p.corner_r * lerp(a.r_scale, b.r_scale),
            lerp(a.x_off, b.x_off))


def frontstrap_x(p: Params, u: float) -> float:
    """Local X of the frontstrap surface at u. Seats the finger cuts."""
    _, d, _, xo = _interp(p, u)
    return xo + d / 2


def backstrap_x(p: Params, u: float) -> float:
    _, d, _, xo = _interp(p, u)
    return xo - d / 2


def _u_at_z(p: Params, z: float) -> float:
    return max(0.0, min(1.0, (p.grip_length - z) / p.grip_length))


# --------------------------------------------------------------------------
def stem(p: Params, neck_overlap: float) -> cq.Workplane:
    """Loft the bare grip stem, butt (z=0) up to neck + overlap.

    `neck_overlap` buries the stem inside the shoe so the union has real
    material to blend through, instead of a knife-edge tangency that OCCT
    would refuse to fillet. Sections must be handed to loft() in ascending
    z or the resulting solid comes out inside-out (negative volume).
    """
    L = p.grip_length
    sketches = []
    for st in reversed(PROFILE):              # u = 1 -> 0, so z = 0 -> L
        z = L * (1.0 - st.u)
        sketches.append(_section(p, st).moved(cq.Location(cq.Vector(st.x_off, 0, z))))
    top = PROFILE[0]
    sketches.append(_section(p, top).moved(
        cq.Location(cq.Vector(top.x_off, 0, L + neck_overlap))))
    return cq.Workplane("XY").placeSketch(*sketches).loft()


def finger_registers(p: Params) -> cq.Workplane:
    """Index scallop plus three finger grooves, cut into the frontstrap.

    Depths are deliberately shallow. Deep grooves lock a hand into exactly
    one position and fight anyone whose fingers sit a few millimetres off
    the model; these register the hand without trapping it, which is what
    turns into launch-to-launch repeatability rather than a hot spot.
    """
    L = p.grip_length
    specs = [(L - TANG_ZONE - 0.5 * p.finger_pitch,
              p.index_scallop_r, p.index_scallop_depth)]
    for k in range(1, 4):
        specs.append((L - TANG_ZONE - (0.5 + k) * p.finger_pitch,
                      p.finger_groove_r, p.finger_groove_depth))

    solids = []
    for z, r, depth in specs:
        # Centre the cutter outside the frontstrap so exactly `depth` of it
        # is buried: surface + r - depth, not surface - r + depth.
        xc = frontstrap_x(p, _u_at_z(p, z)) + r - depth
        span = p.grip_width + 12
        solids.append(cq.Solid.makeCylinder(
            r, span, cq.Vector(xc, -span / 2, z), cq.Vector(0, 1, 0)))
    return cq.Workplane(obj=cq.Compound.makeCompound(solids))


def ballast_bay(p: Params) -> cq.Workplane:
    """Hex socket for M8 ballast nuts, plus the butt-cap insert bore.

    cq.Workplane.polygon() already orients a hexagon with its FLATS normal
    to Y, which is exactly what is wanted: printed on its side the socket's
    roof becomes a flat ~7.7 mm bridge approached by 60 deg walls. Self
    supporting, so there is no internal support to dig out of a blind
    pocket with a screwdriver.
    """
    across_corners = 2 * (p.ballast_af + p.ballast_clear) / math.sqrt(3)
    hexa = (cq.Workplane("XY")
            .polygon(6, across_corners)
            .extrude(p.ballast_depth)
            .translate((p.ballast_offset_x, 0, -0.1)))
    insert = (cq.Workplane("XY")
              .circle(p.cap_insert_dia / 2)
              .extrude(p.cap_insert_depth)
              .translate((p.cap_screw_offset_x, 0, -0.1)))
    return hexa.union(insert)


def cheek_panels(p: Params) -> tuple[cq.Workplane, cq.Workplane | None]:
    """Recess + debossed Player ID on both cheeks.

    The glyphs are mirrored for the far cheek so the tag reads correctly
    from either side rather than appearing reversed on one of them.
    """
    z_mid = p.grip_length * 0.46
    half = p.grip_width / 2
    over = 2.0                       # cutter overshoot past the surface

    recess = None
    for sign in (1, -1):
        box = (cq.Workplane("XY")
               .box(p.panel_width, p.panel_recess + over, p.panel_len)
               .translate((0, sign * (half + over / 2 - p.panel_recess / 2), z_mid)))
        recess = box if recess is None else recess.union(box)

    text = None
    tag = p.player_id.strip()
    if tag:
        # Workplane("XZ").text() lies in the XZ plane and always extrudes
        # along -Y, occupying y in [-D, 0] whichever cheek it is destined
        # for. It is NOT symmetric about y = 0, so the two cheeks need
        # different translations -- a mirrored sign puts the far copy
        # entirely outside the part, where it cuts nothing and fails
        # silently.
        depth = p.text_depth + over
        surface = half - p.panel_recess          # floor of the recessed panel

        # The tag runs ALONG the grip axis. text() lays glyphs out on the
        # plane's X, which here is the 24 mm fore-aft width; a nine
        # character gamer tag is about 45 mm long and would hang off both
        # edges. Rotating it into Z puts it down the 56 mm length instead.
        #
        # Customers type whatever they like, so the size is auto-fitted to
        # the panel rather than trusted. An order must never silently
        # produce a tag running off the side of the part.
        size = p.text_size
        for _ in range(8):
            probe = cq.Workplane("XZ").text(
                tag, size, depth, combine=False, font=p.text_font)
            bb = probe.val().BoundingBox()
            if bb.xlen <= p.panel_len - 6 and bb.zlen <= p.panel_width - 6:
                break
            size *= 0.88

        glyphs = []
        for sign in (1, -1):
            t = cq.Workplane("XZ").text(
                tag, size, depth, combine=False, font=p.text_font)
            t = t.rotate((0, 0, 0), (0, 1, 0), 90)    # baseline X -> -Z
            if sign > 0:
                # Mirror in X so the tag reads correctly from the +Y side
                # too: between the two viewpoints it is the X axis that
                # flips, whichever way the baseline runs.
                t = t.mirror("YZ")
                y = surface - p.text_depth + depth    # -> [surface-d, ...]
            else:
                y = -(surface - p.text_depth)         # -> [..., -surface+d]
            glyphs.extend(t.translate((0, y, z_mid)).solids().vals())
        text = cq.Workplane(obj=cq.Compound.makeCompound(glyphs))

    return recess, text


def texture(p: Params) -> list[cq.Workplane]:
    """Grip texture, returned as cutters to apply in sequence.

    Two crossed sets of shallow rounded grooves on the front and back strap.
    Each set is a non-overlapping Compound so it can be cut in a single
    boolean -- a few dozen operations rather than the few thousand a field
    of discrete pyramids would need, which matters when the pipeline
    regenerates geometry per order.

    Fine stipple is deliberately NOT modelled here. Below roughly 0.8 mm the
    slicer's fuzzy-skin modifier produces a better surface than B-Rep
    booleans do, for none of the build cost (docs/04).
    """
    if p.texture == "none":
        return []

    L = p.grip_length
    r = 1.1
    pitch = p.knurl_pitch
    span = (p.grip_width + 14) / math.cos(math.radians(p.knurl_angle_deg))
    angles = ([p.knurl_angle_deg, -p.knurl_angle_deg]
              if p.texture == "knurl" else [0.0])

    overhang = (p.grip_width / 2 + 6) * math.tan(
        math.radians(max(abs(a) for a in angles))) if angles else 0.0
    z0, z1 = -overhang - pitch, L + overhang + pitch

    cutters = []
    for ang in angles:
        a = math.radians(ang)
        direction = cq.Vector(0, math.cos(a), math.sin(a))
        solids = []
        n = int((z1 - z0) / pitch) + 1
        for i in range(n):
            z = z0 + i * pitch
            u = _u_at_z(p, z)
            for strap_x, outward in ((frontstrap_x(p, u), +1.0),
                                     (backstrap_x(p, u), -1.0)):
                xc = strap_x + outward * (r - p.knurl_depth)
                start = cq.Vector(xc, 0, z) - direction.multiply(span / 2)
                solids.append(cq.Solid.makeCylinder(r, span, start, direction))
        cutters.append(cq.Workplane(obj=cq.Compound.makeCompound(solids)))
    return cutters


def _cut_all(wp: cq.Workplane, cutter: cq.Workplane) -> cq.Workplane:
    """Subtract every solid in `cutter`.

    Workplane.cut() handed a Workplane wrapping a Compound returns the base
    UNCHANGED and reports no error, so a missing cut looks exactly like a
    successful one. Shape.cut(*solids) is the call that actually subtracts.
    """
    solids = cutter.solids().vals()
    if not solids:
        return wp
    return cq.Workplane(obj=wp.val().cut(*solids))


def build_grip_local(p: Params, neck_overlap: float) -> cq.Workplane:
    """Assemble every local-frame feature into the finished grip stem.

    Every boolean passes clean=False. CadQuery cleans by default, and
    clean() merges coplanar faces -- on a solid carrying this many lofted
    and textured faces that search does not terminate in any useful time
    (measured: every boolean here is sub-second, a single default-clean cut
    ran for minutes without returning). The solids come out valid and
    watertight without it; the only cost is a slightly more fragmented face
    list in the STEP, which no downstream consumer here cares about.
    """
    g = stem(p, neck_overlap)
    for cutter in texture(p):
        g = _cut_all(g, cutter)
    g = _cut_all(g, finger_registers(p))
    g = g.cut(ballast_bay(p), clean=False)

    recess, text = cheek_panels(p)
    g = g.cut(recess, clean=False)
    if text is not None:
        g = _cut_all(g, text)
    return g


def blend_collar(p: Params, neck_z: float, shoe_length: float,
                 collar_len: float = 15.0) -> cq.Workplane:
    """A lofted flare from the shoe footprint down onto the grip stem.

    This replaces a fillet at the neck, deliberately.

    OCCT's fillet is the least predictable operation in the stack and it
    gets worse as the surfaces it blends get more organic. Measured on this
    part it fails at every radius from 6.0 mm down to 1.5 mm, because the
    edge band at the neck picks up texture grooves and dovetail edges along
    with the junction itself. A fillet that fails on some fraction of orders
    is a pipeline outage, not a cosmetic issue.

    A lofted collar is deterministic, runs in milliseconds, and gives
    explicit control of the blend profile instead of whatever radius OCCT
    happens to accept. It is unioned BEFORE the shoe cutter runs, so it can
    never intrude into the dovetail.
    """
    rake = math.radians(p.rake_deg)
    L = p.grip_length
    u = collar_len / L
    w, d, r, xo = _interp(p, u)
    r = min(r, min(w, d) / 2 - 0.1)

    lower = cq.Sketch().rect(d, w).reset().vertices().fillet(r)
    pos = cq.Vector(
        xo * math.cos(rake) - collar_len * math.sin(rake) + p.neck_offset_x,
        0.0,
        -xo * math.sin(rake) - collar_len * math.cos(rake) + neck_z)
    lower = lower.moved(cq.Location(pos, cq.Vector(0, 1, 0), p.rake_deg))

    upper = (cq.Sketch()
             .rect(shoe_length, p.grip_width).reset().vertices().fillet(5.0)
             .moved(cq.Location(cq.Vector(0, 0, neck_z + 1.5))))

    return cq.Workplane("XY").placeSketch(lower, upper).loft()


def recoil_shelf(p: Params, neck_z: float, shoe_length: float) -> cq.Workplane:
    """The forward ledge the index finger hooks under.

    Built in the PART frame, not the grip frame: it answers to the launcher
    and the shoe, not to the rake. Without it the blend collar just ramps
    smoothly from the shoe down to the stem and there is nothing for the
    index finger to pull against, so the whole downward and forward recoil
    has to be carried by grip friction -- which is exactly what fails on a
    violent pull and what makes launch angle drift between launches.

    Lofted from a full-height root to a thinner, slightly raised lip. The
    taper keeps the underside self-supporting and angles the bearing face
    up by `shelf_rise_deg`, so the reaction pushes the hand INTO the grip
    rather than letting it slide forward off the shelf.
    """
    x0 = shoe_length / 2 - p.shelf_root_inset
    x1 = shoe_length / 2 + p.shelf_depth
    rise = math.tan(math.radians(p.shelf_rise_deg)) * (x1 - x0)

    def sect(w: float, h: float, r: float, zc: float, x: float) -> cq.Sketch:
        # On a YZ workplane the sketch's local axes are (global Y, global Z)
        # and its placement axis is global X.
        return (cq.Sketch().rect(w, h).reset().vertices().fillet(r)
                .moved(cq.Location(cq.Vector(0, zc, x))))

    root_z = neck_z - p.shelf_thick / 2
    tip_h = p.shelf_thick * 0.60
    tip_z = neck_z - tip_h / 2 + rise * 0.5

    return (cq.Workplane("YZ")
            .placeSketch(sect(p.grip_width, p.shelf_thick, 2.5, root_z, x0),
                         sect(p.grip_width * 0.90, tip_h, 1.6, tip_z, x1))
            .loft())


def place(grip_local: cq.Workplane, p: Params, neck_z: float) -> cq.Workplane:
    """Rake the grip aft and hang it from the shoe underside.

    Rotating (0,0,1) about +Y by +rake maps the local grip axis onto
    (sin rake, 0, cos rake): butt-to-neck runs forward and up, so the butt
    ends up aft and low. That is the rake sign convention for the project.
    """
    L = p.grip_length
    rake = math.radians(p.rake_deg)
    rotated = grip_local.rotate((0, 0, 0), (0, 1, 0), p.rake_deg)
    return rotated.translate((p.neck_offset_x - L * math.sin(rake), 0,
                              neck_z - L * math.cos(rake)))
