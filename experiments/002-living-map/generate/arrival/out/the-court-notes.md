# The Court — generation notes

## Prompt (verbatim)

```text
Use case: sketch-to-render
Asset type: geometry-faithful architectural photograph, 1280x720 landscape

Primary request: Make a photorealistic photograph of the court between two buildings of an innovation campus in 2045, from a render of our own measured 3D model. This is a camera-locked sketch-to-render transformation.

Input images:
- Image 1 is the geometry master and edit target. Preserve its exact camera, perspective, terrain horizon, building footprints, rooflines, façade edges, central gap, ground line, and all visible massing. Every building edge and ground line must stay within about 20 px of Image 1 at 1280x720. Eye height is 1.6 m above measured terrain, with a 48-degree vertical field of view. Follow Image 1 for WHAT IS WHERE.
- Image 2 is the approved adventurous target board. Use it only for materials, architectural character, planting character, and photographic realism. Do not copy its aerial camera, layout, building shapes, or spatial arrangement.

Measured geometry: The campus contains 105,501 m2 of floor area in blocks of 2 to 7 storeys. The two buildings visible in this frame are 17.0 m and 13.6 m high and stand 40 m and 60 m from the camera. Preserve those relative heights, distances, and positions from Image 1. These are their east elevations.

Scene/backdrop: A working, biodiverse court between the two measured buildings. Replace the dark blank ground of Image 1 with sett and gravel paths winding through long wildflower grass, retained mature trees in the locations supported by the plate, timber seating along the glazed ground floor, cycle stands, and a modest covered way. It must not become a lawn and must not become a hard paved plaza.

Architecture and materials: Silvered larch and buff brick above a glazed ground floor, with deep window reveals and a floor-depth spandrel. The buildings must read as crafted low- to mid-rise civic campus buildings, informed by built precedents such as Sara Kulturhus, Goldsmith Street, and Powerhouse Brattorkaia. Never turn either building into a curtain wall or glass-box office park. Keep the Image 1 façade rhythm and massing; apply materials within it.

Lighting/mood: Real light at 16:45 in late August. The east elevations are in their own cool blue-grey shade, while low warm sun rakes across only the upper floors, parapets, and trees behind. Make the shade legible and natural, not crushed black and not artificially filled. No HDR glow.

People: A few ordinary, unposed campus workers at true human scale: some crossing the court, two sitting outside the glazed ground floor, and one person wheeling a bicycle. They must be readable people, not tiny specks, and must not dominate the image.

Style/medium: A believable contemporary architectural photograph of a place no camera has yet stood in. Natural exposure, realistic materials, fine construction detail, restrained documentary character. Design excellence and realism, never a corporate render, never an illustration, never developer-marketing polish.

Composition/framing: Preserve the whole frame of Image 1 without crop, reframing, camera shift, lens change, or perspective warp. Sky must remain no more than 25 percent of the frame.

Constraints: Geometry and camera are sovereign. Keep every building taller/shorter relationship, all rooflines, façade corners, central opening, and ground line where they are in Image 1 within about 20 px at final 1280x720. Keep all additions plausible and subordinate to the fixed geometry. No text or watermark.

Avoid: glass box towers; curtain wall architecture; office-park character; car park; cars; hard empty plaza; manicured lawn; lens flare; HDR glow; excessive bloom; staged crowds; people as specks; added floors; removed floors; moved, widened, narrowed, taller, or shorter buildings; more than 25 percent sky; aerial viewpoint; illustration or CGI marketing style.
```

## Passes

1. Built-in image generation, sketch-to-render, using the 3D plate as the edit target and the adventurous campus board as a materials/character reference. Native result: 1672 × 941 PNG.
2. No correction generation was used. The principal geometry was close enough to the plate that another generative pass posed more risk than benefit.
3. The accepted pass was resized as a whole frame with Lanczos filtering to exactly 1280 × 720. There was no crop, extension, or perspective operation.

## Honest inspection

- **Geometry:** Strong overall. The left sloping roofline, the central step/gap, the tall right-hand block's leading edge, and the right roofline closely track the geometry master at the final scale. The major silhouettes appear within roughly the requested 20 px tolerance by visual comparison. Some lower façade/ground contacts are partly concealed by planting, so the entire ground line cannot be verified pixel-for-pixel.
- **Camera and framing:** The eye-level perspective and wide framing are retained. The right block starts at approximately the same normalized horizontal position as the plate, and the sky remains below 25 percent of the frame. No crop was used.
- **Architecture/materials:** Silvered larch, buff brick piers, deep reveals, floor-depth timber spandrels, and a glazed ground floor are all legible. The result does not read as a curtain-wall office park.
- **Court programme:** Long wildflower planting and gravel paths dominate rather than lawn or paving. Timber seating, cycle stands, a covered/glazed way, and several mature trees are visible. Distinct sett paving is not strongly legible.
- **People:** The scene includes a small number of ordinary workers at readable scale, two seated at the ground floor, and a person handling a bicycle. Poses are generally candid and subordinate to the place.
- **Light:** The late-August raking light and warm upper edges read well, with usable shadow detail. The main shortfall is that the court and east elevations are warmer and more evenly illuminated than the requested cool blue-grey shade; this is the largest departure from the brief.
- **Realism:** Photographic detail, material grain, vegetation, and natural human scale are convincing. It is polished enough to retain a slight architectural-visualisation character, but avoids obvious illustration, lens flare, text, watermark, cars, and HDR bloom.
- **Tree-position caveat:** The supplied geometry plate does not visibly expose individual tree markers against its dark ground, so tree-position compliance could not be verified to the same 20 px standard as the building edges.

## Final asset

`the-court.png` — 1280 × 720 PNG.
