"""
VERTEX-1 parameter model.

Single source of truth for every dimension in the generator. Nothing in
``interface.py`` or ``grip.py`` may hard-code a number that belongs here.

Three tiers of parameter:

  CUSTOMER   -- exposed in the order form / configurator UI. Safe to vary
                across the published range without re-validating the part.
  ENGINEERING -- set by us. Changing one requires a re-print and a re-test.
  GROUND TRUTH -- measured off the physical launcher. See interface.py.

All dimensions are millimetres, all angles are degrees, unless the name
says otherwise.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field, fields
from typing import Literal

# --------------------------------------------------------------------------
# Anthropometric mapping
# --------------------------------------------------------------------------
# "Hand size" is collected from the customer as HAND BREADTH: the width of
# the palm measured across the knuckles (metacarpal heads), thumb excluded.
# It is the single easiest hand dimension for a layperson to self-measure
# accurately with a ruler and a phone camera, and it correlates well with
# the grip circumference that maximises power-grip force.
#
# Published range 80-100 mm spans roughly a 12-year-old to a large adult.
HAND_BREADTH_MIN = 80.0
HAND_BREADTH_MAX = 100.0

# Derived-geometry coefficients, fitted so that the resulting grip
# circumference lands in the 124-141 mm band that pistol-grip ergonomics
# literature treats as the power-grip optimum for this hand-breadth range.
DEPTH_AT_MIN_HAND = 40.0        # fore-aft grip depth at 80 mm hand breadth
DEPTH_PER_MM_HAND = 0.45        # mm of grip depth per mm of hand breadth
RADIUS_AT_MIN_HAND = 9.0        # cross-section corner radius at 80 mm
RADIUS_PER_MM_HAND = 0.05
FINGER_PITCH_RATIO = 0.205      # finger-to-finger spacing / hand breadth


Texture = Literal["knurl", "ribs", "none"]
Material = Literal["PETG", "ABS", "ASA", "PA6-CF"]

# Filament density, g/cm^3.
DENSITY = {"PETG": 1.27, "ABS": 1.04, "ASA": 1.07, "PA6-CF": 1.16}


@dataclass
class Params:
    # ---------------- CUSTOMER TIER ----------------
    hand_breadth: float = 90.0
    """Palm width across the knuckles, 80-100 mm. Drives girth and length."""

    rake_deg: float = 18.0
    """Grip axis rake aft of the launch axis, 10-32 deg. See docs/02."""

    player_id: str = ""
    """Debossed on both cheek panels. <= 10 chars. Empty disables."""

    texture: Texture = "knurl"
    handed: Literal["right", "left", "ambi"] = "ambi"
    material: Material = "PETG"

    ballast_nuts: int = 3
    """M8 hex nuts carried in the butt bay, 0-6. Reported, not modelled."""

    # ---------------- ENGINEERING TIER ----------------
    grip_width: float = 30.0
    """Cheek-to-cheek width. CONSTANT by design -- the flat parallel cheeks
    are what let the part print support-free on its side (docs/04)."""

    neck_offset_x: float = -6.0
    """Grip axis origin aft of the launch axis, at the shoe underside."""

    # Recoil shelf: the forward ledge the index finger hooks under, so
    # downward recoil is carried by the finger's skeleton instead of by
    # grip friction. Projection is measured beyond the shoe's front face.
    shelf_depth: float = 9.0
    shelf_thick: float = 7.0
    shelf_rise_deg: float = 8.0
    shelf_root_inset: float = 6.0

    # No tang parameters: the beavertail is not a separate boss. Raking the
    # grip aft already carries the upper backstrap behind the shoe, and the
    # blend collar fills the corner -- that pocket IS the tang, and the web
    # of the hand seats in it. Adding a boss would only duplicate it.

    # Finger registers cut into the frontstrap
    index_scallop_r: float = 12.0
    index_scallop_depth: float = 2.2
    finger_groove_depth: float = 1.5
    finger_groove_r: float = 9.0

    # Ballast bay -- hex socket sized for DIN 934 M8 nuts
    ballast_af: float = 13.0        # nut across-flats, nominal
    ballast_clear: float = 0.35     # per-socket clearance
    ballast_depth: float = 46.0
    ballast_offset_x: float = -5.0  # aft of local grip axis
    cap_screw_offset_x: float = 11.0
    cap_insert_dia: float = 4.2     # M3 brass heat-set insert, OD
    cap_insert_depth: float = 6.0

    # Cheek customisation panel
    panel_recess: float = 0.8
    panel_len: float = 56.0
    panel_width: float = 24.0
    text_depth: float = 0.6
    text_size: float = 8.0
    text_font: str = "DejaVu Sans"

    # Texture
    knurl_pitch: float = 4.2
    knurl_depth: float = 0.75
    knurl_angle_deg: float = 35.0

    # Structural
    neck_fillet: float = 6.0
    shell_thick: float = 1.6        # 4 perimeters at 0.4 mm
    infill_fraction: float = 0.15

    # ---------------- DERIVED ----------------
    @property
    def hand_t(self) -> float:
        """Hand size normalised to 0..1 across the published range."""
        span = HAND_BREADTH_MAX - HAND_BREADTH_MIN
        return (self.hand_breadth - HAND_BREADTH_MIN) / span

    @property
    def grip_depth(self) -> float:
        """Fore-aft depth at the palm swell -- the girth driver."""
        d = self.hand_breadth - HAND_BREADTH_MIN
        return DEPTH_AT_MIN_HAND + DEPTH_PER_MM_HAND * d

    @property
    def corner_r(self) -> float:
        d = self.hand_breadth - HAND_BREADTH_MIN
        return RADIUS_AT_MIN_HAND + RADIUS_PER_MM_HAND * d

    @property
    def finger_pitch(self) -> float:
        return FINGER_PITCH_RATIO * self.hand_breadth

    @property
    def grip_length(self) -> float:
        """Neck to butt face, along the raked grip axis.

        Four finger pitches (index, middle, ring, little) plus a fixed
        allowance for the tang zone above and the butt flare below.
        """
        return 4.0 * self.finger_pitch + 16.0

    @property
    def grip_circumference(self) -> float:
        """Perimeter of the rounded-rectangle section at the palm swell.

        Rounded rectangle, not ellipse: the straight cheek runs are a real
        part of the contour and an elliptical approximation under-reports
        girth by ~10 %.
        """
        w, d, r = self.grip_width, self.grip_depth, self.corner_r
        import math
        return 2 * (w - 2 * r) + 2 * (d - 2 * r) + 2 * math.pi * r

    @property
    def density(self) -> float:
        return DENSITY[self.material]

    # ---------------- VALIDATION ----------------
    def validate(self) -> list[str]:
        """Return a list of problems. Empty list means the order is buildable."""
        p: list[str] = []
        if not HAND_BREADTH_MIN <= self.hand_breadth <= HAND_BREADTH_MAX:
            p.append(
                f"hand_breadth {self.hand_breadth} outside published range "
                f"{HAND_BREADTH_MIN}-{HAND_BREADTH_MAX} mm"
            )
        if not 10.0 <= self.rake_deg <= 32.0:
            p.append(f"rake_deg {self.rake_deg} outside validated range 10-32 deg")
        if len(self.player_id) > 10:
            p.append(f"player_id '{self.player_id}' exceeds 10 characters")
        if not self.player_id.replace(" ", "").replace("-", "").isalnum() and self.player_id:
            p.append("player_id must be alphanumeric plus space and hyphen")
        if not 0 <= self.ballast_nuts <= 6:
            p.append(f"ballast_nuts {self.ballast_nuts} outside 0-6")
        # Wall check. The hex socket presents its across-FLATS dimension
        # laterally (polygon() orients flats normal to Y), so that is what
        # eats into the cheek wall -- not across-corners.
        wall = (self.grip_width - (self.ballast_af + self.ballast_clear)) / 2
        if wall < 2.4:
            p.append(f"ballast socket leaves only {wall:.1f} mm cheek wall (min 2.4)")
        return p

    # ---------------- SERIALISATION ----------------
    def to_json(self, path: str) -> None:
        with open(path, "w") as fh:
            json.dump(asdict(self), fh, indent=2, sort_keys=True)

    @classmethod
    def from_json(cls, path: str) -> "Params":
        with open(path) as fh:
            raw = json.load(fh)
        known = {f.name for f in fields(cls)}
        unknown = set(raw) - known
        if unknown:
            raise ValueError(f"unknown parameters in {path}: {sorted(unknown)}")
        return cls(**raw)

    def summary(self) -> str:
        return (
            f"hand_breadth={self.hand_breadth:.0f}mm  rake={self.rake_deg:.0f}deg  "
            f"girth={self.grip_circumference:.1f}mm  depth={self.grip_depth:.1f}mm  "
            f"length={self.grip_length:.1f}mm  pitch={self.finger_pitch:.1f}mm"
        )
