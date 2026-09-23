# Round 12: panther, fix the AI fur
Read experiments/003-spider-probe/alignment/ai-texture-notes.md first; it lists what makes our panther look generated and how to fix it. The attached images are H1, H2, H3. **Use them for composition, pose, environment and light direction only, and re-render the animal's fur and surfaces from scratch; do not copy their texture.**

Write every prompt as a real night wildlife photograph: shot on a full-frame mirrorless camera with a 400mm f/2.8 lens wide open, ISO 6400, 1/250 s, lit by one hand-held torch from the side. A melanistic leopard: near-black fur, rosettes only faintly visible where the light grazes. The eye is the sharpest thing in the frame; the ear, shoulder and back fall softly out of focus; the background is creamy bokeh. Fur is a soft dense mass, slightly matted and clumped where damp, uneven, most of it in near-black shadow; the torch catches only a thin rim on the head and back. Specular highlights only on the eye, the wet nose and a few whiskers. Visible fine sensor grain. Restrained, natural colour. Avoid: glossy strands, every hair highlighted, droplets on every whisker, HDR, over-sharpening, bronze or brown fur, illustration or 3D-render look.

Environments (same as the references):
- `p1-panther-sandstone.png`: red sandstone ledge in a desert canyon at night, a little fine dust drifting in the beam.
- `p2-panther-mangrove.png`: crouched on a mangrove root above black water, a few fireflies as soft out-of-focus points, the water mirroring the torch.
- `p3-panther-snow.png`: snow-covered granite ledge in a mountain snowfall, flakes near the lens blurred into soft discs, a little snow caught in the fur of the back.

Generate each at 1024 x 1536, then make 1080 x 1920 with sips (scale to 1920 tall, centre-crop the width, keep the animal inside the central 80%). No HUD, no text. Save PNGs in experiments/003-spider-probe/alignment/out12/. Write `out12/notes.md` and `out12/prompts.json`.
