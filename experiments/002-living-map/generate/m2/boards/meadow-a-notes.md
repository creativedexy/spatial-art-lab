# Meadow A — image-generation record

Built-in `image_gen` was used in sketch-to-render mode. Image 1 was the geometry master/edit target, Image 2 the approved photographic look, and Image 3 context-only. Each variant received one initial generation and one geometry-correction pass. The selected correction-pass outputs were resized as a whole frame to 1280×720 with no crop or retouching.

## Measured

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, measured variant
Primary request: Convert Image 1 into a convincing real aerial photograph of GCHQ at Golden Valley, west Cheltenham, viewed from 340 m to the south-west. This is the measured version: the best of current UK practice, restrained, calm, and already built.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic realism, late-summer light, colour, haze, material detail, wildflower roof and human-scale reference; Image 3 is only a broad reference for how this site sits in the real west-Cheltenham landscape, never a source of replacement geometry or architecture.
Geometry lock: Preserve Image 1's exact 1280x720 whole-frame composition, camera, lens, viewpoint, horizon, terrain silhouette, road alignments, car-park extents, tree belts, individual building positions, footprints, rooflines and heights, the GCHQ ring outline and courtyard opening, and the existing town, within about 15 pixels. Do not crop, warp, zoom, rotate, reframe, move or invent any structure. The pale rectangular service building behind the ring and all foreground ancillary blocks remain exactly where they are. Keep all distant hills and existing neighbourhoods in their plate locations.
Change only these 2045 elements: (1) Render the existing GCHQ ring roof as a natural, textured late-summer wildflower meadow with muted grasses and small yellow, white and purple flowers; retain the roof's exact annular footprint, exact outer and inner edges, and existing concentric path geometry. Make the concentric mown paths physically believable and place only a few tiny people walking on them at true aerial scale. The ring facade remains the same height and footprint, now believable glass and warm restrained masonry/metal detailing. Keep the open central courtyard exactly the same size and position, with mature but plausible planting. (2) Over the car parks already shown in Image 1, turn the existing black canopy planes into orderly blue-black photovoltaic solar canopies on slim posts, using the plate's exact canopy positions, extents, angles and row spacing; show ordinary parked cars visibly beneath and between them. Do not extend canopies onto roads, buildings or landscape. (3) Add restrained native deciduous tree avenues only along existing car-park edges, aligned with the plate, without obscuring the road layout.
Photographic standard: Match Image 2's high-end real aerial photography, late-summer afternoon sunlight, soft atmospheric haze, natural aerial depth, crisp foreground detail, believable glazing, masonry, vegetation, cars and tiny people. Existing town beyond the site must read as an ordinary established English town of red and buff brick houses with slate and clay tile pitched roofs, precisely where Image 1 puts it. Natural variation and imperfection; no glossy masterplan look.
Lighting/mood: calm warm late-summer afternoon, sun direction and long shadows consistent across the whole frame, pale blue slightly hazy sky.
Color palette: restrained greens, straw meadow gold, muted brick, grey slate, clay tile, blue-black PV.
Constraints: Everything must look built and photographed. Seven storeys maximum, though no building height may change from Image 1. People visible only at true scale on existing paths and roof paths; cars only where cars park. No new blocks, no towers, no changed roads, no new paths beyond the existing concentric roof paths, no architectural redesign of surrounding buildings.
Avoid: corporate office park, speculative masterplan, illustration, painterly surfaces, low-poly CGI, oversaturated green, fantasy architecture, extra rings, distorted courtyard, enlarged roof opening, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction pass for the measured 2045 architectural aerial photomontage
Primary request: Correct Image 2 so its geometry and framing conform much more literally to Image 1 while retaining Image 2's successful photographic materials, meadow roof, solar canopies, cars, tiny people and late-summer realism.
Input images: Image 1 is the absolute pixel-layout and geometry master; Image 2 is the first photoreal measured pass to correct; Image 3 remains the approved photographic look reference; Image 4 remains context-only and must not replace the plate landscape.
Correction target: Reconstruct the image on Image 1's exact camera and silhouettes. Match Image 1's horizon line and broad smooth hill silhouette, town density, woodland edge, road and car-park curves, GCHQ ring outer edge and central opening, and every foreground ancillary building outline within about 15 pixels. In particular restore the exact low faceted roof shapes and footprints of the three foreground buildings, restore the exact pale rectangular service building behind the ring, preserve the plate's ring size and placement, and keep the car-park canopy rows on the plate's exact black-plane locations. Do not import the detailed mountain skyline or altered foreground block shapes from Image 2.
Keep only these measured 2045 changes: restrained textured wildflower meadow across the exact annular ring roof; existing concentric mown roof paths with a few tiny true-scale people; blue-black PV canopies on slim posts exactly over the plate's existing car-park canopy planes with cars visible beneath and between; restrained native deciduous avenues along existing car-park edges. Everything else remains as Image 1, photorealised rather than redesigned.
Photographic standard: Retain Image 2 and Image 3's convincing high-end aerial-photo finish, warm late-summer afternoon light, atmospheric haze, realistic English town materials, natural vegetation, believable glass, masonry, cars and people. Keep the existing town ordinary red/buff brick with slate and clay tile pitched roofs. Natural imperfection, calm restrained palette.
Hard invariants: Same full 16:9 frame as Image 1. No crop, zoom, warp, rotation or reframing. No new buildings, towers, roads, paths, canopy rows or altered heights. Do not enlarge or move the courtyard opening. Do not turn ancillary blocks into new architecture. Seven storeys maximum but all heights remain the plate heights.
Avoid: corporate office park, glossy masterplan, illustration, painterly surfaces, low-poly CGI, fantasy architecture, extra rings, distorted courtyard, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Passes and inspection

- Passes: initial generation + one geometry correction; correction selected.
- Geometry: the correction recovers the plate's broad ring placement, courtyard relationship, service block, car-park arcs and three foreground masses better than the first pass, but the requested ~15 px tolerance is not met. The distant hill profile, town grain, tree belt, ring outline and several ancillary roof silhouettes are visibly re-authored; the foreground road/canopy pattern also differs locally.
- Realism: strong aerial-photo light, material detail, roof planting, cars and solar canopy legibility. The restraint is credible for current UK practice.
- CGI/corporate read: substantially reduced; the scene is still unusually clean and evenly maintained, and repeated canopy/house/tree rhythms occasionally betray generation.

## Bold

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, bold variant
Primary request: Convert Image 1 into a convincing real aerial photograph of GCHQ at Golden Valley, west Cheltenham, viewed from 340 m to the south-west. This is the bold version: stronger material identity and visibly more of every sustainable move, while remaining completely buildable and preserving the plate layout.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic realism, late-summer light, colour, haze, material detail, wildflower roof and human-scale reference; Image 3 is only a broad reference for how this site sits in the real west-Cheltenham landscape, never a source of replacement geometry or architecture.
Geometry lock: Preserve Image 1's exact 1280x720 whole-frame composition, camera, lens, viewpoint, horizon, terrain silhouette, road alignments, car-park extents, tree belts, every building position, footprint, roofline and height, the GCHQ ring outline and courtyard opening, and the existing town, within about 15 pixels. Do not crop, warp, zoom, rotate, reframe, move or invent any structure. The pale rectangular service building behind the ring and all foreground ancillary blocks remain exactly where they are. Keep all distant hills and existing neighbourhoods in their plate locations.
Change only these 2045 elements: (1) Render the exact GCHQ annular roof as a richly textured late-summer wildflower meadow, more abundant and biodiverse than the measured version, with legible grasses and drifts of small yellow, white and purple flowers; retain the roof's exact outer and inner edges and all existing concentric path geometry. Make the paths believable and walkable with a modest number of tiny people at true aerial scale. Keep the ring's exact height and footprint; give its facade a robust identity of warm brick, dark metal and clear high-performance glazing without changing its massing. Keep the central courtyard opening exactly fixed, with denser native planting but no geometry change. (2) Over the car parks already shown in Image 1, turn the existing black planes into high-coverage blue-black photovoltaic solar canopies on slim posts, using the plate's exact canopy positions, extents, angles and row spacing; retain ordinary cars visibly beneath and between them. Do not create any additional canopy rows. (3) Strengthen native deciduous tree avenues only along existing car-park edges, with more continuous tree mass but roads and parking geometry still legible. (4) Make existing drainage margins and swales read subtly as a few narrow silver-blue rain-garden lines beside existing car-park edges only; do not add or reroute roads, paths, ponds or earthworks.
Photographic standard: Match Image 2's high-end real aerial photography, late-summer afternoon sunlight, soft atmospheric haze, natural aerial depth, crisp foreground detail, believable glazing, masonry, vegetation, cars and tiny people. Existing town beyond the site must read as an ordinary established English town of red and buff brick houses with slate and clay tile pitched roofs, precisely where Image 1 puts it. Natural variation and imperfection; emphatic sustainability but never a glossy masterplan.
Lighting/mood: warm late-summer afternoon, sun direction and shadows consistent across the entire frame, pale blue slightly hazy sky.
Color palette: deeper native greens, meadow straw and flower colour, warm brick, charcoal metal, grey slate, clay tile, blue-black PV, restrained silver-blue water.
Constraints: Everything must look built and photographed. Seven storeys maximum, though no building height may change from Image 1. People at true scale only on existing paths and roof paths; cars only where cars park. No new blocks, towers, roads, paths, canopy rows or architecture outside the three permitted interventions.
Avoid: corporate office park, speculative masterplan, illustration, painterly surfaces, low-poly CGI, oversaturated green, fantasy architecture, extra rings, distorted courtyard, enlarged roof opening, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction pass for the bold 2045 architectural aerial photomontage
Primary request: Correct Image 2 so its geometry and framing conform literally to Image 1 while retaining Image 2's successful bold wildflower meadow, strong PV presence, native tree mass, narrow visible rain-garden lines, cars, tiny people and convincing photo realism.
Input images: Image 1 is the absolute pixel-layout and geometry master; Image 2 is the first bold photoreal pass to correct; Image 3 is the approved photographic finish; Image 4 is context-only and must not replace the plate landscape.
Correction target: Rebuild on Image 1's exact camera and silhouettes. Match Image 1's smooth horizon and hills, existing-town placement and density, woodland edge, every road and car-park curve, every black canopy-plane location, the GCHQ ring outer and inner outlines, and every foreground ancillary building outline within about 15 pixels. Restore the exact three low faceted foreground block footprints and roof shapes, the exact pale rectangular service building behind the ring, the exact ring size and position, and the exact canopy rows from Image 1. Reject Image 2's imported mountain detail, altered building profiles, extra drainage alignments and changed car-park pattern.
Keep only these bold 2045 changes: richer biodiverse late-summer wildflower planting across the exact annular roof; the plate's exact concentric mown paths with modest tiny true-scale people; warm brick, dark metal and believable glazing on the unchanged ring facade; blue-black PV canopies on slim posts exactly occupying the plate's existing black canopy planes with cars visible below; stronger but aligned native tree avenues along existing car-park edges; only a few narrow silver-blue rain-garden lines within existing landscape margins, never changing geometry.
Photographic standard: Retain Image 2 and Image 3's high-end real aerial-photo finish, warm late-summer afternoon light, atmospheric haze, real English town materials, natural vegetation and believable scale. The background town stays ordinary red/buff brick with slate and clay tile roofs in Image 1's locations.
Hard invariants: Same full 16:9 frame as Image 1. No crop, zoom, warp, rotation or reframing. No new buildings, towers, roads, paths, ponds, canopy rows or altered heights. No moved or enlarged courtyard opening. No redesign of ancillary buildings. Seven storeys maximum and all heights remain those in Image 1.
Avoid: corporate office park, glossy masterplan, illustration, painterly surfaces, low-poly CGI, oversaturated green, fantasy architecture, extra rings, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Passes and inspection

- Passes: initial generation + one geometry correction; correction selected.
- Geometry: the broad camera and spatial hierarchy resemble the master, but the ~15 px tolerance is not met. The generated mountain ridge, fields and town grain depart substantially; the ring, courtyard opening, ancillary blocks, parking rows and local road edges also show visible drift. The correction did not materially solve the plate-registration problem.
- Realism: excellent late-summer aerial finish. The denser flower roof, PV field, avenue planting, cars and faint drainage lines read as built and photographable.
- CGI/corporate read: natural texture and weathering reduce the corporate-office-park feel. Repetition in roofs, PV rows and tree crowns, plus the highly composed cleanliness, can still read as an architectural visualisation.

## Adventurous

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, adventurous variant
Primary request: Convert Image 1 into a convincing real aerial photograph of GCHQ at Golden Valley, west Cheltenham, viewed from 340 m to the south-west. This is the adventurous version: the edge of design excellence that is still buildable and photographable, with expressive timber detail, walkable roof landscape, water and planting dominant, and energy infrastructure reading as landscape—without changing any massing or layout.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic realism, late-summer light, colour, haze, material detail, wildflower roof and human-scale reference; Image 3 is only a broad reference for how this site sits in the real west-Cheltenham landscape, never a source of replacement geometry or architecture.
Geometry lock: Preserve Image 1's exact 1280x720 whole-frame composition, camera, lens, viewpoint, horizon, terrain silhouette, road alignments, car-park extents, tree belts, every building position, footprint, roofline and height, the GCHQ ring outline and courtyard opening, and the existing town, within about 15 pixels. Do not crop, warp, zoom, rotate, reframe, move or invent any structure. The pale rectangular service building behind the ring and all foreground ancillary blocks remain exactly where they are. Keep all distant hills and existing neighbourhoods in their plate locations.
Change only these 2045 elements: (1) Make the exact annular GCHQ roof an immersive, deeply textured wildflower meadow landscape with mature grasses, pollinator drifts and seasonally varied yellow, white and purple flowering; retain the roof's exact outer and inner edges and all existing concentric path geometry. Make the paths clearly walkable, with small rest points integrated into the planting and a lively but true-scale scattering of tiny people. Keep ring height and footprint unchanged. Express the existing facade with believable exposed mass-timber mullions and soffit accents, warm brick and high-performance glass, with no added volumes, fins, bridges or towers. Keep the courtyard opening exactly fixed; make its planting layered and woodland-like while preserving its footprint. (2) Turn only the existing car-park black planes into an energetic landscape of blue-black PV canopies on elegant slim timber/steel posts, following every plate position, extent, angle and row spacing exactly; retain cars visible beneath and between. Do not add canopy rows. (3) Make mature native tree avenues and woodland-edge planting visually dominant only along existing car-park edges, without hiding road geometry. (4) Make open stormwater treatment unmistakable but precise: narrow linked silver-blue channels and rain gardens within existing planted car-park margins, reflecting the sky, never creating new roads, paths, ponds or landform. (5) Let planting, shade, water and solar energy form one coherent public landscape, visibly maintained and genuinely buildable.
Photographic standard: Match Image 2's high-end real aerial photography, late-summer afternoon sunlight, soft atmospheric haze, natural aerial depth, crisp foreground detail, believable timber, glass, brick, vegetation, cars, water and tiny people. Existing town beyond the site must remain an ordinary established English town of red and buff brick houses with slate and clay tile pitched roofs, precisely where Image 1 puts it. Rich and ambitious but naturally weathered, used and imperfect—never a render.
Lighting/mood: warm late-summer afternoon, consistent sun direction and long shadows across the whole frame, pale blue slightly hazy sky, small realistic water glints.
Color palette: layered native greens, straw and tawny meadow, controlled flower colour, warm timber and brick, charcoal metal, grey slate, clay tile, blue-black PV, silver-blue water.
Constraints: Everything must look built and photographed. Seven storeys maximum, though no height may change from Image 1. People at true scale only on existing paths and roof paths; cars only where cars park. No new blocks, towers, roads, paths, canopy rows, bridges, pavilions or altered architecture outside the permitted material expression.
Avoid: corporate office park, speculative masterplan, eco-fantasy, illustration, painterly surfaces, low-poly CGI, oversaturated green, giant people, excessive furniture, extra rings, distorted courtyard, enlarged roof opening, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction pass for the adventurous 2045 architectural aerial photomontage
Primary request: Correct Image 2 so its geometry, built fabric and framing conform literally to Image 1 while retaining an adventurous but buildable hierarchy of walkable meadow roof, expressive timber detail on the unchanged ring facade, mature native planting, exact-location PV canopies, and narrow stormwater channels.
Input images: Image 1 is the absolute pixel-layout and geometry master; Image 2 is the first adventurous photoreal pass to correct; Image 3 is the approved photographic finish; Image 4 is context-only and must not replace the plate landscape.
Correction target: Rebuild on Image 1's exact camera and silhouettes. Match Image 1's smooth horizon and hills, existing-town placement and density, woodland edge, every road and car-park curve, every black canopy-plane location, the ring outer edge and courtyard opening, and every foreground ancillary building outline within about 15 pixels. Restore the exact three low grey faceted foreground block footprints, roof shapes, heights and plain restrained facades; remove Image 2's timber recladding and added public paths from those ancillary blocks. Restore the exact pale rectangular service building behind the ring. Restore the exact ring size, placement and opening. Remove all ponds and broad streams invented in Image 2; water may appear only as a few narrow silver-blue linear rain gardens inside existing planted car-park margins. Restore canopy rows to only Image 1's black-plane positions.
Keep only these adventurous 2045 changes: immersive biodiverse late-summer wildflower meadow on the exact annular roof; the plate's exact concentric walkable paths with tiny true-scale people and very small integrated rest points; subtle exposed mass-timber mullion and soffit expression only on the unchanged ring facade, with warm brick and glass; layered woodland planting in the fixed courtyard; blue-black PV canopies on slim posts exactly matching existing black canopy planes with cars visible beneath; mature native avenues along existing parking edges; narrow reflective rain-garden channels confined to existing margins.
Photographic standard: Retain Image 2 and Image 3's high-end real aerial-photograph finish, warm late-summer afternoon light, atmospheric haze, realistic materials, vegetation, cars, water and human scale. The existing town remains ordinary English red/buff brick with slate and clay tile roofs in Image 1's exact locations. Ambitious but weathered, maintained and real.
Hard invariants: Same full 16:9 frame as Image 1. No crop, zoom, warp, rotation or reframing. No new buildings, towers, roads, pedestrian paths, ponds, bridges, pavilions, canopy rows or altered heights. No altered ancillary architecture. Seven storeys maximum and every building retains its plate height.
Avoid: corporate office park, glossy masterplan, eco-fantasy, illustration, painterly surfaces, low-poly CGI, oversized water bodies, oversaturated green, giant people, extra rings, invented skyline, text, labels, logos, watermark.
Output: one full-frame 1280x720 landscape image, same frame as Image 1.
```

### Passes and inspection

- Passes: initial generation + one geometry correction; correction selected.
- Geometry: this correction most clearly returns the foreground mass hierarchy and strips out the first pass's excessive water and ancillary timber redesign, but it still misses the ~15 px requirement. The ring/opening geometry, town pattern, hill silhouette, roads, parking and individual building profiles visibly differ from the master.
- Realism: the final has the strongest photographic roof meadow and a convincing balance of timber/glass detail, mature trees, roof users, parked cars and blue-black PV. Water is restrained to small glimpses rather than broad invented ponds.
- CGI/corporate read: generally believable at presentation scale, though the uniformly picturesque light, perfect planting condition and repeated canopy/tree rhythms retain an architectural-visualisation quality. It avoids a generic office-park character better than the other two.

## Overall geometry caveat

The built-in generative edit produced credible photoreal architectural images but did not behave as a pixel-registered renderer. Despite explicit geometry locks and one correction pass per variant, none of the three finals holds all master-plate elements within about 15 px. They should be treated as visual-design studies, not accurate photomontage overlays.
