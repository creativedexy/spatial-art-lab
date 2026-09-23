# TouchDesigner HUD for the spider (v003)

The HUD is built by a script, not by hand, so it can be rebuilt and changed from here.

1. **Plate:** Blender renders the spider with no overlays: `Blender -b -P probe_a_spider.py -- --clean`, then encode `render/scratch/trail-clean-*.png` to `render/probe-a-v002-clean.mp4`. The bright dots on the leg tips are what TouchDesigner tracks.
2. **Project:** `python3 td/mktoe.py td/spider_hud.toe td/build_hud.py` writes a .toe whose Execute DAT (`boot`) runs `build_hud.py` on start. It uses `toeexpand`/`toecollapse` from the TouchDesigner app. Errors go to `td/build_hud.py.log`.
3. **Render:** `open -n -a TouchDesigner --args "$PWD/td/spider_hud.toe"`. It builds the network, records 240 frames to `render/probe-a-v003-td.mov` and quits.
4. **Study it:** open the .toe, turn off `boot`'s Start toggle and delete `recorder`, then read the network left to right: plate, level, thresh (the machine's eye), hud (Script TOP: tracking and line work), labels (Text TOP driven by `label_spec`), over, glow, out.

Needs a TouchDesigner licence key (the free Non-Commercial key caps output at 1280 × 1280, so 1280 × 720 fits).

HUD moves from Jayse Hansen's work (see `inspiration/jayse-hud-notes.md`): lock-on brackets that tighten as a track ages, elbowed callouts with live values, a telemetry sidebar with a cadence trace, and a scan sweep.
