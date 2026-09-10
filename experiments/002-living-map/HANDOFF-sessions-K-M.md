# Handoff to the main session

## Standing rules from Dex, 10 Sep 2026

**Look approved, 10 Sep, after 003.** Dex likes the 2045 set. Next: closer
shots, Meshy models of the key buildings, a video plan and the start of the
interactive web work. **No far-field terrain skirt**, which was 003's
suggestion; Dex does not think it is needed, so do not build it.

**No empty frames.** Every generated frame must show a place of interest,
buildings and people; transitions are a blurry zoom-in, not a journey. Full
rule and its check in `generate/README.md`.

**"Before" frames are parked.** No site-today or empty-plot frames until Dex
says otherwise.

### Images first, spend nothing

- **No video generation of any kind** until Dex says he is happy with the image
  generation. That includes the Kling v3 frame-3-to-frame-4 bridge proposed
  below: parked, not cancelled.
- **No paid image tests either.** The clear-air rung 2 re-run that `b96332e`
  asked for will not be run; Dex called it a waste of money.
- **Image work runs on the free Codex subscription.** The local session watches
  this branch every 15 minutes and will carry out any image brief committed
  here. Write it as a file (a `*BRIEF*.md` under `experiments/002-living-map/`
  is easiest to spot) that names the frames, the references to attach, and what
  must not move.

Written 9 Sep 2026 from the local session that ran the ladder and the vision
frames. Everything here is on `claude/maps-generative-video-ia8733`, rebased
cleanly on top of Session L. Sessions K and M in `session-log.md`.

## The verdict you commissioned

**No Blender.** Not one failure across six paid rungs and five free frames was
geometry being wrong or ambiguous — the only row of the brief's table a Blender
session would fix. What was failing was the depth encoding, which you have since
fixed properly in `capture_passes.py`.

US$1.45 in total. Of that, US$0.95 was wasted and the reason is specific and
worth carrying: I animated the **stylised** render with Kling **v1.6** when I
already had a photoreal still, because the brief listed the rungs in that order
and I confirmed v1.6 returned 200 without checking it was current. The dry-run
protocol catches wrong ids and has nothing to say about stale ones.
**Check the version, not just the pulse.**

## The finding that matters most

**Codex on the ChatGPT subscription, at £0, beat the paid models outright.**
Given three or four references and told to inspect its own output, it drafts,
names its own drift, regenerates, and writes itself coordinate-locked correction
prompts. Five frames and a page in `experiments/002-living-map/vision/`.

That is your routing skill's own finding holding under test: engine plus
verify-loop beats engine alone.

## Two single-value fixes, both A/B tested with real money

**GCHQ's roof.** `walls()` is an `ExtrudeGeometry`, so its top cap carried the
facade colour and the ring rendered as one dark solid. A flat dark ellipse in
green is why rung 1 read the most recognisable building in Gloucestershire as a
pond. Real roofs are pale ribbed metal — photographic ground truth now in
`inspiration/golden-valley/`. Split into `gchq:wall` / `gchq:roof`, roof
`0xc9ced2`, mask updated for the new names.

Re-ran rung 1 at US$0.06: **the pond does not come back.** But the ring does not
survive either — flux substituted a shed and a playing field. Beauty-conditioning
was always the weak path and this is the clearest statement of it we have.

**Your depth fix, tested.** Re-ran rung 2 at US$0.08 on the new pass. Against the
old linear pass it lost the town entirely; now the estate curves, the field
working lines and the A40 all match the survey. **Your OSM field lines are
visible in the generated frames**, so the tag work propagates end to end.
Remaining defect: it fogs the upper half and loses the ring in the fog. That is
the word "haze" in `LOOK`, and it is free to fix.

## Environment notes for this machine

- All passes re-rendered here. `.venv` has playwright, pillow and numpy; the
  Linux `CHROMIUM` path in `capture_passes.py` already falls through correctly.
- Relief reproduces your numbers exactly: aerial **10.30**, approach **5.26**,
  gv-site **0.53** with the TOO FLAT warning firing.
- Rungs 5 and 6 stay ARCHIVE. My hand-made `aerial-depth-refit.png` and
  `aerial-depth-disparity.png` are superseded by your renderer and kept only as
  the record of the diagnosis.

## The ask: `plans/pipeline-3d-to-web.md`

Four stages, each handing the next a thing it may not change and a thing it must
invent. Three moves that would go furthest:

1. **Bridge two photoreal frames properly.** Kling **v3 Pro**
   (`fal-ai/kling-video/v3/pro/image-to-video`) takes `start_image_url` **and**
   `end_image_url` as data URIs, $0.112/sec with `generate_audio:false`. Frame 3
   → frame 4 — the site today dissolving into the site built, from one surveyed
   camera — is the pitch, for about £0.56.
2. **Frame-exact registration is the blocker on stage 4.** Codex reports its own
   drift honestly every time. Fine for a vision board; not fine for a handover
   from the live map, where the viewer sees the cut. Cheapest candidate: let the
   map render frame zero and only ask the generator for what comes after it.
3. **Car parks and plot subdivision** are the last two audit rows still absent.
   Raster work in the pipeline we own, both transfer, neither is Blender.

## Corrections to `~/.claude/skills/image-engine-routing`

Measured today, not read:

- Codex `image_gen` returned **1672×941 (16:9)** every time, not the
  "~1086×1448 and not controllable" the skill records.
- **Blender is installed** (`/Applications/Blender.app`). The skill says it is
  not and rules Astra out on that basis. Astra is available — but point it at
  pipeline work (encodings, material assignment, camera rigs), never at
  sculpting, which is the thing Session K ruled out.

## The reference, and why it reframed the work

`inspiration/golden-valley/` — 16 images, private repo, third-party copyright,
provenance in the README. `official/aerial-03.jpg` is the important one: it is a
**photomontage over a real aerial photograph of our exact hill**. So it is free
ground truth for the audit, and it says the scheme's own visual language is
already the shape of our pipeline — real measured place as substrate, authored
buildings painted on.
