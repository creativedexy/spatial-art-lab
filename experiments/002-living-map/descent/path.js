// The descent path, shared by whatever renders it.
//
// The offline capture and the live page must agree to the pixel on where the
// camera is at t=0 and t=1, or the cut into and out of the clip shows. One
// function, one JSON file, both sides import it.

import * as THREE from 'three';

export const PATH = await (await fetch(new URL('./descent-path.json', import.meta.url))).json();
export const frameCount = Math.round(PATH.durationSeconds * PATH.fps);

// Smoothstep: zero velocity at both ends, so the clip leaves the map and
// arrives at the destination without a visible kick.
const ease = (t) => t * t * (3 - 2 * t);

const tmpA = new THREE.Vector3();
const tmpB = new THREE.Vector3();

/**
 * Place `camera` at normalised position `t` (0 = A, 1 = B) along the path.
 * `groundAt(x, z)` supplies the terrain height for the look target.
 */
export function cameraAt(t, camera, groundAt) {
  const e = ease(THREE.MathUtils.clamp(t, 0, 1));
  tmpA.fromArray(PATH.a.pos);
  tmpB.fromArray(PATH.b.pos);
  camera.position.lerpVectors(tmpA, tmpB, e);

  const lx = THREE.MathUtils.lerp(PATH.a.look[0], PATH.b.look[0], e);
  const lz = THREE.MathUtils.lerp(PATH.a.look[1], PATH.b.look[1], e);
  const lift = THREE.MathUtils.lerp(PATH.a.lift, PATH.b.lift, e);
  camera.lookAt(lx, groundAt(lx, lz) + lift, lz);
  camera.updateMatrixWorld();
}

/** A camera configured exactly as the path expects. Aspect comes from size. */
export function makeCamera() {
  return new THREE.PerspectiveCamera(
    PATH.fov, PATH.size[0] / PATH.size[1], PATH.near, PATH.far);
}
