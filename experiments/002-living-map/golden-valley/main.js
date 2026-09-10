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
import { legAt } from './paths.js';
import { createPathWalk } from './walk.js';

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
  // The ground point, not a point in the air: the marker's stem is drawn in
  // screen pixels from here upwards, which is what makes it read as planted
  // in the map rather than floating over a picture of one.
  h.anchor = new THREE.Vector3(x, heightAtLocal(x, z), z);
  h.button = document.createElement('button');
  h.button.className = 'hotspot';
  h.button.innerHTML =
    `<span class="label">${h.name}</span><span class="stem"></span><span class="pin"></span>`;
  h.button.onclick = () => player.descend(h);
  app.appendChild(h.button);
}

// --- the path network -------------------------------------------------------
// The footpaths are already painted into the land cover; this is the same
// routes as lines you can point at. ?paths=off leaves the network dark,
// ?paths=on lights it immediately — which is what a capture wants, since it
// has no camera to settle.
const paths = scene.userData.paths;
const pathMode = params.get('paths') ?? (clean ? 'off' : 'auto');
paths.setViewport(renderer);
if (pathMode === 'on') paths.igniteNow();
if (pathMode === 'off') paths.setVisible(false);

const walk = createPathWalk({
  camera,
  controls,
  groundAt: heightAtLocal,
  onState: (state, leg) => renderWalk(state, leg),
});

// The label that follows the pointer along a route. One element, moved,
// rather than one per route: at 65 routes the DOM would be doing more work
// than the renderer.
const routeLabel = document.createElement('div');
routeLabel.id = 'route-label';
routeLabel.hidden = true;
app.appendChild(routeLabel);

const KIND_NAMES = {
  foot: 'Footpath', cycle: 'Cycle route', bridle: 'Bridleway',
  steps: 'Steps', track: 'Track',
};
const routeTitle = (r) => r.name ?? KIND_NAMES[r.kind] ?? 'Path';

// Picking runs at most once a frame, driven by a dirty flag, because a
// pointer emits moves faster than the map draws and there is nothing to be
// learned from testing the same 3,642 points twice between two pictures.
let pointer = null;
let pointerDirty = false;
const canvas = renderer.domElement;

canvas.addEventListener('pointermove', (e) => {
  pointer = [e.clientX, e.clientY];
  pointerDirty = true;
});
canvas.addEventListener('pointerleave', () => {
  pointer = null;
  pointerDirty = true;
});

// A left-drag pans the map, so a click has to be told apart from the start of
// a drag by how far the pointer travelled — not by which button it was.
let downAt = null;
canvas.addEventListener('pointerdown', (e) => {
  downAt = e.button === 0 ? [e.clientX, e.clientY] : null;
});
canvas.addEventListener('pointerup', (e) => {
  if (!downAt) return;
  const moved = Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]);
  downAt = null;
  if (moved > 4 || player.busy || walk.busy || pathMode === 'off') return;
  const hit = paths.pick(e.clientX, e.clientY, camera, innerWidth, innerHeight);
  // A leg, not the route: clicking two kilometres of cycle route has to mean
  // the stretch you were pointing at.
  if (hit) walk.walk(legAt(hit.route, hit.index));
});

function updatePick() {
  if (!pointerDirty) return;
  pointerDirty = false;
  const hit = (pointer && !player.busy && !walk.busy && pathMode !== 'off')
    ? paths.pick(pointer[0], pointer[1], camera, innerWidth, innerHeight)
    : null;
  paths.setHover(hit?.route ?? null);
  canvas.style.cursor = hit ? 'pointer' : '';
  routeLabel.hidden = !hit;
  if (hit) {
    const r = hit.route;
    routeLabel.textContent =
      `${routeTitle(r)} · ${(r.lengthMetres / 1000).toFixed(2)} km`;
    routeLabel.classList.toggle('named', r.tier === 'named');
    routeLabel.style.left = `${hit.screen[0]}px`;
    routeLabel.style.top = `${hit.screen[1]}px`;
  }
}

// Ignition waits for the camera to settle, which is the moment the map stops
// being something you are moving and starts being something you are reading.
// It happens once: lighting is film, staying lit is interface.
let ignitionStarted = pathMode !== 'auto';
let stillMs = 0;
const lastCam = camera.position.clone();
function updateIgnition(dtMs) {
  if (ignitionStarted || !controls.enabled) return;
  const moved = camera.position.distanceTo(lastCam);
  lastCam.copy(camera.position);
  stillMs = moved < 0.8 ? stillMs + dtMs : 0;
  if (stillMs > 650) {
    paths.ignite(worldSeconds());
    ignitionStarted = true;
  }
}

// --- the place panel --------------------------------------------------------
const panel = document.getElementById('panel');
const panelTitle = document.getElementById('panel-title');
const panelBody = document.getElementById('panel-body');
const panelNote = document.getElementById('panel-note');
// One button, two ways of having arrived somewhere.
document.getElementById('panel-back').onclick = () => {
  if (walk.inside) walk.returnToMap();
  else player.returnToMap();
};

function render(state, hotspot) {
  const inPlace = state === 'arrived';
  panel.hidden = clean || !inPlace;
  document.body.classList.toggle('in-place', inPlace && !clean);
  app.classList.toggle('flying', state === 'descending' || state === 'returning');
  if (inPlace) {
    panelTitle.textContent = hotspot.name;
    panelBody.textContent = hotspot.blurb;
    panelNote.textContent = hotspot.clip
      ? 'Arrived by pre-rendered descent.'
      : 'Descent flown live — no clip generated for this place yet.';
  }
}

function renderWalk(state, leg) {
  const arrived = state === 'arrived';
  panel.hidden = clean || !arrived;
  document.body.classList.toggle('in-place', arrived && !clean);
  app.classList.toggle('flying', state === 'diving' || state === 'returning');
  routeLabel.hidden = routeLabel.hidden || walk.busy;
  if (!arrived) return;
  const r = leg.route;
  panelTitle.textContent = routeTitle(r);
  panelBody.textContent =
    `${Math.round(leg.length)} m of it, walked. The whole route runs `
    + `${(r.lengthMetres / 1000).toFixed(2)} km inside this box — surveyed by `
    + `OpenStreetMap, laid on Environment Agency LiDAR, and here before `
    + `anything is built.`;
  panelNote.textContent = 'Walked live — no clip generated for this leg yet.';
}

// --- the opening ------------------------------------------------------------
// The reference opens on a title over a moving landscape rather than on a
// loading bar, and the move is the point: by the time the words have gone,
// you have already watched the vale for fifteen seconds and the map is
// somewhere you have been rather than a thing you have been handed.
const intro = document.getElementById('intro');
const introSkipped = clean || params.has('descend');
if (!introSkipped) {
  const from = new THREE.Vector3(-1220, 820, 1560);
  const to = camera.position.clone();
  const OPEN_MS = 15000;
  camera.position.copy(from);
  controls.enabled = false;
  intro.hidden = false;
  document.body.classList.add('intro-open');
  const t0 = performance.now();
  const drift = () => {
    if (!controls.enabled) {
      // Ease out, so the move is quickest at the start and has all but
      // stopped by the time anyone reads as far as the button.
      const k = Math.min(1, (performance.now() - t0) / OPEN_MS);
      camera.position.lerpVectors(from, to, 1 - Math.pow(1 - k, 3));
      camera.lookAt(controls.target);
      requestAnimationFrame(drift);
    }
  };
  drift();
  document.getElementById('intro-go').onclick = () => {
    intro.classList.add('leaving');
    document.body.classList.remove('intro-open');
    setTimeout(() => { intro.hidden = true; }, 900);
    // Hand over from wherever the drift has reached, rather than cutting to
    // the resting camera and undoing the move.
    controls.enabled = true;
    controls.update();
  };
}

// --- frame ------------------------------------------------------------------
const v = new THREE.Vector3();
let lastFrame = performance.now();
function tick() {
  requestAnimationFrame(tick);
  const now = performance.now();
  const dtMs = Math.min(now - lastFrame, 100);
  lastFrame = now;
  // The walker owns the camera while it has it, so orbit damping must not
  // fight it for the same three numbers.
  const walking = walk.update(now);
  if (controls.enabled && !walking) controls.update();
  updateIgnition(dtMs);
  updatePick();
  paths.update(worldSeconds());
  // The descent clips were rendered before the network existed. Cutting to
  // one with the paths lit would show a seam that is nothing to do with the
  // ground, so they go dark for the descent and come back as they were.
  if (pathMode !== 'off') paths.setVisible(!player.busy && !player.inside);
  // One clock for the whole world, and the descent player is allowed to hold
  // it still or rebase it — which is how a pre-rendered clip and the live
  // canvas end up under the same cloud.
  updateLife(worldSeconds());
  renderer.render(scene, camera);
  for (const h of hotspots) {
    // A hotspot you are standing in should not offer to take you there.
    const hide = player.busy || player.inside === h || walk.busy || !!walk.inside;
    v.copy(h.anchor).project(camera);
    h.button.hidden = hide || v.z > 1;
    // Clamp, so a place near the edge of the box still reads as a label
    // rather than half a word running off the screen.
    h.button.style.left =
      `${THREE.MathUtils.clamp((v.x * 0.5 + 0.5) * innerWidth, 140, innerWidth - 140)}px`;
    h.button.style.top =
      `${THREE.MathUtils.clamp((-v.y * 0.5 + 0.5) * innerHeight, 60, innerHeight - 20)}px`;
    // Fade with distance rather than showing every marker at the same weight:
    // three labels shouting equally from a 2 km box is a legend, not a place.
    const d = camera.position.distanceTo(h.anchor);
    h.button.style.setProperty('--k',
      THREE.MathUtils.clamp(1.3 - d / 4200, 0.45, 1).toFixed(2));
  }
}
tick();

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  // The ribbon's minimum width is in pixels, so it has to be told how many
  // pixels tall the window now is or every path changes width on a resize.
  paths.setViewport(renderer);
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

// A handle on the running map, for the capture scripts and the flow tests.
// Everything here is already reachable from the page; naming it saves a test
// from reaching into module scope, and saves a capture from screenshotting a
// compositor that under software GL is slower than the render it is waiting
// for. Nothing in the page reads it.
window.__map = {
  renderer, scene, camera, controls, paths, walk, player, hotspots,
  groundAt: heightAtLocal,
};
window.__terrainReady = true;
