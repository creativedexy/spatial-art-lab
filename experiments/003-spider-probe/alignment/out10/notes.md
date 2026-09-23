# Round 10 generation notes

Generated with the built-in image generation tool using the three supplied images only as references for lighting, darkness, photographic realism, and illuminated particles. Their subjects and environments were explicitly excluded. No web assets were used.

## Deliverables

- `g1-shark.png` — oceanic whitetip shark, side profile in open black water
- `g2-owl.png` — barn owl, side profile on a frosted post in falling snow
- `g3-panther.png` — black leopard, side profile on wet basalt in rain
- `g4-wolf.png` — grey wolf, side profile in a night blizzard
- `g5-stag.png` — red deer stag, side profile on a misty frozen moor
- `g6-heron.png` — grey heron, side profile in black shallow water

The original 1024 x 1536 generations are retained in `source-1024x1536/`. The six top-level PNGs are the final 1080 x 1920 plates.

## Processing

Each selected 1024 x 1536 source was scaled to 1920 px high with `sips`, producing a 1280 x 1920 intermediate. That intermediate was centre-cropped by 100 px on both horizontal sides to 1080 x 1920. The composition prompts kept the face, eye, bill or muzzle, and other essential anatomy inside the protected central area.

Equivalent command sequence:

```sh
sips --resampleHeight 1920 source.png --out scaled.png
sips --cropToHeightWidth 1920 1080 scaled.png --out final.png
```

## Selection and QA

- The first shark attempt was rejected because it read too large in the frame. The selected second pass pulls back and protects the eye, gills, dorsal region, and white-tipped pectoral fin through the final crop.
- All selected images use a side-on or slight side three-quarter view, not a frontal pose.
- All plates show more than a headshot and retain environmental darkness in front of the animal's face.
- Final dimensions were verified as 1080 x 1920 PNG. Source dimensions were verified as 1024 x 1536 PNG.
- Final crops were visually checked together as a six-image contact sheet for pose, negative space, and clipped key anatomy.

