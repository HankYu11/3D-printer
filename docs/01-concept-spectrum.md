# 01 — Concept Spectrum

## The thesis the product is built on

A launcher grip is sold as comfort. That is not where the competitive value is.

In Beyblade X the launch *angle* and the consistency of the pull decide whether
a bey catches the stadium's rail line. The bare winder launcher is small enough
that an adult gets two and a half fingers on it, and every launch places the
hand slightly differently. A different hand position is a different wrist angle,
a different wrist angle is a different entry angle, and that variance is lost
matches.

So the product is not a comfort accessory that happens to look good. It is an
**angular repeatability fixture**: a part whose job is to make launch *n+1*
identical to launch *n*. Comfort and the tactical look are what make a blader
want it; repeatability is what makes them keep it.

Three consequences run through every decision downstream:

- Features that **register** the hand (index ledge, finger scallops, tang
  pocket) matter more than features that merely cushion it.
- **Zero wobble at the interface** is not a quality nicety. A grip that moves
  1° on the launcher has destroyed the thing the product exists to sell.
- Per-player **fit** matters, because a grip sized for someone else re-introduces
  exactly the variance it was supposed to remove. This is what justifies
  made-to-order manufacturing rather than three moulded sizes.

---

## Archetype A — VERTEX (combat pistol, near-axial)

**Rake 10–16°** off the launch axis. The grip hangs almost directly beneath the
launcher, fist close under the launch axis, full four-finger wrap.

- **Grip style**: full power grip, hand high under the shoe, index hooked on the
  recoil shelf.
- **Technique served**: hard full-draw power launches — the blader who wants
  maximum RPM and a flat, committed entry.
- **Advantage**: the string's reaction passes almost straight down the forearm,
  so the hand resists it in its strongest direction instead of fighting a
  twisting couple. Longest grip means the most finger-contact area and the
  largest registration surface. Highest "tactical instrument" factor.
- **Risk**: a near-axial grip puts the hand far below the launcher, so any
  interface slack is amplified into a large angular error at the bey. It
  demands the best interface of the three.

## Archetype B — DELTA (low-profile raked)

**Rake 26–32°**. Grip swept aft, hand sitting lower and further back, shorter
effective moment arm from the interface to the hand.

- **Grip style**: relaxed, wrist closer to neutral at low hold positions.
- **Technique served**: control and bank-angle launches — sliding shoots and
  precise entry angles rather than maximum power.
- **Advantage**: the shortest lever to the interface, so interface slack is
  amplified least and the shoe sees the lowest bending moment. Lightest and
  fastest to print. Least intimidating for a younger blader.
- **Risk**: less leverage against the twisting reaction, and it looks much more
  like a stock accessory — weaker on the pride-of-ownership axis the brand
  depends on.

## Archetype C — NEXUS (modular skeleton)

A spine carrying a dovetail accessory rail; grip modules, palm swells and
ballast pods clip on. One chassis, many configurations.

- **Grip style**: whatever module is fitted.
- **Technique served**: the tuner. One purchase, continuous reconfiguration.
- **Advantage**: the strongest business story. One chassis SKU covers every hand
  size, and modules are a recurring-revenue path. This is the platform.
- **Risk — and it is disqualifying for an MVP**: every joint is a compliance.
  The whole product exists to eliminate play between the hand and the bey, and
  this archetype inserts two or three extra tolerance stacks directly into that
  load path. It also multiplies print time, part count, assembly labour and
  failure modes at precisely the moment the business can least absorb them.

---

## Selection

| | VERTEX (A) | DELTA (B) | NEXUS (C) |
|---|---|---|---|
| Repeatability (the core promise) | high | medium | **low — joints add play** |
| Interface risk | highest lever | lowest lever | highest, multiplied |
| Desirability / "cool factor" | high | low | high |
| Print time, one part | ~1.1 h | ~0.9 h | 2.5 h+, multi-part |
| Parts to make and assemble | 1 (+cap) | 1 (+cap) | 4–7 |
| Business upside | product | product | **platform** |

**A and B are not two products.** Once the geometry is parametric, the only
real difference between them is the rake angle and the girth — both already
continuous inputs to the generator. Shipping them as separate SKUs would be
shipping the same part twice.

So the MVP is **the A↔B continuum as a single part**: `VERTEX-1`, rake exposed
as a customer parameter over the validated 10–32° range, default 18°. A blader
who wants the combat-pistol feel orders 12°; one who wants the low raked feel
orders 30°. Same generator, same print profile, same envelope — verified across
the whole range in `cad/vertex/validate.py`.

**NEXUS is the roadmap, not the MVP.** It becomes attractive once the interface
is measured and proven, because at that point the dovetail the shoe already uses
is exactly the joint a module system would be built from. Building it before the
interface is trustworthy would be stacking tolerance on top of an unknown.

What is deliberately *not* in the MVP, and why:

- **No modular joints.** They fight the core promise. (Roadmap: NEXUS.)
- **No ballast heel spur.** It is the only way in-grip ballast could genuinely
  counterbalance the launcher — see `02` — but it is a protrusion that needs real
  on-body testing before it earns its place.
- **No left/right-specific shells.** The part is symmetric about its cheek plane,
  so it is ambidextrous for free. A handed version would double the catalogue to
  serve a preference nobody has yet asked for.
