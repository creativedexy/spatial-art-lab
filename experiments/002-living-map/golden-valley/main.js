// Living map, Sprint 1 vertical slice: Golden Valley / west Cheltenham at
// full 1 m LiDAR resolution, true scale, with every OSM building footprint
// extruded to its DSM-minus-DTM measured height. White-model archviz look;
// GCHQ's doughnut picked out in slate.

import * as THREE from 'three';
import { OrbitControls } from '../terrain/vendor/OrbitControls.js';
import { mergeGeometries } from '../terrain/vendor/BufferGeometryUtils.js';

const app = document.getElementById('app');

const meta = await (await fetch('./gv-meta.json')).json();
const raw = new Uint16Array(await (await fetch(`./${meta.binFile}`)).arrayBuffer());
const buildings = await (await fetch('./gv-buildings.json')).json();
const [W, H] = meta.binPixels;
const zMin = meta.elevationMinMetres;
const zMax = meta.elevationMaxMetres;
const sizeX = meta.widthMetres;
const sizeZ = meta.heightMetres;

function heightAt(u, v) {
  const x = THREE.MathUtils.clamp(u, 0, 1) * (W - 1);
  const y = THREE.MathUtils.clamp(v, 0, 1) * (H - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, W - 1), y1 = Math.min(y0 + 1, H - 1);
  const fx = x - x0, fy = y - y0;
  const h = (yy, xx) => raw[yy * W + xx] / 65535;
  const n = h(y0, x0) * (1 - fx) + h(y0, x1) * fx;
  const s = h(y1, x0) * (1 - fx) + h(y1, x1) * fx;
  return zMin + (n * (1 - fy) + s * fy) * (zMax - zMin);
}
const heightAtLocal = (x, z) => heightAt(x / sizeX + 0.5, z / sizeZ + 0.5);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe9ec);
scene.fog = new THREE.Fog(0xdfe9ec, 2500, 7000);

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

// --- terrain, true scale ----------------------------------------------------
const SEG = 1000; // ~2 m per vertex over the 2 km box
const geo = new THREE.PlaneGeometry(sizeX, sizeZ, SEG, SEG);
geo.rotateX(-Math.PI / 2);
const pos = geo.attributes.position;
const colors = new Float32Array(pos.count * 3);
const col = new THREE.Color();
const grass = new THREE.Color(0x86a274);
const meadow = new THREE.Color(0xa3b184);
const urban = new THREE.Color(0xb9b6a6);

for (let i = 0; i < pos.count; i++) {
  const x = pos.getX(i), z = pos.getZ(i);
  const h = heightAtLocal(x, z);
  pos.setY(i, h);
  // Gentle green-to-urban blend by height, plus large-scale variation so
  // the vale doesn't read as one flat swatch.
  const t = (h - zMin) / (zMax - zMin);
  const wob = 0.5 + 0.5 * Math.sin(x * 0.011) * Math.sin(z * 0.013);
  col.copy(grass).lerp(meadow, wob).lerp(urban, Math.min(t * 1.15, 0.55));
  colors[i * 3] = col.r; colors[i * 3 + 1] = col.g; colors[i * 3 + 2] = col.b;
}
geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
geo.computeVertexNormals();
scene.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
  vertexColors: true, roughness: 1, metalness: 0,
})));

// --- buildings --------------------------------------------------------------
function footprintGeometry(b) {
  const shape = new THREE.Shape(b.ring.map(([x, z]) => new THREE.Vector2(x, -z)));
  for (const hole of b.holes ?? []) {
    shape.holes.push(new THREE.Path(hole.map(([x, z]) => new THREE.Vector2(x, -z))));
  }
  const g = new THREE.ExtrudeGeometry(shape, { depth: b.height, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);              // extrusion now points up (+Y)
  g.translate(0, b.base - 0.4, 0);      // sit slightly into the terrain
  return g;
}

const gchq = [];
const rest = [];
for (const b of buildings) {
  (b.name === 'Government Communications Headquarters' ? gchq : rest)
    .push(footprintGeometry(b));
}
scene.add(new THREE.Mesh(mergeGeometries(rest), new THREE.MeshStandardMaterial({
  color: 0xf3efe4, roughness: 0.95, // masterplan white model
})));
scene.add(new THREE.Mesh(mergeGeometries(gchq), new THREE.MeshStandardMaterial({
  color: 0x4a6f8a, roughness: 0.8,
})));

const sun = new THREE.DirectionalLight(0xfff2dd, 2.4);
sun.position.set(-1500, 1800, -700);
scene.add(sun);
scene.add(new THREE.HemisphereLight(0xd3e4ee, 0x93a183, 1.15));

// --- labels -----------------------------------------------------------------
function toLocal(e, n) {
  return [e - (meta.easting[0] + sizeX / 2), (meta.northing[0] + sizeZ / 2) - n];
}
const places = params.get('clean') ? [] : [
  { name: 'GCHQ — the Doughnut', e: 391523, n: 222336, lift: 40 },
  { name: 'Golden Valley site (phase 1)', e: 390808, n: 222615, lift: 20 },
  { name: 'Princess Elizabeth Way', e: 392130, n: 222220, lift: 15 },
];
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
  ?? toLocal(391523, 222336); // default: open on the doughnut
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
