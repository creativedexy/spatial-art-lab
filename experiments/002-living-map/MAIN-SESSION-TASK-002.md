# Main session, task 002: Google's photogrammetry becomes "today"

**From:** Dex, via the local session, 10 Sep 2026: "google API looks great".
**Owner:** the main (cloud) session. The local session holds the key and
verifies live.
**Evidence:** `tiles-test/` (page and README). At the plates' own cameras,
from about 150 m up, Google Photorealistic 3D Tiles are photoreal, bring the
horizon and the far vale with them, and **GCHQ's ring lands within a few
pixels of our surveyed lock**. The 003 A camera, low and wide, melts in the
foreground.

## The idea

Today's Cheltenham stops being our stylised model and becomes the real place,
streamed. The 2045 scheme stays ours: the written facades, the NCIC wedge,
the paths and the places, overlaid on the photogrammetry. The year dial then
sweeps our future across a real town.

## Part 0: fix the anchor tool (small, do first)

`scripts/measure_leg_anchors.py` crashes on
`generate/close-2045/campus-ncic.json`: `IndexError` in the height lookup
(`at`, line 88), from `describe` (line 158). A projected feature samples
ground outside the height field. Clamp or skip samples outside it. Plates that
look across the box edge are now normal.

## Part 1: tiles as the "today" layer, with a keyless fallback

- **Library:** `3d-tiles-renderer` 0.5.2 on three ≥ 0.167. Two gotchas already
  paid for: map `three/addons/` to `three/examples/jsm/`, and import
  `GoogleCloudAuthPlugin` from `3d-tiles-renderer/core/plugins`, not
  `/three/plugins`.
- **Placing it:** do not trust `ReorientationPlugin`'s axis convention (it put
  the first test facing the wrong way). Measure east, north and up on
  `tiles.ellipsoid` at the origin and place everything from that basis: see
  `basis()` and `local()` in `tiles-test/index.html`. Origin: BNG
  391400 222400 = **51.900076, −2.126397**, at ellipsoid height **48.6 m**
  (the geoid here), so local y equals our AOD heights.
- **The key:** you have none and should never have one. Read it at run time
  from a gitignored `key.js` (`window.GOOGLE_TILES_KEY`), as `tiles-test` does.
  **No key → the current measured map, unchanged.** That is the path your test
  suites run, and it must stay complete, not a blank screen.
- **Our town hides where the tiles cover it:** existing buildings, trees and
  land cover are replaced by photogrammetry, so nothing doubles up. Keep our
  terrain as the collision and height source.
- **Low cameras melt.** Measure the altitude below which the tiles break up at
  the walk and hotspot cameras, and below it keep the measured map (`RIDE` is
  14 m). A written threshold, not a guess.
- **Cost control:** billing is per root tileset request, one per
  `TilesRenderer` created. **Create one per session and never recreate it** on
  a toggle, a resize or a year change. A page that rebuilds it on every dial
  move is a bill.

## Part 2: 2045 on top of the real town

- The written campus facades, the NCIC wedge, glasshouses and homes rise from
  the photogrammetry ground as they do now. Sit each one's base on our DSM
  base, and measure the vertical offset against the tiles at three or four
  points (GCHQ, the campus field, the brook). Report it rather than hiding it.
- **GCHQ's 2045 meadow roof:** overlay our own ring roof (from our LiDAR/OSM
  footprint) on the photogrammetry. That is allowed; see the terms below.
- 2045 orchards, wetland and hedges cannot be painted onto tiles, which may not
  be modified. Where they matter, they are our own instances on top. Where they
  do not, leave today's fields showing, and say which.
- The places from task 001 keep landing on their plate cameras, and the Codex
  photos now crossfade from a map that already looks real.

## The terms (Map Tiles API policies, checked 10 Sep 2026)

- **Attribution:** gather `tiles.getAttributions()`, show it in one line,
  always visible, including at 390 px wide.
- **No pre-fetching or caching of tile content.** If the map gets a service
  worker, tile URLs are excluded from it.
- **No offline use.** Tiles never feed plates, Codex, or a film. The measured
  map stays the source of every generated image.
- Own 3D objects may be overlaid only if they are not traced or derived from
  the tiles. Ours come from LiDAR, OSM and written rules, so they qualify.
- Promotional video featuring tiles must be under 30 s and not resold.

## Done when

1. With a key, the hub view and GCHQ are photogrammetry and the year dial
   raises the 2045 scheme on top, with the attribution line showing, on a
   phone.
2. With no key, every existing suite passes and the map looks exactly as
   today.
3. The melt threshold and the vertical offset are measured and written in the
   commit.

Then drop a line in `generate/README.md`. The local session will verify it
live with the key and report back.

## Not in scope

A production key and a public launch: Dex creates a separate
domain-restricted key, and the per-1,000 price gets checked first, because a
public site's cost grows with visitors. Also not: video, transition effects,
far-field terrain (the tiles bring the horizon), "before" frames.


---

## Result — main session, 10 Sep 2026

**Parts 0, 1 and 2 built. The two numbers are still unmeasured, by design.**

### Part 0 was not what it looked like

The crash was reported as a projected feature sampling ground outside the
height field. It was not — that lookup had clamped all along. **Phase 7 packed
the heightmap and taught only the browser to read it**, and three python
scripts went on indexing the file as four million uint16s: the anchor tool,
`golden_valley_2045.py` (the generator for the whole scheme) and
`find_open_land.py` (the survey its siting rests on). Only the first crashed
loudly enough to be noticed.

`test_heightmap.py` passed throughout, because the python it compared node
against was a copy of the decoder written inside the test. There is one reader
now — `scripts/heightfield.py` — and the test imports it.

Verified by re-running the 2045 generator: trees and footprints byte-identical,
building bases moved by **1 cm**, which is one quantisation step on a survey
whose own neighbouring cells differ by 2.19 cm. The scheme is reverted rather
than kept, because the approved plates were made against the committed one.

### Part 1: the layer

One `TilesRenderer`, made once, never rebuilt — billing is per root request.
Attribution read from the renderer every frame into a line that is always
visible, including at 390 px. No key means `tiles.js` returns null on its first
line and **the library is never fetched**: the public build is 6.76 MB and
11/11, unchanged.

The tiles move into our frame rather than the camera into theirs, because this
map already has a terrain, four thousand buildings, a path network and a wave
living in local metres. `ReorientationPlugin` still does the recentring — six
thousand kilometres from the origin a float has about a metre left — but its
axes are measured, not trusted.

### Part 2: the scheme on top

- **Our ground draws only where 2045 changes it.** The first version masked by
  the wave, which meant that once the front had crossed, our terrain covered
  the real town completely and the layer was pointless. It compares the two
  class maps instead: **68.6 ha of 400, 17.2%** — orchard 21.9, the ground
  under new buildings 17.9, wetland 15.5, agrivoltaic 9.6, new streets 2.5,
  scrub 1.3. The other 331 ha shows the real town through, including 126.6 ha
  of existing residential and 56.3 ha of farmland the scheme does not touch.
- **GCHQ's meadow roof is the one part of our town kept over the tiles**, laid
  on the real ring and faded in with the front rather than switched — a meadow
  appearing all at once on a photograph of a metal roof reads as a glitch.
  Overlaying our geometry is allowed; nothing modifies a tile.
- **2045 trees, hedges and orchards** are already our own instances and stand
  on the photogrammetry unchanged.
- **The melt switch has two thresholds**, 60 m down and 75 m up. One would
  make the walk — which rides at a fixed height over rolling ground — flip the
  whole town between two versions of itself along a route.
- **The places are untouched** and still land on their plate cameras.

### The two numbers

`MELT_METRES = 60` and `GROUND_OFFSET_METRES = 0` are **placeholders, marked as
such in the source**. There is no key in the cloud session and there should not
be one. `scripts/probe_tiles.py` is the measurement: it drops a ray onto the
tiles at GCHQ, the campus field, the brook and Princess Elizabeth Way and
prints the offset at each plus the value to paste, then walks a camera down
twelve altitudes and finds where the finest tiles that exist still cannot meet
the error target. `?tileLift=-0.7` tries a value live without an edit.

`scripts/test_tiles_frame.py` (3/3) checks the arithmetic that needs no key,
and earned itself on the first run: **the lift was applied with the sign
inverted**, which would have put the whole town out by twice the offset with
nothing to show for it. It also holds the sign that catches everyone — north
is −z.

### Tests

`test_places.py` 19/19, `test_public_build.py` 11/11, `test_year_switch.py`
14/14, `test_path_network.py` 12/12, `test_heightmap.py` 6/6,
`test_tiles_frame.py` 3/3 (new).

### For the local session

Run `python3 scripts/probe_tiles.py` with the key in place, paste both numbers
into `golden-valley/tiles.js`, and say what the spread was — a single vertical
shift is an approximation and the residual is worth stating rather than hiding.


---

## Step 1 is done, and the rest of the context moved — 12 Sep 2026

The local session measured both numbers (`MELT_METRES = 105`,
`GROUND_OFFSET_METRES = -0.14`, spread 0.46 m) and they are in `tiles.js`.

Meanwhile phase 11 landed and the map grew a horizon, and both touch this task:
the interface, the camera and the atmosphere are not what this brief was
written against. See
[the handover](HANDOFF-to-local-session.md) — in particular that our far field
now hides wherever the tiles show, which is a swap nobody has watched happen
with a key in place.
