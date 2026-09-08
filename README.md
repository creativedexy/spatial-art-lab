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

- **The living map** — maps × generative video: an explorable stylised world of Cheltenham with generated zoom-in transitions and a season wave, targeting the Golden Valley development as exemplar. See [the plan](plans/living-map-plan.md) and [Sprint 1 brief](experiments/002-living-map/brief.md).

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

- **Living map, Sprint 1 Session A (8 Sep 2026):** real Cheltenham terrain in the browser from EA LiDAR (WCS, one request), recognisable escarpment and Cleeve Hill, georeferenced markers. See [the terrain page](experiments/002-living-map/terrain/index.html) (serve the folder over HTTP), [the session log](experiments/002-living-map/session-log.md) and [the still](exports/002-living-map-terrain-v001.png).
- **Sprint 0 (8 Sep 2026):** environment logged (M5 Pro, 20-core GPU, 48 GB; Blender 5.2.1 LTS; TouchDesigner 2025.33230). Blender half complete — a scripted light study with three saved stills and a reopenable source file. See [the session log](experiments/000-sprint-zero/session-log.md) and [the light study](experiments/000-sprint-zero/light-study.html). TouchDesigner half is pending and specified in [the build sheet](experiments/000-sprint-zero/touchdesigner-build-sheet.md). No paid AI generation has been run yet.
