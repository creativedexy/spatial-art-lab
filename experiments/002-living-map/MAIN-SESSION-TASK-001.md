# Main session, task 001: the approved photos become places in the map

**From:** Dex, via the local session, 10 Sep 2026.
**Owner:** the main (cloud) session. It owns the map code; the local session
supplies photos, loops and GLBs and stays out of `golden-valley/*.js`.

## Why now

Dex approved the 2045 look after brief 003 and asked for the interactive web
work to start. The photos exist; the map exists. Nothing yet joins them.

## Part 1: places of interest you can click (do this first)

Each approved photo was generated from a camera in the map, so each one is
already a place in it. Make them clickable destinations:

| place | photo | camera sidecar | 2045 |
|---|---|---|---|
| GCHQ | `generate/gchq/out/gchq-photo.png` | `generate/gchq/plate.json` | off |
| the campus, GCHQ beyond | `generate/golden-valley-2045/out/a-cyber-central-photo.png` | `generate/golden-valley-2045/a-cyber-central.json` | on |
| the campus from above | `.../out/b-the-campus-photo.png` | `.../b-the-campus.json` | on |
| panels and glasshouses | `.../out/c-panels-and-glasshouses-photo.png` | `.../c-panels-and-glasshouses.json` | on |
| GCHQ with its meadow roof | `generate/close-2045/out/gchq-meadow-photo.png` (landing today) | `generate/close-2045/gchq-meadow.json` | on |

- A marker at each place in the live map. Clicking it flies the map camera to
  that sidecar's `pos` and `look` (fov 48), with the 2045 wave set as the table
  says, then shows the photo over the map at that viewpoint.
- **Plain crossfade in and out. No transition effects.** Dex ruled blur zooms
  out on 10 Sep ("No way"), so do not build transition tooling.
- Back out returns to the live map where the viewer was.
- Mobile first: markers big enough to hit at 390 px wide, and the photo fills
  the viewport.

**Done when:** from the live map you can reach every row above and back again
on a phone, and each photo lands on the viewpoint it was generated from.

## Part 2: real buildings on the 2045 footprints (set it up now, fill it later)

The close-up plates failed the no-empty-frames rule because at 100 m the
campus is blank 38 × 17 m slabs on grass. Meshy models are being made locally
(approved, 70 credits) and will land in `experiments/002-living-map/meshy/`
as GLBs:

- `campus-block.glb`: one bar building, modelled at 38 : 17 : 14.
- `ncic.glb`: the National Cyber Innovation Centre, the sloping meadow-roof
  building from HBD's aerial, roughly 60 × 35 m.

Build the placement now, with a placeholder box, so dropping a GLB in is a
one-file change:

- every `campus` footprint in `gv-2045-buildings.json` gets one instance of the
  campus model, scaled to its footprint (all 20 are 38 × 17 m) and to its own
  height (11.9–17 m), turned to the footprint's long axis, sat on its `base`.
  Glasshouses the same way when a `glasshouse.glb` follows.
- **The NCIC has no footprint in the scheme.** Choose its cell by a written
  rule, as the rest of the scheme is (for example: the campus cell nearest
  GCHQ with a named route frontage), not by hand, and say which rule.
- Keep the untextured extrusions as the fallback when a GLB is missing, so
  nothing renders empty.

**Done when:** the campus plate re-rendered from `generate/close-2045/campus-cluster.json`
shows models rather than slabs. That plate then gets re-briefed through the
`generate/` queue as close-up 004.

## Not in scope

No transitions, no far-field terrain, no "before" frames, no video. Car-park
ranks (the 002 finding) stay on the list for later.

---

## Result — main session, 10 Sep 2026

**Both parts done, 16/16 checks in `scripts/test_places.py`.**

### Part 1

`golden-valley/places.json` + `places.js`. Five markers; clicking one flies the
live camera to that plate's own `pos` and `look` at fov 48, ramps the wave to
the year the plate was rendered in, and crossfades the photograph over it.
Back out restores the camera, the wave and the orbit limits exactly.

**Plain opacity, in and out.** No blur, no scale, no filter, and no transition
tooling for one to creep back into later.

Mobile first: every marker is 68 px tall at 390 px wide, and the photograph
fills the viewport under `cover` with the live camera narrowed to match — so
the crossfade is the same framing rather than a zoom.

One real bug the test caught before anyone saw it: **`places.json` was typed
from the camera each plate was *asked* for, not the one it was *rendered*
from.** Two places were 36 m and 9 m out, which is exactly the drift that makes
the whole idea quietly worthless — the photograph and the map would be two
pictures of roughly the same place instead of one view of the same ground. The
file is now generated from the sidecars and a check fails if they ever part.

### Part 2

`golden-valley/models.js`, with `GLTFLoader` vendored beside the other three
libraries. Both GLBs had already landed, so this is placed rather than
scaffolded: **20 campus blocks and the NCIC**, one InstancedMesh per type, each
instance scaled to its footprint and its own measured height (11.9–17 m) and
turned to the footprint's long axis.

The models rise with the wave like everything else 2045 adds, shadow pass
included. The extrusions are now built one mesh per family so the campus can
stand down on its own — a family whose GLB is missing keeps its boxes, because
an empty field is a worse failure than an untextured one.

**The NCIC rule**, evaluated in code rather than typed in as coordinates:

> the campus field with frontage on a named route — the Cheltenham Circular
> Footpath or the Gloucestershire Cycle Spine within 150 m of the field
> centre — and, of those, the one nearest GCHQ. It stands in that field's
> courtyard, on the axis of the blocks around it, with the low end of its
> meadow roof turned towards GCHQ.

That picks the field at **(−138, −190)**: 364 m from the ring, 120 m off the
Circular, nearest block 57 m from the courtyard centre so a 60 × 27 m building
clears it comfortably. Which end of the roof is the low one is read off the
model's own geometry rather than assumed. Height scaled to 16 m as
`meshy/README.md` asks — the one deliberate distortion, and it is the right
one: the silhouette that matters is the meadow reaching the ground.

`generate/close-2045/campus-cluster.png` is re-rendered and now shows four
banded storeys with sedum roofs and PV rather than slabs. It is briefed as
**004** in the queue.

### One thing for the local session

The generator now writes a `cell` on every 2045 building — the field it was
placed in. The first version of the NCIC rule recovered fields by clustering
the blocks and found five where there are four, because two blocks either side
of a street are nearer each other than either is to its own courtyard. The
geometry is byte-identical; only the new key was added.

The GLBs are 5.8 and 6.1 MB and both are loaded by the map page. The
compression `meshy/README.md` asks for is not done and should happen before
this goes anywhere near a phone on mobile data.
