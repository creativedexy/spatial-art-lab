# 000 — Sprint 0: environment and first result from each tool

Date: 8 September 2026
Intent in one sentence: prove both tools run, record what this machine actually does, and get one saved result out of each.
Reference IDs: none (setup sprint).

## Environment (recorded, step 1 of Sprint 0)

| Item | Value |
|---|---|
| Machine | Mac17,8 — Apple M5 Pro, 20-core GPU, 48 GB unified memory |
| OS | macOS 26.5.1 (25F80) |
| Display | Built-in Liquid Retina XDR, 3456 x 2234 |
| Blender | 5.2.1 LTS (build 2026-08-25), Cycles + Metal |
| TouchDesigner | 2025.33230 — **license tier not yet confirmed** |
| Meshy | MCP connector present; credit balance not yet checked |
| World Labs / Marble | access not yet checked |

## Benchmark (before promising frame rates)

Cycles, Metal GPU, 1280x800, 128 samples + denoise, three-object scene:
**~96 s for the first frame** (includes startup and Metal kernel compile), then **~4 s per subsequent frame**.
So iterate in one session rather than one render per launch. 1280x800 is a comfortable
working preview here; a final still can go far higher without drama.

## Blender: one variable explored — key light position

One area light (2.4 m, 900 W), moved to three positions. Nothing else changed.

- **a-rim-back** — light high and behind. Almost the whole object falls away into black; only the top plane and one edge survive. The most atmospheric and the closest to the graphite/bone territory, but the form is barely legible.
- **b-side-low** — light low and to camera right. Strong front/side split, bright face against a black flank. The most graphic and the most confident silhouette.
- **c-top-front** — light high and front. Everything is described, nothing is hidden. Technically correct and the least interesting; this is the default look worth avoiding.

## What I predicted vs what happened

Predicted the back rim would be the strongest. It is the most atmospheric but it loses the
object; **b-side-low** is the better base because it keeps both mystery and readable form.
The lesson is that darkness is only useful when something is still legible inside it.

## Saved outputs

Source file: `experiments/000-sprint-zero/blender/sprint0-lightstudy-v001.blend`
Script: `experiments/000-sprint-zero/blender/sprint0_scene.py` (rerunnable; edit `POSITIONS` and rerun)
Stills: `exports/000-sprint0-light-{a-rim-back,b-side-low,c-top-front}-v001.png`
Selected variant: **b-side-low**

## Review

**What works:** dark world at 0.008 plus AgX Medium High Contrast gives deep blacks that
do not go muddy. The bevel (0.12 m, 6 segments, harden normals) is doing most of the work —
it is the bevel highlight that reads as metal, not the material.

**What I can now change without AI:** light position, size and energy; bevel width and
segments; roughness and metallic; camera lens and height; world brightness.

**One failure worth keeping:** `use_auto_smooth` was removed after Blender 4.1 and the first
run died on it. Version-specific API guesses fail loudly — check against the installed build.
Second failure, milder: the camera is framed too tight, the block nearly touches the top edge.
Fine for a light study, wrong for a final still.

**Next 20-minute experiment:** keep b-side-low, pull the camera back and drop the lens to 50 mm,
then add a second much dimmer fill from the opposite side and find the point where the dark
flank stops being pure black. That is the whole grammar of the Impossible artefact sprint.

## Not done in this session

TouchDesigner is GUI-driven and was not run here — see `touchdesigner-build-sheet.md`
for the exact network to build, which completes Sprint 0.
