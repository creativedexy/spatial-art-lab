# Panels and glasshouses (2045) — generation notes

## Inputs

1. Geometry master: `experiments/002-living-map/generate/m7/plates/panels-and-glasshouses-2045.png`
2. Old approved photograph, used only for photographic treatment: `experiments/002-living-map/generate/golden-valley-2045/out/c-panels-and-glasshouses-photo.png`
3. Approved adventurous target board, used only for materials and character: `experiments/002-living-map/generate/m2/boards/panels-b-adventurous.png`

## Passes

- Pass 1: built-in `image_gen`, sketch-to-render, using all three reference images.
- Correction pass: not used. The first pass preserved the major camera and land-use geometry well enough that another generative edit was judged more likely to damage the retained alignment than improve it.
- Delivery resize: the generated 1672×941 frame was resized as a whole to 1280×720. There was no crop, extension or local warp.

## Pass 1 prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: approved architectural place photograph, 1280x720 landscape

Primary request: REMAKE Image 1 as a highly realistic aerial architectural photograph. Image 1 is the absolute geometry master and camera master. Photorealistically render the exact scene that Image 1 depicts; do not redesign, simplify, substitute, relocate, add, or omit spatial elements.

Input images:
- Image 1: GEOMETRY MASTER and edit target. It exclusively controls camera, crop, perspective, horizon, terrain, and the exact position, footprint, orientation, height, massing and extent of every building, street, path, tree belt, orchard row, solar row, canopy, watercourse and field boundary.
- Image 2: OLD approved photograph. Use ONLY for photographic look, late-summer sunlight direction, colour, atmospheric haze, natural detail density and camera realism. Ignore its layout and all object positions.
- Image 3: approved adventurous target board. Use ONLY for materials and character: buff brick, honey-toned timber, dark blue-black PV glass, meadow roofs, rich productive planting, and credible built detail. Ignore its camera and layout.

Scene/backdrop: Panels and glasshouses, 2045, in a broad English valley. The whole proposition is visible in one frame: the unchanged 3D-model plan contains about 1,100 homes as compact terraces and timber blocks around and behind five campus courtyard blocks; large mature orchard compartments and woodland belts; open stormwater channels; and foreground working pasture carrying long, narrow rows of vertical bifacial solar panels. The crop/pasture remains visibly farmed between the solar rows. Glasshouses use campus waste heat. The circular GCHQ complex remains exactly where and at the scale shown in Image 1, with solar canopies over its car parks.

Composition/framing: Preserve Image 1 pixel registration as closely as possible, within about 15 px at 1280x720. Same exact oblique aerial camera [-720, 240.817, -520] looking at [-330, 43.977, -230]. Keep the low horizon height and every major silhouette and boundary unchanged. Whole-frame output; no crop, no reframing, no lens change, no warp. In particular preserve:
1. two very large foreground solar-pasture fields and their exact boundaries, with straight parallel vertical bifacial rows following Image 1;
2. foreground-right dense woodland block and its dark cast shadow;
3. the orchard/tree compartments across the lower middle, including the narrow pale glasshouses visible among them;
4. the large open field at middle-right and woodland/orchard beyond it;
5. exactly five principal buff/honey campus courtyard blocks spanning the middle, with their precise U/O-shaped footprints, heights and gaps;
6. the dense residential fabric and street network behind them;
7. the circular GCHQ ring building and adjacent structures in the upper middle;
8. distant settlement, terrain ridgeline and all tree belts exactly as Image 1.

Style/medium: convincing high-resolution professional drone photograph, natural material variation, fine real-world imperfection and true atmospheric depth; built precedent character from Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattorkaia, Augustenborg and Next2Sun. This must read as a real inhabited and farmed place, never an illustration, painting, game render or glossy CGI masterplan.

Lighting/mood: late-summer afternoon matching Image 2, same warm sun direction and long coherent shadows, blue sky and restrained haze, realistic exposure without fantasy grading.

Materials/textures: buff brick and honey timber elevations; meadow roofs and restrained rooftop PV; slim dark bifacial PV glass mounted vertically over living green pasture/crop; functional transparent glasshouses; mixed mature orchard canopies, hedgerows and woodland with species and tonal variation; ordinary asphalt, gravel and mown paths; open stormwater channels with believable water and wetland vegetation.

Scale/activity: only sparse people, bicycles, farm equipment and ordinary vehicles, all at optically correct tiny aerial scale. Keep agriculture legible and working.

Constraints: Geometry beats beauty. Follow Image 1, never Image 2 or Image 3, for what is where. Maintain all geometry and field patterns within about 15 px. Preserve the whole frame. Output must be 16:9 1280x720 by whole-frame resize only if needed. No text, labels, logos, signage or watermark.

Avoid: any old-photo layout; changing the horizon; mountains larger than Image 1 terrain; corporate office-park architecture; generic glass office slabs; extra towers; erased housing; oversized people or vehicles; tilted conventional solar tables replacing the thin vertical bifacial rows; blue rectangular solar carpets; invented ponds; decorative paths; excessive glass; repeated cloned trees; plastic vegetation; over-sharp CGI edges; painterly or illustrative surfaces.
```

## Honest inspection

### Geometry and content retained well

- The low oblique aerial camera, frame coverage and overall horizon height remain close to the plate.
- The two large foreground solar-pasture parcels, central dividing hedge, right woodland mass and broad cast shadow all remain in their correct parts of the frame.
- The orchard compartments, two narrow pale glasshouses, middle-right open field and woodland/orchard edge remain clearly legible.
- The central buff-brick courtyard blocks follow the plate's dominant footprints and spacing; the circular GCHQ complex remains centred behind them at approximately the correct scale.
- Dense housing and roads occupy the same broad background zones as the model rather than reverting to the old photograph's sparse scheme.
- Farming remains legible between thin, upright bifacial solar rows, with a small tractor and correctly tiny livestock.

### Visible drift

- The distant terrain has acquired more articulated rolling ridges and field detail than the comparatively smooth geometry-master skyline; local skyline deviations exceed the requested 15 px in places.
- Individual orchard rows, tree crowns, hedges, minor paths and small background roads are interpretive rather than pixel-registered. Some orchard spacing and woodland edges wander by more than 15 px locally.
- Roof articulation, facade bays, internal courtyard planting and small ancillary structures are generated detail rather than exact model geometry.
- The plate visually reads as four dominant central courtyard blocks plus smaller/partial development at the far left; the prompt's phrase “exactly five principal” was ambiguous. The output retains the four dominant central blocks and the smaller left-edge development rather than inventing a fifth dominant block.
- The solar-row count and exact line endpoints are approximate, although their parcels, direction and vertical agrivoltaic character are retained.
- The open stormwater channels are subtle and not consistently readable as open water throughout the frame.

### Elements that still read as CGI

- Orchard crowns and several background housing clusters repeat too evenly.
- The courtyard roofs and facades are very clean and regular, with limited weathering and service clutter.
- Solar rows are exceptionally straight, evenly dark and crisp; their repetition still has a synthetic quality.
- Some distant industrial facades contain tiny pseudo-detail that can resemble illegible signage at close inspection, though no readable text or watermark is present at delivery size.
- The scene is more uniformly groomed and saturated than a fully candid aerial survey photograph.
