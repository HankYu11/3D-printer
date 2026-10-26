# 07 — Qisi Tech Edition (VERTEX-01)

Brand build on the VERTEX-1 architecture: 奇斯科技's clean structural identity,
rendered as minimal faceted hardware with no decorative noise.

Generate with:

```bash
cd cad
python -m vertex.build --preset ../presets/qisi_edition.json \
       --out vertex/export --name grip_qisi_edition --exact-name --stl-tolerance 0.02
python -m calibration.rail_gauge --out vertex/export --width 32
```

## As built

| | |
|---|---|
| Solid volume | 129 323 mm³ |
| Bounding box | 84.48 × **32.00** × 105.14 mm |
| Grip length / girth | 94.7 mm / 141.6 mm |
| Centre of mass (part frame) | (−17.84, 0.01, −49.36) mm |
| Build height cheek-down | 32.00 mm (160 layers at 0.2 mm) |
| Bed contact | 3 024 mm², full flat cheek |
| Dovetail wall | 3.85 mm, SF **8.06** cheek-down / 4.63 upright |

## Brand decisions

**Texture is `ribs`, not `knurl`.** Diamond knurl is visual noise; clean
transverse bands read as structural. Same grip security, less shouting.

**`panel_recess = 0`.** The stock architecture frames each tag in a recessed
panel. The brand brief asks for zero unnecessary noise, and the recess also
turns out to cost real DFM: a 26 × 60 mm face sitting 0.8 mm off the plate that
the bed-side cheek has to bridge across — on the exact surface the branding is
read from. Debossing straight into the flat cheek is both cleaner and better.

**Per-face tags.** `QISI` on the +Y cheek, `VERTEX-01` on the −Y cheek,
independently fitted and independently drafted.

## The draft angle, and why one face did not get 45°

| Face | Tag | Size | Draft asked | Draft applied |
|---|---|---|---|---|
| +Y (left) | `QISI` | 11.0 mm | 45° | **45°** |
| −Y (right) | `VERTEX-01` | 9.68 mm | 45° | **25°** |

A draft of D on a pocket of depth d widens every glyph by `d·tan(D)` **per
side** at the mouth, so it closes `2·d·tan(D)` of gap between neighbouring
letters. At 45° on a 0.8 mm pocket that is 1.60 mm. Measured on the actual
outlines:

- `QISI` — min inter-glyph gap 1.69 mm at 11 mm. Survives the full 45°.
- `VERTEX-01` — glyphs touch at 0.45 mm offset (29°) and the offset
  self-intersects by 0.60 mm (37°). Max safe is 0.35 mm ≈ 25°.

So the generator measures each string and backs the angle off rather than
shipping a tag fused into a blob. `safe_draft()` offsets the outlines, counts
the solids, and steps the angle down until the count is intact.

**This costs nothing functionally**, because the draft was never load-bearing
here. The stated reason for it was bridging, and in the cheek-down orientation
there is none to avoid: on the up-facing cheek the pocket is open to the sky,
and on the bed-side cheek the glyphs are enclosed voids 0.8 mm deep whose
widest span is a glyph stroke — 1–3 mm, which FDM bridges without noticing. The
orientation had already solved the problem the draft was requested for. What
the draft still buys is crisper release and a cleaner edge, and that is why it
is kept where it fits.

Implementation note: OCCT refuses tapered extrusion outright on any glyph with
an inner wire — Q, R, 0, every counter in the alphabet. The draft is therefore
cut as a staircase at the layer pitch, which is not an approximation anyone
pays for: the printer quantises the wall at the layer height regardless, so a
0.2 mm staircase and a true cone slice to identical G-code.

## Ergonomics

Interpreted "palm swell ~32 mm thickness" as **lateral cheek-to-cheek width**,
set via `grip_width = 32.0`. The alternative reading — 32 mm fore-aft depth —
would give a girth far below the power-grip band and contradict "adult medium",
so it was discarded. Grip height 94.7 mm comes from `hand_breadth = 96`.

Widening to 32 mm also thickens the dovetail wall from 2.85 to 3.85 mm, which
lifts the governing safety factor from 4.42 to **8.06**.

`dual_finger_groove` merges the index and middle registers into one R75 dish
2.6 mm deep spanning two finger pitches. Two fingers braced in a shared scallop
support each other against roll — the axis a launch pull actually twists about
— at the cost of locating each finger less precisely than its own groove would.

## Support: verified, not asserted

Treated as nice-to-have rather than a gate. It is met anyway, and it cost
nothing to meet — see `04`, "What the orientation actually constrains": in this
orientation only the cheek plane and enclosed void roofs are constrained, so
relaxing the requirement would not have bought any ergonomic freedom back.


Measured on the exported mesh in the cheek-down orientation:

| | |
|---|---|
| Bed contact (on-plate, down-facing) | 3 024 mm² |
| Sub-45° down-facing, off-bed | 1 828 mm² (8.6 %) |

None of that remainder is support work:

- **~1 270 mm², first 3 mm** — the convex roll-off of the bottom corner radius.
  Self-supporting; no slicer generates support for it. The cost is a little
  elephant-foot, which is the price of a filleted grip edge rather than a
  chamfered one, and the right trade for a part the hand wraps.
- **~540 mm², mid-height** — the ballast socket roof, a **7.7 mm flat bridge by
  design** (the hexagon is oriented flats-to-cheeks precisely so this is a flat
  bridge approached by 60° walls).
- **~19 mm²** — the tournament-lock bore roof, a 4.2 mm bridge.

**0 % support confirmed.** This check found a real architecture bug on the way
through — see `04`, "The flat cheek has to actually be flat".

## DFM verdict and the profile that was chosen

The brief's two gates — 45–52 g at 1.24 g/cm³, under 75 min — cannot both be
met on a 0.4 mm nozzle at 60–80 mm/s, for any infill and any geometry:

- The lightest in-window part (45 g at 1.24) is 36 290 mm³ of extrudate.
- Laying that down in 75 min needs **8.06 mm³/s sustained**.
- 0.4 mm @ 0.20 mm, 70 mm/s → 4.41 mm³/s — **short**.
- 0.4 mm @ 0.30 mm, 70 mm/s → 6.62 mm³/s — **short**.
- 0.6 mm @ 0.30 mm, 70 mm/s → 8.25 mm³/s — **reaches it**.

Geometry and slicer settings are independent levers, so the exported files do
not change with any row below — only the profile does.

**Quote shell thickness in millimetres, never in perimeter count.** A perimeter
is a nozzle-width wide, so "3 perimeters" means 1.26 mm on a 0.4 mm nozzle and
1.89 mm on a 0.6 mm one. Mixing the two is how an earlier version of this table
recommended a 50.8 g / 83 min profile that would actually have printed at
66.2 g / 108 min.

| Nozzle / layer | Perims | Shell | Material | Mass @1.24 | Time @70 mm/s |
|---|---|---|---|---|---|
| 0.4 / 0.20 | 4 | 1.68 mm | 54 317 mm³ | 67.4 g | 205 min |
| 0.4 / 0.20 | 3 | 1.26 mm | 42 072 mm³ | 52.2 g | 159 min |
| 0.4 / 0.20 | 2 | 0.84 mm | 40 091 mm³ | 49.7 g | 152 min |
| 0.6 / 0.30 | 4 | 2.52 mm | 64 745 mm³ | 80.3 g | 131 min |
| 0.6 / 0.30 | 3 | 1.89 mm | 53 408 mm³ | 66.2 g | 108 min |
| **0.6 / 0.30** | **2** | **1.26 mm** | **42 072 mm³** | **52.2 g** | **85 min** |

(20 % infill rows omitted except the top one; 15 % elsewhere.)

### Chosen profile

**0.6 mm nozzle, 0.30 mm layer, 2 perimeters (1.26 mm shell), 15 % gyroid,
70 mm/s** — 52.2 g at 1.24 g/cm³ (53.4 g in PETG at 1.27), ~85 min.

Mass lands 0.2 g over the window's top and time about 10 min over the target,
both accepted. Note that 2 perimeters at 0.6 mm is **the same 1.26 mm of shell**
as 3 perimeters at 0.4 mm — the wall is not being thinned to buy the time, only
laid down in fewer, fatter passes.

### Time is sensitive to the hotend, not the motion system

At 0.6 mm and 0.30 mm the nozzle is *asked* for 0.63 × 0.30 × 70 = 13.2 mm³/s,
which is above what most stock hotends sustain in PETG. The flow ceiling is
what sets the time, so the estimate moves a lot with the machine:

| Hotend sustained flow | Time |
|---|---|
| 8 mm³/s (stock bed-slinger) | 117 min |
| 9 mm³/s | 104 min |
| **11 mm³/s (assumed)** | **85 min** |
| 13.2 mm³/s (high-flow, no ceiling) | 71 min |

The 85 min figure assumes 11 mm³/s. On a stock library printer budget closer to
**105–120 min**, and slow the print speed rather than let the extruder skip.

## Files

```
cad/vertex/export/grip_qisi_edition.step    B-Rep, manufacturing record
cad/vertex/export/grip_qisi_edition.stl     0.02 mm chord tolerance
cad/vertex/export/grip_qisi_edition.json    manifest: params, mass, balance, warnings
cad/vertex/export/rail_gauge.{step,stl}     fit coupon, 32 mm body
```

The interface is still **UNVERIFIED placeholder geometry** (`03`). These files
were exported with `--exact-name`, so they do not carry the `_PROTOTYPE` stamp
the generator adds by default — the banner and the manifest warning still do.
They will not reliably fit a real launcher until somebody measures one.
