"""
VERTEX-1 build driver.

    python -m vertex.build --preset presets/adult_mid.json --out out/

Produces, per order:
    <name>.step      B-Rep, for CAD handoff and downstream edits
    <name>.stl       mesh, for the slicer
    <name>.json      manifest: parameters, mass properties, analysis, warnings

The manifest is the artefact that makes this a manufacturing pipeline
rather than a model. It carries the exact parameter set, the computed mass
and balance, the interface provenance and every warning, so a part that
comes off a printer in six months can be traced back to the inputs that
generated it.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys
import time
from dataclasses import asdict

import cadquery as cq
from cadquery import exporters

from . import analysis, grip as G, interface as IF
from .params import Params

NECK_OVERLAP = 7.0    # how far the stem buries itself inside the shoe


# --------------------------------------------------------------------------
def build(p: Params) -> tuple[cq.Workplane, dict]:
    """Build the complete grip. Returns (solid, build_report)."""
    report: dict = {"warnings": [], "notes": []}

    problems = p.validate()
    if problems:
        raise ValueError("invalid order:\n  - " + "\n  - ".join(problems))

    shoe = IF.build_shoe(p.grip_width)
    report["interface_provenance"] = IF.provenance()
    if IF.provenance() != "VERIFIED":
        report["warnings"].append(
            "Launcher interface geometry is UNVERIFIED placeholder data. "
            "Measure a physical launcher, populate interface.RAIL_MEASURED "
            "and set RAIL_VERIFIED=True before cutting a saleable part.")
    if not analysis.LAUNCHER_PROPS_VERIFIED:
        report["warnings"].append(
            "Launcher mass and balance point are estimates; the balance "
            "figures below are directional only.")

    grip_local, branding = G.build_grip_local(p, NECK_OVERLAP)
    report["branding"] = branding
    grip = G.place(grip_local, p, shoe.underside_z)

    collar = G.blend_collar(p, shoe.underside_z, shoe.length)
    shelf = G.recoil_shelf(p, shoe.underside_z, shoe.length)

    # Order matters. The shoe cutter runs LAST so that neither the grip nor
    # the blend collar can intrude into the dovetail, whatever they do.
    part = shoe.block.union(grip, clean=False)
    part = part.union(collar, clean=False)
    part = part.union(shelf, clean=False)
    if shoe.leaf is not None:
        part = part.union(shoe.leaf, clean=False)
    part = part.cut(shoe.cutter, clean=False)
    report["neck_blend"] = "lofted collar"

    solid = part.val()
    if not solid.isValid():
        raise RuntimeError("generated solid failed validity check")
    if len(part.solids().vals()) != 1:
        raise RuntimeError(
            f"expected one solid, got {len(part.solids().vals())} -- the grip "
            "is probably not reaching the shoe")

    return part, report


# --------------------------------------------------------------------------
def manifest(p: Params, part: cq.Workplane, report: dict) -> dict:
    solid = part.val()
    volume = solid.Volume()
    area = solid.Area()
    com = solid.Center()
    bb = solid.BoundingBox()

    est = analysis.estimate_print(p, volume, area)
    bal = analysis.balance(p, est.mass, (com.x, com.y, com.z))
    neck = analysis.neck_bending(p)
    wall = analysis.dovetail_wall(p.grip_width, IF.FIT_CLEARANCE_DEFAULT)

    warnings = list(report["warnings"])
    for face, info in report.get("branding", {}).items():
        if info["draft_deg_applied"] < info["draft_deg_requested"]:
            warnings.append(
                f"{face}: deboss draft limited to "
                f"{info['draft_deg_applied']:.0f} deg (requested "
                f"{info['draft_deg_requested']:.0f} deg) -- a larger angle "
                f"merges the glyphs of '{info['tag']}' at the mouth")
    if not 40.0 <= est.mass <= 75.0:
        warnings.append(
            f"estimated mass {est.mass:.1f} g is outside the 40-75 g product "
            "envelope")
    if est.hours > 3.0:
        warnings.append(
            f"estimated print time {est.hours:.2f} h exceeds the 3 h target")
    # The dovetail wall governs, not the neck -- check the one that bites.
    if wall["margin_cheek_down"] < 2.0:
        warnings.append(
            f"dovetail wall safety factor {wall['margin_cheek_down']:.2f} "
            "is below 2.0 even printed cheek-down")

    params = asdict(p)
    digest = hashlib.sha256(
        json.dumps(params, sort_keys=True).encode()).hexdigest()[:12]

    return {
        "schema": "vertex-grip/1",
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "order_digest": digest,
        "parameters": params,
        "derived": {
            "grip_circumference_mm": round(p.grip_circumference, 2),
            "grip_depth_mm": round(p.grip_depth, 2),
            "grip_length_mm": round(p.grip_length, 2),
            "finger_pitch_mm": round(p.finger_pitch, 2),
        },
        "geometry": {
            "solid_volume_mm3": round(volume, 1),
            "surface_area_mm2": round(area, 1),
            "bbox_mm": [round(bb.xlen, 2), round(bb.ylen, 2), round(bb.zlen, 2)],
            "centre_of_mass_mm": [round(com.x, 2), round(com.y, 2), round(com.z, 2)],
            "neck_blend": report["neck_blend"],
        },
        "print_estimate": {
            "material_volume_mm3": round(est.material_volume, 1),
            "estimated_mass_g": round(est.mass, 1),
            "estimated_hours": round(est.hours, 2),
            "effective_density": round(est.effective_density, 3),
            "density_g_cm3": p.density,
            "shell_thick_mm": p.shell_thick,
            "infill_fraction": p.infill_fraction,
            "machine": {"nozzle_mm": p.nozzle_dia, "layer_mm": p.layer_height,
                        "speed_mm_s": p.print_speed, "max_flow_mm3_s": p.max_flow},
            "note": "first-order; the slicer is authoritative",
        },
        "balance": {
            "ballast_nuts": p.ballast_nuts,
            "ballast_mass_g": round(bal.ballast_mass, 1),
            "assembly_mass_g": round(bal.total_mass, 1),
            "cog_overhang_above_hand_mm": round(bal.overhang, 1),
            "cog_height_mm": round(bal.cog_height, 1),
            "wrist_moment_nmm": round(bal.holding_moment, 1),
            "inertia_kgm2": round(bal.inertia, 6),
        },
        "structure": {
            "neck": {k: round(v, 3) for k, v in neck.items()},
            "dovetail_wall": {k: round(v, 3) for k, v in wall.items()},
            "governing_feature": "dovetail_wall",
        },
        "branding": report.get("branding", {}),
        "interface": {
            "provenance": report["interface_provenance"],
            "rail": IF.rail(),
            "fit_clearance_mm": IF.FIT_CLEARANCE_DEFAULT,
            "wedge_taper_deg": IF.WEDGE_TAPER_DEG,
        },
        "warnings": warnings,
    }


# --------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate a VERTEX-1 grip.")
    ap.add_argument("--preset", help="JSON parameter file")
    ap.add_argument("--out", default="out", help="output directory")
    ap.add_argument("--name", help="base filename (default: derived)")
    ap.add_argument("--hand", type=float, help="override hand_breadth, mm")
    ap.add_argument("--rake", type=float, help="override rake_deg")
    ap.add_argument("--id", dest="player_id", help="override player_id")
    ap.add_argument("--texture", choices=("knurl", "ribs", "none"))
    ap.add_argument("--nuts", type=int, help="override ballast_nuts")
    ap.add_argument("--no-stl", action="store_true")
    ap.add_argument("--exact-name", action="store_true",
                    help="do not append the _PROTOTYPE suffix. The stamp is a "
                         "safety marker for unverified interface geometry, so "
                         "dropping it has to be deliberate; the banner and the "
                         "manifest warning are unaffected.")
    ap.add_argument("--stl-tolerance", type=float, default=0.01,
                    help="STL chord (linear deflection) tolerance in mm")
    args = ap.parse_args(argv)

    p = Params.from_json(args.preset) if args.preset else Params()
    for attr, val in (("hand_breadth", args.hand), ("rake_deg", args.rake),
                      ("player_id", args.player_id), ("texture", args.texture),
                      ("ballast_nuts", args.nuts)):
        if val is not None:
            setattr(p, attr, val)

    if IF.provenance() != "VERIFIED":
        print("=" * 70)
        print(" INTERFACE GEOMETRY IS UNVERIFIED PLACEHOLDER DATA")
        print(" Output is a PROTOTYPE. It will not reliably fit a real")
        print(" launcher. See cad/vertex/interface.py and docs/03.")
        print("=" * 70)

    print(p.summary())
    t0 = time.time()
    part, report = build(p)
    print(f"built in {time.time() - t0:.1f}s")

    man = manifest(p, part, report)
    man["export"] = {"stl_chord_tolerance_mm": args.stl_tolerance,
                     "prototype_stamp": not args.exact_name}
    os.makedirs(args.out, exist_ok=True)
    base = args.name or f"vertex1_h{p.hand_breadth:.0f}_r{p.rake_deg:.0f}"
    if IF.provenance() != "VERIFIED" and not args.exact_name:
        base += "_PROTOTYPE"
    stem_path = os.path.join(args.out, base)

    exporters.export(part, stem_path + ".step")
    if not args.no_stl:
        exporters.export(part, stem_path + ".stl",
                         tolerance=args.stl_tolerance, angularTolerance=0.1)
    with open(stem_path + ".json", "w") as fh:
        json.dump(man, fh, indent=2)

    g = man["geometry"]
    e = man["print_estimate"]
    b = man["balance"]
    print(f"  volume   {g['solid_volume_mm3']:>9.1f} mm^3   bbox {g['bbox_mm']}")
    print(f"  material {e['material_volume_mm3']:>9.1f} mm^3 "
          f"-> {e['estimated_mass_g']:.1f} g, {e['estimated_hours']:.2f} h")
    print(f"  assembly {b['assembly_mass_g']:.1f} g, CoG overhang "
          f"{b['cog_overhang_above_hand_mm']:.1f} mm above hand "
          f"({b['ballast_nuts']} nuts)")
    for face, info in man["branding"].items():
        print(f"  {face}: '{info['tag']}' {info['size_mm']}mm, "
              f"draft {info['draft_deg_applied']:.0f}deg "
              f"(asked {info['draft_deg_requested']:.0f})")
    print(f"  dovetail wall SF {man['structure']['dovetail_wall']['margin_cheek_down']:.2f} "
          f"cheek-down vs {man['structure']['dovetail_wall']['margin_upright']:.2f} upright "
          f"(wall {man['structure']['dovetail_wall']['wall_thickness_mm']:.2f}mm)")
    for w in man["warnings"]:
        print(f"  WARNING: {w}")
    print(f"  -> {stem_path}.{{step,stl,json}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
