# GCHQ meadow roof (2045) — generation notes

## Output

- Final image: `gchq-meadow-photo.png`
- Final dimensions: 1280 × 720 px, sRGB
- Method: built-in image generation, `sketch-to-render`
- Passes used: 2 (one initial generation and one correction pass)
- Final selection: pass 2
- Final sizing: the complete generated frame (1672 × 941) was resized directly to 1280 × 720. No crop, extension, or content-aware warp was used. The source and target aspect ratios differ by less than 0.06% because of integer pixel dimensions.

## Input roles

1. `../plates/gchq-meadow-2045.png` — absolute geometry and camera master.
2. `../../close-2045/out/gchq-meadow-photo.png` — old approved photograph, used only for photographic look, light, colour, haze, and detail level.
3. `../../m2/boards/meadow-a-adventurous.png` — approved adventurous target board, used only for materials and character.

## Pass 1 prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: approved architectural place photograph, final project image at exactly 1280×720, landscape 16:9.
Primary request: REMAKE the approved place photograph so it agrees with the current 3D model. Transform the geometry master into a highly realistic late-summer aerial architectural photograph. This is GCHQ's meadow roof in 2045: the most recognisable building in Gloucestershire, re-roofed; 3.6 hectares of south-facing ring, 20 m up, turned over to species-rich wildflower meadow—the largest piece of open land in the box that nobody has to buy, 100 m from the new campus. It must read as an extraordinary but credible built place, based on real built precedents, not a corporate office park and not an illustration.
Input images:
- Image 1 is the ABSOLUTE GEOMETRY MASTER and camera master: the current 3D model render from camera [20, 125, 170] looking at [123, 62.597, 64]. Follow Image 1 for every visible object's position, silhouette, footprint, height, scale, perspective, horizon, occlusion, field boundary, road, building, tree belt, orchard row, solar row, canopy and open stormwater channel. Keep the geometry within approximately 15 pixels at 1280×720. Do not substitute, simplify, invent, relocate, enlarge or erase site elements. Preserve the giant circular ring roof, its central circular courtyard opening, the near-right wedge/entrance projection, outer wall profile, and exact framing.
- Image 2 is the OLD approved photograph at this exact camera. Use Image 2 ONLY for photographic look, natural light, colour, atmospheric haze, believable detail density, camera realism and late-summer afternoon sun. Its layout is obsolete: DO NOT copy its roads, parking, buildings, vegetation layout, roof paths, facade design, or any other geometry.
- Image 3 is the approved adventurous target board for this site. Use it ONLY for material language and character: buff brick, honey-toned structural timber, fine PV glass, rich meadow roofs, ecologically mature planting, elegant restrained detailing. Do not copy its camera or layout.
Scene/backdrop: Exact Image 1 site layout. Across the middle and distance retain the dense new neighbourhood shown in Image 1—about 1,100 homes expressed as compact terraces and mid-rise timber blocks, not detached suburban sprawl. Retain the campus courtyard blocks. Retain the long vertical bifacial solar rows over pasture, the solar canopies over GCHQ car parks, mature orchard rows and woodland belts, and visible open stormwater channels exactly where the geometry master places them. Keep the distant hills and horizon profile exactly aligned to Image 1.
Subject: The dominant huge circular GCHQ ring fills the lower and central frame exactly as in Image 1. Its 3.6-hectare roof is a continuous, credible, slightly weathered late-summer wildflower meadow with fine low species—grasses, seed heads and small yellow, white and muted purple flowers—following the model's concentric maintenance bands and radial seams without adding new broad paths. The central opening remains the exact same size and shape, with its existing trees and lawn in their model positions. Give the outer and inner elevations believable glazing, buff brick and honey timber while preserving every edge and height from Image 1. The roof must visibly feel 20 m above ground.
Style/medium: Photorealistic high-resolution aerial/drone architectural photography; physically plausible materials, reflections, glazing depth, drainage, weathering, vegetation variation and atmospheric perspective. Built-precedent character informed by Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattørkaia, Augustenborg and Next2Sun. Documentary realism, not a glossy corporate visualization.
Composition/framing: Pixel-faithful to Image 1. Same camera pose, focal length, perspective, horizon height and full-frame composition. Whole-frame 1280×720; no crop, no warp, no reframing. The ring roof outer perimeter, courtyard opening, near-right projection, background woodland and every major row/block must land in the same position as Image 1.
Lighting/mood: Match Image 2's warm late-summer afternoon sun direction, soft blue sky, modest scattered cloud, gentle atmospheric haze, natural contrast and believable shadows. Preserve geometric legibility in shadow.
Color palette: Warm buff brick, honey timber, dark charcoal PV glass, meadow olive/green/gold with restrained wildflower colour, natural British late-summer landscape, soft blue sky.
Materials/textures: Highly credible fine meadow planting, low parapets and roof-edge drainage, realistic glass mullions, buff masonry, honey timber, dark bifacial PV modules, asphalt, gravel, pasture, orchards and mature mixed woodland. Detail must stay subordinate to the geometry master.
People and vehicles: Sparse, true-to-scale people and vehicles only where physically plausible; never oversized; no crowds. Do not let parked cars overwrite solar rows, planting, drainage or boundaries.
Text (verbatim): ""
Constraints: Geometry fidelity overrides beauty and overrides Images 2 and 3. Follow Image 1, never the old photograph, for what is where. Maintain all Image 1 silhouettes and alignments within about 15 px at 1280×720. Preserve the exact central void, roof width, circular outline, front wall, near-right wedge, roads, solar arrays, housing masses, woodland belt and distant terrain. Natural photographic detail may be added only inside these fixed shapes. No crop or warp.
Avoid: old Image 2 layout; detached-house suburb replacing the model's new terraces and timber blocks; missing or shifted solar arrays; invented buildings; changed circular proportions; enlarged courtyard; extra roof paths; roof terraces; railings dominating the roof; corporate office-park styling; futuristic forms; illustration; painterly texture; obvious CGI; miniature/tilt-shift look; dramatic cinematic grading; excessive saturation; fake bokeh; distorted roads; floating trees; malformed cars; giant people; signage; labels; logos; text; watermark.
```

### Pass 1 inspection

The first pass had a strong photographic finish, credible meadow planting, and successful buff-brick/honey-timber glazing. It was not accepted because the ring was enlarged and lowered in frame, the courtyard and horizon shifted, and the roof planting obscured too much of the model's concentric and radial organization. Background geometry also became more generic than the master.

## Pass 2 correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: corrected final architectural place photograph, exactly 1280×720, landscape 16:9.
Primary request: CORRECTION PASS ONLY. Rebuild the first-pass photograph onto the exact geometry, camera and full-frame composition of Image 1. Preserve the photorealistic late-summer material treatment of Image 2, but correct all geometry drift. The finished photograph must match Image 1's pixel layout within approximately 15 px at 1280×720.
Input images:
- Image 1 is the ABSOLUTE GEOMETRY AND CAMERA MASTER. It overrides everything. Trace its major silhouettes and screen positions exactly.
- Image 2 is the first generated pass. Retain only its successful photographic realism, meadow texture, glazing, buff brick/honey timber character, sunlight, haze and detail quality. Do not retain its framing or geometry drift.
Required geometry corrections:
1. Zoom out and restore the exact Image 1 framing. The circular ring must occupy exactly the same screen area as Image 1: outer roof left edge near x=181, right edge near x=1208, top edge near y=206, bottom/front edge near y=709 at 1280×720.
2. Restore the central courtyard opening to Image 1: same horizontally oval screen shape, left edge near x=484, right edge near x=883, top near y=258, bottom near y=402. Do not shift or enlarge it.
3. Restore the distant horizon and hills to Image 1: sky is only the narrow upper strip; hill skyline remains near y=0–34. Do not use the taller mountain/horizon composition from Image 2.
4. Restore the roof's modeled concentric maintenance bands and radial seams exactly where visible in Image 1. Meadow planting is low and fine so these bands remain legible; no invented broad diagonal paths.
5. Restore the exact outer wall height and near-right wedge/entrance projection silhouette from Image 1. The near facade is mostly dark/glazed and shaded at this camera, not an oversized bright multi-storey curtain wall.
6. Restore every background object to Image 1: woodland belt shape; pale rectangular service building upper right; long vertical bifacial solar rows behind and to both sides; left solar-canopy rows; roads; open land; houses and blocks. Do not replace this model layout with the first pass's invented landscape.
7. Preserve the exact Image 1 camera [20, 125, 170] looking at [123, 62.597, 64], perspective, horizon height, occlusions and full uncropped frame.
Scene/content: GCHQ meadow roof in 2045, 3.6 hectares of south-facing ring 20 m above ground, credible species-rich late-summer wildflower meadow. Exact Image 1 neighbourhood and infrastructure, including the dense new settlement, campus courtyard blocks, bifacial solar rows over pasture, solar car-park canopies, orchards, woodland belts and open stormwater channels. Materials: buff brick, honey timber, dark PV glass and ecologically mature planting, built-precedent realism informed by Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattørkaia, Augustenborg and Next2Sun.
Style/medium: Natural high-resolution drone architectural photography; documentary realism; physically plausible materials, scale, reflections, weathering, vegetation variation and atmospheric perspective.
Lighting/mood: Keep Image 2's warm late-summer afternoon light, soft blue sky, modest cloud, natural colour and gentle haze, but conform shadows to Image 1 geometry.
People and vehicles: Sparse and true scale only.
Text (verbatim): ""
Constraints: Change the first pass's geometry and framing to match Image 1; retain its photographic finish. Geometry fidelity overrides attractiveness. Whole-frame 1280×720, no crop, no warp, no reframing. Preserve every major edge and object position from Image 1 within about 15 px.
Avoid: enlarged ring; low or shifted building; enlarged/shifted courtyard; tall mountain sky; old-photo layout; invented buildings; missing solar rows; lost roof bands; new roof paths; corporate office park; futuristic design; illustration; obvious CGI; tilt-shift; cinematic grading; excessive saturation; malformed cars; oversized people; signage; labels; logos; text; watermark.
```

### Final inspection

The correction substantially improves the match to the geometry plate. The outer ring's left, right, and top extents, central opening, near-right projection, service block, woodland belt, and principal solar-row fields are close to their master positions. The ring and courtyard retain the intended scale relationship, the foreground facade is dark and subordinate, and the meadow reads clearly as a continuous elevated landscape. Lighting and material character are convincingly photographic and consistent with the reference set.

Visible drift remains. The distant hill skyline is taller and more articulated than the very shallow master horizon. Fine-grain background housing is interpreted as generic low-rise suburban fabric rather than reliably preserving every terrace/timber-block footprint, and some small roads, field edges, orchard trees, drainage lines, and solar-row endpoints cannot honestly be claimed to be within 15 px. The courtyard tree count and exact positions are also interpreted rather than traced. On the roof, the concentric bands are retained but read as mown meadow lines; several radial divisions are softer or slightly shifted.

Elements that can still read as CGI on close inspection include the unusually even repetition of distant houses and trees, the high-density/over-crisp flower pattern, some simplified solar structures, and a few softened or ambiguous tiny vehicles. No text, logo, or watermark is visible.
