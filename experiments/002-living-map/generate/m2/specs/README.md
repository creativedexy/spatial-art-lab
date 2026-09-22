# M2 adventurous target synthesis

Approved by Dex on 22 September 2026. Boards set character; keyless plates remain geometry truth. Regenerated roads, ponds, woods and blocks drift most in `scheme-a` and `campus-b` and must not be copied.

## Shared palette

| Use | Lit sRGB | Shaded sRGB |
|---|---:|---:|
| Buff masonry | `#BE986C` | `#72563E` |
| Honey timber | `#C49A65` | `#6D5038` |
| Pale stone/concrete | `#C7B79A` | `#817562` |
| Reflective glazing | `#687A75` | `#263B3B` |
| Bronze trim/plinth | `#665747` | `#302C27` |
| PV glass | `#17242E`, glint `#91A4AB` | `#101820` |
| Meadow roof | `#8D9552` | `#4A542F` |
| Buff hard landscape | `#A69A83` | `#70695B` |
| Asphalt | `#60615C` | `#3E403C` |
| Open water | `#8CA5A9` | `#2E4B4F` |

## Roof programme

Area-weighted target: **PV 40%, meadow/green 29%, slate/tile 22%, walkable terrace 6%, other 3%**. Apply by typology: near-whole-roof PV on suitable home pitches; planted/PV strips and broad paths on campus; meadow on taller residential blocks; meadow on GCHQ with PV over its car parks; slate and tile on existing Cheltenham. At 340 to 450 m, flower species, furniture and detailed balustrades will not resolve. Use shader variation, broad paths, silhouettes and shadow. Omit board roof forms that escape the plate envelopes.

## Tree and ground palette

Five tree forms: veteran oak 17 to 23 m, mixed woodland 11 to 19 m, upright lime/hornbeam 9 to 15 m, orchard 4 to 7 m, and willow/alder 7 to 12 m. Hedges are 1.8 to 3 m. Canopy palette: lit `#70833E`, mid `#526B34`, shaded `#253D24`. Use clumped woods, avenues, orchard rows, isolated veterans and low wetland trees, never one evenly spaced silhouette.

Ground: meadow `#8FA064`, pasture `#7E925F`, wet meadow `#789067`, gardens `#667B45`, woodland floor `#465A39`, paths `#A69A83`, asphalt `#60615C`, water `#8CA5A9`/`#2E4B4F`. Prefer gardens, planted courts and rain gardens to generic lawn. Soften edges at metre scale with broad tonal variation.

## Top modelling actions by visible impact per effort

| Rank | Action | Main system | Effort | M5 status |
|---:|---|---|---:|---|
| 1 | Five crown families; clumps, avenues, orchards, veterans | `landcover.js`, `future.js`, tree data | 1.5 to 2 days | **In-flight M5** |
| 2 | Split and soften parcel ground; add broad tonal variation | generator, land cover, `future.js` | 1 to 1.5 days | **In-flight M5** |
| 3 | Reflective mapped channels and 2 to 3 ponded reaches; soft reeds | land cover, `future.js`, `life.js` | 1 day | **In-flight M5** |
| 4 | Instanced 2 m vertical agrivoltaics at about 11 m centres | generator, `futureGeometry` | 1 to 1.5 days | M6 |
| 5 | Match 40/29/22/6/3 roof mix; strengthen seams and masks | `facades.js`, `future.js`, data | 1 day | M4 follow-up |
| 6 | Deepen campus timber bays/reveals; split home/campus rules | `facades.js`, `futureGeometry` | 1 day | M4 follow-up |
| 7 | Lift GCHQ canopies with posts, light undersides and gaps | generator, `futureGeometry` | 0.5 to 1 day | M4 follow-up |
| 8 | Give GCHQ fine vertical bays over dark reflective glass | `models.js` or GCHQ material | 1 day | Separate |
| 9 | Make glasshouses read through fine frames and pane contrast | `futureGeometry`, `facades.js` | 0.5 day | M6 |
| 10 | Add sparse people, sheep and vehicles only if M7 needs scale | optional `life.js` | 0.5 day | Deferred |

M5 already covers the three highest-impact landscape gaps: tree variety and maturity, flat hard-edged ground, and water that reads as coloured terrain. Agrivoltaics, glasshouses, facades and roofs stay separate. Photographic leaves, tiny occupants and invented drainage cannot be reproduced honestly within the WebGL budget at this range. Target the same first-glance hierarchy, and keep geometry with the plates.
