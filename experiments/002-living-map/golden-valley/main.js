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
  pinWorld, releaseWorld,
} from './scene.js';
import { loadHotspots } from '../descent/path.js';
import { createDescentPlayer } from '../descent/player.js';
import { legAt } from './paths.js';
import { createPathWalk } from './walk.js';
import { createPlaces } from './places.js';
import { thin } from './declutter.js';
import { addTiles } from './tiles.js';
import { addScheme } from './scheme.js';
import { mark } from './stage.js';

const app = document.getElementById('app');

// The licence line is required by OGL and ODbL both, so on a phone it is
// collapsed to one tappable line rather than shortened or dropped. Opening it
// is the whole interaction; there is nothing to close because it takes the
// space it needs and gives it back on the next tap.
const credit = document.getElementById('credit');
const creditToggle = document.getElementById('credit-toggle');
creditToggle.addEventListener('click', () => {
  const open = credit.classList.toggle('open');
  creditToggle.setAttribute('aria-expanded', String(open));
});

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
//
// Phase 7. The world used to arrive all at once: nothing was drawn until the
// terrain, the land cover, four thousand footprints, the 2045 scheme and two
// GLBs had all landed, which on a phone was twenty-five seconds of the
// background colour. Now each stage of the build hands back the scene as it
// stands and this draws it, so the vale is on screen as soon as the heightmap
// is — and the rest of it grows in while you are already looking at Cheltenham.
//
// It is deliberately not the real frame loop. No controls, no markers, no
// clock: this exists to put ground in front of someone, and `tick` below takes
// over the moment the world is whole.
let drawn = false;
const scene = await buildWorld({
  renderer,
  onStage: async (name, partial) => {
    renderer.render(partial, camera);
    if (!drawn) {
      drawn = true;
      mark('first frame');
    }
    // Once per stage, not once per frame. Nothing here is animated and nobody
    // is steering yet, so a running loop would only take the machine away
    // from the work that makes the next stage arrive — which is measurable:
    // spinning at every opportunity pushed the last stage from 68 seconds to
    // past 110 on this container's software renderer.
    await new Promise((r) => requestAnimationFrame(r));
  },
});

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
//
// Phase 7 first deferred this to requestIdleCallback, on the grounds that
// 2.65 MB of descent video was competing with the terrain for a phone's first
// seconds. Both halves of that were wrong. The prefetch is not a nicety: the
// player gives a clip a fixed budget to reach readyState 2 and falls back to
// flying the descent live if it misses, so on a slow machine an un-warmed
// cache means the clip route is never taken at all — the flow test caught it
// immediately. And it was never really competing: this line runs after
// buildWorld, which now paints the vale at its first stage, so by the time
// the video starts arriving the map has been on screen for ten seconds.
// The staging fixed what the deferral was aimed at, and the deferral only
// broke the descent.
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
  if (moved > 4 || player.busy || walk.busy || places.busy || places.inside
      || pathMode === 'off') return;
  const hit = paths.pick(e.clientX, e.clientY, camera, innerWidth, innerHeight);
  // A leg, not the route: clicking two kilometres of cycle route has to mean
  // the stretch you were pointing at.
  if (hit) walk.walk(legAt(hit.route, hit.index));
});

function updatePick() {
  if (!pointerDirty) return;
  pointerDirty = false;
  const hit = (pointer && !player.busy && !walk.busy && !places.busy && !places.inside
               && pathMode !== 'off')
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

// --- 2045 -------------------------------------------------------------------
// Today, or 2045. Not a year in between.
//
// Phase 8 gave the wave a dial, on the reasoning that the idea of the piece is
// dragging the future across the vale and stopping half way. That was wrong,
// and looking at it says so: a field caught half way through becoming an
// orchard is neither the ground as it is nor the scheme as proposed, and those
// are the only two things a room ever argues about. Nineteen resting states,
// seventeen of them mush.
//
// So the interface offers the two ends, and the sweep between them is a
// transition rather than a place. The shader is untouched — it still takes a
// continuous front, `setWave` still accepts any number, and `?wave=0.45` still
// holds it half way for a capture, which is the one caller that wants it.
//
// ?future=1 renders it already arrived.
const future = scene.userData.future;
// Long enough to read as the front crossing the vale, short enough that nobody
// waits for it. Eased at both ends, so it gathers and settles.
const SWEEP_MS = 1400;

future.setWave(params.has('wave') ? Number(params.get('wave'))
                                  : (params.has('future') ? 1 : 0));

const dial = document.getElementById('year-dial');
const toggle = document.getElementById('year-toggle');
const ends = [...toggle.querySelectorAll('.end')];
dial.hidden = clean || params.has('future') || params.has('wave');

let sweep = null;                  // { from, to, startedAt, ms } while crossing

function sweepTo(to) {
  // Compared against where it is HEADING rather than where it is. Pressed
  // twice in quick succession the second press has to turn it round, and at
  // that moment the vale has barely moved — so comparing against the current
  // wave would read "you are already going to 2026" and commit you to 2045.
  const bound = sweep ? sweep.to : future.wave;
  if (Math.abs(to - bound) < 0.001) return;
  const from = future.wave;
  if (Math.abs(to - from) < 0.001) { sweep = null; future.setWave(to); return; }
  // Pro rata, so turning round after half a crossing is not the same
  // 1.4 seconds as crossing the whole vale.
  sweep = { from, to, startedAt: performance.now(),
            ms: Math.max(500, SWEEP_MS * Math.abs(to - from)) };
}

// Mid-sweep, the switch answers to where it is going rather than where it is:
// a control that ignores the second press because the first has not landed is
// a control that feels broken.
const heading = () => (sweep ? sweep.to : future.wave) >= 0.5;

toggle.addEventListener('click', () => sweepTo(heading() ? 0 : 1));
// A two-state control that only answers to space is one you have to discover
// twice. Left is today and right is 2045, which is also how it is drawn.
toggle.addEventListener('keydown', (e) => {
  const to = { ArrowLeft: 0, ArrowDown: 0, ArrowRight: 1, ArrowUp: 1 }[e.key];
  if (to === undefined) return;
  e.preventDefault();
  sweepTo(to);
});

// What the scheme is, filling as it arrives. It lives inside the switch rather
// than beside it because they are one object to a viewer: the control, and
// what the control is doing to the vale.
const scheme = clean ? null : await addScheme({ future, root: app });
if (scheme) dial.insertBefore(scheme.band, dial.firstChild);

function updateWave(now) {
  if (sweep) {
    const k = Math.min(1, (now - sweep.startedAt) / sweep.ms);
    // Ease at both ends: the front should gather and settle rather than start
    // and stop, which is the whole difference between weather and a wipe.
    const e = k * k * (3 - 2 * k);
    future.setWave(sweep.from + (sweep.to - sweep.from) * e);
    if (k >= 1) sweep = null;
  }
  // Read from the world rather than from whatever last set it. Flying to a
  // place moves the wave too, and a switch that only knew about its own input
  // would sit there saying TODAY over a photograph of 2045.
  if (dial.hidden) return;
  const w = future.wave;
  // The knob's travel IS the front's travel — one number, read every frame,
  // so the control cannot disagree with the vale it describes.
  toggle.style.setProperty('--k', w.toFixed(4));
  toggle.setAttribute('aria-checked', String(w >= 0.5));
  ends[0].classList.toggle('on', w < 0.5);
  ends[1].classList.toggle('on', w >= 0.5);
  dial.classList.toggle('arrived', w >= 0.999);
  dial.classList.toggle('today', w <= 0.001);
  scheme?.update();
}

// --- today, streamed ---------------------------------------------------------
// With a key, today's Cheltenham is Google's photogrammetry of the real town
// and our 2045 scheme stands on it. Without one — which is every environment
// that is not the local session's, including every test suite and the public
// build — this is null and the map is exactly the measured one it has always
// been. That fallback is not a degraded mode; it is the map most people see.
const tiles = clean ? null : await addTiles(scene, {
  camera, renderer, future,
  // ?tileLift=0.7 while the offset between our LiDAR and their photogrammetry
  // is still being measured, so the local session can find it live without
  // an edit and a redeploy.
  lift: params.has('tileLift') ? Number(params.get('tileLift')) : undefined,
});
const attribution = document.getElementById('tiles-attribution');

// Photogrammetry is a picture taken from an aeroplane: come close enough and
// it melts, because nothing ever photographed the underside of that hedge.
// Below the threshold our measured model takes over, which is the one thing
// it is unambiguously better at.
function updateTiles() {
  if (!tiles) return;
  const above = camera.position.y - heightAtLocal(camera.position.x, camera.position.z);
  // Two thresholds, not one: a camera sitting near the line would otherwise
  // flip the whole town between two versions of itself every few frames, and
  // the walk rides at a fixed height over rolling ground.
  const want = tiles.wantsShowing(above);
  if (want !== tiles.showing) tiles.setShowing(want);
  tiles.update();
  // The licence requires this to be visible whenever tiles are, and it is
  // read from the renderer every frame because what is on screen changes it.
  const text = tiles.showing ? tiles.attributions() : '';
  attribution.hidden = !text;
  if (attribution.textContent !== text) attribution.textContent = text;
}

// --- places: the photographs ------------------------------------------------
// Each approved photograph was generated from a plate this map rendered, so
// each one is a viewpoint with coordinates rather than a picture. Clicking a
// marker goes to that camera and crossfades the photograph over it.
// Declared before the places, because their state callback closes over it and
// a temporal dead zone is a silly way to lose a first render.
const placeBack = document.createElement('button');
placeBack.id = 'place-back';
placeBack.type = 'button';
placeBack.textContent = 'Back to the map';
placeBack.hidden = true;
app.appendChild(placeBack);

const places = createPlaces({
  camera,
  controls,
  container: app,
  future,
  onState: (state) => {
    const there = state === 'there';
    placeBack.hidden = clean || !there;
    document.body.classList.toggle('in-photo', there && !clean);
  },
});
placeBack.onclick = () => places.leave();
if (clean) for (const p of places.places) p.button.hidden = true;

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
  // Its own flag, not `controls.enabled`. Using the controls as the liveness
  // test meant the drift ran for as long as anything had them switched off —
  // so a capture, or anything else that takes the camera while the intro is
  // still up, had its camera quietly overwritten every frame and never knew.
  // It cost an afternoon of screenshots that all came out at the same view.
  let drifting = true;
  const drift = () => {
    if (!drifting) return;
    // Ease out, so the move is quickest at the start and has all but stopped
    // by the time anyone reads as far as the button.
    const k = Math.min(1, (performance.now() - t0) / OPEN_MS);
    camera.position.lerpVectors(from, to, 1 - Math.pow(1 - k, 3));
    camera.lookAt(controls.target);
    if (k >= 1) drifting = false;
    else requestAnimationFrame(drift);
  };
  drift();
  // Anything that means to drive the camera can say so, whether or not it
  // wants the controls back.
  intro.addEventListener('dismiss', () => { drifting = false; });
  document.getElementById('intro-go').onclick = () => {
    drifting = false;
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
  const visiting = places.update(now);
  const walking = !visiting && walk.update(now);
  if (controls.enabled && !visiting && !walking) controls.update();
  updateIgnition(dtMs);
  updateTiles();
  updateWave(now);
  if (!clean) places.updateMarkers();
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
    const hide = player.busy || player.inside === h || walk.busy || !!walk.inside
      || places.busy || !!places.inside;
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
  // Last, once everything has been positioned for this frame: the places and
  // the descent hotspots are two systems to us and one thing to a viewer, and
  // they stand on the same ground — GCHQ has both — so they are thinned
  // together or not at all.
  if (!clean) thin([...places.markers, ...hotspots.map((h) => ({
    el: h.button, anchor: h.anchor,
  }))], camera);
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
  // After the renderer, and after the camera's own aspect: a place holds a
  // narrowed field of view so its photograph and the live canvas frame the
  // same ground, and it has to be reapplied on top of the plain resize.
  places.resize();
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
  renderer, scene, camera, controls, paths, walk, player, hotspots, future, places,
  tiles, scheme,
  // A capture that cannot stop the clock is photographing the weather: the
  // flock, the wind and the cloud shadows all move, so two renders of one
  // camera differ by however long the page took to get there.
  pinWorld, releaseWorld,
  models: scene.userData.models,
  groundAt: heightAtLocal,
};
window.__terrainReady = true;
