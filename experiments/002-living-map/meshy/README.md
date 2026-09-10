# Meshy type models for the 2045 scheme

Made 10 Sep 2026 by the local session. Dex approved 70 credits; **60 spent**
(two meshy-6 textured multi-image tasks at 30 each, remeshed in the same call),
437 left.

| file | what | size in the file | polys | placement |
|---|---|---|---|---|
| `campus-block.glb` | 4-storey banded bar, sedum roof, small PV array | ratio 1 : 0.40 : 0.37 (target 38 : 17 : 14 = 1 : 0.45 : 0.37) | 19 k | every `campus` footprint: scale to 38 × 17 m and the block's own height (11.9–17 m), turn to the long axis |
| `ncic.glb` | National Cyber Innovation Centre, one continuous sloping meadow roof | scaled to 60 m long it is 26.6 m wide and **22.4 m tall** | 29 k | one site, chosen by a written rule; **scale the height down to ~16 m** to match HBD's four storeys |

Both have their texture embedded (JPEG) and their origin at the bottom.
`viewer.html` loads both at real scale (serve this folder, then open it).

## Source views

`src/` holds the Codex drawings Meshy was given, made from HBD's own aerial and
courtyard renders with Dex's go-ahead. Those renders are third-party
copyright: **internal pitch work only**, do not publish these models.

- NCIC: `a1` + `a2`, two opposite three-quarter views.
- Campus: **`b2` only.** `b1` drew three storeys where `b2` drew four, and its
  glazed ground floor faded into the background; a mismatched pair makes a
  muddled model, and a plain bar gives little away from its hidden side.

## How they came out

**Good from 80–150 m**, which is what they are for: the campus block reads as
four banded storeys with a planted roof, and the NCIC's meadow slope is
unmistakable.

**Glass is the failure.** Meshy rebuilt the see-through glazing in the source
views as transparency and holes: jagged spikes along the campus block's glazed
ground floor, and a see-through, gappy glazed high end on the NCIC. Fine from
the air, not for eye level. **For the next type (glasshouse, homes), draw the
glazing as opaque dark reflective glass in the source views.** It costs
nothing and removes the one defect both models share.

For the web: 5.7 MB and 6.1 MB each, mostly the texture. Compress the textures
(KTX2 or WebP) before shipping.
