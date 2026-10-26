# 06 — The On-Demand Manufacturing Pipeline

The grip is the first product. The pipeline is the actual asset, and this part
was chosen partly because it exercises every stage of one: per-customer fit,
per-customer text, a hardware interface that needs calibration, a physical
envelope to respect, and a structural claim to stand behind.

## Order to part

```
  customer input ──> validate ──> generate ──> slice ──> print ──> QC ──> ship
   hand breadth      Params       CadQuery     profile   cheek    gauge   manifest
   rake, tag         .validate()  STEP+STL     from 04   down     + fit   + QR
   nuts, material    pure Python  + manifest                              
```

**1. Capture.** Hand breadth from a ruler-and-phone photo; rake from three
preference options described by technique, not by angle; the Player ID; nut
count. Four questions, no CAD literacy.

**2. Validate — before any CAD runs.** `Params.validate()` is pure Python with
no OCCT dependency, so the configurator runs it live in the browser and the
customer sees girth, length, mass and balance update as they drag a slider. A
bad order is refused in milliseconds, not after a build.

**3. Generate.** ~24 s per order, single-threaded. A printer occupied for an
hour is the constraint; CAD time is noise. Emits STEP (manufacturing record),
STL (slicer) and the manifest.

**4. Slice.** Fixed profile from `04`. The orientation is fixed by design, so
there is no per-order slicing judgement to get wrong.

**5. Print.** 150 layers, ~1.5 h, no support, full-cheek bed contact. The squat
geometry is what makes an unattended farm realistic.

**6. QC.** Fit against the reference launcher; confirm the leaf preloads; weigh
and compare to the manifest estimate. A weight outside tolerance means a flow or
filament problem — the manifest turns every part into its own check.

**7. Ship.** Manifest archived against the order digest. Re-order, warranty and
"print me another in ASA" all resolve to re-running one JSON file.

## Calibration as a standing process

Per-printer, per-material, not per-order (`03`):

- New printer, new nozzle, new filament brand → print the gauge, record the
  clearance in that machine's profile.
- Monthly → re-run the gauge on each machine. Drift means a worn nozzle.

This is the difference between a design that fits on the printer it was made on
and a product that fits on a fleet.

## Where the AI leverage actually is

Not in generating the geometry — that is deterministic code, and it should stay
that way. A generative model that emits a slightly different grip each run is a
liability when the output is a load-bearing part someone yanks on.

The leverage is at the edges, where judgement is needed and the cost of being
wrong is bounded:

- **Intake**: turning "my hands are kinda big and I shoot low and flat" into
  `hand_breadth=96, rake_deg=14`, with the reasoning shown so the customer can
  disagree.
- **Fit diagnosis**: "it rocks slightly front-to-back" → that is the leaf, not
  the clearance; here is what to check.
- **Design iteration**: proposing `PROFILE` table changes from returns and
  review text, reviewed as a diff by a human before anything ships.
- **QC triage**: reading printer telemetry and manifest deltas to spot a
  drifting machine before it makes scrap.

Each of these has a human or a hard validator between the model and the
customer. The geometry stays deterministic, parameterised and testable.

## What has to be true before selling one

In order. Nothing below the first line matters until the first line is done.

1. **Measure the launcher.** `03`. Everything is a prototype until then, and the
   repo says so on every run.
2. **Calibrate each printer.** Gauge on every machine in the fleet.
3. **Validate the structural claim.** The dovetail wall safety factor of 4.42 is
   a hand calculation on nominal geometry. Pull-test printed parts to failure and
   confirm the mode is the wall, as predicted. If it fails somewhere else, the
   model is wrong and needs correcting before it is quoted to anyone.
4. **Fit-test the ergonomics.** The anthropometric mapping is fitted to published
   pistol-grip data, not to bladers. Put the three presets in real hands across
   the 80–100 mm range and correct the coefficients.
5. **Weigh a launcher.** `LAUNCHER_PROPS_VERIFIED` is `False`; until it is true
   every balance number is directional and labelled as such.
6. **Cycle-test the interface.** 500 mount/dismount cycles; confirm the leaf
   still preloads and the dovetail has not worn loose.

## Roadmap

**Near** — measured interface; per-printer calibration; AMS two-colour inlay in
the existing cheek panel; team insignia from customer SVG; serialised unit ID.

**Then** — the **ballast heel spur**, the one change that would let ballast
genuinely counterbalance rather than only lower the CoG (`02` §1.7). It needs
on-body testing first.

**Later** — **NEXUS**, the modular platform from `01`. It becomes attractive
precisely when the interface is measured and proven, because the dovetail the
shoe already uses is the joint a module system would be built from. Building it
before the interface is trustworthy would stack tolerance on an unknown.
