# GCHQ photographic conversion

## Passes
Two passes using the built-in image generation tool. Original surveyed plate used as the geometry input. Pass 2 also used pass 1 as a photographic reference. Saved pass 2 as gchq-photo.png at its native 1672×941 resolution.

Pass 1 produced photographic office architecture, dry planted courtyard, full parking ranks, road vehicles and pedestrians. Its horizon was approximately y202 after normalization, residual +28 px. The requested single regeneration explicitly corrected the horizon to y174 and repeated the geometry locks. Pass 2 improves the horizon but shifts the main building upward. No further regeneration was performed, following the requested one-retry limit.

## Final measurements
Manual visual edge measurements on the generated image, normalized by x×1280/1672 and y×720/941. Approximate precision ±3 px for architectural edges and ±4 px for distant horizon; these are visual estimates, not segmentation-derived survey measurements. Boxes use (left, top, right, bottom). Glazing/roof aperture edges define the courtyard box, not the foliage.

| Feature | Requested | Measured final | Residual final minus requested |
|---|---|---|---|
| Ring box | (312,285,1064,539) | (315,262,1064,525) | (+3,-23,0,-14) px |
| Courtyard box | (529,307,832,365) | (525,285,834,349) | (-4,-22,+2,-16) px |
| Horizon | y174 | approximately y178 | +4 px |

Native visual picks: ring approximately (411,343,1390,686); courtyard approximately (686,373,1089,456); flat horizon approximately y232. Ring width residual -3 px, height residual +9 px. Courtyard width residual +6 px, height residual +6 px. The courtyard is not materially enlarged, but its placement exceeds the ~15 px tolerance. Final is NOT a complete geometry-lock pass.

## Named failure inspection
1. **Courtyard filled with water or enlarged:** dry grass, planting and trees; no water. Aperture width/height approximately 309×64 versus locked 303×58. Small size drift, with vertical-position failure documented above.
2. **Ring turned into shed, stadium or roundabout:** absent. Legible multi-storey circular office building, ribbed pale metal annular roof, glazed bands, masonry base and continuous courtyard glazing.
3. **Landscape invented above horizon:** no hills or broad landscape above y174. Flat distant horizon remains approximately 4 px too low; individual tree crowns protrude slightly above the horizon level.
4. **Car parks left empty:** absent. Dense individual cars in parking ranks on both sides and behind the ring. Road vehicles and pedestrians are visible.

GCHQ remains the focal point; buildings read as architecture and weekday activity is visible. Empty sky occupies about one quarter of the frame; combined empty ground and sky visually remain below one half. Both foreground annexes and far-left pitched annex remain, but the foreground annex facades/roof details have drifted from the surveyed shapes. Full compliance with all geometry locks is not claimed. Cloud coverage is more extensive than the requested few small cumulus.

## Final prompt
Use case: sketch-to-render, precision material edit. Input image is the surveyed edit target, not a loose reference. Make this exact view a convincing real photograph of GCHQ, Cheltenham, from a light aircraft on a working weekday afternoon. Output 1280x720 landscape.
GEOMETRY LOCKS in normalized 1280x720 pixels: preserve ring silhouette x312–1064 y285–539, absolutely no shift, resizing or raising. Preserve small elliptical courtyard aperture EXACTLY x529–832 y307–365: only 303px wide and 58px high. Keep the broad annular roof and its existing outline and entrance projection. Courtyard is DRY planting, grass and mature trees, NEVER water. Continuous glass inner wall. Ring is a 14.8m tall circular OFFICE BUILDING, pale white-grey finely ribbed metal annular roof, horizontal glazed office bands over brick base. Not a shed, stadium, arena or roundabout.
Horizon lock y174, sky above it with no added landscape above y174. Keep settlement low and flat, distant rooflines at y209 and bases y228. Existing houses get red brick and grey slate/red clay roofs. Do not introduce hills or extra buildings. Keep all existing annex geometry: left annex centre x357 roof y582 base y654; centre-right centre x924 roof y594 base y669; pitched-roof annex at far left. Preserve camera, crop, perspective and all building outlines.
MATERIALS LIGHT LIFE: late summer, warm low afternoon sunshine from upper left with long shadows matching plate direction. Blue sky, few small cumulus, clear air, no haze fog bloom. Real mature oaks and limes in full leaf replacing faceted trees. Worn asphalt, painted parking bays and road markings. Car parks surrounding ring FULL of individually identifiable cars parked in orderly ranks, clearly visible on left and right and through trees behind ring. Several vehicles driving perimeter road. Scatter of small realistic people walking between foreground annexes and entrance. Fine realistic architectural materials, glazing reflections, brick texture, weathering, photographic exposure and detail rather than CGI.
Rule check: GCHQ focal point, legible office architecture, busy weekday life. Less than half frame empty sky/ground. Empty parking areas forbidden. No text logos watermark. Change materials/light/life only, retain precise surveyed ring and aperture pixel boundaries.
CORRECTION PASS: The previous result's horizon was y202 instead of y174. Set the flat distant land/sky boundary to EXACTLY y174 (24.17% of image height), without moving ANY foreground architecture. No land above that boundary, no hills. Use original surveyed plate for all building geometry. The ring MUST still occupy x312–1064,y285–539 and aperture x529–832,y307–365, measured after scaling to1280x720. Keep aperture boundary exact: do not expand it for trees. Keep full parking ranks, traffic and pedestrians and photographic materials. Only a FEW SMALL clouds, not a crowded cloud bank. Preserve annex shapes from original.

