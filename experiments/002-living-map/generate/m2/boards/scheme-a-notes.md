# Scheme A 2045 — image generation record

Built-in `image_gen` was used in sketch-to-render mode. Image 1 was treated as the geometry master/edit target, Image 2 as the photographic look reference, and Image 3 only as landscape-siting context. Each variant received one initial generation and one geometry-correction pass because visible drift exceeded the requested tolerance. The corrected full frames were resized from 1672×941 to 1280×720 with no crop or local retouching.

## Measured — initial prompt

```text
Use case: sketch-to-render
Asset type: 1280x720 architectural aerial-photograph board image
Primary request: Transform the geometry-master render into a completely photorealistic aerial photograph of the proposed Golden Valley, west Cheltenham, in 2045. This is the MEASURED variant: the best of current UK practice, restrained material palette, calm and credible.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic look reference; Image 3 is landscape-siting context only, never an architectural geometry source.
Scene/backdrop: The whole scheme from approximately 450 m, looking north-east to GCHQ, embedded in the real west Cheltenham landscape. Ordinary existing English town beyond the site: red and buff brick, slate and clay tile roofs. Late-summer fields, mature hedges, native woodland and distant low hills.
Subject: Every sustainability pillar legible at once: home streets, campus courtyards, orchard ring and woodland belts, open stormwater channels and ponds, solar canopies at GCHQ and its wildflower meadow roof, all sitting naturally in the real landscape. Homes use steep-roofed Passivhaus terraces like Goldsmith Street Norwich, cohousing around shared gardens like Marmalade Lane Cambridge, and whole-roof PV like Solarsiedlung Freiburg. Campus uses credible mass timber, brick and glass like Sara Kulturhus and Powerhouse Brattørkaia, with restrained PV roofs oriented to the sun and meadow roofs. Water is built open drainage and rain gardens reading as fine silver lines, like Augustenborg Malmö. Energy includes a limited, orderly amount of Next2Sun-style vertical bifacial PV over grazed pasture and solar carports. Trees are mature native mixes: veteran oaks, woodland courtyards, avenues and orchards.
Style/medium: Real aerial architectural photography, never illustration, never concept art, never a corporate office-park rendering. Match Image 2's photographic realism, fine-grained detail, natural imperfection, believable construction, atmospheric haze and exposure. Everything must look built and photographed.
Composition/framing: LOCK IMAGE 1 PIXEL GEOMETRY. Preserve exactly the 1280x720 full-frame camera, lens, viewpoint, horizon, terrain contours, field boundaries, positions, footprints, orientation and heights of every building block, all streets and paths, tree belts, orchards, fields, watercourse and existing town. Keep all major edges within about 15 pixels of Image 1. Do not crop, extend, warp, tilt, zoom or change aspect ratio. Do not use Image 2's or Image 3's camera or layout.
Lighting/mood: Late-summer afternoon sun matching Image 2, warm but natural, clear blue sky with light small clouds, subtle distance haze, realistic aerial contrast and shadows.
Color palette: Restrained buff and red brick, natural timber, dark slate and clay roof tones, meadow greens and straw-gold late-summer fields; calm, cohesive and not over-saturated.
Materials/textures: Weathered masonry, real glass reflections, expressed timber only where buildable, photovoltaic glass, mixed wildflower meadow, mown paths, wet open channels, mature varied tree canopies. The large GCHQ/campus blocks remain the exact rectilinear courtyard footprints shown in Image 1; interpret their roofs as credible meadow and PV systems without changing massing.
People/vehicles: Small people visible at true 450 m scale on streets, paths and accessible roofs; cars only where streets and parking areas in Image 1 allow them.
Constraints: Seven storeys maximum. Preserve every block; do not invent, remove, merge, move, rotate or resize blocks. No towers. Preserve the existing town exactly where the plate places it. No circular replacement building. No futuristic megastructures. No text, labels, logos, border or watermark.
Avoid: CGI sheen, low-poly vegetation, repetitive cloned trees, sterile plazas, glossy office-park architecture, exaggerated roof forms, fantasy infrastructure, oversized people or vehicles, smeared houses, floating PV, extra roads, changed skyline.
```

## Measured — correction prompt

```text
Use case: sketch-to-render
Asset type: final 1280x720 architectural aerial-photograph board image
Primary request: GEOMETRY CORRECTION PASS for the MEASURED variant. Keep Image 2's photographic realism, restrained materials, planting, meadow roofs and sustainability content, but correct its composition to match Image 1 much more literally.
Input images: Image 1 is the absolute geometry and camera master; Image 2 is the measured candidate to correct; Image 3 is the approved photographic look only.
Correction: Reproject the photoreal design onto Image 1's exact scene. Match Image 1's horizon at about y=54, its near foreground field and stream, its left field/orchard boundary, central woodland footprint, every housing row, every road, and every large rectilinear courtyard block. The principal courtyard blocks must occupy the same pixel footprints and silhouettes as Image 1, within about 15 pixels. Restore any omitted block and remove any invented massing. Keep the original master camera, viewing direction, terrain, skyline and town placement; do not substitute a wider countryside panorama.
Invariants: Do not crop, zoom, tilt, rotate, warp or alter the 16:9 frame. Keep all building heights at Image 1 heights and seven storeys maximum. Existing town stays ordinary red/buff brick with slate and clay roofs. Retain the measured variant's restrained PV, meadow roofs, native woodland, orchards, fine silver stormwater channels, true-scale people and correctly parked cars. Real late-summer afternoon aerial photography matching Image 3.
Avoid: any new blocks, towers, circular buildings, enlarged water bodies, moved roads, changed field boundaries, corporate-office-park polish, illustration, CGI sheen, text, logos or watermark.
```

## Bold — initial prompt

```text
Use case: sketch-to-render
Asset type: 1280x720 architectural aerial-photograph board image
Primary request: Transform the geometry-master render into a completely photorealistic aerial photograph of the proposed Golden Valley, west Cheltenham, in 2045. This is the BOLD variant: keep the identical master-plate layout, but give it a stronger material identity and visibly more of every sustainable move—more photovoltaic area, more wildflower meadow roof, more mature tree mass and more visible water—while remaining credible, built and calm.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic look reference; Image 3 is landscape-siting context only, never an architectural geometry source.
Scene/backdrop: The whole scheme from approximately 450 m, looking north-east to GCHQ, embedded in the real west Cheltenham landscape. Ordinary existing English town beyond the site: red and buff brick, slate and clay tile roofs. Late-summer fields, mature hedges, native woodland and distant low hills.
Subject: Every sustainability pillar legible at once: home streets, campus courtyards, orchard ring and woodland belts, open stormwater channels and ponds, solar canopies at GCHQ and its wildflower meadow roof, all sitting naturally in the real landscape. Homes use steep-roofed Passivhaus terraces like Goldsmith Street Norwich, cohousing around shared gardens like Marmalade Lane Cambridge, and extensive whole-roof PV like Solarsiedlung Freiburg. Campus uses a strong but buildable palette of mass timber, warm brick and glass like Sara Kulturhus and Powerhouse Brattørkaia, with many PV roofs oriented to the sun and generous meadow roofs. Water is built open drainage and rain gardens reading as clear silver-blue lines, like Augustenborg Malmö. Energy includes substantial orderly Next2Sun-style vertical bifacial PV over grazed pasture and broad solar carports. Trees are dense mature native mixes: veteran oaks, woodland courtyards, avenues and orchards.
Style/medium: Real aerial architectural photography, never illustration, never concept art, never a corporate office-park rendering. Match Image 2's photographic realism, fine-grained detail, natural imperfection, believable construction, atmospheric haze and exposure. Everything must look built and photographed.
Composition/framing: LOCK IMAGE 1 PIXEL GEOMETRY. Preserve exactly the 1280x720 full-frame camera, lens, viewpoint, horizon, terrain contours, field boundaries, positions, footprints, orientation and heights of every building block, all streets and paths, tree belts, orchards, fields, watercourse and existing town. Keep all major edges within about 15 pixels of Image 1. Do not crop, extend, warp, tilt, zoom or change aspect ratio. Do not use Image 2's or Image 3's camera or layout.
Lighting/mood: Late-summer afternoon sun matching Image 2, warm but natural, clear blue sky with light small clouds, subtle distance haze, realistic aerial contrast and shadows.
Color palette: Stronger contrast between warm brick, honey-coloured mass timber, dark photovoltaic glass, meadow greens and straw-gold late-summer fields; rich but photographic, never over-saturated.
Materials/textures: Weathered masonry, real glass reflections, clearly expressed timber frames where buildable, photovoltaic glass, species-rich wildflower meadow, mown walkable paths, visibly wet open channels and ponds, mature varied tree canopies. The large GCHQ/campus blocks remain the exact rectilinear courtyard footprints shown in Image 1; interpret their roofs as meadow, walkable roof paths and PV without changing massing.
People/vehicles: Small people visible at true 450 m scale on streets, paths and accessible roofs; cars only where streets and parking areas in Image 1 allow them.
Constraints: Seven storeys maximum. Preserve every block; do not invent, remove, merge, move, rotate or resize blocks. No towers. Preserve the existing town exactly where the plate places it. No circular replacement building. No futuristic megastructures. No text, labels, logos, border or watermark.
Avoid: CGI sheen, low-poly vegetation, repetitive cloned trees, sterile plazas, glossy office-park architecture, exaggerated roof forms, fantasy infrastructure, oversized people or vehicles, smeared houses, floating PV, extra roads, changed skyline.
```

## Bold — correction prompt

```text
Use case: sketch-to-render
Asset type: final 1280x720 architectural aerial-photograph board image
Primary request: GEOMETRY CORRECTION PASS for the BOLD variant. Keep Image 2's stronger material identity, extensive PV, meadow roofs, mature tree mass and visible water, but correct its composition to match Image 1 much more literally.
Input images: Image 1 is the absolute geometry and camera master; Image 2 is the bold candidate to correct; Image 3 is the approved photographic look only.
Correction: Reproject the photoreal design onto Image 1's exact scene. Match Image 1's horizon at about y=54, near foreground field and narrow stream, left field/orchard boundary, central woodland footprint, every housing row, every road, and every large rectilinear courtyard block. The principal courtyard blocks must occupy the same pixel footprints and silhouettes as Image 1, within about 15 pixels. Restore any omitted block and remove any invented massing. Keep the original master camera, viewing direction, terrain, skyline and town placement; do not substitute a wider countryside panorama.
Invariants: Do not crop, zoom, tilt, rotate, warp or alter the 16:9 frame. Keep all building heights at Image 1 heights and seven storeys maximum. Existing town stays ordinary red/buff brick with slate and clay roofs. Retain the bold variant's substantial orderly vertical bifacial PV in the exact left field, broad solar canopies only in existing parking areas, generous meadow roofs, native woodland and orchard density, clearly visible but narrow stormwater channels and ponds, true-scale people and correctly parked cars. Real late-summer afternoon aerial photography matching Image 3.
Avoid: any new blocks, towers, circular buildings, enlarged or relocated water bodies, moved roads, changed field boundaries, corporate-office-park polish, illustration, CGI sheen, text, logos or watermark.
```

## Adventurous — initial prompt

```text
Use case: sketch-to-render
Asset type: 1280x720 architectural aerial-photograph board image
Primary request: Transform the geometry-master render into a completely photorealistic aerial photograph of the proposed Golden Valley, west Cheltenham, in 2045. This is the ADVENTUROUS variant: the edge of design excellence that is still buildable and photographable, with expressive timber structure, walkable roofs, water and planting as the dominant moves, and renewable energy designed as landscape—while preserving the identical master-plate massing and layout.
Input images: Image 1 is the absolute geometry master and edit target; Image 2 is the approved photographic look reference; Image 3 is landscape-siting context only, never an architectural geometry source.
Scene/backdrop: The whole scheme from approximately 450 m, looking north-east to GCHQ, embedded in the real west Cheltenham landscape. Ordinary existing English town beyond the site: red and buff brick, slate and clay tile roofs. Late-summer fields, mature hedges, native woodland and distant low hills.
Subject: Every sustainability pillar legible at once: home streets, campus courtyards, orchard ring and woodland belts, open stormwater channels and ponds, solar canopies at GCHQ and its wildflower meadow roof, all sitting naturally in the real landscape. Homes use steep-roofed Passivhaus terraces like Goldsmith Street Norwich, cohousing around shared gardens like Marmalade Lane Cambridge, and whole-roof PV like Solarsiedlung Freiburg. Campus uses expressive but plausible exposed mass-timber structural rhythms, deep glazed winter gardens and warm brick like Sara Kulturhus and Powerhouse Brattørkaia. Roofs combine species-rich meadow, extensive walkable paths and PV planes precisely tilted to the sun; selected meadow roofs visually descend toward the ground through planted terraces and ramps without altering the master building envelopes. Water and wetland planting dominate public space: connected open channels, rain gardens and ponds read clearly as silver-blue lines like Augustenborg Malmö. Energy is landscape: extensive orderly Next2Sun-style vertical bifacial PV over grazed pasture and large elegant solar carports. Trees form powerful mature native ecologies: veteran oaks, dense woodland courtyards, avenues and orchards.
Style/medium: Real aerial architectural photography, never illustration, never concept art, never a corporate office-park rendering. Match Image 2's photographic realism, fine-grained detail, natural imperfection, believable construction, atmospheric haze and exposure. Everything must look built and photographed.
Composition/framing: LOCK IMAGE 1 PIXEL GEOMETRY. Preserve exactly the 1280x720 full-frame camera, lens, viewpoint, horizon, terrain contours, field boundaries, positions, footprints, orientation and heights of every building block, all streets and paths, tree belts, orchards, fields, watercourse and existing town. Keep all major edges within about 15 pixels of Image 1. Do not crop, extend, warp, tilt, zoom or change aspect ratio. Do not use Image 2's or Image 3's camera or layout.
Lighting/mood: Late-summer afternoon sun matching Image 2, warm but natural, clear blue sky with light small clouds, subtle distance haze, realistic aerial contrast and shadows.
Color palette: Expressive natural timber, warm red and buff brick, dark blue-black photovoltaic glass, richly varied meadow greens and wildflower golds against straw-coloured fields; vivid ecology but true photographic colour.
Materials/textures: Deep mass-timber frames, weathered masonry, real glass reflections, photovoltaic glass, thick mixed wildflower meadow, timber-and-gravel roof walks with tiny true-scale people, wet channels, reed beds and ponds, richly varied mature tree canopies. The large GCHQ/campus blocks remain the exact rectilinear courtyard footprints shown in Image 1; meadow-to-ground gestures are planted access ramps or terraces contained within those footprints, never new massing.
People/vehicles: Small people visible at true 450 m scale on streets, paths and accessible roofs; cars only where streets and parking areas in Image 1 allow them.
Constraints: Seven storeys maximum. Preserve every block; do not invent, remove, merge, move, rotate or resize blocks. No towers. Preserve the existing town exactly where the plate places it. No circular replacement building. No futuristic megastructures. No text, labels, logos, border or watermark.
Avoid: CGI sheen, low-poly vegetation, repetitive cloned trees, sterile plazas, glossy office-park architecture, exaggerated or unbuildable roof forms, fantasy infrastructure, giant bridges, oversized people or vehicles, smeared houses, floating PV, extra roads, changed skyline.
```

## Adventurous — correction prompt

```text
Use case: sketch-to-render
Asset type: final 1280x720 architectural aerial-photograph board image
Primary request: GEOMETRY CORRECTION PASS for the ADVENTUROUS variant. Keep Image 2's expressive but buildable timber architecture, walkable meadow roofs, dominant water and planting, and energy-as-landscape character, but correct its composition to match Image 1 much more literally.
Input images: Image 1 is the absolute geometry and camera master; Image 2 is the adventurous candidate to correct; Image 3 is the approved photographic look only.
Correction: Reproject the photoreal design onto Image 1's exact scene. Match Image 1's horizon at about y=54, near foreground field and narrow stream, left field/orchard boundary, central woodland footprint, every housing row, every road, and every large rectilinear courtyard block. The principal courtyard blocks must occupy the same pixel footprints and silhouettes as Image 1, within about 15 pixels. Restore any omitted block and remove any invented massing. Keep the original master camera, viewing direction, terrain, skyline and town placement; do not substitute a wider countryside panorama.
Invariants: Do not crop, zoom, tilt, rotate, warp or alter the 16:9 frame. Keep all building heights at Image 1 heights and seven storeys maximum. Existing town stays ordinary red/buff brick with slate and clay roofs. Retain expressive credible mass-timber rhythms, walkable meadow roofs and contained planted ramps, extensive orderly vertical bifacial PV in the exact left field, solar canopies only on existing parking, connected but narrow stormwater channels and ponds, dense native woodland and orchards, true-scale people and correctly parked cars. Real late-summer afternoon aerial photography matching Image 3.
Avoid: any new blocks, towers, circular buildings, megastructures, enlarged or relocated water bodies, moved roads, changed field boundaries, impossible roof landforms, corporate-office-park polish, illustration, CGI sheen, text, logos or watermark.
```

## Passes and honest inspection

### Measured

- Passes: one initial generation, then one permitted geometry-correction pass. Final: `scheme-a-measured.png`.
- Geometry: the correction restores the low master horizon, overall left-to-right development sequence, foreground stream, central woodland and three main courtyard blocks. It is not within 15 px everywhere: the distant town/terrain is regenerated, the left housing quarter is more regular and slightly re-spaced, woodland edges and pond positions are inferred, and some secondary block footprints differ. The foreground stream is wider and more sinuous than the plate.
- Realism: convincing aerial-photo light, haze, masonry, mature tree canopies and meadow roofs. Roads, cars and small people generally read at scale.
- CGI/corporate risk: repeated window bays and uniformly pristine courtyard blocks still have a mild architectural-visualisation quality; the large blocks can read more institutional than the desired non-corporate character.

### Bold

- Passes: one initial generation, then one permitted geometry-correction pass. Final: `scheme-a-bold.png`.
- Geometry: the principal massing hierarchy, master horizon, central woodland, left field and foreground stream are retained, but visible drift remains beyond 15 px in the distant town, left housing rows, road alignments, orchard/woodland boundaries and some courtyard dimensions. PV arrays occupy the intended left-side field but their exact rows were invented from the sustainability brief rather than present in the geometry plate.
- Realism: strong photographic texture, late-summer colour and credible roof/PV construction. Water, meadow roof and tree mass read immediately, with believable scale and sunlight.
- CGI/corporate risk: the campus façades are repetitive and unusually consistent; crisp PV repetition and spotless blocks give parts of the image a masterplan-render polish despite otherwise convincing landscape photography.

### Adventurous

- Passes: one initial generation, then one permitted geometry-correction pass. Final: `scheme-a-adventurous.png`.
- Geometry: overall camera and site ordering are close to the other corrected variants, but this is the loosest interpretation. The distant town, many home rows, internal paths, water bodies and woodland clearings are regenerated and exceed the 15 px tolerance. Main courtyard blocks remain rectilinear and tower-free, but some dimensions and separations differ from the master. The stream and linked ponds are substantially more prominent than in the plate.
- Realism: the best landscape/ecology read of the set; timber-grid façades, meadow/PV roofs, wetland planting and tiny people are plausibly photographed, with natural haze and shadow.
- CGI/corporate risk: highly coordinated roof treatments, repeated façade grids and immaculate solar rows reveal generated/masterplan logic. The intended walkable-roof and meadow-to-ground ideas are only partly legible at this altitude.

## Overall caveat

The images meet the requested photographic character, variant progression, 1280×720 delivery size, tower/text/logo exclusions and broad master-plate composition. The built-in generative edit did not achieve literal ±15 px registration across every block, road and landscape edge; even after the single allowed correction per variant, localized geometry drift remains and is most noticeable in the distant town, fine-grain housing, water and vegetation boundaries.
