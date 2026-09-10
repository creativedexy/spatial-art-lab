# 004 — the campus at a hundred metres

**For:** the local session on the Mac, on the free Codex subscription.
**Cost:** £0. No paid call, no video.
**Inputs:** [`close-2045/campus-cluster.png`](close-2045/), with
`campus-cluster.json` and `campus-cluster-anchors.json`.

## What changed since this plate last failed

It failed the interesting-imagery rule, and correctly: at a hundred metres the
campus was twenty blank 38 × 17 m slabs standing on grass, and no description
was going to rescue that. The map's extrusions are honest about *where* and say
nothing about *what*.

**The plate now has real buildings in it.** Every campus footprint carries a
Meshy type model — one bar building modelled once, placed twenty times, scaled
to each footprint and turned to its long axis — so the plate shows four banded
storeys, a sedum roof and a small PV array rather than a box. The National
Cyber Innovation Centre stands in the courtyard of the campus field at
(−138, −190), with its meadow roof running to the ground, chosen by rule:

> the campus field with frontage on a named route (within 150 m of its centre)
> and, of those, the one nearest GCHQ — 364 m from the ring and 120 m off the
> Cheltenham Circular Footpath.

## The rule, answered

| must show | in this frame |
|---|---|
| place of interest | the innovation campus, with the NCIC's meadow roof beyond it |
| buildings | 40 blocks in frame — 7 campus, 30 homes, 3 glasshouses — the nearest 106 m away and filling the middle of the picture |
| people | at 92 m the figures are legible: people on the streets between the blocks, in the courtyards, cycling on the new routes, at the glazed ground floors |

## The locks

At the plate's 1280 × 720. Everything not listed is materials, light and life.

| feature | surveyed position | note |
|---|---|---|
| horizon | y = **100** | sky is the top 14 % only |
| **the development** | x 55–1280, y 145–518 | 40 blocks; nearest 106 m |
| nearest campus block | centre x 410, base y 518, roof y 395 | 17 m — five storeys |
| second campus block | centre x 484, base y 408, roof y 316 | 17 m |
| the brook | (1261,264) → (5,276) | 238 m; narrow, in wet meadow |
| hedge | (1056,184) → (465,214) | 399 m |
| existing Cheltenham | rooflines top out at y = **143**, bases y = 160 | 365 m — red brick, grey slate, red clay tile |

## What the models already say, and what they do not

The type models carry the architecture, so the prompt does not have to invent
it: **four storeys, strong horizontal banding, deep window reveals, a planted
sedum roof, a small PV array, pale buff render and timber.** Keep all of it.

They have one known defect, and it is in this frame. Meshy rebuilt the glazed
ground floor of the source drawing as transparency, so the base of each block
has jagged gaps in it. **Draw the ground floor as continuous dark reflective
glazing with a solid head and cill** — that is a repair, not an invention, and
it is the one thing here where the plate is wrong rather than merely plain.

## Inspect, then correct once

1. the blocks re-proportioned — they are 38 × 17 m on plan and four storeys, and
   a generator that likes towers will stretch them
2. the NCIC's meadow roof turned into a green wall, a lawn, or a separate hill;
   it is one continuous planted roof plane running from the high end to the
   ground
3. buildings added to the open fields, or the development brought forward
4. no people, which fails the rule however good the frame is

## What to write back

A `## Result` as usual: passes, residual drift against the numbers above, and
where the plate is still the limiting factor. The glazing defect is already
known — what is worth reporting is anything *else* the models get wrong at this
distance, because that is what decides whether the next type is worth its
credits.

## Result

**10 Sep 2026, local session. Done, £0, Codex `image_gen`, one correction.**
Output: `close-2045/out/campus-ncic-photo.png`, notes in `campus-ncic-notes.md`.

### Two things in this brief did not match its plate, so the plate changed

1. **The brief describes the Meshy models; the plate has the written facades.**
   The brief predates `facades.js` (73bbab9) and the NCIC wedge (e0a30a1).
   `campus-cluster.png` was re-rendered with the current code before running.
2. **The NCIC is not in this camera's frame, even re-rendered.** From
   `campus-cluster.json` it sits about 51° right of the view axis, against a
   38° half-width. So I rendered **`campus-ncic`**: the same camera position,
   turned to look at (−190, −115), which puts the NCIC centre-right with the
   campus blocks around it. That is the plate this result is for. The
   original stays as specified.

**`measure_leg_anchors.py` crashes on `campus-ncic.json`:** `IndexError` in
the height lookup (`at`, line 88), called from `describe` (line 158), so a
projected feature's ground sample falls outside the height field. Not patched
here, as it is your tool. The locks below were taken from the plate by eye.

### The rule: passes cleanly

| | in the frame |
|---|---|
| place of interest | the NCIC's meadow wedge, glazed high end catching the sun |
| buildings | banded campus blocks with sedum roofs, the NCIC, homes in brick with slate and tile |
| people | on the plazas, outside the glazed ground floors, walkers and cyclists on the new street, on the footway in the foreground |

Sky is about 14 % of the frame, and the ground between the blocks became sett
plazas through wildflower. Nothing is empty.

### The named failures

None of the four: no towers, the meadow roof is a roof, nothing added to the
open fields, people everywhere.

### Residuals, at 1280 × 720 (locks by eye from the plate)

| feature | plate | residual (Codex, ±4 px) |
|---|---|---|
| NCIC | x 722–905, y 268–342 | up to **51 px**; drawn about 35–40 px **high** |
| nearest campus block | x 0–285, y 368–500 | up to 34 px |
| second campus block | x 332–530, y 322–410 | up to 36 px |

The whole scene is drawn **high** again: the sixth frame running where this
generator lifts the composition rather than shifting it at random.

### Where the plate is the limiting factor

**Not the buildings, this time.** At 100–250 m the written facades carry
straight through: the ribbon windows, stone spandrels and sedum roofs are all
in the photo, and the NCIC reads as a wedge you could walk up. Written
geometry is enough for Codex at this distance, and the Meshy credits for more
types are not needed.

What limited it was upstream of the generator: a brief whose camera missed its
own place of interest, and an anchor tool that could not measure the frame.
