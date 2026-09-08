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
