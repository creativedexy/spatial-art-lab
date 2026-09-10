# 002 — GCHQ, filling the frame

**For:** the local session on the Mac, on the free Codex subscription.
**Cost:** £0. No paid call, no video.
**Inputs:** [`gchq/plate.png`](gchq/), with `plate.json` and `anchors.json`.

## The rule, answered first

Per `README.md`, a brief has to name all three before anything is generated:

| must show | in this frame |
|---|---|
| **a place of interest** | **GCHQ, the Doughnut.** The most recognisable building in Gloucestershire, and the reason the cyber campus and the Golden Valley scheme are next door. It occupies 58 % of the frame's width. |
| **buildings** | the ring, three annexes across the foreground, and Hesters Way behind it — built form from the bottom of the frame to the horizon |
| **people** | from this height, life rather than faces: the car parks **densely full of individually parked cars**, traffic moving on the perimeter road, small figures on the paths between the annexes and the ring |

Empty ground and sky: sky is the top 24 % and the ground below the horizon is
almost entirely built or wooded. It passes.

001 was closed for failing exactly this test, and it was the right call — an
empty footpath across a field is a beautiful nothing. This is the same map,
pointed at something.

## Why this one is worth doing first

Because we have already watched a generator get it wrong twice, for two
different reasons, and both are now fixable in words:

- **Rung 1 read the ring as a pond.** Caused by our own bug: `walls()` was an
  `ExtrudeGeometry` whose top cap carried the facade colour, so the ring
  rendered as one flat dark ellipse in green. Fixed — the plate now shows a
  pale roof and a dark glazed facade.
- **On 001, GCHQ at 700 m became "a long pale metal shed",** and the box drawn
  round it was right to the pixel. So that was never a registration failure. At
  22 px tall the plate could not say what the band *was*. Here it is 254 px
  tall and the description below can do the rest.

## What the building actually is

Measured from the LiDAR, not described from memory: a circular office building
**14.8 m tall**, its ground at **52.7 m** above sea level, with a real open
courtyard through the middle. Pale white-grey ribbed metal annular roof; the
inner face of the ring is continuous glazing looking into the courtyard; the
outer face is glazed bands over a brick base. The courtyard is **dry** —
planting and trees, no water, no lake, no pond, ever.

Photographic ground truth for the roof is in `inspiration/golden-valley/`.
**Private reference: do not attach it to a generation.** It is there so this
description could be written accurately, not so the picture can be copied.

## The locks

Surveyed and projected through this plate's own camera, in its 1280 × 720.
Everything not listed is materials, light and life, and is yours.

| feature | surveyed position | note |
|---|---|---|
| **the ring** | x **312–1064**, y **285–539** | do not move it, do not resize it, do not raise it in frame |
| **the courtyard** | x **529–832**, y **307–365** | keep this hole exactly this size — it is the signature, and it is the thing that gets enlarged |
| horizon | y = **174** | sky above; do not invent extra landscape into it |
| settlement behind | rooflines top out at y = **209**, bases y = **228** | nearest houses 203 m; red brick, grey slate and red clay tile |
| annex, left | centre x 357, base y 654, roof y 582 | 109 m out |
| annex, centre-right | centre x 924, base y 669, roof y 594 | 105 m out |
| Royal Court | x 433–508, y 233–246 | 718 m, on the horizon |

## What to put in it

Materials and light only, on top of that geometry. Late summer, warm low
afternoon sun from the upper left, long shadows in the direction the plate
already shows, blue sky with a few small cumulus, clear air to the horizon —
no haze, no fog, no bloom. Mature oaks and limes in full leaf. Asphalt with
real wear and painted markings.

And the life, which is the point of the rule: the car parks around the ring
**full**, cars individually parked in ranks and glimpsed between the trees;
vehicles on the perimeter road; a scatter of small figures walking between the
annexes and the entrance. This is a working building on a weekday afternoon,
photographed from a light aircraft — not an architectural render at dawn with
nobody in it.

No text, no logos, no watermark, no new buildings.

## Inspect, then correct once

Check by name, because these are the known failure modes:

1. the courtyard filled with water, or enlarged
2. the ring turned into a shed, a stadium, or a roundabout
3. landscape invented above the horizon line
4. the car parks left empty — which fails the rule even if the frame is
   beautiful

## What to write back

Append a `## Result` here: how many passes, what you had to correct, and the
residual drift measured against the numbers above. If the plate itself is the
limiting factor — something the map does not model well enough to be described
— say so plainly. That is the most useful thing you can send back, because it
is the only kind of finding that changes what gets built here.

## Result

**10 Sep 2026, local session. Done, £0, two passes on Codex `image_gen`.**
Plate only attached; nothing from `inspiration/`.

### Outputs, in `gchq/out/`

| file | what |
|---|---|
| `gchq-photo.png` | the frame, 1672×941 |
| `contact-plate-vs-photo.jpg` | plate beside photo |
| `codex-notes.md` | Codex's passes, corrections, final prompt, its own residuals |

### The rule: passes cleanly

GCHQ is the unmistakable focal point: pale ribbed roof, continuous glazing on
the inner face, glazed bands over brick outside, and the notch in the plate
read as a glazed entrance block. The annexes and Hesters Way give built form
from the bottom of the frame to the horizon. The car parks are full, cars are
moving on the perimeter road, and there are people at the entrance and on the
path between the annexes. Sky is about a quarter of the frame.

### The four named failures

| | |
|---|---|
| courtyard filled with water or enlarged | **no.** Dry, planted, three trees; within ~5 px of the lock horizontally |
| ring turned into a shed, stadium or roundabout | **no** |
| landscape invented above the horizon | fixed on the second pass; the first put the horizon at y 202 |
| car parks left empty | **no.** Full on both sides and behind |

### Residuals against the locks, at 1280×720

| feature | lock | result | residual |
|---|---|---|---|
| ring, left/right | x 312–1064 | x ~315–1060 | within ~5 px (roof edge ~11 px in, as a roof should be) |
| ring, top of roof | y 285 | y 263 | **−22 px** (measured: pale-roof extent in the result) |
| ring, front base | y 539 | y ~511 | **about −25 to −28 px** (my read; Codex reports −14) |
| courtyard | x 529–832, y 307–365 | x ~524–833, y ~285–347 | x within 5 px; **y about −20 px** |
| horizon | y 174 | y ~178 | +4 px |

So the ring is **drawn uniformly about 20–25 px high**, with its width and its
courtyard proportions held, over a correct horizon. That is outside the ~15 px
tolerance the brief set.

It is also **the same drift as Session M's frames 1 and 2**, where Codex
reported "GCHQ sits higher in frame" both times. Three frames, same direction,
similar size: a systematic tendency of this generator on this building, not
noise. For a blurred zoom-in transition, 25 px is invisible. For a frame that
has to hand back to the live map without a jump it is not, and a third
correction pass is unlikely to cure a bias the first two did not.

### Where the plate is the limiting factor

**The car parks.** They are now the largest single area of life in the frame,
the rule makes them compulsory, and the map has no class for them. The plate
shows them as bare grey hard surface, so every rank, aisle and entrance in
this picture is the generator's invention. It invented them plausibly, but not
where they really are.

That is the one finding here that changes what gets built: **a car-park class
in the land raster** (OSM `amenity=parking`, with `parking_space` where
tagged), drawn as ranks in the plate the way Session L drew fields as working
lines. It also closes one of the last two audit rows Session M left absent.
