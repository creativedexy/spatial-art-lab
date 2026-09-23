# Why the panther reads as AI, and the fix (23 Sep 2026)

## What the crops of H1-H3 show
| Tell | In the plate | Real photograph |
|---|---|---|
| Every hair lit | Fur rendered as combed, separate glossy strands, each with its own highlight | Fur is a soft mass; light catches only the rim, the rest falls into shadow |
| Water on everything | A droplet on every whisker tip and hair, evenly spaced | A few droplets, uneven, many hairs dry or clumped |
| Wrong colour | Bronze/brown fur with strong rosettes | A melanistic leopard is near-black; rosettes show only faintly at a grazing angle |
| Over-cooked micro-contrast | HDR-like local contrast everywhere, frame edge to edge | Contrast falls away out of focus |
| Everything sharp | Ear, shoulder, whiskers and background all in focus | Long lens wide open: the eye is sharp, the shoulder and background go soft |
| Clean pixels | No noise at "night" | A night shot at ISO 3200-12800 has visible grain |

## Fix
1. **Prompt as a photograph, not a rendering:** camera, lens, aperture, ISO and shutter; say what is soft and what is sharp; ask for grain. Never "hyperdetailed", "8k", "every hair".
2. **Name the imperfections:** matted and clumped wet fur, uneven dampness, faint rosettes, a slightly soft ear, some motion softness in the falling rain or snow.
3. **Restrain the light:** one torch as a rim on the edge of the head and back; most of the body in near-black; specular highlights only on the eye, the nose and a few whiskers.
4. **Post-process gently:** add real sensor-like grain and slightly soften everything but the eye. Never sharpen afterwards; sharpening makes it more plastic.

Sources: getimg.ai "Why AI skin looks fake"; Upsampler "Make AI images look real"; TechBullion "Improve AI images without over-processing"; Picasso IA "Why your AI images look fake".

## Result (round 12)
The prompt fix alone did it: P1-P3 read as photographs. A post pass (grain plus softening off the eye) was tested on H2 and dropped; it cannot undo combed-strand fur, and the re-render needs no help.
