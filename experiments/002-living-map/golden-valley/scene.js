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
import { addLandCover, loadClassTexture, classIndex, unitTree, KINDS } from './landcover.js';
import { bringToLife } from './life.js';
import { addPaths } from './paths.js';
import { addFarField } from './farfield.js';
import { addFuture } from './future.js';
import { addModels } from './models.js';
import { pathMeta } from './paths.js';
import { mark } from './stage.js';
import { loadHeights } from './heights.js';

// Re-exported so a page that draws the world imports one module to build it
// and to move it, and cannot end up driving a different clock than the one
// buildWorld installed.
export { updateLife, worldSeconds, pinWorld, releaseWorld } from './life.js';
import { buildBuildings, loadFootprints } from './buildings.js';

const url = (f) => new URL(f, import.meta.url).href;

export const meta = await (await fetch(url('gv-meta.json'))).json();
const raw = await loadHeights(url(meta.binFile), meta);
mark('height');

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
export async function buildScene({ segments = 1000, flatBuildings = true } = {}) {
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
  const ground = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 1, metalness: 0,
  }));
  // Named because the tiles layer has to find it: with photogrammetry showing
  // today's town, our own ground is drawn only where 2045 changes it.
  ground.name = 'terrain';
  scene.add(ground);

  if (flatBuildings) {
    const gchq = [];
    const rest = [];
    for (const b of await loadFootprints()) {
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
export async function buildWorld({ renderer, segments = 1000, onStage = null } = {}) {
  const scene = await buildScene({ segments, flatBuildings: false });
  // Phase 7. applyLook is what makes this a place rather than a mesh — the
  // afternoon sun, the fog, the sky — and it only ever touched the terrain
  // (its mesh loop walks scene.children, and the buildings arrive as a group),
  // so running it here instead of after them is the same world and one that
  // can be shown a second sooner.
  applyLook(scene, renderer, { grade: false });
  mark('terrain');
  // Each stage hands back the scene as it stands. A caller that takes it can
  // start drawing on ground alone; one that ignores it — every capture script
  // and every test — gets exactly what it always got, because the awaits below
  // are unchanged and the scene returned at the end is the same scene.
  if (onStage) await onStage('terrain', scene);
  // The horizon, before anything is built on the ground: it is 280 KB and it
  // is the difference between a world and a slab, so it arrives while the
  // buildings are still coming. It is also the one layer that is allowed to
  // be approximate — OS Terrain 50 at 50 m, out to 75 km — because every part
  // of it a viewer can see is at least a kilometre away.
  scene.userData.farField = await addFarField(scene);
  mark('far field');
  if (onStage) await onStage('far field', scene);
  scene.add(await buildBuildings());
  mark('buildings');
  if (onStage) await onStage('buildings', scene);
  await addLandCover(scene, renderer, heightAtLocal);
  mark('land cover');
  if (onStage) await onStage('land cover', scene);
  // Last, because it patches every material it can find and adds the flock —
  // both of which need everything else to already be in the scene.
  bringToLife(scene, {
    groundAt: heightAtLocal,
    classMap: await loadClassTexture(),
    waterIndex: classIndex('water'),
  });
  // After bringToLife, so the wind shader never finds the ribbons and tries
  // to bend them. The network starts unlit — every fragment discarded — so a
  // world built with paths in it is still pixel-identical to one without,
  // and the seam test measures what it always measured.
  scene.userData.paths = addPaths(scene, { groundAt: heightAtLocal });
  mark('life and paths');
  if (onStage) await onStage('life and paths', scene);
  // Last of all, because it patches the terrain material that bringToLife has
  // just patched and adds meshes that need the same clock. The front starts
  // west of the box, so a world built with 2045 in it renders as today until
  // something moves it.
  scene.userData.future = await addFuture(scene, renderer, {
    groundAt: heightAtLocal, unitTree, treeKinds: KINDS,
  });
  // After the future, because a placed model hides the extrusion it replaces
  // and the extrusions do not exist until addFuture has made them.
  mark('2045');
  scene.userData.models = await addModels(scene, {
    future: scene.userData.future,
    buildings: await (await fetch(url('gv-2045-buildings.json'))).json(),
    namedRoutes: pathMeta.routes.filter((r) => r.tier === 'named'),
    groundAt: heightAtLocal,
  });
  mark('models');
  return scene;
}
