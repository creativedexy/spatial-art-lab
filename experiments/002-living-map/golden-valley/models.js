// Real buildings on the 2045 footprints.
//
// Phase 6b. The close-up plates failed the interesting-imagery rule because at
// a hundred metres the campus is twenty blank 38 x 17 m slabs standing on
// grass — the map's extrusions are honest about *where* and say nothing about
// *what*. Meshy type models say what.
//
// A type model, not a building: one campus block modelled once and placed on
// every campus footprint, scaled to that footprint and turned to its long
// axis. That is the same bargain the trees make — one unit tree, nine
// thousand instances — and it is why this costs one draw call per model
// rather than one per building.
//
// Two things worth knowing:
//
//   The extrusions stay. A family whose model is present hides its own blocks;
//   a family whose model is missing keeps them. A GLB that fails to load must
//   leave a plain box behind rather than an empty field, because "the scheme
//   vanished" is a worse failure than "the scheme is untextured".
//
//   The NCIC has no footprint. It is not in gv-2045-buildings.json because the
//   generator's rules produce bar blocks, and the National Cyber Innovation
//   Centre is a one-off. Its site is chosen by the rule in NCIC_RULE below,
//   evaluated here rather than typed in as coordinates, so it is a decision
//   that can be argued with rather than a number that cannot.

import * as THREE from 'three';
import { GLTFLoader } from '../terrain/vendor/GLTFLoader.js';
import { addNcic, NCIC } from './ncic.js';
import { MeshoptDecoder } from '../terrain/vendor/meshopt_decoder.module.js';
import { riseModel } from './future.js';

const url = (f) => new URL(f, import.meta.url).href;

/**
 * The type models, and what they stand on.
 *
 * `heightFromFootprint` is what separates a bar from a landmark: a campus
 * block takes the measured height of the footprint it replaces, because the
 * generator gave every one of them a height between 11.9 and 17 m and losing
 * that would flatten the scheme. The NCIC has no footprint to take a height
 * from, so it is given one.
 */
export const TYPES = {
  campus: {
    file: '../meshy/campus-block.glb',
    family: 'campus',
    heightFromFootprint: true,
  },
  ncic: {
    file: '../meshy/ncic.glb',
    family: null,                 // it stands on a site, not on a footprint
    lengthMetres: 60,
    // 16 m, not the 22.4 m the model comes out at when it is 60 m long. HBD's
    // building is four storeys and the meshy came back tall; squashing the
    // height is the one distortion worth taking, because the silhouette that
    // matters here is the meadow roof running to the ground, and that reads
    // better low than high.
    heightMetres: 16,
  },
};

export const NCIC_RULE =
  'The National Cyber Innovation Centre takes the campus field with frontage '
  + 'on a named route — the Cheltenham Circular Footpath or the '
  + 'Gloucestershire Cycle Spine within 150 m of the field centre — and, of '
  + 'those, the one nearest GCHQ. It stands in that field\'s courtyard, on '
  + 'the axis of the blocks around it, with the low end of its meadow roof '
  + 'turned towards GCHQ.';

const GCHQ = new THREE.Vector2(123, 64);
const FRONTAGE_METRES = 150;

/** The footprint's centre, long-axis bearing, length and width. */
function footprint(b) {
  const r = b.ring;
  const cx = r.reduce((s, p) => s + p[0], 0) / r.length;
  const cz = r.reduce((s, p) => s + p[1], 0) / r.length;
  let longest = 0;
  let axis = 0;
  const sides = [];
  for (let i = 0; i < r.length; i++) {
    const a = r[i];
    const c = r[(i + 1) % r.length];
    const len = Math.hypot(c[0] - a[0], c[1] - a[1]);
    sides.push(len);
    if (len > longest) {
      longest = len;
      axis = Math.atan2(c[1] - a[1], c[0] - a[0]);
    }
  }
  // Opposite sides of a quad, so the short side is the other pair.
  const width = Math.min(...sides);
  return { cx, cz, axis, length: longest, width };
}

/**
 * Load a GLB and hand back one geometry, one material, and which way it faces.
 *
 * Normalised on the way through: recentred on its own footprint and dropped so
 * its base sits at y = 0, because a model whose origin is in the middle of it
 * has to be corrected at every single placement instead of once here.
 */
// Phase 7. The GLBs left Meshy at 5.5 and 5.8 MB, most of it a 2048 baseColour
// JPEG on a building that is never nearer than eighty metres, and the rest
// float32 positions with three decimal places of a millimetre. Compressed
// they are 0.73 and 0.90 MB. Meshopt is the one that needs anything of the
// page: a 24 KB decoder, shared by every type, against 1.9 MB of geometry.
const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);

async function loadType(spec) {
  const gltf = await loader.loadAsync(url(spec.file));
  let found = null;
  gltf.scene.updateMatrixWorld(true);
  gltf.scene.traverse((o) => { if (o.isMesh && !found) found = o; });
  if (!found) throw new Error(`no mesh in ${spec.file}`);

  const geometry = found.geometry.clone();
  geometry.applyMatrix4(found.matrixWorld);
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  const size = box.getSize(new THREE.Vector3());
  const centre = box.getCenter(new THREE.Vector3());
  geometry.translate(-centre.x, -box.min.y, -centre.z);

  // Which horizontal axis the model is long on. The campus block is long on X
  // and the NCIC on Z; assuming either would put one of them across its own
  // site.
  const longOnX = size.x >= size.z;

  // Which end of the long axis is the tall one. The NCIC's whole idea is a
  // meadow roof running down to the ground, so which way round it sits is a
  // design decision rather than an arbitrary one — and it can be read off the
  // geometry instead of guessed at.
  const pos = geometry.attributes.position;
  let lowSum = 0, lowN = 0, highSum = 0, highN = 0;
  for (let i = 0; i < pos.count; i++) {
    const along = longOnX ? pos.getX(i) : pos.getZ(i);
    if (along > 0) { highSum += pos.getY(i); highN++; }
    else { lowSum += pos.getY(i); lowN++; }
  }
  const tallAtPositive = (highSum / Math.max(highN, 1)) > (lowSum / Math.max(lowN, 1));

  return {
    geometry,
    material: found.material,
    unit: {
      length: longOnX ? size.x : size.z,
      width: longOnX ? size.z : size.x,
      height: size.y,
      longOnX,
      tallAtPositive,
    },
  };
}

/**
 * Where the NCIC goes, by NCIC_RULE.
 *
 * The fields come from the generator rather than from clustering the blocks:
 * every building carries the centre of the field it was placed in. The first
 * version of this grouped footprints by proximity and found five fields where
 * there are four, because a perimeter block sits on the edge of its courtyard
 * and two blocks either side of a street are nearer each other than either is
 * to its own field's centre.
 */
export function chooseNcicSite(buildings, namedRoutes) {
  const campus = buildings.filter((b) => b.family === 'campus' && b.cell);
  if (!campus.length) return null;

  const fields = new Map();
  for (const b of campus) {
    const key = b.cell.join(',');
    if (!fields.has(key)) {
      fields.set(key, { cx: b.cell[0], cz: b.cell[1], members: [] });
    }
    fields.get(key).members.push(footprint(b));
  }

  const list = [...fields.values()];
  for (const g of list) {
    g.toGchq = Math.hypot(g.cx - GCHQ.x, g.cz - GCHQ.y);
    g.toRoute = Math.min(...namedRoutes.map((r) =>
      Math.min(...r.points.map((p) => Math.hypot(p[0] - g.cx, p[1] - g.cz)))));
    // The axis of the blocks around the courtyard, which is the field's own
    // grain and so the grid's.
    g.axis = g.members.reduce((a, b) => (b.length > a.length ? b : a)).axis;
    // The nearest block, so a caller can tell whether the courtyard is big
    // enough for what it wants to stand in it.
    g.clearance = Math.min(...g.members.map((m) =>
      Math.hypot(m.cx - g.cx, m.cz - g.cz)));
  }

  const withFrontage = list.filter((g) => g.toRoute <= FRONTAGE_METRES);
  const pool = withFrontage.length ? withFrontage : list;
  const site = pool.reduce((a, b) => (b.toGchq < a.toGchq ? b : a));
  return { ...site, usedFallback: withFrontage.length === 0, fields: list.length };
}

/**
 * Place every type model that loaded, and hide the extrusions it replaces.
 *
 * `future` is the wave controller: its `blocks` map is how a family stands
 * down, and `riseModel` is how a placed model arrives with the front rather
 * than being there all along.
 */
export async function addModels(scene, { future, buildings, namedRoutes, groundAt }) {
  const group = new THREE.Group();
  group.name = 'models';
  const placed = {};
  // How each thing got here: a loaded GLB, or geometry written from rules.
  // Worth keeping apart, because "the campus has buildings" and "the campus
  // has the buildings we meant" are different claims.
  const built = {};

  const site = chooseNcicSite(buildings, namedRoutes);

  // Which types this copy of the map actually has. Asking the server for a
  // GLB that was deliberately left out is a 404 in everyone's console and two
  // wasted round trips, so the build says what it shipped and this believes
  // it. Fetched here rather than at module scope: a top-level await holds up
  // every module that imports this one.
  const { available } = await (await fetch(url('models.json'))).json();

  for (const [name, spec] of Object.entries(TYPES)) {
    if (!available.includes(name)) {
      // Not an error. The extrusions below it stay standing, which is the
      // whole reason a missing model is survivable.
      continue;
    }
    let type;
    try {
      type = await loadType(spec);
    } catch (err) {
      // A missing or broken GLB is expected while the models are still being
      // made, and it must not take the scheme with it.
      console.warn(`models: ${name} not placed — ${err.message}`);
      continue;
    }

    const rows = spec.family
      ? buildings.filter((b) => b.family === spec.family).map((b) => {
        const f = footprint(b);
        return { ...f, base: b.base - 0.4, height: b.height };
      })
      : site
        ? [{
          cx: site.cx, cz: site.cz, axis: site.axis,
          length: spec.lengthMetres,
          width: spec.lengthMetres * (type.unit.width / type.unit.length),
          base: groundAt(site.cx, site.cz) - 0.4,
          height: spec.heightMetres,
          faceGchq: true,
        }]
        : [];
    if (!rows.length) continue;

    built[name] = 'model';
    const { material, depth } = riseModel(type.material);
    const mesh = new THREE.InstancedMesh(type.geometry, material, rows.length);
    mesh.name = `model:${name}`;
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.customDepthMaterial = depth;
    mesh.frustumCulled = false;

    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const up = new THREE.Vector3(0, 1, 0);
    const pos = new THREE.Vector3();
    const scale = new THREE.Vector3();
    rows.forEach((row, i) => {
      const along = row.length / type.unit.length;
      const across = row.width / type.unit.width;
      const tall = (spec.heightFromFootprint ? row.height : spec.heightMetres)
        / type.unit.height;
      // A model long on Z has to be turned a quarter turn before the
      // footprint's bearing means anything to it.
      let turn = -row.axis + (type.unit.longOnX ? 0 : Math.PI / 2);
      if (row.faceGchq) {
        // Turn it so the TALL end points away from GCHQ, which puts the low
        // end of the meadow roof — the end that reaches the ground — on the
        // side the ring is.
        const dir = new THREE.Vector2(Math.cos(row.axis), Math.sin(row.axis));
        const toGchq = new THREE.Vector2(GCHQ.x - row.cx, GCHQ.y - row.cz);
        const tallTowardsGchq = type.unit.tallAtPositive
          ? dir.dot(toGchq) > 0 : dir.dot(toGchq) < 0;
        if (tallTowardsGchq) turn += Math.PI;
      }
      q.setFromAxisAngle(up, turn);
      scale.set(type.unit.longOnX ? along : across, tall,
                type.unit.longOnX ? across : along);
      pos.set(row.cx, row.base, row.cz);
      mesh.setMatrixAt(i, m.compose(pos, q, scale));
    });
    mesh.instanceMatrix.needsUpdate = true;
    mesh.geometry.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 2000);
    group.add(mesh);
    placed[name] = rows.length;

    // The extrusions this model replaces get out of the way. Only the family
    // it covers: the homes and the glasshouses still need theirs.
    const blocks = spec.family && future.blocks && future.blocks.get(spec.family);
    if (blocks) blocks.visible = false;
  }

  // The NCIC is built rather than modelled — a wedge is four planes — so it
  // stands whether or not a GLB was ever made, and it stands on the site the
  // rule above picked rather than on a footprint. Only when no type model has
  // claimed it: if a real model of it is ever loaded, that wins.
  if (!placed.ncic) {
    const wedge = addNcic(site, groundAt);
    if (wedge) {
      group.add(wedge);
      placed.ncic = 1;
      built.ncic = 'written';
    }
  }

  scene.add(group);
  return { group, placed, built, ncicSite: site, rule: NCIC_RULE,
           ncicSize: NCIC };
}
