// Living map, Golden Valley / west Cheltenham at full 1 m LiDAR resolution,
// true scale: every OSM building footprint extruded to its DSM-minus-DTM
// measured height, roofed from the same survey, standing on surveyed land
// cover under a low afternoon sun. The world itself is built by ./scene.js,
// which the descent seam test shares — one module, so the live canvas and a
// pre-rendered descent can never disagree about what the place looks like.
//
// Clicking a place descends into it — the mechanism Session C measured,
// driven by ../descent/hotspots.json.

import * as THREE from 'three';
import { OrbitControls } from '../terrain/vendor/OrbitControls.js';
import {
  buildWorld, updateLife, worldSeconds, heightAtLocal, toLocal, sizeX, sizeZ,
} from './scene.js';
import { loadHotspots } from '../descent/path.js';
import { createDescentPlayer } from '../descent/player.js';

const app = document.getElementById('app');

// ?cam=x,y,z&look=x,z frames a specific shot (used to render descent
// endpoints); ?clean=1 hides every overlay for capture.
const params = new URLSearchParams(location.search);
const clean = params.has('clean');
const camPos = (params.get('cam') ?? '-750,520,1050').split(',').map(Number);
if (clean) {
  for (const id of ['credit', 'hint', 'panel']) document.getElementById(id).hidden = true;
}

const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 2, 20000);
camera.position.set(...camPos);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
app.appendChild(renderer.domElement);

// After the renderer, because tone mapping and the shadow map live on it.
const scene = await buildWorld({ renderer });

// --- controls ---------------------------------------------------------------
const controls = new OrbitControls(camera, renderer.domElement);
controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
controls.screenSpacePanning = false;
controls.enableDamping = true;
controls.minDistance = 60;
controls.maxDistance = 3600;
controls.maxPolarAngle = 1.38;
const look = params.get('look')?.split(',').map(Number) ?? toLocal(391523, 222336);
controls.target.set(look[0], heightAtLocal(look[0], look[1]), look[1]);
controls.addEventListener('change', () => {
  controls.target.x = THREE.MathUtils.clamp(controls.target.x, -sizeX / 2, sizeX / 2);
  controls.target.z = THREE.MathUtils.clamp(controls.target.z, -sizeZ / 2, sizeZ / 2);
});

// --- hotspots ---------------------------------------------------------------
const hotspots = clean ? [] : await loadHotspots();
// ?live=1 ignores every clip and flies each descent live — useful to compare
// the two, and to exercise the path where video playback is unavailable.
if (params.has('live')) for (const h of hotspots) h.clip = null;
const player = createDescentPlayer({
  camera,
  controls,
  container: app,
  groundAt: heightAtLocal,
  clipBase: new URL('../descent/', import.meta.url),
  onState: (state, hotspot) => render(state, hotspot),
});
// Start the clips arriving now, quietly, rather than when someone clicks.
player.prefetchClips(hotspots);

for (const h of hotspots) {
  const [x, z] = toLocal(h.e, h.n);
  h.anchor = new THREE.Vector3(x, heightAtLocal(x, z) + 40, z);
  h.button = document.createElement('button');
  h.button.className = 'hotspot';
  h.button.innerHTML = `<span class="dot"></span>${h.name}`;
  h.button.onclick = () => player.descend(h);
  app.appendChild(h.button);
}

// --- the place panel --------------------------------------------------------
const panel = document.getElementById('panel');
const panelTitle = document.getElementById('panel-title');
const panelBody = document.getElementById('panel-body');
const panelNote = document.getElementById('panel-note');
document.getElementById('panel-back').onclick = () => player.returnToMap();

function render(state, hotspot) {
  const inPlace = state === 'arrived';
  panel.hidden = clean || !inPlace;
  app.classList.toggle('flying', state === 'descending' || state === 'returning');
  if (inPlace) {
    panelTitle.textContent = hotspot.name;
    panelBody.textContent = hotspot.blurb;
    panelNote.textContent = hotspot.clip
      ? 'Arrived by pre-rendered descent.'
      : 'Descent flown live — no clip generated for this place yet.';
  }
}

// --- frame ------------------------------------------------------------------
const v = new THREE.Vector3();
function tick() {
  requestAnimationFrame(tick);
  if (controls.enabled) controls.update();
  // One clock for the whole world, and the descent player is allowed to hold
  // it still or rebase it — which is how a pre-rendered clip and the live
  // canvas end up under the same cloud.
  updateLife(worldSeconds());
  renderer.render(scene, camera);
  for (const h of hotspots) {
    // A hotspot you are standing in should not offer to take you there.
    const hide = player.busy || player.inside === h;
    v.copy(h.anchor).project(camera);
    h.button.hidden = hide || v.z > 1;
    // Clamp, so a place near the edge of the box still reads as a label
    // rather than half a word running off the screen.
    h.button.style.left =
      `${THREE.MathUtils.clamp((v.x * 0.5 + 0.5) * innerWidth, 90, innerWidth - 90)}px`;
    h.button.style.top =
      `${THREE.MathUtils.clamp((-v.y * 0.5 + 0.5) * innerHeight, 30, innerHeight - 30)}px`;
  }
}
tick();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  player.resize(camera.aspect);
  renderer.setSize(innerWidth, innerHeight);
});

// ?descend=<id> runs a descent immediately, which is how arrival stills are
// captured and how the flow is exercised without a mouse. It lives at the
// very bottom on purpose: it calls straight into the player, whose state
// callback reaches the panel constants above, and those are not initialised
// until this module has finished evaluating.
const auto = params.get('descend');
if (auto) {
  const target = hotspots.find((h) => h.id === auto);
  if (target) player.descend(target);
  else console.warn(`no hotspot with id "${auto}"`);
}

window.__terrainReady = true;
