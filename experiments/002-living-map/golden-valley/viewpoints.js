// The shots, and the fact that you cannot leave them.
//
// Phase 11. Until now this was a map: orbit, pan, dolly, free, and therefore
// every frame a visitor saw was one they had composed themselves, by accident,
// while reaching for something else. The reference we started from does not
// work like that. Primland is *directed* — you are moved between frames
// somebody made — and the magic is not the rendering, it is the refusal to
// hand over the camera.
//
// So the camera lives at one of a handful of named shots, and moving is
// moving BETWEEN them. What survives of the old freedom is a lean: you may
// look around the frame you are in, within a few degrees, and you may not
// dolly at all, because zoom is where composed framings go to die. Every move
// resets the lean, so a shot cannot be permanently spoiled.
//
// Each shot has to read at both ends of the year switch, because the pair is
// the product — the same frame, once as it is and once as proposed. That is a
// composition test, not a code one, and `scripts/compose_viewpoints.py`
// renders the pairs so they can be judged by looking.

import * as THREE from 'three';

const url = (f) => new URL(f, import.meta.url).href;

// How far a lean may go from the shot it belongs to: about 17 degrees of
// swing and 8 of tilt. Wide enough to answer "what is behind that", narrow
// enough that the answer is still inside a frame we composed.
const LEAN_AZIMUTH = 0.30;
const LEAN_POLAR = 0.14;

/**
 * @param {{ camera, controls, groundAt: (x:number,z:number)=>number,
 *           root: HTMLElement, clean: boolean,
 *           onArrive?: (shot: object) => void }} ctx
 */
export async function addViewpoints({ camera, controls, groundAt, root, clean,
                                      onArrive }) {
  const spec = await fetch(url('viewpoints.json')).then((r) => r.json());
  const d = spec.defaults;
  const shots = spec.viewpoints.map((v) => ({
    ...v,
    fov: v.fov ?? d.fov,
    lift: v.lift ?? d.lift,
    flyMs: v.flyMs ?? d.flyMs,
    places: v.places ?? [],
  }));

  // The aim point is a ground position plus a lift, not a fixed height, so a
  // shot survives the heightmap being requantised — which phase 7 did, and
  // which would otherwise have moved every one of these by a metre or two.
  const targetOf = (v) => new THREE.Vector3(
    v.look[0], groundAt(v.look[0], v.look[1]) + v.lift, v.look[1]);
  const posOf = (v) => new THREE.Vector3(v.pos[0], v.pos[1], v.pos[2]);

  let at = 0;
  let flight = null;
  let held = false;        // something else owns the camera (a descent, a walk)

  // The title card is markup rather than something built here: it is the one
  // piece of the interface that is pure copy, and copy belongs in the document.
  const name = document.getElementById('shot-name');
  const says = document.getElementById('shot-says');
  const dots = document.createElement('div');
  dots.id = 'shot-dots';
  dots.setAttribute('role', 'tablist');
  dots.setAttribute('aria-label', 'Views');
  const buttons = shots.map((v, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'dot';
    b.setAttribute('role', 'tab');
    // The name is the accessible label, so the dots are a list of views
    // rather than a row of unexplained circles.
    b.setAttribute('aria-label', v.name);
    b.onclick = () => fly(i);
    dots.appendChild(b);
    return b;
  });
  const arrow = (dir, glyph, label) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = `shot-arrow ${dir}`;
    b.setAttribute('aria-label', label);
    b.innerHTML = `<span aria-hidden="true">${glyph}</span>`;
    b.onclick = () => fly(at + (dir === 'next' ? 1 : -1));
    return b;
  };
  const prev = arrow('prev', '&lsaquo;', 'The view before this one');
  const next = arrow('next', '&rsaquo;', 'The next view');
  // The dots belong to the deck, not to the page: stacked above the switch so
  // neither has to know how tall the other is. The arrows are the page's,
  // because they sit at the edges of the frame rather than under it.
  if (!clean) {
    (document.getElementById('deck') ?? root).prepend(dots);
    root.append(prev, next);
  }

  // Arrows move between shots, except while the switch has focus — it uses
  // left and right for its own two ends, and a control that loses its keys to
  // the page behind it is a control nobody can use.
  addEventListener('keydown', (e) => {
    if (e.target?.closest?.('#year-dial, input, textarea')) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); fly(at + 1); }
    if (e.key === 'ArrowLeft') { e.preventDefault(); fly(at - 1); }
  });

  function paint() {
    const v = shots[at];
    if (name) name.textContent = v.name;
    if (says) says.textContent = v.says ?? '';
    buttons.forEach((b, i) => {
      b.classList.toggle('on', i === at);
      b.setAttribute('aria-selected', String(i === at));
    });
  }

  function settle() {
    const v = shots[at];
    camera.position.copy(posOf(v));
    controls.target.copy(targetOf(v));
    camera.fov = v.fov;
    camera.updateProjectionMatrix();
    camera.lookAt(controls.target);
    // Read the shot back as a sphere around its own aim point, then fence it.
    const s = new THREE.Spherical().setFromVector3(
      camera.position.clone().sub(controls.target));
    controls.minDistance = controls.maxDistance = s.radius;
    controls.minAzimuthAngle = s.theta - LEAN_AZIMUTH;
    controls.maxAzimuthAngle = s.theta + LEAN_AZIMUTH;
    controls.minPolarAngle = Math.max(0.05, s.phi - LEAN_POLAR);
    controls.maxPolarAngle = Math.min(1.45, s.phi + LEAN_POLAR);
    controls.enablePan = false;
    controls.enableZoom = false;
    if (!held) controls.enabled = true;
    controls.update();
    onArrive?.(v);
  }

  function fly(i, { instant = false } = {}) {
    const n = shots.length;
    at = ((i % n) + n) % n;      // the set wraps, so neither end is a dead stop
    paint();
    const to = shots[at];
    const toPos = posOf(to);
    // Nothing to animate if we are already standing in it — which is the case
    // the moment the opening drift finishes on shot one, and a 3.2 second
    // no-op there is 3.2 seconds of a control that does not answer.
    const arrived = camera.position.distanceTo(toPos) < 1
      && controls.target.distanceTo(targetOf(to)) < 1;
    if (instant || arrived) { flight = null; settle(); return; }
    controls.enabled = false;
    flight = {
      fromPos: camera.position.clone(),
      fromTarget: controls.target.clone(),
      toPos,
      toTarget: targetOf(to),
      fromFov: camera.fov,
      toFov: to.fov,
      startedAt: performance.now(),
      ms: to.flyMs,
      // A straight line between two low cameras cuts through whatever hill is
      // between them. Lifting the middle of the move turns a dolly into a
      // flight, and is the difference between going somewhere and sliding.
      arc: Math.min(220, 0.16 * camera.position.distanceTo(toPos)),
    };
  }

  paint();

  return {
    get shots() { return shots; },
    get at() { return at; },
    get current() { return shots[at]; },
    get flying() { return flight !== null; },
    fly,

    /** Let a descent or a walk take the camera, and give it back after. */
    hold(on) {
      held = on;
      if (on) { flight = null; controls.enabled = false; }
      else settle();
    },

    update(now) {
      if (!flight) return false;
      const k = Math.min(1, (now - flight.startedAt) / flight.ms);
      // Eased at both ends: a move that starts and stops is a cut with extra
      // steps.
      const e = k * k * (3 - 2 * k);
      camera.position.lerpVectors(flight.fromPos, flight.toPos, e);
      camera.position.y += Math.sin(Math.PI * e) * flight.arc;
      controls.target.lerpVectors(flight.fromTarget, flight.toTarget, e);
      camera.fov = flight.fromFov + (flight.toFov - flight.fromFov) * e;
      camera.updateProjectionMatrix();
      camera.lookAt(controls.target);
      if (k >= 1) { flight = null; settle(); }
      return true;
    },
  };
}
