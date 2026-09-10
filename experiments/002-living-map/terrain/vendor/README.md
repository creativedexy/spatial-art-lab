# Vendored libraries

Offline-first: everything the map needs is in this folder, so serving it over
HTTP is the whole setup. Nothing here is modified except where noted.

| file | what | licence |
|---|---|---|
| `three.module.min.js` | three.js r169 | MIT |
| `OrbitControls.js` | three.js r169 example | MIT |
| `BufferGeometryUtils.js` | three.js r169 example | MIT |
| `GLTFLoader.js` | three.js r169 example, for the Meshy type models | MIT |
| `meshopt_decoder.module.js` | meshoptimizer, shipped with three.js r169 | MIT |
| `fonts/` | Cormorant Garamond, Jost | see `fonts/README.md` |

`meshopt_decoder.module.js` is 24 KB and unpacks the geometry of every type
model: the two GLBs carry 1.9 MB of float32 positions uncompressed and 0.25 MB
through meshopt, so the decoder pays for itself roughly seventy times over on
a first load.

**One edit.** `GLTFLoader.js` imports `toTrianglesDrawMode` from
`../utils/BufferGeometryUtils.js`, which is where it lives in the three.js
source tree and not where it lives here; the import points at this folder
instead. That is the only change.
