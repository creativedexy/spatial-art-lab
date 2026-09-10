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
