# Spatial art lab — learning through small works

Created 7 September 2026. Working assumption: beginner, three 60–90 minute sessions per week. Treat each stage as a sprint, not a deadline; the complete path is roughly 8–12 weeks. Blender and TouchDesigner are downloaded; Meshy access is user-confirmed. World Labs access, machine performance and installed app versions still need checking in the first session.

## Creative direction

Our starting territory is atmospheric, spatial and tactile: wisps in darkness, scanned nature, distressed point clouds, cinematic metal and objects that reveal their construction. This is an interpretation of the supplied references, open to revision as we make work. Keep two palettes in play: graphite / bone / moss for environments, and steel / ice / black for objects. Use one restrained accent rather than default rainbow particles.

Three connected bodies of work:
- **Ghost ecologies:** caves, botanical fragments and cosmic fields that breathe or dissolve.
- **Impossible artefacts:** an invented relic or instrument, studied as a physical object, then disassembled.
- **World as interface:** the artefact lives in a small navigable environment with three meaningful viewpoints.

Aim for a final miniature exhibition: one polished still, one 10–15 second film, and one interactive scene sharing a visual language.

## AI-first working method

Start every experiment with intent → three alternatives → one cheap proof → manual control → critique → saved result. AI proposes compositions, generates original asset concepts, helps write Blender Python and browser code, explains TouchDesigner networks and diagnoses specific errors. You choose the silhouette, camera, material, timing and final result.

For each session: 10 minutes reference analysis, 15 minutes targeted learning, 45 minutes making, 15 minutes comparison and capture. Change one variable at a time. Save the prompt, tool/model version, seed if available, input image, selected output, time and credits used. Keep generated source assets intact and edit copies. End with one visible result and one thing you can now change without AI.

Do not attempt the full toolchain in the first piece. Use a Meshy mesh for editable objects; a World Labs splat for spatial appearance; Blender for controlled geometry/cameras/lighting; TouchDesigner for live image/signal systems; a browser for distribution and interaction. AI video is a separate route for fast motion studies: a compelling film does not establish that editable 3D geometry exists.

## Sprint sequence

| Sprint | Make | Learn just enough | AI contribution | Complete when |
|---|---|---|---|---|
| 0 · one session | A black-and-white moving texture in TouchDesigner; a lit primitive in Blender | Navigate, connect nodes, move camera, save/reopen | Explain each control and record installed versions | Both source files reopen; save one image from each |
| 1 · 2–3 sessions | **Cosmic breath:** 10-second atmospheric motion sketch | TOPs, noise, levels, transforms; slow CHOP modulation | Suggest a minimal network and three controlled variants | Three looks saved; density, speed and contrast remain independently adjustable |
| 2 · 3 sessions | **Impossible artefact:** one original object | Meshy import; Blender transforms, normals, materials, lighting | Generate three concept directions, choose one for Meshy; help clean up | A textured object looks sound from front, side and back, with one final still |
| 3 · 3 sessions | **Anatomy of an artefact:** exploded assembly | Separate objects, origins, keyframes, easing, camera | Scaffold a reversible animation script with exposed distances | 3–5 distinct components separate and return in a 6–10 second loop |
| 4 · 3 sessions | **Ghost ecology:** a breathing point-field study | TD 3D rendering, instancing and signals; points versus surfaces | Explain the data path and help map audio or a test signal | A 15-second capture plus a live density/displacement control; audio optional |
| 5 · 3–4 sessions | **Memory chamber:** one World Labs spatial scene | World generation, viewpoints, splats versus meshes, export | Draft spatial prompts and a consistent three-view shot list | Inspect three separated viewpoints; export one supported format; log holes and distortions |
| 6 · 3–4 sessions | **World as interface:** one interactive object or room | GLB loading, camera controls, lighting, basic performance; Spark for splats | Implement a small Three.js viewer and one effect | Three viewpoints or one explode slider work; usable fallback and keyboard control |
| 7 · 3 sessions | **Miniature exhibition** | Art direction, editing, presentation and optimisation | Compare versions against the brief; package the selected work | Still + short film + local interactive scene, with source files and a short process note |

### Sprint 0: first session

1. Record Blender and TD versions, computer/chip, RAM, available GPU information and license tier. Open both apps and verify their basic examples render. Start at a modest preview resolution; benchmark before promising frame rates.
2. In TD, make a Noise TOP → Level TOP → Null TOP. Animate the noise slowly using a time expression or a CHOP appropriate to the installed version. Learn what each parameter changes. This is a first texture study, not yet a reconstruction of Dimitri's work.
3. In Blender, use a sphere or bevelled cube, one area light, a dark world and a camera. Move the light through three positions, save three stills.
4. Pick the most interesting result, name it and save the source. Log the one setting that made the biggest difference.

### Sprint 1: Cosmic breath

Reference: I01. Begin with a 2D noise field and contrast. Add slow transform and displacement only once the base looks good. Introduce feedback later as a separate study; make it resettable to prevent a blown-out image. Compare sparse, cloudy and filament-like results. A perfectly seamless loop is a stretch goal; the minimum is a short controlled motion sketch. Learn the official TD 101–103 material as needed rather than watching the entire course first.

### Sprint 2: Impossible artefact

Invent a simple weathered instrument with a strong silhouette. Generate at most three concept candidates, then choose one for a single Meshy trial. Prefer an isolated subject with clear shape and restrained reflective effects. Check the back and underside rather than judging only the input view. Export GLB where available and import in Blender; inspect scale, orientation, shading, textures and triangle count. Keep the original and a cleaned version. If geometry is poor, simplify the design or build the major form from primitives before spending more credits.

### Sprint 3: Exploded assembly

Reference: I05/I06. Start with a shell, core and two rings as separate Blender objects. A generated single-piece mesh is not automatically a functional assembly. Model the main parts separately if needed. Define assembled positions and exploded offsets, expose one 0–1 control, and animate out / hold / return. Bake complex materials to portable textures if the later browser export needs them. First prove the effect in Blender; add scroll control only after the GLB works in a viewer.

### Sprint 4: Ghost ecology

References: I02/I03. First make a procedural field or sample points from your own simple mesh. Use a slow signal before introducing audio. Then map a smoothed audio envelope to one variable, with a clamp and a silent-state default. A point cloud is a collection of samples; a Gaussian splat scene stores additional appearance/shape information. Do not assume a splat PLY can be imported as an ordinary coloured point cloud with an identical result. Browser splat manipulation can be the alternate route if TD import becomes the main obstacle.

### Sprint 5: Memory chamber

Use World Labs / Marble for a single cave-like chamber, with one strong light direction, a clear floor and one focal opening. Generate a world from an original concept if your account supports it. Check near/far surfaces from three different positions, not just the original camera. Export a low-resolution splat first for the browser route; request a high-quality mesh only when you need editable surfaces in Blender. A collider mesh is for simplified collision, not final appearance. Check axes, scale, textures and file size on import. If access or credits are unavailable, prototype the same room with Blender primitives; keep the aesthetic and camera experiment moving.

### Sprint 6: A small interactive scene

Choose one branch initially: (A) the artefact GLB with an explode control; (B) the world splat with three camera stops. Mesh route: Blender → GLB → Three.js. Splat route: Marble export → Spark / Three.js. Spark is developed by World Labs and supports programmable splat effects. Keep HTML labels outside the render canvas, add a static poster while loading, a reduced-motion mode, a reset control and keyboard access. Record FPS, asset size and load time on the actual target device; reduce textures, detail or splat count if needed. Treat 30 FPS and a mesh download around 10 MB as provisional prototype goals, not vendor limits or promises for splat scenes.

## Prompts we can reuse

**Art director:** “Here is the reference and my current result. Separate what you can observe from inferred technique. Propose three changes to composition, material or motion. Preserve the sparse, atmospheric mood. Pick the single highest-impact change for a beginner.”

**Blender collaborator:** “For Blender [version], help me build [small outcome]. Explain the scene structure first. If scripting helps, create named objects in a new collection, expose the useful parameters and avoid deleting existing work. Tell me what to inspect visually and what I should learn to change manually.”

**TouchDesigner tutor:** “For TouchDesigner [build], build the smallest network for [effect]. List each operator, connection and parameter, explaining its purpose. Use a test signal before audio. Give one checkpoint after each addition and ask me to predict what the next parameter change will do.”

**World brief:** “An intimate eroded stone chamber with a clear central floor, moss in the seams, one opening admitting cold daylight, deep but readable shadows, a coherent walkable layout, restrained graphite and moss palette. Three viewpoints should reveal consistent architecture.”

**Critique:** “Score intent, composition, material, motion and control from 1–5. What is accidental? What should we keep? Suggest one 20-minute next experiment rather than a complete rebuild.”

## Constraints and progression

Use existing access first. A planning cap is three AI concept images and one 3D/world trial per experiment, then review before another batch. Actual costs, generation quotas and licensing are account-dependent and must be checked at time of use. No subscription purchase or paid generation was performed while making this plan.

Delay character rigging, full fluid simulation, complex game engines and a large navigable world until the small works are reliable. “KNIGHT LIFE” is an art-direction reference; an armoured character film is not an appropriate first modelling assignment.

At each sprint review, compare intent, composition, technical control, originality and reuse. Advance when the minimum output exists and you can make one intentional variation. If stuck for a session, simplify the asset or effect rather than adding tools.

## Source trail

- [TouchDesigner curriculum](https://learn.derivative.ca/all-courses/) — modular lessons including navigation, TOPs, CHOPs and 3D rendering.
- [TouchDesigner getting started](https://docs.derivative.ca/Getting_Started_With_TouchDesigner) — setup, licensing and Python entry points.
- [Meshy](https://www.meshy.ai/) — image/text generation, texture tools and export formats including GLB. Account entitlement not checked.
- [World Labs mesh export](https://docs.worldlabs.ai/marble/export/mesh) and [export specs](https://docs.worldlabs.ai/marble/export/specs) — distinguishes splats, collider meshes and high-quality meshes.
- [Spark](https://sparkjs.dev/) — World Labs' Three.js Gaussian splat renderer.
- [Blender manual](https://docs.blender.org/manual/en/latest/) — reference link; automated fetch was unavailable during research. Use documentation matching the installed version.
- [Bruno Simon](https://bruno-simon.com/) — a navigable Three.js portfolio with linked source and Blender files.

Product documentation checked 7 September 2026. Recheck version-specific APIs and export entitlements when implementing. Original reference observations and uncertain production claims are recorded in the inspiration library.
