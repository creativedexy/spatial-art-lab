# Cyber Central photograph — generation notes

## Method

- Tool: built-in `image_gen`
- Mode: `sketch-to-render`
- Passes used: 1 generation, 1 correction pass
- Selected result: correction pass (pass 2)
- Generated source: 1672 × 941 PNG (approximately 16:9)
- Delivery: whole-frame resample to 1280 × 720; no crop, extension, or reframing

## User prompt (verbatim)

```text
Use the built-in image_gen tool, sketch-to-render, to REMAKE an approved place photograph so it agrees with the 3D model as it now stands.

INPUT 1 is the geometry master: a render of our own current 3D model from exactly the camera this photograph is taken at. Every building, street, tree belt, orchard row, solar row, canopy and field boundary must keep its position, footprint and height, within about 15 px at 1280x720. The model has changed a great deal since the old photograph: about 1,100 homes as terraces and timber blocks (was 70), campus courtyard blocks, vertical bifacial solar rows over pasture, solar canopies over GCHQ's car parks, mature orchards and woodland belts, open stormwater channels. Follow the plate, never the old photograph, for what is where.
INPUT 2 is the OLD approved photograph at this camera: use it ONLY for photographic look, light, colour, haze and level of detail. Its layout is out of date.
INPUT 3 is the approved adventurous target board for this part of the site: use it for materials and character (buff brick and honey timber, PV glass, meadow roofs, planting).

Design direction: design excellence and realism, built precedents only (Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattorkaia, Augustenborg, Next2Sun), never corporate office park, never illustration, no text or watermark, people and vehicles at true scale. Late summer afternoon, the same sun as INPUT 2.

Output 1280x720 (whole-frame resize only, no crop or warp) to experiments/002-living-map/generate/m7/out/cyber-central-photo.png. One generation plus at most one correction pass if geometry drifts. Write experiments/002-living-map/generate/m7/out/cyber-central-notes.md with the prompts verbatim, passes, and an honest inspection (drift you can see, anything that reads as CGI).

THIS PLACE: Cyber Central (2045). Camera [-760, 209.609, 430] looking at [123, 62.597, 64].
What the place copy says, so the photograph must show it: The innovation campus, on a field grid rebuilt at 22 degrees — inside the band that 35% of the box's surviving hedge length already runs in, so the new streets follow lines that are there rather than lines we liked. Twenty blocks of 38 by 17 m, four or five storeys, banded buff stone over a glazed ground floor. GCHQ sits on the skyline beyond, 100 m away and the whole point of the address. Nothing here is a tower: the scheme caps built ground at a third.
```

## Pass 1 prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: approved place photograph, 1280×720 landscape master

Primary request: REMAKE the approved place photograph as a convincingly real aerial architectural photograph of “Cyber Central (2045),” while matching the current 3D model geometry exactly.

Input images:
- Image 1 is the ABSOLUTE geometry and camera master. Preserve the whole frame, viewpoint, perspective, horizon, landform, and every visible building, street, path, tree belt, orchard row, vertical solar row, canopy, field boundary, drainage channel and open space in its exact position, footprint, orientation and height, within about 15 pixels at 1280×720. Follow Image 1 for all spatial content. Its pale untextured masses become realistic buildings but do not move, multiply, disappear or change scale.
- Image 2 is the OLD approved photograph. Use it ONLY for photographic realism, late-summer afternoon sunlight, colour, haze, atmospheric depth, natural texture and level of detail. Its layout is obsolete: do not retain or borrow its building positions, roads, planting layout or open fields.
- Image 3 is the approved adventurous target board. Use it ONLY for materials and character: banded buff brick/stone, honey-coloured timber, clear dark PV glass, biodiverse meadow roofs and rich naturalistic planting. Do not borrow its layout or camera.

Scene/backdrop: The current 2045 district exactly as Image 1. On the left and mid-left, preserve the plate’s twenty long campus blocks, each 38 by 17 metres and four or five storeys, aligned on the rebuilt field grid at 22 degrees. They are slim rectilinear bars and courtyard-forming groups with planted roofs, occupying no more than one third of their plots, not bulky slabs. Preserve all gaps, staggered offsets, road alignments and woodland/orchard boundaries. Across the centre and foreground preserve the dense field of about 1,100 low homes exactly where Image 1 places them, expressed as compact terraces and modest honey-timber blocks, never detached-house sprawl invented from Image 2. Preserve vertical bifacial PV rows over pasture, solar canopies over GCHQ car parks, mature orchards, woodland belts and open stormwater channels wherever visible in Image 1. The circular GCHQ building stays in its exact central middle-distance position, silhouette, diameter and height, about 100 metres beyond the campus: it is the skyline anchor and the point of the address, but not redesigned or enlarged.

Subject: Cyber Central from camera [-760, 209.609, 430] looking at [123, 62.597, 64]. The innovation campus follows the surviving hedgerow/field grain at 22 degrees. Twenty 38×17 m blocks, four or five storeys, with banded buff stone over transparent glazed active ground floors. Nothing is a tower.

Style/medium: high-resolution professional aerial place photography, natural and credible, with built-precedent discipline informed by Goldsmith Street, Solarsiedlung, Sara Kulturhus, Powerhouse Brattorkaia, Augustenborg and Next2Sun. Fine construction detail, believable occupation and mild real-world imperfection. Never an illustration, game render or glossy corporate-office-park visualisation.

Composition/framing: exact full-frame composition of Image 1; 16:9 landscape; no crop, no warp, no reframing, no camera move. Keep horizon at the same height. Maintain all massing silhouettes, counts and occlusion relationships. Geometry takes priority over beautification.

Lighting/mood: late-summer afternoon with the same sun direction, warm natural light, blue sky, small clouds, believable shadows, haze and aerial atmospheric perspective as Image 2.

Color palette: restrained photographic colour; warm buff masonry, honey timber, muted meadow and orchard greens, dark blue-grey PV glass, natural asphalt and stone.

Materials/textures: banded buff stone or brick façades above clear glazed ground floors; honey timber on housing and selected campus elevations; meadow roofs; credible PV glass; realistic pasture, orchard crowns, hedgerows, woodland, drainage water, reeds and paving. Material articulation must stay within the plate’s silhouettes.

Text: none.

Constraints: Preserve Image 1’s exact building count and arrangement, especially all twenty campus blocks, the circular GCHQ landmark, dense centre/foreground housing, roads and junctions, woods, orchards, drainage, PV rows, canopies and field edges. People and vehicles only at true aerial scale. No new towers. No layout from Images 2 or 3. Whole frame must remain 16:9 for a final whole-frame resize to 1280×720.

Avoid: missing or invented buildings; consolidated campus megablocks; moved roads; altered rooflines; detached-house layout copied from Image 2; enlarged trees concealing geometry; generic office park; lawns or surface parking replacing campus fabric; tower forms; toy-town look; isometric illustration; video-game render; excessive HDR; oversaturation; fake repeated windows; malformed cars or people; labels, signs, logos, text, borders or watermark.
```

## Pass 2 correction prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-correction edit of an approved aerial place photograph

Primary request: Correct ONLY the visible geometry drift in the left and mid-left Cyber Central campus of Image 1. Keep Image 1’s successful photographic appearance and all other areas unchanged. Image 2 is the absolute geometry master.

Input images:
- Image 1 is the first-pass photograph to edit. Preserve its exact camera, framing, horizon, late-summer light, haze, colour, photographic texture, circular GCHQ building, central and foreground housing, right-hand roads, all distant fabric and overall realism.
- Image 2 is the absolute geometry master. Use it to restore the exact campus envelopes, gaps, alignments, roads, orchard/woodland boundaries, field edges and lower-left open channels. Geometry overrides beautification.

Single targeted correction: The first pass wrongly consolidated the left/mid-left campus into about five oversized courtyard megablocks. Replace those consolidated forms with the complete set of separate slim four- and five-storey bars shown in Image 2: twenty blocks, each 38×17 m, stepping across the field grid at 22 degrees. Match every visible block footprint, length, width, height, orientation, stagger, gap and occlusion in Image 2 within about 15 pixels at final 1280×720. Do not enlarge them into square courtyards. Preserve the plate’s open space between bars and its one-third maximum built-ground character. Use banded buff stone/brick above clear glazed ground floors, occasional honey timber, planted meadow roofs and restrained PV glass, all contained inside the master silhouettes.

Also tighten the immediate campus context to Image 2: keep its exact orchard and woodland edges, paths/roads and open stormwater-channel geometry; do not add large ponds or meanders beyond the plate. Do not change unrelated parts of the image.

Composition/framing: exact full-frame geometry of Image 2 and exact photographic camera of Image 1; 16:9; no crop, warp, reframing or camera move.

Constraints: Preserve the circular GCHQ landmark at its current exact position and size; preserve the dense housing and main road network already achieved. No tower. No invented or missing campus buildings. People and vehicles only at true aerial scale. No text, signs, logos or watermark.

Avoid: courtyard megablocks; merging adjacent bars; moving GCHQ; changing foreground housing; hiding blocks with enlarged trees; corporate office park; illustration; game-render appearance; excessive HDR; malformed tiny objects.
```

## Passes and selection

Pass 1 produced the strongest broad photographic transformation but collapsed the left/mid-left campus into roughly five oversized courtyard buildings and made the lower-left drainage more extensive than the plate. The single permitted correction pass was therefore used to split and re-register the campus massing. Pass 2 was selected because it restores a visibly finer sequence of separate bars, reduces the scale of the campus masses, and keeps the successful GCHQ, housing, road and landscape treatment.

## Honest visual inspection

### Geometry and content

- The camera direction, horizon height, central GCHQ landmark, right-hand arterial road, major woodland mass and overall settlement distribution remain close to the master at whole-image scale.
- GCHQ retains the intended central middle-distance role and circular silhouette. Its façade is more glazed and detailed than the model, but it has not become a tower.
- The correction improves the campus from about five large megablocks to a longer sequence of smaller four/five-storey buildings following the diagonal field grain. However, it still does not preserve all twenty 38 × 17 m bars as independently legible objects. Several nearer buildings remain paired or joined into U-shaped/courtyard compositions, and some far-left bars merge with trees or background housing.
- Therefore the requested approximately 15 px tolerance is not achieved feature-by-feature. The campus's broad zone, diagonal alignment and stepping are credible, but exact footprints, gaps and count drift visibly.
- The central and foreground housing is much denser than the old photograph and broadly follows the plate's occupied zones, but individual terraces are regularised into repeated small houses. Exact house-by-house registration and the full 1,100-home typology cannot be verified from this aerial distance.
- The lower-left woodland and orchard bands occupy the correct broad areas. Individual rows and crowns are naturalised rather than registered tree by tree.
- Vertical PV rows survive at the far left, but their count and spacing are simplified. Solar canopies around GCHQ read partly as dark parking/PV bands but are not consistently explicit.
- Open stormwater is visible in the lower-left foreground. Its curves, pools and reed edges remain more pronounced and sinuous than the simplified master channels.
- The lower-right institutional/car-park massing and some foreground road/building details are photographic reinterpretations; local edges and footprints drift from the model.

### Photographic realism / residual CGI tells

- The late-summer light, aerial haze, tonal depth, sky and vegetation variation are convincing and much closer to a real photograph than the geometry render.
- Repetition remains visible in the small foreground houses, campus window bays, roof planting and evenly spaced trees. This gives parts of the image a procedural masterplan/CGI character on close inspection.
- Some roof edges and façade grids are unusually clean, while tiny cars and road markings become soft or inconsistent.
- Meadow and reed textures are attractive but slightly over-lush and uniformly detailed for this viewing distance.
- The image contains no visible text or watermark.
