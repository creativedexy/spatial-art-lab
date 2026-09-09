// The comparison harness.
//
// Phases 1–3 now live in ../golden-valley/scene.js and the map page renders
// them, so this page's job has changed: it is no longer where the look is
// developed, it is where any two states of it can be photographed from one
// identical camera. Every before-and-after sheet in exports/ was made here.
//
//   (nothing)    the world as the map renders it
//   ?flatroofs   land cover and trees, buildings back to flat extrusions
//   ?bare        Phase 1 only — the same light on a blank green ground
//
// Takes the same ?cam / ?look / ?clean parameters as the map page, so a shot
// can be rendered in any of the three states and diffed.

import * as THREE from 'three';
import { OrbitControls } from '../terrain/vendor/OrbitControls.js';
import {
  buildScene, buildWorld, heightAtLocal, toLocal, sizeX, sizeZ,
} from '../golden-valley/scene.js';
import { applyLook } from '../golden-valley/look.js';
import { addLandCover } from '../golden-valley/landcover.js';

const app = document.getElementById('app');

const params = new URLSearchParams(location.search);
const camPos = (params.get('cam') ?? '-750,520,1050').split(',').map(Number);
if (params.has('clean')) {
  for (const id of ['credit', 'hint']) document.getElementById(id).hidden = true;
}

const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 2, 20000);
camera.position.set(...camPos);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
app.appendChild(renderer.domElement);

const bare = params.has('bare');
const flatRoofs = params.has('flatroofs');
let scene;
if (bare || flatRoofs) {
  // The earlier states are assembled by hand from the same parts, so a
  // comparison is never against a differently-built world — only against the
  // same world with one pass left out.
  scene = buildScene();
  applyLook(scene, renderer, { grade: bare });
  if (flatRoofs) await addLandCover(scene, renderer, heightAtLocal);
} else {
  scene = await buildWorld({ renderer });
}

const controls = new OrbitControls(camera, renderer.domElement);
controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
controls.screenSpacePanning = false;
controls.enableDamping = true;
controls.minDistance = 60;
controls.maxDistance = 3600;
controls.maxPolarAngle = 1.45;
const look = params.get('look')?.split(',').map(Number) ?? toLocal(391523, 222336);
controls.target.set(look[0], heightAtLocal(look[0], look[1]), look[1]);
controls.addEventListener('change', () => {
  controls.target.x = THREE.MathUtils.clamp(controls.target.x, -sizeX / 2, sizeX / 2);
  controls.target.z = THREE.MathUtils.clamp(controls.target.z, -sizeZ / 2, sizeZ / 2);
});

function tick() {
  requestAnimationFrame(tick);
  controls.update();
  renderer.render(scene, camera);
}
tick();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

window.__terrainReady = true;
window.__dbg = () => {
  const sun = scene.children.find((c) => c.isDirectionalLight);
  return {
    shadowsOn: renderer.shadowMap.enabled,
    hasMap: !!(sun && sun.shadow && sun.shadow.map),
    castCount: scene.children.filter((c) => c.isMesh && c.castShadow).length,
    meshes: scene.children.filter((c) => c.isMesh).length,
    caps: renderer.capabilities.maxTextureSize,
  };
};
