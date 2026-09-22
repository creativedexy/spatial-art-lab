# Campus B — image-generation notes

Built-in `image_gen` was used in sketch-to-render mode. Each variant received one initial generation and one geometry-only correction pass. Final correction outputs were resized as whole frames from 1672×941 to exactly 1280×720; there was no crop or retouching after image generation. Because the generated source aspect ratio differed from 16:9 by about 0.05%, the exact-size resize introduces a negligible sub-pixel-scale aspect adjustment.

## Measured

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, 1280x720 landscape
Primary request: Transform Image 1 into a convincingly built and photographed 2045 view of the Golden Valley campus around IDEA, looking south-east from 360 m, in the MEASURED variant: the best of current UK sustainable practice, restrained material palette, calm and credible.
Input images: Image 1 is the geometry master and edit target. Image 2 is the approved photographic-realism, late-summer light, colour, haze and detail reference. Image 3 is only a reference for how this scheme sits in the real west-Cheltenham landscape, never for architecture or camera. Image 4 is only a reference for the IDEA building concept of a meadow roof running down to the ground.
Scene/backdrop: Golden Valley, west Cheltenham, in 2045. Existing town beyond the site remains an ordinary existing English town of red and buff brick with slate and clay tile roofs. GCHQ's ring remains exactly in its Image 1 position in the distance, upgraded with a mature wildflower-meadow roof.
Subject: The two exact foreground courtyard-block footprints from Image 1 become refined timber-and-glass campus buildings, no more than seven storeys, with calm façades, legible timber bays, generous glazing, PV roofs sawn to the sun, narrow meadow strips, and woodland courtyards retaining mature oaks. The existing angular IDEA landmark beside GCHQ keeps its exact Image 1 footprint and massing but gains the single meadow roof that runs down to the ground. Keep the mature orchard in the foreground. Add only true-scale people on existing streets, paths, courtyards and accessible roofs, and cars only where the plate already indicates roads or parking.
Style/medium: Ultra-photorealistic real aerial architectural photograph, not a 3D render or illustration. Match Image 2's believable built detail, material variation, vegetation texture, atmospheric depth, lens behaviour and photographic imperfections.
Composition/framing: LOCK Image 1 exactly. Preserve its 1280x720 full frame, camera, aerial viewpoint, horizon, terrain, every building position, footprint and height, every street, path, tree belt, orchard, field and all existing-town fabric within about 15 px. Do not crop, warp, zoom, rotate or shift the frame.
Lighting/mood: Match Image 2: clear late-summer afternoon, warm directional sun, realistic shadows, blue atmospheric haze, calm inhabited mood.
Color palette: Restrained natural timber, muted bronze and charcoal metal, clear glass, weathered buff and red brick, meadow greens and late-summer gold.
Materials/textures: Built, weathered, constructionally plausible mass timber and glass; crisp PV arrays integrated into sawtooth roof planes; modest wildflower roof bands; native woodland planting at maturity; subtle silver open stormwater channels and rain gardens; limited solar carports; ordinary UK road and paving finishes.
Constraints: Geometry master dominates all other references. Change materials, planting maturity and environmental systems only; do not redesign the master layout. Every intervention must have a built precedent. No building above seven storeys. No new blocks, no moved blocks, no towers. Keep GCHQ a ring, keep both foreground blocks as their exact rectangular courtyard forms, keep IDEA as the one landmark. People and cars must be tiny and correctly scaled for a 360 m aerial view.
Avoid: corporate office park character, generic glass boxes, futuristic forms, excessive gloss, sterile plazas, invented roads, invented buildings, displaced housing, oversized people or cars, illustration, painterly effects, obvious CGI, fantasy ecology, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the MEASURED 2045 architectural aerial photomontage
Primary request: Correct only the geometry and framing drift in Image 1, the generated measured render. Preserve its convincing photographic realism, restrained timber-and-glass material language, calm planting, PV/meadow balance, late-summer light and overall measured design intensity.
Input images: Image 1 is the generated measured render to correct. Image 2 is the authoritative geometry master. Image 3 is the approved photographic look reference. Image 4 is landscape context only. Image 5 supplies only the IDEA meadow-roof-to-ground concept.
Geometry correction: Re-register the entire scene to Image 2 within about 15 px at 1280x720. Match Image 2's exact full-frame camera, horizon height and silhouette, terrain contours, orchard extent, fields, every street and path, tree belts, existing town pattern, and the exact positions, footprints and heights of every building. Restore the two foreground campus buildings to Image 2's exact rectangular courtyard footprints, dimensions, separation, orientation and height. Restore GCHQ's ring to Image 2's exact size and position. Restore the angular IDEA building beside GCHQ to Image 2's exact footprint, orientation and massing, keeping its meadow roof running down to ground as the one landmark.
Composition/framing: Output the full 16:9 frame corresponding exactly to Image 2. No crop, zoom, warp, rotation, camera relocation or invented topography.
Constraints: Change geometry alignment only. Keep the measured variant's restrained natural timber, muted bronze and glass, modest integrated PV, narrow meadow strips, woodland courtyards, subtle stormwater lines, true-scale people and correctly parked cars. Keep all buildings at or below seven storeys. Do not add, remove or move any block.
Avoid: any new architecture, changed building mass, enlarged courtyards, altered GCHQ proportions, displaced housing, new hills, changed horizon, corporate office park, CGI appearance, illustration, text, labels, logos, watermark.
```

### Passes and inspection

- Passes: 2 total — one generation, then one geometry-only correction.
- Geometry: the correction retains the two courtyard blocks, GCHQ ring, IDEA wedge and orchard in the right broad relationships, but it does **not** meet the requested ~15 px plate registration. The foreground blocks are still larger and lower in frame than the plate, the ring/IDEA group is enlarged and shifted, and the distant horizon/topography is substantially reinterpreted.
- Realism: strong aerial-photo credibility, convincing mature vegetation, material grain, roof PV and late-summer light.
- CGI/corporate risk: repetitive façades and unusually pristine landscaping still have a polished architectural-visualisation quality; the calm timber palette avoids the worst office-park character.

## Bold

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, 1280x720 landscape
Primary request: Transform Image 1 into a convincingly built and photographed 2045 view of the Golden Valley campus around IDEA, looking south-east from 360 m, in the BOLD variant: stronger material identity and visibly more of every sustainable move than the measured scheme—more integrated PV, more meadow roof, more mature native tree mass and clearly visible water—while remaining completely buildable and photographic.
Input images: Image 1 is the geometry master and edit target. Image 2 is the approved photographic-realism, late-summer light, colour, haze and detail reference. Image 3 is only a reference for how this scheme sits in the real west-Cheltenham landscape, never for architecture or camera. Image 4 is only a reference for the IDEA building concept of a meadow roof running down to the ground.
Scene/backdrop: Golden Valley, west Cheltenham, in 2045. Existing town beyond the site remains an ordinary existing English town of red and buff brick with slate and clay tile roofs. GCHQ's ring remains exactly in its Image 1 position in the distance, with a dense mature wildflower-meadow roof.
Subject: The two exact foreground courtyard-block footprints from Image 1 become high-quality timber-and-glass campus buildings, no more than seven storeys, with a stronger rhythm of exposed mass-timber bays and warm low-carbon masonry, generous glazing, extensive PV roofs cut into purposeful south-facing sawtooth planes, broad meadow strips, and dense woodland courtyards retaining veteran oaks. The existing angular IDEA landmark beside GCHQ keeps its exact Image 1 footprint and massing but gains the single meadow roof that visibly runs down to the ground. Keep and strengthen the mature orchard in the foreground without changing its footprint. Make Augustenborg-like open stormwater channels and rain gardens read as thin silver-blue lines along existing routes; add plausible solar carports only over existing parking; add limited vertical bifacial PV rows only within existing open pasture. Add only true-scale people on existing streets, paths, courtyards and accessible roofs, and cars only where the plate already indicates roads or parking.
Style/medium: Ultra-photorealistic real aerial architectural photograph, not a 3D render or illustration. Match Image 2's believable built detail, material variation, vegetation texture, atmospheric depth, lens behaviour and photographic imperfections.
Composition/framing: LOCK Image 1 exactly. Preserve its 1280x720 full frame, camera, aerial viewpoint, horizon, terrain, every building position, footprint and height, every street, path, tree belt, orchard, field and all existing-town fabric within about 15 px. Do not crop, warp, zoom, rotate or shift the frame.
Lighting/mood: Match Image 2: clear late-summer afternoon, warm directional sun, realistic shadows, blue atmospheric haze, calm inhabited mood.
Color palette: Distinct but natural warm timber, dark bronze, charcoal PV, clear glass, buff and red brick, strong meadow greens and late-summer gold, restrained silver-blue water.
Materials/textures: Tectonically legible mass timber and glass; extensive crisp PV arrays integrated into sawtooth roof planes; generous species-rich meadow roofs; mature mixed native woodland and orchard; open planted water channels, rain gardens, permeable paving; solar carports and sparse vertical bifacial PV with grazed grass below.
Constraints: Geometry master dominates all other references. Change materials, planting maturity and environmental systems only; do not redesign the master layout. Every intervention must have a built precedent. No building above seven storeys. No new blocks, no moved blocks, no towers. Keep GCHQ a ring, keep both foreground blocks as their exact rectangular courtyard forms, keep IDEA as the one landmark. People and cars must be tiny and correctly scaled for a 360 m aerial view.
Avoid: corporate office park character, generic glass boxes, futuristic forms, excessive gloss, sterile plazas, invented roads, invented buildings, displaced housing, oversized people or cars, illustration, painterly effects, obvious CGI, fantasy ecology, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the BOLD 2045 architectural aerial photomontage
Primary request: Correct only the geometry and framing drift in Image 1, the generated bold render. Preserve its convincing photographic realism, stronger timber identity, extensive integrated PV and meadow roofs, dense mature tree mass, visible water, late-summer light and overall bold design intensity.
Input images: Image 1 is the generated bold render to correct. Image 2 is the authoritative geometry master. Image 3 is the approved photographic look reference. Image 4 is landscape context only. Image 5 supplies only the IDEA meadow-roof-to-ground concept.
Geometry correction: Re-register the entire scene to Image 2 within about 15 px at 1280x720. Match Image 2's exact full-frame camera, horizon height and silhouette, terrain contours, orchard extent, fields, every street and path, tree belts, existing town pattern, and the exact positions, footprints and heights of every building. Restore the two foreground campus buildings to Image 2's exact rectangular courtyard footprints, dimensions, separation, orientation and height. Restore GCHQ's ring to Image 2's exact size and position. Restore the angular IDEA building beside GCHQ to Image 2's exact footprint, orientation and massing, keeping its meadow roof running down to ground as the one landmark.
Composition/framing: Output the full 16:9 frame corresponding exactly to Image 2. No crop, zoom, warp, rotation, camera relocation or invented topography.
Constraints: Change geometry alignment only. Keep the bold variant's warm mass timber and glass, extensive sawtooth PV, broad meadow bands, dense woodland courtyards, visible silver-blue stormwater channels and rain gardens, solar carports only over existing parking, sparse vertical bifacial PV only in existing pasture, true-scale people and correctly parked cars. Keep all buildings at or below seven storeys. Do not add, remove or move any block.
Avoid: any new architecture, changed building mass, enlarged courtyards, altered GCHQ proportions, displaced housing, new hills, changed horizon, corporate office park, CGI appearance, illustration, text, labels, logos, watermark.
```

### Passes and inspection

- Passes: 2 total — one generation, then one geometry-only correction.
- Geometry: broad scene hierarchy is recognisable, but registration remains outside ~15 px. The two courtyards, ring and IDEA are noticeably rescaled/repositioned, roads and housing are reauthored, and the horizon is replaced by a different photographic landscape.
- Realism: highly convincing vegetation, PV, water reflections and warm aerial lighting. The bold variant reads clearly stronger than measured without looking speculative.
- CGI/corporate risk: the perfectly even timber grids, uniformly lush roofs and highly curated waterways read slightly like premium visualisation; the water and woodland soften office-park associations.

## Adventurous

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, 1280x720 landscape
Primary request: Transform Image 1 into a convincingly built and photographed 2045 view of the Golden Valley campus around IDEA, looking south-east from 360 m, in the ADVENTUROUS variant: the edge of design excellence that is still buildable and photographable, with expressive timber structure, walkable roofs, water and planting as the dominant spatial moves, and renewable energy designed as landscape.
Input images: Image 1 is the geometry master and edit target. Image 2 is the approved photographic-realism, late-summer light, colour, haze and detail reference. Image 3 is only a reference for how this scheme sits in the real west-Cheltenham landscape, never for architecture or camera. Image 4 is only a reference for the IDEA building concept of a meadow roof running down to the ground.
Scene/backdrop: Golden Valley, west Cheltenham, in 2045. Existing town beyond the site remains an ordinary existing English town of red and buff brick with slate and clay tile roofs. GCHQ's ring remains exactly in its Image 1 position in the distance, with a botanically rich mature wildflower-meadow roof.
Subject: The two exact foreground courtyard-block footprints from Image 1 become exceptional but feasible timber-and-glass campus buildings, no more than seven storeys, with deeply articulated exposed timber exoskeletons and winter gardens, highly legible construction, sawtooth PV roof landscapes angled to the sun, continuous meadow terraces and genuinely walkable planted roof routes contained within the existing envelopes. Their courtyards become dense woodland rooms around retained veteran oaks. The existing angular IDEA landmark beside GCHQ keeps its exact Image 1 footprint and massing and becomes the one landmark through a dramatic but buildable meadow roof that continues down to the ground, following Image 4's idea only. Keep the mature orchard in the foreground. Make a connected chain of broad but plausible Augustenborg-like open stormwater channels, rain gardens and shallow retention landscapes visible along existing routes, reflecting the sky. Treat energy as landscape: solar canopies only above existing parking, and elegant Next2Sun-like vertical bifacial PV rows over grazed existing pasture without creating new building blocks. Add only true-scale people on existing streets, paths, courtyards and walkable roofs, and cars only where the plate already indicates roads or parking.
Style/medium: Ultra-photorealistic real aerial architectural photograph, not a 3D render or illustration. Match Image 2's believable built detail, material variation, vegetation texture, atmospheric depth, lens behaviour and photographic imperfections. The ambition comes from construction, landscape and ecological performance, never from sci-fi form.
Composition/framing: LOCK Image 1 exactly. Preserve its 1280x720 full frame, camera, aerial viewpoint, horizon, terrain, every building position, footprint and height, every street, path, tree belt, orchard, field and all existing-town fabric within about 15 px. Do not crop, warp, zoom, rotate or shift the frame.
Lighting/mood: Match Image 2: clear late-summer afternoon, warm directional sun, realistic shadows, blue atmospheric haze, vivid but natural and inhabited.
Color palette: Expressive honey-toned timber, dark weathered bronze and charcoal PV, transparent glass, local buff and red brick, deep woodland greens, flower-rich late-summer gold, silver-blue water.
Materials/textures: Real structural mass timber with joints and depth; high-performance glass and winter gardens; extensive crisp integrated PV on oriented sawtooth roofs; flower-rich meadow roofs and terraces; mature native woodland, veteran oaks and orchard; constructed wetland edges, stone-lined rills and rain gardens; solar canopies and sparse vertical bifacial PV over grazed pasture.
Constraints: Geometry master dominates all other references. Change materials, planting maturity and environmental systems only; do not redesign the master layout. Every intervention must have a built precedent and look completed, occupied and maintained. No building above seven storeys. No new blocks, no moved blocks, no towers. Keep GCHQ a ring, keep both foreground blocks as their exact rectangular courtyard forms, keep IDEA as the one landmark. People and cars must be tiny and correctly scaled for a 360 m aerial view.
Avoid: corporate office park character, generic glass boxes, biomorphic or futuristic architecture, megastructures, excessive gloss, sterile plazas, invented roads, invented buildings, displaced housing, oversized people or cars, illustration, painterly effects, obvious CGI, fantasy ecology, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the ADVENTUROUS 2045 architectural aerial photomontage
Primary request: Correct only the geometry and framing drift in Image 1, the generated adventurous render. Preserve its convincing photographic realism, expressive but buildable timber structure, walkable planted roofs, dominant water and planting, energy-as-landscape systems, late-summer light and overall adventurous design intensity.
Input images: Image 1 is the generated adventurous render to correct. Image 2 is the authoritative geometry master. Image 3 is the approved photographic look reference. Image 4 is landscape context only. Image 5 supplies only the IDEA meadow-roof-to-ground concept.
Geometry correction: Re-register the entire scene to Image 2 within about 15 px at 1280x720. Match Image 2's exact full-frame camera, horizon height and silhouette, terrain contours, orchard extent, fields, every street and path, tree belts, existing town pattern, and the exact positions, footprints and heights of every building. Restore the two foreground campus buildings to Image 2's exact rectangular courtyard footprints, dimensions, separation, orientation and height. Restore GCHQ's ring to Image 2's exact size and position. Restore the angular IDEA building beside GCHQ to Image 2's exact footprint, orientation and massing, keeping its meadow roof running down to ground as the one landmark.
Composition/framing: Output the full 16:9 frame corresponding exactly to Image 2. No crop, zoom, warp, rotation, camera relocation or invented topography.
Constraints: Change geometry alignment only. Keep the adventurous variant's expressive exposed timber depth and winter gardens, extensive oriented PV, continuous walkable meadow roof routes within the fixed envelopes, veteran-oak woodland courtyards, connected reflective stormwater and rain-garden landscape along existing routes, solar canopies only over existing parking, vertical bifacial PV only over existing grazed pasture, true-scale people and correctly parked cars. Keep all buildings at or below seven storeys. Do not add, remove or move any block.
Avoid: any new architecture, changed building mass, enlarged courtyards, altered GCHQ proportions, displaced housing, new hills, changed horizon, futuristic forms, megastructures, corporate office park, CGI appearance, illustration, text, labels, logos, watermark.
```

### Passes and inspection

- Passes: 2 total — one generation, then one geometry-only correction.
- Geometry: the main identities and ordering survive, but exact plate matching remains unsuccessful. Foreground blocks are enlarged and lowered, GCHQ/IDEA are rescaled, vertical PV is introduced on the right pasture, and much of the town, road network and horizon is regenerated rather than held within ~15 px.
- Realism: strong photographic finish; timber depth, wetland reflections, solar landscape and mature orchard are materially legible and largely buildable.
- CGI/corporate risk: the scene is exceptionally clean and uniformly mature, while repeated façade bays and perfectly distributed ecological features retain some visualisation polish. It reads as landscape-led rather than a conventional corporate park.
