# Specimen Studio

Our own version of geometric-art.com/pro (by Shinichi, @shinichi_sisberry), tuned for the spider piece: geometry plus a HUD layer in Jayse Hansen's grammar, over any image or video. One self-contained file, `studio.html`. It runs on this machine, uploads nothing, and opens on the round-3 K2 plate.

## What geometric-art does (from its PRO manual, read 23 Sep 2026)
Edges and contours are pulled from the image's brightness, then points are sampled along them. The points are linked (proximity, Delaunay, edge chain, radial, orthogonal or hybrid) and dressed with shapes. On top go optional layers: a grid system, a circle chain, a spectral curtain, a portrait window, dither print and pixel memory. Colour and blend modes, audio-reactive sync, a motion program and presets follow. Export is PNG, MP4 at 30 fps, or WebM, in 4:5, 9:16, 1:1 or 16:9 at 3 to 12 seconds.

## What Specimen Studio has
| Panel | Ours | Notes |
|---|---|---|
| Field | Sobel edges at quarter resolution, points sampled by edge strength (count, threshold, bias, radius); re-extracts every N frames on video | The flicker from re-extracting on video is the "tracking glitch" look |
| Shapes | circle, square, cross, bracket, mixed; size from edge strength | |
| Links | proximity, Delaunay (Bowyer-Watson), orthogonal, radial, hybrid | Orthogonal plus Editorial grid is the look in Dex's screenshot |
| Grid and layers | measure, editorial and fragment panels with M/S labels; circle chain; node labels; scanlines; grain | |
| HUD (ours, not theirs) | lock-on brackets that tighten, elbowed callouts, telemetry sidebar, artwork frame with title, size and timecode | Jayse moves |
| Colour | line and accent colour, blend modes, source and overlay opacity | |
| Motion | assemble plus sweep, scan sweep, signal pulse, orbit, glitch slice | |
| Output | PNG; WebM recorded live at 30 fps, 5 to 12 s; four formats; presets in the browser plus copy as JSON | |

## v2: what we took from Ladybug (app.theladybug.app, studied 23 Sep 2026)
Ladybug's structure is source, then effect layer, then finish stack, with any control bindable to sound. Its library holds about 60 effects in categories: type and code, halftone and dither, edges, analog and glitch, textile, pixel and 3D. It also has canvases (terminal, riso, newsprint) and a capture panel (people, face, hand and depth tracking). It has no API or CLI, so we learn from it rather than connect to it. Added:
- **Effect layer:** number field, ASCII, dither (Bayer), contour, pixel sort. One sample per cell with brightness gain, so dark plates still fill.
- **TWIN layout:** the real subject on the left, its machine twin on the right, dashed links from the tracked points (Azat's data-twin structure). Preset: *Data twin (Azat)*.
- **Finish stack:** bloom, streaks, trails, grade (contrast, saturation), paper.
- **Sound and bindings:** + Audio (or drop a track); any bindable slider has a signal menu (bass, mid, high, LFO) with a global depth. The audio goes into the WebM recording.

## Not yet (theirs, worth adding if Dex wants them)
Contour studio (topographic lines), dither print, pixel memory (a binary glyph field, which suits the ASCII direction), audio-reactive sync, subject masking (protect the spider, geometry on the moss only), MP4 export.

## Where it sits
Studio = fast look development on stills and generated clips. TouchDesigner (`../003-spider-probe/td`) = the real-time build, whose tracking follows actual motion. Settings copied as JSON from the studio can be ported to the TouchDesigner network.

## Headless: one shot file, one command
```
python3 experiments/004-specimen-studio/make.py experiments/004-specimen-studio/shots/k2-twin.json
```
- **Shot file** (`shots/*.json`): `plate` (image or video), optional `td_hud: true` (first runs the plate through TouchDesigner's HUD network in `../003-spider-probe/td`, headless), `preset` plus `params` overrides, `format`, `fps`, `seconds`, optional `audio`.
- **How it runs:** a local HTTP server (same origin, so the canvas can be read), the gstack headless browser, and `window.studio.load(shot)` then `studio.frame(i)` for every frame, each written straight to PNG. ffmpeg then encodes with the audio. Outputs are `render/<name>.mp4` and `render/<name>-sheet.jpg`.
- **Deterministic:** time comes from the frame index, not the clock. Video plates are unpacked to numbered frames, because Python's http.server cannot serve byte ranges, so seeking fails. Audio is analysed offline into per-frame bass, mid and high, so bindings land on the exact frame.
- **Adjust by hand:** open `studio.html`, tune, then **Save shot**. Set the `plate` path in the saved JSON and it runs here unchanged.
- **Tested 23 Sep 2026:** `k2-twin.json` (image, audio-bound bloom tracks a 120 BPM pulse frame for frame: 96 frames in 6 s) and `chain-test.json` (Blender plate, TouchDesigner HUD, studio geometry: 72 frames, 18 s end to end).
