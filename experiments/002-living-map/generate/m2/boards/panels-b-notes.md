# Panels B — generation notes

Built-in `image_gen` was used in sketch-to-render mode. Image 1 was the geometry master, Image 2 the photographic-look reference, and Image 3 the landscape-integration reference. Each final file is the corrected pass, resized as a whole frame from the generated 16:9 output to 1280×720 with no crop, warp, or local retouching.

## panels-b-measured.png

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, final board image
Primary request: Transform Image 1 into a fully built, genuinely photographic aerial view of Golden Valley, west Cheltenham, in 2045. This is the MEASURED variant: the best of current UK practice, calm and restrained. In the large central fields, retain the exact long straight row geometry from Image 1 as vertical bifacial photovoltaic fences over grazed pasture, with small sheep visibly grazing between rows at true scale. Retain the campus glasshouses and show them as working horticultural glasshouses using campus waste heat. Make the orchard and woodland belts mature native mixes with veteran oaks. Render the foreground exactly where shown as steep-roofed Passivhaus terraces around shared gardens plus the existing taller timber blocks, using restrained buff and red brick, warm timber, slate/charcoal roofs, modest whole-roof PV, and selective meadow roofs. Integrate narrow open stormwater channels and rain gardens as subtle silver lines. Keep the existing round water-treatment tanks at right exactly in place.
Input images: Image 1 is the geometry master and edit target; Image 2 is the approved photographic look reference only; Image 3 is a landscape-integration reference only, never an architecture or camera reference.
Scene/backdrop: Golden Valley landscape looking south-south-west from 380 m; late-summer English countryside and ordinary existing Cheltenham town beyond.
Style/medium: indistinguishable from a real high-resolution aerial photograph; match Image 2's realism, natural detail, atmospheric haze, late-summer afternoon sun and colour response. Everything must look built, weathered, occupied and photographed, never a render or illustration.
Composition/framing: ABSOLUTE GEOMETRY LOCK TO IMAGE 1. Preserve the exact 1280×720 frame, camera, projection, horizon, terrain contours, field boundaries, roads, paths, tree belts, orchards, water bodies, and the position, footprint, roofline and height of every single building block within approximately 15 pixels. Do not crop, extend, warp, shift the camera, or change the skyline. Preserve the low-rise foreground composition and distant settlement exactly.
Lighting/mood: warm clear late-summer afternoon with believable long shadows, mild aerial haze and natural photographic dynamic range.
Materials/textures: real red and buff English brick, slate and clay tiles, weathered timber, clear glass, dark blue-black PV glass, meadow grasses and wildflowers.
Constraints: no building over seven storeys; no invented buildings; no moved, enlarged, deleted or merged blocks; no towers; no landmark objects. The town beyond the site remains an ordinary existing English town exactly where Image 1 places it, with red/buff brick and slate/clay roofs. People visible at true scale on streets, paths and accessible roofs; cars only where cars plausibly park. Preserve the round tanks at right. The sustainability measures must read as normal constructed infrastructure, not spectacle.
Avoid: corporate office park, glossy masterplan CGI, illustration, fantasy eco-city, excessive glass boxes, monumental architecture, duplicated buildings, distorted roads, floating trees, oversized people or sheep, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction of the measured 2045 aerial photomontage
Primary request: Correct Image 1 only for geometric registration to Image 2 while preserving Image 1's excellent photographic realism, materials, vertical bifacial PV pasture, sheep, glasshouses, mature planting, lighting and calm measured design. Reconstruct the composition so every visible element follows Image 2: restore the exact low smooth horizon and its height; restore every field boundary, woodland edge, orchard edge, pond, road and path; restore the exact position, footprint, orientation, roof ridge, separation and height of every foreground and distant building. In particular, the foreground terraces and taller blocks must occupy the same silhouettes as Image 2, with no invented or merged houses. Keep Image 1's design language only as surface and landscape treatment placed inside those master silhouettes.
Input images: Image 1 is the generated measured photoreal image to correct; Image 2 is the absolute geometry master; Image 3 is photographic finish reference.
Style/medium: real aerial photography, not CGI.
Composition/framing: PIXEL-STRICT REGISTRATION TO IMAGE 2. Same 1280×720 whole frame, same camera, lens, projection, horizon, terrain and layout within approximately 15 pixels. Do not crop, extend, warp or recompose.
Constraints: preserve the geometry master's exact town, all building blocks, vertical-PV-row locations, glasshouse locations, tree belts, orchards, fields and existing round water-treatment tanks at right. No new blocks, deleted blocks, towers or buildings over seven storeys. Ordinary existing English town beyond. People and cars at true scale. No text, labels, logos or watermark.
Avoid: any further geometry reinterpretation, scenic mountain enlargement, changed skyline, corporate office park, illustration, glossy CGI.
```

### Passes and inspection

- Passes: one initial generation plus one geometry-correction pass.
- Geometry: the corrected image retains the overall camera direction, central two-field PV composition, foreground residential band, left orchard/woodland and right wetland/water-treatment zone. It does **not** meet a literal 15 px match: the distant ridge is higher and more detailed; the foreground terraces and taller blocks are reinterpreted and shifted; several field, pond and woodland edges drift; the water-treatment tanks are not clearly retained.
- Realism: strong aerial-photography finish, convincing afternoon light, sheep scale, PV pasture, glasshouses, mature planting and material weathering.
- CGI/corporate risk: low overall; repeated roof/façade rhythms and exceptionally tidy landscape read slightly generated. It reads residential/ecological rather than corporate.

## panels-b-bold.png

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, final board image
Primary request: Transform Image 1 into a fully built, genuinely photographic aerial view of Golden Valley, west Cheltenham, in 2045. This is the BOLD variant: a stronger material identity and visibly more of every sustainable move, without changing any massing. In the large central fields, retain the exact long straight row geometry from Image 1 as dense vertical bifacial photovoltaic fences over grazed pasture, with sheep visibly grazing between rows at true scale. Retain the campus glasshouses and show them as extensive working horticultural glasshouses using campus waste heat. Intensify the orchard and woodland belts into mature native mixes with veteran oaks and woodland courtyards. Render the foreground exactly where shown as steep-roofed Passivhaus terraces around shared gardens plus the existing taller timber blocks: confident red/buff masonry and exposed mass timber, whole-roof PV on most suitable pitches, generous meadow roofs on flat roofs, solar carports only over existing parking. Make open stormwater channels, swales and rain gardens clearly visible as connected silver-blue lines, while staying within the plate's paths and open-space geometry. Keep the existing round water-treatment tanks at right exactly in place.
Input images: Image 1 is the geometry master and edit target; Image 2 is the approved photographic look reference only; Image 3 is a landscape-integration reference only, never an architecture or camera reference.
Scene/backdrop: Golden Valley landscape looking south-south-west from 380 m; late-summer English countryside and ordinary existing Cheltenham town beyond.
Style/medium: indistinguishable from a real high-resolution aerial photograph; match Image 2's realism, natural detail, atmospheric haze, late-summer afternoon sun and colour response. Everything must look built, weathered, occupied and photographed, never a render or illustration.
Composition/framing: ABSOLUTE GEOMETRY LOCK TO IMAGE 1. Preserve the exact 1280×720 frame, camera, projection, horizon, terrain contours, field boundaries, roads, paths, tree belts, orchards, water bodies, and the position, footprint, roofline and height of every single building block within approximately 15 pixels. Do not crop, extend, warp, shift the camera, or change the skyline. Preserve the low-rise foreground composition and distant settlement exactly.
Lighting/mood: warm clear late-summer afternoon with believable long shadows, mild aerial haze and natural photographic dynamic range.
Materials/textures: red and buff English brick, expressed weathered mass timber, slate and clay tiles, clear horticultural glass, dark blue-black PV glass, species-rich meadow roofs, grasses and wildflowers.
Constraints: no building over seven storeys; no invented buildings; no moved, enlarged, deleted or merged blocks; no towers; no landmark objects. The town beyond the site remains an ordinary existing English town exactly where Image 1 places it. People visible at true scale on streets, paths and accessible roofs; cars only where cars plausibly park. Preserve the round tanks at right. Every element must have a credible built precedent.
Avoid: corporate office park, glossy masterplan CGI, illustration, fantasy eco-city, excessive generic glass boxes, monumental architecture, duplicated buildings, distorted roads, floating trees, oversized people or sheep, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction of the bold 2045 aerial photomontage
Primary request: Correct Image 1 only for geometric registration to Image 2 while preserving Image 1's strong photographic realism and bold built character: dense vertical bifacial PV pasture with sheep, extensive waste-heat glasshouses, strong red/buff masonry and timber identity, whole-roof PV, meadow roofs, mature orchards and woodland, visible stormwater channels and rain gardens. Do not reduce those bold sustainability measures; place them strictly inside Image 2's layout.
Input images: Image 1 is the generated bold photoreal image to correct; Image 2 is the absolute geometry master; Image 3 is photographic finish reference.
Style/medium: real late-summer aerial photography, not CGI.
Composition/framing: PIXEL-STRICT REGISTRATION TO IMAGE 2. Restore Image 2's exact 1280×720 frame, camera, projection, low horizon profile and height, terrain, field boundaries, woodland edges, orchard edges, roads, paths, ponds, and every building's position, footprint, orientation, separation, roofline and height within approximately 15 pixels. Restore the right-side water-treatment works exactly as Image 2, including its round tanks. Restore all foreground terraces and taller blocks to the master silhouettes without inventing, enlarging, merging or deleting any.
Constraints: same massing and skyline as Image 2; no block above seven storeys; no towers; ordinary existing English town beyond exactly where shown; true-scale people, sheep and cars; no text, labels, logos or watermark.
Avoid: changed ridge line, repositioned tanks, reinterpreted foreground courtyards, corporate office park, illustration, glossy CGI.
```

### Passes and inspection

- Passes: one initial generation plus one geometry-correction pass.
- Geometry: the broad zoning and view direction remain recognisable, and the correction restores two tanks at the right. The literal 15 px tolerance is still exceeded: the horizon/ridge, central field extents and PV-row count/spacing differ; foreground blocks are re-laid into more regular courtyards; paths, woodland edges, ponds and distant glasshouses shift.
- Realism: highly convincing photographic vegetation, pasture, water, glasshouses, roofs, parked cars and tiny people. Vertical PV and sheep read clearly.
- CGI/corporate risk: some uniform façades, perfect PV arrays and manicured planting have a polished masterplan feel, but timber/brick housing, water and mature ecology prevent a generic office-park reading.

## panels-b-adventurous.png

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: 2045 architectural aerial photomontage, final board image
Primary request: Transform Image 1 into a fully built, genuinely photographic aerial view of Golden Valley, west Cheltenham, in 2045. This is the ADVENTUROUS variant: the edge of design excellence that remains buildable, maintainable and photographable, with no massing changes. In the large central fields, retain the exact long straight row geometry from Image 1 as an energy landscape of vertical bifacial photovoltaic fences over biodiverse grazed pasture, sheep between the rows at true scale. Retain the campus glasshouses and show them as productive horticultural glasshouses running on campus waste heat. Make water and planting the dominant spatial moves: a legible network of open silver stormwater channels, pools and rain gardens following the plate's existing open-space lines; dense mature native woodland courtyards, veteran oaks, avenues and orchards. Render the foreground blocks exactly where shown with expressive but credible exposed mass-timber structure and warm masonry: steep-roofed Passivhaus terraces around shared gardens, existing taller timber blocks, whole-roof PV sawn to the sun, solar canopies only over existing parking, species-rich meadow roofs and carefully designed walkable roof paths where roofs are already flat or gently sloping. Let meadow roofs visually run down to ground only where the geometry already provides a low planted slope; do not invent new building forms.
Input images: Image 1 is the geometry master and edit target; Image 2 is the approved photographic look reference only; Image 3 is a landscape-integration reference only, never an architecture or camera reference.
Scene/backdrop: Golden Valley landscape looking south-south-west from 380 m; late-summer English countryside and ordinary existing Cheltenham town beyond.
Style/medium: indistinguishable from a real high-resolution aerial photograph; match Image 2's realism, natural detail, atmospheric haze, late-summer afternoon sun and colour response. Everything must look built, weathered, occupied and photographed, never a render, diagram or illustration.
Composition/framing: ABSOLUTE GEOMETRY LOCK TO IMAGE 1. Preserve the exact 1280×720 frame, camera, projection, horizon, terrain contours, field boundaries, roads, paths, tree belts, orchards, water bodies, and the position, footprint, roofline and height of every single building block within approximately 15 pixels. Do not crop, extend, warp, shift the camera, or change the skyline. Preserve the low-rise foreground composition and distant settlement exactly.
Lighting/mood: warm clear late-summer afternoon with believable long shadows, mild aerial haze, natural photographic dynamic range; lush but not utopian.
Materials/textures: expressive weathered glulam and mass timber, real red/buff English brick, slate and clay tiles, clear horticultural glass, dark PV glass, weathered steel water edges, species-rich meadow and wetland planting.
Constraints: maximum seven storeys; no invented buildings; no moved, enlarged, deleted or merged blocks; no towers; no landmark objects. The town beyond the site remains an ordinary existing English town exactly where Image 1 places it. People visible at true scale on streets, paths and walkable roofs; cars where cars actually park. Keep the existing round water-treatment tanks at right exactly in place. Every move must have a plausible built precedent.
Avoid: fantasy eco-city, corporate office park, glossy masterplan CGI, illustration, impossible bridges or cantilevers, excessive generic glass, monumental architecture, duplicated buildings, distorted roads, floating vegetation, oversized people or sheep, text, labels, logos, watermark.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry correction of the adventurous 2045 aerial photomontage
Primary request: Correct Image 1 only for geometric registration to Image 2 while preserving Image 1's genuinely photographic finish and adventurous but buildable design: expressive timber, warm masonry, whole-roof PV, meadow roofs and walkable roof paths only on suitable existing roofs, vertical bifacial PV pasture with sheep, productive waste-heat glasshouses, mature woodland and orchards, and water/planting as dominant connected landscape infrastructure. Place all those treatments strictly inside Image 2's unchanged geometry.
Input images: Image 1 is the generated adventurous photoreal image to correct; Image 2 is the absolute geometry master; Image 3 is photographic finish reference.
Style/medium: real late-summer aerial photography, built and occupied, not CGI.
Composition/framing: PIXEL-STRICT REGISTRATION TO IMAGE 2. Restore Image 2's exact 1280×720 frame, camera, projection, low smooth horizon profile and height, terrain contours, field boundaries, woodland and orchard edges, roads, paths, ponds, and every building's position, footprint, orientation, separation, roofline and height within approximately 15 pixels. Restore every foreground terrace and taller block to its master silhouette. Restore the water-treatment works and all round tanks at right exactly where Image 2 places them.
Constraints: same massing and skyline as Image 2; maximum seven storeys; no new, enlarged, merged, moved or deleted blocks; no towers; ordinary existing English town beyond exactly where shown; true-scale people, sheep and cars; no text, labels, logos or watermark. Keep every intervention credible and buildable.
Avoid: altered horizon, reinterpreted courtyards, shifted tanks, fantasy eco-city, corporate office park, illustration, glossy CGI, impossible structures.
```

### Passes and inspection

- Passes: one initial generation plus one geometry-correction pass.
- Geometry: the two PV fields, left orchard/woodland, right wetland and treatment works, and foreground housing band retain the intended ordering, with tanks visible at right. The result still exceeds the 15 px requirement: horizon relief is substantially re-authored; central PV rows, ponds and field limits shift; foreground buildings are regularised and moved; distant town/campus geometry is reconstructed rather than preserved.
- Realism: excellent late-summer aerial-photography qualities, credible sheep/PV scale, convincing wetlands, mature tree canopy, glasshouses and inhabited foreground. The energy landscape is the clearest of the three.
- CGI/corporate risk: low corporate character. Some repeated terrace modules, immaculate PV roofs and unusually resolved vegetation read as generated; the requested expressive timber and walkable-roof character is understated at this camera distance.

## Overall limitation

The built-in generative edit produced strong photoreal imagery but did not reliably preserve the geometry master to the requested ~15 px tolerance, even after the single permitted correction pass for each variant. The files are therefore suitable as design-ambition/atmosphere studies, not as registered photomontages or geometry-faithful evidence.
