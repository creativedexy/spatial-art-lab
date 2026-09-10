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
