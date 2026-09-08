// Living map, Sprint 1 Session A: real Cheltenham terrain in the browser.
// EA LiDAR composite DTM (12 x 12 km, EPSG:27700 388000-400000 E,
// 216000-228000 N) displaces a plane; colours are a stylised Cotswold
// palette by elevation and slope. World units are metres.

import * as THREE from 'three';
import { OrbitControls } from './vendor/OrbitControls.js';

const app = document.getElementById('app');

const meta = await (await fetch('./cheltenham-heightmap.json')).json();
const raw = new Uint16Array(await (await fetch(`./${meta.binFile}`)).arrayBuffer());
const [W, H] = meta.binPixels;
const zMin = meta.elevationMinMetres;
const zMax = meta.elevationMaxMetres;
const sizeX = meta.widthMetres;
const sizeZ = meta.heightMetres;

// Bilinear height lookup, u/v in 0..1 with v = 0 at the north edge.
function heightAt(u, v) {
  const x = Math.min(u, 1) * (W - 1);
  const y = Math.min(v, 1) * (H - 1);
  const x0 = Math.floor(x), y0 = Math.floor(y);
  const x1 = Math.min(x0 + 1, W - 1), y1 = Math.min(y0 + 1, H - 1);
  const fx = x - x0, fy = y - y0;
  const h = (yy, xx) => raw[yy * W + xx] / 65535;
  const n = h(y0, x0) * (1 - fx) + h(y0, x1) * fx;
  const s = h(y1, x0) * (1 - fx) + h(y1, x1) * fx;
  return zMin + (n * (1 - fy) + s * fy) * (zMax - zMin);
}

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe9ec);
scene.fog = new THREE.Fog(0xdfe9ec, 6000, 22000);

const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 10, 60000);
// Open from the south-west so the town sits in the vale with the
// escarpment and Cleeve Hill rising behind it.
camera.position.set(-3800, 3400, 6200);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
app.appendChild(renderer.domElement);

// --- terrain mesh -----------------------------------------------------------
const SEG = 512;
const geo = new THREE.PlaneGeometry(sizeX, sizeZ, SEG, SEG);
geo.rotateX(-Math.PI / 2); // plane in XZ, +X east, +Z south, v grows southward

const pos = geo.attributes.position;
const colors = new Float32Array(pos.count * 3);
const col = new THREE.Color();

// Stylised palette, low valley floor to high limestone edge.
const ramp = [
  [0.00, 0x5d8a5f], // river Chelt valley, deeper green
  [0.18, 0x6f9c62], // town-level greens
  [0.42, 0x94ad6b], // rising farmland
  [0.65, 0xb7b47c], // upper slopes, drying grass
  [0.85, 0xcdc296], // limestone brash
  [1.00, 0xe4dcc0], // Cleeve Hill top
];
function rampColor(t, out) {
  for (let i = 1; i < ramp.length; i++) {
    if (t <= ramp[i][0] || i === ramp.length - 1) {
      const [t0, c0] = ramp[i - 1];
      const [t1, c1] = ramp[i];
      const f = THREE.MathUtils.clamp((t - t0) / (t1 - t0), 0, 1);
      return out.setHex(c0).lerp(new THREE.Color(c1), f);
    }
  }
}

for (let i = 0; i < pos.count; i++) {
  const u = pos.getX(i) / sizeX + 0.5;
  const v = pos.getZ(i) / sizeZ + 0.5;
  const h = heightAt(u, v);
  pos.setY(i, h);

  const t = (h - zMin) / (zMax - zMin);
  // Local slope steepens the colour slightly, so scarps read as terrain.
  const d = 1 / SEG;
  const slope = Math.abs(heightAt(Math.min(u + d, 1), v) - heightAt(Math.max(u - d, 0), v))
              + Math.abs(heightAt(u, Math.min(v + d, 1)) - heightAt(u, Math.max(v - d, 0)));
  rampColor(t, col);
  col.multiplyScalar(1 - Math.min(slope / 220, 0.28));
  colors[i * 3] = col.r; colors[i * 3 + 1] = col.g; colors[i * 3 + 2] = col.b;
}
geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
geo.computeVertexNormals();

const terrain = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
  vertexColors: true, roughness: 1, metalness: 0,
}));
scene.add(terrain);

// Vertical exaggeration keeps the escarpment legible at map altitude.
terrain.scale.y = 1.8;

const sun = new THREE.DirectionalLight(0xfff4e0, 2.2);
sun.position.set(-6000, 7000, -3000); // afternoon light from the south-west
scene.add(sun);
scene.add(new THREE.HemisphereLight(0xcfe4ee, 0x8a9a7a, 1.1));

// --- reference markers ------------------------------------------------------
// EPSG:27700 easting/northing to local XZ (origin at the box centre).
function toLocal(e, n) {
  return [e - (meta.easting[0] + sizeX / 2), (meta.northing[0] + sizeZ / 2) - n];
}
const places = [
  { name: 'GCHQ / Golden Valley', e: 391755, n: 221389 },
  { name: 'Town centre', e: 394950, n: 222200 },
  { name: 'Cleeve Hill 330 m', e: 398470, n: 226070 },
];
for (const p of places) {
  const [x, z] = toLocal(p.e, p.n);
  const y = heightAt(x / sizeX + 0.5, z / sizeZ + 0.5) * terrain.scale.y;
  const pin = new THREE.Mesh(
    new THREE.CylinderGeometry(18, 18, 260, 8),
    new THREE.MeshBasicMaterial({ color: 0x35524a }),
  );
  pin.position.set(x, y + 130, z);
  scene.add(pin);
  const div = document.createElement('div');
  div.className = 'label';
  div.textContent = p.name;
  app.appendChild(div);
  p.anchor = new THREE.Vector3(x, y + 300, z);
  p.div = div;
}

// --- controls ---------------------------------------------------------------
const controls = new OrbitControls(camera, renderer.domElement);
controls.mouseButtons = { LEFT: THREE.MOUSE.PAN, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.ROTATE };
controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
controls.screenSpacePanning = false;
controls.enableDamping = true;
controls.minDistance = 500;
controls.maxDistance = 16000;
controls.maxPolarAngle = 1.32; // never below the horizon
controls.target.set(900, 0, -200); // start focused on the town centre
controls.addEventListener('change', () => {
  // Keep the focus point on the map so the terrain never shows its edges.
  controls.target.x = THREE.MathUtils.clamp(controls.target.x, -sizeX / 2, sizeX / 2);
  controls.target.z = THREE.MathUtils.clamp(controls.target.z, -sizeZ / 2, sizeZ / 2);
  controls.target.y = 0;
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

window.__terrainReady = true; // for headless capture
