// The same world as the map page, lit and graded. Takes the same ?cam / ?look
// / ?clean parameters so any shot can be rendered both ways and compared.

import * as THREE from 'three';
import { OrbitControls } from '../terrain/vendor/OrbitControls.js';
import { buildScene, heightAtLocal, toLocal, sizeX, sizeZ } from '../golden-valley/scene.js';
import { applyLook } from './look.js';
import { addLandCover } from '../golden-valley/landcover.js';
import { buildBuildings } from '../golden-valley/buildings.js';

const app = document.getElementById('app');
const scene = buildScene();

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

// ?bare is the state before Phase 2 — the same light on a blank green ground.
// ?flatroofs keeps the land cover but leaves the buildings as extrusions, so
// the roof pass can be judged on its own from an identical camera.
const bare = params.has('bare');
if (!bare && !params.has('flatroofs')) {
  // Swap the flat-topped extrusions for measured roofs and material
  // families. Done before applyLook, which walks scene.children and would
  // otherwise be re-lighting meshes that are about to be thrown away.
  for (const child of [...scene.children]) {
    if (child.isMesh && child.material && !child.material.vertexColors) {
      scene.remove(child);
    }
  }
  scene.add(buildBuildings());
}
applyLook(scene, renderer, { grade: bare });
if (!bare) await addLandCover(scene, renderer);

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
