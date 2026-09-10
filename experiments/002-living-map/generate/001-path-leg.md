# 001 — the first generated leg

**For:** the local session on the Mac, which has the keys.
**Plates:** [`cheltenham-circular-footpath/`](cheltenham-circular-footpath/) —
`a-start.png`, `b-end.png`, `leg.json`.
**Budget:** stop at the first rung that fails. Worst case ~£2.20, and the
first rung is pennies.

## What this is, and why it replaces the field shot

The storyboard used to bridge "empty field" to "field with houses on it". That
is the most-made image in the industry and it puts the viewer above a plot
looking down like a surveyor. This replaces it.

The **Cheltenham Circular Footpath** is a real right of way. It runs north to
south through our box and passes **160 m** from the Golden Valley phase 1
site. We are not inventing a route to sell a scheme — we are travelling one
that walks past it today. The map already flies this leg live. What we are
buying is whether a generator can make the same 320 m photoreal without moving
the ground.

## The plates

Both frames come from the map's own camera — `cameraOnLeg` in
`golden-valley/walk.js`, the same function the live walk uses, so a clip
generated between them hands back to a camera already standing where the clip
left it. `leg.json` carries the positions, the distances and the duration.

Two things about them worth knowing before you write a prompt:

- **The interface is hidden.** The amber path ribbon is how a viewer *chooses*
  a route. Condition on it and the model paints a glowing strip down the
  middle of the footage.
- **The camera rides at 14 m, not at eye height.** That is a finding, not a
  preference: at 2.4 m the land cover is a 1 m/texel image at a grazing angle
  with no grass or verge geometry under it, and the bottom half of the frame
  is a smear. The first plate captured was exactly that and it was useless.
  14 m is where the texture resolves and hedges, trees and roofs give
  parallax. It still plainly reads as travelling the route.

## The ladder

Cheapest first, and each rung only earns the next.

### Rung A — is the plate photoreal-able at all? (~£0.03)

Image-to-image on `a-start.png`. This is `generation_ladder.py` rung 1 with a
different input, so the quickest route is to point it at a folder:

```
mkdir -p /tmp/leg && cp cheltenham-circular-footpath/a-start.png /tmp/leg/aerial-beauty.png
python3 scripts/generation_ladder.py --passes /tmp/leg --rungs 1 --dry-run
python3 scripts/generation_ladder.py --passes /tmp/leg --rungs 1
```

The filename is a legacy of the aerial rungs; the rung does not care what the
picture is of. Adjust `LOOK` in the script from "Aerial photograph" to a
ground-level framing before running — everything after that first sentence
(materials, light, the negatives) still holds. `strength: 0.62` is the number
to sweep if the result is ambiguous.

**Passes if:** it comes back as a photograph of an English field path towards
a housing edge, with the worn line, the field working lines, the stream and
the treeline still where we put them.
**Fails if:** the layout moves, or it stays plastic at every strength. A moved
layout is a conditioning problem and rung B will not fix it — say so and stop.

### Rung B — the bridge, short (~£0.45)

Image-to-video with **both** ends pinned, which is the thing the pipeline plan
has wanted since the beginning and has never actually been tried.

- model: `fal-ai/kling-video/v3/pro/image-to-video`
- `start_image_url`: `a-start.png` as a data URI
- `end_image_url`: `b-end.png` as a data URI
- `duration`: `5`
- `generate_audio`: `false` (this is what makes it $0.112/sec)
- prompt: motion only, never layout —
  *"Slow continuous forward travel along a footpath across an English field
  towards a housing edge, camera holding a steady height. Ground, hedges,
  trees and buildings stay rigid; correct parallax; one unbroken shot, no
  cuts, no new structures appearing. No text, no people, no vehicles."*

Note the mismatch and do not try to hide it: the leg is **18.8 s** of travel
and this clip is **5 s**, so it covers 320 m at 64 m/s — a glide, not a walk.
That is deliberate for a first test. It answers the photorealism and the
registration question for a tenth of the price of the full duration, and the
map's own timing can be matched to whatever we end up keeping
(`legSeconds` in `walk.js` is one function).

**Passes if:** the last frame still looks like `b-end.png` — same treeline,
same houses, same ground — and nothing grows or dissolves on the way.
**Fails if:** it drifts off the route, or invents buildings. Either means the
end pin is not doing its job; report which.

### Rung C — the bridge, full length (~£1.70)

Only if B passes. Same call, `duration` at the leg's real 18.8 s if the
endpoint allows it, otherwise the longest it does allow. This is the one that
could go straight into the map.

## What to write back

Append a `## Result` section here with: which rungs ran, the model ids as
actually called, what each cost, and your reading of the failure mode if any.
Put the outputs in `cheltenham-circular-footpath/out/`. Then flip the row in
[`README.md`](README.md) from open to done.

Never commit a key. `--dry-run` reports only whether one is set.
