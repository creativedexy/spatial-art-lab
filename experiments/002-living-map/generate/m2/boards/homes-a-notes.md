# Homes A — image generation notes

Built-in `image_gen` was used for every pass. The three selected corrected outputs were resized as complete frames from 1672×941 to 1280×720; there was no crop, local retouching, compositing, or post-generation geometry edit.

## Measured

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Transform Input 1 into a completely believable aerial photograph of Golden Valley, west Cheltenham, in 2045. This is the MEASURED variant: the best of current UK practice, restrained palette, calm, mature and convincingly built, never an illustration or a corporate office park.
Input images:
- Input 1 is the edit target and absolute geometry master. Preserve it exactly.
- Input 2 is the approved photographic-look reference. Match its realism, late-summer afternoon sunlight, colour, atmospheric haze and fine-grained photographic detail.
- Input 3 is site-context reference only, for how the proposal sits in the real west Cheltenham landscape; do not copy its architecture.
Scene/backdrop: homes streets looking north-east from 380 metres toward the existing town. Keep the distant existing town an ordinary English town of red and buff brick, slate and clay tile roofs, exactly where Input 1 places it.
Subject/design: steep-roofed Passivhaus terrace streets, with dark blue-black photovoltaic panels covering the south-east-facing roof pitches and natural slate on the opposite pitches; 4-6 storey mass-timber apartment blocks with modest meadow roofs; shared gardens inside the blocks; mature native street avenues; open stormwater channels and rain gardens along the streets reading as narrow silver lines; the mature orchard beside the homes. Use built precedents in the spirit of Goldsmith Street Norwich, Marmalade Lane Cambridge, Solarsiedlung Freiburg, Augustenborg Malmö, Sara Kulturhus and Powerhouse Brattørkaia, without copying a signature building.
Style/medium: high-resolution real aerial photography, physically plausible materials and construction, varied occupied homes, subtle weathering and maintenance, photographic micro-detail, no CGI sheen.
Composition/framing: preserve Input 1's exact camera, 16:9 frame, horizon, terrain, perspective and occlusion. Preserve every building position, footprint, roofline and height; every street, path, tree belt, orchard, field and existing-town block within about 15 pixels at 1280x720. One-to-one spatial registration to Input 1. Do not crop, reframe or change lens.
Lighting/mood: late-summer afternoon, natural warm sun and long soft-edged shadows, blue-grey atmospheric distance, calm inhabited neighbourhood.
Colour palette: restrained warm timber, buff and muted red brick, natural slate, dark PV, meadow greens and late-summer straw; avoid oversaturation.
Scale/life: small people at true aerial scale on streets and paths; a few people on accessible roofs only where credible; cars only in the parking locations shown or implied by Input 1, never scattered across gardens.
Constraints: seven storeys maximum. Keep the orchard mass and all tree belts. Keep fields as fields. Keep the existing town unchanged in layout and character. No invented blocks, moved blocks, extra buildings, towers, landmark objects or altered terrain. No text, labels, signage, logos or watermark.
Avoid: corporate office-park language; glossy curtain-wall slabs; generic masterplan illustration; miniature-model look; repetitive cloned trees; fantasy eco-architecture; excessive roof gardens; displaced streets; geometric drift.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for a photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Correct the MEASURED render by restoring strict pixel-level spatial registration to the geometry master. Input 1 is the actual image to edit and the absolute geometry source. Photorealistically resurface Input 1; do not redesign or reinterpret its composition. Take only photographic material/detail cues from Input 2.
Input images:
- Input 1: ABSOLUTE EDIT TARGET AND GEOMETRY MASTER. Keep its exact pixels as the spatial scaffold: same camera, lens, horizon, skyline, terrain silhouette, fields, streets, blocks, footprints, heights, roofs, tree belts, orchard bounds and existing-town pattern.
- Input 2: previous measured pass, aesthetic/material reference only. Reuse its convincing brick, timber, slate, PV, meadow roofs, mature planting and photographic finish, but copy none of its displaced geometry, widened valley, enlarged orchard or invented streets.
- Input 3: approved photographic-look reference only: match realism, late-summer afternoon sunlight, colour, haze and micro-detail.
- Input 4: site-context reference only; do not borrow its camera, landscape arrangement, building forms or architecture.
Required correction: The prior pass drifted far outside tolerance. Restore the low horizon and distant hills exactly to Input 1. Restore the large simple open field across the upper-left/centre exactly to Input 1. Restore the orchard to Input 1's precise polygon and rows. Restore every long terrace, apartment block, street and courtyard to Input 1's exact position, footprint, roofline, height and perspective. Do not add, remove, rotate, extend, subdivide or move any block. Aim for less than 15 pixels of drift at 1280x720.
Design/material treatment: restrained best-current-UK-practice. Steep-roofed Passivhaus terraces, dark PV only on the south-east-facing pitches and slate on the others; 4-6 storey mass-timber apartment blocks with modest meadow roofs; shared gardens inside the existing blocks; mature native street avenues; open stormwater channels along the existing streets as narrow silver lines; mature orchard. Warm timber and buff/muted red brick, natural slate, dark PV, late-summer meadow.
Style/medium: real aerial photograph, physically plausible construction, subtle weathering, occupied but calm, no CGI sheen.
Composition/framing: EXACTLY Input 1, 16:9, looking north-east from 380 m. No crop, reframe, lens change, new skyline or changed occlusion. Keep the existing town beyond the site exactly where and as dense as Input 1, ordinary English red/buff brick with slate/clay tile roofs.
Lighting/mood: late-summer afternoon sun, natural long soft-edged shadows, modest blue-grey haze, restrained colour.
Scale/life: people at true aerial scale on streets and paths; cars only where parking belongs.
Constraints: seven storeys maximum; no invented blocks, new roads, towers, landmarks, altered terrain or changed field boundaries. No text, labels, signage, logos or watermark.
Avoid: the previous pass's panoramic countryside substitution, extra hills, relocated town, oversized orchard, changed blocks and streets; corporate office park; illustration; miniature-model look; cloned trees; fantasy eco-architecture.
```

### Passes and inspection

- Passes: one initial generation and one geometry-correction pass; correction budget exhausted.
- Geometry: the correction restores the broad upper field, orchard adjacency, town edge and principal site structure, but it does **not** meet the requested ~15 px tolerance. The horizon/terrain profile remains different, and several terraces, courtyards, apartment blocks and streets are visibly shifted or reinterpreted.
- Realism: strong photographic light, haze, brick/slate/PV material response, mature planting and inhabited detail. It reads as a plausible aerial photograph at first glance.
- CGI/corporate risk: limited corporate character; apartment blocks are calm and residential. Some repeated roof/façade rhythms and uniformly resolved landscaping retain a polished generated/CGI quality.

## Bold

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Photorealistically resurface Input 1 as Golden Valley, west Cheltenham, in 2045. This is the BOLD variant: stronger material identity and more of every sustainable move—more photovoltaic coverage, more meadow roof, denser mature tree mass and clearly visible open water—while remaining built, inhabitable and photographable, never an illustration or corporate office park.
Input images:
- Input 1 is the ABSOLUTE EDIT TARGET AND GEOMETRY MASTER. Work directly over this composition and preserve its spatial scaffold.
- Input 2 is the approved photographic-look reference only. Match its real aerial-photograph finish, late-summer afternoon sunlight, colour, haze and level of detail; do not copy its circular architecture.
- Input 3 is site-context reference only, for the real west Cheltenham landscape character; do not borrow its camera, composition, buildings or architecture.
Scene/backdrop: the homes streets looking north-east from 380 metres toward the existing town. Keep the large open field, distant low hills and ordinary English town exactly as Input 1 positions them. Existing town remains red and buff brick, slate and clay tile roofs.
Exact geometry lock: Preserve Input 1's camera, lens, horizon, terrain silhouette, perspective, occlusion, field boundaries, streets, paths, every building position, footprint, roofline and height, every courtyard, tree belt, orchard boundary and existing-town block within about 15 pixels at 1280x720. Do not infer a different masterplan. Do not add, remove, rotate, extend, subdivide or move blocks. Maintain the exact low horizon and the exact division between field, orchard, site and town. No crop or reframe.
Subject/design: steep-roofed Passivhaus terraces with whole south-east-facing pitches of dark blue-black PV and slate on the others; 4-6 storey expressive but robust mass-timber apartment blocks on the existing footprints with fuller species-rich meadow roofs and occasional PV canopies; cohousing shared gardens inside the exact existing courtyards; substantially mature native avenues and woodland courtyards without hiding the geometry; conspicuous open stormwater channels and rain gardens along the existing streets, reading as continuous narrow silver-blue lines; the exact orchard shown in Input 1, mature and productive. Add solar carports only in parking areas already present. Built-precedent quality in the spirit of Goldsmith Street, Marmalade Lane, Solarsiedlung Freiburg, Augustenborg Malmö, Sara Kulturhus, Powerhouse Brattørkaia and Next2Sun.
Style/medium: high-resolution real aerial photography with physically plausible materials, construction joints, subtle weathering, occupied homes and convincing fine detail; no CGI sheen.
Lighting/mood: late-summer afternoon, warm natural sun, long soft-edged shadows, blue-grey atmospheric distance.
Colour/materials: stronger contrast between warm exposed timber, buff/muted red brick, dark slate and near-black PV; meadow golds, greens and wildflower flecks; silver water. Still natural, not oversaturated.
Scale/life: people at true aerial scale on streets, paths and credible accessible roofs; cars only in actual parking locations.
Constraints: seven storeys maximum. Use only the block envelopes already in Input 1. Keep fields as fields. Keep existing town layout and character. No invented blocks, new roads, towers, landmark objects or altered terrain. No text, labels, signage, logos or watermark.
Avoid: camera drift; panoramic landscape substitution; changed skyline; enlarged orchard; generic eco-masterplan rendering; corporate glass office slabs; fantasy forms; miniature-model look; cloned trees; excessive visual clutter.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the BOLD photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Restore strict spatial registration to Input 1 while keeping the bold sustainability/material character of Input 2. Input 1 is the actual edit target; photorealistically resurface it in place. Input 2 supplies appearance only, never geometry.
Input images:
- Input 1: ABSOLUTE EDIT TARGET AND GEOMETRY MASTER. Its camera, lens, low horizon, terrain silhouette, broad field, all streets and paths, every building footprint/height/roofline, exact orchard polygon and rows, tree belts and existing town are immutable.
- Input 2: previous bold pass, appearance reference only. Retain its convincing high PV coverage, species-rich meadow roofs, warm timber/brick, visible linear rain gardens, mature planting and photographic realism, but copy none of its altered panorama, field divisions, enlarged orchard, moved streets or redesigned blocks.
- Input 3: approved photographic finish only—late-summer afternoon realism, natural colour, haze and detail.
- Input 4: real site context only; do not borrow camera, composition, layout or architecture.
Geometry correction: Register the output one-to-one to Input 1, aiming for less than 15 pixels drift at 1280x720. Restore Input 1's exact horizon height and modest distant landform. Restore its single broad open upper field without the added hedgerow grid. Restore the existing town to Input 1's exact location and density. Restore the orchard to its exact bounds and row pattern. Restore each terrace, apartment block, courtyard, road and gap to the exact position, angle, footprint, extent and height shown in Input 1. No added/removed/rotated/extended/subdivided blocks. Do not change camera, crop, reframe or lens.
Bold design treatment on those exact surfaces only: whole south-east roof pitches of dark PV, slate on other terrace pitches; 4-6 storey mass-timber apartment blocks with full but plausible meadow roofs and limited PV canopies; shared gardens within existing courtyards; denser mature native avenues; conspicuous but narrow open stormwater channels and rain gardens strictly following existing streets as silver-blue lines; exact orchard mature; solar canopies only over existing parking.
Style/medium: real high-resolution aerial photograph, physically plausible built construction, subtle weathering and occupation, never CGI or illustrative.
Lighting/mood: late-summer afternoon, warm natural sun and long soft shadows, restrained haze and colours.
Scale/life: people at true aerial scale; cars only in parking.
Constraints: seven storeys maximum. No new blocks, roads, towers, landmarks, terrain changes or field-boundary changes. Existing town remains ordinary red/buff brick with slate/clay tile roofs. No text, labels, signage, logos or watermark.
Avoid: prior pass's panoramic countryside, added field hedges, shifted orchard, redesigned housing layout; office park; glossy corporate slabs; fantasy eco-forms; miniature model; excessive clutter.
```

### Passes and inspection

- Passes: one initial generation and one geometry-correction pass; correction budget exhausted.
- Geometry: broad field and town placement improve in the correction, but the result still misses the ~15 px requirement. The horizon relief is altered; the orchard shape/row pattern expands; many terrace lengths, courtyards, streets and apartment positions differ visibly from the plate.
- Realism: convincing late-summer aerial light, atmospheric recession, mature vegetation and material texture. PV, meadow roofs and silver water channels are legible without reading as pure diagram.
- CGI/corporate risk: not strongly corporate, though the repeated square apartment blocks and immaculate continuous landscape treatment can read as masterplan CGI. Water channels are more visually dominant than they would likely appear at this altitude.

## Adventurous

### Initial prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Photorealistically resurface Input 1 as Golden Valley, west Cheltenham, in 2045. This is the ADVENTUROUS variant: the edge of design excellence that is still buildable and photographable—expressive timber structure, credible walkable roofs, water and planting as the dominant moves, and renewable energy designed as landscape—without changing a single building envelope or the masterplan geometry.
Input images:
- Input 1 is the ABSOLUTE EDIT TARGET AND GEOMETRY MASTER. Work directly over its exact composition.
- Input 2 is the approved photographic-look standard only. Match its convincing real aerial-photograph finish, late-summer afternoon light, colour, haze and detail; do not copy its circular building.
- Input 3 is site-context only, for real west Cheltenham landscape character; do not borrow its camera, layout, buildings or architecture.
Scene/backdrop: homes streets looking north-east from 380 metres to the existing town. The ordinary red/buff-brick English town with slate and clay tile roofs stays exactly where Input 1 places it. Keep Input 1's open field and distant landform.
Non-negotiable geometry lock: Preserve Input 1's exact camera, lens, 16:9 frame, low horizon, terrain silhouette, perspective and occlusion. Preserve every building's position, footprint, roofline and height; every street, path, courtyard, tree belt, orchard row and boundary, field and existing-town block within about 15 pixels at 1280x720. Do not add, remove, move, rotate, extend or subdivide blocks. Do not change roads, fields, terrain, skyline or town. No crop or reframe.
Subject/design on exact existing envelopes: steep-roofed Passivhaus terraces with south-east pitches fully integrated as dark photovoltaic roofs and slate on the other pitches; 4-6 storey apartment blocks with legible, expressive but buildable mass-timber frames, deep timber reveals and meadow roofs. Where the existing flat-roof geometry permits, make roofs genuinely walkable with modest paths, railings hidden in planting and a few tiny people at true scale, without raising the mass. Link shared gardens and exact existing streets with a dominant open-blue-green stormwater system: linear channels, stepped rain gardens and small planted retention basins strictly inside existing landscape/road space, reading as silver water lines. Very mature native woodland courtyards, veteran oaks, avenues and the exact productive orchard. Energy as landscape: sculptural but buildable solar pergolas over existing parking and limited vertical bifacial PV only within suitable open landscape already shown, never new buildings or towers. Built precedent logic in the spirit of Goldsmith Street, Marmalade Lane, Solarsiedlung Freiburg, Sara Kulturhus, Powerhouse Brattørkaia, Augustenborg and Next2Sun.
Style/medium: an actual high-resolution aerial photograph of a completed, weathered-in, inhabited place; physically plausible timber connections, brick, slate, glass, PV, water and vegetation; rich but controlled micro-detail; no CGI sheen.
Lighting/mood: late-summer afternoon, warm sunlight, long natural soft-edged shadows, blue-grey atmospheric haze, thriving and calm.
Colour/materials: expressive warm timber, muted local brick, dark slate and PV, diverse meadow golds/greens/purple flecks, reflective silver-blue water. Natural photographic colour.
Scale/life: small people at true scale on streets, paths and credible walkable roofs; cars only in existing parking locations.
Constraints: seven storeys maximum. All interventions fit the exact Input 1 envelopes and landscape spaces. No new blocks, roads, bridges, towers, landmark objects, altered terrain or field boundaries. No text, labels, signage, logos or watermark.
Avoid: geometry drift; panoramic countryside substitution; changed skyline; enlarged orchard; greenwashed office campus; spectacular fantasy forms; giant rooftop parks; corporate glass slabs; masterplan illustration; miniature-model look; cloned vegetation.
```

### Correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the ADVENTUROUS photorealistic aerial planning visualisation, final 1280x720 landscape frame
Primary request: Restore strict one-to-one geometry from Input 1 while retaining only the buildable adventurous material, roof, water and planting character from Input 2. Input 1 is the image to edit. Do not redesign the site.
Input images:
- Input 1: ABSOLUTE EDIT TARGET AND GEOMETRY MASTER. Its camera, frame, lens, low horizon, simple terrain, field boundaries, streets, paths, every block footprint/height/roofline, exact orchard, tree belts and existing town are immutable.
- Input 2: previous adventurous pass, aesthetic reference only. Retain expressive buildable timber frames, dark integrated PV, walkable meadow roofs, water-rich rain gardens and mature native planting, but reject all changed geometry and all invented infrastructure.
- Input 3: approved photographic finish only—natural late-summer afternoon sun, colour, haze, detail and realism.
- Input 4: real site context only; do not copy its camera, panorama, buildings, layout or architecture.
Mandatory corrections: Align to Input 1 within about 15 pixels at 1280x720. Restore Input 1's exact low horizon and restrained distant hills. Restore its single simple upper field and exact town edge. Restore the orchard's exact polygon, rows and separation from adjacent tree belt. Restore every terrace, apartment block, street, courtyard and gap to Input 1's exact position, angle, footprint, length, roofline and height. Remove the invented left-edge ground-mounted solar array completely. Remove any new basins, paths or channels that do not sit within Input 1's existing street/landscape corridors. No crop, reframe or lens change. Do not add, remove, move, rotate, extend or subdivide any building.
Adventurous design treatment on exact existing surfaces only: dark integrated PV over the south-east terrace pitches and slate on others; 4-6 storey apartment blocks with expressive but credible mass-timber bays and deep reveals, no change to envelope; species-rich meadow roofs with subtle walkable paths only on the exact flat roofs; true-scale tiny roof users; water as continuous narrow silver-blue stormwater channels and planted rain gardens strictly along the existing streets; mature native woodland courtyards, avenues, veteran oaks and exact orchard. Solar pergolas only over parking already visible in Input 1; no ground array and no vertical solar objects unless already represented by geometry.
Style/medium: actual high-resolution aerial photography of a completed inhabited development; physically plausible timber connections, brick, slate, PV, water and plants; subtle weathering; no CGI sheen.
Lighting/mood: warm late-summer afternoon sun, long soft natural shadows, blue-grey distance, rich but photographic colour.
Scale/life: tiny people at true scale on paths and credible roofs; cars only in parking.
Constraints: seven storeys maximum; unchanged masterplan, fields, terrain, skyline and existing-town layout. No new blocks, roads, bridges, towers, landmarks, solar fields or altered boundaries. No text, labels, signage, logos or watermark.
Avoid: prior pass's solar field, shifted orchard, widened panorama, altered block layout; fantasy eco-architecture; giant roof parks; corporate office campus; illustration; miniature model; cloned trees.
```

### Passes and inspection

- Passes: one initial generation and one geometry-correction pass; correction budget exhausted.
- Geometry: the correction removes the invented left-edge solar field and restores the broad site relationships, but it still fails the ~15 px requirement. Horizon/terrain, orchard geometry, block positions, terrace lengths and streets remain substantially reinterpreted.
- Realism: good photographic lighting, plausible timber-frame expression, integrated PV, meadow roofs, rich native planting and occupied detail. The scene feels built rather than speculative illustration.
- CGI/corporate risk: lowest corporate-office-park risk of the three; timber bays and water/planting dominate. The uniformly lush landscape, repeated façade grids and visibly abundant water still give parts of the image a polished generated-visualisation character.
