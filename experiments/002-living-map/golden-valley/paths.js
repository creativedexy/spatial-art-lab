// The path network as something you can touch.
//
// Phase 5. The same footpaths are already in gv-landcover.png as texels, and
// that is still how they *look* correct — a 1.8 m footway is narrower than
// the terrain mesh's own 2 m triangles, so drawn as geometry at true width it
// would z-fight and crawl. What a texel cannot do is have a name, a pair of
// ends, or a state. So the routes arrive here a second time as polylines from
// gv-paths.json, and this module gives them the four things the picture
// cannot: ground height, a lit ribbon, a hit test, and a leg you can walk.
//
// Three decisions worth knowing about:
//
//   The ribbon has a floor in PIXELS, not just a width in metres. From the
//   hub the camera is 800-2000 m up, where a metre is around a pixel, so a
//   true-width path dissolves exactly where the aerial spends most of its
//   pixels. The vertex shader expands the ribbon by whichever is larger —
//   its real width, or a minimum screen width — so it thickens honestly as
//   you descend and never disappears from altitude.
//
//   Ignition is one-way. A path lights, and stays lit. Igniting is better
//   film; staying lit is better interface, and the map has to be both.
//
//   Picking is done on the CPU against the projected spine, not with a pick
//   buffer. 3,642 points is a fifth of a millisecond, it runs on pointer
//   moves rather than per frame, and it costs no render target — the pick
//   buffer is the right answer only once the routes outnumber the pixels.

import * as THREE from 'three';

const url = (f) => new URL(f, import.meta.url).href;
export const pathMeta = await (await fetch(url('gv-paths.json'))).json();

// Warm on the named routes, because the ground under them is sage and a low
// sun: a cool line reads as an overlay drawn on a picture of a place, and a
// warm one reads as light falling on the place itself. The web underneath is
// pale and weak on purpose — it is grain, not an offer.
const STYLE = {
  named: { colour: 0xffc27a, width: 2.4, minPixels: 2.8, glow: 0.95, opacity: 0.72 },
  // Warm rather than neutral, and wider than it looks like it needs to be.
  // Additive light on sunlit grass has very little to add — a cool pale line
  // over a ground already at three-quarter brightness is arithmetic nobody
  // can see. Warmth is what separates it from the green underneath.
  strand: { colour: 0xf3ddb0, width: 1.8, minPixels: 2.2, glow: 0.62, opacity: 0.52 },
};
const HOVER = { glow: 2.1, opacity: 1.0, minPixels: 4.2 };
const LIFT = 0.5;             // metres above the ground the ribbon floats
const PICK_PIXELS = 16;       // how near the pointer has to be to catch a route

const vertexShader = /* glsl */`
  attribute vec3 aSide;
  attribute vec3 aTangent;
  attribute float aV;
  attribute float aU;
  uniform vec2 uResolution;   // drawing buffer, in device pixels
  uniform float uMinPixels;
  uniform float uWidth;
  varying float vU;
  varying float vV;
  varying float vDepth;
  void main() {
    vec4 mv = modelViewMatrix * vec4(position, 1.0);
    vDepth = max(-mv.z, 1.0);
    vec4 c0 = projectionMatrix * mv;
    vec2 hr = uResolution * 0.5;

    // Where the path's TRUE width actually lands, measured in pixels. This is
    // the honest number: it already carries the foreshortening, which is the
    // whole difficulty — a ribbon lying flat on the ground and seen at a
    // grazing angle projects to a fraction of its width, so a minimum
    // enforced in metres is not a minimum on screen at all. That was why the
    // route across the field came out as dashes.
    vec4 cw = projectionMatrix * modelViewMatrix
              * vec4(position + aSide * (uWidth * 0.5 * aV), 1.0);
    vec2 offPx = (cw.xy / cw.w - c0.xy / c0.w) * hr;
    float have = length(offPx);

    // The direction to push in, taken from the projected line itself so it
    // survives the case where the true width projects to nothing at all.
    vec4 ct = projectionMatrix * modelViewMatrix * vec4(position + aTangent, 1.0);
    vec2 tPx = (ct.xy / ct.w - c0.xy / c0.w) * hr;
    vec2 fallback = normalize(vec2(-tPx.y, tPx.x) + vec2(1e-6)) * aV;
    vec2 dir = have > 1e-3 ? offPx / have : fallback;

    // Whichever is wider on screen: what the path is, or what it takes to
    // still be a line. Widening in screen space rather than in the ground
    // plane is what makes that a promise rather than a hope.
    float use = max(have, uMinPixels * 0.5);
    gl_Position = c0;
    gl_Position.xy += dir * use / hr * c0.w;

    vU = aU;
    vV = aV;
  }
`;

const fragmentShader = /* glsl */`
  uniform vec3 uColour;
  uniform float uProgress;
  uniform float uGlow;
  uniform float uOpacity;
  varying float vU;
  varying float vV;
  varying float vDepth;
  void main() {
    // Soft across the ribbon, so a 3 px line is not a 3 px staircase.
    float edge = 1.0 - smoothstep(0.45, 1.0, abs(vV));
    // A hot core with soft shoulders rather than a flat band: a uniform strip
    // of colour reads as a highlighter drawn over a photograph, and a line
    // that is brightest down its middle reads as light lying on the ground.
    float core = 1.0 - smoothstep(0.0, 0.55, abs(vV));
    // The head runs from just before the start to just past the end, so a
    // fully lit route is lit all the way to its last vertex rather than
    // stopping one blend width short of it.
    float head = uProgress * 1.08 - 0.04;
    // Lit behind the head, dark in front of it — written as an increasing
    // smoothstep and inverted, because GLSL leaves smoothstep UNDEFINED when
    // edge0 >= edge1 and a driver that returns zero there draws nothing at
    // all. That is exactly what it did.
    float lit = 1.0 - smoothstep(head - 0.05, head, vU);
    // The flare that travels the route once and is gone. Squared by
    // multiplication rather than pow(), which is also undefined for a
    // negative base — and half of this ramp is negative.
    float d = (vU - head) * 30.0;
    float flare = exp(-d * d)
                  * step(0.0001, uProgress) * (1.0 - step(0.9999, uProgress));
    // Gone by the time you are standing on it. The network is how you choose
    // a route, not something laid along the ground — walking a leg with an
    // amber strip blazing under the camera looks like a runway, and by then
    // the choice has been made anyway. It lights the way ahead and clears out
    // from under your feet.
    float near = smoothstep(9.0, 48.0, vDepth);
    float a = edge * near * clamp(lit * uOpacity + flare * 0.85, 0.0, 1.0);
    if (a <= 0.003) discard;
    gl_FragColor = vec4(uColour * (uGlow * (0.6 + core * 0.8) + flare * 2.4), a);
  }
`;

/**
 * Lay a route on the ground.
 *
 * The file carries no Y, exactly as the tree instances carry no Y: height
 * comes from the height field the terrain is built from, so a route cannot
 * float over a hill or sink into one if either the terrain or the path ever
 * changes. `arc` is cumulative length along the draped line — the 3D length,
 * not the map length, so walking it at a constant speed feels constant.
 */
function drape(points, groundAt) {
  const pts = points.map(([x, z]) =>
    new THREE.Vector3(x, groundAt(x, z) + LIFT, z));
  const arc = [0];
  for (let i = 1; i < pts.length; i++) {
    arc.push(arc[i - 1] + pts[i].distanceTo(pts[i - 1]));
  }
  return { pts, arc, length: arc[arc.length - 1] };
}

function ribbonGeometry(pts, arc) {
  const n = pts.length;
  const total = arc[n - 1] || 1;
  const position = new Float32Array(n * 2 * 3);
  const side = new Float32Array(n * 2 * 3);
  const tangent = new Float32Array(n * 2 * 3);
  const across = new Float32Array(n * 2);
  const along = new Float32Array(n * 2);
  const dir = new THREE.Vector3();

  for (let i = 0; i < n; i++) {
    // Central difference, so a corner gets the average of the two directions
    // meeting at it and the ribbon mitres instead of pinching.
    dir.subVectors(pts[Math.min(i + 1, n - 1)], pts[Math.max(i - 1, 0)]);
    dir.y = 0;
    if (dir.lengthSq() < 1e-9) dir.set(1, 0, 0);
    dir.normalize();
    // Perpendicular in the ground plane: the ribbon lies flat, which is what
    // makes it foreshorten correctly rather than standing up like a fence.
    const sx = dir.z, sz = -dir.x;
    for (const k of [0, 1]) {
      const j = i * 2 + k;
      position[j * 3] = pts[i].x;
      position[j * 3 + 1] = pts[i].y;
      position[j * 3 + 2] = pts[i].z;
      side[j * 3] = sx;
      side[j * 3 + 1] = 0;
      side[j * 3 + 2] = sz;
      tangent[j * 3] = dir.x;
      tangent[j * 3 + 1] = 0;
      tangent[j * 3 + 2] = dir.z;
      across[j] = k === 0 ? -1 : 1;
      along[j] = arc[i] / total;
    }
  }

  const index = new Uint32Array((n - 1) * 6);
  for (let i = 0; i < n - 1; i++) {
    const a = i * 2, b = i * 2 + 1, c = a + 2, d = b + 2;
    index.set([a, b, c, b, d, c], i * 6);
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(position, 3));
  g.setAttribute('aSide', new THREE.BufferAttribute(side, 3));
  g.setAttribute('aTangent', new THREE.BufferAttribute(tangent, 3));
  g.setAttribute('aV', new THREE.BufferAttribute(across, 1));
  g.setAttribute('aU', new THREE.BufferAttribute(along, 1));
  g.setIndex(new THREE.BufferAttribute(index, 1));
  g.computeBoundingSphere();
  return g;
}

/**
 * Build the network, add it to `scene`, and return the handle that drives it.
 *
 * `groundAt(x, z)` is the terrain height function — passed in rather than
 * imported, because scene.js imports this module and two modules that both
 * await at the top level cannot also import each other.
 */
export function addPaths(scene, { groundAt }) {
  const group = new THREE.Group();
  group.name = 'paths';
  // Interface, not scenery: it is drawn after the world, lit by nothing, and
  // it must not write depth or the ribbons would occlude each other where
  // they cross. Additive so a lit path brightens the ground it lies on
  // instead of covering it with a strip of plastic.
  group.renderOrder = 10;

  const routes = pathMeta.routes.map((r) => {
    const { pts, arc, length } = drape(r.points, groundAt);
    const style = STYLE[r.tier] ?? STYLE.strand;
    const material = new THREE.ShaderMaterial({
      vertexShader,
      fragmentShader,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      // A ribbon laid flat on the ground has no consistent winding: the quad
      // for a stretch heading north comes out the opposite way round from one
      // heading south, so under the default FrontSide half a route is culled
      // and the half that survives reads as scattered chevrons rather than a
      // line. There is no back of a path to cull.
      side: THREE.DoubleSide,
      // Half a metre of lift is far below what the depth buffer can resolve
      // two kilometres out with the near plane at 2 m, so the bias is applied
      // in depth-buffer units instead, where it is the same bias at every
      // distance. The ribbon still loses to a hill in front of it, which is
      // the one thing it must still do.
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -60,
      uniforms: {
        uColour: { value: new THREE.Color(style.colour) },
        uProgress: { value: 0 },
        uGlow: { value: style.glow },
        uOpacity: { value: style.opacity },
        uWidth: { value: style.width },
        uMinPixels: { value: style.minPixels },
        uResolution: { value: new THREE.Vector2(1280, 720) },
      },
    });
    const mesh = new THREE.Mesh(ribbonGeometry(pts, arc), material);
    mesh.frustumCulled = true;
    mesh.name = `path:${r.id}`;
    group.add(mesh);
    return {
      ...r, pts, arc, length, mesh, material, style,
      igniteAt: null, progress: 0,
      // Midway along, for a label that sits on the route rather than at one
      // end of it where two routes meeting at a junction would collide.
      anchor: pts[Math.floor(pts.length / 2)],
    };
  });

  scene.add(group);

  let hovered = null;
  const ndc = new THREE.Vector3();

  const controller = {
    group,
    routes,
    named: routes.filter((r) => r.tier === 'named'),

    /**
     * Tell the ribbons how big the picture is.
     *
     * The drawing buffer, not the CSS window: on a 2x display the shader is
     * counting device pixels, and a minimum measured in the wrong ones is
     * half the line it promised.
     */
    setViewport(renderer) {
      const size = renderer.getDrawingBufferSize(new THREE.Vector2());
      for (const r of routes) r.material.uniforms.uResolution.value.copy(size);
    },

    /**
     * Start the network lighting up, longest first.
     *
     * Longest first because the two named routes are the longest things in
     * the box, so the eye is given the spine of the place before the web
     * around it — and because a stagger that ran shortest first would look
     * like a loading bar rather than like light finding its way along a path.
     */
    ignite(seconds, { stagger = 0.28 } = {}) {
      const order = [...routes].sort((a, b) => b.length - a.length);
      order.forEach((r, i) => {
        if (r.igniteAt === null) r.igniteAt = seconds + i * stagger;
      });
    },

    get ignited() {
      return routes.every((r) => r.igniteAt !== null && r.progress >= 1);
    },

    /** Advance ignition. Cheap, and does nothing once everything is lit. */
    update(seconds) {
      for (const r of routes) {
        if (r.igniteAt === null || r.progress >= 1) continue;
        // A long route takes longer to fill than a short one, so the light
        // reads as travelling at a speed rather than as an animation.
        const span = THREE.MathUtils.clamp(r.length / 420, 0.7, 2.4);
        r.progress = THREE.MathUtils.clamp((seconds - r.igniteAt) / span, 0, 1);
        r.material.uniforms.uProgress.value = r.progress;
      }
    },

    /** Light everything instantly — for capture, and for ?paths=on. */
    igniteNow() {
      for (const r of routes) {
        r.igniteAt = -1e6;
        r.progress = 1;
        r.material.uniforms.uProgress.value = 1;
      }
    },

    /**
     * Nearest route to a point on screen, or null.
     *
     * Returns the vertex index too, because clicking a 2 km route has to mean
     * something more specific than "that route" — it means the leg of it you
     * were pointing at.
     */
    pick(px, py, camera, width, height) {
      let best = null;
      for (const r of routes) {
        if (r.progress <= 0) continue;         // unlit is not yet an offer
        for (let i = 0; i < r.pts.length; i++) {
          ndc.copy(r.pts[i]).project(camera);
          if (ndc.z > 1) continue;             // behind the camera
          const sx = (ndc.x * 0.5 + 0.5) * width;
          const sy = (-ndc.y * 0.5 + 0.5) * height;
          const d = Math.hypot(sx - px, sy - py);
          // Named routes win a tie: where a spine and the web share ground,
          // the thing with a name is what you meant.
          const bias = r.tier === 'named' ? 0.6 : 1;
          if (!best || d * bias < best.score) {
            best = { route: r, index: i, distance: d, score: d * bias,
                     screen: [sx, sy] };
          }
        }
      }
      return best && best.distance <= PICK_PIXELS ? best : null;
    },

    setHover(route) {
      if (hovered === route) return false;
      for (const r of [hovered, route]) {
        if (!r) continue;
        const on = r === route;
        r.material.uniforms.uGlow.value = on ? HOVER.glow : r.style.glow;
        r.material.uniforms.uOpacity.value = on ? HOVER.opacity : r.style.opacity;
        r.material.uniforms.uMinPixels.value =
          on ? HOVER.minPixels : r.style.minPixels;
      }
      hovered = route;
      return true;
    },

    get hovered() { return hovered; },

    /**
     * Hide the whole network.
     *
     * Needed because the descent clips were rendered from a world with no lit
     * paths in it. Cutting from a live canvas with the network burning to a
     * clip without it would open a seam that has nothing to do with the
     * geometry — so the paths go out for the duration of a descent and come
     * back lit, with their progress untouched.
     */
    setVisible(on) { group.visible = on; },
  };

  return controller;
}

/**
 * The stretch of a route you actually travel: a leg, not the whole thing.
 *
 * Clicking two kilometres of cycle route cannot mean "fly all of it" — at a
 * speed that fits in a shot it is a blur, and at a speed you could walk it is
 * twenty minutes. A leg is a few hundred metres centred on the point you
 * pointed at, which is a watchable arrival and, not by accident, exactly the
 * span a generated clip would later stand in for.
 */
export function legAt(route, index, metres = 320) {
  const total = route.length;
  const here = route.arc[index];
  const half = Math.min(metres, total) / 2;
  let from = here - half;
  let to = here + half;
  if (from < 0) { to -= from; from = 0; }
  if (to > total) { from -= (to - total); to = total; }
  from = Math.max(0, from);

  // Keep every original vertex in range, plus exact ends, so the leg follows
  // the same ground the ribbon is drawn on.
  const pts = [pointAtArc(route, from)];
  for (let i = 0; i < route.arc.length; i++) {
    if (route.arc[i] > from + 0.01 && route.arc[i] < to - 0.01) {
      pts.push(route.pts[i].clone());
    }
  }
  pts.push(pointAtArc(route, to));
  return { route, pts, length: to - from, from, to };
}

/** A point at a given distance along a route, interpolated between vertices. */
export function pointAtArc(route, distance) {
  const d = THREE.MathUtils.clamp(distance, 0, route.length);
  let i = 1;
  while (i < route.arc.length - 1 && route.arc[i] < d) i++;
  const a = route.arc[i - 1], b = route.arc[i];
  const k = b > a ? (d - a) / (b - a) : 0;
  return route.pts[i - 1].clone().lerp(route.pts[i], k);
}
