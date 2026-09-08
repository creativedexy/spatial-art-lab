# Spatial art lab

A home for learning 3D modelling, generative visuals and world-building with AI through small, finished artworks.

Start with [the visual moodboard](inspiration/index.html), then [the learning plan](plans/learning-plan.md). The moodboard is a local HTML file: open it in a browser. No build, account or network connection is needed to view the saved captures and notes; external source links require the internet.

## First things to make

1. Cosmic breath — a monochrome TouchDesigner motion study.
2. Impossible artefact — an original Meshy object, refined and lit in Blender.
3. Exploded assembly — a short controllable animation of the artefact.
4. Ghost ecology — a sparse spatial field responding to a slow signal or sound.
5. Memory chamber — one World Labs environment, inspected and exported.
6. World as interface — an interactive object or room in the browser.

The plan assumes three 60–90 minute sessions per week and can stretch or compress. Start with the [first experiment brief](experiments/001-cosmic-breath/brief.md).

## Projects

- **The living map** — maps × generative video: an explorable stylised world of Cheltenham with generated zoom-in transitions and a season wave, targeting the Golden Valley development as exemplar. See [the plan](plans/living-map-plan.md), [the look development plan](plans/living-map-lookdev-plan.md) — how it gets from massing model to the thing we actually want — and the [Sprint 1 brief](experiments/002-living-map/brief.md).

## Where things live

- `inspiration/`: the visual board, source records and credited study captures.
- `plans/`: learning path, tool roles and AI collaboration prompts.
- `experiments/`: one folder per experiment, each with a brief and session notes.
- `assets/`: original generated and imported assets; preserve original exports.
- `exports/`: selected stills, films and interactive deliverables.
- `scripts/`: repeatable helpers. `build_library.py` currently contains the seed records and renders JSON, Markdown and HTML; edit its records and rerun to update all three consistently. Browser notes are separate and should be exported for backup.

Use names such as `002-artefact/blender/artefact-v003.blend` and `exports/002-artefact-still-v003.png`. Log prompts, versions, seeds when supplied, credits, failures and the setting that made the largest difference. Keep inspiration screenshots attributed as study material; use original or appropriately licensed inputs for finished artworks.

All seven supplied references were identified and captured.

## Progress

- **Living map, Phase 1 look development (8 Sep 2026):** the same geometry and the same data, lit. A low afternoon sun casting real shadows, filmic tone mapping, a graded sky the fog agrees with, and ground colour driven by slope — no new data at all, and it takes the map from planning document to architectural render. See [the lookdev page](experiments/002-living-map/lookdev/index.html) (serve the folder over HTTP), [the before/after](exports/002-living-map-lookdev-v001.png) and [the phased plan](plans/living-map-lookdev-plan.md) for what each remaining phase buys.
- **Living map, Session D — hotspot descents (8 Sep 2026):** the map is now explorable: click a place, descend into it, read it, return. Three places, each with a descent path and an *optional* clip — the doughnut arrives by pre-rendered descent, the other two fly the identical path live, so the map is complete before any video is generated and improves the moment one lands. End-to-end interaction test in `scripts/test_hotspot_flow.py`. See [the map](experiments/002-living-map/golden-valley/index.html) (serve the folder over HTTP), [the session log](experiments/002-living-map/session-log.md) and [the contact sheet](exports/002-living-map-hotspots-v001.png).
- **Living map, Session B — the first generated descent (8 Sep 2026):** one Kling 1.6 Pro clip, generated locally from our own two anchor frames, and it inverts the assumption Session C was built on. The landing hands back at 1.43 % but the *departure* is twice as bad at 2.79 %, because the wide aerial holds several thousand tiny buildings the model cannot redraw exactly while the landing holds a handful of large masses it can. Not framing and not tone — both were ruled out. So cross-fade the departure and cut the landing, the opposite of the plan. The clay style held completely, with no photoreal drift. Veo remains unrun for want of a key. See [the session log](experiments/002-living-map/session-log.md), [the numbers](experiments/002-living-map/descent/fal/seam-report.json) and [the contact sheet](exports/002-living-map-descent-fal-sheet-v001.png).
- **Living map, Session C — the seam holds (8 Sep 2026):** the hand-off between the live map and a pre-rendered descent is invisible, and now measured rather than argued about. A control clip rendered from the map's own scene puts both seams at ~0.5% mean pixel difference; the surprise is that a ten-times-larger near-lossless encode barely improves on it, while five metres of landing drift makes it five times worse. Landing accuracy is the whole game. See [the seam test](experiments/002-living-map/descent/seam-test/index.html) (serve the folder over HTTP), [the numbers](experiments/002-living-map/descent/seam-report.json), [the session log](experiments/002-living-map/session-log.md) and [the contact sheet](exports/002-living-map-descent-sheet-v001.png).
- **Living map, Golden Valley vertical slice (8 Sep 2026):** full 1 m LiDAR terrain over west Cheltenham with all 4,033 OSM buildings extruded to their DSM−DTM measured heights, true scale — GCHQ's doughnut (courtyard and all) proves the map ties to the real place. Descent-generation pipeline ready (`scripts/generate_descent.py`), awaiting a Gemini key. See [the slice page](experiments/002-living-map/golden-valley/index.html), [the session log](experiments/002-living-map/session-log.md) and [the still](exports/002-living-map-goldenvalley-v001.png).
- **Living map, Sprint 1 Session A (8 Sep 2026):** real Cheltenham terrain in the browser from EA LiDAR (WCS, one request), recognisable escarpment and Cleeve Hill, georeferenced markers. See [the terrain page](experiments/002-living-map/terrain/index.html) (serve the folder over HTTP), [the session log](experiments/002-living-map/session-log.md) and [the still](exports/002-living-map-terrain-v001.png).
- **Sprint 0 (8 Sep 2026):** environment logged (M5 Pro, 20-core GPU, 48 GB; Blender 5.2.1 LTS; TouchDesigner 2025.33230). Blender half complete — a scripted light study with three saved stills and a reopenable source file. See [the session log](experiments/000-sprint-zero/session-log.md) and [the light study](experiments/000-sprint-zero/light-study.html). TouchDesigner half is pending and specified in [the build sheet](experiments/000-sprint-zero/touchdesigner-build-sheet.md). No paid AI generation has been run yet.
