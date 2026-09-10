// Phase 4, the half that needs no decision from anyone: weather and movement.
//
// Everything before this was true and still. A surveyed place with the right
// light, the right ground and the right roofs — and nothing in it moving,
// which is the last thing that says "render" rather than "afternoon". Four
// things fix that, and none of them needs new data:
//
//   cloud shadows   a noise field drifting across the vale, so the light
//                   changes while you look at it
//   wind            the trees lean and recover, amplitude by height
//   water           the streams and ponds catch the sun and ripple
//   birds           a flock, actually flocking
//
// ── The one hard constraint ──────────────────────────────────────────────
//
// A descent hands a pre-rendered clip to a live canvas and the join is
// measured in pixels. Anything animated by `performance.now()` would put the
// clip's last frame and the live canvas at different moments of the same
// afternoon, and no fade can hide a cloud shadow in the wrong place. So
// nothing here reads the wall clock. Everything is a function of one number,
// `updateLife(seconds)`, which the map advances in real time, the capture
// steps frame by frame, and the descent player pins to the clip's own
// playback position. The flock is a simulation and therefore the awkward
// case: it is stepped at a fixed 1/60 s and rewinds to a seeded start
// whenever time goes backwards, so asking for t = 3.9583 s twice gives the
// same 90 birds in the same places both times.

import * as THREE from 'three';

const FLOCK = 90;
const FIXED_STEP = 1 / 60;
const MAX_CATCHUP = 4;            // seconds of simulation any one call may run

const uniforms = {
  uTime: { value: 0 },
  // Scales the wind to nothing for a structure pass. A depth or normal render
  // uses an override material, which does not carry the tree material's sway,
  // so a swaying beauty frame and a still depth frame would disagree about
  // where the canopy is — and disagreeing by a metre is exactly the kind of
  // thing a depth-conditioned generator turns into a smear.
  uWindAmp: { value: 1 },
  // West-south-west, the same quarter the sun is in, because a sky where the
  // cloud and the light disagree reads as two separate effects.
  uWind: { value: new THREE.Vector2(0.86, 0.51).normalize() },
  uClassMap: { value: null },
  uWaterIndex: { value: 10 },
};

// Two octaves of value noise. Three looked better and cost a third of the
// frame on a machine with no GPU; the shadows are soft-edged anyway.
const NOISE = /* glsl */`
  float lifeHash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
  }
  float lifeNoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(mix(lifeHash(i), lifeHash(i + vec2(1.0, 0.0)), f.x),
               mix(lifeHash(i + vec2(0.0, 1.0)), lifeHash(i + vec2(1.0, 1.0)), f.x), f.y);
  }
  float lifeCloud(vec2 world, vec2 wind, float t) {
    // A noise cell is about 800 m, so three or four clouds cross the box —
    // enough that the light changes as you pan, few enough that the vale
    // never reads as dappled.
    vec2 p = world * 0.00125 - wind * t * 0.0065;
    return lifeNoise(p) * 0.66 + lifeNoise(p * 2.7 + 4.1) * 0.34;
  }`;

const WORLD_VARYING = 'varying vec2 vLifeWorld;';
const WORLD_ASSIGN = /* glsl */`
  #ifdef USE_INSTANCING
    vLifeWorld = (modelMatrix * instanceMatrix * vec4(transformed, 1.0)).xz;
  #else
    vLifeWorld = (modelMatrix * vec4(transformed, 1.0)).xz;
  #endif`;

// Cloud shadow applied to albedo rather than to the sun alone. Not physical —
// a cloud dims the direct sun far more than the sky — but a stylised map
// wants the whole surface to cool and settle, and the honest version needs
// the light loop rewritten for one visual effect that reads the same.
const CLOUD_FRAGMENT = /* glsl */`
  float lifeCover = smoothstep(0.40, 0.63, lifeCloud(vLifeWorld, uWind, uTime));
  diffuseColor.rgb *= mix(vec3(1.0), vec3(0.55, 0.61, 0.74), lifeCover);`;

function inject(source, marker, addition, where = 'after') {
  return source.replace(marker, where === 'after' ? marker + addition : addition + marker);
}

/** Cloud shadows on any standard material, plus whatever else is asked for. */
/**
 * Give a material the world's clock: cloud shadows, wind, water shimmer.
 *
 * Exported because Phase 6 adds meshes AFTER bringToLife has run its traverse,
 * and a new hedge that did not darken when a cloud crossed it would be the
 * one thing in the frame that was not in the same weather as everything else.
 */
export function applyLife(material, { water = false, wind = 0, flap = 0 } = {}) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);

    let v = shader.vertexShader;
    v = inject(v, '#include <common>',
      `\n${WORLD_VARYING}\nuniform float uTime;\nuniform vec2 uWind;\nuniform float uWindAmp;\n`);
    if (wind) {
      // The unit tree is one metre tall before its instance matrix scales it,
      // so `position.y` is already "fraction of the way up the tree" and the
      // square of it is a decent bending curve for a trunk. Displacing in
      // local space means the sway scales with the tree, which is what makes
      // a hedge twitch while a mature oak rolls.
      v = inject(v, '#include <begin_vertex>', /* glsl */`
        #ifdef USE_INSTANCING
          vec2 lifeBase = (modelMatrix * instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xz;
        #else
          vec2 lifeBase = vec2(0.0);
        #endif
        float lifePhase = dot(lifeBase, vec2(0.061, 0.043));
        float lifeGust = 0.65 + 0.35 * sin(uTime * 0.31 + lifeBase.x * 0.004);
        float lifeSway = sin(uTime * 1.7 + lifePhase) * 0.6
                       + sin(uTime * 3.1 + lifePhase * 1.7) * 0.4;
        transformed.xz += uWind * lifeSway * lifeGust * uWindAmp
                        * position.y * position.y * ${wind.toFixed(3)};`);
    }
    if (flap) {
      v = inject(v, '#include <begin_vertex>', /* glsl */`
        #ifdef USE_INSTANCING
          vec3 lifeBird = (instanceMatrix * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
        #else
          vec3 lifeBird = vec3(0.0);
        #endif
        transformed.y += abs(position.x)
                       * sin(uTime * 8.0 + dot(lifeBird.xz, vec2(0.7, 0.3)))
                       * ${flap.toFixed(3)};`);
    }
    v = inject(v, '#include <project_vertex>', WORLD_ASSIGN);
    shader.vertexShader = v;

    let f = shader.fragmentShader;
    f = inject(f, '#include <common>',
      `\n${WORLD_VARYING}\nuniform float uTime;\nuniform vec2 uWind;\n` +
      (water ? 'uniform sampler2D uClassMap;\nuniform float uWaterIndex;\n' : '') +
      NOISE);
    if (water) {
      // gv-landclass.png has been sitting in the repo since Phase 2 with
      // nothing reading it. This is what it was kept for: the ground knows
      // which of its texels are water, so the water can move without any
      // geometry, any mask painted by hand, or any second material.
      f = inject(f, '#include <map_fragment>', /* glsl */`
        float lifeClass = texture2D(uClassMap, vMapUv).r * 255.0;
        float lifeWater = 1.0 - step(0.5, abs(lifeClass - uWaterIndex));
        float lifeRipple =
            sin(vLifeWorld.x * 0.85 + vLifeWorld.y * 0.55 + uTime * 1.5)
          * sin(vLifeWorld.x * -0.47 + vLifeWorld.y * 1.05 + uTime * 2.1);
        diffuseColor.rgb += lifeWater * vec3(0.05, 0.07, 0.09)
                          * smoothstep(0.25, 1.0, lifeRipple);`);
      f = inject(f, '#include <roughnessmap_fragment>', /* glsl */`
        roughnessFactor = mix(roughnessFactor, 0.24, lifeWater);`);
    }
    f = inject(f, '#include <map_fragment>', CLOUD_FRAGMENT);
    shader.fragmentShader = f;
  };
  material.needsUpdate = true;
}

// --- the flock ---------------------------------------------------------------

function mulberry32(a) {
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function birdGeometry() {
  // Pointing down -Z, wings along X, flat — a silhouette, because at 200 m a
  // bird is four pixels and all that survives is its outline and its beat.
  const v = [];
  const tri = (a, b, c) => v.push(...a, ...b, ...c);
  tri([0, 0, -1.0], [-0.11, 0, 0.45], [0.11, 0, 0.45]);
  for (const s of [-1, 1]) {
    tri([0, 0, -0.2], [s * 1.0, 0, 0.1], [s * 0.85, 0, 0.42]);
    tri([0, 0, -0.2], [s * 0.85, 0, 0.42], [0, 0, 0.3]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(v, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(new Float32Array(v.length / 3 * 2), 2));
  g.computeVertexNormals();
  return g;
}

// `steps` rather than a time: the simulation only ever advances in whole
// 1/60 s increments, so the state is a pure function of how many of them
// have run, and asking for the same second twice gives the same 90 birds.
const flock = {
  mesh: null, pos: null, vel: null, groundAt: null, steps: -1,
  span: 700, cruise: 95, speed: 11,
};

function seedFlock() {
  const rng = mulberry32(20260909);
  const { span, cruise } = flock;
  for (let i = 0; i < FLOCK; i++) {
    const x = (rng() - 0.5) * span * 2;
    const z = (rng() - 0.5) * span * 2;
    flock.pos[i * 3] = x;
    flock.pos[i * 3 + 1] = flock.groundAt(x, z) + cruise + (rng() - 0.5) * 30;
    flock.pos[i * 3 + 2] = z;
    const a = rng() * Math.PI * 2;
    flock.vel[i * 3] = Math.cos(a) * flock.speed;
    flock.vel[i * 3 + 1] = (rng() - 0.5) * 0.6;
    flock.vel[i * 3 + 2] = Math.sin(a) * flock.speed;
  }
  flock.steps = 0;
}

function stepFlock(dt) {
  const { pos, vel, span, cruise, speed, groundAt } = flock;
  const SEP = 24, SEP2 = SEP * SEP, NEAR = 70, NEAR2 = NEAR * NEAR;
  for (let i = 0; i < FLOCK; i++) {
    const ix = i * 3;
    let sx = 0, sy = 0, sz = 0;        // separation
    let ax = 0, ay = 0, az = 0, an = 0; // alignment
    let cx = 0, cy = 0, cz = 0, cn = 0; // cohesion
    for (let j = 0; j < FLOCK; j++) {
      if (j === i) continue;
      const jx = j * 3;
      const dx = pos[jx] - pos[ix], dy = pos[jx + 1] - pos[ix + 1], dz = pos[jx + 2] - pos[ix + 2];
      const d2 = dx * dx + dy * dy + dz * dz;
      if (d2 > NEAR2 || d2 < 1e-6) continue;
      if (d2 < SEP2) {
        const w = (SEP2 - d2) / SEP2;
        sx -= dx * w; sy -= dy * w; sz -= dz * w;
      }
      ax += vel[jx]; ay += vel[jx + 1]; az += vel[jx + 2]; an++;
      cx += pos[jx]; cy += pos[jx + 1]; cz += pos[jx + 2]; cn++;
    }
    let fx = sx * 0.9, fy = sy * 0.9, fz = sz * 0.9;
    if (an) {
      fx += (ax / an - vel[ix]) * 1.1;
      fy += (ay / an - vel[ix + 1]) * 1.1;
      fz += (az / an - vel[ix + 2]) * 1.1;
    }
    if (cn) {
      fx += (cx / cn - pos[ix]) * 0.06;
      fy += (cy / cn - pos[ix + 1]) * 0.06;
      fz += (cz / cn - pos[ix + 2]) * 0.06;
    }
    // Hold a cruising height above the ground rather than an altitude: the
    // vale rises 35 m across the box, and a flock at a fixed altitude flies
    // into the escarpment.
    const want = groundAt(pos[ix], pos[ix + 2]) + cruise;
    fy += (want - pos[ix + 1]) * 0.5;
    // And stay over the map.
    fx -= pos[ix] * 0.004 * Math.max(0, Math.abs(pos[ix]) / span - 0.7);
    fz -= pos[ix + 2] * 0.004 * Math.max(0, Math.abs(pos[ix + 2]) / span - 0.7);

    vel[ix] += fx * dt; vel[ix + 1] += fy * dt; vel[ix + 2] += fz * dt;
    const sp = Math.hypot(vel[ix], vel[ix + 1], vel[ix + 2]) || 1;
    const k = speed / sp;
    vel[ix] *= k; vel[ix + 1] *= k * 0.55; vel[ix + 2] *= k;
    pos[ix] += vel[ix] * dt;
    pos[ix + 1] += vel[ix + 1] * dt;
    pos[ix + 2] += vel[ix + 2] * dt;
  }
}

const _m = new THREE.Matrix4();
const _q = new THREE.Quaternion();
const _p = new THREE.Vector3();
const _d = new THREE.Vector3();
const _s = new THREE.Vector3(2.2, 2.2, 2.2);
const FORWARD = new THREE.Vector3(0, 0, -1);

function writeFlock() {
  for (let i = 0; i < FLOCK; i++) {
    const ix = i * 3;
    _p.set(flock.pos[ix], flock.pos[ix + 1], flock.pos[ix + 2]);
    _d.set(flock.vel[ix], flock.vel[ix + 1], flock.vel[ix + 2]).normalize();
    _q.setFromUnitVectors(FORWARD, _d);
    flock.mesh.setMatrixAt(i, _m.compose(_p, _q, _s));
  }
  flock.mesh.instanceMatrix.needsUpdate = true;
}

/**
 * Patch every material in the scene for weather, and add the flock.
 * `classMap` is the Phase 2 land class image; `waterIndex` its water value.
 */
export function bringToLife(scene, { groundAt, classMap, waterIndex }) {
  uniforms.uClassMap.value = classMap;
  uniforms.uWaterIndex.value = waterIndex;

  scene.traverse((obj) => {
    const m = obj.isMesh && obj.material;
    if (!m || !m.isMeshStandardMaterial) return;
    if (m.vertexColors && m.map) applyLife(m, { water: true });         // the ground
    else if (obj.parent && obj.parent.name === 'trees') applyLife(m, { wind: 0.05 });
    else applyLife(m);
  });

  const material = new THREE.MeshStandardMaterial({
    color: 0x33343a, roughness: 0.9, side: THREE.DoubleSide, flatShading: true,
  });
  applyLife(material, { flap: 0.32 });
  flock.mesh = new THREE.InstancedMesh(birdGeometry(), material, FLOCK);
  flock.mesh.name = 'birds';
  flock.mesh.castShadow = false;
  flock.mesh.receiveShadow = false;
  flock.mesh.frustumCulled = false;
  flock.pos = new Float32Array(FLOCK * 3);
  flock.vel = new Float32Array(FLOCK * 3);
  flock.groundAt = groundAt;
  seedFlock();
  writeFlock();
  scene.add(flock.mesh);
  return flock.mesh;
}

/**
 * Move the world to `seconds`. The only clock in the scene: called once per
 * frame with `worldSeconds()` on the map, and with the frame's own time when
 * capturing, which is what makes a captured clip reproducible.
 */
export function updateLife(seconds) {
  uniforms.uTime.value = seconds;
  if (!flock.mesh) return;
  const target = Math.floor(seconds / FIXED_STEP);
  if (target < flock.steps) seedFlock();          // time ran backwards: rewind
  // A tab that was in the background for a minute must not spend a minute of
  // simulation catching up, so a large jump is skipped rather than replayed.
  // Determinism is only promised forwards from a rewind, which is the case
  // the capture and the descent both use.
  const catchUp = Math.min(target - flock.steps, MAX_CATCHUP / FIXED_STEP);
  for (let i = 0; i < catchUp; i++) stepFlock(FIXED_STEP);
  flock.steps = target;
  writeFlock();
}

// --- the clock ---------------------------------------------------------------
// Wall time, but rebaseable, because a descent has to be able to say "the
// world is now at the moment this clip's frame was rendered" and then hand
// the map back a clock that carries on from there rather than snapping.

let originMs = 0;
let pinned = null;

export function worldSeconds() {
  return pinned !== null ? pinned : (performance.now() - originMs) / 1000;
}

/**
 * Freeze the vegetation and hide the flock, for renders that are describing
 * the world's *structure* rather than picturing it. Everything a generator is
 * conditioned on has to agree with everything else, and a bird is a hole in a
 * depth map.
 */
export function setStructureMode(on) {
  uniforms.uWindAmp.value = on ? 0 : 1;
  if (flock.mesh) flock.mesh.visible = !on;
}

/** Hold the world at one instant — used while a pre-rendered clip is on screen. */
export function pinWorld(seconds) {
  pinned = seconds;
}

/** Let time run again, continuing from `atSeconds` with no jump. */
export function releaseWorld(atSeconds) {
  pinned = null;
  originMs = performance.now() - atSeconds * 1000;
}
