# 002 — Living map, Sprint 1

Status: Session A done (terrain), Session A+ done (Golden Valley slice at true scale), Session C done (the seam holds — see the [session log](session-log.md)). Session B is the only one outstanding and is blocked on a `GEMINI_API_KEY` reaching the container. Verdict on the next decision below: **the seam convinces**, on one condition — the clip's last frame must be rendered from our own scene at the destination camera and handed to the generator as its last-frame anchor, because landing accuracy, not video quality, is what makes the join visible. Source plan: [the living map plan](../../plans/living-map-plan.md). Inspiration: [Explore Primland](https://explore.ownprimland.com/) — study the feeling of the map and the hotspot transitions, not their assets.

**Question:** Can real Cheltenham terrain live in the browser, and can a generated video descent play so seamlessly over it that the seam disappears?

**Output:** Two proofs. (1) A Three.js page with Environment Agency LiDAR terrain of Cheltenham you can pan and zoom. (2) A first/last-frame generated clip between two owned images, playing over a pixel-matched canvas frame. Plus session notes recording costs, generation times and what broke.

**Session A — terrain:** Download the EA National LiDAR Programme DTM tile covering Cheltenham (Open Government Licence; note the tile reference). Convert to a heightmap with GDAL. Displace a plane in Three.js, add orbit-style pan/zoom limits and a simple gradient material. Success is recognising the Cotswold escarpment.

**Session B — one descent** (run it locally where the keys live: [LOCAL-SESSION.md](descent/LOCAL-SESSION.md))**:** Pick two owned images — an aerial-style frame and a ground-level photograph of the same Cheltenham spot. Generate 3–5 first/last-frame candidates (Veo 3.1 via Gemini API, or Kling/Luma via fal.ai). Log prompt, model, cost and duration per candidate. Keep the best and the worst; the worst teaches more.

**Session C — the seam:** Build the swap: canvas renders frame A's camera pose, video element fades in on the matching first frame, plays, holds on the last frame. Measure where the eye catches the join (colour grade? resolution? motion stop?). Record findings in three sentences.

**AI help:** "Help me displace a Three.js PlaneGeometry from a 16-bit heightmap PNG. Explain vertex counts versus texture-based displacement, and how to set camera limits so the terrain never shows its edges."

**Done:** Terrain page reopens and runs at 60 fps on the laptop, one descent clip exists with its endpoints and prompt logged, and the seam experiment has a written verdict. Season shaders and birds are Sprint 2–3; resist starting them.

**Next decision:** If the seam convinces, proceed to the season wave (Sprint 2). If it doesn't, test the Blender-rendered fallback descent before investing further in generation.
