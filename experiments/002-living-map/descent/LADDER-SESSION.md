# The generation ladder — run this on a machine with keys

The question: **do we need to spend sessions in Blender adding detail to the
model, or is what we already have enough to condition a generator on?**

The bet is that an image or video model does not need our render to be
*realistic*, it needs it to be *unambiguous*.

```
   what a generator can invent          what it cannot
   ───────────────────────────          ──────────────────────────────
   brick, render, slate, glass          where the ridge line runs
   tarmac wear, kerbs, verges           that GCHQ is 14.8 m on a 52.7 m base
   leaf detail, undergrowth             that the A40 crosses there, not there
   sky, haze, time of day               the shape of the ground under it all
   ↑ surface — cheap, and it will       ↑ structure — expensive, and we have
     overwrite ours anyway                it, measured, to the metre
```

If that is right, Blender is the wrong place to spend: hand-modelling this
hill does not transfer to the next postcode, and the measurement does. That
repeatability is the whole proposition. But it is a bet, and this settles it
for about three pounds.

## What is already rendered for you

`experiments/002-living-map/passes/out/` holds four passes for three views,
all from one camera at one instant, wind off and birds hidden:

| | |
|---|---|
| `<view>-beauty.png` | the map as it renders |
| `<view>-depth.png` | **the conditioning encoding** — disparity plus true height above the terrain. Not metres; this is the one to condition on |
| `<view>-metric.png` | linear view depth in metres, range fitted to the frame, for anything that wants the number |
| `<view>-normal.png` | world-space normals |
| `<view>-mask.png` | flat colour by class **and by material family** — walls, domestic slate roofs, terrace roofs, shed roofs, civic roofs, road, hardstanding, water, field, wood, tree |
| `<view>.json` | camera, field of view, the fitted depth planes **in metres**, the mask palette |

Every capture reports the **mean local relief in grey levels** each depth
pass carries, and warns below four. That number is the whole lesson of the
first ladder run: a linear depth pass fitted over 357–1580 m gave a 15 m
house 1.07 grey levels out of 255, the control net saw a ground ramp and
nothing else, reproduced the ramp faithfully and invented a beautiful and
completely wrong town on top of it. The corrected pass carries 10.3.

It is worth knowing which way the warning can fire honestly: `gv-site`
reports 0.53 and is **right to**. That site is an empty field. There is
nothing there to condition on, which is exactly what Phase 5 is for.

Views: `aerial` (camera A of the doughnut descent — wide and dense),
`approach` (camera B — low, a few large masses), `gv-site` (the Golden Valley
site itself). Re-render any of them with
`python3 scripts/capture_passes.py --views aerial`.

The mask is worth a look before you start. It separates carriageway from
pasture from water from roof without a single extra mesh, because Phase 2
wrote a class per square metre and this reads it back — and the roofs are
split by material family from the OSM `building` tag, so a
segmentation-conditioned model can be told which roof is domestic slate,
which is profiled metal over a shed and which is membrane over a retail park.

Worth knowing what OSM does and does not carry here, because it shapes what
the mask can promise. `building:material` appears **zero** times in this box
and `roof:material` only 41 times. What it does carry is
`roof:shape` on 874 buildings, `building:levels` on 687, `surface` on 577
ways and `lanes` on 134 — none of which is a material, all of which implies
one. The families in the mask are therefore *inferred* from the building tag,
the storey count and the measured roof, and the `-mask.png` palette in the
sidecar says exactly which colour is which.

## The run, cheapest first

Each rung is a gate on the next. **Stop at any rung that answers the
question** — you do not have to climb it all.

```bash
export FAL_KEY=...                 # never commit it, never paste it anywhere
pip install fal-client

# 0. free. Prints every request. Proves the key is seen. Never skip it.
python3 scripts/generation_ladder.py --dry-run --rungs 1,2,3,4

# 1. pennies. Our render straight to photoreal. Does it keep the town?
python3 scripts/generation_ladder.py --rungs 1

# 2. pennies. The same view conditioned on depth instead of on our picture.
python3 scripts/generation_ladder.py --rungs 2

# 3. ~£0.40. A departure from the low approach — the easy case.
python3 scripts/generation_ladder.py --rungs 3

# 4. ~£0.40. The same from the wide aerial — the case Session B measured at
#    twice the error. If 3 works and 4 does not, that is the answer.
python3 scripts/generation_ladder.py --rungs 4
```

**Model ids go stale.** Every one in the script is a suggestion, not a
verified entry — check each on fal.ai and override with `--model-1`,
`--model-2` and so on. The dry run prints exactly what would be sent, so a
wrong id costs nothing.

## What to look at

Not the score. **The failure mode**, because three different failures point
three different ways:

| what you see | what it means | what it costs to fix |
|---|---|---|
| it invents the wrong buildings | a conditioning problem | try rung 2, or a segmentation-conditioned model with `-mask.png` — free |
| everything goes plastic | a prompt or model problem | prompt wording, or a different model — free |
| it cannot tell brick from render | a material-hint problem | roof and wall material from the OSM tags we already read, in our own renderer — one session, and it transfers to every future site |
| the geometry itself is wrong or ambiguous | **the only failure a Blender session would fix** | and I would be surprised |

Rung 2 beating rung 1 is the most interesting single result available here:
it would mean the *geometry* is doing the work, and that adding surface
detail to the model — in Blender or anywhere else — is beside the point.

## Two things Session B and Session G already measured

Worth knowing before you interpret anything:

- **Detail density drives the error.** Session B's generated clip scored
  2.79 % at the departure against 1.43 % at the landing, because a wide
  aerial holds thousands of tiny buildings a model cannot redraw exactly and
  a low approach holds a few large masses it can. Rungs 3 and 4 are that
  finding, tested again on a world that now has foliage and roofs.
- **These are departures, not returns.** A departure opens into an authored
  scene and stays there, so only the in-seam has to hold and detail density
  stops being a liability. Return descents — clip hands back to the live map
  — are where detail hurts, and those we keep stylised. Do not mix them up.

## What to bring back

- everything in `experiments/002-living-map/ladder/` — outputs and
  `ladder-log.json`
- a session-log entry in `experiments/002-living-map/session-log.md` in the
  house format, recording **actual cost per rung** from the fal dashboard,
  wall time, which prompt wording changed the result most, and **the worst
  result as well as the best** — the worst teaches more
- a one-line verdict on the Blender question, with the evidence for it

Push to `claude/maps-generative-video-ia8733`; it flows into PR #1.

## Guardrails

- Never commit, echo or paste a key. `--dry-run` reports only whether one is
  *set*, never its value.
- Never skip step 0. A free check before every paid one is the whole protocol.
- If a call fails, log the error verbatim and stop rather than retrying blind.
  Two key tests have already been spent on guessing.
- `.gitignore` excludes `*.mp4`, so a video worth keeping has to be encoded to
  WebM to travel:
  `ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 32 -b:v 0 -row-mt 1 out.webm`
