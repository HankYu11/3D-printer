"""
Interface fit gauge.

    python -m calibration.rail_gauge --out out/

Prints as one small coupon in roughly 10 minutes and turns the project's
biggest unknown into a measured number.

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
GAP = 6.0          # between stations
BASE_THICK = 3.0   # spine tying the stations together
LABEL_SIZE = 4.5
LABEL_DEPTH = 0.6


def build_gauge(stations: list[float] = STATIONS,
                grip_width: float = 30.0) -> cq.Workplane:
    """A strip of dovetail stations, one per candidate clearance."""
    r = rail()
    pitch = grip_width + GAP
    span = pitch * len(stations)

    gauge = None
    for i, clearance in enumerate(stations):
        y = (i - (len(stations) - 1) / 2) * pitch
        shoe = build_shoe(grip_width, fit_clearance=clearance,
                          tournament_lock=False)
        block = shoe.block.union(shoe.leaf, clean=False)
        block = block.cut(shoe.cutter, clean=False)
        station = block.translate((0, y, 0))

        # Deboss the clearance on the aft face so it stays readable once a
        # launcher is sitting in the pocket.
        label = f"{clearance:+.2f}"
        txt = (cq.Workplane("XZ")
               .text(label, LABEL_SIZE, LABEL_DEPTH + 1.0,
                     combine=False, font="DejaVu Sans")
               .rotate((0, 0, 0), (1, 0, 0), 90)
               .translate((0, y, -shoe.height + LABEL_DEPTH + 1.0 - 0.001)))
        glyphs = txt.solids().vals()
        if glyphs:
            station = cq.Workplane(obj=station.val().cut(*glyphs))

        gauge = station if gauge is None else gauge.union(station, clean=False)

    # Spine underneath, so the stations print and handle as one coupon.
    shoe_h = build_shoe(grip_width, fit_clearance=0.0).height
    spine = (cq.Workplane("XY")
             .box(r["slide_length"] * 0.6, span - GAP, BASE_THICK,
                  centered=(True, True, False))
             .translate((0, 0, -shoe_h - BASE_THICK + 0.001)))
    return gauge.union(spine, clean=False)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build the interface fit gauge.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--width", type=float, default=30.0)
    args = ap.parse_args(argv)

    print(f"interface provenance: {provenance()}")
    print(f"stations: {', '.join(f'{s:+.2f}' for s in STATIONS)} mm")

    g = build_gauge(grip_width=args.width)
    solid = g.val()
    if not solid.isValid():
        raise RuntimeError("gauge solid failed validity check")
    bb = solid.BoundingBox()

    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "rail_gauge")
    exporters.export(g, path + ".step")
    exporters.export(g, path + ".stl", tolerance=0.01, angularTolerance=0.1)

    print(f"volume {solid.Volume():.0f} mm^3, "
          f"bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
    print(f"-> {path}.{{step,stl}}")
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
