Use the built-in image_gen tool, sketch-to-render, to make a photograph of a place in
2045 that no camera has ever stood in, from a render of our own measured 3D model.

INPUT 1 is the geometry master: a render of our 3D model from the exact camera this
photograph is taken at, eye height 1.6 m above the measured terrain, 48 degree vertical
field of view. Every building edge, street width, tree position and ground line must keep
its place within about 20 px at 1280x720. Follow the plate for WHAT IS WHERE. Everything
you add — windows, doors, thresholds, planting, people, surfaces — must sit inside the
massing the plate gives you.
INPUT 2 is the approved adventurous target board for the homes: use it for materials and
character only, not layout.

THIS PLACE: a street in the new neighbourhood west of Cheltenham, 2045. It is measured,
not invented: 1,030 dwellings, terraces of 2.5 and 3 storeys with 5 and 17 m apartment
blocks among them, facing terraces 23 m apart, an open stormwater channel in the verge
8 m from the camera, street trees along both sides.

What the photograph must show, because the model says it is there:
- Brick and honey-timber terraces either side, eaves at 6.8 to 8.5 m, pitched roofs at
  45 degrees carrying solar glass on their sunward slopes, slate or dark standing seam
  on the rest.
- Front doors straight onto the street with a shallow defensible planted strip, not
  garages and not gated frontage. Goldsmith Street and Solarsiedlung are the precedents.
- The open water channel in the verge: a shallow, planted swale with a stone edge and
  reeds, not a kerbed gutter and not a river.
- Street trees, young to semi-mature, in a planted verge, not in tree pits in tarmac.
- A shared surface rather than a carriageway with white lines: block paving, a soft
  central drainage line, a few parked cars at the ends, cycles.
- People at true scale doing ordinary things at the end of a late summer afternoon:
  children, someone carrying shopping, a person on a doorstep, two people talking. Not a
  crowd, not a CGI family posed in the middle of the road.

Design direction: design excellence and realism, built precedents only (Goldsmith Street,
Solarsiedlung, Sara Kulturhus, Augustenborg). Never a corporate render, never an
illustration, never the developer's marketing style. No text or watermark. Real British
late-summer light at about 16:45, long soft shadows, hazy sky, no HDR glow.

Forbid: wide American-style road; front gardens with driveways and garages; identical
repeated house units; sky more than 30 per cent of frame; shiny black roofs on every
plane; a lifeless empty street; people as distant specks; any building taller or shorter
than the plate; any tree where the plate has none.

Output 1280x720 (whole-frame resize only, no crop or warp) to
experiments/002-living-map/generate/arrival/out/the-street.png. One generation plus at
most one correction pass if geometry drifts. Write
experiments/002-living-map/generate/arrival/out/the-street-notes.md with the prompt
verbatim, the passes, and an honest inspection: drift you can see against the plate, and
anything that reads as CGI.
