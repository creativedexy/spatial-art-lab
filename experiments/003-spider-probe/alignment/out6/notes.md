# Round 6 notes

All six plates were generated with the built-in `image_gen` tool at 1024 × 1536, scaled to 1920 px tall with `sips`, and centre-cropped to 1080 × 1920. Final PNGs are opaque RGB. Coordinates below refer to the final 1080 × 1920 crops and are rough percentages for tracker seeding.

## Plates

- `p1-peacock-face.png` — Head-on peacock spider with raised blue/red iridescent fan, eyes and pedipalps level, and one moss tip at the bottom. Tracker anchor: **x 50%, y 48%**. Animal bounds: roughly **x 5–95%, y 15–80%**.
- `p2-peacock-profile.png` — Side-profile peacock spider climbing a single dark stem; blue/red scales catch a restrained rim light. Tracker anchor: **x 48%, y 49%**. Spider bounds: roughly **x 20–82%, y 20–78%**.
- `p3-moonlight-wolf.png` — Wolf spider from slightly above, spread legs under cold silver-blue rim light, with one wet leaf corner. Tracker anchor: **x 50%, y 51%**. Animal bounds: roughly **x 1–97%, y 18–84%**.
- `p4-moon-bell.png` — Moon jelly from below, complete bell and four gonad rings, with fine tentacles continuing out of frame. Bell tracker anchor: **x 50%, y 29%**. Full animal bounds: roughly **x 7–93%, y 5–100%**.
- `p5-compass-column.png` — Compass jelly as a narrow central column with a patterned amber bell, fine tentacles, and a few isolated plankton sparks. Tracker anchor: **x 50%, y 48%**. Animal bounds: roughly **x 27–73%, y 12–91%**.
- `p6-comb-pair.png` — One large near comb jelly and one small far comb jelly, with iridescent comb rows and one seaweed strand at the left edge. Tracker anchors: **near x 43%, y 53%; far x 84%, y 23%**. Combined animal bounds: roughly **x 3–96%, y 15–81%**.

## Rule misses / compromises

- P1 and P3 use nearly all of the crop width. No animal pixels are cut, but their outer hairs sit outside a strict central-80%-of-final-frame guide.
- P2's stem crosses the top and bottom quiet zones. The spider itself leaves those zones usable.
- P3's wet leaf enters the top-left quiet zone, as requested by the habitat trace.
- P4 follows the shot-specific requirement that tentacles fall out of the bottom. Consequently, its full visible extent exceeds the general 55–75% height rule and the bottom 18% contains fine tentacles. The bell also begins within the top 12%.
- P5's complete fine-tentacle extent is about 79% of frame height, slightly above the 75% general maximum; this preserves the requested full-height column feeling. A few tentacles enter the bottom quiet zone.
- P6's seaweed strand crosses the top-left quiet zone. The two-animal exception is intentional.
- Generated macro anatomy is visually plausible but should not be treated as taxonomic reference photography.
