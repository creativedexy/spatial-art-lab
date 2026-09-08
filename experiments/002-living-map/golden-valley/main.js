// Living map, Sprint 1 vertical slice: Golden Valley / west Cheltenham at
// full 1 m LiDAR resolution, true scale, with every OSM building footprint
// extruded to its DSM-minus-DTM measured height. White-model archviz look;
// GCHQ's doughnut picked out in slate. The world itself is built by
// ./scene.js, which the descent seam test shares.

import * as THREE from 'three';
import { OrbitControls } from '../terrain/vendor/OrbitControls.js';
import { buildScene, heightAtLocal, toLocal, sizeX, sizeZ, PLACES } from './scene.js';

const app = document.getElementById('app');
const scene = buildScene();

// ?cam=x,y,z&look=x,z frames a specific shot (used to render descent
// endpoints); ?clean=1 hides labels and credits for capture.
const params = new URLSearchParams(location.search);
const camPos = (params.get('cam') ?? '-750,520,1050').split(',').map(Number);
if (params.get('clean')) {
  document.getElementById('credit').hidden = true;
  document.getElementById('hint').hidden = true;
}

const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 2, 20000);
camera.position.set(...camPos);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
app.appendChild(renderer.domElement);

// --- labels -----------------------------------------------------------------
const places = params.get('clean') ? [] : Object.values(PLACES);
for (const p of places) {
  const [x, z] = toLocal(p.e, p.n);
  p.anchor = new THREE.Vector3(x, heightAtLocal(x, z) + p.lift, z);
  p.div = document.createElement('div');
  p.div.className = 'label';
  p.div.textContent = p.name;
  app.appendChild(p.div);
}

// --- controls ---------------------------------------------------------------
const controls = new OrbitControls(camera, renderer.domElement);
controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
controls.screenSpacePanning = false;
controls.enableDamping = true;
controls.minDistance = 60;
controls.maxDistance = 3600;
controls.maxPolarAngle = 1.38;
const look = params.get('look')?.split(',').map(Number)
  ?? toLocal(PLACES.doughnut.e, PLACES.doughnut.n); // default: open on the doughnut
controls.target.set(look[0], heightAtLocal(look[0], look[1]), look[1]);
controls.addEventListener('change', () => {
  controls.target.x = THREE.MathUtils.clamp(controls.target.x, -sizeX / 2, sizeX / 2);
  controls.target.z = THREE.MathUtils.clamp(controls.target.z, -sizeZ / 2, sizeZ / 2);
});

const v = new THREE.Vector3();
function tick() {
  requestAnimationFrame(tick);
  controls.update();
  renderer.render(scene, camera);
  for (const p of places) {
    v.copy(p.anchor).project(camera);
    p.div.hidden = v.z > 1;
    p.div.style.left = `${(v.x * 0.5 + 0.5) * innerWidth}px`;
    p.div.style.top = `${(-v.y * 0.5 + 0.5) * innerHeight}px`;
  }
}
tick();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

window.__terrainReady = true;
