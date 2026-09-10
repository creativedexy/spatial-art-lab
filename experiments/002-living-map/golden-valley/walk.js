// Travelling a path.
//
// Phase 5, the half that turns a lit line into somewhere you have been. The
// shape is deliberately the same as the descent player's — dive, travel,
// arrive, return — because a walk along a route and a descent into a place
// are the same move at different scales, and when a generated clip eventually
// stands in for one of these legs it has to hand back to a live camera that
// was following exactly this curve.
//
// Two things it does not do, on purpose:
//
//   It does not fly the whole route. Two kilometres of cycle route is twenty
//   minutes at a walk and a blur at anything faster. A leg is a few hundred
//   metres around the point you clicked, which is a shot.
//
//   It does not pin the world clock. The descent player does, because a
//   pre-rendered clip has to be under the same cloud as the live canvas it
//   cuts back to. Nothing here is pre-rendered yet, so the weather simply
//   keeps running — and the day the first leg is generated, this is the one
//   line that has to change.

import * as THREE from 'three';
import { pointAtArc } from './paths.js';

// How high the camera rides, and how far up the path it looks.
//
// Not eye height, and that is a finding rather than a preference. At 2.4 m the
// land cover is a 1 m/texel image seen at a grazing angle and there is no
// grass, kerb or verge geometry under it, so the bottom half of the frame is
// a smear — and the first plate captured for a generator was exactly that.
// The map is surveyed to the metre from the air; it is not a walk simulator,
// and pretending otherwise makes both the picture and the conditioning worse.
// A low glide is honest about what we have: high enough that the texture
// resolves and hedges and roofs give parallax, low enough that you are plainly
// travelling the route rather than looking down at it.
export const RIDE = { eye: 14, lookAhead: 70 };
const SPEED = 17;            // metres a second — brisk, not a blur
const MIN_S = 9, MAX_S = 22;
const DIVE_MS = 1700;
const RETURN_MS = 2100;

// What the orbit controls are allowed to do while you are standing on a path,
// as against hovering over two square kilometres. The map's own limits — keep
// sixty metres off the target, never tilt within eleven degrees of level —
// are the right limits for an aerial and completely wrong for a walker: on
// hand-over they would shove the camera back to sixty metres and lift it
// clear of the ground to satisfy the tilt, which is how an arrival at eye
// height became an arrival twelve metres in the air.
const WALK_LIMITS = { minDistance: 2, maxDistance: 400, maxPolarAngle: 1.57 };

// Zero velocity at both ends, and zero acceleration too, so neither the
// departure nor the arrival has a kick in it.
const smoother = (t) => t * t * t * (t * (t * 6 - 15) + 10);

function arcOf(pts) {
  const arc = [0];
  for (let i = 1; i < pts.length; i++) {
    arc.push(arc[i - 1] + pts[i].distanceTo(pts[i - 1]));
  }
  return arc;
}

/** A leg with its own arc table — its ends fall mid-segment on the route. */
export function measureLeg(chosen) {
  const arc = arcOf(chosen.pts);
  return { ...chosen, arc, length: arc[arc.length - 1] };
}

/**
 * Where the camera stands, and what it looks at, `distance` metres along a
 * leg. Exported because the offline capture and the live walk must agree to
 * the pixel: a generated clip is only invisible at the cut if the frame it
 * starts from came from the same camera the map hands back to. One function,
 * both sides — the same bargain descent/path.js makes.
 */
export function cameraOnLeg(leg, distance, groundAt,
                            pos = new THREE.Vector3(), look = new THREE.Vector3(),
                            ride = RIDE) {
  const { eye, lookAhead } = ride;
  const p = pointAtArc(leg, distance);
  pos.set(p.x, groundAt(p.x, p.z) + eye, p.z);
  // Looking up the path rather than at a fixed point: on a curve that is what
  // makes the walk feel like following a route instead of orbiting a target
  // that happens to be ahead of you.
  const q = pointAtArc(leg, Math.min(distance + lookAhead, leg.length));
  // Slightly below eye level, because a walker looks at the ground they are
  // about to cover, and because a level camera on a rising path aims at sky.
  look.set(q.x, groundAt(q.x, q.z) + eye * 0.72, q.z);
  // Within a look-ahead of the end the target would stop moving and the
  // camera would swing round to face it. Push it past the end instead.
  if (distance + lookAhead > leg.length) {
    const back = pointAtArc(leg, Math.max(0, leg.length - lookAhead));
    const end = pointAtArc(leg, leg.length);
    look.set(
      end.x + (end.x - back.x) * 0.5,
      groundAt(end.x, end.z) + eye * 0.72,
      end.z + (end.z - back.z) * 0.5,
    );
  }
  return { pos, look };
}

/** How long a leg takes to walk, in seconds. Also the clip's duration. */
export const legSeconds = (leg) =>
  THREE.MathUtils.clamp(leg.length / SPEED, MIN_S, MAX_S);

/**
 * A leg walker bound to one camera and one set of orbit controls.
 *
 * `onState(state, leg)` is called with 'diving', 'walking', 'arrived',
 * 'returning' and 'map', which is what the page hangs its panel off.
 */
export function createPathWalk({ camera, controls, groundAt, onState = () => {} }) {
  // The leg's own arc table, rather than the parent route's: a leg starts and
  // ends mid-segment, so its distances are its own.
  let leg = null;
  let state = 'map';
  let t0 = 0;
  let seconds = 0;
  let home = null;            // where the map was before we left it
  const pos = new THREE.Vector3();
  const look = new THREE.Vector3();
  const from = new THREE.Vector3();
  const fromTarget = new THREE.Vector3();

  const placeAt = (distance) => cameraOnLeg(leg, distance, groundAt, pos, look);

  const api = {
    get state() { return state; },
    get busy() { return state === 'diving' || state === 'walking' || state === 'returning'; },
    get inside() { return state === 'arrived' ? leg : null; },
    get leg() { return leg; },

    /** Take a leg — the object legAt() returns, with its own arc table. */
    walk(chosen) {
      if (api.busy) return;
      leg = measureLeg(chosen);
      seconds = legSeconds(leg);
      home = {
        pos: camera.position.clone(),
        target: controls.target.clone(),
        minDistance: controls.minDistance,
        maxDistance: controls.maxDistance,
        maxPolarAngle: controls.maxPolarAngle,
      };
      from.copy(camera.position);
      fromTarget.copy(controls.target);
      controls.enabled = false;
      state = 'diving';
      t0 = performance.now();
      onState(state, leg);
    },

    /** Back to the aerial the walk left from. */
    returnToMap() {
      if (state !== 'arrived') return;
      from.copy(camera.position);
      fromTarget.copy(controls.target);
      // The controls were handed back on arrival, so they have to be taken
      // away again: a drag part-way through the return would fight the lerp
      // for the same three numbers and win half of them.
      controls.enabled = false;
      state = 'returning';
      t0 = performance.now();
      onState(state, leg);
    },

    /** Drive the camera. Returns true while it owns it. */
    update(now = performance.now()) {
      if (state === 'map' || state === 'arrived') return false;
      const elapsed = now - t0;

      if (state === 'diving') {
        const k = smoother(Math.min(1, elapsed / DIVE_MS));
        placeAt(0);
        camera.position.lerpVectors(from, pos, k);
        controls.target.lerpVectors(fromTarget, look, k);
        camera.lookAt(controls.target);
        if (k >= 1) { state = 'walking'; t0 = now; onState(state, leg); }
        return true;
      }

      if (state === 'walking') {
        const k = Math.min(1, elapsed / (seconds * 1000));
        placeAt(smoother(k) * leg.length);
        camera.position.copy(pos);
        controls.target.copy(look);
        camera.lookAt(look);
        if (k >= 1) {
          state = 'arrived';
          // Handing the controls over where the camera already is, rather
          // than snapping to a tidier vantage: the place you were left is the
          // place you get to look around from. Which only works if the limits
          // let it — hence the swap first, and controls.update() second.
          Object.assign(controls, WALK_LIMITS);
          controls.enabled = true;
          controls.update();
          onState(state, leg);
        }
        return true;
      }

      // returning
      const k = smoother(Math.min(1, elapsed / RETURN_MS));
      camera.position.lerpVectors(from, home.pos, k);
      controls.target.lerpVectors(fromTarget, home.target, k);
      camera.lookAt(controls.target);
      if (k >= 1) {
        state = 'map';
        leg = null;
        controls.minDistance = home.minDistance;
        controls.maxDistance = home.maxDistance;
        controls.maxPolarAngle = home.maxPolarAngle;
        controls.enabled = true;
        controls.update();
        onState(state, null);
      }
      return true;
    },
  };

  return api;
}
