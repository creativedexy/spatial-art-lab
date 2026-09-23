# Round 11 generation notes

Generated with the built-in image generation tool as reference-preserving environment edits. The supplied G3 panther, G1 shark, and F5 octopus plates were used as edit targets. For every variant, the animal's pose, side-on angle, framing, scale, position, and anatomy were held as close as possible to its source while only the environment changed.

## Deliverables

- `h1-panther-sandstone.png` — panther on a red sandstone ledge in a desert canyon at night
- `h2-panther-mangrove.png` — panther on a mangrove root above black water with fireflies and reflected light
- `h3-panther-snow.png` — panther on a snow-covered granite ledge with lit snowfall and frosted whiskers
- `h4-shark-plankton.png` — shark over pale sand with blue bioluminescent plankton trailing from the fin
- `h5-shark-reefwall.png` — shark gliding along a sheer reef wall with sea fans and sponges
- `h6-shark-ice.png` — shark beneath cracked sea ice with bubbles and ice crystals
- `h7-octopus-shells.png` — octopus eye and curled arm on pale scallop and cockle shells
- `h8-octopus-seawhips.png` — octopus eye and curled arm among red sea whips and orange cup corals
- `h9-octopus-urchins.png` — octopus eye and curled arm in kelp holdfasts with purple sea urchins

The original 1024 x 1536 generations are retained in `source-1024x1536/`. The nine top-level PNGs are the final 1080 x 1920 plates.

## Shared direction

- One low directional light source with rapid falloff to deep black
- Photographic wildlife realism and correct anatomy
- Suspended particles catching the light
- No ferns, moss, HUD, text, lines, watermark, or extra animals
- Essential animal anatomy kept inside the central 80% for the final centre crop

## Processing

Each 1024 x 1536 source was scaled to 1920 px high with `sips`, producing a 1280 x 1920 intermediate. The intermediate was centre-cropped by 100 px on both horizontal sides to 1080 x 1920.

Equivalent command sequence:

```sh
sips --resampleHeight 1920 source.png --out scaled.png
sips --cropToHeightWidth 1920 1080 scaled.png --out final.png
```

## QA

- All nine source images were verified as 1024 x 1536 PNG.
- All nine final plates were verified as 1080 x 1920 PNG.
- Final crops were checked for retained eye, head, and essential anatomy.
- Panther variants retain the right-facing crouched head-and-shoulders composition.
- Shark variants retain the right-facing side profile, front body, and near pectoral fin.
- Octopus variants retain the tight eye close-up and one curled arm across the lower frame.

