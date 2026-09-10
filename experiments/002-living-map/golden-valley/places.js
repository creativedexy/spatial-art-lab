// The photographs, as places you can go to.
//
// Every approved photograph was generated from a plate this map rendered, and
// every plate carries the camera it was rendered from. So each picture is
// already somewhere in the world — not a framing chosen to flatter it, but a
// viewpoint with coordinates. Clicking a marker flies the live camera to that
// exact camera and crossfades the photograph over it, so what you see is the
// same view of the same ground, twice: once as we measured it and once as a
// generator painted it.
//
// Plain crossfade, in and out. Dex ruled transition effects out on 10 Sep, so
// there is no transition tooling here to be tempted by later: an opacity ramp
// on an <img>, and nothing else.
//
// The photographs are of different years, so each place carries the wave
// position its picture was made at and the map is moved to agree with it on
// the way in — and put back exactly as the viewer left it on the way out.

import * as THREE from 'three';

const url = (f) => new URL(f, import.meta.url).href;
export const placeMeta = await (await fetch(url('places.json'))).json();

// Zero velocity and zero acceleration at both ends: the flight should gather
// and settle rather than start and stop.
const smoother = (t) => t * t * t * (t * (t * 6 - 15) + 10);

/**
 * Markers, flights and the crossfade.
 *
 * `future` is the wave controller from scene.js — passed in rather than
 * imported so this module has no opinion about whether 2045 exists.
 */
export function createPlaces({ camera, controls, container, future, onState = () => {} }) {
  const d = placeMeta.defaults;
  const places = placeMeta.places.map((p) => ({
    ...p,
    anchor: new THREE.Vector3(p.look[0], p.look[1], p.look[2]),
    from: new THREE.Vector3(...p.pos),
    to: new THREE.Vector3(...p.look),
  }));

  // One <img> reused for every place. Five separate elements would each hold a
  // decoded 2 MB bitmap for the whole session; one holds at most two while it
  // swaps.
  const photo = document.createElement('img');
  photo.className = 'place-photo';
  photo.alt = '';
  photo.hidden = true;
  container.appendChild(photo);

  // A marker per place. Sized for a thumb rather than a mouse: the hit area
  // is the whole button and it is 44 px tall at 390 px wide, which is the
  // smallest target a phone should ever be asked to hit.
  for (const p of places) {
    p.button = document.createElement('button');
    p.button.className = `place-marker${p.wave >= 0.5 ? ' future' : ''}`;
    p.button.type = 'button';
    p.button.innerHTML =
      `<span class="label">${p.name}</span><span class="year">${p.year}</span>`
      + '<span class="stem"></span><span class="pin"></span>';
    p.button.onclick = () => api.visit(p);
    container.appendChild(p.button);
  }

  const caption = document.createElement('div');
  caption.className = 'place-caption';
  caption.hidden = true;
  container.appendChild(caption);

  let state = 'map';           // map | flying | there | leaving
  let current = null;
  let t0 = 0;
  let home = null;
  const fromPos = new THREE.Vector3();
  const fromTarget = new THREE.Vector3();
  let fromWave = 0;
  const ndc = new THREE.Vector3();

  const setState = (s) => {
    state = s;
    container.classList.toggle('place-flying', s === 'flying' || s === 'leaving');
    onState(s, current);
  };

  const api = {
    places,
    get state() { return state; },
    get busy() { return state === 'flying' || state === 'leaving'; },
    get inside() { return state === 'there' ? current : null; },

    /** Fly to a place's own camera, then fade its photograph in over it. */
    visit(place) {
      if (api.busy || state === 'there') return;
      current = place;
      home = {
        pos: camera.position.clone(),
        target: controls.target.clone(),
        wave: future ? future.wave : 0,
        fov: camera.fov,
        minDistance: controls.minDistance,
        maxPolarAngle: controls.maxPolarAngle,
      };
      fromPos.copy(camera.position);
      fromTarget.copy(controls.target);
      fromWave = home.wave;
      controls.enabled = false;
      // The plates were rendered at fov 48 and the window is whatever the
      // viewer gives it, so the photograph is shown with `cover` and the live
      // camera is narrowed to match — the same bargain the descent makes.
      camera.fov = d.fov;
      matchFov();
      t0 = performance.now();
      setState('flying');
    },

    /** Back to the map, exactly where the viewer left it. */
    leave() {
      if (state !== 'there') return;
      fromPos.copy(camera.position);
      fromTarget.copy(controls.target);
      fromWave = future ? future.wave : 0;
      photo.classList.remove('shown');
      caption.hidden = true;
      t0 = performance.now();
      setState('leaving');
    },

    /** Drive the camera and the fade. Returns true while it owns the camera. */
    update(now = performance.now()) {
      if (state === 'map') return false;
      if (state === 'there') return true;

      const span = state === 'flying' ? d.flyMs : d.flyMs * 0.8;
      const k = smoother(Math.min(1, (now - t0) / span));
      const target = state === 'flying' ? current : home;
      const toPos = state === 'flying' ? current.from : home.pos;
      const toLook = state === 'flying' ? current.to : home.target;

      camera.position.lerpVectors(fromPos, toPos, k);
      controls.target.lerpVectors(fromTarget, toLook, k);
      camera.lookAt(controls.target);
      // The year arrives with the camera. Ramping it rather than snapping is
      // not a transition effect: it is the world's own move, and a hard cut
      // between 2026 and 2045 under a still camera looks like a bug.
      if (future) future.setWave(fromWave + (target.wave - fromWave) * k);

      if (k < 1) return true;

      if (state === 'flying') {
        photo.src = url(current.photo);
        photo.hidden = false;
        // One frame before the class lands, or the browser has nothing to
        // transition from and the fade is a cut.
        requestAnimationFrame(() => photo.classList.add('shown'));
        caption.innerHTML =
          `<strong>${current.name}</strong><span>${current.year}</span>`;
        caption.hidden = false;
        setState('there');
        return true;
      }

      photo.hidden = true;
      photo.removeAttribute('src');
      camera.fov = home.fov;
      camera.aspect = innerWidth / innerHeight;
      camera.updateProjectionMatrix();
      controls.minDistance = home.minDistance;
      controls.maxPolarAngle = home.maxPolarAngle;
      controls.enabled = true;
      controls.update();
      current = null;
      setState('map');
      return false;
    },

    /**
     * Put every marker where its place is on screen.
     *
     * Called each frame from the page's own loop rather than owning a loop
     * here: one clock drives this world and a second one would be a second
     * opinion about where the camera is.
     */
    /** The markers as declutter.js wants them: an element and a ground point. */
    get markers() {
      return places.map((p) => ({ el: p.button, anchor: p.anchor }));
    },

    updateMarkers() {
      const hide = api.busy || state === 'there';
      for (const p of places) {
        ndc.copy(p.anchor).project(camera);
        p.button.hidden = hide || ndc.z > 1;
        if (p.button.hidden) continue;
        p.button.style.left =
          `${THREE.MathUtils.clamp((ndc.x * 0.5 + 0.5) * innerWidth, 92, innerWidth - 92)}px`;
        p.button.style.top =
          `${THREE.MathUtils.clamp((-ndc.y * 0.5 + 0.5) * innerHeight, 56, innerHeight - 96)}px`;
        // Fade with distance: five markers shouting equally from a 2 km box is
        // a legend, not a place.
        const k = camera.position.distanceTo(p.anchor);
        p.button.style.setProperty('--k',
          THREE.MathUtils.clamp(1.35 - k / 3200, 0.5, 1).toFixed(2));
      }
    },

    /** Keep the live camera framing what the photograph frames. */
    resize() {
      if (state !== 'map') matchFov();
    },
  };

  function matchFov() {
    // Under `object-fit: cover` a wide window fills the photograph's width and
    // crops its top and bottom, so the live camera must narrow its vertical
    // field of view by the same amount or the two images are at different
    // scales and the crossfade shows as a zoom.
    const clipAspect = 16 / 9;
    const aspect = innerWidth / innerHeight;
    const halfV = THREE.MathUtils.degToRad(d.fov) / 2;
    camera.aspect = aspect;
    camera.fov = aspect >= clipAspect
      ? THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(halfV) * clipAspect / aspect))
      : d.fov;
    camera.updateProjectionMatrix();
  }

  return api;
}
