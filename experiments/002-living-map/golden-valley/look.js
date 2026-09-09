// Look development for the living map.
//
// The geometry has been right for a while — real terrain, real buildings at
// measured heights, true scale. What has been missing is everything that
// makes a render look like a place rather than a planning diagram, and
// almost none of it needs new data:
//
//   flat ambient light  ->  a low sun that casts long shadows
//   sRGB clipping       ->  filmic tone mapping, so highlights roll off
//   a blue clear colour ->  a graded sky the fog agrees with
//   one green blanket   ->  slope and height shading with warmth in it
//
// Proved in lookdev/ first and adopted here once the roofs landed, because
// adopting it means re-rendering the descent anchors and the control clip —
// the seam measurements compare pixels and every one of these changes them.
// Doing that once for three phases rather than three times is the whole
// reason this lived apart for two days.

import * as THREE from 'three';

// Late afternoon, sun in the west-south-west at about 22 degrees. Low sun is
// the single biggest lever: it is what puts a long shadow off every building
// and reveals the shape of the ground between them.
export const SUN_DIRECTION = new THREE.Vector3(-1500, 700, -900).normalize();
const HORIZON = new THREE.Color(0xd9dfe0);
const ZENITH = new THREE.Color(0x7ea3c4);
const SUN_TINT = new THREE.Color(0xffe6c2);

function skyDome() {
  const material = new THREE.ShaderMaterial({
    side: THREE.BackSide,
    depthWrite: false,
    uniforms: {
      horizon: { value: HORIZON },
      zenith: { value: ZENITH },
      sunTint: { value: SUN_TINT },
      sunDir: { value: SUN_DIRECTION.clone() },
    },
    vertexShader: `
      varying vec3 vWorld;
      void main() {
        vWorld = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }`,
    fragmentShader: `
      uniform vec3 horizon, zenith, sunTint, sunDir;
      varying vec3 vWorld;
      void main() {
        vec3 dir = normalize(vWorld);
        // Bias the gradient towards the horizon: most of what a map camera
        // sees is the bottom of the sky, and a linear ramp wastes it.
        float h = pow(clamp(dir.y, 0.0, 1.0), 0.55);
        vec3 col = mix(horizon, zenith, h);
        // A broad, cheap sun glow — no disc, this is haze, not a light source.
        float glow = pow(max(dot(dir, normalize(sunDir)), 0.0), 6.0);
        col = mix(col, sunTint, glow * 0.45);
        gl_FragColor = vec4(col, 1.0);
      }`,
  });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(9000, 32, 16), material);
  dome.frustumCulled = false;
  return dome;
}

// Ground colour by height, slope and a little noise. The map's own palette
// is a flat blend that reads as felt: at true scale a hillside needs the
// drier, paler tone the steep ground actually has, or the terrain looks like
// one painted surface however well it is lit.
function regradeTerrain(mesh) {
  const pos = mesh.geometry.attributes.position;
  const nrm = mesh.geometry.attributes.normal;
  const col = mesh.geometry.attributes.color;
  if (!col) return;
  const lowland = new THREE.Color(0x6c8a51);
  const upland = new THREE.Color(0x8b9760);
  const dry = new THREE.Color(0xa2986e);
  const c = new THREE.Color();
  let min = Infinity, max = -Infinity;
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    if (y < min) min = y;
    if (y > max) max = y;
  }
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    const h = (y - min) / (max - min);
    // Steepness from the surface normal, which is already computed.
    const steep = THREE.MathUtils.clamp((1 - nrm.getY(i)) * 7, 0, 1);
    // Two scales of variation so neither tiles nor reads as a single wash.
    const n = 0.5 + 0.25 * Math.sin(x * 0.0071 + z * 0.0043)
                  + 0.25 * Math.sin(x * 0.031 - z * 0.027);
    c.copy(lowland).lerp(upland, THREE.MathUtils.clamp(h * 1.2, 0, 1) * 0.85 + n * 0.15);
    c.lerp(dry, steep * 0.75);
    c.multiplyScalar(0.94 + n * 0.12);
    col.setXYZ(i, c.r, c.g, c.b);
  }
  col.needsUpdate = true;
}

/**
 * Re-light and re-grade a scene built by ./scene.js.
 * `extent` is the half-width in metres the shadow camera must cover.
 * `grade` colours the terrain by height and slope; turn it off when a land
 * cover image is supplying the ground colour instead, or the two multiply.
 */
export function applyLook(scene, renderer, { extent = 1250, grade = true } = {}) {
  // Filmic tone mapping, so a white model stops clipping to flat paper and
  // keeps detail in the lit faces.
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.98;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  // The old lights and the flat background go.
  for (const child of [...scene.children]) {
    if (child.isLight) scene.remove(child);
  }
  scene.background = null;

  // Exponential fog sits the far distance into the sky instead of ending at a
  // hard line, and matches the horizon colour so the join is invisible.
  scene.fog = new THREE.FogExp2(HORIZON.getHex(), 0.00022);

  const sun = new THREE.DirectionalLight(0xffe0b5, 3.9);
  sun.position.copy(SUN_DIRECTION).multiplyScalar(3000);
  sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  const cam = sun.shadow.camera;
  cam.left = -extent; cam.right = extent;
  cam.top = extent; cam.bottom = -extent;
  cam.near = 100; cam.far = 8000;
  cam.updateProjectionMatrix();
  // Normal bias rather than constant bias: the terrain is 2 km of gentle
  // slope, where a constant offset either acnes the flats or detaches the
  // shadows on the slopes.
  sun.shadow.bias = -0.0004;
  sun.shadow.normalBias = 0.15;
  scene.add(sun);
  scene.add(sun.target);

  // Sky fill, cool from above and warm bounced off the ground, so shadowed
  // faces read as shadow rather than as black.
  // Deliberately low. Fill light is what quietly erases shadows, and the
  // shadows are the entire point of this pass.
  scene.add(new THREE.HemisphereLight(0xa9c8e4, 0x8a7d5c, 0.5));

  // Do this before the dome is added: a 9 km sphere wrapping the whole scene
  // renders into the shadow map and puts everything in its own shadow.
  for (const obj of scene.children) {
    if (!obj.isMesh) continue;
    obj.castShadow = true;
    obj.receiveShadow = true;
    const m = obj.material;
    if (!m || !m.isMeshStandardMaterial) continue;
    if (m.vertexColors) {
      if (grade) regradeTerrain(obj);
      m.roughness = 1;
    } else {
      m.roughness = 0.88;
    }
    m.envMapIntensity = 0.6;
    m.needsUpdate = true;
  }

  const dome = skyDome();
  dome.castShadow = false;
  dome.receiveShadow = false;
  scene.add(dome);
  return scene;
}
