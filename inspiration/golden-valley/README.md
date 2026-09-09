# Golden Valley — reference imagery

Collected 2026-09-09 for Experiment 002. **Third-party copyright, held as private
reference only.** Do not republish, do not ship in any deliverable, do not feed as a
style reference into anything that leaves this machine without checking first.

| Folder | Source | What it is |
|---|---|---|
| `official/` | goldenvalleyuk.com (Squarespace CDN) | The scheme's own hero images, ~2500px |
| `grimshaw/` | grimshaw.global — masterplan architects | Masterplan drawings and CGI |
| `hbd/` | static.hbd.co.uk — HBD, the developer | **Full-resolution originals, 5–18 MB** |

## The one that changes the brief: `official/aerial-03.jpg`

It is not a CGI world. It is a **photomontage**: a real aerial photograph of west
Cheltenham — GCHQ unmistakable at bottom right, the fields to the west, the same hill —
with the development composited into it.

Two consequences:

1. **Their visual language is our pipeline's shape.** Real measured place as substrate,
   authored buildings painted on. That is what rung 6 demonstrated, arrived at from the
   other direction.
2. **It is very close to our camera A.** Same hill, same GCHQ, same field pattern. It is
   free ground truth for how well our measured structure matches the real place — a
   direct accuracy check against a photograph, costing nothing.

## Art direction, read off the images rather than described

- Pale timber and buff stone, horizontal banding, deep window reveals, slatted soffits
- **Green and wildflower roofs are the signature move** — one whole building is a sloping
  meadow. PV arrays on the flat roofs
- Landscape-led: retained veteran oaks at full maturity, wildflower verges, SuDS ponds,
  angular buff-sett paving cutting across meadow
- Heavily populated. People are the scale reference in every frame
- Bright summer, high sun, blue sky with cumulus, Severn Vale and the Welsh hills on the
  far horizon — a horizon our terrain already has

Grimshaw's stated strategy: "regenerative community", native habitat mosaics, existing
waterways and soil "left in better shape".

## The overlay test, run 9 Sep

`overlay-test-v001.png` — their hero above, our render below, camera matched by
eye. **Internal only, like everything else in this folder.**

Camera: local `(141, 505, 757)` looking at `(-201, 327)`, 47 deg vertical field
of view — that is 141 m east and 757 m south of the box centre, 505 m up,
looking north-north-west. Reproduce with:

```
python3 -m http.server 8137   # in experiments/002-living-map
open "…/passes/index.html?pass=beauty&size=1500,825&cam=141,505,757&look=-201,327&fov=47"
```

**What it shows.** GCHQ, the Chelt's woodland belt, the Hesters Way and Benhall
street grain, the field pattern west of the site and the A40 corridor all land
in the same relationships in both images. The structure is the same place.

**What it also shows, and this is the useful part.** Three gaps, all of them
things to do rather than things wrong:

1. **The development is missing from ours.** Their centre-left is the scheme;
   ours is a caravan park and an empty field. That is Phase 5, and this image
   is the argument for it.
2. **Our box is smaller than their framing.** The photograph runs off our data
   at the top left — they shot 3.5 x 2.6 km, we hold 2 x 2. A town-scale map
   needs a bigger box regardless of anything else.
3. **The match is eyeballed, not solved.** GCHQ's courtyard lands about 95 px
   left and 30 px high in a 1500 px frame, which is roughly 60 m of apparent
   ground offset — two or three degrees of camera error. A proper solve needs
   correspondences the photograph cannot give: the doughnut is clipped by the
   right edge, so its centre has to be guessed. Worth doing properly against
   `official/aerial.jpg` if the comparison is ever going in front of anyone.
