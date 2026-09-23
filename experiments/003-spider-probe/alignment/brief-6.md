# Round 6: portrait, minimal, the animal large in frame

**For:** Codex, free subscription, built-in image_gen. £0. No reference images.

Dex is making Instagram Reels (9:16). He wants this round **minimal** with the **animal large in frame**. Everything learned so far still holds: true black, one light, the colour comes from the animal (the jellyfish and the iridescent peacock spider won), nature present but only as a trace. These are clean plates: no HUD, no text, no lines, no frames; a video model animates them and the HUD is drawn afterwards.

Generate each in portrait (1024 × 1536 is fine), then make a 1080 × 1920 version with `sips` by scaling to 1920 tall and centre-cropping the width; keep the animal inside the central 80% of the width so the crop never cuts it. Save as PNG in `experiments/003-spider-probe/alignment/out6/`.

**Composition rules (all six):** the animal fills 55 to 75% of the frame height; one subject only (P6 excepted); the background is true black with at most one habitat element entering from an edge; one light source; the top 12% and bottom 18% are quiet enough for small type to sit over later; the animal is sharp end to end.

- `p1-peacock-face.png`: a peacock spider head-on, very close, the iridescent fan raised; its big front eyes and pedipalps at eye level; one cool soft light from above. A single moss tip at the bottom edge.
- `p2-peacock-profile.png`: the same peacock spider in side profile, walking upwards along a thin dark stem that enters from the bottom; its blue and red scales catch a rim light.
- `p3-moonlight-wolf.png`: a wolf spider seen from slightly above, legs spread, filling the frame, silver rim light from the moonlight palette (cold blue-white), one wet leaf edge in a corner.
- `p4-moon-bell.png`: a moon jellyfish from below, its bell filling the upper two thirds, four gonad rings glowing, tentacles falling out of the bottom of the frame.
- `p5-compass-column.png`: a compass jellyfish as a vertical column: bell at the top, long fine tentacles running the full height; a few plankton sparks only.
- `p6-comb-pair.png`: two comb jellies, one large and near, one small and far, their iridescent comb rows lit; one strand of seaweed at an edge.

Write `out6/notes.md` (what came out, rule misses, where the animal sits in the frame as a rough x/y % for the tracker) and `out6/prompts.json`.
