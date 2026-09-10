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

## Result

**10 Sep 2026, local session. Rung A answered, free. Rungs B and C parked.**

### What ran

Rung A, but **not on fal**. Dex's standing rule as of 10 Sep: spend nothing on
generation until he is happy with the images, and no video of any kind until
then (recorded at the top of `HANDOFF-sessions-K-M.md`). Rung A is a still-image
question, so it ran on the Codex subscription's built-in `image_gen` instead of
`fal-ai/flux/dev/image-to-image`.

- **Engine:** Codex CLI `codex exec`, built-in `image_gen`, both plates attached
  with `-i`, one session so light and season match across the two ends.
- **References:** the two plates only. Nothing from `inspiration/`, per the
  rule in `README.md`.
- **Cost:** £0. **Wall time:** about 12 minutes for both, including one
  self-inspected regeneration each.
- **Also did B's end frame.** The request asks rung A for `a-start.png` only,
  but a bridge pins both ends, so a photoreal `b-end` made in the same session
  is the half of rung B that costs nothing.

### Outputs, in `cheltenham-circular-footpath/out/`

| file | what |
|---|---|
| `a-start-photo.png` | start of the leg, 1672×941 |
| `b-end-photo.png` | end of the leg, 1672×941 |
| `contact-plate-vs-photo.jpg` | plate beside photo, both ends |
| `codex-prompts.md` | Codex's own final prompts and its drift record |

### Reading, against this request's own pass/fail

**Passes on photorealism.** Both read as a photograph of an English field path
towards a housing edge: a trodden line of bare earth, tractor lines, a small
brook with rushes, red brick and slate and tile along the horizon, one
afternoon's light.

**Partial on registration, which is the question that matters for the bridge.**
The layout does not *move* in the sense this request means by failure — nothing
invented, nothing relocated — but it drifts. Codex measured its own:

- **A:** brook bends, housing silhouettes, tractor-line spacing and the shed's
  surroundings shifted. GCHQ, which the plate shows edge-on as a low dark band,
  became a long pale metal shed. At this distance that is nearly a fair reading
  of a ring seen side-on, but it is not the building.
- **B:** horizon about **18 px** too high and the far end of the path about
  **15 px** left, measured at the plate's 1280×720.

That is the same blocker `plans/pipeline-3d-to-web.md` names for stage 4:
good enough for a vision frame, not good enough for an end pin that has to hand
back to `cameraOnLeg` without a visible jump. An 18 px horizon step at the
handover is a cut the viewer will see.

### What would move it, still free

- **Hold the horizon and the path as hard lines.** Both drifts are in the two
  features that carry the registration. A second pass that states them as pixel
  rows and columns taken from the plate (Codex did this unprompted on the site
  frames in Session M and it tightened them) is the next free thing to try.
- **Let the map own frame zero.** If the clip starts on the map's own render
  rather than a regenerated one, only the far end has to be registered, which
  halves the problem.

### Parked

- **Rung B** (`fal-ai/kling-video/v3/pro/image-to-video`, both ends pinned, 5 s,
  `generate_audio:false`, about £0.45) and **Rung C** (full 18.8 s, about £1.70):
  video, so parked until Dex is happy with the stills. When unparked, pin the two
  photos in `out/`, not the raw plates, or the clip will be photoreal at neither end.
