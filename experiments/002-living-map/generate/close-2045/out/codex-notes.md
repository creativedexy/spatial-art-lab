# GCHQ meadow photograph — inspection notes

## Deliverable
- Final: `gchq-meadow-photo.png`, 1280 × 720.
- Built-in image_gen, sketch-to-render edit using the surveyed plate as geometry target and approved frame as palette/light reference only.
- One generation pass; no corrective generation required.
- Native generation: 1672 × 941. Resampled to the requested 1280 × 720 with sips; no cropping or geometry warping.
- Original generated file: `/Users/user/.codex/generated_images/01a08bbf-38de-7981-bff4-e99b43c946d1/exec-6e9e873a-1e49-402b-84d2-bcf52a7d241f.png`.

## Measured residuals
Manual visual edge readings from the final 1280 × 720 image, approximately ±3 px (vegetation boundaries ±5 px). These are estimates, not automated segmentation. Residual = generated minus requested coordinate; positive x is right, positive y is down.

| Feature | Requested | Final measured estimate | Residual |
|---|---|---|---|
| Ring outer left/right | x 183 / 1210 | x 185 / 1208 | +2 / −2 px |
| Ring roof top | y 212 | y 211 | −1 px |
| Ring front base, excluding entrance projection | y ~712 | y ~708 | −4 px |
| Courtyard left/right | x 485 / 882 | x 484 / 883 | −1 / +1 px |
| Courtyard top/bottom | y 258 / 392 | y 255 / 395 | −3 / +3 px |
| Pale annex left/right | x 955 / 1113 | x 958 / 1117 | +3 / +4 px |
| Pale annex top/bottom | y 192 / 262 | y 189 / 263 | −3 / +1 px |
| Background settlement roofline/base landmarks | y ~68 / ~98 | y ~68 / ~98 | approximately 0 / 0 px |
| Woodland belt | x 505..960, y 90..210 | x ~506..960, y ~94..213 | +1 / 0 / +4 / +3 px |

Ring comparison box: approximately (185,211)–(1208,708), versus (183,212)–(1210,712): width −4 px; height −3 px.
Courtyard comparison box: approximately (484,255)–(883,395), versus (485,258)–(882,392): width +2 px; height +6 px. Minor edge drift, no material enlargement.
Maximum estimated ring boundary residual 4 px; courtyard boundary residual 3 px. Both within the ~15 px correction threshold. Entrance projects to the lower frame edge as in the plate; do not substitute its clipped base for the main ring front base.

## Rule checks and corrections
- PASS: annular roof visibly covered in grasses and white/yellow/purple wildflowers; no metal roof or solar panels.
- PASS: courtyard is dry planting, lawn, paths and a few trees; continuous glazed inner elevation; no water.
- PASS: glazed exterior bands over brick base; right notch retains a glazed entrance block.
- PASS: occupied car parks with individual parked vehicles on both sides and behind ring; traffic on perimeter roads.
- PASS: visible walkers at right entrance, ground paths, and multiple people on roof maintenance paths.
- PASS: GCHQ dominates the photograph and reads as architecture.
- PASS: empty sky/ground clearly below half of frame (sky approximately top tenth; most remainder building, settlement, woodland and occupied circulation).
- PASS: clear summer light and warm green/gold palette consistent with reference; no obvious text, logos or watermark.
- No corrective pass triggered. Photographic material detail changes local edge texture; surveyed pixel agreement remains approximate.

## Final prompt
Use case: sketch-to-render. Edit IMAGE 1 into a convincing detailed aerial photograph of GCHQ Cheltenham in proposed 2045. IMAGE 1 is the absolute surveyed geometry and composition target. IMAGE 2 is ONLY light, sky, season, colour and material reference; NEVER its composition or buildings. Output 1280x720 landscape, same camera and silhouette as IMAGE 1, light aircraft about 150m out.
Preserve exact pixel geometry in 1280x720 coordinates: ring outer edge x183..1210, roof top y212, front base about y712. Do not raise, shrink, move or reframe the ring. Courtyard opening exactly x485..882 y258..392. Pale right annex exactly x955..1113 y192..262. Background Cheltenham rooflines top about y68 and bases about y98; woodland belt x505..960 y90..210. Trace original edges, replace placeholder materials only and add realistic fine detail. Preserve right entrance notch and glazed entrance block.
Annular roof is a lush WILDFLOWER MEADOW: grasses, little white yellow and purple flowers, natural uneven botanical texture, a few narrow maintenance paths with several clearly visible small people. Never a metal roof, never panels. Keep meadow entirely within the original annular roof silhouette. Inner face continuous architectural glazing with fine mullions around the unchanged small DRY planted courtyard with a few trees, grass and dry paths. Never water, never enlarged courtyard. Outer face horizontal glazed bands above a brick base, detailed legible architecture, physically credible reflections.
Match IMAGE 2 warm clear sunlight, blue sky with modest small clouds, summer greens and golden meadow tones, red brick, slate and clay tile, mature foliage, crisp clear air no haze. Existing houses and woodland stay in original positions; no new buildings.
Compulsory life: fill existing car park surfaces around ring with many individually parked cars in orderly marked parking bays, especially behind and on both sides. Perimeter roads have moving traffic. Visible people walking to the right entrance and on ground paths, and a few people on roof maintenance paths. GCHQ remains dominant focal point. Less than half image empty sky/ground. No text logos watermarks. Photographic fine detail, not polygonal or illustrative. Geometry preservation is paramount.

