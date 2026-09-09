// The hotspot descent player.
//
// Session C proved the hand-off between live WebGL and a pre-rendered clip
// and measured what breaks it. This is that mechanism made reusable, wired to
// places rather than to one hard-coded path:
//
//   map ──fly to A──▶ [ clip, or the same descent flown live ] ──▶ arrived
//    ▲                                                              │
//    └──────────────────── fly back up the path ────────────────────┘
//
// A hotspot with no clip descends live along the identical path, so the map
// is complete before any video exists and simply gets better when one lands.
// That is deliberate: the path is the source of truth and the clip is an
// enhancement, which also means a clip can be swapped, re-generated or
// dropped without touching the experience around it.

import * as THREE from 'three';
import { cameraAt, matchFovToClip } from './path.js';

const wait = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * @param {object} o
 * @param {THREE.PerspectiveCamera} o.camera  the map's own camera, animated in place
 * @param {object} o.controls                 OrbitControls, disabled while flying
 * @param {HTMLElement} o.container           where the clip overlay is mounted
 * @param {(x: number, z: number) => number} o.groundAt
 * @param {URL|string} o.clipBase             what `hotspot.clip` is relative to
 * @param {(state: string, hotspot?: object) => void} [o.onState]
 */
export function createDescentPlayer({
  camera, controls, container, groundAt, clipBase, onState = () => {},
  // Asymmetric on purpose, and on evidence. Session B measured a generated
  // clip against our anchors and found the departure seam twice as bad as the
  // landing (2.79% against 1.43%): the wide aerial holds thousands of tiny
  // buildings the model cannot redraw exactly, while the landing holds a few
  // large masses it can. So spend the fade where the error is — and the
  // departure is also where the camera moves fastest, which is where a fade
  // is cheapest to hide. A path may override either.
  fadeInMs = 320, fadeOutMs = 80,
}) {
  const video = document.createElement('video');
  video.className = 'descent-clip';
  video.muted = true;
  video.playsInline = true;
  video.preload = 'auto';
  video.hidden = true;
  container.appendChild(video);

  // How long the clip is allowed to take to become playable, separately from
  // how long it is then allowed to take to play. They are different failures:
  // the first is the network, the second is a broken file, and rolling them
  // into one budget meant a slow download looked like a corrupt clip — which
  // is exactly what happened the day the world stopped being a white model
  // and the clip grew with it.
  const LOAD_BUDGET_MS = 25000;

  const mapFov = camera.fov;
  const mapMaxPolar = controls.maxPolarAngle;
  let busy = false;
  let here = null;                 // the hotspot we are standing in, if any

  function frame(path, t) {
    cameraAt(t, camera, groundAt, path);
  }

  /** Tween the camera along the path; `t` is linear, the path eases itself. */
  function flyPath(path, from, to, ms) {
    return new Promise((resolve) => {
      const t0 = performance.now();
      const step = () => {
        const k = Math.min(1, (performance.now() - t0) / ms);
        frame(path, from + (to - from) * k);
        if (k < 1) requestAnimationFrame(step);
        else resolve();
      };
      step();
    });
  }

  /** Tween from wherever the viewer left the camera to the top of the path. */
  function flyToStart(path, ms) {
    const fromPos = camera.position.clone();
    const fromLook = controls.target.clone();
    const toCam = camera.clone();
    cameraAt(0, toCam, groundAt, path);
    const toLook = new THREE.Vector3(
      path.a.look[0], groundAt(path.a.look[0], path.a.look[1]) + path.a.lift, path.a.look[1]);
    const ease = (t) => t * t * (3 - 2 * t);
    return new Promise((resolve) => {
      const t0 = performance.now();
      const look = new THREE.Vector3();
      const step = () => {
        const k = ease(Math.min(1, (performance.now() - t0) / ms));
        camera.position.lerpVectors(fromPos, toCam.position, k);
        look.lerpVectors(fromLook, toLook, k);
        camera.lookAt(look);
        camera.updateMatrixWorld();
        if (k < 1) requestAnimationFrame(step);
        else resolve();
      };
      step();
    });
  }

  /** Hand the view to the clip and take it back, per Session C's sequence. */
  async function playClip(path, src) {
    const fadeIn = path.fadeInMs ?? fadeInMs;
    const fadeOut = path.fadeOutMs ?? fadeOutMs;
    video.src = src;
    video.hidden = false;
    video.style.transition = 'none';
    video.style.opacity = '0';
    await new Promise((resolve, reject) => {
      if (video.readyState >= 2) return resolve();
      const timer = setTimeout(
        () => reject(new Error(`clip did not load in ${LOAD_BUDGET_MS} ms`)),
        LOAD_BUDGET_MS);
      video.addEventListener('loadeddata', () => { clearTimeout(timer); resolve(); },
                             { once: true });
    });
    video.currentTime = 0;

    // Fade up over an identical image: the live canvas is already sitting on
    // the clip's first frame, so this cross-fade has nothing to reveal.
    await new Promise(requestAnimationFrame);
    video.style.transition = `opacity ${fadeIn}ms linear`;
    video.style.opacity = '1';
    await wait(fadeIn + 20);

    await video.play();
    // While the clip is opaque, move the live camera to the destination and
    // leave it there. The hand-back must never wait on a first frame.
    frame(path, 1);

    const endsAt = video.duration - fadeOut / 1000;
    await new Promise((resolve) => {
      const check = () => {
        if (video.currentTime >= endsAt || video.ended) resolve();
        else requestAnimationFrame(check);
      };
      check();
    });
    video.style.transition = `opacity ${fadeOut}ms linear`;
    video.style.opacity = '0';
    await wait(fadeOut + 20);
    video.pause();
    video.hidden = true;
  }

  async function descend(hotspot) {
    if (busy || here === hotspot) return;
    busy = true;
    here = null;
    onState('descending', hotspot);
    controls.enabled = false;

    const { path } = hotspot;
    // Match the clip's framing before anything is shown, so the live frame we
    // fade out of is the frame the clip fades in on.
    matchFovToClip(camera, path, container.clientWidth / container.clientHeight);

    await flyToStart(path, 900);
    if (hotspot.clip) {
      try {
        // Guard the wall clock as well as the exceptions: a clip that stalls
        // rather than fails would otherwise leave the viewer hanging in the
        // sky for ever.
        // Loading is the slow half now: a descent of a world with foliage
        // and roofs costs 2.9 MB where the white model cost 1.8 MB, so the
        // budget has to cover arriving as well as playing.
        const budget = LOAD_BUDGET_MS + (path.durationSeconds + 6) * 1000;
        await Promise.race([
          playClip(path, new URL(hotspot.clip, clipBase).href),
          wait(budget).then(() => { throw new Error(`clip stalled after ${budget} ms`); }),
        ]);
      } catch (err) {
        // A missing or undecodable clip must never strand the viewer in the
        // sky: fall through to the live descent along the same path.
        console.warn('descent clip failed, flying it live:', err);
        video.style.opacity = '0';
        video.hidden = true;
        await flyPath(path, 0, 1, path.durationSeconds * 1000);
      }
    } else {
      await flyPath(path, 0, 1, path.durationSeconds * 1000);
    }

    frame(path, 1);
    controls.target.set(
      path.b.look[0], groundAt(path.b.look[0], path.b.look[1]) + path.b.lift, path.b.look[1]);
    // The map stops you tipping below the horizon, but an arrival is a low,
    // near-level shot by design — and OrbitControls enforces its limit on the
    // first update, silently lifting the camera off the frame the clip just
    // handed over. Open the limit to whatever this arrival needs.
    allowArrivalPitch(path);
    controls.enabled = true;
    controls.update();
    here = hotspot;
    busy = false;
    onState('arrived', hotspot);
  }

  /** Widen the pitch limit just enough for this path's landing angle. */
  function allowArrivalPitch(path) {
    const offset = camera.position.clone().sub(controls.target);
    const polar = Math.acos(THREE.MathUtils.clamp(offset.y / offset.length(), -1, 1));
    controls.maxPolarAngle = Math.max(mapMaxPolar, polar + 0.04);
  }

  async function returnToMap() {
    if (busy || !here) return;
    busy = true;
    const hotspot = here;
    here = null;
    onState('returning', hotspot);
    controls.enabled = false;

    await flyPath(hotspot.path, 1, 0, hotspot.path.durationSeconds * 800);
    controls.maxPolarAngle = mapMaxPolar;      // back to the map's own limits
    camera.fov = mapFov;                       // back to the map's own framing
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    controls.target.set(
      hotspot.path.a.look[0],
      groundAt(hotspot.path.a.look[0], hotspot.path.a.look[1]),
      hotspot.path.a.look[1]);
    controls.enabled = true;
    controls.update();
    busy = false;
    onState('map');
  }

  return {
    descend,
    returnToMap,
    /**
     * Warm the HTTP cache for every clip, at idle priority, so that clicking
     * a place does not then mean waiting for five megabytes. `prefetch` and
     * not `preload`: the world's own data has to arrive first, and a descent
     * nobody clicks should cost them nothing but spare bandwidth.
     */
    prefetchClips(hotspots) {
      for (const h of hotspots) {
        if (!h.clip) continue;
        const link = document.createElement('link');
        link.rel = 'prefetch';
        link.as = 'video';
        link.href = new URL(h.clip, clipBase).href;
        document.head.appendChild(link);
      }
    },
    get busy() { return busy; },
    get inside() { return here; },
    /** Keep the descent framing correct when the window changes shape. */
    resize(aspect) {
      if (here) matchFovToClip(camera, here.path, aspect);
    },
  };
}
