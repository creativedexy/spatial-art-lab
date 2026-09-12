# Campus NCIC photographic conversion

Generated with the built-in image_gen tool. Two passes: initial generation and one requested correction. Final saved at 1280×720 (native generation 1672×941, resized using sips).

## Final status
Visual treatment achieved, but **geometry QA fails**. This is not a geometry-approved frame. No further generation was performed after the single requested correction.

## Measurements
Manual visual bounding-box estimates on the final 1280×720 image; approximately ±4 px, with some tree occlusion. Boxes include architectural roof/frame, excluding shadows, people and isolated planting. Order: left, top, right, bottom. Residual = output minus requested edge.

| Building | Requested box | Final measured box | Edge residuals px | Maximum absolute residual |
|---|---|---|---|---|
| NCIC | 722,268,905,342 | 718,224,956,320 | -4,-44,+51,-22 | 51 px |
| Nearest left campus block | 0,368,285,500 | 0,334,286,488 | 0,-34,+1,-12 | 34 px |
| Second campus block | 332,322,530,410 | 319,286,535,386 | -13,-36,+5,-24 | 36 px |

First-pass approximate boxes were NCIC [722,238,980,342], nearest [0,346,294,493], second [337,302,537,391]. Correction requested restoration of original bounds and floor count. It reduced NCIC rightward extension but moved roof/building tops farther upward; it did not resolve overall composition drift.

## Rule checks
- No towers: PASS. Blocks remain broad horizontal bars; second foreground block reads as four storeys. Nearest block still appears simplified in floor count versus the plate.
- NCIC as architectural focal point: PASS visually. Buff frame, horizontal glazing, glazed high end and continuous sloping flowering meadow roof with a walking path remain legible.
- NCIC roof not lawn/green wall/separate hill: PASS.
- NCIC location/size: FAIL against supplied box, as above.
- No buildings added in open orchard/field areas: no obvious intrusion into left open fields observed. Exact development geometry preservation FAILS: several building silhouettes and positions differ from plate; background and foreground homes are not an exact survey match.
- Visible life: PASS. Walkers, cyclists, people on roof path and seated/standing groups outside glazing are visible.
- Courtyards: PASS. Buff paths/plazas, seating, planted meadow areas and mature trees.
- Empty area <=50%: PASS by visual estimate, not segmentation. Sky about 15%; empty open ground modest, combined comfortably below half.
- Light/season/palette: warm upper-left sun, long shadows, blue sky/small cumulus and late-summer planting. Distant countryside fills former map-data band.
- No visible text, logos or watermark: PASS.
- Photo treatment: detailed natural materials and vegetation, though some polished architectural-visualisation character remains.

## Final prompt
The complete correction prompt submitted to the built-in tool follows. Inputs: original campus plate (geometry master), approved panels/glasshouses photo (lighting only), first generated result (materials/activity only).

Use case: sketch-to-render. Edit image 1 into a real aerial photograph of the proposed 2045 Golden Valley innovation campus, west Cheltenham, weekday late-summer afternoon. Image 1 is the GEOMETRY AND COMPOSITION MASTER: keep camera, framing, silhouettes, footprints, perspective and every building in exactly the same pixel locations. Image 2 is ONLY light/sky/season/palette reference. NEVER borrow its composition or buildings. Output 1280x720 landscape.
Keep NCIC focal building at x722–905 y268–342 (1280x720 coordinates): single architectural wedge with ONE continuous dense flowering wildflower meadow roof sloping from ground at RIGHT end to 16m at LEFT end, pale stone perimeter frame, buff stone flanks with long horizontal glazing bands, fully glazed high end. Roof must visibly contain varied tall late summer meadow flowers, seedheads and grasses, and a narrow path with a few visible walking people. Not lawn, not green wall, not separate hill.
Keep nearest campus block x0–285 y368–500, second block x332–530 y322–410, and all blocks behind precisely aligned with original silhouettes. 38x17m bars, 4–5 storeys, wide horizontal proportions. Deep buff stone spandrel band above each storey, ribbon windows wider than tall, timber fins at bay edges, continuous dark reflective glazed ground floor with solid head and cill, sedum roofs. Never stretch into towers. Keep foreground right homes exactly in place, red brick/timber walls, grey slate and red clay tile roofs.
Ground BETWEEN CAMPUS BLOCKS must be occupied landscaped courtyards: angular buff sett plazas cutting through wildflower and long grass, few retained mature oaks, benches, bicycle racks, outdoor seating at glazed ground floors. Many small but clearly recognizable realistically scaled people crossing plazas, sitting outside glazing, cyclists and walkers on existing streets/paths, and people walking up meadow roof. Real afternoon campus activity is compulsory.
Keep orchards, hedgerows and open fields in their original areas at left and distance, no added buildings in fields, no development brought forward. Land edge around y200 retained. Replace flat grey map-data band just above furthest land with distant Severn Vale countryside extending to natural distant horizon, NOT more sky. Blue sky small scattered cumulus. Match image2 warm low upper-left afternoon sunlight and late-summer palette, maintain original shadow direction, clear air. Rich natural photographic materials, real trees, convincing architecture, no CGI appearance. NCIC remains focal through architecture/detail, not moving or enlarging it. No more than half frame empty ground plus empty sky: activate existing courtyard surfaces with paving, planting and people without altering framing. No text, logos, watermarks. Exact geometry preservation is critical; all three specified boxes within 15px of original.
CORRECTION PASS: Image 3 is first photographic attempt, for retaining its photographic materials and activity ONLY. It has geometry errors. Restore geometry from IMAGE 1 rigorously. At 1280x720 first attempt measured NCIC approximately [722,238,980,342], target [722,268,905,342]: shrink NCIC right edge 75px LEFT and lower top edge 30px, base fixed. Its roof must be shallower like master. Nearest left block first attempt [0,346,294,493], target [0,368,285,500]: top down22px, right left9px, base down7px. Second block first attempt [337,302,537,391], target [332,322,530,410]: translate left5px down20px, right edge to530. Preserve original four-to-five storey band count within these silhouettes, not three-storey simplified buildings. All other building positions, homes, roads, and undeveloped fields must follow image1 precisely, not the drifted third image. Keep flowering roof with visible walkers, horizontal stone/glazing bands, full-height high-end glass, lively plazas, cyclists, natural mature trees, distant countryside and lighting. Do not add any new buildings. Exact silhouettes matter more than visual enlargement of focal point.

