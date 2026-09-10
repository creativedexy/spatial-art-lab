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
function intoLocalFrame(b) {
  // Columns of the basis we are mapping FROM: east, up, south.
  const m = new THREE.Matrix4().makeBasis(b.e, b.u, b.n.clone().negate());
  // Orthonormal, so the inverse is the transpose — and doing it that way
  // avoids inverting a matrix built from three measured, nearly-orthogonal
  // vectors, where a general inverse would quietly amplify the "nearly".
  m.transpose();
  const back = b.o.clone().applyMatrix4(m).negate();
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
export async function addTiles(scene, { camera, renderer, future }) {
  const key = globalThis.GOOGLE_TILES_KEY;
  if (!key) return null;

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
      // Our ground comes back where 2045 changes it — orchards, wetland, the
      // new streets — because tiles may not be modified, so anything the
      // scheme paints has to be drawn on top rather than into them.
      if (ours.terrain) ours.terrain.visible = showing ? true : wasVisible.terrain;
      if (future?.setGroundMasked) future.setGroundMasked(showing);
    },

    /** Metres above the ground, below which the tiles are not trusted. */
    meltsBelow: MELT_METRES,

    update() {
      if (!showing) return;
      // Measured once the root tileset has arrived, because before that the
      // group's matrix is not yet the one the plugin means.
      if (!placed && tiles.root) {
        frame.matrixAutoUpdate = false;
        frame.matrix.copy(intoLocalFrame(measureBasis(tiles)));
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
