# 3D → image → video → interactive web

Where the four stages actually sit, what each is allowed to invent, and which
of them is proven. Written 9 Sep 2026 at the end of Sessions K–M, after the
ladder settled the Blender question and the free frames beat the paid ones.

## The one idea

Each stage hands the next a **thing it may not change** and a **thing it must
invent**. The pipeline works exactly as well as that boundary is enforced, and
every failure in Sessions K–M was a boundary that had gone soft.

```
  stage        may NOT change                 must invent            cost
  ─────────────────────────────────────────────────────────────────────────
  1  3D        nothing — it IS the truth      nothing                free, ours
     measured structure: terrain, footprints, heights, roads, classes

  2  image     the structure it was given     surface: brick, tile,  £0 Codex
     conditioned still                        cars, light, weather   $0.08 paid

  3  video     the two frames it bridges      only the motion        £0.56/5s
     first→last frame interpolation           between them

  4  web       the clips and the map           when to hand over
     the live map, and where the clips are allowed to take over     free, ours
```

The thing that makes this a business rather than a one-off is that stage 1
**transfers**. Hand-modelling this hill buys one postcode; measuring it buys
every postcode. That is the whole proposition and it is why no stage above 1 is
allowed to become the place structure lives.

## What is proven, and what is not

| Stage | Status | Evidence |
|---|---|---|
| 1 → 2, still | **Proven** | Rung 6, and the five free frames. Structure survives when the conditioning image carries it |
| The conditioning encoding | **Proven, and it was the bug** | 1.07 grey levels of relief → 10.3. Session L put the fix in the renderer |
| Material and class hints | **Proven cheap, partly done** | One colour value caused a paid failure. Session L's OSM families and field lines come through visibly |
| 2 → 3, video | **Not attempted properly** | Session K animated the *stylised* render with Kling v1.6. Wrong input, stale model |
| 3 → 4, handover | **Open** | The seam is measured at 0.83%/0.95%, but on stylised clips, not photoreal ones |
| Frame-exact registration | **Open, and it is the blocker** | Codex reports its own drift honestly every time. Good enough for a vision board, not for a seam |

## The three things that would move this furthest

**1. Bridge two photoreal frames, properly.** Kling **v3 Pro**
(`fal-ai/kling-video/v3/pro/image-to-video`) takes `start_image_url` **and**
`end_image_url`, both as data URIs, at $0.112/sec with `generate_audio:false`.
Generate both frames free on Codex, pay ~£0.56 to bridge. Session K paid $0.95
to interpolate clay because it animated the wrong input with a two-generation-old
model. The obvious first test is frame 3 → frame 4: the site today dissolving
into the site built, from one surveyed camera. That single clip is the pitch.

**2. Close the registration gap, because it gates stage 4.** A vision board
tolerates drift; a handover from a live WebGL map to a clip does not — the
viewer sees the cut. Two candidate routes, cheapest first:
   - Condition the *generator* on the disparity pass rather than the beauty
     pass (rung 2's path, now that the encoding is fixed) and accept its style,
     rather than conditioning on beauty and fighting the drift.
   - Or let the map render the first frame, and only ever ask the generator for
     what comes after it, so frame zero is ours by construction.
   The second is almost certainly right and costs nothing to try.

**3. Add the two remaining classes, not more mesh.** Car parks and plot
subdivision are the last two rows of the audit still marked absent. Both are
raster work in the pipeline we own, both transfer, and neither is Blender.

## What stage 4 actually is

The live map already exists and already has a measured seam. The interactive
piece is not a new build, it is a **policy**: given where the camera is and
what the viewer has asked for, decide whether to keep rendering or hand over to
a clip, and hand back cleanly.

Sessions B and G established the asymmetry that policy turns on:

- **Departures** — the clip opens into an authored scene and stays there. Only
  the in-seam has to hold, so detail density stops being a liability.
- **Returns** — the clip hands back to the live map, so both ends have to
  match. These stay stylised, deliberately.

Do not mix them up. It is the one thing in this pipeline that is already
settled and easy to forget.

## Engine routing, as measured here

Follow `~/.claude/skills/image-engine-routing`, with three corrections found on
9 Sep 2026:

- Codex `image_gen` returned **1672×941 (16:9)** every time, not the
  "~1086×1448, not controllable" the skill records. Aspect appears to follow the
  references.
- **Blender is installed** (`/Applications/Blender.app`); the skill says it is
  not, so it rules Astra out. Astra is available — and should be pointed at
  *pipeline* work (encodings, material assignment, camera rigs), never at
  sculpting, which is the thing Session K ruled out.
- The skill's core finding held under test: engine plus verify-loop beat engine
  alone. Codex drafted, inspected its own output, named the drift and corrected
  it unprompted, and wrote itself coordinate-locked correction prompts.

Verify the **version**, not just the pulse. Session K confirmed Kling v1.6
returned 200 and spent $0.95 on it without checking it was current.
