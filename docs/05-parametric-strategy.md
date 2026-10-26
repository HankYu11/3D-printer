# 05 — Parametric Strategy: the Code-to-CAD Bridge

## Why CadQuery

| | CadQuery | OpenSCAD | Mesh / implicit |
|---|---|---|---|
| Output | **B-Rep, STEP** | CSG → mesh | mesh |
| Downstream CAD edits | yes | no | no |
| Mass properties | exact | none | approximate |
| Lofts, variable sections | native | `hull()` approximation | yes |
| Ecosystem reach | Python | huge in the maker scene | niche |

Made-to-order manufacturing needs **STEP**: a real B-Rep that a contract
manufacturer can open, that mass properties can be computed from, and that can be
edited six months from now without re-deriving the model. CadQuery is the
primary implementation and the one the pipeline runs.

`cad/openscad/vertex_grip.scad` is a parallel port, for the modding community
that lives on OpenSCAD customisers. It is marked clearly: **OpenSCAD could not be
installed in the environment this was authored in, so unlike the CadQuery model
it has never been executed.** It is a reviewed transcription, not a tested build;
render it and compare against the reference STL before trusting it. Saying that
plainly costs less than someone discovering it on a print bed.

## Module structure

```
cad/vertex/
  params.py      all dimensions; three tiers; validation
  interface.py   GROUND TRUTH boundary -- the only launcher geometry anywhere
  grip.py        stem loft, ergonomics, ballast, texture, customisation
  build.py       assembly order, export, manifest
  analysis.py    mass, balance, structure -- pure Python, no CAD dependency
  validate.py    envelope sweep; the regression test
cad/calibration/
  rail_gauge.py  fit coupon, built from the SAME build_shoe()
```

Four boundaries are load-bearing:

**`interface.py` is a firewall.** The one unverified thing in the project is
sealed behind one module (`03`). Nothing downstream reasons about the launcher.

**`analysis.py` has no CAD dependency.** Mass, balance and structural checks are
pure Python, so the order validator and the configurator's live fit preview can
run them without pulling in OCCT. Only the final cut needs CadQuery.

**`params.py` tiers its parameters.** CUSTOMER (safe to vary across the
published range), ENGINEERING (changing one requires a reprint and a retest) and
GROUND TRUTH (measured off hardware). The tier tells you what a change costs.

**`validate.py` asserts the envelope separately from the geometry.** The
generator will happily produce a watertight solid that is the wrong size, too
heavy to sell or too weak to pull on. Validity is not correctness.

## Where customer parameters inject

```python
@dataclass
class Params:
    hand_breadth: float = 90.0   # 80-100 mm  -> girth, length, finger pitch
    rake_deg:     float = 18.0   # 10-32 deg  -> grip axis vs launch axis
    player_id:    str   = ""     # <=10 chars -> debossed both cheeks
    texture:      str   = "knurl"
    ballast_nuts: int   = 3      # 0-6        -> balance, reported
    material:     str   = "PETG"
```

Hand breadth is the one real anthropometric input: palm width across the
knuckles, chosen because it is the dimension a layperson can self-measure
accurately with a ruler and a phone, and it tracks the grip circumference that
maximises power-grip force. Everything dimensional derives from it:

```python
grip_depth   = 40.0 + 0.45 * (hand_breadth - 80)      # 40.0 .. 49.0
corner_r     = 9.0  + 0.05 * (hand_breadth - 80)      #  9.0 .. 10.0
finger_pitch = 0.205 * hand_breadth                   # 16.4 .. 20.5
grip_length  = 4 * finger_pitch + 16                  # 81.6 .. 98.0
grip_width   = 30.0                                   # CONSTANT -- see 04
```

## The profile table

The grip's shape is one data table, not a thousand lines of modelling:

```python
PROFILE = [
    Station(0.00, 1.000, 0.780, 0.80,  0.0),   # neck pad
    Station(0.06, 1.000, 0.860, 0.90,  0.6),   # tang zone
    Station(0.20, 1.000, 0.970, 1.00,  1.2),   # index register
    Station(0.40, 1.000, 1.000, 1.00,  1.0),   # middle -- palm swell
    Station(0.62, 1.000, 0.960, 1.00,  0.0),   # ring
    Station(0.82, 0.987, 0.880, 0.95, -1.4),   # little
    Station(0.94, 1.013, 0.900, 0.90, -2.6),   # butt flare
    Station(1.00, 0.947, 0.840, 0.80, -3.2),   # butt face
]
```

Fractions, not millimetres, so the whole family scales from one table. An
ergonomics change is a table edit, reviewable as a diff. Interpolating the same
table seats the finger cuts on the real frontstrap surface at any size, which
is why the scallops stay correct across the range instead of drifting off the
curve at the extremes.

## Assembly order is a safety property

```python
part = shoe.block.union(grip).union(collar).union(shelf).union(leaf)
part = part.cut(shoe.cutter)      # dovetail pocket cut LAST
```

The dovetail is cut **after** everything is blended in. It is structurally
impossible for a blend, a future grip revision or a stray flare to intrude into
the mating geometry. The interface cannot be broken from downstream — a property
of the build order, not of anyone remembering to check.

## Four traps, documented in the source

These cost real debugging time and each one fails *silently*. They are commented
at the site, not just here, because the next person will hit them.

**1. `Sketch.rect(w, d)` axis order.** `rect()` takes (X, Y). Passing width
before depth builds the entire grip rotated 90° about its own axis. It still
lofts, still reports a plausible volume, still passes a validity check — and
every surface-referenced cutter downstream silently misses.

**2. `Workplane.cut()` no-ops on a Compound.** Handed a Workplane wrapping a
Compound it returns the base **unchanged, with no error**. A missing cut looks
exactly like a successful one. `Shape.cut(*solids)` is the call that subtracts.

**3. `clean=True` (the default) does not terminate here.** Every boolean in this
part is sub-second; a single default-clean cut ran for minutes without
returning. Coplanar-face merging does not cope with this many lofted and
textured faces. Every boolean passes `clean=False`; the solids come out valid
and watertight regardless.

**4. Fillets fail; lofted collars do not.** OCCT's fillet failed at every radius
from 6.0 down to 1.5 mm at the neck. A fillet that fails on some fraction of
orders is a pipeline outage. The lofted collar runs in 0.02 s, every time.

**Groove cutter sign.** Not a library trap, just arithmetic worth stating: to cut
`depth` into a surface the cutter's centre sits at `surface + r − depth`,
**outside** the part. Getting the sign backwards either removes half the grip or
nothing at all, depending on the radius.

## Guardrails on customer input

Customers type arbitrary strings and pick arbitrary numbers, so the generator
treats input as hostile:

- `Params.validate()` refuses out-of-range hand breadth, rake, tag length,
  non-alphanumeric tags, nut counts, and any combination leaving < 2.4 mm of
  cheek wall. `build()` raises before cutting geometry.
- Player ID is **auto-fitted**: the glyph run is measured and the size stepped
  down until it fits the panel. A ten-W tag shrinks to 47.1 mm inside a 56 mm
  panel rather than running off the side of the part.
- The build asserts a single valid solid and fails loudly otherwise.

## Manifest

Every order emits `.step`, `.stl` and a `.json` manifest carrying the full
parameter set, a 12-char order digest, geometry, mass and balance, structural
margins, interface provenance and every warning. It is what makes this a
pipeline rather than a model: a part that comes off a printer in six months
traces back to the exact inputs that generated it.

```json
{ "order_digest": "a3f2c81d9e04",
  "print_estimate": { "estimated_mass_g": 54.4, "estimated_hours": 1.08,
                      "note": "first-order; the slicer is authoritative" },
  "balance":   { "cog_overhang_above_hand_mm": 40.4, "wrist_moment_nmm": 47.3 },
  "structure": { "governing_feature": "dovetail_wall" },
  "interface": { "provenance": "UNVERIFIED-NOMINAL" },
  "warnings":  ["Launcher interface geometry is UNVERIFIED placeholder data..."] }
```
