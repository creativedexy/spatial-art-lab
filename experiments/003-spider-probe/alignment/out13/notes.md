# Round 13 notes

Generated with the built-in image editor from the three `out11` PNG edit targets.

## Outputs

- `g1-sandstone.png` — replaced only the foreground ground treatment with a bedded, fractured sandstone ledge: cross-bedding, wind-worn faces, sparse grit and pebbles, desert-varnish variation, raking edge light, and a soft near foreground.
- `g2-mangrove.png` — replaced the glazed root treatment with grey-brown rough bark, lenticels, restrained oysters and barnacles at the waterline, green algae, and lower-only wetness; the foreground retains shallow-focus falloff.
- `g3-snow.png` — replaced the oversized crystalline foreground with fine matte powder drifts over dark granite, blue-grey shadow snow, sparse torch sparkles, feldspar grain, subdued lichen, and a soft near foreground.

## Invariants requested

Each edit prompt explicitly locked the panther, pose, lighting, colour grade, background, framing, camera angle, depth of field outside the ground, and overall composition, and limited the requested material change to the surface under and in front of the paws in roughly the lower third.

## Output processing and QA

- Built-in edit results were `941 x 1672` PNGs.
- Each result was proportionally resampled to `1920` px tall with `sips`, then centre-cropped by one pixel to exactly `1080 x 1920`.
- Final files were visually inspected after resizing.
- Confirmed final dimensions: `1080 x 1920` PNG for all three files.

