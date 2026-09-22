# Campus courtyards photograph — generation notes

## Method

- Tool: built-in `image_gen`
- Mode: `sketch-to-render`
- Passes used: 1 generation, 0 correction passes
- Generated source: 1672 × 941 PNG (16:9)
- Delivery: whole-frame resample to 1280 × 720; no crop, extension, or reframing

## User prompt (verbatim)

```text
Use the built-in image_gen tool, sketch-to-render, to REMAKE an approved place photograph so it agrees with the 3D model as it now stands.

INPUT 1 is the geometry master: a render of our own current 3D model from exactly the camera this photograph is taken at. Every building, street, tree belt, orchard row, solar row, canopy and field boundary must keep its position, footprint and height, within about 15 px at 1280x720. The model has changed a great deal since the old photograph: about 1,100 homes as terraces and timber blocks (was 70), campus courtyard blocks, vertical bifacial solar rows over pasture, solar canopies over GCHQ's car parks, mature orchards and woodland belts, open stormwater channels. Follow the plate, never the old photograph, for what is where.
INPUT 2 is the OLD approved photograph at this camera: use it ONLY for photographic look, light, colour, haze and level of detail. Its layout is out of date.
INPUT 3 is the approved adventurous target board for this part of the site: use it for materials and character (buff brick and honey timber, PV glass, meadow roofs, planting).

Design direction: design excellence and realism, built precedents only (Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattorkaia, Augustenborg, Next2Sun), never corporate office park, never illustration, no text or watermark, people and vehicles at true scale. Late summer afternoon, the same sun as INPUT 2.

Output 1280x720 (whole-frame resize only, no crop or warp) to experiments/002-living-map/generate/m7/out/campus-courtyards-photo.png. One generation plus at most one correction pass if geometry drifts. Write experiments/002-living-map/generate/m7/out/campus-courtyards-notes.md with the prompts verbatim, passes, and an honest inspection (drift you can see, anything that reads as CGI).

THIS PLACE: The courtyards (2045). Camera [-380, 225.664, 60] looking at [-190, 47.341, -200].
What the place copy says, so the photograph must show it: Straight down onto the campus. The blocks make perimeter courtyards rather than sitting in car parks, and the ground between them is designed: sett plazas cut through wildflower, retained oaks, seating at the glazed ground floors. The brook corridor on the left is let out of its culvert into 15.5 hectares of wet meadow. Every building you can see was placed by the same rule — campus within reach of GCHQ and a road — and none of them by hand.
```

## Pass 1 prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: approved place photograph, 1280×720 landscape master
Primary request: REMAKE the approved place photograph as a highly realistic aerial architectural photograph of “The courtyards (2045),” while matching the current 3D model geometry exactly.
Input images:
- Image 1 is the absolute geometry master and camera master. Preserve the entire frame, viewpoint, perspective, horizon, and every visible building, street, path, tree belt, orchard row, solar row, canopy, field boundary, open space, and landform in its exact position, footprint, orientation, and height, within about 15 pixels at 1280×720. Follow Image 1 for all spatial content. Do not import or retain any layout from Image 2 or Image 3.
- Image 2 is an OLD approved photograph. Use it ONLY for photographic realism, late-summer afternoon sunlight, colour, haze, atmospheric depth, natural texture, and level of detail. Its spatial layout is obsolete and must not influence geometry.
- Image 3 is the approved adventurous target board. Use it ONLY for materials and architectural character: buff brick, honey-coloured timber, clear PV glass, biodiverse meadow roofs, rich planting, glazed active ground floors.
Scene/backdrop: The current 2045 campus and surrounding district exactly as Image 1. The dominant foreground and middle-ground campus buildings are perimeter courtyard blocks rather than freestanding office slabs in car parks. Designed ground between them includes sett plazas cutting through wildflower planting, retained mature oaks, and small-scale seating beside glazed ground floors. On the left, the brook is open rather than culverted and occupies a broad 15.5-hectare wet-meadow corridor. Keep the extensive terraces and timber housing blocks, orchards, woodland belts, vertical bifacial solar rows over pasture, solar canopies over GCHQ car parks, roads and existing suburban fabric wherever Image 1 places them.
Subject: Straight down onto the campus from camera [-380, 225.664, 60] looking at [-190, 47.341, -200]. Every visible building follows the same siting logic: campus within reach of GCHQ and a road.
Style/medium: convincingly real, high-resolution professional aerial place photography; built-precedent credibility inspired by Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattorkaia, Augustenborg, and Next2Sun. Natural construction detail and mild real-world imperfection. Never an illustration and never a glossy corporate-office-park visualisation.
Composition/framing: exact full-frame composition of Image 1; no crop, no warp, no reframing, no camera move. Maintain all massing silhouettes and occlusion relationships.
Lighting/mood: late-summer afternoon, exactly the sun direction and warm natural light character of Image 2, with believable shadows, haze and aerial atmospheric perspective.
Color palette: warm buff masonry, honey timber, muted meadow greens, dark blue-grey PV glass, natural asphalt and stone; restrained photographic saturation.
Materials/textures: buff brick and honey timber façades with plausible bays and windows; meadow roofs and PV where indicated; realistic wet grass, reeds, orchard crowns, retained oaks, hedgerows, water, sett paving and glazing.
Text: none.
Constraints: Geometry is more important than beautification. Retain Image 1’s count and exact arrangement of courtyard blocks, housing, streets, vegetation belts, orchards, solar infrastructure and field edges. People and vehicles only at true aerial scale. Preserve every feature visible in Image 1 even if Image 2 differs. Whole frame must remain landscape 16:9 for a final 1280×720 resize.
Avoid: any layout from Image 2 or Image 3; invented buildings; missing buildings; moved roads; altered courtyards; changed rooflines; enlarged trees that hide geometry; office-campus lawns or surface car parks replacing designed public realm; generic corporate office park; toy-town look; isometric illustration; video-game render; excessive HDR; oversaturated foliage; fake repeated windows; malformed cars or people; labels, signs, logos, text, borders or watermark.
```

## Passes and selection

Pass 1 was selected as final. A correction pass was not used because the three primary campus blocks, their courtyards, the gaps between them, the adjacent north–south road, the right-side housing and the broad left-side orchard/woodland bands all remained strongly registered to the geometry plate. Another generative edit was judged more likely to move those large, successful envelopes than to improve the smaller discrepancies.

## Honest visual inspection

### Geometry and content

- The three principal campus blocks retain the plate's staggered alignment, approximate footprints, heights and courtyard voids. The middle block's internal diagonal landscape/paving gesture is preserved, although it is more detailed and slightly softened.
- The foreground block, central block and rear block remain in their intended order and sit against the correct right-hand road corridor. Their façades and planted/PV roofs are interpretive photographic detail rather than literal model texture.
- The main right-side suburban roads, curved solar-canopy car park and background housing remain in the correct broad locations. At small scale, individual distant houses and road junctions are regularised and cannot be claimed within a strict 15 px feature-by-feature tolerance.
- The left-side woodland/orchard bands follow the plate's broad boundaries. Individual orchard crowns and rows have been naturalised, so exact tree-by-tree registration drifts.
- The lower-left open brook and wet-meadow channels are more visibly articulated than in the geometry plate. This supports the place copy, but the precise meanders, pools and reed edges are generative additions and visibly drift from the simplified source geometry.
- The far-left linear solar rows are retained in the correct zone, but their count, spacing and panel morphology are simplified. Some other small PV arrays appear on roofs or near orchard edges as material interpretation rather than exact plate objects.
- Some distant terrace/timber-block groups merge into more generic repeated housing as atmospheric detail increases toward the horizon.

### Photographic realism / residual CGI tells

- The overall aerial light, haze, vegetation variation and material response read as a plausible late-summer photograph.
- Repetition in façade bays, roof PV modules, orchard trees and distant houses still carries a mild procedural/CGI signature.
- A few tiny cars and pedestrians are only impressionistic at this scale; close inspection may reveal soft or inconsistent shapes.
- Courtyard meadow texture is lush and coherent but slightly too evenly distributed, and some roof planting/PV junctions are cleaner than real construction.
- The image contains no visible text or watermark.

