# Among the Panels — generation notes

## Inputs

- Geometry master: `experiments/002-living-map/generate/arrival/final/among-the-panels-2045.png`
- Materials/character board: `experiments/002-living-map/generate/m2/boards/panels-b-adventurous.png`
- Method: built-in `image_gen`, sketch-to-render
- Final image: `experiments/002-living-map/generate/arrival/out/among-the-panels.png`
- Final delivery size: 1280 × 720. The selected 1672 × 941 generated frame was resized as a whole frame to 1280 × 720; it was not cropped or warped.

## Pass 1 prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: final architectural landscape photograph, 1280×720, 16:9
Primary request: Convert INPUT 1 into a rigorously geometry-faithful, natural photographic view of this exact measured place in 2045. It is a photograph taken from the exact INPUT 1 camera: eye height 1.6 m above the measured terrain, 48 degree vertical field of view. Follow INPUT 1 for WHAT IS WHERE within about 20 px at 1280×720. Do not reinterpret, crop, warp, raise, lower, or relocate the camera.
Input images: INPUT 1 is the absolute geometry, camera, composition, horizon, terrain, panel-row, tree, and building master. Preserve its pixel layout and silhouettes. INPUT 2 is materials and character only for panels, glasshouses, vegetation, solar roofs, and restrained realism; never copy its aerial layout or camera.
Scene/backdrop: Standing between rows of a 9.7 hectare vertical agrivoltaic field at the edge of the new neighbourhood in 2045. There are 39 rows in 3 fields, rows 11 m apart on a 22 degree bearing. Modules are vertical, 2.0 m tall, 0.35 m clear of the ground, 1.1 m wide in frames, fixed to slim posts at 3.6 m centres. New homes remain 86–155 m behind exactly where INPUT 1 places them, including the 20.4 m apartment block, with trees between.
Subject: Bifacial photovoltaic modules standing truly vertical and edge-on along the measured lines. Render them as individual blue-black solar-glass modules with subtle seams and restrained sky reflection at this glancing angle, never opaque fence panels and never a continuous black wall. Show the genuine 0.35 m clear gap below the rows wherever perspective permits, with crop visible through it. Use slim galvanised steel posts and rails, no ballast.
Agriculture: The entire 11 m inter-row corridor is actively farmed in a late-summer cereal or legume crop, following the terrain and drilled in fine parallel rows along the field, as at the built Next2Sun Donaueschingen precedent. Retain narrow uncultivated service bands immediately beside each panel line. It must read as productive agriculture: not lawn, mown grass, gravel, bare soil, or membrane.
People: Include only one or two ordinary, small, true-scale working figures where they fit without obscuring the geometry: a grower walking the crop rows and/or one person cycling on the distant field track. Candid work, not posing.
Homes: Preserve every building from INPUT 1 and add none. Keep their exact positions, extents, rooflines, and apparent size for the measured distance. Use calm built-precedent character informed by Solarsiedlung and Goldsmith Street: durable warm masonry/timber tones, solar-glass roofs, credible glazing, trees between. The apartment block stays exactly at its INPUT 1 scale and position.
Style/medium: Highly realistic editorial architectural and agricultural photography; physically plausible optics and materials; natural detail; explicitly not an illustration, CG render, solar-farm stock photograph, or developer marketing image.
Composition/framing: Exact whole frame of INPUT 1 at 1280×720. Preserve the near right panel-row top edge, vertical posts, receding vanishing line, opposing left row, terrain crest, crop corridor, tree canopy, all roof silhouettes, and central apartment block within about 20 px. Keep visible sky under 30 percent of the frame by the existing foreground structures/vegetation only, without changing the camera or adding anything.
Lighting/mood: Late-summer afternoon around 16:45, warm but restrained side light, long soft-edged shadows crossing the drilled crop rows, lightly hazy pale blue sky, realistic atmospheric depth, moderate dynamic range, no HDR glow.
Color palette: Natural muted late-summer greens and straw tones, blue-grey reflective solar glass, galvanised silver-grey steel, warm subdued homes, hazy blue sky.
Materials/textures: Slightly dusty crop leaves and seed heads, fine worked soil glimpsed between drilled rows, realistic blue-black bifacial glass with restrained reflections and subtle module divisions, thin galvanised structure, solar glass integrated into distant roofs.
Text (verbatim): ""
Constraints: Geometry and camera from INPUT 1 are inviolable. Materials/character from INPUT 2 only. Whole-frame 16:9 output; no crop, no lens change, no warp. All panels truly vertical; rows remain 11 m apart; physical module height 2.0 m; 0.35 m ground clearance; posts at 3.6 m centres. Every existing building remains and no building is added. One or two people maximum, true scale.
Avoid: tilted panels or rack arrays; continuous black wall; opaque fence appearance; panels physically taller than 2 m; rows closer than 11 m; panels blocking the real under-gap where visible; mown grass; generic turf; gravel; bare fallow soil; plastic membrane; sheep; security fence; concrete ballast blocks; invented buildings; removed buildings; relocated buildings; oversized people; posing; dramatic clouds; sky over 30 percent; excessive saturation; cinematic teal-orange; HDR halo or glow; aerial viewpoint; text; signage; logo; watermark.
```

## Pass 1 inspection

The first pass established convincing blue-black solar glass, believable late-summer light, solar roofs, trees, and productive crop. It retained the broad camera idea but rendered the field as dense wheat, made the under-panel clearance weak, used conspicuously heavy cylindrical posts, and did not give enough prominence to drilled crop rows. A correction pass was therefore used.

## Pass 2 correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction pass for the final 1280×720 architectural landscape photograph
Primary request: Correct INPUT 1, the first photographic pass, by restoring the exact camera composition and measured layout from INPUT 2, the geometry master. Keep the natural photographic materials and restrained late-summer realism already achieved, with INPUT 3 as material character only. This is the single correction pass: geometry fidelity takes priority over prettiness.
Input images: INPUT 1 is the photographic edit target. INPUT 2 is the absolute geometry/camera plate and overrides INPUT 1 wherever silhouettes, positions, scale, horizon, or perspective differ. INPUT 3 is approved materials and character only, never layout.
Composition/framing: Match INPUT 2 within about 20 px when viewed at 1280×720, as a whole-frame 16:9 image with no crop or warp. Restore these explicit plate landmarks: the huge near right-hand vertical panel row begins around x=770 at its upper-left corner near y=100, its close leading edge continues down beyond the bottom around x=940, and its top edge recedes toward the right vanishing area around x=1240,y=335. This blue-black glass plane must dominate the right foreground just as in INPUT 2, not begin around x=1000. Restore the opposing left row with its upper edge near y=250 at the far left and near y=330 across the middle, and its lower edge reaching roughly y=490 at the far left. Restore the crop-covered terrain crest rising around x=465,y=390 and meeting the near row around x=765,y=395. Restore the exact distant tree and roof silhouettes between roughly y=240 and y=345. Keep the 20.4 m apartment block at INPUT 2’s exact central size and position, approximately x=575–685 with its roof near y=252. Keep every other building in INPUT 2; add or remove none. Restore the same 1.6 m eye-height and 48 degree vertical field of view.
Panels and structure: All modules are genuinely vertical bifacial solar-glass, 2.0 m physical height, 0.35 m clear of ground, 1.1 m wide, on slim galvanised posts and rails at 3.6 m centres. The near right-hand surface should remain blue-black reflective glass with subtle module seams and sky reflection at a grazing angle—not a continuous opaque fence—but do not shrink or relocate its plate silhouette. Make the 0.35 m under-panel gap visibly legible on the left row and on the receding right row wherever INPUT 2 perspective permits; crop continues through the gap. No cylindrical oversized posts: posts are slim, workmanlike galvanised sections.
Agriculture: Replace the overly dense undifferentiated wheat foreground of INPUT 1 with a lower worked cereal or legume crop in visibly drilled fine parallel rows running along the field exactly as the furrows shown in INPUT 2, following the measured terrain. Preserve narrow uncultivated service bands tight to both panel lines. The full 11 m between the panel rows remains farmed. It must not read as lawn, wildflower verge, gravel, membrane, or bare field.
Homes and vegetation: Keep all homes, solar-glass roofs, apartment block, trees, and their scale/positions exactly from INPUT 2. Preserve credible subdued built-precedent materials; no invented buildings and no enlargement.
People: If a figure can be included without geometry drift, use at most one very small, true-scale grower walking a distant crop row or one cyclist on the far field track; otherwise omit people rather than compromise geometry.
Style/medium: Natural editorial architectural/agricultural photograph, physically plausible, fine realistic texture, no illustration or CGI appearance, no stock-photo or developer-marketing polish.
Lighting/mood: Late-summer afternoon around 16:45; restrained warm side light; long shadows across the drilled crop; hazy pale-blue sky; moderate dynamic range; no HDR glow.
Constraints: Edit only what is required to restore INPUT 2 geometry, drilled-row agriculture, slim structure, and under-panel clearance. Preserve the good realistic solar-glass, crop, lighting, and building material treatment from INPUT 1. Exact full frame; no crop; no warp; no camera move. Sky must occupy no more than 30 percent of the total visible frame: accomplish this by restoring the dominant foreground panel silhouette and plate geometry, not by changing the camera or inventing objects.
Avoid: geometry drift; near row starting too far right; lowered horizon; oversized round posts; panels taller than 2 m physically; rows closer than 11 m; tilted or rack-mounted panels; continuous featureless black wall; missing under-gap; dense unstructured wheat filling everything; lawn; gravel; membrane; bare soil; sheep; security fence; concrete ballast; altered, added, or removed buildings; oversized people; sky over 30 percent; dramatic clouds; excessive saturation; HDR halo; text; signage; logo; watermark.
```

## Final inspection

The final selected image is the corrected second pass.

What succeeded:

- Exact 1280 × 720 delivery, produced by whole-frame resize only.
- The near right-hand row is close to the master at its upper-left corner and along its receding top edge; it remains the dominant foreground element.
- Modules are vertical, divided into individual blue-black glass panels, and show restrained reflections rather than reading as a featureless black wall.
- The field is visibly productive and the full inter-row space is planted in drilled rows, with a narrow service margin beside the right panel line.
- Under-panel clearance is visible on the left row and along the receding right row.
- Houses, solar roofs, trees, and the central apartment block retain the broad placement and apparent scale of the geometry master.
- Late-summer side light, long field shadows, atmospheric depth, and restrained colour are credible. There is no text, watermark, security fence, ballast, gravel, membrane, sheep, tilted rack, or HDR glow.

Remaining deviations after the allowed correction:

- The opposing left panel row begins about 65–75 px lower than the geometry master at the far-left edge, exceeding the requested ±20 px tolerance; its lower edge also differs.
- The near-row leading post and panel corner are roughly within 20 px, but the generator made the foreground post much thicker and more cylindrical than the specified slim galvanised section.
- The visible sky is approximately one-third of the frame and likely remains slightly above the 30% limit.
- No grower or cyclist is visible. The correction prompt allowed omission if a figure threatened geometry, but this means the requested ordinary human activity is absent.
- The crop is legume-like rather than clearly cereal, which is permitted, but the foreground contains more exposed worked soil between drills than the ideal target.
- Building facades and fine tree shapes are photoreal reinterpretations rather than pixel-exact transfers. The principal apartment block is close in position and size, but exact preservation of every distant building cannot be claimed.

No further generation was made because the instruction limited the work to one generation plus at most one correction pass.
