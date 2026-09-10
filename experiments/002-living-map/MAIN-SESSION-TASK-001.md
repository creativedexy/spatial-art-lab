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
