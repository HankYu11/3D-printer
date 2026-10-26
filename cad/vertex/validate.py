"""
Envelope sweep.

    python -m vertex.validate            # fast, texture off
    python -m vertex.validate --full     # as-shipped, with texture

Builds across the published fit range and checks every order against the
product envelope: 40-75 g, under 3 h, a girth in the power-grip band, and a
dovetail wall safety factor above 2.0.

This is the regression test. The generator will happily produce a watertight
solid that is the wrong size, too heavy to sell or too weak to pull on --
validity is not correctness, so the envelope has to be asserted separately.
"""

from __future__ import annotations

import argparse
import sys

from . import analysis
from .build import build, manifest
from .params import Params

MASS_MIN, MASS_MAX = 40.0, 75.0
HOURS_MAX = 3.0
GIRTH_MIN, GIRTH_MAX = 118.0, 145.0
WALL_SF_MIN = 2.0


def run(full: bool) -> int:
    texture = "knurl" if full else "none"
    cases = [(h, r) for h, r in
             ((80, 20), (85, 19), (90, 18), (95, 17), (100, 16))]
    cases += [(90, 10), (90, 32)]          # rake extremes

    print(f"VERTEX-1 envelope sweep (texture={texture})")
    print(f"{'hand':>5} {'rake':>5} {'girth':>7} {'len':>6} {'mass':>7} "
          f"{'hours':>6} {'wallSF':>7} {'overhang':>9}  status")
    print("-" * 74)

    failures = 0
    for hand, rake in cases:
        p = Params(hand_breadth=float(hand), rake_deg=float(rake),
                   player_id="TESTER", texture=texture)
        part, report = build(p)
        man = manifest(p, part, report)

        mass = man["print_estimate"]["estimated_mass_g"]
        hours = man["print_estimate"]["estimated_hours"]
        girth = man["derived"]["grip_circumference_mm"]
        wall = man["structure"]["dovetail_wall"]["margin_cheek_down"]
        over = man["balance"]["cog_overhang_above_hand_mm"]

        problems = []
        if not MASS_MIN <= mass <= MASS_MAX:
            problems.append(f"mass {mass:.1f}g")
        if hours > HOURS_MAX:
            problems.append(f"time {hours:.2f}h")
        if not GIRTH_MIN <= girth <= GIRTH_MAX:
            problems.append(f"girth {girth:.1f}mm")
        if wall < WALL_SF_MIN:
            problems.append(f"wallSF {wall:.2f}")
        if len(part.solids().vals()) != 1:
            problems.append("not a single solid")

        status = "ok" if not problems else "FAIL: " + ", ".join(problems)
        failures += bool(problems)
        print(f"{hand:>5} {rake:>5} {girth:>7.1f} "
              f"{man['derived']['grip_length_mm']:>6.1f} {mass:>7.1f} "
              f"{hours:>6.2f} {wall:>7.2f} {over:>9.1f}  {status}")

    print("-" * 74)

    # Rejection cases: the validator must refuse these, not build them.
    print("\nOrder validation (these must be refused):")
    bad = [("hand 70", Params(hand_breadth=70.0)),
           ("hand 115", Params(hand_breadth=115.0)),
           ("rake 45", Params(rake_deg=45.0)),
           ("11-char id", Params(player_id="OVERLONGTAG")),
           ("8 nuts", Params(ballast_nuts=8))]
    for label, q in bad:
        issues = q.validate()
        ok = bool(issues)
        failures += not ok
        print(f"  {label:<12} {'refused' if ok else 'ACCEPTED (BUG)':<16} "
              f"{issues[0] if issues else ''}")

    print()
    if failures:
        print(f"{failures} check(s) failed")
    else:
        print("all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true",
                    help="build with texture as shipped (slower)")
    sys.exit(run(ap.parse_args().full))
