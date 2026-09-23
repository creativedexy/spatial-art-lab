# Round 7: the chosen direction, in portrait

**For:** Codex, free subscription, built-in image_gen. £0. References attached: our own plates k1, k2, k3 (`out3/`) and j1, j2, j3 (`out4/`), in that order.

Dex rejected round 6 (minimal, animal filling a black frame) as the wrong direction. Go back to the look of the attached plates, which is the direction he chose: a real animal in a real, rich habitat (wet moss, oak leaves, a mossy log, dew; a rock pool with kelp and barnacles, seagrass, plankton sparks), one low light, deep black beyond the light, photographic macro realism. The only change is the frame: **portrait 9:16 for Instagram Reels**.

For each reference, make a portrait version that keeps the same animal, the same light direction and colour, the same habitat and the same mood. Recompose for vertical rather than cropping: the habitat extends downward (more moss, leaves, rock and kelp in the lower third), the darkness extends upward, and the animal sits between one third and one half down the frame at a similar size relative to the habitat as in the reference (not larger). Clean plates: no HUD, no text, no lines.

Generate each at 1024 × 1536, then make 1080 × 1920 with `sips` (scale to 1920 tall, centre-crop the width; keep the animal inside the central 80%). Save as PNG in `experiments/003-spider-probe/alignment/out7/`:
- `v1-forest-floor.png` from k1 (wolf spider stepping into torchlight, forest floor)
- `v2-moss-stride.png` from k2 (wolf spider mid-stride over dewy moss)
- `v3-log-crossing.png` from k3 (wolf spider crossing the mossy log; in portrait, the log runs diagonally upward)
- `v4-rock-pool.png` from j1 (moon jellyfish above the rock pool, kelp and barnacled rock below)
- `v5-open-water.png` from j2 (compass jellyfish, long tentacles falling down the frame, seagrass rising from the bottom)
- `v6-comb-jellies.png` from j3 (three comb jellies beside the seaweed frond, stacked vertically)

Write `out7/notes.md` (what came out, anything that drifted from its reference, rough x/y % of the animal for the tracker) and `out7/prompts.json`.
