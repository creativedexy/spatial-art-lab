// Today's Cheltenham, streamed, with our 2045 scheme standing on it.
//
// Task 002. Everything in this map was measured or written: LiDAR terrain, OSM
// footprints extruded to their own heights, roofs classified from the survey,
// facades from rules. That is what makes it defensible, and it is also why it
// looks like a model. Google's photogrammetry of the real town is photoreal
// from about 150 m up and brings the horizon with it, and the local session
// found GCHQ's ring landing within a few pixels of our own surveyed lock —
// two independent sources agreeing about where a building is.
//
// So: today becomes the real place, and the future stays ours. The year dial
// then sweeps a scheme we can defend across a town nobody has to take on
// trust.
//
// ── What the licence decides ─────────────────────────────────────────────
//
// The Map Tiles API terms (checked 10 Sep 2026) are not a footnote here, they
// are the architecture:
//
//   No caching, no pre-fetching, no offline use. Tiles are a LIVE layer and
//   nothing else. They never feed a plate, Codex, or a film — the measured map
//   stays the source of every generated image, which is also why none of this
//   touches capture_plate.py.
//
//   Attribution must be visible, always, including at 390 px. It is gathered
//   from the renderer rather than typed, because what is being credited
//   changes with what is on screen.
//
//   Our own 3D objects may be overlaid, provided they are not traced or
//   derived from the tiles. Ours come from LiDAR, OSM and written rules, so
//   they qualify — and that is worth keeping true.
//
// ── What our ground still draws, measured ─────────────────────────────────
//
// Tiles may not be modified, so 2045's orchards and wetland cannot be painted
// onto them: our terrain is drawn on top instead, and only where the scheme
// actually changes the ground. Comparing the two class maps square metre by
// square metre, that is **68.6 ha of the 400 in the box — 17.2%**:
//
//   orchard      21.9 ha      the ring of new planting around everything built
//   grass        17.9 ha      the ground the new buildings stand on
//   wetland      15.5 ha      the brook corridor let go
//   agrivoltaic   9.6 ha      the west-facing slopes under panels
//   roads         2.5 ha      the new streets between the blocks
//   scrub         1.3 ha
//
// The other 331 ha is the real town, showing through: 126.6 ha of existing
// residential, 56.3 ha of farmland the scheme does not touch, 26.1 ha of
// grass, 24.4 ha of minor road, 17.8 ha of wood, 17.6 ha of hardstanding and
// 12 ha of park. That is the point — a scheme is a change to a place, and
// this is the only version of the map where the place is not also ours.
//
// ── Two things that cost money or credibility if got wrong ───────────────
//
//   Billing is per root tileset request, which is one per TilesRenderer. So
//   there is exactly one, made once, and never rebuilt on a toggle, a resize
//   or a year change. A page that recreates it when the dial moves is a bill.
//
//   Without a key this module does nothing at all — it is not even fetched,
//   because the import lives behind the check. The public map is the measured
//   one, unchanged, at the weight phase 7 got it down to.

import * as THREE from 'three';

/** The box centre, BNG 391400 222400, and the geoid height here. */
export const ORIGIN = { lat: 51.900076, lon: -2.126397, geoid: 48.6 };

/**
 * Below this height above the ground, photogrammetry stops being photoreal:
 * it melts, because a camera flying over a town never saw the underside of a
 * hedge or the face of a wall from six metres. Our measured map takes over.
 *
 * UNMEASURED. There is no key in this container, so this is the local
 * session's number to fill in — `scripts/probe_tiles.py` prints it. Until it
 * does, this is deliberately generous rather than a guess dressed as a
 * finding: the walk rides at 14 m and the low wide 003 camera was already
 * reported as melting, so nothing under 60 m is trusted.
 */
export const MELT_METRES = 60;

/**
 * Metres to lift the photogrammetry so its ground agrees with ours.
 *
 * Our heights are Environment Agency LiDAR to ordnance datum. Google's are
 * photogrammetry over the ellipsoid, placed here through a geoid separation
 * of 48.6 m. Those two will not agree exactly, and every 2045 building in
 * this map stands on OUR ground — so whatever they differ by is the height
 * the scheme floats above, or sinks into, the real town.
 *
 * The tiles move, not our scheme. One number in one place, applied to the
 * photogrammetry, so nothing measured is perturbed: the plates, the places,
 * the paths and every test go on meaning exactly what they meant.
 *
 * Sign, stated because it is the kind of thing that gets pasted in backwards:
 * this is what to ADD to the tiles' height. `probe_tiles.py` reports
 * `theirs − ours` at each point, so what goes here is the NEGATIVE of its
 * median — if their ground reads 0.7 m above ours, the value is −0.7.
 *
 * UNMEASURED, and 0 until it is. The probe samples GCHQ, the campus field,
 * the brook and Princess Elizabeth Way; it will not be one number, so the
 * median goes here and the spread is a residual worth stating rather than
 * hiding. `?tileLift=-0.7` overrides it while that is being worked out.
 */
export const GROUND_OFFSET_METRES = 0;

/**
 * The melt switch has two thresholds, not one. A single one at the altitude
 * where the tiles give up means a camera hovering there flips the entire town
 * between two versions of itself every few frames — and the walk, which rides
 * at a fixed height over rolling ground, would do exactly that all the way
 * along a route.
 */
export const MELT_HYSTERESIS = 15;

const D = THREE.MathUtils.DEG2RAD;

/**
 * The frame the tiles arrive in, measured rather than assumed.
 *
 * `ReorientationPlugin` recentres the tileset — which is what keeps us out of
 * the 6,378,000-metre part of the number line, where a float has about a
 * metre of precision left — but its axis convention put the first test facing
 * the wrong way. So the plugin does the recentring and this does the axes, by
 * stepping a ten-thousandth of a degree east, north and up on the ellipsoid
 * and seeing which way the world moved.
 */
function measureBasis(tiles) {
  const at = (lat, lon, h) => {
    const v = new THREE.Vector3();
    tiles.ellipsoid.getCartographicToPosition(lat * D, lon * D, h, v);
    tiles.group.updateMatrixWorld(true);
    return v.applyMatrix4(tiles.group.matrixWorld);
  };
  const o = at(ORIGIN.lat, ORIGIN.lon, ORIGIN.geoid);
  const e = at(ORIGIN.lat, ORIGIN.lon + 1e-4, ORIGIN.geoid).sub(o).normalize();
  const n = at(ORIGIN.lat + 1e-4, ORIGIN.lon, ORIGIN.geoid).sub(o).normalize();
  const u = at(ORIGIN.lat, ORIGIN.lon, ORIGIN.geoid + 1).sub(o).normalize();
  return { o, e, n, u };
}

/**
 * The matrix that carries the tiles into OUR frame, rather than carrying our
 * camera into theirs.
 *
 * The test page did it the other way round, which is right for a test page: it
 * had one camera and nothing else. This map has a terrain, four thousand
 * buildings, a path network, a flock and a wave, all in local metres, so the
 * tiles are the thing that moves.
 *
 * Local metres are x east, y above ordnance datum, z SOUTH — so north is −z,
 * which is the sign that catches everyone including the first draft of this.
 */
export function intoLocalFrame(b, lift = 0) {
  // Columns of the basis we are mapping FROM: east, up, south.
  const m = new THREE.Matrix4().makeBasis(b.e, b.u, b.n.clone().negate());
  // Orthonormal, so the inverse is the transpose — and doing it that way
  // avoids inverting a matrix built from three measured, nearly-orthogonal
  // vectors, where a general inverse would quietly amplify the "nearly".
  m.transpose();
  const back = b.o.clone().applyMatrix4(m).negate();
  // The vertical agreement, applied to them rather than to us. Positive
  // raises the photogrammetry: the translation goes on after the rotation, so
  // this simply adds to every tile's height in our frame.
  back.y += lift;
  m.setPosition(back);
  return m;
}

/**
 * Add the layer. Returns null when there is no key, which is not a failure:
 * it is the public map.
 *
 * @param {THREE.Scene} scene
 * @param {{ camera, renderer, future }} ctx
 */
export async function addTiles(scene, { camera, renderer, future, lift }) {
  const key = globalThis.GOOGLE_TILES_KEY;
  if (!key) return null;
  const offset = Number.isFinite(lift) ? lift : GROUND_OFFSET_METRES;

  // Imported here and not at module scope, so a map with no key never fetches
  // the library at all. Phase 7 spent a day on the first load; this must not
  // put it back.
  const [{ TilesRenderer }, { ReorientationPlugin }, { GoogleCloudAuthPlugin }] =
    await Promise.all([
      import('3d-tiles-renderer/three'),
      import('3d-tiles-renderer/three/plugins'),
      import('3d-tiles-renderer/core/plugins'),
    ]);

  const tiles = new TilesRenderer();
  tiles.registerPlugin(new GoogleCloudAuthPlugin({
    apiToken: key, autoRefreshToken: true,
  }));
  tiles.registerPlugin(new ReorientationPlugin({
    lat: ORIGIN.lat * D, lon: ORIGIN.lon * D, height: ORIGIN.geoid,
    recenter: true,
  }));
  tiles.setCamera(camera);
  tiles.setResolutionFromRenderer(camera, renderer);
  tiles.errorTarget = 6;

  // The wrapper carries the measured transform. The plugin owns tiles.group's
  // own matrix, so anything we set there would be overwritten the next time it
  // re-anchored — a bug that would look like the town drifting.
  const frame = new THREE.Group();
  frame.name = 'tiles';
  frame.add(tiles.group);
  scene.add(frame);

  // Our own town, which the photogrammetry replaces. Kept as objects rather
  // than removed: the terrain is still the height source for every camera,
  // every path and every building base, and it has to go on existing for that
  // whether or not it is drawn.
  const ours = {
    terrain: scene.getObjectByName('terrain'),
    buildings: scene.getObjectByName('buildings'),
    trees: scene.getObjectByName('trees'),
  };
  const wasVisible = Object.fromEntries(
    Object.entries(ours).map(([k, o]) => [k, o ? o.visible : false]));

  let placed = false;
  let showing = false;
  let lastError = null;
  tiles.addEventListener('load-error', (e) => {
    lastError = e.error?.message ?? String(e.error);
  });

  const api = {
    /** The one renderer. Never a second: each one is a billed request. */
    tiles,
    group: frame,
    get placed() { return placed; },
    get showing() { return showing; },
    get error() { return lastError; },

    /**
     * Show the real town, or our model of it.
     *
     * Our buildings and trees go when the tiles are showing, because
     * photogrammetry already has them and two towns in one place is worse
     * than either. The terrain stays in the scene either way.
     */
    setShowing(on) {
      showing = !!on;
      frame.visible = showing;
      for (const [k, o] of Object.entries(ours)) {
        if (o) o.visible = showing ? false : wasVisible[k];
      }
      // One exception, and it is the point of the exercise: the ring's 2045
      // meadow roof stays, laid over the real building. Our own geometry over
      // a tile is allowed; changing a tile is not, and this changes nothing.
      // The buildings group has to stay visible to carry it — a hidden parent
      // hides every child however visible the child thinks it is.
      if (ours.buildings) {
        ours.buildings.visible = true;
        for (const child of ours.buildings.children) {
          child.visible = showing ? child.name === 'gchq:roof' : true;
        }
        if (!showing) ours.buildings.visible = wasVisible.buildings;
      }
      future?.setOverTiles?.(showing);
      // Our ground comes back where 2045 changes it — orchards, wetland, the
      // new streets — because tiles may not be modified, so anything the
      // scheme paints has to be drawn on top rather than into them.
      if (ours.terrain) ours.terrain.visible = showing ? true : wasVisible.terrain;
      if (future?.setGroundMasked) future.setGroundMasked(showing);
    },

    /** Metres above the ground, below which the tiles are not trusted. */
    meltsBelow: MELT_METRES,
    /** How far the photogrammetry was lifted to meet our datum. */
    lift: offset,

    /**
     * Should the tiles be on at this height above the ground? Two thresholds,
     * so a camera sitting near the line does not flip the town on and off.
     */
    wantsShowing(aboveGround) {
      return showing
        ? aboveGround >= MELT_METRES
        : aboveGround >= MELT_METRES + MELT_HYSTERESIS;
    },

    update() {
      if (!showing) return;
      // Measured once the root tileset has arrived, because before that the
      // group's matrix is not yet the one the plugin means.
      if (!placed && tiles.root) {
        frame.matrixAutoUpdate = false;
        frame.matrix.copy(intoLocalFrame(measureBasis(tiles), offset));
        frame.updateMatrixWorld(true);
        placed = true;
      }
      tiles.update();
    },

    /** Whatever is on screen right now says who it belongs to. */
    attributions() {
      const a = (tiles.getAttributions?.() ?? [])
        .map((x) => x.value).filter(Boolean);
      return [...new Set(a)].join(' · ') || 'Google';
    },
  };

  api.setShowing(true);
  return api;
}
