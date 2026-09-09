// Structure passes — what we hand a generator instead of a photograph.
//
// The bet behind this page: an image or video model conditioned on our render
// does not need our render to be *realistic*, it needs it to be
// *unambiguous*. It can invent brick, slate, tarmac wear and undergrowth. It
// cannot invent that GCHQ is 14.8 m tall on a 52.7 m base, that the ridge
// runs with the street, or the shape of the ground under all of it. Those we
// have, measured, and these are the passes that say so:
//
//   beauty   the map as it renders — composition, light, colour
//   depth    linear view depth, near white, far black, with the near and far
//            planes written into the sidecar so the number means something
//   normal   world-space normals — surface orientation, which is what tells a
//            model a roof is a roof and not a paving slab
//   mask     flat colour by category: ground, road, water, building, tree
//
// All four are rendered from one camera, at one instant, with the wind
// switched off and the birds hidden — see setStructureMode. A pass that
// disagrees with the beauty frame by a metre is worse than no pass at all.
//
//   ?cam=x,y,z  ?look=x,z  ?pass=beauty|depth|normal|mask  ?size=W,H

import * as THREE from 'three';
import { buildWorld, updateLife, heightAtLocal, toLocal } from '../golden-valley/scene.js';
import { setStructureMode } from '../golden-valley/life.js';
import { loadClassTexture, coverMeta } from '../golden-valley/landcover.js';

const params = new URLSearchParams(location.search);
const pass = params.get('pass') ?? 'beauty';
const [W, H] = (params.get('size') ?? '1280,720').split(',').map(Number);
const camPos = (params.get('cam') ?? '-420,300,650').split(',').map(Number);
const look = params.get('look')?.split(',').map(Number) ?? toLocal(391523, 222336);
const lift = Number(params.get('lift') ?? 0);
// The depth range is fitted to what the camera can actually see rather than
// given: a hand-picked near and far turned the whole approach shot white,
// because a 40 m near plane on a view whose nearest ground is 90 m away
// spends most of its range on empty air. These are only the outer bounds of
// the search, and the fitted values are what the sidecar records.
const nearLimit = Number(params.get('near') ?? 5);
const farLimit = Number(params.get('far') ?? 8000);
let near = nearLimit;
let far = farLimit;

const camera = new THREE.PerspectiveCamera(
  Number(params.get('fov') ?? 48), W / H, 2, 20000);
camera.position.set(...camPos);
camera.lookAt(look[0], heightAtLocal(look[0], look[1]) + lift, look[1]);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
document.body.appendChild(renderer.domElement);

const scene = await buildWorld({ renderer });
setStructureMode(true);
updateLife(0);

// --- the passes -------------------------------------------------------------
// begin_vertex and project_vertex are included rather than hand-written
// because they are what carry instancing: without them every one of the 9,181
// trees renders at the origin, which looks like a bug in the terrain.
const CHUNKS = `
  #include <common>
  #include <batching_pars_vertex>
  #include <logdepthbuf_pars_vertex>`;

const depthMaterial = new THREE.ShaderMaterial({
  uniforms: { uNear: { value: near }, uFar: { value: far }, uPack: { value: 0 } },
  vertexShader: `
    ${CHUNKS}
    varying float vDepth;
    void main() {
      #include <begin_vertex>
      #include <project_vertex>
      vDepth = -mvPosition.z;
    }`,
  fragmentShader: `
    uniform float uNear, uFar, uPack;
    varying float vDepth;
    void main() {
      if (uPack > 0.5) {
        // Measuring pass: distance packed across 24 bits so it can be read
        // back in metres. The background stays exactly zero, which geometry
        // can never be, so sky is unambiguous when the range is fitted.
        float z = clamp(vDepth / uFar, 0.0, 0.999999);
        float r = floor(z * 255.0) / 255.0;
        float g = floor(fract(z * 255.0) * 255.0) / 255.0;
        float b = fract(z * 65025.0);
        gl_FragColor = vec4(r, g, b, 1.0);
        return;
      }
      // Near white, far black — the convention depth-conditioned models are
      // trained on. Clamped rather than wrapped, so ground beyond the far
      // plane reads as distance and not as a second hill.
      float d = 1.0 - clamp((vDepth - uNear) / (uFar - uNear), 0.0, 1.0);
      gl_FragColor = vec4(vec3(d), 1.0);
    }`,
});

/** Read the frame back and find the depth range the camera actually sees. */
function fitDepthRange() {
  depthMaterial.uniforms.uPack.value = 1;
  depthMaterial.uniforms.uFar.value = farLimit;
  scene.overrideMaterial = depthMaterial;
  renderer.render(scene, camera);
  scene.overrideMaterial = null;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(renderer.domElement, 0, 0);
  const px = ctx.getImageData(0, 0, W, H).data;
  const seen = [];
  // Every fourth pixel in each direction: a sixteenth of the work, and the
  // 2nd and 98th percentiles do not move.
  for (let y = 0; y < H; y += 4) {
    for (let x = 0; x < W; x += 4) {
      const i = (y * W + x) * 4;
      const z = (px[i] / 255 + px[i + 1] / 65025 + px[i + 2] / 16581375) * farLimit;
      if (z > 0.001) seen.push(z);
    }
  }
  if (seen.length < 32) return;                 // nothing but sky; leave as is
  seen.sort((a, b) => a - b);
  const at = (q) => seen[Math.min(seen.length - 1, Math.floor(q * seen.length))];
  // Trim the tails: one chimney at the horizon should not flatten the town.
  near = Math.max(nearLimit, at(0.02) * 0.97);
  far = Math.min(farLimit, at(0.98) * 1.03);
  depthMaterial.uniforms.uPack.value = 0;
  depthMaterial.uniforms.uNear.value = near;
  depthMaterial.uniforms.uFar.value = far;
}

const normalMaterial = new THREE.ShaderMaterial({
  vertexShader: `
    ${CHUNKS}
    varying vec3 vNormalW;
    void main() {
      #include <beginnormal_vertex>
      #include <defaultnormal_vertex>
      #include <begin_vertex>
      #include <project_vertex>
      vNormalW = normalize(mat3(modelMatrix) * objectNormal);
    }`,
  fragmentShader: `
    varying vec3 vNormalW;
    void main() { gl_FragColor = vec4(normalize(vNormalW) * 0.5 + 0.5, 1.0); }`,
});

// Flat colour by what a thing *is*, in hues far enough apart to survive a
// resize. The palette is arbitrary but stable and written into the sidecar,
// so a segmentation-conditioned model can be told which colour means roof.
//
// The ground is not one category. Phase 2 wrote a class per square metre and
// this is the second thing to read it: the mask separates carriageway from
// pasture from water without a single extra mesh, which is the difference
// between a mask that says "ground" and one a model can actually condition on.
const MASK = {
  sky: 0x000000, building: 0xd94f3d, tree: 0x7ad14f,
  field: 0x3f8f3a, wood: 0x1f5f2a, hard: 0x9a9a9a,
  road: 0x4a4a4a, water: 0x2d6fb5,
};
const GROUND_CLASS = {
  farmland: 'field', meadow: 'field', grass: 'field', pitch: 'field',
  park: 'field', scrub: 'wood', wood: 'wood',
  residential: 'hard', hardstanding: 'hard', parking: 'hard',
  water: 'water', path: 'road', road_minor: 'road', road: 'road', rail: 'road',
};
// Set without colour conversion. A structure pass is data, not a picture:
// three treats a hex as sRGB and converts it into the working space, and the
// renderer converts back on the way out — which is fine for something you
// look at and wrong for something a model reads as a label. Written linear
// and read out linear, the pixel equals the number in the sidecar.
const rgb = (v) => new THREE.Color().setHex(v, THREE.LinearSRGBColorSpace);
const classPalette = Object.entries(coverMeta.classes)
  .sort((a, b) => a[1].index - b[1].index)
  .map(([name]) => rgb(MASK[GROUND_CLASS[name] ?? 'field']));

const groundMaskMaterial = new THREE.ShaderMaterial({
  uniforms: {
    uClass: { value: await loadClassTexture() },
    uPalette: { value: classPalette },
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
  fragmentShader: `
    uniform sampler2D uClass;
    uniform vec3 uPalette[${classPalette.length}];
    varying vec2 vUv;
    void main() {
      int i = int(texture2D(uClass, vUv).r * 255.0 + 0.5);
      gl_FragColor = vec4(uPalette[clamp(i, 0, ${classPalette.length - 1})], 1.0);
    }`,
});

const maskMaterials = Object.fromEntries(Object.entries(MASK).map(
  ([k, v]) => [k, new THREE.MeshBasicMaterial({ color: rgb(v) })]));

function maskMaterialFor(obj) {
  if (obj.parent && obj.parent.name === 'trees') return maskMaterials.tree;
  if (obj.material && obj.material.vertexColors) return groundMaskMaterial;
  return maskMaterials.building;
}

function render() {
  if (pass === 'beauty') {
    setStructureMode(true);
    renderer.render(scene, camera);
    return;
  }
  // Tone mapping and sRGB encoding are for pictures. Every other pass here is
  // a measurement — a depth in metres, a normal vector, a class label — and a
  // filmic curve applied to a number is just a corrupted number.
  const savedTone = renderer.toneMapping;
  const savedSpace = renderer.outputColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  const skyBackground = rgb(pass === 'mask' ? MASK.sky : 0x000000);
  const previousFog = scene.fog;
  scene.fog = null;                       // fog is atmosphere, not structure
  scene.background = skyBackground;
  const dome = scene.children.find((c) => c.isMesh && c.geometry.type === 'SphereGeometry');
  const domeWasVisible = dome ? dome.visible : false;
  if (dome) dome.visible = false;

  if (pass === 'mask') {
    const saved = new Map();
    scene.traverse((o) => {
      if (!o.isMesh || o === dome) return;
      saved.set(o, o.material);
      o.material = maskMaterialFor(o);
    });
    renderer.render(scene, camera);
    for (const [o, m] of saved) o.material = m;
  } else if (pass === 'depth') {
    fitDepthRange();
    scene.overrideMaterial = depthMaterial;
    renderer.render(scene, camera);
    scene.overrideMaterial = null;
  } else {
    scene.overrideMaterial = normalMaterial;
    renderer.render(scene, camera);
    scene.overrideMaterial = null;
  }

  if (dome) dome.visible = domeWasVisible;
  scene.fog = previousFog;
  scene.background = null;
  renderer.toneMapping = savedTone;
  renderer.outputColorSpace = savedSpace;
}
render();

window.__pass = {
  pass, size: [W, H], cam: camPos, look, fov: camera.fov,
  depth: pass === 'depth'
    ? { nearMetres: Math.round(near * 10) / 10, farMetres: Math.round(far * 10) / 10,
        encoding: 'near=white, far=black, linear in view space, range fitted to the frame' }
    : null,
  maskColours: pass === 'mask'
    ? Object.fromEntries(Object.entries(MASK).map(([k, v]) => [k, `#${v.toString(16).padStart(6, '0')}`]))
    : null,
};
window.__terrainReady = true;
