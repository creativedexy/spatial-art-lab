// Shared Golden Valley world builder.
//
// The seam test and the map page must render *pixel-identical* worlds — a
// descent clip is only invisible at the cut if the frame it starts from and
// the frame the live canvas resumes on came from the same scene. So the
// scene lives here once, and data paths resolve against this module's URL
// rather than the importing page's, letting it be built from any folder.

import * as THREE from 'three';
import { mergeGeometries } from '../terrain/vendor/BufferGeometryUtils.js';
import { applyLook } from './look.js';
import { addLandCover, loadClassTexture, classIndex } from './landcover.js';
import { bringToLife } from './life.js';

// Re-exported so a page that draws the world imports one module to build it
// and to move it, and cannot end up driving a different clock than the one
// buildWorld installed.
export { updateLife, worldSeconds, pinWorld, releaseWorld } from './life.js';
import { buildBuildings } from './buildings.js';

const url = (f) => new URL(f, import.meta.url).href;

export const meta = await (await fetch(url('gv-meta.json'))).json();
const raw = new Uint16Array(await (await fetch(url(meta.binFile))).arrayBuffer());
const buildings = await (await fetch(url('gv-buildings.json'))).json();

const [W, H] = meta.binPixels;
const zMin = meta.elevationMinMetres;
const zMax = meta.elevationMaxMetres;
export const sizeX = meta.widthMetres;
export const sizeZ = meta.heightMetres;

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
export const heightAtLocal = (x, z) => heightAt(x / sizeX + 0.5, z / sizeZ + 0.5);

// EPSG:27700 easting/northing to local XZ (origin at the box centre).
export function toLocal(e, n) {
  return [e - (meta.easting[0] + sizeX / 2), (meta.northing[0] + sizeZ / 2) - n];
}

// Named anchors, so a descent path can be written in real coordinates.
export const PLACES = {
  doughnut: { name: 'GCHQ — the Doughnut', e: 391523, n: 222336, lift: 40 },
  gvSite: { name: 'Golden Valley site (phase 1)', e: 390808, n: 222615, lift: 20 },
  princessElizabethWay: { name: 'Princess Elizabeth Way', e: 392130, n: 222220, lift: 15 },
};

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

// `segments` trades terrain fidelity for build time: 1000 is ~2 m per vertex
// over the 2 km box, which is what the map page uses. `flatBuildings` draws
// every footprint as one white extrusion at its median height, which is what
// the world looked like before roofs were measured — kept so the lookdev page
// can render the before of a before-and-after, and skipped by buildWorld so
// 4,033 buildings are not built twice.
export function buildScene({ segments = 1000, flatBuildings = true } = {}) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xdfe9ec);
  scene.fog = new THREE.Fog(0xdfe9ec, 2500, 7000);

  const geo = new THREE.PlaneGeometry(sizeX, sizeZ, segments, segments);
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

  if (flatBuildings) {
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
  }

  const sun = new THREE.DirectionalLight(0xfff2dd, 2.4);
  sun.position.set(-1500, 1800, -700);
  scene.add(sun);
  scene.add(new THREE.HemisphereLight(0xd3e4ee, 0x93a183, 1.15));

  return scene;
}

/**
 * The world as it is meant to be seen: Phase 1's light, Phase 2's land cover
 * and trees, Phase 3's roofs and materials, Phase 4's weather and movement.
 *
 * Every page that shows the map must call this and nothing else. The descent
 * hands a pre-rendered clip to a live canvas and the join is measured in
 * pixels, so a page that built the world even slightly differently would open
 * a seam that no amount of fading could close — which is exactly why the
 * world has lived in one module since the beginning.
 *
 * Needs the renderer, because tone mapping and the shadow map are properties
 * of the renderer rather than of the scene, so it must be constructed first.
 */
export async function buildWorld({ renderer, segments = 1000 } = {}) {
  const scene = buildScene({ segments, flatBuildings: false });
  scene.add(buildBuildings());
  applyLook(scene, renderer, { grade: false });
  await addLandCover(scene, renderer, heightAtLocal);
  // Last, because it patches every material it can find and adds the flock —
  // both of which need everything else to already be in the scene.
  bringToLife(scene, {
    groundAt: heightAtLocal,
    classMap: loadClassTexture(),
    waterIndex: classIndex('water'),
  });
  return scene;
}
