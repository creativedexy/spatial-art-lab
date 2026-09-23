# Round 3: key frames for a 15-second sequence (plates + HUD targets)

**For:** Codex, free subscription, built-in image_gen. £0. No reference images except the plates you make in this run.

Dex picked round 1 frames 02 and 05, round 2 moved nature first, and the HUD language now follows Jayse Hansen's film work (lock-on brackets that tighten, elbowed callouts with values, a telemetry sidebar on one edge, a scan sweep, two type sizes, one alarm colour, dense edges and an empty centre).

The pipeline: each **plate** becomes the first frame of a 5-second video clip (a video model animates it), then TouchDesigner tracks the motion and draws the HUD. So the plates must contain **no HUD, no text, no lines**: just the animal and the habitat. The **HUD targets** show what the finished frame should look like.

Make six PNGs at 1600 × 900 in `experiments/003-spider-probe/alignment/out3/`:
- `k1-plate.png` then `k1-hud.png`: establishing. Forest floor at night under a single low torch: wet moss, fallen oak leaves, a rotten log. A wolf spider has just stepped into the light, left third of frame. Deep black beyond the torchlight.
- `k2-plate.png` then `k2-hud.png`: macro, low and close. The same wolf spider mid-stride over moss, legs sharp, dew on the moss. Room on the right for a sidebar.
- `k3-plate.png` then `k3-hud.png`: the spider crossing the mossy log from left to right, side-on, room behind it for a time trail.

Rules:
- Plates: photographic macro realism, but the spider and moss carry a subtle point-cloud quality (fine glowing specks on edges) so the finished piece reads "seen by a machine" before any HUD. Gold and white highlights, deep black. Anatomy right: eight legs, two body parts.
- HUD targets: make each by editing its plate (keep the plate identical underneath). Add, in thin white hairlines and tiny monospace type: k1 a scan sweep line and "SURFACE RESPONSE | MOSS"; k2 lock-on brackets on the leg tips, a hairline pose skeleton, two elbowed callouts with short values (e.g. "L2 FEMUR 4.1 mm"), a telemetry sidebar on the right edge with a small trace graph; k3 five fading copies of the spider behind it along the log, a thin frame round the present one and a timecode. One accent colour only (a small warm red) for a single alert element.
- Text must be short, real and legible; no gibberish.

Write `out3/notes.md` (what came out, rule misses) and `out3/prompts.json`.
