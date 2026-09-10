# Golden Valley: from approved look to a working experience

10 Sep 2026. Dex approved the 2045 look after brief 003 and set five
workstreams: closer shots, Meshy models of the key buildings, combining with
the existing Golden Valley assets, a video plan, and the interactive web work.
No far-field terrain. Phase: **Develop → Deliver.**

The rules that still hold: no empty frames (a place of interest, buildings and
people in every one); "before" frames parked; transitions are not a focus
(no blur zooms; a plain cut is enough);
every paid run needs Dex's yes with the bill stated.

## 1. Closer shots: one works now, the campus needs step 2 first

Three close plates rendered from the 2045 map at 80–150 m.

| plate | rule | why |
|---|---|---|
| GCHQ with its meadow roof | **passes, done** | the ring fills the frame; no measurable drift |
| campus centre, campus cluster | **fails** | four blank slabs far apart; grass plus sky is over half the frame |
| glasshouse quarter | **fails** | the glasshouse is one thin block in an orchard |

That failure is the finding. From 400 m up the rule-based scheme reads as a
town; from 100 m it is sparse (built area is capped at a third) and its blocks
are featureless extrusions with plain grass between them. **Closer shots of the
campus need real buildings and designed ground between them.** Prompting more
will not help, because the plate does not contain what the rule asks for.

## 2. Meshy: a kit, not a set of one-offs

Model **types** and place them on the scheme's own footprints, rather than
modelling individual buildings. One model, many placements, and it carries
over to the next site.

| # | model | placements | why |
|---|---|---|---|
| a | **the National Cyber Innovation Centre**, the sloping meadow-roof building | 1 | the signature; the campus's place of interest up close |
| b | **campus courtyard block**, 4–5 storeys, timber and buff stone, horizontal banding | 20 campus footprints | turns the blank slabs into architecture |
| c | **glasshouse** | 3 | the glasshouse quarter becomes a subject |
| d | **terrace home**, brick and timber, gabled | 70 home footprints | optional; homes read fine from the air already |

**GCHQ is not on the list.** The measured ring is better than any generated
model of it.

**How:** Codex (free) draws each type clean and isolated: a three-quarter view
plus a second angle, neutral ground, in the approved 2045 materials. Then
`meshy_multi_image_to_3d` (meshy-6, textured), then `meshy_remesh` down to a
web budget, then GLB into the map, scaled and turned to each footprint in
`gv-2045-buildings.json`.

**Cost:** 497 credits available. meshy-6 textured is 30 credits a model and a
remesh is 5. A and b first as the test: **70 credits**. All four: **140**.

## 3. Using the existing Golden Valley assets

`inspiration/golden-valley/` holds the developer's and Grimshaw's renders.
The innovation centre in the HBD aerial *is* building (a), so those images are
the best reference there is for what it should look like.

- **Use them as reference for the Codex drawings that feed Meshy**, so model
  (a) is recognisably the scheme's own building rather than a lookalike.
- **Copyright:** they are HBD's and Grimshaw's work. Models derived from them
  are for internal pitch work; do not publish or ship them without permission.
  The queue's README says to ask before feeding these to a generator, and Dex
  has now asked for it, so this is the one sanctioned use.

## 4. Video: life inside approved frames, never travel between them

Transitions are not a focus and get no generated video, so generated video
has one job: **bring an approved still to life**. Locked camera, 5 s, loops.

| clip | from | what moves |
|---|---|---|
| agrivoltaics | 003 C | the tractor between the panel rows, workers, the crop in the wind |
| GCHQ | 002 | traffic on the perimeter road, people walking to the entrance |
| campus courtyards | 003 B | people crossing the courtyards, cyclists on the streets |

- **Engine:** `fal-ai/kling-video/v3/pro/image-to-video`, the approved photo as
  both `start_image_url` and `end_image_url` so the clip loops back to where it
  started, `generate_audio: false`, `duration: 5`.
- **Prompt:** 40–70 words, camera locked off, name whatever must move as
  arriving in the frame (the routing skill's rules, each learned from a failed
  take).
- **Check by numbers, not by eye:** per-frame mean luminance and the drift
  against frame 0, as the routing skill does it.
- **Cost:** $0.112/s × 5 s = **$0.56 a clip, $1.68 for all three (about
  £1.30).** Not spent until Dex says yes.

## 5. The interactive web experience

The living map already exists (the three.js map in `golden-valley/`, Session
D's hotspot player, the 2045 toggle). The experience is the join between the
map and the approved photos:

```
live map (today) --2045 toggle sweeps the future across the vale-->
  click a place of interest (GCHQ, the campus, the agrivoltaic fields)
  --> camera flies to that photo's own map camera        (the plates ARE map cameras)
  --> the approved photo (or its loop) over the map, plain crossfade
  --> back out to the live map
```

Every generated photo came from a map camera, so the handover always lands on
a matched viewpoint. No transition effects: Dex ruled blur zooms out on 10 Sep,
and the play area built to tune one has been deleted.

**Who builds it:** the main session, which owns the map code: see
`experiments/002-living-map/MAIN-SESSION-TASK-001.md`. The local session
supplies photos, loops and GLBs.

## Order

1. GCHQ close-up: **done**, `generate/close-2045/out/gchq-meadow-photo.png`. One pass, no correction; the ring and courtyard held within about 4 px (Codex) and the ring's top edge sits on its lock by eye. The first frame with no measurable drift: up close, the ring fills the frame and there is nowhere to drift to.
2. Meshy a + b: **approved by Dex, 70 credits**, then the campus close-ups pass.
3. Video loops (**$1.68, awaiting Dex's yes**).
4. Web build in the map: main session, task 001.
