# Phase 12 step 3 — the subtraction, inventory

**Produced by Codex** (`gpt-5.6-sol`, read-only over the repo at `665efcd`,
12 Sep 2026) as a work package, then checked here. Codex is a different model
with no memory of how this codebase got the way it is, which is why it was
given the inventory: it counts what is there rather than what we remember
putting there.

**What I verified myself, and it holds:**

- The three unreferenced photographs and their exact total, **983,940 B**.
  `grep` across every `.js`, `.json` and `.html` under `experiments/002-living-map`
  returns zero references to `contact-sheet`, `a-start-photo` or `b-end-photo`,
  and `places.json` names exactly five photographs. **Acted on already** — see
  the commit that reads the photograph list from `places.json` instead of
  globbing `generate/*/out/*.webp`.
- `build_site.py` has no keyed profile: it writes a null key into both outputs.

**What I did NOT verify and the next person must:** every other byte count in
the table below, the runtime-cost claims, and the ordering. They are Codex's
readings, they were right everywhere I spot-checked, and they are still claims.

**Ownership.** Items 2 to 7 are map-code surgery and belong to the session that
owns `golden-valley/`. This file is the handoff, not a change.

---

### Asset inventory

`build_site.py` does not currently produce a keyed build. It splits public versus `--internal` models, then writes a null key into both outputs ([build_site.py](/Users/user/Projects/3D%20Design/scripts/build_site.py:62), [build_site.py](/Users/user/Projects/3D%20Design/scripts/build_site.py:97)). A tiles-capable output therefore needs a third profile; the key itself should remain externally supplied.

| Asset | On-disk size | When / loader | Needed by 2045? | Needed by fallback? |
|---|---:|---|---|---|
| `descent/clips/descent-control.webm` | 2,774,574 B / 2.646 MiB | Idle-prefetched by `player.prefetchClips()` in [main.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/main.js:144), implemented in [player.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/descent/player.js:285) | No. It is a pre-rendered “today” descent from the measured scene. | Yes by the current authored/test contract, although live flight is technically a fallback. |
| `golden-valley/gv-buildings.json` | 986,939 B / 0.941 MiB | Startup, `loadFootprints()` in [buildings.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/buildings.js:35) | Only one of 4,033 records: GCHQ, whose roof becomes meadow. That record is 2,327 B minified. | Yes: all 4,033 buildings, including the keyed low-camera fallback. |
| `generate/gchq/out/gchq-photo.webp` | 380,488 B / 0.363 MiB | On demand when the “gchq” place is reached; `photo.src` in [places.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/places.js:152) | No. | Yes if the current “today photograph as a place” remains. |
| `golden-valley/gv-landcover.webp` | 290,676 B / 0.277 MiB | Startup, `TextureLoader` in [landcover.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/landcover.js:44) | Yes in the current implementation: the 2045 shader mixes from this map to the future map. A keyed-specific shader could fade the future map directly over the photograph and eliminate it. | Yes. |
| `golden-valley/gv-far-near.bin.gz` | 191,819 B / 0.183 MiB | Startup through metadata, [farfield.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/farfield.js:77) | No while tiles show; Google supplies the horizon. | Yes, including the tiles-off low-camera state if its horizon must remain complete. |
| `golden-valley/gv-landclass.webp` | 103,218 B / 0.098 MiB | Startup via [landcover.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/landcover.js:90); called once for `life.js` and again by [future.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/future.js:503) | Yes. It is compared with `gv-2045-landclass.webp` to decide which 68.6 ha may cover the tiles. | Yes, for present-day water and land classes. |
| `golden-valley/gv-far-far.bin.gz` | 95,046 B / 0.091 MiB | Startup through metadata, [farfield.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/farfield.js:77) | No while tiles show. | Yes. |
| `golden-valley/gv-trees.bin` | 73,728 B / 0.070 MiB | Startup, [landcover.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/landcover.js:137) | No. The 6,234 proposed trees come from `gv-2045-trees.bin`. | Yes: 9,216 existing trees, including the keyed low-camera fallback. |
| `golden-valley/gv-far-meta.json` | 1,087 B | Startup, [farfield.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/farfield.js:64) | No while tiles show. | Yes. |

The startup subset above totals **1,742,513 B / 1.662 MiB**. The video is deferred/prefetched and the GCHQ photograph is interaction-loaded, so neither belongs to a deterministic first-load subtraction.

There are also 983,940 B copied by the broad `generate/*/out/*.webp` glob but never referenced by the page:

| Shipped but never downloaded | Size |
|---|---:|
| `golden-valley-2045/out/contact-sheet.webp` | 323,580 B |
| `cheltenham-circular-footpath/out/a-start-photo.webp` | 277,548 B |
| `cheltenham-circular-footpath/out/b-end-photo.webp` | 382,812 B |

No code or JSON references any of these. Replace the `PHOTOS` glob in [build_site.py](/Users/user/Projects/3D%20Design/scripts/build_site.py:42) with the five paths actually named by `places.json`.

### Runtime work paid before tiles exist

`main.js` awaits the entire `buildWorld()` before calling `addTiles()` ([scene.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/scene.js:153), [main.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/main.js:368)). Consequently, the Google library and root tileset request do not even begin until all of this has finished:

| Work still performed | Cost that becomes dead once tiles show |
|---|---|
| Far-field construction | Two height streams are decompressed; 321,962 samples become two meshes totalling 633,976 triangles, with positions, colours, normals and indices. It is then hidden by `farField.setShowing(false)`. |
| Existing buildings | JSON for 4,033 buildings is parsed. Roughly two source geometries per building are created, roof normals computed, then merged into 12 meshes. All are uploaded, shader-patched, shadow-enabled and rendered during staging. With tiles showing, only `gchq:roof` survives. |
| Existing trees | 9,216 records are decoded; 9,216 terrain-height lookups, matrices and instance colours are produced across three instanced meshes. They are shader-patched, uploaded and staged once, then their parent is hidden. |
| Today colour texture | A 2,000×2,000 WebP is decoded, uploaded and mipmapped. `neutralGrade()` also loops over all 1,002,001 terrain vertices. The texture remains coupled to the future shader even though no present-day ground is visible. |
| Today class texture | `loadClassTexture()` is invoked twice, producing two Three textures for the same 2,000×2,000 image: one for water/life, one for the future comparison. The compressed HTTP object may cache, but the code creates two decode/upload objects. |
| Staging renders | Five pre-tile frames are deliberately rendered: terrain; far field; buildings; land cover; life and paths. Those renders compile and upload geometry which is about to be hidden, and they postpone the first Google request. |

`setShowing()` is effective at eliminating most continuing draw work, but only after the above costs have been paid ([tiles.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/tiles.js:290)):

- The hidden tree and far-field groups stop producing draw calls.
- Ten ordinary building meshes plus the GCHQ wall stop drawing; the building group remains visible solely to carry `gchq:roof`.
- Their parsed data, geometries, materials, textures and GPU buffers remain resident.
- The full terrain remains visible. At “today” its two million triangles are still submitted every frame and its fragment shader samples class maps before discarding every fragment. It also remains a shadow caster because the mask is absent from the depth material.
- The flock is not dead work: it remains visible over the tiles and still runs its 90-bird, pairwise simulation plus 90 matrix writes per frame.
- Paths, places, viewpoints, scheme geometry, future trees, sky and lighting remain live features.

### Subtraction order

| Order | Exact change | Bytes removed/deferred | Failure if wrong | Existing coverage |
|---:|---|---:|---|---|
| 1 | Stop copying the three unreferenced WebPs above. | **983,940 B from the built folder**; no first-load change | Only a future undocumented link could break. | None needed today; no current runtime references them. `test_places.py` already validates every photograph that *is* named by `places.json`. |
| 2 | When tiles are active, null the control hotspot’s `clip` before `prefetchClips()`, so it flies live. Do not merely omit the file: that causes a 404 and a 25-second wait before fallback. | **2,774,574 B eventual transfer** | The keyed GCHQ descent changes from video to live flight. | [test_hotspot_flow.py](/Users/user/Projects/3D%20Design/scripts/test_hotspot_flow.py:107) catches an accidental change to the keyless path. No keyed equivalent exists. |
| 3 | Do not build the far field before tiles. Lazy-load it if the camera is approaching the tiles-off state. | **287,952 B first-load** plus the full far-field construction | A tiles-off walk/arrival can expose the survey edge or blank horizon. | [test_far_field.py](/Users/user/Projects/3D%20Design/scripts/test_far_field.py:49) catches a global regression. |
| 4 | Do not build existing trees before tiles; lazy-load the fallback set. Keep `KINDS` and `unitTree()`, which build the 2045 trees. | **73,728 B first-load**, with disproportionately large CPU/GPU savings | Keyless or low-camera fallback becomes treeless. | Missing-file failures reach `test_public_build.py`; no existing test asserts the 9,216-tree count. `guard_plates.py` would catch the visual loss against a baseline. |
| 5 | Split GCHQ from the building corpus. Build its 2,327-byte footprint immediately for the meadow roof; lazy-load the other 4,032 buildings for fallback. | **984,612 B first-load** | Losing the retained record removes the meadow roof. Loading the bulk too late makes walks/arrivals temporarily building-free. | No structural test counts today’s buildings or asserts the GCHQ roof. `guard_plates.py` catches the keyless image change; `test_public_build.py` only catches a failed request/page error. |
| 6 | Give keyed terrain a direct future-map material: identify it by `name === "terrain"`, use the future texture only in changed/arrived pixels, and stop requiring `material.map` in [future.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/future.js:488). Lazy-load today’s colour texture only for fallback. | **290,676 B first-load** | If the current `material.map` discovery is removed without replacement, the entire future-ground blend silently fails. A wrong fade exposes model-coloured ground over the photograph. | `test_year_switch.py` checks wave state, not pixels. Only `guard_plates.py` offers visual coverage, and its `clean=1` path deliberately disables tiles. A keyed visual test is required. |
| 7 | Remove `gchq-photo.webp` only if “today as a generated photograph” is intentionally retired as a place. | **380,488 B on demand** | Visiting GCHQ loses its photograph/crossfade. | `test_places.py` catches global deletion via its file check, but does not exercise this particular place in-browser. |

The immediate phase-12 target from items 3–6 is:

```text
full buildings minus retained GCHQ     984,612 B
today colour texture                   290,676 B
today trees                             73,728 B
far-field metadata and two grids       287,952 B
                                      ───────────
total                                1,636,968 B = 1.561 MiB
```

Applied arithmetically to the reported 6.66 MiB, the keyed site-origin first-load becomes **5.10 MiB**. If the ground shader is left coupled to `gv-landcover.webp`, the smaller safe target is **5.38 MiB**.

Two qualifications matter:

- `test_public_build.py` will itself remain at approximately **6.66 MiB**, because it explicitly builds and asserts the no-key fallback ([test_public_build.py](/Users/user/Projects/3D%20Design/scripts/test_public_build.py:152)). A new keyed build/payload test is needed.
- Its byte counter is explicitly timing-dependent and described as a floor ([test_public_build.py](/Users/user/Projects/3D%20Design/scripts/test_public_build.py:100)). The **5.10 MiB** figure is the exact file-size delta applied to 6.66, not a promise that the race-prone counter will print precisely 5.10. Google/CDN library and streamed tile traffic are additional, camera-dependent network traffic.

### Looks removable, but is not

| Item | Why it stays |
|---|---|
| `gv-height-2000.bin.gz` — 2,077,247 B | The decoded 2,000×2,000 heightfield drives camera targets, tile melt height and focus marching, path draping, hotspot anchors, existing and future tree bases, and NCIC placement. [scene.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/scene.js:30) |
| `gv-meta.json` — 1,385 B | Supplies height-file encoding, dimensions, real-world origin and elevation range. The terrain and coordinate transform depend on it even when today is photographic. |
| The terrain mesh | It is both the drawable 2045 ground overlay and the surface receiving the future land-cover shader. Hiding or deleting it removes orchards, wetland, new roads and agrivoltaics. What can be optimized is its all-box per-frame submission, not its existence. |
| `gv-landclass.webp` — 103,218 B | Current code needs it to compare today with 2045 square metre by square metre. Removing it makes the “only changed 17.2%” mask impossible. A separately generated change mask could replace it, but that is a new asset pipeline, not a deletion. |
| The GCHQ footprint/roof | It is the only existing building geometry deliberately retained over tiles, to carry the 2045 meadow roof ([future.js](/Users/user/Projects/3D%20Design/experiments/002-living-map/golden-valley/future.js:510)). |
| `landcover.js` as a whole | Even after existing trees retire, `future.js` uses its class-texture loader, `KINDS`, and `unitTree()` to construct proposed trees. Split the today loaders; do not delete the module. |
| Paths and `gv-paths.json` | They are interface and traversal geometry, not an imitation of today: picking, walking, route labels and NCIC siting consume them. |
| `life.js` | It supplies animation to future materials as well as the existing model. The flock remains visible over tiles and is covered by the world-clock contract. |
| The tiles-off state | [test_tiles_frame.py](/Users/user/Projects/3D%20Design/scripts/test_tiles_frame.py:159) explicitly requires walks, arrivals and low hover to fall back to the measured model. Permanently excluding fallback assets from a keyed distribution contradicts that contract; initial-load savings require lazy loading unless the product decision changes. |
| `clean=1` behavior | `main.js` deliberately disables tiles for captures even when a key exists. A branch based only on “key exists” would strip the model and break `guard_plates.py` and every plate/capture tool. The branch must be based on the actual render mode: `!clean && key`. |

The largest test gap is a keyed integration test. All current strong visual tests either force or assume the measured path, while `test_tiles_frame.py` tests only the gate arithmetic. A bad keyed subtraction can therefore pass every existing suite while showing no meadow roof, no future ground, or an empty low-camera fallback.
