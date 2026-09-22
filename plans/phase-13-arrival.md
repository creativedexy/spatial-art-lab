# Phase 13 — arrival

*Designed by Codex 12 Sep 2026 against the model at `665efcd`; re-measured here
against the phase-12 model on 22 Sep, which changed the answer.*
*Phase: Deliver. Branch head `6e886f7`.*

## What the re-measurement found

The design below was written when the allocation held 70 repeated house
footprints, panels painted into the ground, and no glasshouse anyone could
stand near. Phase 12 put 1,030 dwellings on internal streets, 195 real panel
row segments and 7,806 trees into the same box. Three of its conclusions no
longer hold, and one of them reverses:

- **The Homes now has a there.** 75 pairs of facing terraces stand 23 m apart
  with a stormwater channel in the verge. `homes-street-close` at
  `(-230, -636)` puts 38 buildings in frame, the nearest rising 25 to 27
  degrees either side. This is the strongest arrival in the set, and the
  design ruled it out for a reason that has since been built over.
- **Both arrivals the design chose are standing inside an orchard.** At
  `(-280, -150)` the nearest tree is 5 m away and the campus is not visible;
  at `(-410, -380)` there are 885 trees in frame, the nearest 9 m off, and the
  glasshouse is 92 m away rising 2.6 degrees behind them. Neither camera
  survives contact with the trees phase 12 planted. The plates are in
  `experiments/002-living-map/generate/arrival/plates/`.
- **Fiddlers Brook is not where the design put it.** The nearest water to the
  campus centroid is 41 m south-west of it, not 13 m from that camera.
- **`scripts/measure_arrival.py` is the instrument**, written for this phase.
  It reports the ground under foot, the buildings in frame with how far they
  rise in the picture, what the ground is made of along a fan of rays, the
  trees (read from `gv-2045-trees.bin`, not the class raster — the first
  version missed them, and three plates came back as a wall of leaves from
  positions it had called clear), the nearest panel row, and whether the
  flight in clears the terrain. The straight line from every parent viewpoint
  to every arrival clears the ground, so no new descent machinery is needed:
  the existing `places.js` flight lands at 1.6 m unmodified.

## What eye level exposed in the model, and the fix

Standing in it is the first honest test of a model signed off from 340 m.

**The agrivoltaic rows were opaque black walls.** 2 m tall, no sky in the face,
no module joints, no posts at a believable spacing, and mown grass between the
rows — when the crop between the rows is the entire argument for vertical
agrivoltaics. The plan geometry was never wrong: 3 fields, 39 rows, 195
segments, 11 m centres, 2.0 m tall, 0.35 m clear of the ground, 22 degrees,
all unchanged and compared equal after regeneration.

The first attempt failed in an instructive way. It mixed a sky colour into
`diffuseColor` behind a view-elevation gate, so that the lift could not reach
the signed-off aerial. It changed nothing: M6b's PV body is a linear 0.04 at
its brightest, the sun is behind the panel, and no amount of mixing a dark
albedo makes a dark albedo bright. **Reflected sky is light, not albedo.** So
the face is now lit after the lighting stage by two terms, and neither is gated
on where the camera is, because a term that only appears when you stand up is
a fudge:

- `skyHemisphere` 0.10 — a vertical module's shaded face is lit by roughly half
  the sky hemisphere.
- `skyRadiance` 0.45 on a third-power Schlick term — at grazing incidence it
  mirrors that sky.

What that costs the aerial, measured rather than assumed: on the held
`the-panels` framing, mean luminance moves 2 parts in 255 and 9% of pixels move
by more than 8, and nearly all of it is the field gaining the crop stripes it
should always have had.

**The rows now have module rhythm**, drawn in world metres in the shader rather
than bought with geometry: 1.1 m bays, 30 mm joints, 120 mm posts at 3.6 m
centres instead of 7 m. One 36 m segment is still one instance and the rows are
still four instanced draws.

**The 11 m between the rows is farmed.** Only texels whose class is exactly
`agrivoltaic` are worked, with a 0.7 m unworked service band beside each panel
line and alternating drill rhythms on neighbouring strips. Contrast was raised
from 0.07 to 0.16 after the first pass read as mown stripes rather than a crop.
These are legibility assumptions about the aggregate rows a person sees, not a
claim about plant spacing, and they say so in the metadata.

**The campus courts are unlit lawns.** The blocks face east, so the late
afternoon sun the photographs are matched to puts their own courtyards in
shadow, and the ground between them carries nothing. Not fixed in the model:
the court arrival's plate is handed to the generator with the court surface,
planting and seating described in the prompt.

## The three arrivals, revised

| Arrival | Stand | Looks at | Why it, and not the alternative |
|---|---|---|---|
| The street | `(-230, -636)` | `(-150, -604)` | 38 buildings, terraces 20 m either side rising 25°, channel in the verge |
| The court | `(-150, -210)` | `(-200, -190)` | the one clearing in the campus orchard; two blocks at 40 and 60 m |
| Among the panels | `(-500, -545)` | `(-365, -581)` | panels 2 m off, the new homes 86 to 155 m behind — held until the rows are fixed |

Eye is 1.6 m above the measured terrain at each. The lens is 48 degrees
vertical, the lens every photograph in this map was made with. All three are
2045-only; before frames stay parked.

---

**Produced by Codex** (`gpt-5.6-sol`, read-only over the repo at `665efcd`,
12 Sep 2026) as a work package, then checked here.

**What I verified myself, and it holds:**

- `groundAt(-280, -150)` = 38.90 m against its claimed 38.89; `groundAt(-410, -380)`
  = 40.65 against its claimed 40.63. Both within 2 cm, so the standing
  positions are real ground, not plausible-looking numbers.
- The look target `[-190, 47.341, -200]` is `campus-courtyards` in `places.json`,
  exactly.

**What I did NOT verify:** the building footprints quoted from
`gv-2045-buildings.json`, the bearings, and the claim that The Homes contains
no named square or civic focus.

**Worth keeping whatever else changes:** it declines to give three of the five
shots an arrival, on the grounds that they have no "there" to get to, and says
so rather than inventing one. That matches the plan's own line — "not every
viewpoint has a there to get to" — and it is the answer that is easy to get
wrong in the direction of more work.

**Both frames are 2045-only.** Before frames stay parked.

---

## Delivered

Three arrivals, each a photograph generated from a plate rendered at the camera
a person standing there would have, and each reachable from the shot that looks
at that ground:

| Arrival | From | Stand | Eye on landing |
|---|---|---|---|
| The street | the-homes | `(-230, -636)` | 1.56 m above the terrain |
| The court | the-campus | `(-150, -210)` | 1.59 m |
| Among the panels | the-panels | `(-500, -545)` | 1.48 m |

- An arrival and an aerial photograph of the same courtyard are two routes into
  the same ground, which `viewpoints.json` forbids and `test_viewpoints.py`
  enforces. The campus shot now offers the arrival; the aerial photograph of
  that court moved to the vale, which looks across the campus from the west.
- `test_public_build.py` no longer has the number five typed into it. It counts
  the places in `places.json`, because a number typed into a test goes stale.
- Payload is unchanged: 6.48 MB measured before and after, +3.6 KB. The
  photographs load when a place is visited, not on first load. The build test's
  own first-load counter is noisy by its own admission and moved from 2.58 to
  7.15 MB between runs on identical code; `measure_payload.py` is the number to
  quote.
- Tests: 19/19 places, 16/16 viewpoints, 13/13 public build, 9/9 tiles gate,
  7/7 keyed hand-off.

### Left undone, deliberately

- **No arrival for the vale or the meadow roof.** The original design's refusal
  still holds for both: the vale is a regional relationship, and GCHQ's roof has
  no credible public ground-level destination. Two of its three refusals stand;
  only The Homes reversed, and only because phase 12 built the street.
- **The court arrives into shade.** The campus blocks face east, so at the hour
  every photograph in this map is matched to, their courtyards are in their own
  shadow. The generated photograph is brighter and warmer than its plate. That
  is the generator disagreeing with the model about the light, and it was
  allowed because the picture is better; it is not measured.
- **No people in the panels photograph**, though the prompt asked for a grower
  and someone on the field track.
- **No back-down path.** Leaving an arrival uses the same flight every other
  place uses, reversed. The design's stylised descent, and its "Back to Cyber
  Central" control, were not built: the straight line from every parent
  viewpoint clears the terrain, so the machinery would have been ceremony.
- **The crop between the rows is a shader pattern, not plants.** It reads from
  340 m and it reads at 1.6 m as drilled rows; it is not modelled growth.

## The original design, as written 12 Sep

*Kept as written. Its verifications and its three refusals are still worth reading; its two chosen cameras are superseded above.*

### Choose two

- **Cyber Central → The Courtyards at Fiddlers Brook.** This is the essential arrival: the 15.8 ha wetland corridor only becomes intelligible beside its narrow watercourse, with the campus occupied behind it. This carries frame 5’s planted foreground, architecture and human life.
- **Panels and glasshouses → Working glasshouse edge.** At eye level the proposition becomes concrete: crops beneath spaced panels, waste-heat glasshouses and campus buildings in one working landscape.

Both are **2045-only**. TODAY arrivals remain parked.

Keep these aerial:

- **The Vale:** no “there”; it is a regional relationship—town, Doughnut and escarpment.
- **The Homes:** no “there”; the geometry contains 70 repeated house footprints but no named square, street or civic focus. Inventing one would be dishonest.
- **The Meadow Roof:** it has a subject, but no credible public ground-level destination. GCHQ’s secured, elevated roof is understood from above; ground access would either hide the meadow or fabricate access.

### Destination frames

### 1. The Courtyards at Fiddlers Brook

- **Camera:** `[-280.00, 40.49, -150.00]`; terrain `38.89 m AOD`, eye `+1.60 m`.
- **Look:** `[-190.00, 47.341, -200.00]`, the existing `campus-courtyards` target in `places.json`; bearing `061°`, elevation `+3.8°`, vertical FOV `48°`.
- **Time:** late August, `16:45`, warm low afternoon sun.
- **Place of interest:** **The Courtyards**, seen across the narrow Fiddlers Brook and its wet meadow. The nearest brook centreline is about 13 m from the camera.
- **Buildings:** the `13.6 m` campus block on footprint `[(-235.84,-168.28),(-221.61,-203.51),(-205.84,-197.14),(-220.08,-161.91)]`, plus the `11.9 m` block immediately behind on `[(-180.80,-136.34),(-216.03,-150.57),(-209.66,-166.33),(-174.43,-152.10)]`.
- **People:** campus workers crossing the planted court, two people sitting outside the glazed ground floor, walkers and one cyclist passing the wetland edge.
- **Composition:** reeds, wildflowers and people in the lower third; occupied architecture across the middle; sky no more than 25%.

**Forbid:** broad river, lake or flood basin; empty nature-reserve foreground; invented large bridge; generic curtain-wall office park; moved/taller blocks; token distant people; drone-height camera; more than half empty meadow or sky.

### 2. Working glasshouse edge

- **Camera:** `[-410.00, 42.23, -380.00]`; terrain `40.63 m AOD`, eye `+1.60 m`. This is a crop gap between the agrivoltaic rows.
- **Look:** `[-338.93, 43.11, -321.56]`, the centre and mid-façade of the glasshouse below; bearing `129°`, elevation `+0.5°`, vertical FOV `48°`.
- **Time:** the same late-August `16:45`.
- **Place of interest:** **Panels and glasshouses**, specifically the waste-heat growing house.
- **Buildings:** the `62 × 13 m`, `6.5 m` glasshouse on `[(-365.24,-339.20),(-307.75,-315.97),(-312.62,-303.92),(-370.11,-327.14)]`; behind it, the `15.3 m` campus block on `[(-218.23,-211.86),(-204.00,-247.09),(-188.24,-240.72),(-202.47,-205.49)]`.
- **People:** growers wheeling harvested produce from the glasshouse, one technician working beneath a raised panel row, and two campus staff walking through the service court.
- **Composition:** crops and thin panel rows in the foreground, glasshouse dominant in the middle, campus behind; sky no more than 20%.

**Forbid:** continuous black solar carpet; panels higher than roughly `2 m` or closer than the `11 m` row spacing; bare gravel solar farm; glasshouse becoming a warehouse, domestic polytunnel or giant conservatory; duplicated buildings; generic towers; empty fields or people reduced to specks.

### Back up

A persistent **“Back to Cyber Central”** or **“Back to Panels and glasshouses”** control should:

1. Plain-crossfade the held photograph onto the matching live 2045 endpoint at the identical camera.
2. Run the measured descent path backward, `B → A`, live and stylised—about `3.2 s`, as `returnToMap()` already does.
3. Complete the reverse approach to the exact originating viewpoint, restore its FOV and camera fence, and leave the switch at 2045.

Do not reverse-generate the photographic clip. Its final hand-back would occur in the dense aerial frame—the part already measured as hardest to match. The live reverse path is deterministic, survives a missing clip, and avoids both a visible aerial seam and a blur-zoom.
