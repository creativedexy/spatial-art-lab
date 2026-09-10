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
