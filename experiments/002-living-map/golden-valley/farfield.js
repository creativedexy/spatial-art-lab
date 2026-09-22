// The land beyond the box.
//
// Two square kilometres of LiDAR, and then nothing: the ground ran out at a
// cliff and the sky started. Phase 11 could only compose around it — of
// sixteen candidate shots, every one that looked north-west was thrown out
// because the survey ends 270 m behind the new homes, and the best
// establishing frame was rejected for being a plan view with no sky in it.
// That is composition paying for a data problem.
//
// This is the data problem fixed. OS Terrain 50 gives the skyline this place
// actually has: Cleeve Common, 330 m and 8.6 km out on a bearing of 75, the
// whole eastern escarpment behind it; the Malverns at 27 km; May Hill at 22;
// the Black Mountains past 70. `scripts/far_field.py` builds it — see there
// for the seam, which is the part that had to be right.
//
// Three things this module is responsible for, none of which belong in the
// data:
//
//   the tuck    the far field runs a little way UNDER the box, and is dropped
//               while it does, so the 50 m grid and the 2 m LiDAR never fight
//               along the boundary. The join is hidden rather than matched.
//   curvature   the Earth falls away; at 75 km that is 340 m, which is the
//               difference between distant hills standing on the horizon and
//               floating above it. Heights on disk stay true elevations.
//   distance    no land cover exists out here and inventing some would be a
//               lie, so the far field is shaded by height and slope only and
//               reads as distance, which is what it is.

import * as THREE from 'three';

import { loadHeights } from './heights.js';

const url = (f) => new URL(f, import.meta.url).href;

// Light bends toward the ground, so the horizon sits further off than plain
// geometry says. Seven sixths is the surveyor's constant for it.
const EARTH_RADIUS = 6371000;
const REFRACTION = 7 / 6;

// How far under the box the far field is tucked, and how far it is dropped
// while it is under there. 12 m clears the worst disagreement between the two
// surveys (3.2 m, measured) several times over.
const TUCK_METRES = 100;
const TUCK_DROP = 12;

/** Height and slope only, in the palette the near ground already uses. */
const LOW = new THREE.Color(0x7f9065);        // vale farmland
const MID = new THREE.Color(0x76855f);        // rising ground
const HIGH = new THREE.Color(0x6d7a63);       // the tops, thinner and greyer
const STEEP = new THREE.Color(0x5d6a52);      // wooded scarp faces

// Aerial perspective, baked into the colours rather than left to the fog.
// Fog is one blend against one colour and it was not enough on its own: with
// only fog the far field came back the same saturated green as the field you
// are standing in, and a horizon that is the same colour as the foreground is
// not a horizon, it is wallpaper. Air scatters blue into everything with
// distance, so distance is drawn that way — from three kilometres, where the
// box has just ended, to sixty, where only the shape is left.
const HAZE = new THREE.Color(0xa9bccb);
const HAZE_FROM = 3000;
const HAZE_TO = 60000;
const HAZE_MAX = 0.82;

export async function addFarField(scene) {
  const meta = await fetch(url('gv-far-meta.json')).then((r) => r.json());
  const group = new THREE.Group();
  group.name = 'far-field';
  // Never in a shadow map: it is tens of kilometres across and the sun's
  // shadow camera is eight, so including it would spend the whole map on
  // ground nobody can see the shadows of.
  group.castShadow = false;
  group.receiveShadow = false;

  const order = ['near', 'far'];
  const inner = { near: meta.boxHalfMetres, far: meta.grids.near.halfExtentMetres };

  for (const name of order) {
    const g = meta.grids[name];
    if (!g) continue;
    const [w, h] = g.binPixels;
    // The same reader the box's own heightmap goes through — one codec, one
    // code path, and phase 7's lesson about four readers of one format.
    const q = await loadHeights(url(g.binFile), g);
    group.add(ring(q, {
      w, h,
      half: g.halfExtentMetres,
      step: g.stepMetres,
      lo: g.elevationMinMetres,
      hi: g.elevationMaxMetres,
      hole: inner[name],
    }));
  }

  scene.add(group);
  return {
    group,
    meta,
    /** Phase 12: where Google's photogrammetry covers this ground, it brings
     *  its own far field and ours would be a second, worse one underneath. */
    setShowing(on) { group.visible = on; },
  };
}

function ring(q, { w, h, half, step, lo, hi, hole }) {
  const pos = new Float32Array(w * h * 3);
  const col = new Float32Array(w * h * 3);
  const span = hi - lo;
  const c = new THREE.Color();

  for (let j = 0, v = 0; j < h; j++) {
    const z = -half + j * step;
    for (let i = 0; i < w; i++, v++) {
      const x = -half + i * step;
      let y = lo + (q[j * w + i] / 65535) * span;
      // Under the box, and dropped while it is there.
      if (Math.max(Math.abs(x), Math.abs(z)) < hole) y -= TUCK_DROP;
      // The Earth falls away from wherever you are standing, and you are
      // standing in the middle of the box.
      y -= (x * x + z * z) / (2 * EARTH_RADIUS * REFRACTION);
      pos[v * 3] = x;
      pos[v * 3 + 1] = y;
      pos[v * 3 + 2] = z;
    }
  }

  // Colour after the heights are in, so slope is read off the real surface.
  for (let j = 0, v = 0; j < h; j++) {
    for (let i = 0; i < w; i++, v++) {
      const e = lo + (q[j * w + i] / 65535) * span;
      const up = q[Math.max(0, j - 1) * w + i];
      const dn = q[Math.min(h - 1, j + 1) * w + i];
      const lf = q[j * w + Math.max(0, i - 1)];
      const rt = q[j * w + Math.min(w - 1, i + 1)];
      const grade = (Math.abs(rt - lf) + Math.abs(dn - up)) / 65535 * span
        / (2 * step);
      const k = THREE.MathUtils.clamp((e - 30) / 260, 0, 1);
      c.copy(LOW).lerp(MID, Math.min(1, k * 2))
        .lerp(HIGH, Math.max(0, k * 2 - 1))
        .lerp(STEEP, THREE.MathUtils.clamp(grade * 5, 0, 0.7));
      const x = -half + i * step;
      const z = -half + j * step;
      const far = THREE.MathUtils.smoothstep(
        Math.hypot(x, z), HAZE_FROM, HAZE_TO);
      c.lerp(HAZE, far * HAZE_MAX);
      col[v * 3] = c.r; col[v * 3 + 1] = c.g; col[v * 3 + 2] = c.b;
    }
  }

  // Quads, minus the hole the next surface in covers.
  const idx = [];
  for (let j = 0; j < h - 1; j++) {
    const z0 = -half + j * step;
    const z1 = z0 + step;
    for (let i = 0; i < w - 1; i++) {
      const x0 = -half + i * step;
      const x1 = x0 + step;
      const reach = Math.max(Math.abs(x0), Math.abs(x1),
                             Math.abs(z0), Math.abs(z1));
      // Entirely inside what covers it: not drawn at all. The quads that
      // straddle the line ARE drawn, and are what runs under the edge.
      if (reach <= hole - TUCK_METRES) continue;
      const a = j * w + i, b = a + 1, d = a + w, e = d + 1;
      idx.push(a, d, b, b, d, e);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  geo.setIndex(idx.length > 65535
    ? new THREE.Uint32BufferAttribute(idx, 1)
    : new THREE.Uint16BufferAttribute(idx, 1));
  geo.computeVertexNormals();

  const mesh = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({
    vertexColors: true,
    // Flat rather than physically shaded: this is a silhouette under haze,
    // and a roughness model on ground 50 km away is arithmetic nobody sees.
    fog: true,
  }));
  mesh.name = `far-field:${half}`;
  mesh.castShadow = false;
  mesh.receiveShadow = false;
  // It is behind everything, always, and sorting 300,000 triangles against
  // the town every frame is work for no picture.
  mesh.renderOrder = -1;
  mesh.matrixAutoUpdate = false;
  return mesh;
}
