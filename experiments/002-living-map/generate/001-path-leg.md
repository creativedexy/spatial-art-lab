# 001 — the first generated leg, with Codex

**For:** the local session on the Mac, where Codex runs on the ChatGPT
subscription at £0.
**Inputs:** [`cheltenham-circular-footpath/`](cheltenham-circular-footpath/) —
`a-start.png`, `b-end.png`, `leg.json`, `anchors.json`.
**Cost:** nothing. Nothing here is a paid API call.

## Why Codex, and not the cheap image-to-image rungs

Because we already bought that answer and it was no. Session M re-ran ladder
rung 1 on the corrected GCHQ geometry for US$0.06 and wrote it down plainly:

> the pond does not come back. But the ring does not survive either — flux
> substituted a shed and a playing field. **Beauty-conditioning was always the
> weak path** and this is the clearest statement of it we have.

And the other half of the same handoff:

> **Codex on the ChatGPT subscription, at £0, beat the paid models outright.**
> Given three or four references and told to inspect its own output, it drafts,
> names its own drift, regenerates, and writes itself coordinate-locked
> correction prompts.

So the imagery route is Codex. The paid ladder's image rungs are a record of a
question already answered, not a step to repeat.

## What Codex gets wrong, and the one thing new here

Its own honest verdict on the frame 3 / frame 4 pair was *"closely aligned
visually, but not survey-exact"* — a rounder woodland, a higher hedge, a wider
stream, extra landscape invented above the skyline. It found all of that by
inspecting its first draft and then writing itself a correction prompt full of
normalised coordinates.

**That second pass is now avoidable, because we can measure those coordinates
before the first one.** `anchors.json` is every surveyed feature projected
through this leg's own camera: `u` runs 0 at the left edge to 1 at the right,
`v` runs 0 at the top to 1 at the bottom — the same convention the correction
prompts already used, except derived from LiDAR and OpenStreetMap rather than
from looking at a draft.

## The plates

Both frames come from the map's own camera (`cameraOnLeg` in
`golden-valley/walk.js`, the same function the live walk uses), with the path
network hidden — the amber ribbon is how a viewer *chooses* a route, and
conditioning on it would paint a glowing strip down the middle of the picture.
The camera rides at 14 m, not eye height: at 2.4 m the land cover is a 1 m
image at a grazing angle with no grass or verge geometry under it, and the
frame is a smear.

`a-start.png` and `b-end.png` are the two ends of 320 m of the **Cheltenham
Circular Footpath**, a real right of way that passes 160 m from the Golden
Valley phase 1 site. Nothing here is invented; the whole job is to make it look
like the photograph it should be.

## Job A — `a-start.png` into a photograph

One image, 16:9, same projection and framing. Input 1 is the **edit target and
absolute truth for geometry**. Retexture and relight it; move nothing.

Lock these, from `anchors.json`:

| feature | where it must stay |
|---|---|
| horizon | `v = 0.452`. Sky above it, ground below. Do **not** invent extra landscape into the sky. |
| the footpath | dead centre, `u = 0.500` the whole way. `v = 0.825` at 40 m, `0.634` at 80 m, `0.543` at 160 m, `0.482` at 320 m. A worn earth line through a crop, roughly a metre wide — not a track, not a lane, no gravel, no fence. |
| the stream | a **very narrow** ribbon. Enters at `u 0.528, v 0.473`, curves down and right, leaves at `u 0.932, v 0.704`. Nearest point 67 m. Not a river, not a canal, no banks to speak of. |
| the near hedge | left side only, `u 0.123, v 0.475` down to `u 0.008, v 0.528`. Low and thin. Do not raise it, do not run it further right. |
| the settlement | a band along the horizon from `u 0.21` to the right edge. Roofline tops at `v = 0.436`, bases at `v = 0.451`, nearest house 277 m away. Do not bring it forward, do not raise the roofline, do not add a single building in the open field. |

Everything else is materials and light: late-summer English arable with visible
working lines, mown pasture beyond the stream, mature deciduous trees in full
leaf along the settlement edge, 1930s–70s red brick and pale render houses with
grey slate and red clay tile roofs. Warm low afternoon sun, shadows in the
existing direction, natural colour, clear air to the horizon. A photograph from
a low drone, not a render. No text, no people, no vehicles, no new structures.

## Job B — `b-end.png`, made by **editing your Job A output**

This is the part that decides whether the pair is usable. Do **not** generate B
from the raw plate independently: the frame 3 / frame 4 pair held together
because B was an edit of an accepted A, and that is the only reason the two
read as one place.

The camera has moved 320 m forward along the same path — so this is not a
composite, it is the same world from further on. Use `b-end.png` as the
**geometry check** and your Job A output as the **material and light truth**,
so the crop textures, the sky, the roof colours and the sun are continuous
between them.

Locks for B:

| feature | where it must stay |
|---|---|
| horizon | `v = 0.374` |
| the footpath | `u = 0.500` at 40 m (`v 0.734`) and 80 m (`v 0.556`), then bending slightly right to `u 0.542, v 0.458` at 160 m |
| the stream | enters `u 0.622, v 0.528`, leaves `u 0.903, v 0.757`, nearest point 43 m — closer and larger in frame than in A, still narrow |
| nearest houses | a group at `u 0.935–1.007`, bases `v ≈ 0.437`, roofs `v ≈ 0.40`, about 170 m out on the right |
| the settlement | roofline tops `v = 0.361`, bases `v = 0.381`, from the left edge across |

Same time of day, same weather, same crop. If the sky or the crop colour shifts
between A and B, the pair is dead however good each frame looks alone.

## Inspect, then correct once

Do what worked last time: look at your own output against the plate and name
the drift in coordinates before regenerating. The four failure modes are known,
so check them by name —

1. landscape invented above the horizon line
2. the stream widened into a river
3. the hedge raised or lengthened
4. the settlement crept forward or grew a building into the open field

## What to write back

Append a `## Result` section here: what you ran, how many passes each frame
took, and your own honest reading of the residual drift against the numbers
above — the way Session M did, because that record is what made this brief
possible. Put the outputs in `cheltenham-circular-footpath/out/`, then flip the
row in [`README.md`](README.md).

## Not yet: the video bridge

Once the pair is good, the one thing Codex cannot do is move between them, and
that is the only step worth paying for: Kling v3 Pro
(`fal-ai/kling-video/v3/pro/image-to-video`) takes `start_image_url` **and**
`end_image_url`, about £0.45 for 5 s with `generate_audio: false`. That is
request 002 and it does not exist yet. **Do not run it as part of this one** —
a bridge between two frames we have not accepted is £0.45 spent on finding out
whether we like the frames.
