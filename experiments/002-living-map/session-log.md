# 002 — Living map, session log

## Session A — LiDAR terrain in the browser

Date: 8 Sep 2026
Intent in one sentence: Prove real Cheltenham terrain can live in the browser and be recognised.
Tool/build/model: EA WCS 2.0.1 service, Python 3.11 (numpy/tifffile/Pillow), Three.js 0.169.0 (vendored), headless Chromium for capture.
Input files / source rights: EA LIDAR Composite DTM 1m via WCS (`spatialdata/lidar-composite-digital-terrain-model-dtm-1m/wcs`, coverage `..._Lidar_Composite_Elevation_DTM_1m`), Open Government Licence v3, attributed on the page.
Time / credits used: one cloud session; no paid generation.

### One variable to explore

Whether a single WCS `GetCoverage` request (12×12 km box, E 388000–400000 / N 216000–228000, `scaleFactor≈0.17` → 2048², ~16 MB GeoTIFF) beats the interactive tile portal for a repeatable pipeline.

### What I predicted

Tile downloads and GDAL wrangling; possibly no programmatic route at all.

### What happened

The dataset exposes a proper WCS with GeoTIFF output and server-side scaling — one URL replaces the whole portal flow. Elevation range came back 8.25–330.04 m; 330 m is Cleeve Hill's actual summit, which validated the data before a single pixel rendered. Converted to a 16-bit PNG (archival, 2048²) plus a uint16 binary (1024², 2 MB) the page reads directly, dodging the browser's 8-bit PNG decode. CPU vertex displacement (513² grid) with height+slope vertex colours rendered at full speed; ×1.8 vertical exaggeration keeps the scarp legible from map altitude. Drainage lines and field boundaries are visible in the vale — 1 m LiDAR carries texture even downsampled to ~12 m.

### Saved outputs

Source file: `experiments/002-living-map/terrain/` (page + data + vendored three.js). Rerun the fetch with `scripts/lidar_to_heightmap.py` and the WCS URL in this log.
Preview: `exports/002-living-map-terrain-v001.png`
Selected variant: south-west opening camera, town centred, escarpment behind.

### Review (Session A)

What works: the terrain is unmistakably Cheltenham; markers for GCHQ/Golden Valley, town centre and Cleeve Hill confirm georeferencing (EPSG:27700 → local XZ) is correct.
What I can now change without AI: palette ramp stops, vertical exaggeration, camera limits, marker set, box extent.
One failure worth keeping: first WCS guess used a wrong service path (`environment.data.gov.uk/image/...` — doesn't exist); the real pattern is `environment.data.gov.uk/spatialdata/<dataset-slug>/wcs`, discovered by scraping the dataset page for service links.
Next 20-minute experiment: Session B — generate the first descent clip candidates between an aerial-style frame and a ground-level photo (needs a Gemini or fal.ai key, and owned imagery of a Cheltenham spot).

## Session A+ — Golden Valley vertical slice

Date: 8 Sep 2026
Intent in one sentence: Prove the map ties to the real place — full 1 m resolution, real buildings at measured heights, true scale.
Tool/build/model: EA WCS (DTM + last-return DSM at native 1 m), OSM map API for footprints, pyproj for EPSG:27700↔WGS84, Three.js ExtrudeGeometry + merged buffers.
Input files / source rights: EA LiDAR composites (OGL v3); building footprints © OpenStreetMap contributors (ODbL). Both attributed on the page.

### What happened

`scripts/golden_valley_slice.py` builds the whole dataset: 2×2 km box (E 390400–392400, N 221400–223400) fetched at native 1 m from both the DTM and the last-return DSM; **DSM − DTM = measured height of everything standing on the ground**. 4,042 OSM footprints rasterised against that difference grid give 4,033 buildings, each extruded to its median measured height (median 5.7 m — two-storey Benhall, correct; the page renders them as an archviz white model over the terrain, no vertical exaggeration).

Three catches worth recording: (1) Overpass API is unreachable through this environment's proxy — the plain OSM `map` endpoint works for small boxes and returns everything; (2) my remembered GCHQ coordinate was ~1 km off and the first box clipped the doughnut — always convert a checked lat/lon through pyproj rather than trusting recall; (3) the doughnut is an OSM *relation* (outer ring + courtyard hole), so way-only parsing missed the single most recognisable building — the parser now handles building relations with holes, and the courtyard renders.

Validation: LiDAR-measured doughnut height 14.8 m over a 52.7 m base; the surrounding crescents match the real street pattern; B&Q, the BMW dealer and Nuffield Hospital all appear where they are in life.

### Saved outputs

Source: `experiments/002-living-map/golden-valley/` (page + data), `scripts/golden_valley_slice.py` (rerun to rebuild).
Preview: `exports/002-living-map-goldenvalley-v001.png`
Camera/capture support: `?cam=x,y,z&look=x,z&clean=1` URL parameters frame clean stills — this is how descent frame A endpoints are rendered.

## Session B — descent pipeline (prepared, awaiting key)

`scripts/generate_descent.py` is the one-command pipeline: frame A + frame B → N candidate clips via Veo 3.1 frames-to-video (Gemini API), with a JSON run log for prompt/timing/cost discipline. Frame A for the first descent is rendered and saved (`descent/frames/gv-doughnut-aerial-frameA.png`, clean capture over the doughnut).

Blocked on two inputs: a `GEMINI_API_KEY` in the environment, and a frame B (ground-level photo or render of the destination). Next 20-minute experiment once the key lands: three candidates between the saved frame A and a frame B, then the Session C seam test.

## Session B key test — key did not reach the container

Date: 8 Sep 2026
Intent in one sentence: Verify the newly added GEMINI_API_KEY works for Veo generation with one cheap candidate.
Tool/build/model: attempted `veo-3.1-fast-generate-preview` via `scripts/generate_descent.py` (image-to-video from frame A alone).

**Key worked: no.** `GEMINI_API_KEY` was not present in the freshly provisioned container's environment, so the variable set in the claude.ai environment settings did not propagate. The free validation (`GET /v1beta/models`) confirmed it independently: with no key header Google returned 403 "unregistered caller" (the proxy injected nothing), and a placeholder header was forwarded verbatim and rejected with 400 API_KEY_INVALID. The generation script exited before any billable call ("GEMINI_API_KEY is not set"), so generation wall time was 0 s and cost was zero. Evidence in `descent/keytest/run-log.json`.

Fix to try: re-save the key in the environment settings and start a fresh session — env vars are read at container start, and this container (provisioned 8 Sep 13:14 UTC) never received it.

## Session B key test — retry after credential fix

Date: 8 Sep 2026
Intent in one sentence: Re-verify Veo access now that the Gemini credential is injected by the network proxy as an `x-goog-api-key` header rather than exposed as an env var.

**Key worked: no.** The free validation call (`GET /v1beta/models`, no key header or query param added by this test, letting the proxy attach the credential) returned HTTP 401 UNAUTHENTICATED / `ACCESS_TOKEN_TYPE_UNSUPPORTED` — not the 403 "unregistered caller" seen last time, but still not a successful auth. Per the test instructions, generation was not attempted since the free step failed; wall time was 0 s and no billable call was made. Evidence in `descent/keytest/run-log.json`.

One-line note: the credential header mechanism was reconfigured between attempts, from `Authorization: Bearer <key>` to `x-goog-api-key` with no prefix (the format the Generative Language API expects) — this retest confirms the header format change alone hasn't yet produced a working call.

Correction (checked directly, 8 Sep ~15:05 UTC): there is no credential
injection to reconfigure. The agent proxy documents CA trust and egress
policy only — it attaches no Gemini credential, and `/__agentproxy/status`
lists no such accommodation. `GEMINI_API_KEY`, `GOOGLE_API_KEY`,
`GOOGLE_GENAI_API_KEY` and `FAL_KEY` are all unset in this container too, and
an uncredentialled `GET /v1beta/models` returns Google's ordinary 401
`ACCESS_TOKEN_TYPE_UNSUPPORTED` — the 403-then-401 change between attempts is
Google's own response to no credentials, not evidence of a header being
attached. Both key tests are therefore the same result: **no key has reached
any container**, and the only fix is a `GEMINI_API_KEY` saved in the "Play
area" environment settings, picked up by a session started afterwards.
## Session C — the descent seam, measured

Date: 8 Sep 2026
Intent in one sentence: Find out whether a viewer can see the cut between the live map and a pre-rendered descent — and if so, what actually causes it.
Tool/build/model: Three.js scene shared with the map page, headless Chromium for rendering, ffmpeg (VP9 + H.264) for encoding and decoding. No paid generation.
Input files / source rights: as Session A+ (EA LiDAR OGL v3, OSM footprints ODbL).
Time / credits used: one cloud session; £0.

### The thing being tested

A descent is two cuts, not one:

```mermaid
flowchart LR
  A["live WebGL<br/>camera A"] -->|in-seam| C["pre-rendered clip<br/>4 s"]
  C -->|out-seam| B["live WebGL<br/>camera B"]
  style C fill:#4a6f8a,color:#fff
```

Either cut can betray the trick. So rather than argue about it, I rendered a
**control clip** — the descent path drawn from the very same scene the map
runs — and measured both seams. A control has perfect seams by construction,
so every percentage point that shows up is the *pipeline's* error, not the
world's, and a generated clip inherits all of it as a floor.

### One variable to explore

How far can the clip's last frame drift from where the live map resumes
before the hand-back is visible? `?errors=` renders the destination as the
map would draw it at 0, 5, 10, 20, 40 and 60 m of landing error, and each is
compared against the clip's decoded final frame.

### What I predicted

That codec quality would be the problem, and we would need an expensive encode.

### What happened

The opposite, decisively. Mean absolute pixel difference, delivery encode
(VP9, 1.84 MB for 4 s at 1280x720):

| seam | mean | pixels a viewer could see differ |
|---|---|---|
| in-seam (clip frame 0 vs live A) | 0.48 % | 0.95 % |
| out-seam, 0 m landing error | 0.46 % | 1.8 % |
| out-seam, 5 m | 2.50 % | 12.0 % |
| out-seam, 10 m | 3.56 % | 17.6 % |
| out-seam, 60 m | 7.05 % | 31.1 % |

Re-encoding all but losslessly (18.8 MB, ten times the size) moves the 0 m
case from 0.46 % to 0.38 %. **Codec is not the limiting factor — landing
accuracy is.** Five metres of drift is a five-fold jump in error and a
twelve-fold jump in visibly different pixels.

The geometry says why. At the landing the camera sits 300 m from the
doughnut with a 48° field of view across 1280 px, so one pixel is 0.21 m:

```
metres per pixel = 2 x 300 m x tan(24°) / 1280 px = 0.209
5 m of drift  ->  24 px of jump   (obvious)
0.5 m         ->  2.4 px          (a cross-fade will bury it)
```

### The consequence for the project

The last frame of a generated descent cannot be left to the generator's
judgement — it has to be *given* to it. Veo's frames-to-video mode takes a
last-frame anchor, and that anchor must be rendered from our own scene at
exactly camera B, which `scripts/capture_descent_path.py` now does as a
by-product. Landing on a photograph of the real place is still possible, but
it is a separate, deliberate cut, not this hand-back — or the photograph has
to be registered into the scene first.

### Saved outputs

Source: `experiments/002-living-map/descent/` — `descent-path.json` (the path,
shared by every renderer of it), `path.js`, `seam-test/` (the page),
`clips/descent-control.webm`, `seam-report.json` (the numbers above).
Rebuild everything with `python3 scripts/capture_descent_path.py`.
Also saved: `descent/frames/gv-doughnut-landing-frameB.png` — the destination
rendered from the live scene at camera B. That is the last-frame anchor
Session B needs, so the descent no longer waits on a photograph of the place.
Preview: `exports/002-living-map-descent-sheet-v001.png`

### Review (Session C)

What works: the hand-off itself. Serve the folder, open
`descent/seam-test/index.html`, press **Run descent**, and the map descends
and hands back with nothing to see — then drag *landing error* to 5 m and
press **Flip** to watch it fall apart.
What I can now change without AI: path endpoints, easing, clip length, fade
duration, encode settings — all in one JSON file and one script.
One failure worth keeping: the first version of this test measured the seams
inside the browser and reported a 6.8 % out-seam. It was measuring nothing of
the kind — `seeked` fires when the decoder has moved, not when a frame has
been *painted*, so headless Chromium kept handing `drawImage` the previous
frame and the test compared the clip's opening frame against the destination.
Two lessons: a measurement that surprises you deserves a second, independent
route before it becomes a finding; and the render is bit-for-bit reproducible
(the refactor onto a shared `scene.js` changed exactly zero pixels), which is
what makes offline comparison trustworthy in the first place.
Next 20-minute experiment: Session B proper — same path, but the middle four
seconds generated by Veo from our own frame A and frame B, then re-run this
measurement and compare against the control's floor.

## Session B — the first generated descent (8 Sep 2026, run locally)

Ran on Dex's Windows machine rather than the cloud container, because the
container has never been able to see a Gemini credential. Locally the split is
the same as it was there: `FAL_KEY` present, `GEMINI_API_KEY` absent — the
BrandFlow desktop app keeps both in the Windows Credential Manager
(`service "BrandFlow Studio"`, accounts `gemini-api-key` / `fal-api-key`),
not in any `.env`, and reading it out of the vault is blocked in this harness.
So **fal only this session; Veo still unrun.**

Protocol held: dry-run first (free, confirmed the request shape and that the
key was seen), then one candidate, then measure before buying more. One paid
call, no retries.

| | in-seam | out-seam |
|---|---|---|
| control floor (our own render) | 0.478 % | 0.464 % |
| **Kling 1.6 Pro, 1 candidate** | **2.793 %** | **1.427 %** |
| visible pixels | 17.25 % | 6.02 % |

- model: `fal-ai/kling-video/v1.6/pro/image-to-video`, both anchors attached
  (`image_url` + `tail_image_url`), `--style clay`
- wall time **4m 00s** for one 5 s clip; cost **~£0.37 / $0.475 estimated**
  (5 s at Kling 1.6 Pro's per-second rate — the run log does not record the
  actual charge, which is a gap worth closing in `generate_descent.py`)
- 1920×1080 30 fps, 6.2 MB, rounded up from the requested 4.0 s to Kling's 5 s
  minimum

### The finding, which inverts Session C's assumption

Session C concluded landing accuracy is everything and the departure is free,
because at the destination one pixel is 0.21 m. **The generated clip does the
opposite: the in-seam is twice as bad as the out-seam.**

The reason is detail density, not geometry. Frame A is a wide aerial holding
several thousand tiny extruded buildings; the model cannot reproduce that
high-frequency field pixel-for-pixel, so it redraws it slightly. Frame B is a
low landing view of a handful of large masses, which it matches far more
closely. Two checks ruled out the boring explanations:

- **not framing** — anchors and clip are both 16:9; a zoom sweep from 1.00 to
  1.08 has its minimum at exactly 1.00, so there is no scale or crop mismatch
- **not tone** — fitting a per-channel gain and offset *worsens* the in-seam
  (2.79 % → 2.91 %) and only recovers 28 % of the out-seam error, so this is
  structural, not a grade

So the seam budget should be spent the other way round from what we planned:
cross-fade the departure, cut the landing. The departure is also where the
camera is moving fastest, which is exactly where a fade is cheapest to hide.

### What actually worked

The style held. `--style clay` was the thing I most expected to fail and it
did not drift photoreal at any point in the five seconds — matte white masses,
pale green terrain, no foliage or signage invented. Geometry stayed rigid:
GCHQ's doughnut stays a doughnut with its courtyard intact all the way down,
and no new structures appear. As a piece of camera work it is a genuinely
convincing continuous descent. The failure is entirely in the pixel-exact
hand-back at the top, not in the shot.

### Saved outputs

`descent/fal/candidate-0.mp4`, `descent/fal/run-log.json`,
`descent/fal/seam-report.json`.
Preview: `exports/002-living-map-descent-fal-sheet-v001.png` — anchor A, four
frames through the clip, anchor B, side by side.

### Review (Session B)

Worst thing about it: 17 % of the departure frame is visibly different, which
would read as a flicker on the cut. Best thing: it cost one call to learn that
the expensive end of the descent is the cheap end to fix.
Next 20-minute experiment: re-generate with frame A taken 300 m lower, where
the building field is sparser, and see whether the in-seam falls towards the
out-seam's 1.4 %. If it does, the rule is "hand over below the detail
threshold" and the whole descent path gets re-cut around it. Then the same
two frames through Veo, once a key is available, as the provider comparison
this session could not run.
## Session D — the hotspot descent player

Date: 8 Sep 2026
Intent in one sentence: Turn Session C's proven hand-off into the thing it exists for — click a place, descend into it, come back.
Tool/build/model: Three.js scene shared with the seam test, Playwright for an end-to-end interaction test, no paid generation.

### One variable to explore

Whether the descent can be made a property of a *place* rather than a
hard-coded path — and specifically whether the map can be complete before any
generated clip exists.

### What happened

`descent/hotspots.json` now holds three places, each with a descent path in
the shape `descent-path.json` already used, and an optional `clip`. The
doughnut carries the Session C control clip; the other two carry `null` and
**descend live along the identical path**. That fallback is the design, not a
stopgap: the path is the source of truth and the clip is an enhancement, so a
clip can be generated, swapped, regenerated or dropped without touching the
experience around it — and the map is finished today.

`descent/player.js` is the mechanism, reusable and place-agnostic: fly from
wherever the viewer is to the top of the path, hand over to the clip (or fly
it), hand back, and offer the way home.

Three things that only showed up by testing the real thing:

1. **`maxPolarAngle` quietly stole the landing.** The map stops you tipping
   below the horizon; an arrival is a low, near-level shot by design. The
   path put the camera exactly on the clip's last frame, then OrbitControls'
   first `update()` enforced its limit and lifted it 26 m — off the frame the
   clip had just handed over. The player now opens the pitch limit to
   whatever the arrival needs and restores it on the way out.
2. **`[hidden]` does nothing against an author `display` rule.** `.descent-clip`
   sets `display: block` and `.hotspot` sets `display: flex`, both of which
   outrank the user agent's `[hidden] { display: none }`. So the clip stayed
   on screen after handing back — showing its own first frame, which is
   camera A, over a live canvas that had correctly moved to camera B. It read
   exactly like a broken descent while the code was doing its job perfectly.
3. **The test agreed with the bug.** It asserted `!button.hidden`, which was
   true, while the screenshot showed all three pills still drawn. Assertions
   now read `getComputedStyle(...).display`, because what matters is what is
   on the screen, not what a property says.

There is also a geometry detail worth keeping: a clip has one aspect ratio
for ever and a window has whatever the viewer gives it. The overlay uses
`object-fit: cover`, so `matchFovToClip()` narrows the live camera's vertical
field of view by exactly the amount `cover` crops. Without it the two images
are at different scales and the seam shows however perfectly the clip lands.

### Saved outputs

Source: `experiments/002-living-map/descent/{hotspots.json,player.js,path.js}`,
`experiments/002-living-map/golden-valley/`. Test: `python3 scripts/test_hotspot_flow.py --shots DIR`
(8 checks, including that the clip's `currentTime` actually advanced — headless
virtual time fast-forwards timers but not media, so only a real-time run can
tell the clip route from its fallback).
Preview: `exports/002-living-map-hotspots-v001.png`

### Review (Session D)

What works: the whole loop — click, descend, arrive, read, return — with the
control clip on one place and live flight on the other two, and no visible
difference in how they behave.
What I can now change without AI: places, blurbs, paths, fade length, and
which places have clips, all from one JSON file.
One failure worth keeping: I diagnosed the stuck-at-camera-A symptom as the
`[hidden]` bug, fixed that, and the symptom stayed — because there were two
independent causes and I had stopped at the first. The pitch clamp was the
other. Fixing what you find is not the same as fixing what you are looking at.
Amended the same day, once Session B's numbers landed: the player's fades are
now asymmetric — 320 ms into the clip, 80 ms out of it. Session C's control
said both seams were equal, so a symmetric fade looked right; Session B's
generated clip put the departure at twice the landing, so the fade is spent
where the error actually is. Both live in `hotspots.json` as data, per path.
This is the point of keeping the path and the clip separate: a measurement
changed the experience without anything being rebuilt.

Next 20-minute experiment: Session B's proposal — re-cut the path so the
hand-over happens *below* the detail threshold (frame A around 150 m rather
than 300 m, where the building field is sparser) and see whether the in-seam
falls towards the out-seam's 1.4 %. The anchors for it are a capture run
away.

## Session E — land cover, roads and trees

Date: 9 Sep 2026
Intent in one sentence: Stop the ground reading as a lawn — Phase 2 of the look plan and the tree half of Phase 3, in one pass, from OSM we already hold.
Tool/build/model: Python + PIL rasterisation, Three.js `InstancedMesh`, headless Chromium for stills, no paid generation.

### One variable to explore

Whether **surface** is really what was missing. Every session so far had gone
into structure, and Phase 1 suggested the answer without proving it: light
alone turned the massing model into an architectural render, but it was still
an architectural render of a lawn.

### What happened

`scripts/golden_valley_landcover.py` reads the OSM extract already cached
from the buildings run — no new fetch — and finds 327 area polygons, 1,484
lines and 540 individually surveyed trees inside the same 2 km box. It writes
three things:

| file | size | what it is |
|---|---|---|
| `gv-landcover.png` | 605 KB | the ground, 1 m per texel, roads drawn in |
| `gv-trees.bin` | 72 KB | 9,181 trees, 8 bytes each |
| `gv-landclass.png` | 169 KB | the same raster as class indices, for Phase 4 |

Two decisions carried the result.

**Roads are texels, not geometry.** A service road is 4 m wide and the
terrain mesh's triangles are 2 m, so as geometry the road network would
z-fight and crawl at every altitude. Drawn into the ground image at 2x and
box-downsampled, it is exact, anti-aliased, and the entire network — 1,484
ways — costs one texture fetch. It is also why anisotropy is not optional
here: at 1 m/texel over 2 km, the far half of an aerial view is deep in the
mip chain, which is exactly where an aerial spends most of its pixels.

**Trees carry no Y.** Each 8-byte record holds x, z, height, rotation, kind
and canopy spread, and the map computes the ground height from the same field
the terrain is built from. A tree therefore cannot float or sink if either
ever changes — the one class of bug that would otherwise be invisible until a
descent lands next to it.

The vale now measures 31.7 % residential, 22.9 % farmland, 10.5 % amenity
grass, 9.4 % carriageway, 7.1 % meadow, 4.5 % woodland, 3.0 % park, 0.66 %
water. None of that was art-directed; it is what is there.

### Two things that cost time, both worth keeping

1. **PIL reads an integer colour lowest-byte-first.** `fill=0x7d9460` paints
   `#60947d`. The whole first raster came out in BGR — a plausible-looking
   mint-green Cheltenham that only gave itself away when I sampled a pixel
   rather than trusting the render. Colours are tuples now.
2. **`mergeGeometries` returns `null` for a mix of indexed and non-indexed
   inputs.** It does not throw. The trunk is an indexed cylinder and the
   canopy a non-indexed icosahedron, so the tree geometry came back null and
   the failure surfaced hundreds of frames later as
   `Cannot read properties of null (reading 'id')` inside three.module.min.js
   — a stack trace pointing at everything except the cause.

### Saved outputs

Source: `scripts/golden_valley_landcover.py`,
`experiments/002-living-map/golden-valley/landcover.js`. See it with
`python3 -m http.server` in `experiments/002-living-map` and open
`lookdev/index.html`; add `?bare` to render the same camera without Phase 2,
which is how the comparison sheet was made.
Preview: `exports/002-living-map-landcover-v001.png` (before/after),
`exports/002-living-map-landcover-aerial-v001.png`,
`exports/002-living-map-trees-v001.png`.

### Review (Session E)

What works: the answer to "I can't see the vision" is now a single image. The
same camera, the same light, the same buildings — the only difference is that
the ground knows what it is, and it stops being a diagram.
What I can now change without AI: every colour in one table at the top of the
script, tree density per land-cover class in another, and a rebuild is five
seconds.
One failure worth keeping: I sanity-checked the first raster by *looking* at
it, decided the mint-green fields were a preview quirk, and moved on. The
check that caught it was reading one pixel value. Looking at output is not
inspecting it.

Next 20-minute experiment: roof pitch from the DSM. We take the median height
inside each footprint and throw the rest away, but the ridge and the eaves
are both sitting in a file already on disk — the difference between the
footprint's median and its 90th percentile is a roof.

## Session F — roofs, and what the ridge direction turned out to be

Date: 9 Sep 2026
Intent in one sentence: The building half of Phase 3 — recover roof shape from the DSM we already downloaded, and material families from the OSM tags already on every footprint.
Tool/build/model: Python + numpy percentiles over the LiDAR difference, Three.js merged geometry, no paid generation.

### One variable to explore

We keep the **median** height inside each footprint and throw the
distribution away. The DSM holds the eaves and the ridge of every house in
west Cheltenham; the question was whether a 1 m composite can resolve them.

### What happened

It can, and it also answered a question I did not think was open.

`scripts/golden_valley_roofs.py` measures four things per footprint: eaves
(20th percentile of the roof pixels), ridge (97th), the direction the ridge
runs, and whether it is a gable or a hip. 2,658 gables, 735 hips, 640 flat,
median ridge 2.5 m above the eaves. Sheds come out 84 % flat and houses 79 %
pitched without being told which is which, which is the check that the
measurement is measuring roofs.

**The finding.** The ridge direction is measured, not assumed — the
minimum-area rectangle offers two axes and the DSM says which one the surface
falls away from. I expected the measurement to agree with the obvious prior
(a ridge runs along a building's long axis) nearly always, and treated
disagreement as noise to be suppressed. It disagrees **62 % of the time**,
and the prior is the thing that is wrong:

```
   OSM footprint of one semi          what I assumed         what the DSM says
   ┌──────────┐                       ┌──────────┐           ┌──────────┐
   │          │  9 m deep             │ ───────► │           │    ▲▲    │
   │          │  6 m frontage         │  ridge   │           │    ││    │
   └──────────┘                       └──────────┘           └──────────┘
        street ────────────────           wrong               ridge runs
                                                              with the street
```

A British semi or terraced house is narrow-fronted and deep. Its ridge runs
parallel to the road, which is *across* its own footprint's long axis.
Assuming the long axis would have laid every terrace in Hesters Way at right
angles to the street it faces, and it would have looked wrong without anyone
being able to say why.

The same two numbers separate a gable from a hip. Fall-off in one direction
and level in the other means vertical ends and a full-length ridge; fall-off
in both means the ends are hipped and the ridge is short. In the browser that
is one parameter — how far the ridge segment is inset from the footprint's
extent — and every footprint edge is then joined to its own projection on
that segment. It is the straight skeleton of a rectangle, it stays closed for
any simple polygon, and it needs no offsetting library.

Materials come from the `building` tag. Nearly half say only `building=yes`,
so those are inferred from the land cover Phase 2 put underneath the
centroid, the footprint area, and whether the roof measured pitched.

### Three things worth keeping

1. **The percentiles were checked, not chosen.** At the 97th percentile the
   ridge lands within 0.11 m of the footprint's highest pixel, so it is the
   ridge and not a chimney. The eaves are the fragile end: at the 12th
   percentile they come out at 3.7 m, a metre and a half below where a
   two-storey semi's eaves actually sit, because the wall line mixes roof and
   garden however hard it is filtered. The 20th puts them at 4.9 m.
2. **Ground leak was tilting the ridge direction, and it looked like signal.**
   A footprint rasterised diagonally on a 1 m grid is fringed with pixels
   that are half garden. Those sit at the greatest distance from every centre
   line, so they bias the tent fit in whichever direction the building is
   longest — turning a measurement of roofs into a measurement of footprint
   shape. My first run reported the DSM overruling the long axis 55 % of the
   time and I nearly shipped that number as a finding.
3. **Under this sun, grey renders as tan.** The light is 0xffe0b5 at a low
   angle, so a neutral roof arrives brown. Slate has to be specified cool —
   these values read blue in the file and grey on the screen.

### Saved outputs

Source: `scripts/golden_valley_roofs.py`,
`experiments/002-living-map/golden-valley/buildings.js`. Serve
`experiments/002-living-map` and open `lookdev/index.html`; `?flatroofs`
keeps the land cover and leaves the buildings as extrusions, which is how the
comparison sheet was made, and `?bare` goes all the way back to Phase 1.
Preview: `exports/002-living-map-roofs-v001.png` (before/after),
`exports/002-living-map-roofs-aerial-v001.png`.

### Review (Session F)

What works: the roofscape reads as British suburbia from 300 m — ridges
following streets, hipped semis among gabled terraces, flat sheds on the
industrial estate — and none of it was drawn.
What I can now change without AI: the five material families in one table,
the two percentiles that define eaves and ridge, and the gable/hip threshold.
One failure worth keeping: I built the ridge-direction test around a prior I
never questioned, then read a 55 % disagreement as noise rather than as the
prior being wrong. It was both — contaminated pixels *and* a wrong
assumption — and the only reason I found either was printing the actual
height grid of three houses instead of another summary statistic.

Next 20-minute experiment: adopt Phases 1–3 into `golden-valley/scene.js` and
re-run `scripts/capture_descent_path.py`. The seam has been measured against
a white model; measuring it again against a world with foliage and roof
detail tests Session B's finding — that the seam is driven by detail density
— on our own control clip, for free.

## Session G — adoption, and re-measuring the seam against a real place

Date: 9 Sep 2026
Intent in one sentence: Move Phases 1–3 into the map page itself, re-render the descent anchors, and find out what a detailed world does to a seam that was measured on a white model.
Tool/build/model: Three.js, headless Chromium capture, ffmpeg, Playwright, no paid generation.

### One variable to explore

Session C measured the hand-off on a clay model and concluded that codec
quality barely matters while landing accuracy is everything. Session B, on a
generated clip, found the seam is driven by **detail density**. Adopting three
phases of surface detail into the world is the experiment that tests both at
once, for free, on a control clip that is perfect by construction.

### What happened

`golden-valley/scene.js` now exports `buildWorld({ renderer })` and the map
page, the seam test and the lookdev harness all call it. `look.js` moved out
of `lookdev/` and into the world; `lookdev/` is now purely the comparison
harness that makes the before-and-after sheets, and it builds its earlier
states from the same parts with one pass left out rather than from a
differently-built world.

Then `scripts/capture_descent_path.py` re-rendered all 96 frames and the six
landing errors, and the numbers moved a long way:

| | white model | land cover, trees, roofs |
|---|---|---|
| in-seam, perfect landing | 0.478 % | 0.704 % |
| out-seam, perfect landing | 0.464 % | 0.940 % |
| out-seam, 5 m of drift | 2.496 % | 7.736 % |
| out-seam, 10 m of drift | 3.559 % | 8.997 % |
| delivery clip, crf 24 | 1.84 MB | 5.09 MB |

**Session B's detail-density finding is confirmed on our own control clip.**
Five metres of drift used to cost 2.5 % and now costs 7.7 % — landing accuracy
matters about three times as much as it did, because there is three times as
much detail to be wrong about.

**Codec quality changed less than it looks.** The delivery encode now sits
0.37 points above the near-lossless one where it used to sit 0.08 above, so
absolute codec error more than quadrupled. But it quadrupled against a
landing penalty that tripled, so the ratio survives — and measuring the whole
curve settled it:

```
  crf 24   5.09 MB   in 0.644 %   out 0.781 %
  crf 28   3.84 MB   in 0.670 %   out 0.865 %
  crf 32   2.87 MB   in 0.704 %   out 0.940 %
  crf 36   2.05 MB   in 0.756 %   out 1.028 %
```

Halving the download costs 0.16 of a percentage point where five metres of
drift costs seven. **Bitrate is still not what breaks a hand-off.** The
delivery encode moved to crf 32.

### The bug the adoption exposed, which was there all along

The clip stopped playing. `test_hotspot_flow.py` had been failing two of its
eight checks for two days and I had been writing it off as "a container
flake". It was two real bugs, and the heavier world only made them visible.

1. **The clip was never preloaded.** `video.preload = 'auto'` was set at
   construction, but `video.src` was only assigned when a descent started, so
   there was nothing to preload. At 1.8 MB nobody noticed; at 5 MB the clip
   took seven seconds to become playable, the player's twelve-second stall
   guard fired, and the map quietly fell back to flying the path live — doing
   exactly what it was designed to do, which is why it never looked broken.
   The player now warms the HTTP cache for every hotspot's clip at
   `rel="prefetch"` priority as soon as the map loads, and loading has its own
   budget separate from playing, because "the network is slow" and "the file
   is corrupt" are different failures that were sharing one number.
2. **The test was waiting on the clock, not on the world.** It slept 2,600 ms
   and assumed the clip would be up. The descent is driven by
   `requestAnimationFrame`, and this container renders through software WebGL
   at *seconds per frame* — a 900 ms fly-in can take half a minute of wall
   time. Every fixed `wait_for_timeout` was really measuring the renderer.
   Waits are on state now, with long timeouts, so a slow renderer costs
   patience rather than a false failure.

All eight checks pass, for the first time in this container.

### The measurement I nearly reported and should not have

Load time looked like it had doubled: 6.6 s to first frame before adoption,
12.8 s after. It had not. Both numbers were the page's own render loop —
3.9 seconds per frame under software WebGL — being counted inside the
measurement. Timing the build with no renderer in the loop:

```
   805 ms   buildScene, flat buildings (the old world)
   764 ms   buildScene, terrain only
   216 ms   buildBuildings — 4,033 roofs and five material families
     2 ms   applyLook
    69 ms   applyLandCover
    34 ms   loadTrees — 9,181 instances
```

The whole world builds in 1.08 s against the old 0.81 s. Three phases of
detail cost 280 ms, not six seconds. A benchmark that shares a thread with a
renderer measures the renderer.

### Saved outputs

Source: `experiments/002-living-map/golden-valley/scene.js` (`buildWorld`),
`descent/player.js`, `scripts/capture_descent_path.py`.
Numbers: `experiments/002-living-map/descent/seam-report.json`.
Anchors: `descent/frames/*.png` re-rendered from the current world — a
generated descent bought against the old ones would be a descent of a place
that no longer exists.
Preview: `exports/002-living-map-adopted-v001.png`.

### Review (Session G)

What works: one `buildWorld` call, three pages, no way for the live canvas
and a pre-rendered clip to disagree about the world — which was always the
reason the scene lived in one module.
What I can now change without AI: the delivery encode's quality, the stall
and load budgets, and which phases the lookdev harness leaves out.
One failure worth keeping: I called a failing test a flake for two days
because it failed identically on a clean checkout. That was good evidence it
was not *my* regression and no evidence at all that it was not a bug. "Not
caused by this change" and "not real" are different findings, and I reported
the first as though it settled the second.

Next 20-minute experiment: Phase 4's free half — cloud shadows across the
vale, driven by a scrolling noise texture on the sun's shadow, which costs
one shader and turns a static render into weather.

## Session H — Phase 4a: weather, wind, water, birds, and one clock

Date: 9 Sep 2026
Intent in one sentence: Make the map an afternoon rather than a render of one — and do it without breaking the hand-off that everything else has been measured against.
Tool/build/model: Three.js shader patching via `onBeforeCompile`, a boids flock in plain JS, headless Chromium capture, no paid generation.

### One variable to explore

Whether a living world and a measured seam can coexist. Every phase so far
made the map more detailed but kept it *still*, and stillness is the only
reason a pre-rendered clip could ever match a live canvas exactly. The moment
a cloud moves, the clip's last frame and the live canvas are two different
moments of the same afternoon, and no fade hides that.

### What happened

Four things move now, and none of them needed new data:

- **cloud shadows** — two octaves of value noise in world XZ, drifting with a
  wind vector that shares the sun's quarter, because a sky where cloud and
  light disagree reads as two separate effects
- **wind** — trees lean and recover, amplitude by `position.y²` in unit-tree
  space, so a hedge twitches while a mature oak rolls
- **water** — `gv-landclass.png` has been in the repo since Phase 2 with
  nothing reading it. This is what it was kept for: the ground knows which of
  its texels are water, so the streams and ponds ripple and go glossy with no
  second material and no mask painted by hand
- **birds** — ninety of them, actually flocking, holding a cruising height
  *above the ground* rather than an altitude, because the vale rises 35 m
  across the box and a flock at a fixed altitude flies into the escarpment

### The clock, which is the actual work

Nothing here reads the wall clock. Everything is a function of one number:

```
   the map          updateLife(worldSeconds())      wall time, rebaseable
   the capture      updateLife(i / fps)             frame by frame
   during a clip    pinWorld(floor(t·fps) / fps)    the clip's own frame
   at hand-back     releaseWorld(clipSeconds)       carries on, never snaps
```

Two details earned their names. `clipSeconds` is how much time a clip's
*frames* span, which is one frame less than its duration — 96 frames at 24 fps
run to 95/24 = 3.958 s, not to 4 s. Four seconds is close enough to look right
and wrong enough to measure. And the pin during playback is quantised to the
clip's frame grid, because the clip is showing frame `floor(t·fps)`, not the
continuous instant `t`.

The flock is the hard case, because a simulation remembers. It steps at a
fixed 1/60 s, indexed by an integer step count rather than by elapsed time,
and rewinds to a seeded start whenever time runs backwards — so asking for
t = 3.958 s twice gives the same ninety birds in the same places both times.
`scripts/test_world_clock.py` checks exactly that, and it is the test that has
to keep passing if anything else moving is ever added.

### It cost nothing at the seam

| | before Phase 4 | after |
|---|---|---|
| in-seam | 0.704 % | 0.700 % |
| out-seam at 0 m | 0.940 % | 0.938 % |

A world with weather, wind, water and a flock in it hands over to a
pre-rendered clip exactly as well as a still one did. That is the whole
result: the architecture is what made it free, and had the clock been an
afterthought it would have cost a re-render to find out.

> **Correction, added in Session J.** The in-seam figures in the table above
> — 0.704 % before, 0.700 % after — were both measured on a frame 0 that had
> no land cover texture on it, because `TextureLoader.load` was never awaited.
> The *comparison* stands, since both runs carried the same bug, and the
> out-seam numbers are unaffected. The absolute in-seam on a correct frame 0
> is 0.823 %. See Session J.

### Saved outputs

Source: `experiments/002-living-map/golden-valley/life.js`, wired in by
`scene.js` and pinned by `descent/player.js`.
Tests: `scripts/test_world_clock.py` (3 checks), `scripts/test_hotspot_flow.py`
(8 checks) — all passing.
Preview: `exports/002-living-map-weather-v001.png` (one camera, four instants,
the cloud shadow crossing the vale), `exports/002-living-map-birds-v001.png`.

### Review (Session H)

What works: the map is an afternoon now. The light changes while you look at
it, and the seam did not notice.
What I can now change without AI: wind direction and strength, cloud scale and
drift, flock size and cruising height, ripple speed — all constants at the top
of one file.
One failure worth keeping: my first flock stepped `min(FIXED_STEP, remaining)`,
which quietly made the simulation depend on *how the caller sliced time* rather
than on time itself. It would have passed every visual check and failed the
seam, and the only reason it did not ship is that writing the determinism test
forced me to say out loud what "deterministic" meant.

Next 20-minute experiment: the season wave. The land class image already says
which texels are woodland, which are farmland and which are mown grass, and
each turns a different colour at a different time of year — so the wave is a
palette lookup against a class the ground already knows, driven by the clock
that now exists.

## Session I — Phase 4b: art direction, taken from the reference rather than described

Date: 9 Sep 2026
Intent in one sentence: Give the map a voice — and, per the brief, keep it close to the thing it is aimed at.
Tool/build/model: CSS, two open-licence typefaces, Playwright, no paid generation.

### One variable to explore

Every previous phase had a dataset to be right about. This one had a
judgement, and the brief settled it in four words: *keep it close to
inspiration*. So the question became how to do that honestly — how to take a
direction from explore.ownprimland.com without taking their assets.

### What happened

I stopped describing the reference and read it. `curl` its Nuxt bundle,
`grep` the stylesheet:

```
@font-face families   inferi · centra · petitserif
CSS variables         --font-family-display, --font-family-serif, --font-family-sans
palette               #fffbe7 #fffdf3 #efeae6   warm paper
                      #798d73 #a8a98f #4a6b4a   sage
                      #a8611a #eab279 #f7d9bb   burnt amber
```

That is a whole direction in three lines, and it is not a guess. Their faces
are Inferi (Blaze Type) and Centra (Sharp Type), both commercial and neither
redistributable, so ours are Cormorant Garamond and Jost — open licence,
same register, vendored rather than linked because a webfont that arrives
late would change what is on screen between one capture run and the next.
The palette is ours, sampled from the world instead of their stylesheet: the
farmland green the terrain is painted with, the warmth of the 0xffe0b5 sun,
the slate the Doughnut is picked out in. Close, and none of it theirs.

Four things changed:

1. **The opening** — a title over a landscape already in motion, the camera
   easing in for fifteen seconds behind the words. Their structure exactly: a
   tracked-out overline, a big serif name with one word in italic, one line
   of invitation, an *Explore the map* pill. The move matters more than the
   words: by the time the title has gone, the map is somewhere you have
   watched rather than a thing you have been handed.
2. **Markers that are planted rather than floating** — a pin on the ground, a
   hairline stem, the label above it. The stem is the whole difference
   between a label that belongs to a point on the map and browser chrome
   sitting on a picture of one. They fade with distance, because three labels
   shouting equally from a 2 km box is a legend, not a place.
3. **The place panel** in cream, name in the display serif, and the
   attribution *stepping aside* when it opens rather than going out — OGL and
   ODbL both require it to stay visible.
4. **A shallow bottom vignette** — seating the credit line against sunlit
   farmland, the one place on this map where cream type has nothing to sit
   on, and giving a still its bottom weight.

### The find that was not the point but is the best part

The case study for the reference describes their hardest problem as
"realistic low-poly trees and foliage that would be duplicated and scattered
across an entire vast landscape without crushing performance", and their
atmosphere as "ambient nature sounds, birdsong, fog, drifting clouds, and
even the ability to change seasons".

We built the trees in Phase 3 and the drifting clouds and birds in Phase 4a,
from a different direction entirely — because a surveyed place needed them,
not because the reference had them. The season wave, which this plan had
parked at Phase 6, turns out to be *their* signature move too, and it moves
up: the land class image already knows which texels are woodland, farmland
and mown grass, and Phase 4a built the clock it would run on.

### What is still missing

Sound. The reference opens with ambient nature audio and a *start without
audio* link, and it is obviously right — but it needs a recording, and
shipping the control without the file would be a dead switch. It is the only
part of this phase waiting on an asset rather than a decision.

### Saved outputs

Source: `experiments/002-living-map/golden-valley/direction.css` (everything
with a colour or a typeface in it now lives in one file), the opening in
`golden-valley/main.js`.
Fonts: `terrain/vendor/fonts/` with a README naming both licences.
Tests: 8 hotspot checks — updated to walk through the opening rather than
skip it with a parameter no visitor has — and 3 clock checks, all passing.
Preview: `exports/002-living-map-direction-v001.png`,
`exports/002-living-map-markers-v001.png`.

### Review (Session I)

What works: it stops looking like a tool. The opening in particular does the
job the plan has been asking for since "I can't see the vision" — it says
what this is before it says what it does.
What I can now change without AI: the entire look, from one CSS file with
eleven custom properties at the top, without opening a line of JavaScript.
One failure worth keeping: my first pass drew the markers, the credit and the
hint over the title card, because I built the opening as a layer rather than
as a state. Three lines of `body.intro-open` fixed it, but the lesson is that
"an overlay" and "a moment in a sequence" are different things and I had
built the first while designing the second.

Next 20-minute experiment: the season wave — one palette per land class per
season, crossing the vale on the Phase 4a clock rather than cutting.

## Session J — structure passes, and the ladder that decides the Blender question

Date: 9 Sep 2026
Intent in one sentence: Build what a generator should actually be conditioned on, and a cheapest-first ladder that answers "do we need a Blender session?" with evidence instead of opinion.
Tool/build/model: Three.js override materials, Playwright capture, fal client, no paid generation yet.

### One variable to explore

Dex's proposal: feed the 3D structure into image and video generators for
hyper-real zoom sections, and spend less time in Blender. The question under
it is whether a generator needs our render to be **realistic** or merely
**unambiguous** — and the answer decides where the next few sessions go.

### What happened

Four passes, from one camera at one instant, wind off and birds hidden:

| pass | what it carries |
|---|---|
| beauty | composition, light, colour |
| depth | linear view depth, near white, **range fitted to the frame** |
| normal | world-space normals — what says a roof is a roof and not a paving slab |
| mask | flat colour by class: building, road, water, field, wood, tree |

The mask is the one worth pointing at. It separates carriageway from pasture
from water from roof **without a single extra mesh**, because Phase 2 wrote a
class per square metre and this is the second thing to read it. A
segmentation-conditioned model can now be told which colour means roof.

### Three things that had to be right, and one that was not

1. **The depth range is fitted, not given.** A hand-picked 40 m near plane on
   a view whose nearest ground is 90 m away turned the whole approach shot
   white. The pass now renders once with distance packed across 24 bits, reads
   it back, takes the 2nd and 98th percentiles of the non-sky pixels, and
   re-renders with those — so one chimney at the horizon cannot flatten the
   town. The approach view fits to 71–824 m and says so in the sidecar.
2. **A structure pass is data, not a picture.** The first version inherited
   the scene's ACES tone mapping and sRGB output, so every depth, normal and
   class value was quietly gamma-warped on the way out. Tone mapping off,
   linear output, and mask colours set with `setHex(v, LinearSRGBColorSpace)`
   so the pixel equals the number in the sidecar. A filmic curve applied to a
   measurement is just a corrupted measurement.
3. **The wind had to stop.** Depth and normal render through an override
   material, which does not carry the tree material's sway — so a swaying
   beauty frame and a still depth frame would disagree about where the canopy
   is by a metre, which is exactly what a depth-conditioned model turns into
   a smear. `setStructureMode` zeroes the wind and hides the flock.

And the one that was not right, found by accident:

**The land cover textures were never awaited.** `TextureLoader.load` fires
and forgets, so `buildWorld` could resolve — and `__terrainReady` could go
true — before either the colour or the class image had arrived. Found because
the class mask came back entirely `farmland`: the shader was sampling a blank
texture, which decodes as class 0.

Then it turned out to be much worse than a cosmetic race. Re-capturing the
descent and diffing the new frame 0 against the anchor that had been
committed that morning:

```
  frame A, old capture vs new:  mean 12.35 % of 255
                                45.8 % of pixels differing by more than 8
  frame 1 vs frame 0, new:      mean  0.26 %   (ordinary camera motion)
```

The old anchor had **no land cover on it at all** — two square kilometres of
near-black ground with the buildings floating on it. That was the frame about
to be handed to a paid generator, and the frame the control clip starts on.

The part worth keeping is *why the seam measurement said nothing*. It
compares the clip's first frame against the live render at the same instant,
and both came from the same capture run, so both were equally black. The
measurement reported 0.704 % and was telling the truth: the two images agreed
beautifully about a world that did not exist. A measurement of *agreement*
cannot see an error that both sides share, and this project has been leaning
on exactly that measurement for four sessions.

Both textures are awaited now, the descent is re-captured, and the seam is
0.823 % / 0.935 % — the in-seam is *worse* than yesterday's 0.704 %, which is
the correct direction: frame 0 now carries a fully textured world, and there
is more in it for the codec to lose.

### And a second one, from the same re-capture

The interaction test started failing the clip check again, and this time it
was not the container. The player had a wall-clock budget on the *whole*
descent — load plus fade plus playback plus a margin — and the diagnostic
showed the clip loading, playing, and reaching 4.00 s of 4.00 s before the
budget fired anyway and threw the viewer into the live fallback. The descent
had simply taken longer in wall time than the budget, because the 900 ms
fly-in takes half a minute on a page rendering at four seconds a frame.

That is a real bug for a real person: a viewer on a throttled phone is
exactly who the fallback exists for, and a wall-clock budget takes the clip
away from them for being slow rather than for being broken. The guard now
watches *progress* — the clip must become playable within 25 s, and must not
go 8 s without its clock advancing — and nothing is timed against the page.

Worth noting how close it came to being written off: I had a ready-made
explanation ("this container renders at a frame every four seconds") that
was true, relevant, and not the cause.

### The ladder

`scripts/generation_ladder.py`, four rungs, each a gate on the next, about
three pounds for the lot:

```
  0  dry-run        free      prints every request, spends nothing
  1  still, beauty  pennies   our render → photoreal. Does it keep the town?
  2  still, depth   pennies   the same view conditioned on structure instead
  3  video, low     ~£0.40    a departure from the low approach — the easy case
  4  video, aerial  ~£0.40    the same from the wide shot — Session B's hard case
```

Rung 2 beating rung 1 is the most interesting single result available: it
would mean the geometry is doing the work, and that adding surface detail —
in Blender or anywhere else — is beside the point.

The brief tells whoever runs it to look at the **failure mode, not the
score**. Wrong buildings is a conditioning problem; plastic is a prompt
problem; brick-versus-render is a material-hint problem, and material hints
are cheap raster work in the pipeline we own. Only a failure that *geometry*
would fix earns a Blender session.

### Saved outputs

Source: `experiments/002-living-map/passes/`, `scripts/capture_passes.py`,
`scripts/generation_ladder.py`.
Images: `experiments/002-living-map/passes/out/` — three views, four passes
each, committed so the paid session starts from identical inputs.
Brief: `experiments/002-living-map/descent/LADDER-SESSION.md`.

### Review (Session J)

What works: the map can now hand a generator four different descriptions of
the same instant, and every number in them means something because the
sidecar says what.
What I can now change without AI: the views, the depth fitting percentiles,
the mask palette, and every prompt in the ladder.
One failure worth keeping: I also managed to write a fix, run the test, watch
it fail, and only then notice that my edit had never applied — a string
replacement that matched nothing and said nothing. Two comment lines I had
not accounted for. Check that the change is in the file before concluding
anything about the change.
Another: I built the mask, looked at it, saw green fields
and red buildings and nearly called it done — the roads were missing and I
almost read that as "roads are part of the ground texture, fair enough". They
were missing because the texture had not loaded. Two of the three things I
had to fix in this session were found by counting pixels rather than by
looking at them.

Next 20-minute experiment: the ladder itself, on a machine with keys.
