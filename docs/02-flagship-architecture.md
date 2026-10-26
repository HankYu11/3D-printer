# 02 — VERTEX-1 Flagship Architecture

Every number below is produced by `cad/vertex/`, not quoted from a sketch.
Regenerate with `python -m vertex.build --preset presets/adult_mid.json`.

As-built reference unit (hand breadth 90 mm, rake 18°, knurl, 3 nuts):

| | |
|---|---|
| Solid volume | 104 955 mm³ |
| Bounding box | 81.4 × 30.0 × 100.3 mm |
| Estimated printed mass, PETG | **54.7 g** (envelope 40–75 g) |
| Estimated print time | **1.45 h** (target < 3 h) |
| Grip circumference | 132.7 mm |
| Assembly mass with launcher | 146.6 g |
| Generator runtime | ~25 s |

---

## 1. Structural anatomy

Eight features, from the launcher down.

### 1.1 Interface Shoe — `interface.py`
34 × 30 × 10.15 mm block containing a female dovetail that swallows the
launcher's mounting boss. Mating face is the part origin, z = 0.

Three things do the work, and only one of them is a tolerance:

- **Dovetail flanks at 22.9°** — the launcher cannot lift straight out.
- **1.2° longitudinal wedge taper** — the pocket narrows toward the closed end,
  so the launcher *jams tight* as it slides home rather than relying on a
  clearance number being right.
- **A compliant floor leaf** — a printed cantilever, 16 × 8 × 1.0 mm, standing
  0.8 mm proud. The launcher squashes it; it pushes the boss up into the flanks
  and takes out vertical slack whatever the clearance did.

Taper plus leaf is what delivers zero wobble across the ±0.15 mm spread you get
between printers, filaments and humidity. Clearance alone never could, and a
design that depends on hitting a clearance target is a design that wobbles on
somebody else's printer. See `03`.

Also: an M3 brass heat-set insert in the shoe wall for the **Tournament Lock**,
a nylon-tipped grub screw that takes out any last residual play for match play
without marring the launcher.

### 1.2 Blend Collar
A 15 mm lofted flare from the shoe footprint down onto the stem. This replaces
a fillet **deliberately** — measured on this part, OCCT's fillet fails at every
radius from 6.0 down to 1.5 mm, because the edge band at the neck picks up
texture grooves and dovetail edges along with the junction. A fillet that fails
on some fraction of orders is a pipeline outage. The collar is deterministic,
runs in 0.02 s, and lets us state the blend profile instead of accepting
whatever OCCT tolerates.

### 1.3 Recoil Shelf
Forward ledge projecting 9 mm beyond the shoe's front face, 7 mm thick at the
root tapering to 4.2 mm, bearing face rising 8° toward the front.

This is the feature that converts downward and forward recoil into a load the
index finger's skeleton carries, instead of something grip friction has to
hold. The 8° rise matters: it angles the reaction so it pushes the hand *into*
the grip rather than letting it creep forward off the ledge under repeated
pulls. The forward taper also keeps the underside self-supporting.

### 1.4 Tang pocket
Not a boss. Raking the grip aft already carries the upper backstrap behind the
shoe, and the blend collar fills the corner — that pocket *is* the beavertail,
and the web of the hand seats into it. It sets hand height identically every
launch, which is the single biggest contributor to angular repeatability.
Adding a separate tang boss would only duplicate geometry the rake gives free.

### 1.5 Palm ergonomics — the cross-section rule
**Lateral width is constant at 30.0 mm everywhere. All ergonomic volume lives
in the fore-aft depth.**

This one decision pays three ways at once, which is why it is the backbone of
the design rather than a detail:

1. Flat parallel cheeks mean the part lies on a cheek and prints **support-free**
   — the walls stay vertical all the way up (`04`). This only holds if the
   cheeks are genuinely coplanar: the profile table's lateral scale is pinned
   to 1.0 at every station and asserted at import, because an earlier revision
   varied it and silently destroyed the flat bed face (`04`).
2. That same orientation puts the structural load path **in-plane** instead of
   across layer bonds (`04`).
3. The flat cheek becomes the **customisation canvas** (1.8).

It is also simply correct ergonomics: 1911 and Glock grips are near-constant
width with the swell in the front and back strap. Depth, not width, is what
fills a hand.

### 1.6 Finger registration
Index scallop R12 × 2.2 mm deep, directly under the recoil shelf; three
further grooves R9 × 1.5 mm at the computed finger pitch.

Depths are deliberately shallow. Deep finger grooves lock a hand into exactly
one position and fight anyone whose fingers sit a few millimetres off the
model. These **register without trapping** — the hand finds the same place every
time, which is repeatability, rather than being clamped into one place, which
is a hot spot and a blister by round six.

### 1.7 Ballast Bay — and an honest correction
Blind hex socket at the butt, 13.35 mm across flats × 46 mm, taking up to six
DIN 934 **M8** nuts (5.73 g each, computed). Closed by a printed cap on one M3
heat-set insert, with a compliant pad so a partial stack cannot rattle.

The hexagon is oriented **flats-to-cheeks**. Printed on its side the socket roof
is then a flat 7.7 mm bridge approached by 60° walls — self-supporting, so
there is no internal support to dig out of a blind pocket.

Measured effect across the tuning range:

| nuts | ballast | assembly | **CoG above hand** | CoG height | wrist moment | inertia |
|---|---|---|---|---|---|---|
| 0 | 0.0 g | 129.4 g | **50.5 mm** | +0.8 mm | +45.5 N·mm | 0.00211 |
| 3 | 17.2 g | 146.6 g | **40.4 mm** | −8.9 mm | +47.3 N·mm | 0.00213 |
| 6 | 34.4 g | 163.8 g | **34.5 mm** | −14.6 mm | +50.2 N·mm | 0.00218 |

Read that table honestly, because it corrects two things the category routinely
claims:

- **What ballast really does here**: it pulls the centre of gravity down the
  grip and into the hand. The CoG sits 50.5 mm above the hand's centre of
  pressure bare, 34.5 mm fully loaded — a **32 % reduction in the lever the hand
  has to stabilise**, and a 15.4 mm drop in absolute CoG height. That is the
  "planted" feel, and it is real and worth selling.
- **What it does not do**: it does not counterbalance the launcher, and it does
  not meaningfully damp tremor. Ballast carried *inside* the butt sits slightly
  **forward** of the wrist, so the static holding torque actually rises slightly
  (+45.5 → +50.2 N·mm) and inertia about the wrist gains only 3 %. Anyone
  claiming otherwise for this geometry is selling something.

Counterbalancing would need the mass **behind** the wrist — a heel spur below
and aft of the butt. That is a genuine option and it is in `01` as deferred, not
forgotten: it is a protrusion, and it needs on-body testing before it earns its
place on a tournament part.

The same reasoning kills the usual "resists launch torque" pitch. Resisting the
ripcord's reaction torque is a **stiffness** problem — in the quasi-static limit
the steady angular error is torque divided by grip stiffness, with mass nowhere
in the expression. It is solved by leverage, hand coupling and a tight
interface. Not by adding grams.

### 1.8 Modular Customisation Zone
Recessed panel 56 × 24 × 0.8 mm on each cheek; Player ID debossed 0.6 mm
inside it, running **along** the grip axis, auto-fitted so an arbitrary
customer string can never run off the edge of the part.

This zone exists for free. The flat cheek is already mandated by the print
orientation (1.5), so the branding surface costs no extra material, no extra
print time and no structure. The bed-side cheek additionally comes off a smooth
build plate with a near-injection-moulded finish.

Roadmap, same zone, no geometry change: second-material inlay on an AMS/MMU
printer, team insignia from customer SVG, and a serialised unit ID in the butt.

---

## 2. Dimensional schedule

Driven by **hand breadth** — palm width across the knuckles, the one hand
dimension a layperson can self-measure accurately with a ruler and a phone.

| Parameter | 80 mm hand | 90 mm | 100 mm | Rule |
|---|---|---|---|---|
| Grip circumference | 124.5 mm | 132.7 mm | 140.8 mm | derived |
| Fore-aft depth | 40.0 mm | 44.5 mm | 49.0 mm | `40 + 0.45·Δ` |
| Lateral width | 30.0 mm | 30.0 mm | 30.0 mm | **constant** |
| Corner radius | 9.0 mm | 9.5 mm | 10.0 mm | `9 + 0.05·Δ` |
| Finger pitch | 16.4 mm | 18.4 mm | 20.5 mm | `0.205 × breadth` |
| Grip length | 81.6 mm | 89.8 mm | 98.0 mm | `4·pitch + 16` |
| Printed mass | 46.4 g | 53.3 g | 60.7 g | measured |
| Print time | 1.23 h | 1.41 h | 1.61 h | estimated |

The 124.5–140.8 mm girth band brackets a Glock 19 (127 mm) at the small end and
a full-size 1911 (~142 mm) at the large end — the span pistol-grip ergonomics
treats as the power-grip optimum for these hands.

**Rake** is independent of hand size, because it is a technique preference, not
an anthropometric one: 10–32°, default 18°. See `01`.

---

## 3. Load path and what actually governs

The pull applies a lateral reaction at the launcher; the hand resists it ~35 mm
below. Taking a deliberately pessimistic 120 N:

| Feature | Stress | SF (cheek-down) | SF (upright) |
|---|---|---|---|
| Neck in bending | 1.27 MPa | **37.1** | 21.3 |
| **Dovetail shoe wall** | **10.64 MPa** | **4.42** | **2.54** |

**The neck is not the limiting feature, and this was worth finding out.** Sizing
the grip for a human hand has already over-sized it for strength by more than an
order of magnitude. Design attention spent thickening the neck would be wasted.

What governs is the **shoe side wall**. A 150 N separation force on 22.9° flanks
resolves into 177 N splaying each **2.85 mm** wall outward, and that wall is the
thinnest loaded structure in the part — 8.4× more stressed than the neck.

The wall thickness is *derived from the grip width*, not a constant: the shoe is
built as wide as the grip, so `(grip_width − boss_width − 2·clearance) / 2`. An
earlier revision hard-coded 3.0 mm here and reported a safety factor of 4.89;
the real wall on a 30 mm grip is 2.85 mm and the real factor is 4.42. Widening
the grip thickens the wall — the Qisi edition's 32 mm body gives a 3.85 mm wall
and a factor of 8.06.

It also carries the orientation argument in one number: **4.42 printed
cheek-down versus 2.54 printed upright**. Same geometry, same material; the
difference is purely whether the load runs along the extrusions or across the
layer bonds. `04` covers why.
