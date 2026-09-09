// The descent path, shared by whatever renders it.
//
// The offline capture and the live page must agree to the pixel on where the
// camera is at t=0 and t=1, or the cut into and out of the clip shows. One
// function, one JSON file, both sides import it.

import * as THREE from 'three';

const load = async (file) => (await fetch(new URL(file, import.meta.url))).json();

/** The control path Session C measured — also the seam test's subject. */
export const PATH = await load('./descent-path.json');
export const frameCount = Math.round(PATH.durationSeconds * PATH.fps);
/**
 * How much time the clip's *frames* span, which is one frame less than its
 * duration: 96 frames at 24 fps run from 0 to 95/24 = 3.958 s, not to 4 s.
 * Worth a name, because anything animated in the world has to be at 3.958 s
 * when the live canvas takes the picture back, and 4 s is close enough to
 * look right and wrong enough to measure.
 */
export const clipSeconds = (path = PATH) =>
  (Math.round(path.durationSeconds * path.fps) - 1) / path.fps;

/** Every place you can descend into, each path filled in from `defaults`. */
export async function loadHotspots() {
  const doc = await load('./hotspots.json');
  return doc.hotspots.map((h) => ({ ...h, path: { ...doc.defaults, ...h.path } }));
}

// Smoothstep: zero velocity at both ends, so the clip leaves the map and
// arrives at the destination without a visible kick.
const ease = (t) => t * t * (3 - 2 * t);

const tmpA = new THREE.Vector3();
const tmpB = new THREE.Vector3();

/**
 * Place `camera` at normalised position `t` (0 = A, 1 = B) along `path`.
 * `groundAt(x, z)` supplies the terrain height for the look target.
 */
export function cameraAt(t, camera, groundAt, path = PATH) {
  const e = ease(THREE.MathUtils.clamp(t, 0, 1));
  tmpA.fromArray(path.a.pos);
  tmpB.fromArray(path.b.pos);
  camera.position.lerpVectors(tmpA, tmpB, e);

  const lx = THREE.MathUtils.lerp(path.a.look[0], path.b.look[0], e);
  const lz = THREE.MathUtils.lerp(path.a.look[1], path.b.look[1], e);
  const lift = THREE.MathUtils.lerp(path.a.lift, path.b.lift, e);
  camera.lookAt(lx, groundAt(lx, lz) + lift, lz);
  camera.updateMatrixWorld();
}

/** A camera configured exactly as the path expects. Aspect comes from size. */
export function makeCamera(path = PATH) {
  return new THREE.PerspectiveCamera(
    path.fov, path.size[0] / path.size[1], path.near, path.far);
}

/**
 * Make a live camera frame exactly what a clip shows when the clip is
 * displayed with `object-fit: cover`.
 *
 * The clip has one aspect ratio for ever; the window has whatever the viewer
 * gives it. Under `cover` a wide window fills the clip's width and crops its
 * top and bottom, so the live camera must narrow its vertical field of view
 * by the same amount or the two images are at different scales and the seam
 * shows however perfectly the clip lands.
 */
export function matchFovToClip(camera, path, aspect) {
  const clipAspect = path.size[0] / path.size[1];
  const halfV = THREE.MathUtils.degToRad(path.fov) / 2;
  camera.aspect = aspect;
  camera.fov = aspect >= clipAspect
    ? THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(halfV) * clipAspect / aspect))
    : path.fov;                     // taller window: height is what survives
  camera.updateProjectionMatrix();
}
