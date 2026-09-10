# Google Photorealistic 3D Tiles: live-layer test

A throwaway test of whether photogrammetry of the real town, streamed live,
is good enough up close to be the map's context layer. It uses our plates'
own cameras, so it compares directly with `generate/` plates and photos.

**Terms that decide what this can ever be** (Map Tiles API policies, checked
10 Sep 2026): our own 3D objects may be overlaid; **no pre-fetching or
caching, no offline use**; attributions must be shown in a line; promotional
video under 30 s and not resold. So tiles can only be a *live* layer in the web
map. They must never feed plates, Codex, or a film.

**Cost:** billed per root tileset request (one per session); tile requests are
unmetered. A 1,000-a-month free allowance was reported for this Enterprise SKU.
A test is a handful of sessions.

## Run

Needs a Google Maps Platform key with the Map Tiles API enabled, stored in the
keychain. Write it to a gitignored `key.js`, never to the repo:

    printf 'window.GOOGLE_TILES_KEY=%s;\n' "\"$(security find-generic-password -w -a "$USER" -s <KEYCHAIN_NAME>)\"" \
      > experiments/002-living-map/tiles-test/key.js

Then serve this folder and open `index.html`.

## Result, 10 Sep 2026

Run at our plates' own cameras, 1280 × 720, `3d-tiles-renderer` 0.5.2. No
screenshots are kept in the repo: the terms forbid caching tile content.

| camera | verdict |
|---|---|
| GCHQ close (`close-2045/gchq-meadow.json`) | **photoreal.** Ribbed roof, courtyard, annexes, full car parks, Hesters Way, real hills on the horizon |
| 002 (`gchq/plate.json`) | **photoreal, and it registers.** The ring spans about x 315–1052 against our surveyed lock of 312–1064 (by eye): two independent sources agree on where GCHQ is |
| 003 A wide (`golden-valley-2045/a-cyber-central.json`) | **good in the middle distance, melted in the foreground.** Near ground and trees at this low oblique are smeared photogrammetry blobs |

**What it means**

1. For the **existing town, from about 150 m up**, the tiles look like the
   Codex photos and cost nothing to generate. Most of the realism problem in
   the live map disappears for today's Cheltenham.
2. They bring the **horizon and the far vale** for free, which is the gap 003
   found and a terrain skirt was proposed for.
3. They show **today only**. The 2045 scheme would be our own geometry
   overlaid (the procedural facades of task 001), which the terms allow
   because it is not derived from the tiles.
4. **Low cameras melt.** The live map should keep its cameras up, which it
   already does (`RIDE` is 14 m for other reasons, and the plates sit at
   80–250 m).
5. **Live only.** Tiles can never feed plates, Codex or a film; the measured
   map stays the source of every generated image.

**The keying detail worth keeping:** do not trust `ReorientationPlugin`'s axis
convention. Measure east, north and up on `tiles.ellipsoid` at the origin and
place cameras from that; see `basis()` in `index.html`.

**Before any public launch:** check the current per-1,000 price for root
tileset requests. The test is inside the free allowance; a public site's cost
scales with visitors.
