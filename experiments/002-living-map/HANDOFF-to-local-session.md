# Handover to the local session — 12 Sep 2026

The cloud session is closing. Everything below is committed and pushed on
`claude/maps-generative-video-ia8733`, which is **4 commits ahead of `main`**
and carries your phase 12 step 1 merged in.

Your two measured numbers landed while I was working on the horizon and are in
the branch: `MELT_METRES = 105`, `GROUND_OFFSET_METRES = -0.14`. Thank you for
quoting the spread — 0.46 m is the useful half of that report.

---

## What changed while you were measuring

### Phase 11 — the piece stopped being a map (merged to `main`, `aa622a5`)

Three notes from Dex that turned out to be one note: no slider, use the
photogrammetry, and *it is still a 3d map you move around*.

- **The year slider is a toggle.** `TODAY ⟷ 2045`, two resting states, a 1.4 s
  crossing between them. The shader is untouched — `setWave` still takes any
  number and **`?wave=0.45` still holds the front half way for a capture**, so
  every plate script works exactly as before.
- **Free flight is gone.** The camera lives at one of five composed shots in
  `golden-valley/viewpoints.json` and moves between them. Orbit survives as a
  fenced lean: 34° of swing, 16° of tilt, no pan, no dolly, reset on every
  move. **`?clean=1&cam=…&look=…` is exempt** — it had to be, or every plate in
  `generate/` would have been silently re-framed.
- **One route per ground point, per shot.** Four of the eight markers stand on
  the same ground at (123, 64): `gchq`, `gchq-meadow`, `cyber-central` and the
  `doughnut` descent. Declutter had been quietly discarding three of them since
  the markers landed. `test_viewpoints.py` now fails if any shot offers two
  markers within 60 m.

### The horizon (`bb9e3fe`) — this one touches your work

The map used to end at a cliff. It now has the skyline this place actually has,
from **OS Terrain 50** (OGL v3, same licence family as the LiDAR): 24 km at
50 m for the escarpment, 150 km at 500 m for the Malverns and Wales. **280 KB**,
first frame unchanged at 3.0 s.

**The bit that concerns phase 12.** Our far field stands down wherever the
tiles are showing, in `main.js`:

```js
const want = tiles.wantsShowing(above);
if (want !== tiles.showing) {
  tiles.setShowing(want);
  scene.userData.farField?.setShowing(!want);   // ours hides when theirs shows
}
```

So with a key, above your 105 m melt: Google's horizon. Below it, tiles go and
**ours comes back**, which is exactly what a low camera needs. Worth a look with
the key on — I could not test that path, and the thing to watch for is the
moment of the swap, where two different horizons trade places. If it reads as a
flinch, the fix is probably to cross-fade rather than switch, and the hysteresis
you already have is the place to hang it.

Also changed and relevant to anything you capture:

- **The air is different.** Fog went from `0.00022` to `0.000033` — the old
  value gave 4.5 km of visibility, right for a 2 km world and wrong the moment
  there is a horizon behind it.
- **The camera far plane is 180 km** (was 20 km) and **the sky dome is 150 km**
  (was 9 km). Those three numbers are now coupled: the dome must be bigger than
  the land and smaller than the far plane. Getting it wrong does not draw a
  bigger sky, it draws **no** sky — ask me how I know.
- **Every approved plate has moved** and the guard rejects the change: 10 of 12,
  worst 17.9% of pixels. It is the right rejection and the wrong conclusion —
  the foreground is untouched in all of them and what changed is the top of the
  frame, where sky became land. They are **re-baselined, not reverted**. If you
  regenerate anything from a plate, re-render it first.

---

## Two things to be careful of

1. **`test_public_build.py`'s byte count is a floor, not the payload figure.**
   It counts whichever responses have started when it stops watching, and this
   map defers half its load on purpose — so adding a 0.27 MB horizon moved its
   reported first load *down*, 6.71 MB to 5.25. It now waits longer and is
   documented as a ceiling check. **The number to quote is
   `measure_payload.py --site dist`: 6.46 MB.**

2. **GitHub Pages deploys twice on every push to `main`.** Ours, and GitHub's
   own branch build, which Jekyll-builds the repo root and knows nothing about
   `dist/`. Whichever finishes last wins, and on 12 Sep theirs did — the public
   URL served a README and `/golden-valley/` 404ed. Restored by re-running the
   workflow. **The fix is one setting only Dex can change:** Settings → Pages →
   Build and deployment → Source: **GitHub Actions**. Until then, check the live
   URL after any merge to `main`. The deploy job now fails loudly if the map is
   not at the URL afterwards.

---

## Where phase 12 stands

Step 1 is done — your numbers. What the plan has next, from
[from map to piece](../../plans/living-map-the-piece.md):

- **Tiles as the substrate, not a layer**, wherever a key exists.
- **Our today-geometry retires.** Existing buildings, existing trees and land
  cover have one job left: the 2045 scheme, and the keyless fallback. This is a
  *subtraction* phase — the payload should go down, not up.
- **The 2045 scheme learns to stand in a photograph's light.** Matching the
  tiles' exposure and shadow direction is a measurement, not an art problem,
  and it is what makes the montage read as one image rather than two.

Settled and not worth reopening: the **public URL stays ours** (no key, no
bill, no terms to honour) and a **keyed build** goes in front of a client.
`build_site.py` already does that split for the Meshy models.

## Suites as they stand

`test_far_field.py` 11/11 (new) · `test_viewpoints.py` 16/16 (new) ·
`test_year_switch.py` 20/20 · `test_places.py` 19/19 ·
`test_public_build.py` 11/11 · `test_tiles_frame.py` 3/3 ·
`test_hotspot_flow.py` green · `guard_plates.py` rejects, deliberately, and is
re-baselined on `payload/plates/after-horizon`.
