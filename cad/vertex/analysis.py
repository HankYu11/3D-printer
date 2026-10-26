"""
VERTEX-1 physical analysis.

Pure Python. No CAD dependency, so the order validator, the configurator's
fit preview and CI can all run it without pulling in OCCT.

Everything here is first-order. It is good enough to size the product, rank
options and catch nonsense before a printer is tied up for two hours. It is
NOT a substitute for the slicer (print time, material) or for strain-gauging
a real launch (loads).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .params import Params

G = 9.80665          # m/s^2
STEEL_DENSITY = 7.85e-3   # g/mm^3

# --------------------------------------------------------------------------
# Ballast hardware -- DIN 934 hex nuts
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Nut:
    name: str
    across_flats: float   # mm
    thickness: float      # mm
    thread_dia: float     # mm, nominal major

    @property
    def mass(self) -> float:
        """Mass in grams, from the hexagonal prism less the thread bore.

        The bore is taken at ~0.88 x major diameter, which approximates the
        mean of the major and minor thread diameters. Checked against
        published DIN 934 masses: M8 lands at 5.6 g (published 5.1-5.6 g),
        M10 at 12.0 g (published 11.0-12.5 g).
        """
        hex_area = math.sqrt(3) / 2 * self.across_flats ** 2
        bore_area = math.pi / 4 * (0.88 * self.thread_dia) ** 2
        return (hex_area - bore_area) * self.thickness * STEEL_DENSITY


NUTS = {
    "M8": Nut("M8", across_flats=13.0, thickness=6.8, thread_dia=8.0),
    "M10": Nut("M10", across_flats=17.0, thickness=8.4, thread_dia=10.0),
}


# --------------------------------------------------------------------------
# Printed mass and time
# --------------------------------------------------------------------------
@dataclass
class PrintEstimate:
    solid_volume: float      # mm^3, the CAD solid
    material_volume: float   # mm^3, what the nozzle actually lays down
    mass: float              # g
    hours: float
    effective_density: float # material / solid


def estimate_print(p: Params, solid_volume: float, surface_area: float,
                   density_override: float | None = None) -> PrintEstimate:
    """First-order shelled-part material and time estimate.

    Models the part as a shell of `p.shell_thick` over its whole surface
    with `p.infill_fraction` inside.

    Time comes from the machine profile rather than one magic throughput
    figure, because the honest answer differs by about 3x across machines
    that all print this file. A 0.4 mm nozzle at 0.2 mm and 70 mm/s lays
    down 0.42 x 0.2 x 70 = 5.9 mm^3/s before any overhead; a 0.6 mm nozzle
    at 0.3 mm moves 13.2 mm^3/s and runs into the hotend's flow ceiling
    instead. Quoting a single number hides exactly the decision a user
    making this on a library printer needs to make.

    The slicer is still authoritative. This exists to reject an impossible
    order before it ties up a printer for two hours.
    """
    shell = min(surface_area * p.shell_thick, solid_volume)
    interior = max(solid_volume - shell, 0.0)
    material = shell + interior * p.infill_fraction

    density = density_override if density_override is not None else p.density

    line_width = p.nozzle_dia * 1.05
    deposition = line_width * p.layer_height * p.print_speed
    effective = min(deposition, p.max_flow) * p.duty_cycle

    return PrintEstimate(
        solid_volume=solid_volume,
        material_volume=material,
        mass=material * density / 1000.0,
        hours=material / effective / 3600.0,
        effective_density=material / solid_volume if solid_volume else 0.0,
    )


# --------------------------------------------------------------------------
# Balance
# --------------------------------------------------------------------------
# Launcher mass properties. UNVERIFIED -- weigh a real unit and find its
# balance point before quoting any of this to a customer.
LAUNCHER_MASS_G = 75.0
LAUNCHER_COG = (5.0, 0.0, 35.0)      # part frame, mm
LAUNCHER_PROPS_VERIFIED = False

WRIST_OFFSET = 20.0   # mm beyond the butt face, along the grip axis


@dataclass
class Balance:
    cog: tuple[float, float, float]
    hand: tuple[float, float, float]
    wrist: tuple[float, float, float]
    total_mass: float        # g
    ballast_mass: float      # g
    overhang: float          # mm of CoG above the hand, along the grip axis
    cog_height: float        # mm, part-frame z
    holding_moment: float    # N.mm about the wrist
    inertia: float           # kg.m^2 about the wrist


def _axis(p: Params) -> tuple[float, float, float]:
    """Unit vector from neck toward butt: aft and down."""
    rake = math.radians(p.rake_deg)
    return (-math.sin(rake), 0.0, -math.cos(rake))


def balance(p: Params, grip_mass_g: float,
            grip_cog: tuple[float, float, float],
            nut: str = "M8",
            launcher_mass_g: float = LAUNCHER_MASS_G,
            launcher_cog: tuple[float, float, float] = LAUNCHER_COG) -> Balance:
    """Mass properties of launcher + grip + ballast.

    OVERHANG is the headline number and the one ballast actually moves: how
    far the assembly's centre of gravity sits ABOVE the hand's centre of
    pressure, measured along the grip axis. It is the lever the hand has to
    stabilise. Large overhang is the top-heavy, tippy feel of a bare
    launcher; shrinking it is what "planted" means, and it is the honest
    reading of tuning the balance point.

    HOLDING MOMENT about the wrist is reported too, and it is reported
    because it is unflattering. Ballast carried inside the butt sits
    slightly FORWARD of the wrist, so it very slightly increases the static
    torque the forearm holds, and raises inertia about the wrist by only a
    couple of percent. Anyone claiming an in-butt bay counterbalances a
    launcher, or that it meaningfully damps tremor, is selling something.
    What the bay genuinely does is pull the CoG down the grip toward the
    hand, and add total mass that the whole assembly carries. Those are
    worth having; the other claims are not true of this geometry, and a
    bay that could counterbalance would have to extend behind the wrist as
    a heel spur -- see docs/02 for why that was not taken for the MVP.
    """
    axis = _axis(p)
    neck = (p.neck_offset_x, 0.0, -10.0)              # approx shoe underside
    butt = tuple(neck[i] + axis[i] * p.grip_length for i in range(3))
    wrist = tuple(butt[i] + axis[i] * WRIST_OFFSET for i in range(3))

    # Centre of pressure of the hand: roughly the middle finger, i.e. the
    # tang zone plus one and a half finger pitches down from the neck.
    from .grip import TANG_ZONE
    hand_d = TANG_ZONE + 1.5 * p.finger_pitch
    hand = tuple(neck[i] + axis[i] * hand_d for i in range(3))

    n = NUTS[nut]
    ballast_mass = p.ballast_nuts * n.mass
    stack = p.ballast_nuts * n.thickness
    ballast_cog = tuple(butt[i] - axis[i] * (stack / 2 + 4.0) for i in range(3))

    items = [(launcher_mass_g, launcher_cog), (grip_mass_g, grip_cog)]
    if ballast_mass > 0:
        items.append((ballast_mass, ballast_cog))

    total = sum(m for m, _ in items)
    cog = tuple(sum(m * c[i] for m, c in items) / total for i in range(3))

    # Project CoG - hand onto the grip axis. The axis points down the grip,
    # so a NEGATIVE projection means the CoG is above the hand; flip the
    # sign so that "overhang" reads as a positive distance above.
    along = sum((cog[i] - hand[i]) * axis[i] for i in range(3))
    overhang = -along

    holding_moment = total / 1000.0 * G * (cog[0] - wrist[0])

    inertia = 0.0
    for m, c in items:
        d2 = sum((c[i] - wrist[i]) ** 2 for i in range(3))
        inertia += m / 1000.0 * d2 / 1e6          # g.mm^2 -> kg.m^2

    return Balance(cog=cog, hand=hand, wrist=wrist, total_mass=total,
                   ballast_mass=ballast_mass, overhang=overhang,
                   cog_height=cog[2], holding_moment=holding_moment,
                   inertia=inertia)


def balance_sweep(p: Params, grip_mass_g: float,
                  grip_cog: tuple[float, float, float],
                  nut: str = "M8") -> list[tuple[int, Balance]]:
    """Balance across the full 0-6 nut tuning range."""
    out = []
    for n in range(0, 7):
        q = Params(**{**p.__dict__, "ballast_nuts": n})
        out.append((n, balance(q, grip_mass_g, grip_cog, nut)))
    return out


# --------------------------------------------------------------------------
# Structural checks
# --------------------------------------------------------------------------
# PETG, printed. In-plane is along the extrusion; interlayer is across the
# layer bond and is the number that governs an upright-printed part.
PETG_INPLANE_MPA = 47.0
PETG_INTERLAYER_MPA = 27.0


def neck_bending(p: Params, pull_force_n: float = 120.0,
                 hand_offset: float = 35.0) -> dict[str, float]:
    """Bending at the neck under a hard ripcord pull.

    120 N is a deliberately pessimistic lateral reaction for a violent adult
    pull, pending strain-gauge data.

    The answer comes out boring, and that is the finding: the neck carries a
    30 x 35 mm section against a 4.2 N.m moment and is nowhere near
    anything. The neck is NOT the limiting feature of this part. Sizing the
    grip for comfort has already over-sized it for strength by more than an
    order of magnitude, so design effort belongs at the interface instead.
    """
    b = p.grip_width
    h = p.grip_depth * 0.78                    # neck station depth
    moment = pull_force_n * hand_offset
    z_mod = b * h ** 2 / 6
    solid_fraction = 0.55                      # shelled, not solid
    stress = moment / z_mod / solid_fraction
    return {
        "moment_nmm": moment,
        "section_modulus_mm3": z_mod,
        "stress_mpa": stress,
        "margin_inplane": PETG_INPLANE_MPA / stress,
        "margin_interlayer": PETG_INTERLAYER_MPA / stress,
    }


def dovetail_wall(grip_width: float = 30.0,
                  fit_clearance: float = 0.15,
                  separation_force_n: float = 150.0) -> dict[str, float]:
    """Splay of the shoe side wall -- the feature that actually governs.

    A vertical separation force tries to pull the launcher boss out of the
    dovetail. The converging flanks turn that into a lateral force that
    splays the two side walls apart, and the walls are the thinnest loaded
    structure in the part.

    Each flank carries half the pull. With the flank inclined `theta` from
    vertical, the contact normal sits `theta` off horizontal, so

        N      = (F/2) / sin(theta)
        splay  = N * cos(theta) = (F/2) / tan(theta)

    and each wall is then a cantilever off the pocket floor, loaded at
    mid-height.

    The wall is derived from `grip_width`, not read from RAIL_NOMINAL: the
    shoe is built as wide as the grip, so widening the grip thickens the
    wall and the safety factor moves with it. A hard-coded wall figure
    would silently under-report a 32 mm part and over-report a 28 mm one.

    Printed cheek-down the wall's bending stress runs along Z, inside the
    layer plane, so the allowable is the in-plane figure. Printed upright
    the same stress crosses every layer bond and the allowable drops to the
    interlayer figure -- both margins are returned so the gap is visible.
    """
    from .interface import rail
    r = rail()
    half_delta = (r["boss_width_bottom"] - r["boss_width_top"]) / 2
    theta = math.atan2(half_delta, r["boss_height"])

    wall = (grip_width - r["boss_width_bottom"] - 2 * fit_clearance) / 2

    splay = (separation_force_n / 2) / math.tan(theta)
    moment = splay * r["boss_height"] / 2
    z_mod = r["slide_length"] * wall ** 2 / 6
    stress = moment / z_mod
    shear = 1.5 * splay / (r["slide_length"] * wall)

    return {
        "wall_thickness_mm": wall,
        "flank_angle_deg": math.degrees(theta),
        "splay_force_n": splay,
        "moment_nmm": moment,
        "section_modulus_mm3": z_mod,
        "bending_stress_mpa": stress,
        "interlaminar_shear_mpa": shear,
        "margin_cheek_down": PETG_INPLANE_MPA / stress,
        "margin_upright": PETG_INTERLAYER_MPA / stress,
    }
