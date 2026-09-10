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

const url = (f) => new URL(f, import.meta.url).href;
export const futureMeta = await (await fetch(url('gv-2045-meta.json'))).json();

const SWEEP_FROM = -1250;     // local metres: the front starts west of the box
const SWEEP_TO = 1250;
const SOFT = 150;             // metres the front takes to pass a point
const RAGGED = 110;           // metres of noise on the front

// Shared by every material the wave touches, so they cannot disagree about
// where the front is.
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
export function blendGround(mesh, futureTexture) {
  const m = mesh.material;
  const previous = m.onBeforeCompile;
  m.onBeforeCompile = (shader) => {
    if (previous) previous(shader);
    Object.assign(shader.uniforms, uniforms,
                  { uFutureMap: { value: futureTexture } });
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
         uniform float uFront; uniform float uSoft; uniform float uRagged;
         varying vec3 vFutureWorld;
         ${NOISE}`)
      .replace('#include <map_fragment>',
        `#include <map_fragment>
         {
           // The sampler is sRGB, so the GPU has already linearised this and
           // it can be mixed with diffuseColor directly.
           vec4 futureTexel = texture2D(uFutureMap, vMapUv);
           diffuseColor.rgb = mix(diffuseColor.rgb, futureTexel.rgb,
                                  futureAt(vFutureWorld));
         }`);
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
 * a roof — which is also why it can afford to carry two extra attributes.
 */
function futureGeometry(list, palette) {
  const pos = [];
  const base = [];
  const anchor = [];
  const col = [];
  let tint = new THREE.Color();
  const push = (x, y, z, b, ax, az) => {
    pos.push(x, y, z);
    base.push(b);
    anchor.push(ax, az);
    col.push(tint.r, tint.g, tint.b);
  };
  const quad = (a, b, c, d, bs, ax, az) => {
    push(...a, bs, ax, az); push(...b, bs, ax, az); push(...c, bs, ax, az);
    push(...a, bs, ax, az); push(...c, bs, ax, az); push(...d, bs, ax, az);
  };

  for (const b of list) {
    const spec = palette[b.family] ?? { wall: '#e6dcc6', roof: '#7d8f5a' };
    const wallColour = new THREE.Color(spec.wall);
    const roofColour = new THREE.Color(spec.roof);
    tint = wallColour;
    const ring = b.ring;
    const y0 = b.base - 0.4;
    const ax = ring.reduce((s, p) => s + p[0], 0) / ring.length;
    const az = ring.reduce((s, p) => s + p[1], 0) / ring.length;
    const eaves = y0 + (b.roof === 'flat' ? b.height : b.eaves);

    for (let i = 0; i < ring.length; i++) {
      const [x1, z1] = ring[i];
      const [x2, z2] = ring[(i + 1) % ring.length];
      quad([x1, y0, z1], [x2, y0, z2], [x2, eaves, z2], [x1, eaves, z1],
           y0, ax, az);
    }

    tint = roofColour;
    if (b.roof === 'flat') {
      const [p, q, r, s] = ring;
      quad([p[0], eaves, p[1]], [q[0], eaves, q[1]],
           [r[0], eaves, r[1]], [s[0], eaves, s[1]], y0, ax, az);
    } else {
      // A gable on a quad: the ridge runs between the midpoints of the two
      // ends, which for these blocks is the long axis by construction.
      const [p, q, r, s] = ring;
      const mid = (a, c) => [(a[0] + c[0]) / 2, (a[1] + c[1]) / 2];
      const m1 = mid(p, s);
      const m2 = mid(q, r);
      const ridge = y0 + b.ridge;
      quad([p[0], eaves, p[1]], [q[0], eaves, q[1]],
           [m2[0], ridge, m2[1]], [m1[0], ridge, m1[1]], y0, ax, az);
      quad([r[0], eaves, r[1]], [s[0], eaves, s[1]],
           [m1[0], ridge, m1[1]], [m2[0], ridge, m2[1]], y0, ax, az);
      // The two triangular ends.
      for (const [a, c, m] of [[p, s, m1], [q, r, m2]]) {
        push(a[0], eaves, a[1], y0, ax, az);
        push(c[0], eaves, c[1], y0, ax, az);
        push(m[0], ridge, m[1], y0, ax, az);
      }
    }
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aBase', new THREE.Float32BufferAttribute(base, 1));
  g.setAttribute('aAnchor', new THREE.Float32BufferAttribute(anchor, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
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

function riseMaterial() {
  const m = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 0.85 });
  return share(m, function future(shader) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>\n${RISE}\n${NOISE}`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
${RISE_BODY}`);
  });
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
export async function addFuture(scene, renderer, { groundAt, unitTree, treeKinds }) {
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
      futureGeometry(list, futureMeta.families), riseMaterial());
    mesh.name = `future:blocks:${family}`;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.frustumCulled = false;
    mesh.customDepthMaterial = depthFor(RISE, RISE_BODY, 'future:rise:depth');
    group.add(mesh);
    blocks.set(family, mesh);
  }

  const trees = await loadFutureTrees(groundAt, unitTree, treeKinds);
  if (trees) group.add(trees);

  scene.add(group);

  // Today's terrain, whichever mesh carries the surveyed ground.
  const ground = scene.children.find(
    (o) => o.isMesh && o.material && o.material.map && o.material.vertexColors);
  let futureTexture = null;
  if (ground) {
    futureTexture = await new THREE.TextureLoader().loadAsync(
      url(futureMeta.colourFile));
    futureTexture.colorSpace = THREE.SRGBColorSpace;
    futureTexture.anisotropy = renderer
      ? renderer.capabilities.getMaxAnisotropy() : 8;
    futureTexture.wrapS = futureTexture.wrapT = THREE.ClampToEdgeWrapping;
    blendGround(ground, futureTexture);
  }

  // GCHQ's roof is a change to a building that already exists, so it is a
  // colour lerp rather than new geometry — and it is the one image that says
  // what the place has become.
  const change = futureMeta.roofChanges?.[0];
  const gchqRoof = scene.getObjectByName('gchq:roof');
  const gchqFrom = gchqRoof && gchqRoof.material.color.clone();
  const gchqTo = change && new THREE.Color(change.roof);

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
    /** 0 = today, 1 = the front has crossed the whole box. */
    setWave(t) {
      wave = THREE.MathUtils.clamp(t, 0, 1);
      uniforms.uFront.value = SWEEP_FROM + (SWEEP_TO - SWEEP_FROM) * wave;
      if (gchqRoof && gchqTo) {
        // GCHQ sits at x = 123, so its roof turns when the front reaches it
        // rather than when the toggle is pressed.
        const at = THREE.MathUtils.clamp(
          (uniforms.uFront.value - 123 + SOFT) / (SOFT * 2), 0, 1);
        gchqRoof.material.color.copy(gchqFrom).lerp(gchqTo, at);
      }
    },
  };
}

async function loadFutureTrees(groundAt, unitTree, treeKinds) {
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
        color: 0xffffff, roughness: 0.92, flatShading: true })),
      list.length);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.customDepthMaterial = depthFor(GROW, GROW_BODY, 'future:grow:depth');
    list.forEach((t, i) => {
      pos.set(t.x, groundAt(t.x, t.z) - 0.2, t.z);
      q.setFromAxisAngle(axis, t.rot);
      scale.set(t.h * t.spread, t.h, t.h * t.spread);
      mesh.setMatrixAt(i, m.compose(pos, q, scale));
      const v = 0.78 + ((t.rot * 97) % 1) * 0.44;
      tint.setHex(kind.colour).multiplyScalar(v);
      tint.offsetHSL(((t.spread * 31) % 1 - 0.5) * 0.06, 0, 0);
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
