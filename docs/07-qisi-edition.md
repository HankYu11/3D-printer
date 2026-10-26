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

## DFM verdict: the mass and time gates conflict

| | Target | At 4 perim / 20 % infill, 0.4 mm @ 0.2 mm, 70 mm/s |
|---|---|---|
| Mass @ 1.24 g/cm³ | 45–52 g | **65.7 g** |
| Print time | < 75 min | **200 min** |

Geometry and slicer settings are independent levers, so the exported files do
not change — only the profile does:

| Profile | Material | Mass @1.24 | 0.4/0.2 | 0.6/0.3 |
|---|---|---|---|---|
| 4 perim / 20 % | 52 963 mm³ | 65.7 g | 200 min | 107 min |
| 3 perim / 20 % | 46 188 mm³ | 57.3 g | 175 min | 93 min |
| **3 perim / 15 %** | 40 992 mm³ | **50.8 g** ✓ | 155 min | 83 min |
| **2 perim / 20 %** | 39 414 mm³ | **48.9 g** ✓ | 149 min | 80 min |
| 2 perim / 15 % | 33 794 mm³ | 41.9 g | 128 min | **68 min** ✓ |

**No profile satisfies both gates at once**, and on a 0.4 mm nozzle the time
gate is not reachable at all. The arithmetic is short:

- The lightest in-window part (45 g at 1.24) is 36 290 mm³ of extrudate.
- Laying that down in 75 min needs **8.06 mm³/s sustained**.
- 0.4 mm @ 0.20 mm, 70 mm/s → 4.41 mm³/s — **short**.
- 0.4 mm @ 0.30 mm, 70 mm/s → 6.62 mm³/s — **short**.
- 0.6 mm @ 0.30 mm, 70 mm/s → 8.25 mm³/s — **OK**.

So a 45 g part cannot print in 75 minutes on a 0.4 mm nozzle at 60–80 mm/s, at
any infill, for any geometry. The gate needs a 0.6 mm nozzle.

The gates are also sized for roughly the *stock* VERTEX-1, not this enlarged
body. The 95 × 32 mm brief adds about 23 % volume over the 90 × 30 mm standard.

**Recommended resolution**, in order:

1. **0.6 mm nozzle @ 0.3 mm, 3 perimeters / 15 % infill** — 50.8 g, 83 min.
   Misses 75 min by 8, hits the mass window, keeps a sound shell. Closest
   honest fit to the brief.
2. **Accept ~105 min** on the library's 0.4 mm nozzle at 4 perimeters / 15 %.
3. **Drop to the 30 mm standard body** if both gates are hard requirements; at
   3 perim / 15 % on a 0.6 mm nozzle it lands near 45 g and 73 min.

Dropping to 2 perimeters is what the table says fits, and it is not
recommended: the shell is the structure in this part, and the dovetail wall's
safety factor assumes solid material.

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
