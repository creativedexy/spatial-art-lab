// The National Cyber Innovation Centre: a wedge with a meadow on it.
//
// The signature building of the scheme, and the one the campus close-up is
// actually about. It is a wedge — a roof plane running from the ground at one
// end to about 16 m at the other, planted as one continuous wildflower meadow
// so you can walk up the building. That is the whole idea, and it is the
// reason this is not another bar: the silhouette IS the argument.
//
// Two things make it different from every other building in this map.
//
// It has no footprint. The 2045 scheme generates its own blocks from rules;
// this one is placed by a rule instead, written down in models.js and
// evaluated rather than typed in as coordinates — the campus field with
// frontage on a named route, and of those the one nearest GCHQ. It stands in
// that field's courtyard, on the axis of the blocks around it, with the low
// end of the meadow turned towards GCHQ so the roof reads as running down to
// meet the ring.
//
// And it is built rather than modelled. Meshy gave this back soft, with the
// glazed high end turned into holes and spikes; task 001 part 2 was rewritten
// on the strength of it. A wedge is four planes. Four planes are arithmetic.

import * as THREE from 'three';
import { riseMesh } from './future.js';

/** Metres. The rectangle the wedge stands on, and the height it reaches. */
export const NCIC = { length: 60, width: 27, height: 16 };

/** GCHQ, in local metres — the thing the low end is turned towards. */
const GCHQ = new THREE.Vector2(123, 64);

/**
 * The wedge, in world space, with everything the wave and the facade need.
 *
 * Surfaces, which the shader reads off `aSurface`:
 *   0  the two side walls — pale buff stone with long horizontal glazing
 *   1  the roof — wildflower meadow inside a pale stone edge
 *   2  the high end — fully glazed, opaque, no transparency anywhere
 */
export function ncicGeometry(site, groundAt) {
  const { length: L, width: W, height: H } = NCIC;
  const half = W / 2;
  const base = groundAt(site.cx, site.cz) - 0.4;

  // Which way is "up the slope". The rule says the LOW end faces GCHQ, so the
  // high end points away from it: if the field's own axis happens to point the
  // wrong way, turn the building round rather than moving it.
  let dir = new THREE.Vector2(Math.cos(site.axis), Math.sin(site.axis));
  const toGchq = new THREE.Vector2(GCHQ.x - site.cx, GCHQ.y - site.cz);
  if (dir.dot(toGchq) > 0) dir = dir.negate();
  const side = new THREE.Vector2(-dir.y, dir.x);

  // Local (u along the slope from the low end, w across, y up) into the map.
  const at = (u, w, y) => [
    site.cx + dir.x * (u - L / 2) + side.x * w,
    base + y,
    site.cz + dir.y * (u - L / 2) + side.y * w,
  ];

  const pos = [];
  const aBase = [];
  const aAnchor = [];
  const col = [];
  const uv = [];
  const surface = [];
  const bay = [];
  const wallTop = [];

  let kind = 0;
  let tint = new THREE.Color('#e8dfcb');
  const push = (p, u, v) => {
    pos.push(p[0], p[1], p[2]);
    aBase.push(base);
    // One anchor for the whole building, so it arrives as one thing when the
    // front reaches its courtyard rather than growing across itself.
    aAnchor.push(site.cx, site.cz);
    col.push(tint.r, tint.g, tint.b);
    uv.push(u, v);
    surface.push(kind);
    bay.push(3);
    wallTop.push(H);
  };
  const tri = (a, b, c, ta, tb, tc) => {
    push(a, ...ta); push(b, ...tb); push(c, ...tc);
  };
  const quad = (a, b, c, d, ta, tb, tc, td) => {
    tri(a, b, c, ta, tb, tc);
    tri(a, c, d, ta, tc, td);
  };

  const yAt = (u) => (u / L) * H;

  // --- the two side walls: a right triangle each, low end to high end ------
  kind = 0;
  for (const w of [-half, half]) {
    const a = at(0, w, 0);
    const b = at(L, w, 0);
    const c = at(L, w, H);
    // Wound so each face turns outward. The side at +half and the side at
    // -half are mirror images, so one of them has to run the other way round
    // or it renders inside out — which on a wedge means the meadow appears to
    // float with daylight under it.
    if (w > 0) tri(a, b, c, [0, 0], [L, 0], [L, H]);
    else tri(a, c, b, [0, 0], [L, H], [L, 0]);
  }

  // --- the high end: fully glazed -----------------------------------------
  kind = 2;
  quad(at(L, -half, 0), at(L, half, 0), at(L, half, H), at(L, -half, H),
       [0, 0], [W, 0], [W, H], [0, H]);

  // --- the roof: one plane of meadow, ground to 16 m -----------------------
  kind = 1;
  tint = new THREE.Color('#8fa262');
  // u runs up the slope in metres ALONG THE PLANE, not along the ground, so
  // the meadow does not stretch: a 60 m run rising 16 m is 62.1 m of roof.
  const slope = Math.hypot(L, H);
  quad(at(0, -half, 0), at(0, half, 0), at(L, half, H), at(L, -half, H),
       [0, 0], [0, W], [slope, W], [slope, 0]);

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('aBase', new THREE.Float32BufferAttribute(aBase, 1));
  g.setAttribute('aAnchor', new THREE.Float32BufferAttribute(aAnchor, 2));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setAttribute('aFacade', new THREE.Float32BufferAttribute(uv, 2));
  g.setAttribute('aSurface', new THREE.Float32BufferAttribute(surface, 1));
  g.setAttribute('aBay', new THREE.Float32BufferAttribute(bay, 1));
  g.setAttribute('aWallTop', new THREE.Float32BufferAttribute(wallTop, 1));
  g.computeVertexNormals();
  g.userData.slope = slope;
  g.userData.yAt = yAt;
  return g;
}

/** Build it and put it in the scene, or return null if there is no site. */
export function addNcic(site, groundAt) {
  if (!site) return null;
  const mesh = riseMesh(ncicGeometry(site, groundAt), 'ncic');
  mesh.name = 'future:ncic';
  return mesh;
}
