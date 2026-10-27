"""
Interface fit gauge.

    python -m calibration.rail_gauge --out out/

Turns the project's biggest unknown into a measured number.

Run it: it prints its own time estimate for several profiles rather than
quoting a figure here. An earlier version of this docstring claimed
"roughly 10 minutes" because nobody had run the numbers -- it was really
2.5-4 h, and the claim survived precisely because it was asserted rather
than computed.

WHY THIS EXISTS
---------------
The dovetail clearance that gives a dead-solid fit is not a number anyone
can derive. It is the sum of the launcher's real geometry, the printer's XY
flow compensation, the filament, the nozzle, and how humid the room was.
Different printers in the same fleet land 0.1 mm apart on the same file.

So the pipeline does not guess it. It measures it once per printer/material
pairing: print the gauge, try each station on a real launcher, keep the
tightest one that still slides home without force, and write that number
into FIT_CLEARANCE for that machine profile.

The gauge imports the SAME build_shoe() the product uses, so what you test
is the geometry that ships. A gauge with its own copy of the dovetail would
drift out of sync with the part on the first revision and quietly certify
the wrong fit.
"""

from __future__ import annotations

import argparse
import os
import sys

import cadquery as cq
from cadquery import exporters

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vertex.interface import build_shoe, provenance, rail   # noqa: E402

STATIONS = [-0.05, 0.00, 0.05, 0.10, 0.15]
GAP = 4.0          # between stations
BASE_THICK = 1.6   # spine tying the stations together
LABEL_SIZE = 4.5
LABEL_DEPTH = 0.6

# The gauge is stripped to the one thing it measures: the dovetail fit.
#
# The first version simply repeated the production shoe five times, and it
# was a 2.5-4 h print -- more surface area than the grip itself, and the
# leaf spring's relief slot was the only feature on the whole project that
# forces support. A calibration coupon that costs half a day defeats its
# own purpose; nobody re-runs it when they change filament.
#
# So: floor cut to the minimum that holds the dovetail, no leaf spring
# (preload is not what is being measured here, and it is validated on the
# real part), and a thin spine. Engagement LENGTH is deliberately left at
# full size -- perceived wobble scales with how long the joint is, so a
# shortened station would feel looser than the real shoe and bias the
# reading it exists to produce.
GAUGE_FLOOR = 1.6


def build_gauge(stations: list[float] = STATIONS,
                grip_width: float = 30.0) -> cq.Workplane:
    """A strip of dovetail stations, one per candidate clearance."""
    r = rail()
    pitch = grip_width + GAP
    span = pitch * len(stations)

    # Every station must finish the SAME total height, or the spine only
    # touches the tallest ones. Pocket depth grows with clearance, so the
    # floor is thinned by the same amount to compensate: height becomes
    # boss_height + max_clearance + GAUGE_FLOOR for all of them. Without
    # this the -0.05 station sat 0.05 mm proud of the spine and its entire
    # 34 x 32 mm underside -- 1 088 mm^2, the whole face -- printed as an
    # unsupported ceiling.
    max_c = max(stations)

    gauge = None
    for i, clearance in enumerate(stations):
        y = (i - (len(stations) - 1) / 2) * pitch
        shoe = build_shoe(grip_width, fit_clearance=clearance,
                          tournament_lock=False, leaf=False,
                          floor_override=GAUGE_FLOOR + (max_c - clearance))
        block = shoe.block.cut(shoe.cutter, clean=False)
        station = block.translate((0, y, 0))

        # Label on the TOP face, in the flat margin beside the pocket.
        #
        # Not on the pocket floor, for two reasons. The floor is the mating
        # surface -- glyph recesses under the launcher boss are noise in
        # the one measurement this part exists to make. And with the floor
        # trimmed to GAUGE_FLOOR the old 1.6 mm label cut went clean
        # THROUGH it, turning every label into a hole into the spine and
        # putting 1 134 mm2 of unsupported ceiling back into the print.
        label = f"{clearance:+.2f}"
        pocket_half = (r["boss_width_top"] + 2 * max(stations)) / 2
        txt = (cq.Workplane("XY")
               .text(label, LABEL_SIZE, LABEL_DEPTH + 1.0,
                     combine=False, font="DejaVu Sans")
               .translate((0, y + pocket_half + LABEL_SIZE / 2 + 1.5,
                           -LABEL_DEPTH)))
        glyphs = txt.solids().vals()
        if glyphs:
            station = cq.Workplane(obj=station.val().cut(*glyphs))

        gauge = station if gauge is None else gauge.union(station, clean=False)

    # Spine underneath, so the stations print and handle as one coupon.
    shoe_h = build_shoe(grip_width, fit_clearance=max_c,
                        floor_override=GAUGE_FLOOR).height
    # Full station width, not a narrow rib. A spine narrower than the
    # stations leaves every station's underside overhanging it -- measured
    # at 3 028 mm^2, 14.6 % of the surface, all of it needing support or a
    # bridge. Full width makes the whole underside one flat bed face.
    spine = (cq.Workplane("XY")
             .box(r["slide_length"] + r["stop_thick"], span - GAP, BASE_THICK,
                  centered=(True, True, False))
             .translate((0, 0, -shoe_h - BASE_THICK + 0.001)))
    return gauge.union(spine, clean=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the interface fit gauge.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--width", type=float, default=30.0)
    ap.add_argument("--stations", type=int, default=len(STATIONS),
                    help="how many clearance stations to include (1-5). "
                         "Fewer is a shorter print; start with 3 and refine.")
    args = ap.parse_args(argv)

    chosen = STATIONS
    if args.stations < len(STATIONS):
        # Keep the ends and spread the rest, so a reduced gauge still
        # brackets the range instead of clustering.
        idx = [round(i * (len(STATIONS) - 1) / (args.stations - 1))
               for i in range(args.stations)] if args.stations > 1 else [2]
        chosen = [STATIONS[i] for i in sorted(set(idx))]

    print(f"interface provenance: {provenance()}")
    print(f"stations: {', '.join(f'{s:+.2f}' for s in chosen)} mm")

    g = build_gauge(stations=chosen, grip_width=args.width)
    solid = g.val()
    if not solid.isValid():
        raise RuntimeError("gauge solid failed validity check")
    bb = solid.BoundingBox()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "rail_gauge")
    exporters.export(g, path + ".step")
    exporters.export(g, path + ".stl", tolerance=0.01, angularTolerance=0.1)

    # Estimate rather than assert. The original version of this file
    # claimed "roughly 10 minutes" from nobody having run the numbers; it
    # was really 2.5-4 h, and the claim survived because no one checked.
    vol, area = solid.Volume(), solid.Area()
    print(f"volume {vol:.0f} mm^3, surface {area:.0f} mm^2, "
          f"bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"-> {path}.{{step,stl}}")
    print()
    print("ESTIMATED PRINT TIME (no support needed in this orientation):")
    for shell, infill, label in ((0.8, 0.15, "2 walls / 15%"),
                                 (1.2, 0.20, "3 walls / 20%")):
        sh = min(area * shell, vol)
        mat = sh + max(vol - sh, 0) * infill
        for nozzle, layer, speed in ((0.4, 0.2, 50), (0.4, 0.2, 60),
                                     (0.6, 0.3, 60)):
            rate = min(nozzle * 1.05 * layer * speed, 11.0) * 0.75
            print(f"  {label:<14} {nozzle}mm/{layer}mm @ {speed}mm/s -> "
                  f"{mat / rate / 60:5.0f} min  ({mat * 1.24 / 1000:.0f} g)")
    print()
    print("PROCEDURE")
    print("  1. Print flat, SAME printer / material / profile as the grip.")
    print("  2. Try each station on the launcher, tight to loose.")
    print("  3. Keep the TIGHTEST that seats fully by hand, no tool, no force.")
    print("  4. Write that value into interface.FIT_CLEARANCE_DEFAULT")
    print("     (or the machine profile) and re-run the build.")
    print("  5. Re-run whenever the filament, nozzle or printer changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
