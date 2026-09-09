# Session B, run locally — generate the descent

Everything below is ready to run on a machine that has `GEMINI_API_KEY` and/or
`FAL_KEY` in its shell. Nothing here needs the cloud container, and nothing
here needs a photograph: both anchor frames already exist in the repo.

## Why it has to be anchored at both ends

Session C measured the hand-off with a control clip and found that video
quality barely matters — landing accuracy does. Session B then generated a
real clip and found the seam falls the *other* way round: the departure was
twice as bad as the landing (2.79 % against 1.43 %), because the wide aerial
holds thousands of tiny buildings a model cannot redraw exactly while the
landing holds a few large masses it can.

Both still hold, and together they say: anchor both ends, and expect the
error at the top. The map's player now fades the departure over 320 ms and
cuts the landing in 80 ms because of it.

```
 live map            generated clip              live map
  camera A ──in-seam──▶  ~4-5 s  ──out-seam──▶   camera B
     │                                              │
     └── frameA.png ── given to the model ── frameB.png ──┘
             (first frame)          (last frame anchor)
```

At the destination one pixel is 0.21 m of ground, so five metres of drift is
a 24 px jump. The generator therefore does not get to choose where the clip
ends — we hand it the last frame.

Floors to beat: control clip **0.704 % / 0.940 %**; first generated clip
(Kling 1.6 Pro) **2.793 % / 1.427 %**.

⚠️ **Both anchor frames were re-rendered on 9 Sep** and no longer show a white
model — the map now has surveyed land cover, 9,181 trees, and roofs measured
from the DSM. Two consequences: pull before you generate, or you will buy an
expensive descent of a world that no longer exists; and the Kling numbers
above were measured against the old world, so they are a record rather than a
comparison. The control clip's own floor moved with the world — the seam is
worse in absolute terms because there is far more detail to get wrong, and
**five metres of landing drift now costs 7.7 % where it used to cost 2.5 %**.
Landing accuracy matters about three times as much as it did.

`--style clay` is therefore probably the wrong default now. The map is no
longer a clay model, and a clip that arrives matte-white would break the
hand-back on style. Worth generating one of each and measuring.

## Start the session

```bash
# on Windows the interpreter is `python`, not `python3`
git clone https://github.com/creativedexy/spatial-art-lab.git   # or pull
cd spatial-art-lab
git checkout claude/maps-generative-video-ia8733
pip install google-genai fal-client imageio-ffmpeg pillow numpy

export GEMINI_API_KEY=...     # never commit these, never paste into chat
export FAL_KEY=...
claude
```

Then give the session this task:

> Read `experiments/002-living-map/descent/LOCAL-SESSION.md` and run it.
> Work on branch `claude/maps-generative-video-ia8733`, commit the clips and
> the run log, and push.

## The run, cheapest first

Always spend in this order. Each step is a gate on the next.

```bash
D=experiments/002-living-map/descent
A=$D/frames/gv-doughnut-aerial-frameA.png
B=$D/frames/gv-doughnut-landing-frameB.png

# 1. free — prints the exact request, spends nothing, proves the key is seen
python3 scripts/generate_descent.py $A $B $D/veo --dry-run

# 2. one cheap candidate, to prove the round trip end to end
python3 scripts/generate_descent.py $A $B $D/veo \
  --model veo-3.1-fast-generate-preview --candidates 1

# 3. score it against the anchors before buying more
python3 scripts/measure_clip_seam.py $D/veo/candidate-0.mp4 $A $B

# 4. only if step 3 is sane: three candidates on the full model
python3 scripts/generate_descent.py $A $B $D/veo --candidates 3

# 5. the same two frames through fal, for comparison
python3 scripts/generate_descent.py $A $B $D/fal --provider fal --dry-run
python3 scripts/generate_descent.py $A $B $D/fal --provider fal --candidates 1
```

`--style clay` is the default and is deliberate: our anchors are a matte white
architectural model, and a video model left to itself will drift towards
photoreal. A clip that lands perfectly but arrives photographic still breaks
the hand-back — on style rather than geometry. If it drifts anyway, that is
itself the finding, and the answer is the *departure* descent below.

## See it in the map

Drop the winning candidate in as the clip the seam test plays:

```bash
# .gitignore excludes *.mp4, so the winning clip has to be encoded to WebM to
# travel with the repo — which is also what the map plays.
ffmpeg -i $D/fal/candidate-0.mp4 -c:v libvpx-vp9 -crf 24 -b:v 0 -row-mt 1 \
  $D/clips/descent-doughnut-kling.webm
# then point the doughnut's "clip" at it in descent/hotspots.json
cd experiments/002-living-map && python3 -m http.server 8000
# open http://localhost:8000/golden-valley/index.html  (click the doughnut)
# or http://localhost:8000/descent/seam-test/index.html  (measure and flip)
```

Commit that WebM: without it nobody else can see the descent, and the cloud
session cannot wire it into the map.

Press **Run descent**, then **Flip** to hold the clip's last frame against the
live map and judge the join by eye. The measured number tells you whether it
is close; the flip tells you whether it is *invisible*, which is the only
thing that matters.

## Two species of descent, and the second experiment

The above is a **return** descent: it hands back to the live map, so both ends
must be ours. Worth generating one **departure** descent too, which is the
Primland move — the map opens into an authored scene and stays there:

```bash
python3 scripts/generate_descent.py $A $D/veo-departure \
  --style photoreal --candidates 1
```

No frame B, because there is nothing to hand back to. Only the in-seam has to
hold; the clip is *meant* to become the real place. Whether the living map
wants stylised returns, photoreal departures, or both, is the design question
this pair of clips settles.

## What to bring back

- the clips (`candidate-*.mp4`) and `run-log.json` from each provider
- `python3 scripts/measure_clip_seam.py ... --json` output per winning clip
- a session-log entry in `experiments/002-living-map/session-log.md` in the
  house format, recording **actual cost per candidate**, wall time, which
  prompt wording changed the result most, and the worst candidate as well as
  the best — the worst teaches more

Push to `claude/maps-generative-video-ia8733`; it flows into PR #1.

## Guardrails

- Never commit, echo or paste a key. `--dry-run` reports only whether one is
  *set*, never its value.
- Never skip step 1 and step 3. A free check before every paid one is the
  whole protocol.
- If a call fails, log the error verbatim in `run-log.json` and stop rather
  than retrying blind — two key tests have already been spent on guessing.
