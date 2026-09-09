// Buildings that read as buildings — roofs and materials.
//
// The building half of Phase 3. Both halves come from data already on disk:
// scripts/golden_valley_roofs.py recovers each footprint's eaves, ridge,
// ridge direction and roof shape from the DSM we downloaded for the heights,
// and its material family from the OSM tag that was already on the way.
//
// The roof is built as a tent over the real footprint rather than over a
// bounding box, so it never overhangs into thin air:
//
//        ridge segment (from the measured axis)
//            ┌───────────────┐                    gable: ridge spans the
//            │╲             ╱│                    whole length, the ends
//   eaves ───┴─╲───────────╱─┴─── eaves           are vertical triangles
//               ╲_________╱                       hip:   ridge is inset by
//        every footprint edge is joined to               the half-span, the
//        its own projection on the ridge                 ends slope in
//
// Every edge of the footprint gets a quad up to its own projection on the
// ridge segment, which is the straight skeleton of a rectangle and stays
// closed for any simple polygon — no offsetting, no clipping, no library.

import * as THREE from 'three';
import { mergeGeometries } from '../terrain/vendor/BufferGeometryUtils.js';

const url = (f) => new URL(f, import.meta.url).href;
const meta = await (await fetch(url('gv-meta.json'))).json();
const buildings = await (await fetch(url('gv-buildings.json'))).json();

// Walls stay in a narrow off-white range on purpose. The map's proposition is
// a measured architectural model, and 4,000 brick-red houses would trade that
// for a video game; the roofs carry the difference, which is also what you
// actually see from the air.
export const FAMILIES = meta.roofs.families;
const GCHQ = 'Government Communications Headquarters';

function shapeOf(b) {
  const shape = new THREE.Shape(b.ring.map(([x, z]) => new THREE.Vector2(x, -z)));
  for (const hole of b.holes ?? []) {
    shape.holes.push(new THREE.Path(hole.map(([x, z]) => new THREE.Vector2(x, -z))));
  }
  return shape;
}

function walls(b, top) {
  const g = new THREE.ExtrudeGeometry(shapeOf(b), { depth: top, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);
  g.translate(0, b.base - 0.4, 0);      // sit slightly into the terrain
  return g;
}

function flatRoof(b) {
  // A flat roof is still a roof: giving it the family's roof colour is what
  // makes the retail parks and the industrial estate read from altitude.
  const g = new THREE.ShapeGeometry(shapeOf(b));
  g.rotateX(-Math.PI / 2);
  g.translate(0, b.base - 0.4 + b.height + 0.05, 0);
  return g.toNonIndexed();
}

/** The ridge, as measured: a segment in the XZ plane at the roof's centre. */
function ridgeSegment(b) {
  const t = THREE.MathUtils.degToRad(b.axis);
  const c = Math.cos(t), s = Math.sin(t);
  let uMin = Infinity, uMax = -Infinity, vMin = Infinity, vMax = -Infinity;
  for (const [x, z] of b.ring) {
    const u = x * c + z * s;
    const v = -x * s + z * c;
    if (u < uMin) uMin = u;
    if (u > uMax) uMax = u;
    if (v < vMin) vMin = v;
    if (v > vMax) vMax = v;
  }
  const uc = (uMin + uMax) / 2, vc = (vMin + vMax) / 2;
  const half = (uMax - uMin) / 2;
  // A hip's ridge stops short by the roof's half-span at each end, which is
  // exactly where the sloping end faces meet it; a gable's runs the lot.
  const inset = b.roof === 'hip' ? Math.min(half, (vMax - vMin) / 2) : 0;
  const len = Math.max(0, half - inset);
  const to = (u) => new THREE.Vector3(u * c - vc * s, 0, u * s + vc * c);
  return [to(uc - len), to(uc + len)];
}

const _ab = new THREE.Vector3();
const _ap = new THREE.Vector3();

function closestOnSegment(a, b, px, pz, out) {
  _ab.subVectors(b, a);
  _ap.set(px - a.x, 0, pz - a.z);
  const len2 = _ab.lengthSq();
  const t = len2 < 1e-9 ? 0 : THREE.MathUtils.clamp(_ap.dot(_ab) / len2, 0, 1);
  return out.copy(_ab).multiplyScalar(t).add(a);
}

function pitchedRoof(b) {
  const [r0, r1] = ridgeSegment(b);
  const eaveY = b.base - 0.4 + b.eaves;
  const ridgeY = b.base - 0.4 + b.ridge;
  const ring = b.ring;
  const pos = [];
  const a = new THREE.Vector3(), c = new THREE.Vector3();
  const push = (p, q, r) => {
    // OSM rings wind either way and a wrong winding renders a roof inside
    // out, so orient each triangle by its own normal rather than trusting
    // the source data.
    const ny = (q.z - p.z) * (r.x - p.x) - (q.x - p.x) * (r.z - p.z);
    const [u, v] = ny > 0 ? [q, r] : [r, q];
    pos.push(p.x, p.y, p.z, u.x, u.y, u.z, v.x, v.y, v.z);
  };
  for (let i = 0; i < ring.length; i++) {
    const [x0, z0] = ring[i];
    const [x1, z1] = ring[(i + 1) % ring.length];
    if (Math.hypot(x1 - x0, z1 - z0) < 1e-6) continue;
    closestOnSegment(r0, r1, x0, z0, a).setY(ridgeY);
    closestOnSegment(r0, r1, x1, z1, c).setY(ridgeY);
    const p = new THREE.Vector3(x0, eaveY, z0);
    const q = new THREE.Vector3(x1, eaveY, z1);
    push(p, q, c.clone());
    if (a.distanceToSquared(c) > 1e-8) push(p, c.clone(), a.clone());
  }
  if (!pos.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  // mergeGeometries needs every input to carry the same attributes, and
  // ExtrudeGeometry brings uv along.
  g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(pos.length / 3 * 2), 2));
  g.computeVertexNormals();
  return g;
}

/**
 * The town, in eleven meshes: walls and roofs for each material family, plus
 * GCHQ, which is neither a house nor a shed.
 */
export function buildBuildings() {
  const group = new THREE.Group();
  group.name = 'buildings';
  const parts = {};
  const bin = (key) => (parts[key] ??= []);

  for (const b of buildings) {
    if (b.name === GCHQ) {
      bin('gchq').push(walls(b, b.height));
      continue;
    }
    const family = FAMILIES[b.family] ? b.family : 'house';
    if (b.roof && b.ridge > b.eaves) {
      bin(`${family}:wall`).push(walls(b, b.eaves));
      const roof = pitchedRoof(b);
      if (roof) bin(`${family}:roof`).push(roof);
    } else {
      bin(`${family}:wall`).push(walls(b, b.height));
      bin(`${family}:roof`).push(flatRoof(b));
    }
  }

  for (const [key, geoms] of Object.entries(parts)) {
    if (!geoms.length) continue;
    const [family, part] = key.split(':');
    const colour = key === 'gchq' ? 0x4a6f8a
      : parseInt(FAMILIES[family][part].slice(1), 16);
    const mesh = new THREE.Mesh(mergeGeometries(geoms), new THREE.MeshStandardMaterial({
      color: colour,
      // Roofs are tile and slate; walls are render and brick. Half a point of
      // roughness between them is most of what tells the two apart in a
      // low sun.
      roughness: part === 'roof' ? 0.78 : 0.93,
    }));
    mesh.name = key;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    group.add(mesh);
  }
  return group;
}
