# 04 — DFM and Print Specification

## The orientation decision

**Print the part lying on a cheek. Build direction is the part's lateral (Y)
axis.** Everything else in the DFM follows from this, and it is worth the space
because it is the single highest-leverage decision in the design.

### Why not upright

Printed upright — shoe flat on the bed, grip rising — the layer planes are
horizontal. The neck's bending stress and the dovetail wall's splay stress both
run vertically, which means they run **normal to every layer bond**. PETG's
interlayer strength is roughly 27 MPa against about 47 MPa in-plane, so upright
printing throws away ~43 % of the material's strength in exactly the direction
the part is loaded. The grip would also need support under the raked stem.

### Why on a cheek

Lying on a cheek, the layer planes are the part's XZ planes. Now:

- The neck's bending stress lies **inside** the layer plane, carried by
  continuous extrusions rather than by bonds between them.
- The dovetail wall's splay stress likewise runs along Z, in-plane.
- The entire dovetail profile is drawn as an **in-plane contour** — XY precision
  rather than Z-stacked steps. This is the best possible case for a precision
  mating feature.
- The compliant floor leaf flexes in-plane, so it survives thousands of cycles
  instead of snapping along a layer line on the first hard mount.

Quantified, from `analysis.dovetail_wall()` on the governing feature:

| | cheek-down | upright |
|---|---|---|
| Dovetail wall safety factor | **4.89** | 2.81 |

Same geometry, same material, same load. A 1.74× strength difference, free.

### Why it costs nothing

This is the part that makes it an easy decision. Lying a rounded object on its
side is normally a support nightmare: the whole lower half grows outward and
overhangs. **It does not here, because the cheeks are flat.** A flat cheek means
the silhouette barely changes with build height, so the walls stay vertical from
first layer to last.

And the flat cheek was not adopted for printing — it is the correct ergonomic
section (`02`, §1.5) and the customisation canvas (`02`, §1.8). The DFM
constraint, the ergonomics and the branding surface are the same surface.

The result is a **squat** print:

| | |
|---|---|
| Footprint | 81.4 × 100.3 mm |
| Build height | **30.7 mm** |
| Layers at 0.2 mm | **154** |
| Bed contact | full flat cheek |
| Support material | **none** |

A 154-layer print cannot topple, has no tall-thin resonance, needs no brim, and
the bed-side cheek comes off a smooth plate with a near-moulded finish.

## Support-free by construction

Every feature was designed against the cheek-down build direction:

| Feature | Why it is self-supporting |
|---|---|
| Dovetail pocket | all faces are vertical walls in this orientation |
| Ballast hex socket | hexagon oriented **flats-to-cheeks** — roof is a flat 7.7 mm bridge approached by 60° walls |
| Finger scallops / knurl | shallow surface cuts, no enclosed overhang |
| Recoil shelf | tapers toward the tip, underside never exceeds 45° |
| Blend collar | converges upward from the shoe footprint |
| Cheek panel + text | 0.8 mm and 0.6 mm pockets in faces normal to build |
| Compliant leaf | in-plane cantilever |

The ballast socket deserves the callout. Rotating that hexagon 30° "to line the
flats up" turns it corner-to-cheek, and the roof stops being a flat bridge — a
blind 46 mm pocket full of support you cannot reach. Both the CadQuery and
OpenSCAD sources carry a comment saying so, because it is exactly the kind of
tidy-looking change a later maintainer makes.

## Material

| | Material | Why | Watch out |
|---|---|---|---|
| **Default** | **PETG** | tough rather than merely strong, snap-load tolerant, low warp, no enclosure, UV-stable | stringing; dry it |
| Premium | ASA / ABS | stiffer, acetone-smoothable, better in a hot car | needs an enclosure; warp |
| Pro | PA6-CF | stiffest, best fatigue life | hardened nozzle; must be dried |
| **Never** | PLA | brittle at the neck, creeps under sustained grip pressure, softens in a car | — |

PLA is excluded on purpose. It would test fine and fail in the field — the load
case is repeated snap loading by a teenager, and a grip that shatters mid-pull
is a safety problem, not a warranty problem.

## Slicer profile (PETG, 0.4 mm nozzle)

| Setting | Value | Reason |
|---|---|---|
| Layer height | 0.2 mm | 154 layers; 0.16 for finer text |
| Perimeters | **4** (1.6 mm) | shell carries the load; the in-plane path |
| Top / bottom | 5 / 5 | cheek faces are visible surfaces |
| Infill | **15 % gyroid** | isotropic; grip is shell-dominated |
| Nozzle temp | **245–255 °C** | run hot — interlayer bonding is the point |
| Bed | 80 °C, smooth PEI | bed-side cheek is a finished surface |
| Cooling | 30–50 % | enough for bridges, not enough to spoil bonding |
| Seam | rear corner, aligned | keep it off the cheek panel |
| Support | **none** | by construction |

Two deviations from a generic profile, both load-bearing:

- **Four perimeters, not three.** The shell is the structure here; infill is
  nearly incidental.
- **Upper-range nozzle temperature.** Interlayer strength is the whole argument
  for the orientation choice; printing cool would give some of it back.

## Stress-concentration discipline

- **No sharp internal corners anywhere in the load path.** Every section carries
  a corner radius that scales with hand size (9.0–10.0 mm).
- Blend collar instead of a fillet at the neck — not a cosmetic choice, see
  `02` §1.2.
- Recoil shelf root filleted R2.5, tapering to R1.6 at the tip.
- Ballast socket leaves **8.3 mm** of cheek wall; `params.validate()` refuses any
  order that would take it below 2.4 mm.

## Envelope compliance

Verified across the full published fit range by `python -m vertex.validate`:

| hand | rake | girth | mass | time | wall SF | status |
|---|---|---|---|---|---|---|
| 80 | 20° | 124.5 mm | 46.3 g | 0.92 h | 4.89 | ok |
| 85 | 19° | 128.6 mm | 49.6 g | 0.99 h | 4.89 | ok |
| 90 | 18° | 132.7 mm | 53.1 g | 1.06 h | 4.89 | ok |
| 95 | 17° | 136.8 mm | 56.7 g | 1.13 h | 4.89 | ok |
| 100 | 16° | 140.8 mm | 60.5 g | 1.20 h | 4.89 | ok |
| 90 | 10° | 132.7 mm | 53.0 g | 1.05 h | 4.89 | ok |
| 90 | 32° | 132.7 mm | 53.2 g | 1.06 h | 4.89 | ok |

Envelope 40–75 g and under 3 h, met with margin at both extremes. The
as-shipped unit with knurl texture is 54.4 g / 1.08 h.

Mass and time are **first-order estimates** — a shell of `shell_thick` over the
measured surface area plus `infill_fraction` inside, at an effective 11 mm³/s
including travel and acceleration. They exist to reject an impossible order
before it ties up a printer. **The slicer is authoritative**, and the manifest
says so.
