# Round 12 notes

Generated with the built-in image-generation tool on 23 September 2026.

The H1–H3 images were used only as references for composition, pose, environment, and light direction. The animal fur and scene surfaces were explicitly re-rendered from scratch. Prompts follow the texture corrections in `../ai-texture-notes.md`: near-black fur treated as a soft mass, faint rosettes only in grazing light, selective specular highlights, shallow depth of field with the eye as the sharpest point, restrained colour, and visible sensor grain.

## Outputs

| Environment | 1024 × 1536 source | 1080 × 1920 final |
|---|---|---|
| Sandstone | `p1-panther-sandstone-1024x1536.png` | `p1-panther-sandstone.png` |
| Mangrove | `p2-panther-mangrove-1024x1536.png` | `p2-panther-mangrove.png` |
| Snow | `p3-panther-snow-1024x1536.png` | `p3-panther-snow.png` |

## Processing

Each generated 1024 × 1536 PNG was copied into this directory. A working copy was then resized with `sips --resampleHeight 1920` (producing 1280 × 1920) and centre-cropped with `sips --cropToHeightWidth 1920 1080`.

Final files were visually checked after cropping. The panther's head, eye, forelegs, and environmental support remain in frame. No HUD, text, or watermark is present.

Exact generation prompts and reference mappings are in `prompts.json`.
