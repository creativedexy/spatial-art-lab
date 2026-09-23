# Jayse Hansen: HUD notes for the spider piece

Researched 22 Sep 2026 from jayse.io (work, spidey, home, about, press) plus two cross-checks. Anything not seen on his own site is marked **(unverified)**.

**TL;DR:** Jayse Hansen is the film FUI designer behind Iron Man's HUD, Spider-Man: Homecoming's suit UI and, most useful for you, the *computer-vision* HUDs in Tron: Ares. That last one is almost exactly your brief: a machine looking at real people and places, labelling them, measuring them and counting down. Steal his method, not his chrome: find the grid in the subject (he literally built Spidey's HUD grid from photographed spider webs), hang everything off a few anchors, and make every number mean something.

---

## 1. Who he is

| | |
|---|---|
| Name | Jayse Hansen (company: Jayse Design Group, Inc., per site footer) |
| Role | UI, HUD and hologram designer for film; "UI Design Lead/Director and UI System Architect" on Tron: Ares |
| Studios he designs through | Cantina Creative (Spider-Man: Homecoming, and Iron Man 3 per Cantina's own site); GMUNK Studio (Top Gun: Maverick, with Toros Köse and Nicolas Lopardo) |
| Films listed on his site | Tron: Ares, Iron Man, Spider-Man (Homecoming), Top Gun: Maverick, The Mitchells vs the Machines, X-Men Origins: Wolverine, Funny People, Rise of the Planet of the Apes, Wall Street: Money Never Sleeps, Transformers, 2012, The Avengers, Hunger Games, Mockingjay, Ender's Game, Need for Speed, Max Steel, Batman v Superman, Big Hero 6, Star Wars (R2-D2's map hologram), Bloodshot, Sight: Extended, Star Trek Picard, RoboCop, Guardians of the Galaxy, Blaze, Cloverfield, Pixels, Project 22, Selection, Star Trek Beyond, Superintelligence, The Suicide Squad, Red Notice |
| Real-world work (about page) | Future F-35 and NGAD cockpit UI (Navy, Northrop Grumman), SOCOM special-forces HUDs, Army Research Lab volumetric UI, Da Vinci surgical robot UI consulting, Meta AR spatial OS |
| Stated toolkit | Paper, Concepts and Procreate (iPad), Gravity Sketch and Shapes XR (VR sketching), Figma / Illustrator for vectors, After Effects and Rive for animation, Cinema 4D / Redshift, Element 3D, Unreal / Unity for interactive |

**Important:** of the ~35 titles on /work, only **Spider-Man** has a project page. The rest are plain text (not links). Tron: Ares, Top Gun: Maverick and a 2024 showreel are Vimeo embeds on the homepage. Frames below come from the Spidey page images and from those reels.

## 2. Projects (what is actually viewable)

| Project | Client / studio | Year | What the HUD does on screen | Tools stated |
|---|---|---|---|---|
| Spider-Man: Homecoming, suit HUD, web-slinger holos, 576-type web menu, holo-map, Iron Spider blueprints | Marvel / Columbia via Cantina Creative | 2017 (film year; not stated on page) | "Karen" suit OS meant to *overwhelm* Peter. HUD built on a spider-web grid; view modes (thermal, FLIR, synthetic aperture), vitals, web-fluid gauges, drone and recon windows, a tracker beacon on a holographic map | VR sketching (Gravity Sketch, Tilt Brush), pen, Procreate, then Illustrator, Cinema 4D, After Effects |
| Tron: Ares, Ares and Athena computer-vision HUDs | Disney | 2025 (film year; reel uploaded Feb 2026) | The programs *see* the real world: tracking boxes on people, name and rank tags, biometric readouts, material "surface response" analysis, a "De-resolution" countdown, voxelised faces and cities | Not stated on site. A YouTube talk titles it "Figma to After Effects with Jayse Hansen & Darby Faccinto" (unverified detail) |
| Top Gun: Maverick, Darkstar cockpit and command centre | Paramount via GMUNK Studio, with Lockheed Martin Skunk Works | 2022 | Cockpit MFDs, radar, attitude and command-centre storytelling screens | Not stated |
| Iron Man / Avengers HUD (in 2024 reel) | Marvel | 2008 to 2013 era | The helmet-cam face HUD: rings around the eye, mirrored numeric readouts, vertical tape scales | Not stated on site |
| The Mitchells vs the Machines | Netflix / Sony Animation | 2021 | Robot "language" and HUDs (per press list: NAB 2022 talk) | Adobe CC (per talk title) |

## 3. The design language, concretely

**Typography**
- Square-shouldered, wide, technical sans in ALL CAPS for labels (FLIR/HI-CON, VIEW MODES, DE-RESOLUTION IMMINENT). Exact face not stated **(unverified)**; it reads like the Eurostile / Industry family. His own website sets everything in **Industry** at **0.7em tracking**, which is the same instinct.
- Two sizes do almost all the work: tiny labels (roughly 1 to 1.5% of frame height) and one oversized hero number (16:48 -37, 355MM, 92% 43% 21%). Nothing in between.
- Units go small and raised after the number (355<sub>MM</sub>, 76<sub>%</sub>). Separators are typographic: `::`, `//`, `|`, `>>>REGEN<<<`.
- Labels are real-sounding but in-world: "DIFFUSIVE ADHESION :: 79.7%", "STRAND WIDTH :: 42mm", "SURFACE RESPONSE | LEATHER".

**Grid and layout**
- He builds the grid before any element. Spidey: "Data-heavy designs don't click until the grid does." The grid came from **photographed spider webs** (angular radial web, then a softer round one; water drops on the threads became the dot patterns).
- **Visual anchors**: he plots a few points and "hangs" everything off them.
- Frame the edges, keep the centre open. Heavy clusters sit left and right; the subject gets the middle third.
- Z-depth stacking: layers at different depths so the grid "becomes a tunnel". Grouping by depth instead of by boxes.

**Line and colour**
- Hairlines (1 px at 1080p and finer), a slightly heavier line only on the one element that matters.
- Monochrome UI plus **one alarm colour**. Spidey: cyan-steel with red accents only for armed or active states. Tron: all red-orange, brighter orange only for the hero readout.
- Glow and bloom, chromatic fringing, lens dirt and defocus so the UI feels photographed, not pasted on.

**How data is drawn**
- Brackets and corner ticks instead of full boxes. Hexagonal and radial icons.
- Leader lines that bend once (a 45 degree elbow), ending in a dot or small tick. Spidey's anatomy board is almost all elbowed callouts.
- Vertical tape scales with small ticks on the edges of frame (Iron Man, Tron).
- Readout stacks: 5 to 8 lines of tiny caps text, left-aligned, with a thin vertical rule on the left.
- Point constellations: scattered dot fields that thin out with distance (Tron lock-on frame).
- Geometry diagrams: overlapping circles joined by straight lines with angle labels (Tron surface-analysis frame).
- Zoom windows: a small box on the subject, lines fanning out to a larger magnified inset (Tron lock-on).

**Motion (from the reels)**
- Elements attach along the grid lines and animate in and out along them (his own words about Spidey's web-lines).
- Counters: timecodes that tick with small fast digits after the big slow ones (16:48 -37).
- Resolution as a state: the image breaks into blocks and voxels, then resolves (Tron "de-resolution").
- Scan and populate: a dot field appears first, then boxes, then labels. Jitter on the smallest text only.

**Density vs negative space**
- Very dense at the edges, almost empty in the centre. The dense bits are small enough to read as texture; only two or three things are legible at a glance.

## 4. Rules you can copy (each tied to a frame)

| # | Rule | Where he does it |
|---|---|---|
| 1 | **Find the grid in the subject.** Photograph the real thing, trace its structure, make that the layout grid. | Spidey HUD grid traced from spider webs (`jayse-spidey-web-line-reference.jpg`, `jayse-spidey-web-grid.jpg`) |
| 2 | **Anchors first, elements second.** Plot 5 to 8 anchor points, hang every widget off one. | Spidey "Visual Anchors" section |
| 3 | **Edges dense, centre empty.** Subject owns the middle third. | `jayse-spidey-hud-full.jpg`, `jayse-tron-ares-lock-on.jpg` |
| 4 | **One colour for the system, one for alarm.** | Spidey cyan plus red "PRIMED"/"ACTIVE"; Tron red with orange hero numbers |
| 5 | **Two type sizes only:** tiny caps labels, one huge number. | 355MM in `jayse-spidey-view-modes.jpg`; 16:48 in `jayse-tron-ares-lock-on.jpg` |
| 6 | **Numbers carry units and precision.** Small raised units, trailing fast digits. | "16:48 -37", "92% 43% 21%" |
| 7 | **Name things in-world.** Labels describe the subject's physics, not generic sci-fi. | "STRAND WIDTH :: 42mm", "DIFFUSIVE ADHESION" (`jayse-spidey-slinger-ui.jpg`) |
| 8 | **Brackets not boxes.** Corner ticks imply a frame. | Recon and UAV windows (`jayse-spidey-hud-components.jpg`) |
| 9 | **Elbowed leader lines to a dot.** One bend, then horizontal. | Anatomy and components boards |
| 10 | **Zoom inset:** small box on target, fan lines to a magnified window. | `jayse-tron-ares-lock-on.jpg` |
| 11 | **Dots before lines, lines before words.** Build-on order signals the machine thinking. | Tron reel dot fields that resolve into boxes and labels |
| 12 | **Resolution is a state.** Degrade and rebuild the image (blocks, voxels) as the machine's confidence changes. | `jayse-tron-ares-countdown.jpg` |
| 13 | **Material analysis as a readout.** Stack "surface response" data next to a geometric diagram. | `jayse-tron-ares-surface-analysis.jpg` |
| 14 | **Photograph the UI.** Bloom, fringing, defocus and depth layering so it sits in the lens. | `jayse-spidey-web-fluid.jpg`, `jayse-iron-man-hud.jpg` |
| 15 | **Write the manual.** A 50+ page "suit manual" made the whole OS coherent. For you: a one-page spec of what the machine measures. | Spidey "The Spidey Manual" |

## 5. The field and the words

**Around him (verified only)**
- **Cantina Creative** (LA): the VFX/design house he worked through on Spider-Man: Homecoming; Cantina also credits him on Iron Man 3 HUDs.
- **GMUNK Studio**: he designed Top Gun: Maverick screens there with Toros Köse and Nicolas Lopardo.
- **Territory Studio** (London): screen graphics for Blade Runner 2049 and Ex Machina.
- **Perception** (New York): Marvel technology and UI, notably Black Panther: Wakanda Forever's vibranium-sand interfaces.
- **Darby Faccinto**: animated his Spidey slinger breakdown and worked on Tron: Ares UI.
- **Carolyn Farino**: UX designer, co-organised the 576 web types with him.
- **Ash Thorp** (unverified link): his press page lists a "Collective Podcast" where "Ash and Jayse chat"; that is very likely Ash Thorp's podcast, not confirmed.
- **"Rudd"**: nothing found connecting a Rudd to this field. Dropped.

**Vocabulary**

| Term | Meaning |
|---|---|
| FUI | Fictional (or futuristic) user interface: screens designed for film and games, not for use |
| HUD | Heads-up display: data overlaid on the view, in world space or screen space |
| Diegetic UI | UI that exists inside the story world (the character sees it), as opposed to overlay for the audience |
| Callout | A label attached to a point by a leader line |
| Reticle | Aiming or lock mark: crosshair, brackets or rings on a target |
| Readout | A block of live values (text or numbers) |
| Telemetry | Streamed measurements over time (speed, heading, heart rate) |
| Boot sequence | The build-on animation as a UI powers up |
| Lock-on | The reticle snapping and tightening onto a target, usually with a confirm flash |
| Tape | A vertical or horizontal sliding scale with ticks (altitude, speed) |

## 6. Five HUD moves for a tracked spider on moss

Premise: the machine is *studying* the spider, not targeting it. Keep his discipline (edges dense, centre open, one alarm colour), swap his vocabulary for biology.

**1. Web-grid from the real web**
What: photograph or scan a real orb web, trace it, and use it as the HUD's layout grid and as a faint depth layer behind everything.
Build (Blender): trace the web as a curve, Geometry Nodes: *Curve to Points* at threads' crossings gives you anchor points; *Instance on Points* for tick marks. Render as a separate view layer with Emission shader.
Build (TouchDesigner): import the traced SVG into a *Script SOP* or *Trace SOP* from a thresholded photo TOP, *Line MAT* for hairlines, anchors from *Point SOP* positions exported to CHOPs via *SOP to CHOP*.

**2. Lock-on brackets on the body, tightening as confidence rises**
What: four corner brackets appear wide and loose, then snap in to the cephalothorax and abdomen with one flash, plus a joint ID tag (e.g. `ARANEAE :: ID 07`).
Build (TouchDesigner): tracked position from your skeleton data (CHOP), a *Filter CHOP* or *Lag CHOP* to ease it, bracket scale driven by a confidence channel through a *Math CHOP*; draw brackets in a *Geometry COMP* with *Line SOP*s, or as 2D in a *Rectangle TOP* masked to corners. Flash with a *Trigger CHOP*.
Build (Blender): Empty parented to the tracked bone, brackets as Grease Pencil or curve objects with a *Track To* constraint to camera; animate scale with a Drivers expression on a custom "confidence" property.

**3. Elbowed callouts with real measurements on each leg joint**
What: leader lines from 2 or 3 leg joints to readouts at the frame edge: `L2 FEMUR :: 4.1mm`, `STRIDE 11.3mm`, `CADENCE 3.2Hz`. Only the joint currently moving is bright.
Build (TouchDesigner): joint positions from the skeleton CHOP, projected to screen via *Object CHOP* or a camera matrix in a *Script CHOP*; *Line SOP* with a mid-point for the 45 degree elbow; text via *Text TOP* or *Text SOP* with values from *CHOP Execute* formatting to fixed decimals. Brightness from joint velocity (*Slope CHOP*).
Build (Blender): Geometry Nodes on the armature: sample bone positions (*Object Info* per bone empty), build a 3 point polyline, *String to Curves* for labels; values via drivers into a *Value* node.

**4. Telemetry sidebar with a timecode and a stride trace**
What: one edge of frame carries a vertical readout stack (species guess, body length, heading, substrate: `MOSS / BRYOPHYTA`, humidity) plus a small scrolling line graph of leg cadence and a big timecode with fast trailing digits.
Build (TouchDesigner): *Trail CHOP* of the cadence channel into *CHOP to SOP* for the graph, or *CHOP to TOP* for a strip. Timecode from *Timer CHOP* formatted in a *Text TOP*. Composite with *Over TOP*; add *Bloom* (*Blur* plus *Add*) and a slight *Chromatic* offset via *Displace TOP*.
Build (Blender): easiest in the compositor or as a 2D overlay made in After Effects from exported CSV. Pure Blender: Text objects with drivers, and a Geometry Nodes curve built from a baked F-curve.

**5. Scan sweep that resolves the moss into points, then back to image**
What: a slow plane sweeps across the frame; behind it the moss becomes a point cloud with a dot field thinning by distance (his Tron dot constellations), in front it is still photographic. Use it as the "machine looking" beat, and pair it with a `SURFACE RESPONSE | MOSS` readout stack (his Tron surface-analysis frame).
Build (TouchDesigner): depth or point cloud into a *Point File In TOP* or from a camera via *Kinect / Azure TOP*; *Instance* points in a *Geometry COMP*; sweep position as an LFO or *Pattern CHOP* feeding a GLSL MAT that compares each point's X to the sweep and mixes image vs points. Or 2D: *Ramp TOP* as mask into *Switch* / *Cross TOP* between the photo and a rendered points TOP.
Build (Blender): Geometry Nodes *Mesh to Points* on the moss scan, *Delete Geometry* by comparing position to an animated Empty's X (Object Info), plus the reverse selection shown as the textured mesh. Emission on points; compositor Glare node for bloom.

## 7. Frames captured

All in `inspiration/images/`, 1400 px max, each checked by eye:

| File | What it shows |
|---|---|
| `jayse-tron-ares-lock-on.jpg` | Dot field, zoom inset on a motorcyclist, biometric stack, De-resolution timecode |
| `jayse-tron-ares-crowd-scan.jpg` | Machine vision over a real crowd: name and rank tags, particle overlay, timecode |
| `jayse-tron-ares-surface-analysis.jpg` | "Surface response" material readouts beside a circle-and-line geometry diagram |
| `jayse-tron-ares-countdown.jpg` | Face degraded into blocks, reticle on forehead, "De-resolution imminent" countdown |
| `jayse-iron-man-hud.jpg` | Classic face-cam HUD: eye ring, mirrored numerics, tape scale |
| `jayse-spidey-hud-full.jpg` | Full Spidey HUD: centre horizon, edge clusters, tracker, vitals |
| `jayse-spidey-view-modes.jpg` | Detail: view-mode list, leader lines, 355MM hero number |
| `jayse-spidey-web-fluid.jpg` | Web-fluid payload gauges, red alarm accents, heavy lens treatment |
| `jayse-spidey-hud-components.jpg` | Annotated component sheet: elbowed callouts, bracket windows, icon set |
| `jayse-spidey-web-grid.jpg` | The angular spider-web layout grid with element placement |
| `jayse-spidey-web-line-reference.jpg` | His real web-line reference photo that drove the shape language |
| `jayse-spidey-slinger-ui.jpg` | Slinger UI: STRAND WIDTH, DIFFUSIVE ADHESION, hex icons |

Sources: jayse.io/work, /work/spidey, /, /about, /press; [Cantina Creative, Iron Man 3](https://www.cantinacreative.com/film/iron-man-3); [Territory Studio, Blade Runner 2049](https://territorystudio.com/project/blade-runner-2049/); [Perception, Wakanda Forever](https://www.experienceperception.com/work/black-panther-wakanda-forever-technology/); [Tron: Ares workflow talk (YouTube)](https://www.youtube.com/watch?v=1IHZ6LpSHik).
