# Why the panther plates read as AI, and the fix (23 Sep 2026)

**Correction:** Dex meant the ground, not the fur, and preferred H1-H3's original lighting. Round 12 (fur re-render, section below) was the wrong target; round 13 (ground only) is the fix. See "The ground" at the end.

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

## The ground (round 13, the actual fix)
| Plate | Generated tell | What the edit asked for |
|---|---|---|
| H1 sandstone | Same crumbly sponge lumps everywhere, all equally sharp, flat saturated orange | Bedding lines, a fracture edge, wind-worn faces, loose grit, varied rust to ochre, foreground out of focus |
| H2 mangrove | Smeared glaze like melted chocolate | Rough bark, oysters and barnacles at the waterline, algae, foreground soft |
| H3 snow | Oversized sugar-like crystals, even sparkle | Soft matte powder in drifts, sparkle only where the torch hits, blue-grey shadow, granite grain |

Method: pass the approved plate as the edit target, say what to keep (animal, light, grade, composition) and change only the ground. The rule that carried over: a real long-lens shot has **one plane of focus**; generated surfaces are equally sharp and equally textured from front to back.
