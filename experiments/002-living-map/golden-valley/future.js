// 2045, arriving like weather.
//
// Phase 6. The reference's signature move is a toggle that carries a season
// across the landscape; ours carries twenty years. Same mechanism, and it
// works because everything in this map is already a pure function of data:
// the future is not a different engine, it is a second copy of the same four
// files, and a scalar that says how far across the vale it has got.
//
//   gv-2045-landcover.png   the ground, cross-faded against today's
//   gv-2045-buildings.json  only what is NEW; today's 4,033 still stand
//   gv-2045-trees.bin       hedges first, then orchards and street trees
//   gv-2045-meta.json       the families, and GCHQ's new roof
//
// The front runs west to east because that is the way weather comes off the
// Severn, and because the allocation is in the west — so the change starts in
// the fields and moves towards the town, rather than the other way about. It
// is ragged rather than straight for the same reason a cloud shadow is.
//
// One wave, one direction, once. There is no scrubber: a slider is a better
// tool and a much weaker shot, and this is the shot.

import * as THREE from 'three';
import { applyLife } from './life.js';
import { loadClassTexture, treeScale, treeTint } from './landcover.js';
import { facadeChunk } from './facades.js';
import { MEASURED_SUN } from './look.js';

const url = (f) => new URL(f, import.meta.url).href;
export const futureMeta = await (await fetch(url('gv-2045-meta.json'))).json();

const SWEEP_FROM = -1250;     // local metres: the front starts west of the box
const SWEEP_TO = 1250;
const SOFT = 150;             // metres the front takes to pass a point
const RAGGED = 110;           // metres of noise on the front

// Shared by every material the wave touches, so they cannot disagree about
// where the front is.
/**
 * Task 002. When the photogrammetry is showing, our ground is drawn ONLY
 * where 2045 changes it — the orchards, the wetland, the new streets — and
 * discarded everywhere else, because today's ground is now the real town and
 * the tiles may not be modified. 0 draws the whole terrain, as it always did.
 */
export const groundMask = { value: 0 };
const groundDirect = { value: 0 };
const groundProbeMask = { value: 0 };

/**
 * A keyed build's grade for what 2045 paints over the photograph.
 *
 * Measured by scripts/probe_light.py, 14 Sep 2026, on the keyed build with the
 * photograph's sun and a sky environment: our 2045 ground, future trees and
 * GCHQ's meadow roof against photographed fields and canopy in the same
 * frames. Saturation is the reliable part — too high in every view that
 * measured it — and each value is a ratio of photographed to authored median.
 *
 *   ground vs fields        saturation 0.68 (0.43-0.72, 4 views)  exposure 0.74
 *   trees vs canopy         saturation 0.53 (0.47-0.57, 3 views)  exposure 1.16
 *   meadow roof, field proxy saturation 0.80 (2 views)            exposure 0.55
 *
 * First pass. The probe reads saturation off the rendered, tone-mapped frame,
 * so a factor applied to albedo does not land one-for-one; it is re-measured
 * after each change, as the lighting was. The keyless map is not graded.
 */
export const KEYED_GRADE = {
  ground: { saturation: 0.68, exposure: 0.74 },
  // M5's first keyed render measured -0.10 saturation and -0.28 stops against
  // photographed canopy. 0.47 restores the lost colour; 1.41 is 1.16 * 2^0.28.
  trees: { saturation: 0.47, exposure: 1.41 },
  meadow: { saturation: 0.52, exposure: 0.55 },   // M4: textured meadow measured +0.15 sat at 0.80 (22 Sep)
  // M4 starts each authored material about 0.4 stops below the former pale
  // boxes in the keyed build. These are deliberately palette compensation,
  // not a second light: probe_light.py remains the authority on the live map.
  homes: { saturation: 0.88, exposure: 1.02 },
  campus: { saturation: 0.82, exposure: 1.48 },
  glasshouse: { saturation: 0.70, exposure: 1.22 },
  canopy: { saturation: 0.85, exposure: 1.00 },
};
const groundGrade = { saturation: { value: 1 }, exposure: { value: 1 } };

/** Desaturate a colour toward its own luminance, then scale it. In place. */
function gradeColour(c, { saturation, exposure }) {
  const l = 0.2126 * c.r + 0.7152 * c.g + 0.0722 * c.b;
  return c.setRGB(
    (l + (c.r - l) * saturation) * exposure,
    (l + (c.g - l) * saturation) * exposure,
    (l + (c.b - l) * saturation) * exposure);
}

export const uniforms = {
  uFront: { value: SWEEP_FROM },
  uSoft: { value: SOFT },
  uRagged: { value: RAGGED },
};

// A hash-based value noise, the same shape life.js uses for cloud shadows, so
// the front breaks up on the same scale the weather does.
const NOISE = /* glsl */`
  float fHash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
  }
  float fNoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(fHash(i), fHash(i + vec2(1.0, 0.0)), f.x),
               mix(fHash(i + vec2(0.0, 1.0)), fHash(i + vec2(1.0, 1.0)), f.x), f.y);
  }
  // How far 2045 has got at a point on the ground. 0 today, 1 built.
  float futureAt(vec3 w) {
    float edge = uFront + (fNoise(w.xz * 0.0016) - 0.5) * 2.0 * uRagged
                        + (fNoise(w.xz * 0.0067) - 0.5) * uRagged * 0.5;
    return 1.0 - smoothstep(edge - uSoft, edge + uSoft, w.x);
  }
`;

/**
 * Give a material the world's clock first, then the wave on top of it.
 *
 * Order matters and chaining matters: life.js sets `onBeforeCompile` outright,
 * so applying it second would silently drop the wave and the whole thing
 * would arrive fully built with no front at all.
 */
function share(material, patch, life = {}) {
  applyLife(material, life);
  const previous = material.onBeforeCompile;
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, uniforms);
    patch(shader);
  };
  material.customProgramCacheKey = () => `future:${patch.name}`;
  material.needsUpdate = true;
  return material;
}

// --- the ground -------------------------------------------------------------

/**
 * Cross-fade the terrain's map against the 2045 one.
 *
 * Patched into the existing standard material rather than replacing it: the
 * ground keeps its lighting, its shadows, its wind and its cloud shadows, and
 * gains one texture fetch and a mix. Anything else would mean two terrains.
 */
const groundMaskUniforms = [];
const groundDirectUniforms = [];
const groundProbeMaskUniforms = [];
const groundClass = Object.fromEntries(Object.entries(futureMeta.classes)
  .map(([name, value]) => [name, value.index / 255]));

/** Draw our ground only where 2045 changes it. */
export function setGroundMasked(on) {
  groundMask.value = on ? 1 : 0;
  for (const u of groundMaskUniforms) u.value = groundMask.value;
}

export function setGroundDirect(on) {
  groundDirect.value = on ? 1 : 0;
  for (const u of groundDirectUniforms) u.value = groundDirect.value;
}

/** Flat binary output for probe_light.py; never enabled in the live map. */
export function setGroundProbeMask(on) {
  groundProbeMask.value = on ? 1 : 0;
  for (const u of groundProbeMaskUniforms) u.value = groundProbeMask.value;
}

/** World-space meadow detail for GCHQ's very large annular roof. */
function meadowRoof(material, amount) {
  const previous = material.onBeforeCompile;
  const previousKey = material.customProgramCacheKey?.bind(material);
  material.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    shader.uniforms.uMeadowAt = amount;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>',
        '#include <common>\nvarying vec2 vGchqMeadowWorld;')
      .replace('#include <begin_vertex>', `#include <begin_vertex>
         vGchqMeadowWorld = (modelMatrix * vec4(transformed, 1.0)).xz;`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
        uniform float uMeadowAt;
        varying vec2 vGchqMeadowWorld;
        float meadowHash(vec2 p) {
          return fract(sin(dot(floor(p), vec2(127.1, 311.7))) * 43758.5453);
        }
        float meadowNoise(vec2 p) {
          vec2 i = floor(p), f = fract(p);
          f = f * f * (3.0 - 2.0 * f);
          return mix(mix(meadowHash(i), meadowHash(i + vec2(1.0, 0.0)), f.x),
                     mix(meadowHash(i + vec2(0.0, 1.0)),
                         meadowHash(i + vec2(1.0, 1.0)), f.x), f.y);
        }
        float meadowRay(vec2 p, vec2 direction) {
          float ahead = smoothstep(-1.0, 2.0, dot(p, direction));
          float off = abs(p.x * direction.y - p.y * direction.x);
          return ahead * (1.0 - smoothstep(1.25, 2.05, off));
        }`)
      .replace('#include <map_fragment>', `#include <map_fragment>
        if (uMeadowAt > 0.001) {
          vec2 p = vGchqMeadowWorld - vec2(141.5, 58.0);
          float radius = length(vec2(p.x, p.y * 1.035));
          // Broad 5-20 m changes stop the hectare-scale roof becoming a
          // single olive band, while the grade still supplies its base hue.
          float patches = meadowNoise(vGchqMeadowWorld / 18.0) * 0.22
                        + meadowNoise(vGchqMeadowWorld / 7.0 + 19.0) * 0.12;
          vec3 meadow = diffuseColor.rgb;
          vec3 planted = meadow * (0.82 + patches);
          float flower = meadowHash(vGchqMeadowWorld * 1.35 + 7.0);
          planted = mix(planted, meadow * vec3(1.62, 1.48, 0.54),
                        step(0.955, flower) * 0.82);
          planted = mix(planted, meadow * vec3(1.62, 1.58, 1.42),
                        step(0.975, flower) * 0.78);
          planted = mix(planted, meadow * vec3(1.25, 0.72, 1.38),
                        step(0.989, flower) * 0.72);
          float rings = 1.0 - smoothstep(1.35, 2.25,
            min(abs(radius - 61.0), abs(radius - 80.0)));
          float radials = max(meadowRay(p, normalize(vec2(0.91, 0.42))),
                           max(meadowRay(p, normalize(vec2(-0.28, 0.96))),
                               meadowRay(p, normalize(vec2(-0.82, -0.57)))));
          float mown = clamp(rings + radials, 0.0, 1.0);
          planted = mix(planted, meadow * vec3(0.84, 0.88, 0.66), mown * 0.90);
          float edge = 1.0 - smoothstep(0.45, 1.75,
            min(abs(radius - 43.5), abs(radius - 98.5)));
          planted = mix(planted, meadow * 0.54, edge * 0.72);
          diffuseColor.rgb = mix(diffuseColor.rgb, planted, uMeadowAt);
        }`)
      .replace('#include <roughnessmap_fragment>',
        `#include <roughnessmap_fragment>
         roughnessFactor = mix(roughnessFactor, 0.98, uMeadowAt);`);
  };
  material.customProgramCacheKey = () =>
    `${previousKey ? previousKey() : 'gchq'}:meadow-v2`;
  material.needsUpdate = true;
}

export function blendGround(
  mesh, futureTexture, todayClasses, futureClasses, directGround = false,
) {
  groundDirect.value = directGround ? 1 : 0;
  groundGrade.saturation.value = directGround ? KEYED_GRADE.ground.saturation : 1;
  groundGrade.exposure.value = directGround ? KEYED_GRADE.ground.exposure : 1;
  const m = mesh.material;
  const previous = m.onBeforeCompile;
  m.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, uniforms,
                  { uFutureMap: { value: futureTexture },
                    uTodayClass: { value: todayClasses ?? null },
                    uFutureClass: { value: futureClasses ?? null },
                    uGroundTexel: { value: new THREE.Vector2(
                      1 / (futureTexture.image?.width || 2000),
                      1 / (futureTexture.image?.height || 2000)) },
                    uGroundMask: { value: groundMask.value },
                    uGroundProbeMask: { value: groundProbeMask.value },
                    uDirectGround: { value: groundDirect.value },
                    uGroundSaturation: groundGrade.saturation,
                    uGroundExposure: groundGrade.exposure });
    // Held so setGroundMasked can move it without recompiling: a shader
    // rebuild on a toggle is a stutter, and on a year change it would be a
    // stutter every frame.
    groundMaskUniforms.push(shader.uniforms.uGroundMask);
    groundProbeMaskUniforms.push(shader.uniforms.uGroundProbeMask);
    groundDirectUniforms.push(shader.uniforms.uDirectGround);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>',
        '#include <common>\nvarying vec3 vFutureWorld;')
      .replace('#include <worldpos_vertex>',
        `#include <worldpos_vertex>
         vFutureWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;`);
    // worldpos_vertex only emits when something else needs it, so compute it
    // unconditionally rather than relying on a define we do not control.
    if (!shader.vertexShader.includes('vFutureWorld =')) {
      shader.vertexShader = shader.vertexShader.replace(
        '#include <project_vertex>',
        `vFutureWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;
         #include <project_vertex>`);
    }
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>',
        `#include <common>
         uniform sampler2D uFutureMap;
         uniform sampler2D uTodayClass;
         uniform sampler2D uFutureClass;
         uniform vec2 uGroundTexel;
         uniform float uGroundMask;
         uniform float uGroundProbeMask;
         uniform float uDirectGround;
         uniform float uGroundSaturation;
         uniform float uGroundExposure;
         uniform float uFront; uniform float uSoft; uniform float uRagged;
         varying vec3 vFutureWorld;
         float gvWaterAmount = 0.0;
         float gvClassEqual(float sampleValue, float classValue) {
           return 1.0 - step(0.5 / 255.0, abs(sampleValue - classValue));
         }
         float gvClassWeight(float classValue, float centre, vec4 around) {
           return gvClassEqual(centre, classValue) * 0.36
             + dot(vec4(
                 gvClassEqual(around.x, classValue),
                 gvClassEqual(around.y, classValue),
                 gvClassEqual(around.z, classValue),
                 gvClassEqual(around.w, classValue)), vec4(0.16));
         }
         ${NOISE}`)
      .replace('#include <map_fragment>',
        `{
           // Over photogrammetry, our ground is drawn ONLY where 2045
           // actually changes it — an orchard where there was stubble, wet
           // meadow where there was a culverted brook — and never where the
           // scheme leaves a field alone. The first version of this masked by
           // the wave instead, which meant that once the front had crossed,
           // our terrain covered the real town completely and the whole layer
           // was pointless. The class maps answer it exactly: two indices,
           // and they either differ or they do not.
           //
           // This is deliberately the original, binary centre-texel test.
           // probe_light.py uses the same discard to classify authored ground;
           // colour filtering and field detail belong to the render below and
           // must never alter which square metres the diagnostic can see.
           if (uGroundMask > 0.5) {
             float wasClass = texture2D(uTodayClass, vMapUv).r;
             float willClass = texture2D(uFutureClass, vMapUv).r;
             bool changed = abs(wasClass - willClass) > 0.002;
             if (!changed || futureAt(vFutureWorld) < 0.5) discard;
           }
         }
         #include <map_fragment>
         vec2 detailStep = uGroundTexel * 3.5;
         vec4 futureTexel = texture2D(uFutureMap, vMapUv) * 0.36
           + texture2D(uFutureMap, vMapUv + vec2(detailStep.x, 0.0)) * 0.16
           + texture2D(uFutureMap, vMapUv - vec2(detailStep.x, 0.0)) * 0.16
           + texture2D(uFutureMap, vMapUv + vec2(0.0, detailStep.y)) * 0.16
           + texture2D(uFutureMap, vMapUv - vec2(0.0, detailStep.y)) * 0.16;
         float futureMix = futureAt(vFutureWorld);
         if (uDirectGround > 0.5) {
           diffuseColor.rgb = futureTexel.rgb;
         }
         if (uDirectGround < 0.5) {
           // The sampler is sRGB, so the GPU has already linearised this and
           // it can be mixed with diffuseColor directly.
           diffuseColor.rgb = mix(diffuseColor.rgb, futureTexel.rgb, futureMix);
         }

         // Class samples share the colour filter's radius. The class image
         // itself stays lossless and nearest-filtered; averaging membership,
         // not numeric indices, is what makes a real boundary transition.
         float fc = texture2D(uFutureClass, vMapUv).r;
         vec4 fa = vec4(
           texture2D(uFutureClass, vMapUv + vec2(detailStep.x, 0.0)).r,
           texture2D(uFutureClass, vMapUv - vec2(detailStep.x, 0.0)).r,
           texture2D(uFutureClass, vMapUv + vec2(0.0, detailStep.y)).r,
           texture2D(uFutureClass, vMapUv - vec2(0.0, detailStep.y)).r);
         float grass = gvClassWeight(${groundClass.grass}, fc, fa) * futureMix;
         float meadow = gvClassWeight(${groundClass.meadow}, fc, fa) * futureMix;
         float orchard = gvClassWeight(${groundClass.orchard}, fc, fa) * futureMix;
         float arable = gvClassWeight(${groundClass.farmland}, fc, fa) * futureMix;
         float wetland = gvClassWeight(${groundClass.wetland}, fc, fa) * futureMix;

         // The measured field grain is 22 degrees. All frequencies are in
         // world metres, so the effect neither swims with the camera nor
         // changes scale when a texture is recompressed.
         const vec2 gvAlong = vec2(0.927184, 0.374607);
         const vec2 gvAcross = vec2(-0.374607, 0.927184);
         float along = dot(vFutureWorld.xz, gvAlong);
         float across = dot(vFutureWorld.xz, gvAcross);
         float mown = sin(across * 0.785398) * 0.028;
         float meadowPatch = (fNoise(vFutureWorld.xz / 16.0)
                            + fNoise(vFutureWorld.xz / 5.0 + 19.0) * 0.45
                            - 0.725) * 0.13;
         float orchardStrip = sin(across * 0.837758) * 0.045
                            + (fNoise(vec2(along / 22.0, across / 7.5)) - 0.5)
                              * 0.055;
         float drills = sin(across * 1.047198) * 0.022
                      + sin(across * 0.349066) * 0.018;
         float groundDetail = mown * grass + meadowPatch * meadow
                            + meadowPatch * wetland * 0.85
                            + orchardStrip * orchard + drills * arable;
         diffuseColor.rgb *= max(0.72, 1.0 + groundDetail);

         // Wet meadow remains vegetation except for sparse 10-30 m pools.
         // Existing water and those pools use the keyed sky environment via
         // MeshStandardMaterial's low-roughness specular response below.
         float wetNoise = fNoise(vFutureWorld.xz / 21.0) * 0.68
                        + fNoise(vFutureWorld.xz / 8.0 + 31.0) * 0.32;
         float pools = smoothstep(0.68, 0.79, wetNoise) * wetland;
         float futureWater = min(1.0,
           gvClassWeight(${groundClass.water}, fc, fa) + pools);
         float todayWater = gvClassEqual(texture2D(uTodayClass, vMapUv).r,
                                         ${groundClass.water});
         gvWaterAmount = mix(todayWater, futureWater, futureMix);
         float waterLuma = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
         vec3 silver = mix(diffuseColor.rgb, vec3(waterLuma) * 0.72
                           + vec3(0.055, 0.075, 0.095), 0.62);
         diffuseColor.rgb = mix(diffuseColor.rgb, silver, gvWaterAmount);

         // Drawn straight over the photograph in a keyed build, so grade the
         // finished detail rather than changing the established base palette.
         if (uDirectGround > 0.5) {
           float gl = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
           diffuseColor.rgb = mix(vec3(gl), diffuseColor.rgb, uGroundSaturation)
                              * uGroundExposure;
         }`)
      .replace('#include <roughnessmap_fragment>',
        `#include <roughnessmap_fragment>
         roughnessFactor = mix(roughnessFactor, 0.18, gvWaterAmount);`)
      .replace('#include <metalnessmap_fragment>',
        `#include <metalnessmap_fragment>
         metalnessFactor = mix(metalnessFactor, 0.06, gvWaterAmount);`)
      .replace('#include <normal_fragment_maps>',
        `#include <normal_fragment_maps>
         float gvRippleX = sin(vFutureWorld.x * 0.72
                             + vFutureWorld.z * 0.31 + uTime * 1.35);
         float gvRippleY = cos(vFutureWorld.x * -0.28
                             + vFutureWorld.z * 0.83 + uTime * 1.75);
         normal = normalize(normal + gvWaterAmount * 0.035
                            * vec3(gvRippleX, gvRippleY, 0.0));`)
      .replace('#include <opaque_fragment>',
        `// The probe needs classification, not the terrain's light or grade.
         if (uGroundProbeMask > 0.5) outgoingLight = vec3(1.0);
         #include <opaque_fragment>`);
  };
  m.needsUpdate = true;
}

// --- new buildings ----------------------------------------------------------

/**
 * A 2045 building, as geometry that knows where its own ground is.
 *
 * Built here rather than by buildings.js because these have to *rise*, and
 * rising means every vertex needs the base it grows from. The 2045 footprints
 * are convex quads with no holes, so the whole builder is four wall quads and
 * a roof, plus the low-cost parapet, eaves and dwelling-scale detail below.
 */
function futureGeometry(list, palette, grade = null) {
  const pos = [];
  const base = [];
  const anchor = [];
  const col = [];
  // Facade attributes stay in metres and carry the few categorical choices
  // that must survive merging a whole family into one draw call.
  //
  // `aFacade` is the surface in METRES — how far along the wall, and how far
  // up it — not the 0..1 a texture usually wants. That is the whole trick: a
  // rule written in metres ("a window every 3 m, a storey every 3.4 m, the
  // ground floor glazed to 3.4") then holds on a 38 m block and a 17 m one
  // without a single number changing, and a facade never stretches to fit.
  //
  // `aSurface` says whether a triangle is a wall or a roof, because a family
  // is one mesh and the shader has to tell sedum from stone.
  const uv = [];
  const surface = [];
  const bays = [];
  const walls = [];
  const typologies = [];
  const variants = [];
  let tint = new THREE.Color();
  let kind = 0;
  let bayWidth = 3;
  let wallHeight = 0;
  let typology = 0;
  let variant = 0;
  const push = (x, y, z, b, ax, az, u = 0, v = 0) => {
    pos.push(x, y, z);
    base.push(b);
    anchor.push(ax, az);
    col.push(tint.r, tint.g, tint.b);
    uv.push(u, v);
    surface.push(kind);
    bays.push(bayWidth);
    walls.push(wallHeight);
    typologies.push(typology);
    variants.push(variant);
  };
  const quad = (a, b, c, d, bs, ax, az, uvs = null) => {
    const t = uvs ?? [[0, 0], [0, 0], [0, 0], [0, 0]];
    push(...a, bs, ax, az, ...t[0]); push(...b, bs, ax, az, ...t[1]);
    push(...c, bs, ax, az, ...t[2]);
    push(...a, bs, ax, az, ...t[0]); push(...c, bs, ax, az, ...t[2]);
    push(...d, bs, ax, az, ...t[3]);
  };

  const area = (ring) => ring.reduce((sum, p, i) => {
    const q = ring[(i + 1) % ring.length];
    return sum + p[0] * q[1] - q[0] * p[1];
  }, 0) * 0.5;
  const clockwise = (ring) => {
    const out = ring.map((p) => [...p]);
    if (area(out) > 0) out.reverse();
    return out;
  };
  const rotateLongEdgeFirst = (ring) => {
    let at = 0;
    let longest = -1;
    for (let i = 0; i < ring.length; i++) {
      const q = ring[(i + 1) % ring.length];
      const d = Math.hypot(q[0] - ring[i][0], q[1] - ring[i][1]);
      if (d > longest) { longest = d; at = i; }
    }
    return [...ring.slice(at), ...ring.slice(0, at)];
  };
  const lineIntersection = (a, b, c, d) => {
    const abx = b[0] - a[0], abz = b[1] - a[1];
    const cdx = d[0] - c[0], cdz = d[1] - c[1];
    const den = abx * cdz - abz * cdx;
    if (Math.abs(den) < 1e-6) return [...b];
    const t = ((c[0] - a[0]) * cdz - (c[1] - a[1]) * cdx) / den;
    return [a[0] + abx * t, a[1] + abz * t];
  };
  const offsetRing = (ring, distance) => {
    const cx = ring.reduce((s, p) => s + p[0], 0) / ring.length;
    const cz = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    const lines = ring.map((p, i) => {
      const q = ring[(i + 1) % ring.length];
      const dx = q[0] - p[0], dz = q[1] - p[1];
      const len = Math.hypot(dx, dz);
      let nx = -dz / len, nz = dx / len;
      if ((cx - p[0]) * nx + (cz - p[1]) * nz < 0) {
        nx = -nx; nz = -nz;
      }
      return [[p[0] + nx * distance, p[1] + nz * distance],
              [q[0] + nx * distance, q[1] + nz * distance]];
    });
    return lines.map((line, i) => {
      const prev = lines[(i + lines.length - 1) % lines.length];
      return lineIntersection(prev[0], prev[1], line[0], line[1]);
    });
  };
  const mix2 = (a, b, t) => [a[0] + (b[0] - a[0]) * t,
                              a[1] + (b[1] - a[1]) * t];
  const solidPost = (x, z, y0, y1, along, across, bs, ax, az) => {
    const half = 0.075;
    const ring = clockwise([
      [x - along[0] * half - across[0] * half,
       z - along[1] * half - across[1] * half],
      [x + along[0] * half - across[0] * half,
       z + along[1] * half - across[1] * half],
      [x + along[0] * half + across[0] * half,
       z + along[1] * half + across[1] * half],
      [x - along[0] * half + across[0] * half,
       z - along[1] * half + across[1] * half],
    ]);
    for (let i = 0; i < 4; i++) {
      const p = ring[i], q = ring[(i + 1) % 4];
      quad([p[0], y0, p[1]], [q[0], y0, q[1]],
           [q[0], y1, q[1]], [p[0], y1, p[1]], bs, ax, az);
    }
    quad([ring[0][0], y1, ring[0][1]], [ring[1][0], y1, ring[1][1]],
         [ring[2][0], y1, ring[2][1]], [ring[3][0], y1, ring[3][1]],
         bs, ax, az);
  };

  for (const b of list) {
    const spec = palette[b.family] ?? { wall: '#e6dcc6', roof: '#7d8f5a' };
    const wallColour = new THREE.Color(spec.wall);
    const roofColour = new THREE.Color(
      b.typology === 'apartments' ? (spec.flatRoof ?? spec.roof) : spec.roof);
    if (grade) {
      gradeColour(wallColour, grade);
      gradeColour(roofColour, grade);
    }
    tint = wallColour;
    const ring = rotateLongEdgeFirst(clockwise(b.ring));
    const y0 = b.base - 0.4;
    const ax = ring.reduce((s, p) => s + p[0], 0) / ring.length;
    const az = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    typology = b.typology === 'apartments' ? 1 : 0;
    variant = b.name === 'OUTPUT' ? 1 : b.name === 'ROUTER' ? 2 : 0;

    // Solar car ports are slabs and posts, not short buildings. The top plane
    // leans six degrees toward the measured south-east sun; the clear 3.2 m
    // underside leaves the photographed cars and circulation legible.
    if (b.family === 'canopy') {
      const [p, q, r, s] = ring;
      const length = Math.hypot(q[0] - p[0], q[1] - p[1]);
      const depth = Math.hypot(s[0] - p[0], s[1] - p[1]);
      const along = [(q[0] - p[0]) / length, (q[1] - p[1]) / length];
      const across = [(s[0] - p[0]) / depth, (s[1] - p[1]) / depth];
      const sun = { x: Math.sin(THREE.MathUtils.degToRad(MEASURED_SUN.azimuth)),
                    z: -Math.cos(THREE.MathUtils.degToRad(MEASURED_SUN.azimuth)) };
      const sign = across[0] * sun.x + across[1] * sun.z >= 0 ? 1 : -1;
      const downSlope = { x: across[0] * sign, z: across[1] * sign };
      const tilt = Math.tan(THREE.MathUtils.degToRad(b.tiltDegrees ?? 6));
      const topY = (point) => y0 + 0.4 + (b.underside ?? 3.2)
        + (b.thickness ?? 0.3) + depth * 0.5 * tilt
        - ((point[0] - ax) * downSlope.x
           + (point[1] - az) * downSlope.z) * tilt;
      const top = ring.map((point) => [point[0], topY(point), point[1]]);
      const bottom = top.map((point) => [point[0], point[1] - (b.thickness ?? 0.3), point[2]]);
      bayWidth = 1.7; wallHeight = b.underside ?? 3.2;
      tint = roofColour; kind = 1;
      quad(top[0], top[1], top[2], top[3], y0, ax, az,
           [[0, 0], [length, 0], [length, depth], [0, depth]]);
      tint = wallColour; kind = 0;
      quad(bottom[3], bottom[2], bottom[1], bottom[0], y0, ax, az);
      for (let i = 0; i < 4; i++) {
        const j = (i + 1) % 4;
        quad(bottom[i], bottom[j], top[j], top[i], y0, ax, az);
      }
      const postCount = Math.max(2, Math.ceil(length / 9));
      const generatedPosts = b.posts ?? Array.from(
        { length: postCount }, (_, i) => {
          const t = postCount === 1 ? 0.5 : 0.07 + i * 0.86 / (postCount - 1);
          const c = mix2(mix2(p, q, t), mix2(s, r, t), 0.5);
          return { x: c[0], z: c[1], ground: b.base };
        });
      for (const post of generatedPosts) {
        const c = [post.x, post.z];
        // Every foot comes from the terrain heightfield at this exact point;
        // a shared minimum base is what made the old white needles pass up
        // through GCHQ's roof on sloping/overlapping source polygons.
        solidPost(c[0], c[1], post.ground,
                  topY(c) - (b.thickness ?? 0.3),
                  along, across, post.ground, ax, az);
      }
      continue;
    }

    const roofLevel = y0 + (b.roof === 'flat' ? b.height : b.eaves);
    const parapet = b.roof === 'flat' ? 0.75 : 0;
    const eaves = roofLevel + parapet;

    kind = 0;
    // `run` is metres travelled around the building, so a bay grid starts at a
    // corner and stays continuous around it rather than restarting per wall.
    let run = 0;
    const wallTop = eaves - y0;
    for (let i = 0; i < ring.length; i++) {
      const [x1, z1] = ring[i];
      const [x2, z2] = ring[(i + 1) % ring.length];
      const span = Math.hypot(x2 - x1, z2 - z1);
      // Bays divide THIS elevation exactly, which is what an architect does:
      // a 35.2 m wall gets twelve bays of 2.93 m, not eleven of 3.0 and a
      // sliver. Still metres — the wall's own bay width travels with it, so
      // the shader keeps working in real sizes rather than in fractions.
      const longSide = i === 0 || i === 2;
      bayWidth = b.typology === 'terrace' && longSide
        ? span / Math.max(1, b.dwellings ?? 1)
        : span / Math.max(1, Math.round(span / 3.0));
      wallHeight = wallTop;
      quad([x1, y0, z1], [x2, y0, z2], [x2, eaves, z2], [x1, eaves, z1],
           y0, ax, az,
           [[0, 0], [span, 0], [span, wallTop], [0, wallTop]]);
      run += span;
    }

    tint = roofColour;
    kind = 1;
    if (b.roof === 'flat') {
      const [p, q, r, s] = ring;
      const inner = offsetRing(ring, 0.28);
      // The roof is metres too, measured from the building's own corner, so a
      // PV array lands on a grid rather than on a stretched square.
      const ru = (t) => [Math.hypot(t[0] - p[0], t[1] - p[1]), 0];
      const rv = (t) => Math.hypot(t[0] - q[0], t[1] - q[1]);
      quad([inner[0][0], roofLevel, inner[0][1]],
           [inner[1][0], roofLevel, inner[1][1]],
           [inner[2][0], roofLevel, inner[2][1]],
           [inner[3][0], roofLevel, inner[3][1]], y0, ax, az,
           [[0, 0], [ru(q)[0], 0], [ru(q)[0], rv(r)], [0, rv(s)]]);
      // A real 750 mm parapet: outer and inner faces with a 280 mm coping.
      tint = wallColour; kind = 3;
      for (let i = 0; i < 4; i++) {
        const j = (i + 1) % 4;
        quad([ring[i][0], eaves, ring[i][1]],
             [ring[j][0], eaves, ring[j][1]],
             [inner[j][0], eaves, inner[j][1]],
             [inner[i][0], eaves, inner[i][1]], y0, ax, az);
        quad([inner[j][0], roofLevel, inner[j][1]],
             [inner[i][0], roofLevel, inner[i][1]],
             [inner[i][0], eaves, inner[i][1]],
             [inner[j][0], eaves, inner[j][1]], y0, ax, az);
      }
    } else {
      // A gable on a quad: the ridge runs between the midpoints of the two
      // ends, which for these blocks is the long axis by construction.
      const overhang = offsetRing(ring, b.family === 'glasshouse' ? -0.3 : -0.4);
      const [p, q, r, s] = overhang;
      const mid = (a, c) => [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2];
      const m1 = mid(p, s);
      const m2 = mid(q, r);
      const dwellings = b.typology === 'terrace' ? Math.max(1, b.dwellings ?? 1) : 1;
      const roofRun = Math.hypot(q[0] - p[0], q[1] - p[1]);
      const sun = new THREE.Vector2(
        Math.sin(THREE.MathUtils.degToRad(MEASURED_SUN.azimuth)),
        -Math.cos(THREE.MathUtils.degToRad(MEASURED_SUN.azimuth)));
      const side1 = new THREE.Vector2(p[0] - m1[0], p[1] - m1[1]).normalize();
      const solarFirst = side1.dot(sun) >= 0;
      const ridgeAt = (i) => y0 + b.ridge
        + (b.typology === 'terrace' ? ((Math.floor(i / 2) % 3) - 1) * 0.16 : 0);
      for (let i = 0; i < dwellings; i++) {
        const t0 = i / dwellings, t1 = (i + 1) / dwellings;
        const a = mix2(p, q, t0), bb = mix2(p, q, t1);
        const d = mix2(s, r, t0), c = mix2(s, r, t1);
        const rm0 = mid(a, d), rm1 = mid(bb, c);
        const rh = ridgeAt(i);
        bayWidth = roofRun / dwellings;
        kind = solarFirst ? 1 : 2;
        quad([a[0], roofLevel, a[1]], [bb[0], roofLevel, bb[1]],
             [rm1[0], rh, rm1[1]], [rm0[0], rh, rm0[1]], y0, ax, az,
             [[i * bayWidth, 0], [(i + 1) * bayWidth, 0],
              [(i + 1) * bayWidth, Math.hypot(rm1[0] - bb[0], rm1[1] - bb[1])],
              [i * bayWidth, Math.hypot(rm0[0] - a[0], rm0[1] - a[1])]]);
        kind = solarFirst ? 2 : 1;
        quad([c[0], roofLevel, c[1]], [d[0], roofLevel, d[1]],
             [rm0[0], rh, rm0[1]], [rm1[0], rh, rm1[1]], y0, ax, az,
             [[(i + 1) * bayWidth, 0], [i * bayWidth, 0],
              [i * bayWidth, Math.hypot(rm0[0] - d[0], rm0[1] - d[1])],
              [(i + 1) * bayWidth, Math.hypot(rm1[0] - c[0], rm1[1] - c[1])]]);
        // Roof-height changes form a slim party-wall break every two homes.
        if (i && Math.abs(ridgeAt(i - 1) - rh) > 0.01) {
          kind = 3; tint = wallColour;
          const low = Math.min(ridgeAt(i - 1), rh), high = Math.max(ridgeAt(i - 1), rh);
          for (const edge of [a, d]) {
            push(edge[0], roofLevel, edge[1], y0, ax, az);
            push(rm0[0], low, rm0[1], y0, ax, az);
            push(rm0[0], high, rm0[1], y0, ax, az);
            push(edge[0], roofLevel, edge[1], y0, ax, az);
            push(rm0[0], high, rm0[1], y0, ax, az);
            push(rm0[0], low, rm0[1], y0, ax, az);
          }
          tint = roofColour;
        }
      }
      // The two triangular ends.
      tint = wallColour; kind = 0;
      const endSpan = Math.hypot(ring[3][0] - ring[0][0],
                                 ring[3][1] - ring[0][1]);
      bayWidth = endSpan;
      push(ring[0][0], roofLevel, ring[0][1], y0, ax, az,
           0, roofLevel - y0);
      push((ring[0][0] + ring[3][0]) / 2, ridgeAt(0),
           (ring[0][1] + ring[3][1]) / 2, y0, ax, az,
           endSpan / 2, ridgeAt(0) - y0);
      push(ring[3][0], roofLevel, ring[3][1], y0, ax, az,
           endSpan, roofLevel - y0);
      push(ring[1][0], roofLevel, ring[1][1], y0, ax, az,
           0, roofLevel - y0);
      push(ring[2][0], roofLevel, ring[2][1], y0, ax, az,
           endSpan, roofLevel - y0);
      push((ring[1][0] + ring[2][0]) / 2, ridgeAt(dwellings - 1),
           (ring[1][1] + ring[2][1]) / 2, y0, ax, az,
           endSpan / 2, ridgeAt(dwellings - 1) - y0);
    }
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aBase', new THREE.Float32BufferAttribute(base, 1));
  g.setAttribute('aAnchor', new THREE.Float32BufferAttribute(anchor, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('aFacade', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('aSurface', new THREE.Float32BufferAttribute(surface, 1));
  g.setAttribute('aBay', new THREE.Float32BufferAttribute(bays, 1));
  g.setAttribute('aWallTop', new THREE.Float32BufferAttribute(walls, 1));
  g.setAttribute('aTypology', new THREE.Float32BufferAttribute(typologies, 1));
  g.setAttribute('aVariant', new THREE.Float32BufferAttribute(variants, 1));
  g.computeVertexNormals();
  return g;
}

const RISE = /* glsl */`
  attribute float aBase;
  attribute vec2 aAnchor;
  uniform float uFront; uniform float uSoft; uniform float uRagged;
`;
const GROW = /* glsl */`
  uniform float uFront; uniform float uSoft; uniform float uRagged;
`;

// The vertex work, written once. It has to run in the shadow pass too, and a
// second copy of it would drift from this one the first time either changed.
const RISE_BODY = /* glsl */`
  float f = futureAt(vec3(aAnchor.x, 0.0, aAnchor.y));
  // Rise from the ground the footprint sits on, and collapse to the
  // footprint's own centre on the way. Scaling height alone leaves a flat
  // quad lying on the field before the front reaches it, which does not read
  // as "not built yet", it reads as a black slab.
  transformed.xz = mix(vec2(aAnchor.x, aAnchor.y), transformed.xz,
                       smoothstep(0.0, 0.22, f));
  transformed.y = aBase + (transformed.y - aBase) * f;
`;
// For a placed model: its origin is at the base of its own footprint and its
// instance matrix carries the position, so the same collapse-and-rise the
// extrusions get needs no attributes at all.
const MODEL_BODY = /* glsl */`
  float f = futureAt(vec3(instanceMatrix[3].x, 0.0, instanceMatrix[3].z));
  transformed.xz *= smoothstep(0.0, 0.22, f);
  transformed.y *= f;
`;
const GROW_BODY = /* glsl */`
  // The instance's own translation is its position on the ground, so a tree
  // needs no extra attribute to know where it is.
  float f = futureAt(vec3(instanceMatrix[3].x, 0.0, instanceMatrix[3].z));
  transformed *= smoothstep(0.0, 0.85, f);
`;

/**
 * The same transform, for the shadow pass.
 *
 * Three renders shadows with its own depth material, which never sees a
 * patched `onBeforeCompile` on the visible one. Without this, every building
 * and every tree casts its full-grown shadow from the first frame — and a
 * field with twenty crisp black rectangles lying in it and nothing standing
 * up is a stranger sight than either state on its own.
 */
/**
 * Make a placed model rise with the front, like everything else 2045 adds.
 *
 * The material comes from the GLB, so it is patched in place rather than built
 * here — its texture, its roughness and its double-sidedness are what the
 * model was made with, and none of that is ours to decide.
 */
export function riseModel(material) {
  share(material, function riseModel(shader) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${GROW}\n${NOISE}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\n${MODEL_BODY}`);
  });
  return { material, depth: depthFor(GROW, MODEL_BODY, 'future:model:depth') };
}


function depthFor(declarations, body, key) {
  const d = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  d.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${declarations}\n${NOISE}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>\n${body}`);
  };
  d.customProgramCacheKey = () => key;
  return d;
}

function riseMaterial(family) {
  const m = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 0.85 });
  // Phase 8. A family whose facade is written gets it here, layered onto the
  // same material that already carries the wave and the world's clock rather
  // than replacing it — replacing it would silently drop the growth transform
  // and the buildings would arrive fully built with no front at all.
  const facade = facadeChunk(family);
  share(m, function future(shader) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>',
               `#include <common>\n${RISE}\n${NOISE}${facade ? `\n${facade.vertex}` : ''}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
${RISE_BODY}${facade ? facade.vertexBody : ''}`);
    if (!facade) return;
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\n${facade.fragment}`)
      // After <normal_fragment_maps> and not a line earlier. Three's fragment
      // chunks run roughnessmap → metalnessmap → normal_fragment_begin →
      // normal_fragment_maps, so `normal` does not exist yet at the roughness
      // chunk: patching there compiles nothing, and a material that fails to
      // compile does not draw — while its customDepthMaterial, untouched by
      // any of this, goes on casting shadows. Twenty campus blocks vanished
      // and left their shadows lying in the fields.
      .replace('#include <normal_fragment_maps>',
               `#include <normal_fragment_maps>\n${facade.fragmentBody}`);
  });
  // Three caches compiled programs by this key, and every family used to
  // return the same one. With a facade on only some of them that would hand
  // the campus's shader to the houses, or the houses' to the campus —
  // whichever compiled first, silently, and differently between runs.
  m.customProgramCacheKey = () => `future:rise:${family}`;
  return m;
}

/**
 * A mesh that belongs to 2045: it grows with the front, casts a shadow that
 * grows with it, and carries whatever facade its family has.
 *
 * Exported so a building that is NOT in `gv-2045-buildings.json` — the
 * National Cyber Innovation Centre, which the scheme sites by rule rather
 * than by footprint — can be one of the scheme's buildings rather than an
 * ornament placed on top of it. The alternative was a second copy of the rise
 * transform, and the shadow pass has already caught this project out once:
 * two copies drift the first time either changes.
 */
export function riseMesh(geometry, family) {
  const mesh = new THREE.Mesh(geometry, riseMaterial(family));
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.frustumCulled = false;
  mesh.customDepthMaterial = depthFor(RISE, RISE_BODY, 'future:rise:depth');
  return mesh;
}

// --- new trees ---------------------------------------------------------------

function growMaterial(base) {
  const m = base.clone();
  return share(m, function grow(shader) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${GROW}\n${NOISE}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
${GROW_BODY}`);
  }, { wind: 0.05 });
}

// --- assembly ----------------------------------------------------------------

/**
 * Everything 2045 adds, and the handle that moves the front.
 *
 * `unitTree` and the today-tree material arrive as arguments rather than
 * imports so that the new hedges and orchards are made of exactly the same
 * geometry as the surveyed woods — a future that used different trees would
 * announce itself as a different dataset.
 */
export async function addFuture(scene, renderer, {
  groundAt, unitTree, treeKinds, directGround = false,
}) {
  const group = new THREE.Group();
  group.name = 'future';

  const buildings = await (await fetch(url(futureMeta.buildingFile))).json();
  // One mesh per family rather than one for all of them. Wall and roof are
  // still vertex colours — two meshes per family drew every building twice —
  // but a family has to be able to stand down on its own, because the moment
  // a real model exists for the campus blocks the extrusions underneath them
  // are z-fighting rubbish rather than a fallback.
  const byFamily = new Map();
  for (const b of buildings) {
    if (!byFamily.has(b.family)) byFamily.set(b.family, []);
    byFamily.get(b.family).push(b);
  }
  const blocks = new Map();
  for (const [family, list] of byFamily) {
    const mesh = new THREE.Mesh(
      futureGeometry(list, futureMeta.families,
                     directGround ? KEYED_GRADE[family] : null),
      riseMaterial(family));
    mesh.name = `future:blocks:${family}`;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.frustumCulled = false;
    mesh.customDepthMaterial = depthFor(RISE, RISE_BODY, 'future:rise:depth');
    group.add(mesh);
    blocks.set(family, mesh);
  }

  const trees = await loadFutureTrees(groundAt, unitTree, treeKinds,
    directGround ? KEYED_GRADE.trees : null);
  if (trees) group.add(trees);

  scene.add(group);

  // The surveyed terrain is named at construction. In a keyed build it has no
  // today texture yet: the future map is its direct material until the
  // measured fallback is prepared, so discovery must not depend on `map`.
  const ground = scene.getObjectByName('terrain');
  let futureTexture = null;
  if (ground) {
    futureTexture = await new THREE.TextureLoader().loadAsync(
      url(futureMeta.colourFile));
    futureTexture.colorSpace = THREE.SRGBColorSpace;
    futureTexture.anisotropy = renderer
      ? renderer.capabilities.getMaxAnisotropy() : 8;
    futureTexture.wrapS = futureTexture.wrapT = THREE.ClampToEdgeWrapping;
    if (directGround) {
      ground.material.map = futureTexture;
      // The colour map supplies the colour directly. The surveyed vertex
      // grade is prepared only with the measured fallback, while still hidden.
      ground.material.vertexColors = false;
      ground.material.roughness = 1;
      ground.material.needsUpdate = true;
    }
    // Both class maps, so the shader can answer the only question that
    // matters over photogrammetry: did 2045 CHANGE this square metre? Indices,
    // so nearest filtering and no colour management — a bilinear tap between
    // "water" and "grass" returns a class nothing is.
    const [todayClasses, futureClasses] = await Promise.all([
      loadClassTexture(),
      loadClassTexture(futureMeta.classFile),
    ]);
    blendGround(ground, futureTexture, todayClasses, futureClasses, directGround);
  }

  // GCHQ's roof is a change to a building that already exists, so it is a
  // colour lerp rather than new geometry — and it is the one image that says
  // what the place has become.
  const change = futureMeta.roofChanges?.[0];
  const gchqRoof = scene.getObjectByName('gchq:roof');
  const gchqFrom = gchqRoof && gchqRoof.material.color.clone();
  const gchqTo = change && new THREE.Color(change.roof);
  if (gchqTo && directGround) gradeColour(gchqTo, KEYED_GRADE.meadow);
  const meadowMix = { value: 0 };
  if (gchqRoof) meadowRoof(gchqRoof.material, meadowMix);
  // How far the front has passed the ring, 0 to 1. Kept because the tiles
  // layer needs it: over photogrammetry our GCHQ roof is the ONLY part of our
  // town still drawn, and it has to arrive with the meadow rather than sit
  // there from the start covering the real one.
  let meadowAt = 0;
  let overTiles = false;

  let wave = 0;
  return {
    group,
    /**
     * The extruded blocks, per family, so a family that gets a real model can
     * hide its own. They stay in the scene rather than being removed: a
     * missing GLB has to fall back to something, and an empty field where a
     * campus should be is worse than a plain box.
     */
    blocks,
    get wave() { return wave; },
    /** Draw our ground only where 2045 changes it: see setGroundMasked. */
    setGroundMasked,
    /** Use today's base map again once the measured fallback is ready. */
    setGroundDirect,
    /** Emit the exact authored-ground classification for probe_light.py. */
    setGroundProbeMask,
    /** Shared with the tile shader that clears photographed roof furniture. */
    get gchqMeadowUniform() { return meadowMix; },
    /**
     * Over photogrammetry, our whole town is hidden except one thing: the
     * ring's 2045 meadow roof, laid over the real building. Overlaying our own
     * geometry is allowed; modifying a tile is not, and this modifies nothing.
     */
    setOverTiles(on) {
      overTiles = !!on;
      if (!gchqRoof) return;
      gchqRoof.material.transparent = overTiles;
      gchqRoof.material.depthWrite = !overTiles;
      gchqRoof.material.opacity = overTiles ? meadowAt : 1;
      gchqRoof.visible = overTiles ? meadowAt > 0.01 : true;
      gchqRoof.material.needsUpdate = true;
    },
    /** How far the front has crossed the ring, 0 to 1. */
    get gchqMeadow() { return meadowAt; },
    /**
     * Where the front is standing, in local metres east. The wave is the
     * scheme's argument and this is the only number that says whether it
     * actually moved: a dial can change a year on screen without the ground
     * under it changing at all, and that failure looks exactly like success.
     */
    get frontX() { return uniforms.uFront.value; },
    /** 0 = today, 1 = the front has crossed the whole box. */
    setWave(t) {
      wave = THREE.MathUtils.clamp(t, 0, 1);
      uniforms.uFront.value = SWEEP_FROM + (SWEEP_TO - SWEEP_FROM) * wave;
      if (gchqRoof && gchqTo) {
        // GCHQ sits at x = 123, so its roof turns when the front reaches it
        // rather than when the toggle is pressed.
        meadowAt = THREE.MathUtils.clamp(
          (uniforms.uFront.value - 123 + SOFT) / (SOFT * 2), 0, 1);
        meadowMix.value = meadowAt;
        gchqRoof.material.color.copy(gchqFrom).lerp(gchqTo, meadowAt);
        if (overTiles) {
          // Fading rather than switching: the real ring is underneath, and a
          // meadow that appears all at once on a photograph of a metal roof
          // reads as a glitch rather than as a proposal.
          gchqRoof.material.opacity = meadowAt;
          gchqRoof.visible = meadowAt > 0.01;
        }
      }
    },
  };
}

async function loadFutureTrees(groundAt, unitTree, treeKinds, grade = null) {
  const buf = await (await fetch(url(futureMeta.treeFile))).arrayBuffer();
  const view = new DataView(buf);
  const count = buf.byteLength / 8;
  if (!count) return null;
  const byKind = treeKinds.map(() => []);
  for (let i = 0; i < count; i++) {
    const o = i * 8;
    byKind[Math.min(view.getUint8(o + 6), treeKinds.length - 1)].push({
      x: view.getInt16(o, true) / 10,
      z: view.getInt16(o + 2, true) / 10,
      h: view.getUint8(o + 4) * 0.25,
      rot: (view.getUint8(o + 5) / 256) * Math.PI * 2,
      spread: view.getUint8(o + 7) / 100,
    });
  }

  const group = new THREE.Group();
  group.name = 'future:trees';
  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  const pos = new THREE.Vector3();
  const tint = new THREE.Color();
  const axis = new THREE.Vector3(0, 1, 0);
  treeKinds.forEach((kind, k) => {
    const list = byKind[k];
    if (!list.length) return;
    const mesh = new THREE.InstancedMesh(
      unitTree(kind),
      growMaterial(new THREE.MeshStandardMaterial({
        color: 0xffffff, roughness: 0.94, vertexColors: true,
        flatShading: true })),
      list.length);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.customDepthMaterial = depthFor(GROW, GROW_BODY, 'future:grow:depth');
    list.forEach((t, i) => {
      pos.set(t.x, groundAt(t.x, t.z) - 0.2, t.z);
      q.setFromAxisAngle(axis, t.rot);
      mesh.setMatrixAt(i, m.compose(pos, q, treeScale(t, scale)));
      treeTint(t, kind, tint);
      // Baked into the instance colour, so unlike the ground it stays graded if
      // the measured fallback takes over below the melt line. A small mismatch
      // at low camera heights against our ungraded existing trees; noted.
      if (grade) gradeColour(tint, grade);
      mesh.setColorAt(i, tint);
    });
    mesh.instanceMatrix.needsUpdate = true;
    if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
    mesh.frustumCulled = false;
    mesh.geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 2000);
    group.add(mesh);
  });
  return group;
}
