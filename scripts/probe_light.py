"""Measure the light the 2045 scheme has to stand in.

Phase 12 does not ask for a nicer sun. It asks for the sun already printed
into Google's photograph, and for our written geometry to arrive at the same
brightness and colour as that photograph. Neither answer can be taken in this
session: the tiles need a key, and the measurement needs their final pixels.

STATUS, 14 Sep 2026: the photographed-building reference has run on a real GPU.
Its masks exposed coarse distant speckle and one view dominated by GCHQ's pale
roof, so this filtered reference and the field/canopy references added here
need a new real-GPU run.

  python3 scripts/probe_light.py

Needs `experiments/002-living-map/golden-valley/key.js` on disk, holding
`window.GOOGLE_TILES_KEY`. It is gitignored; it must stay that way. Also needs
Playwright, Pillow and NumPy:

  python3 -m pip install playwright pillow numpy
  python3 -m playwright install chromium

**The sun.** Each patch is rendered from directly above, north at the top.
A ray through every sample pixel supplies the tile height and surface normal.
Raised, locally planar pixels are roofs. For each possible sun, those roofs
are projected onto the ground by `height / tan(elevation)`. The answer is the
direction whose projected footprint is darkest compared with its mirror.

That is run independently over several parts of the town and over quadrants
inside each part. Agreement is part of the measurement. If two well-resolved
parts contain incompatible suns, the tiles are a mosaic and one matching sun
does not exist; averaging them would manufacture an answer the photograph
does not have.

**The tone.** At each authored shot the probe takes Today and 2045 captures
with the same camera and pinned world clock. A third render contains only our
future buildings and models and becomes a pixel mask; the tiles are merely
hidden for that auxiliary render, never edited. A tile raycast separately
finds raised planar roofs and facades in Today, outside future footprints.
Those two building populations supply median log luminance, the P10–P90
luminance span, and neutral-pixel chromaticity.

The same frames also compare masked 2045 ground with photographed fields and
future trees with rough photographed canopy, reporting luminance, contrast and
saturation deltas. GCHQ's meadow roof uses the field population only as an
explicitly labelled proxy because no like-for-like photographed roof exists.

Run it in a visible browser on a real GPU. Settling means no tile downloads or
parses for thirty consecutive frames — not "waited a bit", which measures the
link. The report is saved beside the earlier tile probe, with diagnostic
images that must be looked at before any number is pasted into `look.js`.
"""
import argparse
import base64
import http.server
import itertools
import json
import math
import socketserver
import threading
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
GV = SITE / "golden-valley"
KEY = GV / "key.js"
VIEWPOINTS = GV / "viewpoints.json"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

# Local metres: x east, y up, z SOUTH. The camera is north-up, so image right
# is +x and image down is +z.
PATCHES = {
    "gchq": [123, 64],
    "west-campus": [-250, -150],
    "princess-elizabeth-way": [700, -180],
    "north-east-housing": [650, -650],
    "south-east-town": [650, 550],
}
PATCH_SPAN_METRES = 360
PATCH_VIEWPORT = 768
SAMPLE_PIXELS = 144
TONE_SAMPLE_WIDTH = 320
TONE_SAMPLE_HEIGHT = 180
MIN_REFERENCE_SAMPLES = 200
MIN_REFERENCE_COMPONENT_CELLS = 16
DOMINANCE_THRESHOLD = 0.5
GROUND_HEIGHT_TOLERANCE_METRES = 1.5
GROUND_PLANAR_ROUGHNESS_METRES = 1.0
GROUND_MIN_NORMAL_Y = 0.8
CANOPY_MIN_HEIGHT_METRES = 3.0
CANOPY_MAX_HEIGHT_METRES = 25.0
CANOPY_MAX_COHERENT_NEIGHBOURS = 1


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *args):
        pass


SETTLE = """async (ms) => {
  const m = window.__map;
  const t = m.tiles.tiles;
  const until = performance.now() + ms;

  // Settled means nothing left to fetch or parse, held for a moment — not
  // "waited a bit", which on a slow link measures the link.
  let quiet = 0;
  let frames = 0;
  while (performance.now() < until) {
    await new Promise((resolve) => requestAnimationFrame(resolve));
    t.update();
    frames++;
    // Nothing downloading is not the same as nothing left to download. Right
    // after a camera move, and always on a loaded machine, the renderer can
    // go thirty frames without having requested anything yet — so "quiet"
    // was satisfied before loading began, the first patch photographed an
    // empty frame, and the tone views settled on coarse parents that the tile
    // error filter then rightly rejected wholesale. Quiet only counts once the
    // root tileset exists and something is actually on screen, and never in
    // the first half-second after the camera moved.
    const started = !!t.root && t.visibleTiles.size > 0 && frames > 30;
    const busy = t.stats.downloading + t.stats.parsing;
    quiet = started && busy === 0 ? quiet + 1 : 0;
    if (quiet > 30) break;
  }
  // How far the camera is from where the framer put it. Anything that writes
  // the camera during a settle — the intro, a flight, orbit damping — shows up
  // here as metres, instead of as a measurement of somewhere else.
  const want = window.__probeCam;
  const p = m.camera.position;
  const drift = want ? Math.hypot(p.x - want.x, p.y - want.y, p.z - want.z) : 0;
  return {
    downloading: t.stats.downloading,
    parsing: t.stats.parsing,
    visible: t.visibleTiles.size,
    settled: quiet > 30,
    drift,
  };
}"""

PREPARE = """async () => {
  const THREE = await import('three');
  window.__LightProbeTHREE = THREE;
  const m = window.__map;
  m.controls.enabled = false;
  m.pinWorld?.(0);
  m.tiles.wantsShowing = () => true;
  m.tiles.setShowing(true);
  m.future.setWave(0);

  // End the opening drift before framing anything. It lerps the camera every
  // frame for fifteen seconds and is skipped only for ?clean=1, which cannot
  // be used here because clean also refuses the tiles. The first runs of this
  // probe framed their patches while the drift was still writing the camera,
  // so the pixels came from the intro and the raycast came from the patch —
  // which is how a patch labelled west-campus photographed GCHQ, and why the
  // sun would not resolve. Hold the shots too, so no flight can take it back.
  document.getElementById('intro')?.dispatchEvent(new Event('dismiss'));
  m.viewpoints?.hold?.(true);

  // Take our own interface out of the photograph before measuring it. The
  // first run measured the title card and the bottom deck along with the town:
  // the scrim behind the words is a gradient over the top of the frame, so it
  // darkens the sky end of every luminance sample and lands hardest on exactly
  // the roofs the sun search is looking for.
  //
  // `?clean=1` is the normal way to hide chrome and it CANNOT be used here: it
  // also passes null instead of a tiles layer, deliberately, so that no plate
  // ever contains Google's imagery. So hide the overlays directly — and never
  // the canvas or anything containing it, because a zero-sized canvas makes
  // every screen-space error zero and the tiles quietly stop loading.
  const canvas = m.renderer.domElement;
  const keep = new Set();
  for (let e = canvas; e; e = e.parentElement) keep.add(e);
  let hidden = 0;
  for (const el of document.querySelectorAll('body *')) {
    if (keep.has(el) || el.contains(canvas)) continue;
    const pos = getComputedStyle(el).position;
    if (pos === 'static') continue;
    el.style.setProperty('visibility', 'hidden', 'important');
    hidden++;
  }
  await new Promise((r) => requestAnimationFrame(r));
  return { hidden, canvas: [canvas.width, canvas.height] };
}"""

FRAME_PATCH = """({ x, z, span }) => {
  const m = window.__map;
  const ground = m.groundAt(x, z);
  const above = 1000;
  m.controls.enabled = false;
  m.tiles.wantsShowing = () => true;
  m.tiles.setShowing(true);
  m.future.setWave(0);

  m.camera.aspect = 1;
  m.camera.fov = 2 * Math.atan(span / (2 * above)) * 180 / Math.PI;
  m.camera.up.set(0, 0, -1); // north (-z) is the top of the image
  m.camera.position.set(x, ground + above, z);
  m.camera.lookAt(x, ground, z);
  window.__probeCam = { x, y: ground + above, z };
  m.camera.updateProjectionMatrix();
  m.camera.updateMatrixWorld(true);
  m.tiles.update();
  return { ground, above, fov: m.camera.fov };
}"""

SAMPLE_TILE_GEOMETRY = """({ n }) => {
  const THREE = window.__LightProbeTHREE;
  const m = window.__map;
  const ray = new THREE.Raycaster();
  ray.firstHitOnly = true;
  const normal = new THREE.Vector3();
  const heights = new Array(n * n).fill(null);
  const normalY = new Array(n * n).fill(null);
  const east = new Array(n * n).fill(null);
  const south = new Array(n * n).fill(null);

  for (let py = 0; py < n; py++) {
    for (let px = 0; px < n; px++) {
      // Pixel centres, in the same convention used by the canvas image.
      const ndc = new THREE.Vector2(
        ((px + 0.5) / n) * 2 - 1,
        1 - ((py + 0.5) / n) * 2
      );
      ray.setFromCamera(ndc, m.camera);
      const hits = ray.intersectObject(m.tiles.group, true);
      if (!hits.length) continue;

      const hit = hits[0];
      const i = py * n + px;
      const ground = m.groundAt(hit.point.x, hit.point.z);
      heights[i] = hit.point.y - ground;
      east[i] = hit.point.x;
      south[i] = hit.point.z;

      if (hit.face) {
        normal.copy(hit.face.normal).transformDirection(hit.object.matrixWorld);
        normalY[i] = Math.abs(normal.y);
      }
    }
  }
  return { heights, normalY, east, south };
}"""

SAMPLE_TONE_GEOMETRY = """({ width, height }) => {
  const THREE = window.__LightProbeTHREE;
  const m = window.__map;
  const tileRay = new THREE.Raycaster();
  tileRay.firstHitOnly = true;
  const footprintRay = new THREE.Raycaster();
  footprintRay.firstHitOnly = true;
  const down = new THREE.Vector3(0, -1, 0);
  const origin = new THREE.Vector3();
  const normal = new THREE.Vector3();
  const size = width * height;
  const heights = new Array(size).fill(null);
  const surfaceY = new Array(size).fill(null);
  const normalX = new Array(size).fill(null);
  const normalY = new Array(size).fill(null);
  const normalZ = new Array(size).fill(null);
  const east = new Array(size).fill(null);
  const south = new Array(size).fill(null);
  const tileGeometricError = new Array(size).fill(null);
  const futureFootprint = new Array(size).fill(false);
  const all2045Footprint = new Array(size).fill(false);

  // CPU geometry stays full-sized while the arrival wave is in the shader,
  // so a vertical ray gives the actual plan footprint at either wave end.
  // Trees are deliberately absent: this exclusion is only future buildings.
  const footprintMeshes = [];
  const future = m.scene.getObjectByName('future');
  future?.traverse((object) => {
    let inTrees = false;
    for (let p = object; p; p = p.parent) {
      if (p.name === 'future:trees') inTrees = true;
    }
    if (object.isMesh && !inTrees) footprintMeshes.push(object);
  });
  m.scene.getObjectByName('models')?.traverse((object) => {
    if (object.isMesh) footprintMeshes.push(object);
  });
  const gchqMeadowRoof = m.scene.getObjectByName('gchq:roof');

  for (let py = 0; py < height; py++) {
    for (let px = 0; px < width; px++) {
      const ndc = new THREE.Vector2(
        ((px + 0.5) / width) * 2 - 1,
        1 - ((py + 0.5) / height) * 2
      );
      tileRay.setFromCamera(ndc, m.camera);
      const hits = tileRay.intersectObject(m.tiles.group, true);
      if (!hits.length) continue;

      const hit = hits[0];
      const i = py * width + px;
      heights[i] = hit.point.y - m.groundAt(hit.point.x, hit.point.z);
      surfaceY[i] = hit.point.y;
      east[i] = hit.point.x;
      south[i] = hit.point.z;

      // 3d-tiles-renderer 0.5.2 stamps every object in a loaded tile scene
      // with this owning-tile back-reference. A raycast intersection therefore
      // maps straight back to the geometric error of that tile, in metres.
      const tile = hit.object.userData.tile;
      const geometricError = tile?.geometricError;
      if (Number.isFinite(geometricError)) {
        tileGeometricError[i] = geometricError;
      }
      if (hit.face) {
        normal.copy(hit.face.normal).transformDirection(hit.object.matrixWorld);
        normalX[i] = normal.x;
        normalY[i] = normal.y;
        normalZ[i] = normal.z;
      }

      origin.set(hit.point.x, hit.point.y + 1000, hit.point.z);
      footprintRay.set(origin, down);
      const inFutureFootprint = footprintRay
        .intersectObjects(footprintMeshes, false).length > 0;
      futureFootprint[i] = inFutureFootprint;
      all2045Footprint[i] = inFutureFootprint || !!(
        gchqMeadowRoof?.isMesh
        && footprintRay.intersectObject(gchqMeadowRoof, false).length > 0
      );
    }
  }
  return {
    heights, surfaceY, normalX, normalY, normalZ, east, south,
    tileGeometricError, futureFootprint, all2045Footprint,
  };
}"""

FRAME_VIEWPOINT = """(view) => {
  const m = window.__map;
  const lookY = m.groundAt(view.look[0], view.look[1])
              + (view.lift ?? 20);
  m.controls.enabled = false;
  m.tiles.wantsShowing = () => true;
  m.tiles.setShowing(true);
  m.camera.up.set(0, 1, 0);
  m.camera.aspect = innerWidth / innerHeight;
  m.camera.fov = view.fov;
  m.camera.position.set(...view.pos);
  m.camera.lookAt(view.look[0], lookY, view.look[1]);
  window.__probeCam = { x: view.pos[0], y: view.pos[1], z: view.pos[2] };
  m.camera.updateProjectionMatrix();
  m.camera.updateMatrixWorld(true);
  m.tiles.update();
  return true;
}"""

CAPTURE = """(wave) => {
  const m = window.__map;
  m.future.setWave(wave);
  m.tiles.update();
  m.renderer.render(m.scene, m.camera);
  return m.renderer.domElement.toDataURL('image/png');
}"""

FUTURE_MASK = """() => {
  const THREE = window.__LightProbeTHREE;
  const m = window.__map;
  const scene = m.scene;
  const renderer = m.renderer;

  const top = scene.children.map((object) => ({
    object,
    visible: object.visible,
  }));
  const futureTrees = scene.getObjectByName('future:trees');
  const futureTreesVisible = futureTrees?.visible;
  const oldBackground = scene.background;
  const oldFog = scene.fog;
  const oldOverride = scene.overrideMaterial;
  const oldToneMapping = renderer.toneMapping;
  const oldExposure = renderer.toneMappingExposure;

  // Only our proposed buildings and placed models belong in this mask.
  // The tile group is hidden, not recoloured or otherwise modified.
  for (const entry of top) {
    const name = entry.object.name;
    entry.object.visible = name === 'future' || name === 'models';
  }
  if (futureTrees) futureTrees.visible = false;

  scene.background = new THREE.Color(0x000000);
  scene.fog = null;
  scene.overrideMaterial = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    fog: false,
    toneMapped: false,
  });
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.render(scene, m.camera);
  const data = renderer.domElement.toDataURL('image/png');

  scene.overrideMaterial.dispose();
  scene.overrideMaterial = oldOverride;
  scene.background = oldBackground;
  scene.fog = oldFog;
  renderer.toneMapping = oldToneMapping;
  renderer.toneMappingExposure = oldExposure;
  for (const entry of top) entry.object.visible = entry.visible;
  if (futureTrees) futureTrees.visible = futureTreesVisible;

  renderer.render(scene, m.camera);
  return data;
}"""

SURFACE_MASKS = """() => {
  const THREE = window.__LightProbeTHREE;
  const m = window.__map;
  const scene = m.scene;
  const renderer = m.renderer;
  const terrain = scene.getObjectByName('terrain');
  const future = scene.getObjectByName('future');
  const futureTrees = scene.getObjectByName('future:trees');
  const buildings = scene.getObjectByName('buildings');
  const gchqMeadowRoof = scene.getObjectByName('gchq:roof');

  const visibility = [];
  scene.traverse((object) => visibility.push({ object, visible: object.visible }));
  const oldBackground = scene.background;
  const oldFog = scene.fog;
  const oldOverride = scene.overrideMaterial;
  const oldToneMapping = renderer.toneMapping;
  const oldExposure = renderer.toneMappingExposure;
  const white = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    fog: false,
    toneMapped: false,
  });

  const hideAllTopLevel = () => {
    for (const object of scene.children) object.visible = false;
  };
  const restoreVisibility = () => {
    for (const entry of visibility) entry.object.visible = entry.visible;
  };
  const capture = () => {
    renderer.render(scene, m.camera);
    return renderer.domElement.toDataURL('image/png');
  };

  m.future.setWave(1);
  scene.background = new THREE.Color(0x000000);
  scene.fog = null;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.toneMappingExposure = 1;

  // Keep the terrain's own shader for this pass: its discard is the exact
  // future-class != today-class mask used over tiles. Everything else is
  // absent, so blocks, placed models and future trees cannot enter the mask.
  hideAllTopLevel();
  if (terrain) terrain.visible = true;
  for (const object of scene.children) {
    if (object.isLight) object.visible = true;
  }
  scene.overrideMaterial = null;
  const ground = capture();

  // These targets have ordinary geometry, so an unlit white override gives
  // a binary screen mask without changing any tile or application material.
  hideAllTopLevel();
  if (future && futureTrees) {
    future.visible = true;
    for (const child of future.children) child.visible = child === futureTrees;
    futureTrees.visible = true;
  }
  scene.overrideMaterial = white;
  const planting = capture();

  hideAllTopLevel();
  if (buildings && gchqMeadowRoof) {
    buildings.visible = true;
    for (const child of buildings.children) {
      child.visible = child === gchqMeadowRoof;
    }
    gchqMeadowRoof.visible = true;
  }
  const meadowRoof = capture();

  white.dispose();
  scene.overrideMaterial = oldOverride;
  scene.background = oldBackground;
  scene.fog = oldFog;
  renderer.toneMapping = oldToneMapping;
  renderer.toneMappingExposure = oldExposure;
  restoreVisibility();
  renderer.render(scene, m.camera);
  return { ground, planting, meadowRoof };
}"""

READ_LOOK = """() => {
  const m = window.__map;
  const sun = m.scene.children.find((object) => object.isDirectionalLight);
  const hemi = m.scene.children.find((object) => object.isHemisphereLight);
  return {
    toneMapping: m.renderer.toneMapping,
    toneMappingExposure: m.renderer.toneMappingExposure,
    sun: sun ? {
      colour: `#${sun.color.getHexString()}`,
      intensity: sun.intensity,
      position: sun.position.toArray(),
    } : null,
    hemisphere: hemi ? {
      skyColour: `#${hemi.color.getHexString()}`,
      groundColour: `#${hemi.groundColor.getHexString()}`,
      intensity: hemi.intensity,
    } : null,
  };
}"""


def decode_data_url(value):
    encoded = value.split(",", 1)[1]
    return Image.open(BytesIO(base64.b64decode(encoded))).convert("RGB")


def slug(name):
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def srgb_to_linear(image):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float64) / 255.0
    return np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        ((rgb + 0.055) / 1.055) ** 2.4,
    )


def local_planar_mask(height, normal_y):
    finite = np.isfinite(height) & np.isfinite(normal_y)
    raised = finite & (height >= 4.0) & (normal_y >= 0.72)

    # A roof changes slowly inside itself; a canopy does not. Edges are
    # sacrificed deliberately because their uncertainty is larger than their
    # value to the shadow fit.
    rough = np.zeros_like(height)
    rough[1:-1, 1:-1] = np.maximum.reduce([
        np.abs(height[1:-1, 1:-1] - height[:-2, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[2:, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, :-2]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, 2:]),
    ])
    raised &= rough <= 1.5
    raised[:2, :] = False
    raised[-2:, :] = False
    raised[:, :2] = False
    raised[:, -2:] = False
    return raised


def projected_shadow(height, roofs, azimuth, elevation, metres_per_pixel):
    """Return a swept roof projection in image pixels.

    Azimuth is clockwise from north. Image right is east and image down is
    south. The shadow therefore travels (-sin azimuth, +cos azimuth).
    """
    yy, xx = np.nonzero(roofs)
    mask = np.zeros(roofs.shape, dtype=bool)
    if not len(xx):
        return mask

    az = math.radians(azimuth)
    el = math.radians(elevation)
    dx = -math.sin(az)
    dy = math.cos(az)
    length = height[yy, xx] / max(math.tan(el), 1e-6) / metres_per_pixel

    # Sweeping instead of marking only the tip works for both isolated roofs
    # and terraces, and makes the score less dependent on one dark pixel.
    for fraction in (0.22, 0.40, 0.58, 0.76, 0.94):
        tx = np.rint(xx + dx * length * fraction).astype(int)
        ty = np.rint(yy + dy * length * fraction).astype(int)
        valid = (
            (tx >= 0) & (tx < roofs.shape[1])
            & (ty >= 0) & (ty < roofs.shape[0])
        )
        mask[ty[valid], tx[valid]] = True
    return mask


def score_candidate(darkness, height, roofs, azimuth, elevation,
                    metres_per_pixel):
    predicted = projected_shadow(
        height, roofs, azimuth, elevation, metres_per_pixel)
    mirror = projected_shadow(
        height, roofs, (azimuth + 180) % 360, elevation, metres_per_pixel)

    # Do not score pixels on another roof/canopy. They contain photographed
    # material colour, not the ground shadow being predicted.
    clear = ~(np.isfinite(height) & (height > 2.0))
    predicted &= clear
    mirror &= clear

    count = int(predicted.sum())
    mirror_count = int(mirror.sum())
    if count < 40 or mirror_count < 40:
        return -1e9, predicted

    scale = float(np.nanstd(darkness))
    if scale < 1e-6:
        return -1e9, predicted
    score = (
        float(np.mean(darkness[predicted]))
        - float(np.mean(darkness[mirror]))
    ) / scale
    return score, predicted


def angular_distance(a, b):
    return abs((a - b + 180) % 360 - 180)


def estimate_shadow(image, height, normal_y, metres_per_pixel):
    rgb = srgb_to_linear(image)
    luminance = (
        rgb[..., 0] * 0.2126
        + rgb[..., 1] * 0.7152
        + rgb[..., 2] * 0.0722
    )
    log_y = np.log2(np.maximum(luminance, 1e-5))

    # A broad local reference removes roads, roof colours and the gentle
    # exposure gradient across the aerial photograph. Positive means darker
    # than the neighbourhood.
    blurred = np.asarray(
        Image.fromarray(
            np.uint8(np.clip((log_y + 16) / 16 * 255, 0, 255))
        ).filter(ImageFilter.GaussianBlur(radius=8)),
        dtype=np.float64,
    ) / 255 * 16 - 16
    darkness = blurred - log_y

    roofs = local_planar_mask(height, normal_y)
    roof_pixels = int(roofs.sum())
    if roof_pixels < 80:
        return {
            "status": "indeterminate",
            "reason": "too few raised planar pixels",
            "roofPixels": roof_pixels,
            "_roofs": roofs,
            "_predicted": np.zeros(roofs.shape, dtype=bool),
        }

    candidates = []
    for azimuth in range(0, 360, 4):
        for elevation in range(10, 61, 5):
            score, _ = score_candidate(
                darkness, height, roofs, azimuth, elevation,
                metres_per_pixel)
            candidates.append((score, azimuth, elevation))
    candidates.sort(reverse=True)
    _, coarse_azimuth, coarse_elevation = candidates[0]

    refined = []
    for da in range(-5, 6):
        for elevation in range(
                max(6, coarse_elevation - 6),
                min(70, coarse_elevation + 6) + 1):
            azimuth = (coarse_azimuth + da) % 360
            score, predicted = score_candidate(
                darkness, height, roofs, azimuth, elevation,
                metres_per_pixel)
            refined.append((score, azimuth, elevation, predicted))
    refined.sort(key=lambda item: item[0], reverse=True)
    best_score, best_azimuth, best_elevation, predicted = refined[0]

    mirror_score, _ = score_candidate(
        darkness, height, roofs, (best_azimuth + 180) % 360,
        best_elevation, metres_per_pixel)

    alternatives = [
        item for item in candidates
        if angular_distance(item[1], best_azimuth) > 20
        or abs(item[2] - best_elevation) > 10
    ]
    alternative_score = alternatives[0][0] if alternatives else -1e9
    peak_gap = best_score - alternative_score
    mirror_margin = best_score - mirror_score

    roof_heights = height[roofs]
    shadow_pixels = float(
        np.median(roof_heights)
        / math.tan(math.radians(best_elevation))
        / metres_per_pixel
    )
    thin = shadow_pixels < 3.0
    ambiguous = mirror_margin < 0.04
    confident = (
        best_score >= 0.08
        and peak_gap >= 0.015
        and not ambiguous
        and not thin
    )

    return {
        "status": "ok" if confident else "indeterminate",
        "azimuthDegrees": round(float(best_azimuth), 1),
        "elevationDegrees": round(float(best_elevation), 1),
        "score": round(float(best_score), 4),
        "peakGap": round(float(peak_gap), 4),
        "mirrorScore": round(float(mirror_score), 4),
        "mirrorMargin": round(float(mirror_margin), 4),
        "mirrorAmbiguous": ambiguous,
        "medianShadowPixels": round(shadow_pixels, 2),
        "thinShadow": thin,
        "roofPixels": roof_pixels,
        "_roofs": roofs,
        "_predicted": predicted,
    }


def diagnostic_image(image, roofs, predicted):
    base = image.convert("RGBA")
    overlay = np.zeros((image.height, image.width, 4), dtype=np.uint8)
    overlay[roofs] = [0, 220, 255, 150]
    overlay[predicted] = [255, 50, 30, 145]
    return Image.alpha_composite(base, Image.fromarray(overlay, "RGBA"))


def clean_estimate(estimate):
    return {
        key: value for key, value in estimate.items()
        if not key.startswith("_")
    }


def circular_mean(values):
    radians = np.radians(values)
    return float(
        math.degrees(math.atan2(
            float(np.mean(np.sin(radians))),
            float(np.mean(np.cos(radians))),
        )) % 360
    )


def circular_median(values):
    centre = circular_mean(values)
    unwrapped = [
        centre + ((value - centre + 180) % 360 - 180)
        for value in values
    ]
    return float(np.median(unwrapped) % 360)


def provisional_sun_report(patches):
    candidates = [
        (name, value["estimate"])
        for name, value in patches.items()
        if "azimuthDegrees" in value["estimate"]
        and "elevationDegrees" in value["estimate"]
    ]
    clusters = []
    for size in range(3, len(candidates) + 1):
        for cluster in itertools.combinations(candidates, size):
            azimuths = [item[1]["azimuthDegrees"] for item in cluster]
            azimuth_spread = max(
                angular_distance(a, b) for a in azimuths for b in azimuths)
            if azimuth_spread > 12:
                continue
            elevations = [item[1]["elevationDegrees"] for item in cluster]
            clusters.append((
                -size,
                azimuth_spread,
                max(elevations) - min(elevations),
                tuple(item[0] for item in cluster),
                cluster,
            ))

    clusters.sort(key=lambda item: item[:4])
    if not clusters:
        return {
            "status": "indeterminate",
            "reason": "fewer than three patches of any confidence agree "
                      "within 12 degrees azimuth",
            "patches": 0,
        }

    cluster = clusters[0][4]
    azimuths = [item[1]["azimuthDegrees"] for item in cluster]
    elevations = [item[1]["elevationDegrees"] for item in cluster]
    return {
        "status": "provisional-not-strict",
        "warning": "not the strict recommendedSun answer",
        "patches": len(cluster),
        "patchNames": [item[0] for item in cluster],
        "medianAzimuthDegrees": round(circular_median(azimuths), 1),
        "medianElevationDegrees": round(float(np.median(elevations)), 1),
        "azimuthSpreadDegrees": round(max(
            angular_distance(a, b) for a in azimuths for b in azimuths), 1),
        "elevationSpreadDegrees": round(
            float(max(elevations) - min(elevations)), 1),
    }


def consistency_report(patches):
    accepted = [
        value for value in patches.values()
        if value["estimate"]["status"] == "ok"
    ]
    mosaic_suspects = [
        name for name, value in patches.items()
        if value.get("mosaicSuspect")
    ]

    if len(accepted) < 3:
        return {
            "status": "indeterminate",
            "reason": "fewer than three independent patches resolved",
            "acceptedPatches": len(accepted),
            "mosaicSuspects": mosaic_suspects,
            "recommendedSun": None,
        }

    azimuths = [
        value["estimate"]["azimuthDegrees"] for value in accepted]
    elevations = np.array([
        value["estimate"]["elevationDegrees"] for value in accepted])
    mean_azimuth = circular_mean(azimuths)
    azimuth_spread = max(
        angular_distance(value, mean_azimuth) for value in azimuths)
    median_elevation = float(np.median(elevations))
    elevation_mad = float(np.median(np.abs(
        elevations - median_elevation)))

    consistent = (
        azimuth_spread <= 12
        and elevation_mad <= 6
        and not mosaic_suspects
    )
    return {
        "status": "consistent" if consistent else "inconsistent",
        "acceptedPatches": len(accepted),
        "azimuthSpreadDegrees": round(azimuth_spread, 1),
        "elevationMadDegrees": round(elevation_mad, 1),
        "mosaicSuspects": mosaic_suspects,
        "recommendedSun": {
            "azimuthDegrees": round(mean_azimuth, 1),
            "elevationDegrees": round(median_elevation, 1),
        } if consistent else None,
    }


def connected_components(mask):
    """Return 8-connected component coordinates, largest first."""
    seen = np.zeros(mask.shape, dtype=bool)
    components = []
    height, width = mask.shape
    for start_y, start_x in zip(*np.nonzero(mask)):
        if seen[start_y, start_x]:
            continue
        seen[start_y, start_x] = True
        stack = [(start_y, start_x)]
        component = []
        while stack:
            y, x = stack.pop()
            component.append((y, x))
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    if mask[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        stack.append((ny, nx))
        components.append(component)
    return sorted(components, key=len, reverse=True)


def photographed_building_masks(
        geometry, output_size, max_geometric_error_m):
    shape = (TONE_SAMPLE_HEIGHT, TONE_SAMPLE_WIDTH)

    def values(name):
        return np.array([
            np.nan if value is None else value
            for value in geometry[name]
        ], dtype=float).reshape(shape)

    height = values("heights")
    surface_y = values("surfaceY")
    east = values("east")
    south = values("south")
    nx = values("normalX")
    ny = values("normalY")
    nz = values("normalZ")
    geometric_error = values("tileGeometricError")
    future_footprint = np.array(
        geometry["futureFootprint"], dtype=bool).reshape(shape)

    finite = (
        np.isfinite(height) & np.isfinite(surface_y)
        & np.isfinite(east) & np.isfinite(south)
        & np.isfinite(nx) & np.isfinite(ny) & np.isfinite(nz)
    )
    raised = finite & (height >= 4.0)

    rough = np.full(shape, np.inf)
    rough[1:-1, 1:-1] = np.maximum.reduce([
        np.abs(height[1:-1, 1:-1] - height[:-2, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[2:, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, :-2]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, 2:]),
    ])
    abs_ny = np.abs(ny)
    roof = (abs_ny >= 0.72) & (rough <= 1.5)

    # Facades legitimately change height quickly down the screen, so test
    # them in their own plane instead. Canopy facets fail because adjacent
    # normals and points do not support one coherent plane.
    support = np.zeros(shape, dtype=np.uint8)
    points = np.stack([east, surface_y, south], axis=2)
    normals = np.stack([nx, ny, nz], axis=2)
    for ys, xs, yn, xn in (
        (slice(1, None), slice(None), slice(None, -1), slice(None)),
        (slice(None, -1), slice(None), slice(1, None), slice(None)),
        (slice(None), slice(1, None), slice(None), slice(None, -1)),
        (slice(None), slice(None, -1), slice(None), slice(1, None)),
    ):
        dot_normals = np.abs(np.sum(
            normals[ys, xs] * normals[yn, xn], axis=2))
        displacement = points[yn, xn] - points[ys, xs]
        residual = np.abs(np.sum(
            displacement * normals[ys, xs], axis=2))
        neighbour_ok = finite[ys, xs] & finite[yn, xn]
        support[ys, xs] += (
            neighbour_ok & (dot_normals >= 0.94) & (residual <= 0.75)
        )
    facade = (abs_ny <= 0.35) & (support >= 2)

    unfiltered = raised & (roof | facade) & ~future_footprint
    unfiltered[:2, :] = False
    unfiltered[-2:, :] = False
    unfiltered[:, :2] = False
    unfiltered[:, -2:] = False

    mapped = np.isfinite(geometric_error)
    measured_errors = geometric_error[unfiltered & mapped]
    error_filtered = (
        unfiltered & mapped & (geometric_error <= max_geometric_error_m))
    components = connected_components(error_filtered)
    kept = [
        component for component in components
        if len(component) >= MIN_REFERENCE_COMPONENT_CELLS
    ]
    filtered = np.zeros(shape, dtype=bool)
    for component in kept:
        yy, xx = zip(*component)
        filtered[yy, xx] = True

    reference_samples = int(filtered.sum())
    dominant_cells = len(kept[0]) if kept else 0
    dominant_fraction = (
        dominant_cells / reference_samples if reference_samples else 0.0)

    if measured_errors.size:
        percentiles = np.percentile(measured_errors, [10, 50, 90])
        bucket_counts = {
            f"<={bound}": int(np.sum(measured_errors <= bound))
            for bound in (2, 4, 6, 8, 12, 16)
        }
        bucket_counts[">16"] = int(np.sum(measured_errors > 16))
        geometric_error_distribution = {
            "samples": int(measured_errors.size),
            "p10": round(float(percentiles[0]), 4),
            "p50": round(float(percentiles[1]), 4),
            "p90": round(float(percentiles[2]), 4),
            "max": round(float(np.max(measured_errors)), 4),
            "cumulativeBucketCounts": bucket_counts,
        }
    else:
        geometric_error_distribution = {
            "samples": 0,
            "p10": None,
            "p50": None,
            "p90": None,
            "max": None,
            "cumulativeBucketCounts": {
                key: 0 for key in (
                    "<=2", "<=4", "<=6", "<=8", "<=12", "<=16", ">16")
            },
        }

    details = {
        "tileMapping": "hit.object.userData.tile",
        "provisionalGeometricErrorFilter": (
            "tile.geometricError <= provisionalMaxGeometricErrorMetres"),
        "provisionalMaxGeometricErrorMetres": max_geometric_error_m,
        "unfilteredBuildingGeometricErrorMetres": (
            geometric_error_distribution),
        "unfilteredGeometrySamples": int(unfiltered.sum()),
        "missingGeometricErrorSamplesRejected": int(
            (unfiltered & ~mapped).sum()),
        "overProvisionalGeometricErrorSamplesRejected": int(
            (unfiltered & mapped
             & (geometric_error > max_geometric_error_m)).sum()),
        "minimumComponentCells": MIN_REFERENCE_COMPONENT_CELLS,
        "smallComponentSamplesRejected": int(
            error_filtered.sum() - reference_samples),
        "keptComponents": len(kept),
        "referenceSamples": reference_samples,
        "dominantComponent": "component-1" if kept else None,
        "dominantComponentCells": dominant_cells,
        "dominantComponentFraction": round(dominant_fraction, 4),
        "dominated": dominant_fraction > DOMINANCE_THRESHOLD,
        "dominanceThreshold": DOMINANCE_THRESHOLD,
    }

    def resized(sample_mask):
        image = Image.fromarray(np.uint8(sample_mask) * 255).resize(
            output_size, Image.Resampling.NEAREST)
        return np.asarray(image) >= 128

    return resized(unfiltered), resized(filtered), details


def filtered_reference_mask(
        unfiltered, geometric_error, output_size, max_geometric_error_m,
        criteria):
    """Apply the building reference's metres, component and dominance gates."""
    mapped = np.isfinite(geometric_error)
    error_filtered = (
        unfiltered & mapped & (geometric_error <= max_geometric_error_m))
    components = connected_components(error_filtered)
    kept = [
        component for component in components
        if len(component) >= MIN_REFERENCE_COMPONENT_CELLS
    ]
    filtered = np.zeros(unfiltered.shape, dtype=bool)
    for component in kept:
        yy, xx = zip(*component)
        filtered[yy, xx] = True

    reference_samples = int(filtered.sum())
    dominant_cells = len(kept[0]) if kept else 0
    dominant_fraction = (
        dominant_cells / reference_samples if reference_samples else 0.0)
    details = {
        "tileMapping": "hit.object.userData.tile",
        "provisionalGeometricErrorFilter": (
            "tile.geometricError <= provisionalMaxGeometricErrorMetres"),
        "provisionalMaxGeometricErrorMetres": max_geometric_error_m,
        "criteria": criteria,
        "unfilteredGeometrySamples": int(unfiltered.sum()),
        "missingGeometricErrorSamplesRejected": int(
            (unfiltered & ~mapped).sum()),
        "overProvisionalGeometricErrorSamplesRejected": int(
            (unfiltered & mapped
             & (geometric_error > max_geometric_error_m)).sum()),
        "minimumComponentCells": MIN_REFERENCE_COMPONENT_CELLS,
        "smallComponentSamplesRejected": int(
            error_filtered.sum() - reference_samples),
        "keptComponents": len(kept),
        "referenceSamples": reference_samples,
        "dominantComponent": "component-1" if kept else None,
        "dominantComponentCells": dominant_cells,
        "dominantComponentFraction": round(dominant_fraction, 4),
        "dominated": dominant_fraction > DOMINANCE_THRESHOLD,
        "dominanceThreshold": DOMINANCE_THRESHOLD,
    }

    def resized(sample_mask):
        image = Image.fromarray(np.uint8(sample_mask) * 255).resize(
            output_size, Image.Resampling.NEAREST)
        return np.asarray(image) >= 128

    return resized(unfiltered), resized(filtered), details


def photographed_surface_masks(
        geometry, future_ground_mask_image, output_size,
        max_geometric_error_m):
    """Build like-for-like photographed field and canopy references."""
    shape = (TONE_SAMPLE_HEIGHT, TONE_SAMPLE_WIDTH)

    def values(name):
        return np.array([
            np.nan if value is None else value
            for value in geometry[name]
        ], dtype=float).reshape(shape)

    height = values("heights")
    surface_y = values("surfaceY")
    east = values("east")
    south = values("south")
    nx = values("normalX")
    ny = values("normalY")
    nz = values("normalZ")
    geometric_error = values("tileGeometricError")
    all_2045_footprint = np.array(
        geometry["all2045Footprint"], dtype=bool).reshape(shape)

    ground_sample_image = future_ground_mask_image.resize(
        (TONE_SAMPLE_WIDTH, TONE_SAMPLE_HEIGHT),
        Image.Resampling.NEAREST,
    )
    future_ground = (
        np.max(np.asarray(ground_sample_image.convert("RGB")), axis=2) >= 8)

    finite = (
        np.isfinite(height) & np.isfinite(surface_y)
        & np.isfinite(east) & np.isfinite(south)
        & np.isfinite(nx) & np.isfinite(ny) & np.isfinite(nz)
    )
    rough = np.full(shape, np.inf)
    rough[1:-1, 1:-1] = np.maximum.reduce([
        np.abs(height[1:-1, 1:-1] - height[:-2, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[2:, 1:-1]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, :-2]),
        np.abs(height[1:-1, 1:-1] - height[1:-1, 2:]),
    ])

    points = np.stack([east, surface_y, south], axis=2)
    normals = np.stack([nx, ny, nz], axis=2)
    plane_support = np.zeros(shape, dtype=np.uint8)
    normal_agreement = np.zeros(shape, dtype=np.uint8)
    finite_neighbours = np.zeros(shape, dtype=np.uint8)
    for ys, xs, yn, xn in (
        (slice(1, None), slice(None), slice(None, -1), slice(None)),
        (slice(None, -1), slice(None), slice(1, None), slice(None)),
        (slice(None), slice(1, None), slice(None), slice(None, -1)),
        (slice(None), slice(None, -1), slice(None), slice(1, None)),
    ):
        dot_normals = np.abs(np.sum(
            normals[ys, xs] * normals[yn, xn], axis=2))
        displacement = points[yn, xn] - points[ys, xs]
        residual = np.abs(np.sum(
            displacement * normals[ys, xs], axis=2))
        neighbour_ok = finite[ys, xs] & finite[yn, xn]
        finite_neighbours[ys, xs] += neighbour_ok
        normal_agreement[ys, xs] += neighbour_ok & (dot_normals >= 0.94)
        plane_support[ys, xs] += (
            neighbour_ok & (dot_normals >= 0.94) & (residual <= 0.75)
        )

    abs_ny = np.abs(ny)
    building_roof = (abs_ny >= 0.72) & (rough <= 1.5)
    building_facade = (abs_ny <= 0.35) & (plane_support >= 2)
    outside_2045 = ~all_2045_footprint
    field = (
        finite
        & (np.abs(height) <= GROUND_HEIGHT_TOLERANCE_METRES)
        & (abs_ny >= GROUND_MIN_NORMAL_Y)
        & (rough <= GROUND_PLANAR_ROUGHNESS_METRES)
        & outside_2045
        & ~future_ground
    )
    canopy = (
        finite
        & (height >= CANOPY_MIN_HEIGHT_METRES)
        & (height <= CANOPY_MAX_HEIGHT_METRES)
        & (finite_neighbours >= 2)
        & (normal_agreement <= CANOPY_MAX_COHERENT_NEIGHBOURS)
        & ~(building_roof | building_facade)
        & outside_2045
    )
    for mask in (field, canopy):
        mask[:2, :] = False
        mask[-2:, :] = False
        mask[:, :2] = False
        mask[:, -2:] = False

    field_criteria = {
        "heightFromGroundMetres": (
            f"absolute value <= {GROUND_HEIGHT_TOLERANCE_METRES}"),
        "minimumAbsoluteNormalY": GROUND_MIN_NORMAL_Y,
        "maximumCardinalHeightResidualMetres": (
            GROUND_PLANAR_ROUGHNESS_METRES),
        "exclusions": [
            "all 2045 building/model/GCHQ-meadow-roof footprints",
            "masked future-ground area",
        ],
    }
    canopy_criteria = {
        "heightFromGroundMetres": [
            CANOPY_MIN_HEIGHT_METRES, CANOPY_MAX_HEIGHT_METRES],
        "roughNormals": (
            "at most one of four finite cardinal neighbours has "
            "abs(normal dot) >= 0.94"),
        "minimumFiniteCardinalNeighbours": 2,
        "buildingPlaneRejection": (
            "reject the same locally planar roof or supported facade "
            "accepted by the building mask"),
        "exclusions": [
            "all 2045 building/model/GCHQ-meadow-roof footprints"],
    }
    field_masks = filtered_reference_mask(
        field, geometric_error, output_size, max_geometric_error_m,
        field_criteria)
    canopy_masks = filtered_reference_mask(
        canopy, geometric_error, output_size, max_geometric_error_m,
        canopy_criteria)
    return field_masks, canopy_masks


def tone_arrays(today, future, mask_image):
    today_rgb = srgb_to_linear(today)
    future_rgb = srgb_to_linear(future)
    mask = np.asarray(mask_image.convert("L")) >= 96
    mask = np.asarray(
        Image.fromarray(np.uint8(mask) * 255)
        .filter(ImageFilter.MinFilter(5))
    ) >= 128

    # Retain only pixels that visibly changed. This removes mask fragments
    # hidden behind nearer tile geometry.
    changed = np.mean(
        np.abs(future_rgb - today_rgb), axis=2) >= 0.015
    mask &= changed

    today_y = np.sum(
        today_rgb * np.array([0.2126, 0.7152, 0.0722]), axis=2)
    future_y = np.sum(
        future_rgb * np.array([0.2126, 0.7152, 0.0722]), axis=2)
    unclipped = (
        (today_y > 0.003) & (today_y < 0.95)
        & (future_y > 0.003) & (future_y < 0.95)
    )
    under_footprint = mask & unclipped
    future_mask = mask & (future_y > 0.003) & (future_y < 0.95)

    def saturation(rgb):
        high = np.max(rgb, axis=2)
        low = np.min(rgb, axis=2)
        return (high - low) / np.maximum(high, 1e-6)

    under_neutral = (
        under_footprint
        & (saturation(today_rgb) < 0.22)
        & (saturation(future_rgb) < 0.22)
    )
    future_neutral = future_mask & (saturation(future_rgb) < 0.22)
    return {
        "todayRgb": today_rgb,
        "futureRgb": future_rgb,
        "underFootprint": under_footprint,
        "underNeutral": under_neutral,
        "futureMask": future_mask,
        "futureNeutral": future_neutral,
        "todayLuminance": today_y,
        "todaySaturation": saturation(today_rgb),
        "futureSaturation": saturation(future_rgb),
    }


def luminance_statistics(values):
    p10, p50, p90 = np.percentile(values, [10, 50, 90])
    return {
        "p10Stops": round(float(p10), 4),
        "medianStops": round(float(p50), 4),
        "p90Stops": round(float(p90), 4),
        "p10P90SpanStops": round(float(p90 - p10), 4),
    }


def white_balance_statistics(reference_rgb, future_rgb, recommend=False):
    if len(reference_rgb) < 50 or len(future_rgb) < 50:
        return {
            "status": "indeterminate",
            "reason": "fewer than 50 neutral pixels in either population",
        }
    eps = 1e-6
    target_rg = np.median(np.log2(
        (reference_rgb[:, 0] + eps) / (reference_rgb[:, 1] + eps)))
    target_bg = np.median(np.log2(
        (reference_rgb[:, 2] + eps) / (reference_rgb[:, 1] + eps)))
    future_rg = np.median(np.log2(
        (future_rgb[:, 0] + eps) / (future_rgb[:, 1] + eps)))
    future_bg = np.median(np.log2(
        (future_rgb[:, 2] + eps) / (future_rgb[:, 1] + eps)))
    red_stops = float(target_rg - future_rg)
    blue_stops = float(target_bg - future_bg)
    result = {
        "redVsGreenDeltaStops": round(red_stops, 4),
        "blueVsGreenDeltaStops": round(blue_stops, 4),
    }
    if recommend:
        result["firstPassRgbGain"] = [
            round(2 ** red_stops, 4),
            1.0,
            round(2 ** blue_stops, 4),
        ]
    return result


def under_footprint_statistics(arrays):
    mask = arrays["underFootprint"]
    neutral = arrays["underNeutral"]
    if int(mask.sum()) < 100:
        return {
            "status": "indeterminate",
            "reason": "fewer than 100 visible future pixels",
            "underFootprintPixels": int(mask.sum()),
            "futureBuildingPixels": int(mask.sum()),
        }

    today_rgb = arrays["todayRgb"]
    future_rgb = arrays["futureRgb"]
    weights = np.array([0.2126, 0.7152, 0.0722])
    ty = np.sum(today_rgb * weights, axis=2)[mask]
    fy = np.sum(future_rgb * weights, axis=2)[mask]
    tl = np.log2(np.maximum(ty, 1e-6))
    fl = np.log2(np.maximum(fy, 1e-6))

    result = {
        "status": "ok",
        "reference": "Today pixels under the future-building screen mask",
        "underFootprintPixels": int(mask.sum()),
        "futureBuildingPixels": int(mask.sum()),
        "pairedNeutralPixels": int(neutral.sum()),
        "underFootprintToday": luminance_statistics(tl),
        "futureBuildings": luminance_statistics(fl),
        "medianDeltaStops": round(
            float(np.median(tl) - np.median(fl)), 4),
        "contrastDeltaStops": round(
            float((np.percentile(fl, 90) - np.percentile(fl, 10))
                  - (np.percentile(tl, 90) - np.percentile(tl, 10))), 4),
    }
    result["whiteBalanceDiagnosticNotRecommendation"] = (
        white_balance_statistics(today_rgb[neutral], future_rgb[neutral])
    )
    return result


def photographed_building_statistics(arrays, building_mask, filter_details):
    future_mask = arrays["futureMask"]
    reference_samples = filter_details["referenceSamples"]
    reference_mask = (
        building_mask
        & (arrays["todayLuminance"] > 0.003)
        & (arrays["todayLuminance"] < 0.95)
    )
    result = {
        "status": "indeterminate",
        "reference": "photographed existing buildings outside 2045 footprints",
        "photographedBuildingPixels": int(reference_mask.sum()),
        "photographedBuildingGeometrySamples": reference_samples,
        "futureBuildingPixels": int(future_mask.sum()),
        "filters": filter_details,
        "dominated": filter_details["dominated"],
    }
    if int(future_mask.sum()) < 100:
        result["reason"] = "fewer than 100 visible future pixels"
        return result
    if reference_samples < MIN_REFERENCE_SAMPLES:
        result["reason"] = (
            f"fewer than {MIN_REFERENCE_SAMPLES} independent photographed-"
            "building geometry samples"
        )
        return result
    if int(reference_mask.sum()) < 100:
        result["reason"] = "fewer than 100 unclipped photographed-building pixels"
        return result

    reference_neutral = reference_mask & (arrays["todaySaturation"] < 0.22)
    future_neutral = arrays["futureNeutral"]
    weights = np.array([0.2126, 0.7152, 0.0722])
    rl = np.log2(np.maximum(
        np.sum(arrays["todayRgb"] * weights, axis=2)[reference_mask], 1e-6))
    fl = np.log2(np.maximum(
        np.sum(arrays["futureRgb"] * weights, axis=2)[future_mask], 1e-6))
    reference_lum = luminance_statistics(rl)
    future_lum = luminance_statistics(fl)
    median_delta = float(np.median(rl) - np.median(fl))
    contrast_delta = float(
        future_lum["p10P90SpanStops"]
        - reference_lum["p10P90SpanStops"])
    result.update({
        "status": "ok",
        "photographedBuildingNeutralPixels": int(reference_neutral.sum()),
        "futureBuildingNeutralPixels": int(future_neutral.sum()),
        "photographedExistingBuildings": reference_lum,
        "futureBuildings": future_lum,
        "medianDeltaStops": round(median_delta, 4),
        "contrastDeltaStops": round(contrast_delta, 4),
        "firstPassLightScale": round(2 ** median_delta, 4),
        "contrastAdvice": {
            "action": (
                "reduce-future-contrast" if contrast_delta > 0.1
                else "increase-future-contrast" if contrast_delta < -0.1
                else "hold"
            ),
            "p10P90Stops": round(abs(contrast_delta), 4),
        },
    })

    result["whiteBalance"] = white_balance_statistics(
        arrays["todayRgb"][reference_neutral],
        arrays["futureRgb"][future_neutral],
        recommend=True,
    )
    return result


def authored_target_mask(arrays, mask_image, threshold=96):
    mask = np.asarray(mask_image.convert("L")) >= threshold
    mask = np.asarray(
        Image.fromarray(np.uint8(mask) * 255)
        .filter(ImageFilter.MinFilter(5))
    ) >= 128
    changed = np.mean(
        np.abs(arrays["futureRgb"] - arrays["todayRgb"]), axis=2) >= 0.015
    future_y = np.sum(
        arrays["futureRgb"] * np.array([0.2126, 0.7152, 0.0722]), axis=2)
    return mask & changed & (future_y > 0.003) & (future_y < 0.95)


def dilated_screen_mask(mask_image, threshold=96):
    mask = np.asarray(mask_image.convert("L")) >= threshold
    return np.asarray(
        Image.fromarray(np.uint8(mask) * 255)
        .filter(ImageFilter.MaxFilter(5))
    ) >= 128


def saturation_statistics(values):
    p10, p50, p90 = np.percentile(values, [10, 50, 90])
    return {
        "p10": round(float(p10), 4),
        "median": round(float(p50), 4),
        "p90": round(float(p90), 4),
        "p10P90Span": round(float(p90 - p10), 4),
    }


def photographed_surface_statistics(
        arrays, target_mask, reference_mask, filter_details,
        reference_name, target_name, proxy=False):
    reference_samples = filter_details["referenceSamples"]
    reference_pixels = (
        reference_mask
        & (arrays["todayLuminance"] > 0.003)
        & (arrays["todayLuminance"] < 0.95)
    )
    result = {
        "status": "indeterminate",
        "comparisonType": "proxy" if proxy else "like-for-like",
        "proxy": proxy,
        "reference": reference_name,
        "target": target_name,
        "photographedReferencePixels": int(reference_pixels.sum()),
        "photographedReferenceGeometrySamples": reference_samples,
        "authoredTargetPixels": int(target_mask.sum()),
        "filters": filter_details,
        "dominated": filter_details["dominated"],
    }
    if int(target_mask.sum()) < 100:
        result["reason"] = "fewer than 100 visible authored target pixels"
        return result
    if reference_samples < MIN_REFERENCE_SAMPLES:
        result["reason"] = (
            f"fewer than {MIN_REFERENCE_SAMPLES} independent photographed-"
            "reference geometry samples"
        )
        return result
    if int(reference_pixels.sum()) < 100:
        result["reason"] = "fewer than 100 unclipped photographed-reference pixels"
        return result

    weights = np.array([0.2126, 0.7152, 0.0722])
    reference_luminance = np.log2(np.maximum(
        np.sum(arrays["todayRgb"] * weights, axis=2)[reference_pixels],
        1e-6,
    ))
    target_luminance = np.log2(np.maximum(
        np.sum(arrays["futureRgb"] * weights, axis=2)[target_mask],
        1e-6,
    ))
    reference_lum_stats = luminance_statistics(reference_luminance)
    target_lum_stats = luminance_statistics(target_luminance)
    reference_saturation = arrays["todaySaturation"][reference_pixels]
    target_saturation = arrays["futureSaturation"][target_mask]
    median_delta = float(
        np.median(reference_luminance) - np.median(target_luminance))
    contrast_delta = float(
        target_lum_stats["p10P90SpanStops"]
        - reference_lum_stats["p10P90SpanStops"])
    saturation_delta = float(
        np.median(target_saturation) - np.median(reference_saturation))
    result.update({
        "status": "ok",
        "photographedReferenceLuminance": reference_lum_stats,
        "authoredTargetLuminance": target_lum_stats,
        "photographedReferenceSaturation": saturation_statistics(
            reference_saturation),
        "authoredTargetSaturation": saturation_statistics(target_saturation),
        "medianDeltaStops": round(median_delta, 4),
        "medianDeltaDefinition": (
            "photographed reference median minus authored target median"),
        "contrastDeltaStops": round(contrast_delta, 4),
        "contrastDeltaDefinition": (
            "authored target P10-P90 span minus photographed reference span"),
        "saturationDelta": round(saturation_delta, 4),
        "saturationDeltaDefinition": (
            "authored target median minus photographed reference median"),
        "firstPassLightScale": round(2 ** median_delta, 4),
        "contrastAdvice": {
            "action": (
                "reduce-target-contrast" if contrast_delta > 0.1
                else "increase-target-contrast" if contrast_delta < -0.1
                else "hold"
            ),
            "p10P90Stops": round(abs(contrast_delta), 4),
        },
        "saturationAdvice": {
            "action": (
                "reduce-target-saturation" if saturation_delta > 0.03
                else "increase-target-saturation" if saturation_delta < -0.03
                else "hold"
            ),
            "absoluteMedianDelta": round(abs(saturation_delta), 4),
        },
    })
    return result


def spread(values):
    return {
        "minimum": round(float(min(values)), 4),
        "maximum": round(float(max(values)), 4),
        "range": round(float(max(values) - min(values)), 4),
    }


def aggregate_photographed_building_statistics(view_statistics):
    dominated = [
        {
            "view": name,
            "dominantComponentFraction": value["filters"][
                "dominantComponentFraction"],
        }
        for name, value in view_statistics
        if value["dominated"]
    ]
    indeterminate = [
        name for name, value in view_statistics
        if value["status"] != "ok" and not value["dominated"]
    ]
    accepted = [
        (name, value) for name, value in view_statistics
        if value["status"] == "ok" and not value["dominated"]
    ]
    result = {
        "status": "indeterminate",
        "reference": "photographed existing buildings outside 2045 footprints",
        "aggregation": "median across non-dominated determinate views",
        "viewCount": len(accepted),
        "views": [name for name, _ in accepted],
        "excludedDominatedViews": dominated,
        "excludedIndeterminateViews": indeterminate,
    }
    if not accepted:
        result["reason"] = (
            "no non-dominated viewpoint supplied a determinate reference")
        return result

    median_deltas = [
        value["medianDeltaStops"] for _, value in accepted]
    contrast_deltas = [
        value["contrastDeltaStops"] for _, value in accepted]
    median_delta = float(np.median(median_deltas))
    contrast_delta = float(np.median(contrast_deltas))
    result.update({
        "status": "ok",
        "medianDeltaStops": round(median_delta, 4),
        "medianDeltaSpreadStops": spread(median_deltas),
        "contrastDeltaStops": round(contrast_delta, 4),
        "contrastDeltaSpreadStops": spread(contrast_deltas),
        "firstPassLightScale": round(2 ** median_delta, 4),
        "contrastAdvice": {
            "action": (
                "reduce-future-contrast" if contrast_delta > 0.1
                else "increase-future-contrast" if contrast_delta < -0.1
                else "hold"
            ),
            "p10P90Stops": round(abs(contrast_delta), 4),
        },
    })

    white_balances = [
        value["whiteBalance"] for _, value in accepted
        if "redVsGreenDeltaStops" in value.get("whiteBalance", {})
        and "blueVsGreenDeltaStops" in value.get("whiteBalance", {})
    ]
    if white_balances:
        red = [value["redVsGreenDeltaStops"] for value in white_balances]
        blue = [value["blueVsGreenDeltaStops"] for value in white_balances]
        median_red = float(np.median(red))
        median_blue = float(np.median(blue))
        result["whiteBalance"] = {
            "aggregation": "median across determinate accepted views",
            "viewCount": len(white_balances),
            "redVsGreenDeltaStops": round(median_red, 4),
            "redVsGreenSpreadStops": spread(red),
            "blueVsGreenDeltaStops": round(median_blue, 4),
            "blueVsGreenSpreadStops": spread(blue),
            "firstPassRgbGain": [
                round(2 ** median_red, 4),
                1.0,
                round(2 ** median_blue, 4),
            ],
        }
    else:
        result["whiteBalance"] = {
            "status": "indeterminate",
            "reason": "no accepted view supplied enough neutral pixels",
            "viewCount": 0,
        }
    return result


def aggregate_photographed_surface_statistics(
        view_statistics, reference_name, target_name, proxy=False):
    dominated = [
        {
            "view": name,
            "dominantComponentFraction": value["filters"][
                "dominantComponentFraction"],
        }
        for name, value in view_statistics
        if value["dominated"]
    ]
    indeterminate = [
        name for name, value in view_statistics
        if value["status"] != "ok" and not value["dominated"]
    ]
    accepted = [
        (name, value) for name, value in view_statistics
        if value["status"] == "ok" and not value["dominated"]
    ]
    result = {
        "status": "indeterminate",
        "comparisonType": "proxy" if proxy else "like-for-like",
        "proxy": proxy,
        "reference": reference_name,
        "target": target_name,
        "aggregation": "median across non-dominated determinate views",
        "viewCount": len(accepted),
        "views": [name for name, _ in accepted],
        "excludedDominatedViews": dominated,
        "excludedIndeterminateViews": indeterminate,
    }
    if not accepted:
        result["reason"] = (
            "no non-dominated viewpoint supplied a determinate reference")
        return result

    median_deltas = [value["medianDeltaStops"] for _, value in accepted]
    contrast_deltas = [value["contrastDeltaStops"] for _, value in accepted]
    saturation_deltas = [value["saturationDelta"] for _, value in accepted]
    median_delta = float(np.median(median_deltas))
    contrast_delta = float(np.median(contrast_deltas))
    saturation_delta = float(np.median(saturation_deltas))
    result.update({
        "status": "ok",
        "medianDeltaStops": round(median_delta, 4),
        "medianDeltaDefinition": (
            "photographed reference median minus authored target median"),
        "medianDeltaSpreadStops": spread(median_deltas),
        "contrastDeltaStops": round(contrast_delta, 4),
        "contrastDeltaDefinition": (
            "authored target P10-P90 span minus photographed reference span"),
        "contrastDeltaSpreadStops": spread(contrast_deltas),
        "saturationDelta": round(saturation_delta, 4),
        "saturationDeltaSpread": spread(saturation_deltas),
        "saturationDeltaDefinition": (
            "authored target median minus photographed reference median"),
        "firstPassLightScale": round(2 ** median_delta, 4),
        "contrastAdvice": {
            "action": (
                "reduce-target-contrast" if contrast_delta > 0.1
                else "increase-target-contrast" if contrast_delta < -0.1
                else "hold"
            ),
            "p10P90Stops": round(abs(contrast_delta), 4),
        },
        "saturationAdvice": {
            "action": (
                "reduce-target-saturation" if saturation_delta > 0.03
                else "increase-target-saturation" if saturation_delta < -0.03
                else "hold"
            ),
            "absoluteMedianDelta": round(abs(saturation_delta), 4),
        },
    })
    return result


def combine_tone_arrays(items):
    combined = {}
    for key in ("todayRgb", "futureRgb"):
        combined[key] = np.concatenate([
            item[key].reshape(-1, 3) for item in items
        ]).reshape(1, -1, 3)
    for key in (
        "underFootprint", "underNeutral", "futureMask", "futureNeutral",
        "todayLuminance", "todaySaturation", "futureSaturation",
    ):
        combined[key] = np.concatenate([
            item[key].reshape(-1) for item in items
        ]).reshape(1, -1)
    return combined


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8271)
    parser.add_argument("--settle-ms", type=int, default=30000)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--max-geometric-error-m",
        type=float,
        default=16.0,
        help=(
            "provisional maximum tile geometric error in metres for the "
            "photographed building, field and canopy references (default: 8)"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=SITE / "payload" / "light-probe.json",
    )
    args = parser.parse_args()

    if (not np.isfinite(args.max_geometric_error_m)
            or args.max_geometric_error_m <= 0):
        parser.error("--max-geometric-error-m must be finite and greater than 0")

    if not KEY.exists():
        print(
            f"no key at {KEY.relative_to(ROOT)} — this probe needs one.\n"
            "See experiments/002-living-map/tiles-test/README.md for how to "
            "write it from the keychain. Never commit it."
        )
        return 1

    from playwright.sync_api import sync_playwright

    args.out.parent.mkdir(parents=True, exist_ok=True)
    image_dir = args.out.parent / "light-probe"
    image_dir.mkdir(parents=True, exist_ok=True)

    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    report = {
        "frame": {
            "x": "east",
            "y": "up",
            "z": "south",
            "azimuth": "degrees clockwise from north",
            "elevation": "degrees above horizon",
        },
        "sunPatches": {},
        "toneViews": {},
        "pageErrors": [],
    }

    try:
        with sync_playwright() as playwright:
            launch = {
                "headless": args.headless,
                "args": ["--no-sandbox"],
            }
            if CHROMIUM.exists():
                launch["executable_path"] = str(CHROMIUM)

            browser = playwright.chromium.launch(**launch)
            page = browser.new_page(viewport={
                "width": PATCH_VIEWPORT,
                "height": PATCH_VIEWPORT,
            })
            page.on(
                "pageerror",
                lambda error: report["pageErrors"].append(str(error)),
            )
            page.goto(
                f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                wait_until="load",
                timeout=900000,
            )
            page.wait_for_function(
                "window.__terrainReady === true",
                timeout=900000,
            )
            if not page.evaluate("() => !!window.__map.tiles"):
                print("the map came up with no tiles layer — is the key valid?")
                browser.close()
                return 1

            page.evaluate(PREPARE)
            report["existingLook"] = page.evaluate(READ_LOOK)

            print("\n  the photographed sun\n")
            print(
                f"  {'patch':27} {'azimuth':>9} {'elevation':>10} "
                f"{'score':>8} {'result':>15}"
            )

            for name, (x, z) in PATCHES.items():
                page.set_viewport_size({
                    "width": PATCH_VIEWPORT,
                    "height": PATCH_VIEWPORT,
                })
                page.evaluate(FRAME_PATCH, {
                    "x": x,
                    "z": z,
                    "span": PATCH_SPAN_METRES,
                })
                settled = page.evaluate(SETTLE, args.settle_ms)
                if settled['drift'] > 1.0:
                    raise SystemExit(
                        f"camera moved {settled['drift']:.1f} m during settle; "
                        "refusing to measure somewhere other than the frame")

                image_path = image_dir / f"sun-{slug(name)}.png"
                page.locator("#app canvas").screenshot(path=str(image_path))
                image = Image.open(image_path).convert("RGB").resize(
                    (SAMPLE_PIXELS, SAMPLE_PIXELS),
                    Image.Resampling.LANCZOS,
                )

                geometry = page.evaluate(
                    SAMPLE_TILE_GEOMETRY,
                    {"n": SAMPLE_PIXELS},
                )
                height = np.array(
                    [np.nan if value is None else value
                     for value in geometry["heights"]],
                    dtype=float,
                ).reshape(SAMPLE_PIXELS, SAMPLE_PIXELS)
                normal_y = np.array(
                    [np.nan if value is None else value
                     for value in geometry["normalY"]],
                    dtype=float,
                ).reshape(SAMPLE_PIXELS, SAMPLE_PIXELS)

                estimate = estimate_shadow(
                    image,
                    height,
                    normal_y,
                    PATCH_SPAN_METRES / SAMPLE_PIXELS,
                )

                # Independent quadrants expose a mosaic boundary inside what
                # would otherwise be reported as one agreeing patch.
                quadrants = {}
                q = SAMPLE_PIXELS // 2
                for qname, ys, xs in (
                    ("north-west", slice(0, q), slice(0, q)),
                    ("north-east", slice(0, q), slice(q, SAMPLE_PIXELS)),
                    ("south-west", slice(q, SAMPLE_PIXELS), slice(0, q)),
                    ("south-east", slice(q, SAMPLE_PIXELS),
                     slice(q, SAMPLE_PIXELS)),
                ):
                    quadrant = estimate_shadow(
                        image.crop((xs.start, ys.start, xs.stop, ys.stop)),
                        height[ys, xs],
                        normal_y[ys, xs],
                        PATCH_SPAN_METRES / SAMPLE_PIXELS,
                    )
                    quadrants[qname] = clean_estimate(quadrant)

                resolved_quadrants = [
                    value for value in quadrants.values()
                    if value["status"] == "ok"
                ]
                mosaic_suspect = any(
                    angular_distance(
                        resolved_quadrants[a]["azimuthDegrees"],
                        resolved_quadrants[b]["azimuthDegrees"],
                    ) > 15
                    or abs(
                        resolved_quadrants[a]["elevationDegrees"]
                        - resolved_quadrants[b]["elevationDegrees"]
                    ) > 8
                    for a in range(len(resolved_quadrants))
                    for b in range(a + 1, len(resolved_quadrants))
                )

                diagnostic = diagnostic_image(
                    image,
                    estimate["_roofs"],
                    estimate["_predicted"],
                ).resize(
                    (PATCH_VIEWPORT, PATCH_VIEWPORT),
                    Image.Resampling.NEAREST,
                )
                diagnostic_path = (
                    image_dir / f"sun-{slug(name)}-diagnostic.png")
                diagnostic.save(diagnostic_path)

                clean = clean_estimate(estimate)
                report["sunPatches"][name] = {
                    "centre": [x, z],
                    "spanMetres": PATCH_SPAN_METRES,
                    "settled": settled,
                    "estimate": clean,
                    "quadrants": quadrants,
                    "mosaicSuspect": mosaic_suspect,
                    "image": str(image_path.relative_to(ROOT)),
                    "diagnostic": str(diagnostic_path.relative_to(ROOT)),
                }
                print(
                    f"  {name:27} "
                    f"{clean.get('azimuthDegrees', float('nan')):9.1f} "
                    f"{clean.get('elevationDegrees', float('nan')):10.1f} "
                    f"{clean.get('score', float('nan')):8.3f} "
                    f"{clean['status']:>15}"
                )

            report["sunConsistency"] = consistency_report(
                report["sunPatches"])
            report["provisionalSunEstimateNotStrict"] = (
                provisional_sun_report(report["sunPatches"])
            )
            sun_result = report["sunConsistency"]
            if sun_result["status"] == "consistent":
                sun = sun_result["recommendedSun"]
                print(
                    f"\n  -> sun azimuth {sun['azimuthDegrees']:.1f}°, "
                    f"elevation {sun['elevationDegrees']:.1f}°"
                )
            elif sun_result["status"] == "inconsistent":
                print(
                    "\n  -> NO SINGLE SUN: independently resolved parts of "
                    "the imagery disagree"
                )
            else:
                print(
                    "\n  -> sun indeterminate: not enough independent "
                    "shadow measurements resolved"
                )

            provisional = report["provisionalSunEstimateNotStrict"]
            if provisional["status"] == "provisional-not-strict":
                print(
                    "  -> PROVISIONAL ONLY (not recommendedSun): "
                    f"azimuth {provisional['medianAzimuthDegrees']:.1f}° "
                    f"(spread {provisional['azimuthSpreadDegrees']:.1f}°), "
                    f"elevation {provisional['medianElevationDegrees']:.1f}° "
                    f"(spread {provisional['elevationSpreadDegrees']:.1f}°)"
                )
            else:
                print("  -> provisional sun also indeterminate")

            print("\n  the photograph's tone against our 2045 geometry\n")
            print(
                f"  {'view / reference':42} {'median Δ':>10} "
                f"{'contrast Δ':>12} {'sat Δ':>9} "
                f"{'ref px':>9} {'2045 px':>9}"
            )

            viewpoint_data = json.loads(VIEWPOINTS.read_text())
            default_fov = viewpoint_data["defaults"].get("fov", 47)
            default_lift = viewpoint_data["defaults"].get("lift", 20)
            tone_arrays_all = []
            photographed_view_statistics = []
            ground_view_statistics = []
            planting_view_statistics = []
            meadow_roof_proxy_view_statistics = []

            page.set_viewport_size({"width": 1280, "height": 720})
            for view in viewpoint_data["viewpoints"]:
                framed = {
                    "pos": view["pos"],
                    "look": view["look"],
                    "fov": view.get("fov", default_fov),
                    "lift": view.get("lift", default_lift),
                }
                page.evaluate(FRAME_VIEWPOINT, framed)
                settled = page.evaluate(SETTLE, args.settle_ms)
                if settled['drift'] > 1.0:
                    raise SystemExit(
                        f"camera moved {settled['drift']:.1f} m during settle; "
                        "refusing to measure somewhere other than the frame")

                geometry = page.evaluate(SAMPLE_TONE_GEOMETRY, {
                    "width": TONE_SAMPLE_WIDTH,
                    "height": TONE_SAMPLE_HEIGHT,
                })
                today = decode_data_url(page.evaluate(CAPTURE, 0))
                future = decode_data_url(page.evaluate(CAPTURE, 1))
                mask = decode_data_url(page.evaluate(FUTURE_MASK))
                surface_masks = page.evaluate(SURFACE_MASKS)
                ground_target_mask_image = decode_data_url(
                    surface_masks["ground"])
                planting_target_mask_image = decode_data_url(
                    surface_masks["planting"])
                meadow_roof_target_mask_image = decode_data_url(
                    surface_masks["meadowRoof"])
                unfiltered_building_mask, building_mask, filter_details = (
                    photographed_building_masks(
                        geometry,
                        today.size,
                        args.max_geometric_error_m,
                    ))
                field_masks, canopy_masks = photographed_surface_masks(
                    geometry,
                    ground_target_mask_image,
                    today.size,
                    args.max_geometric_error_m,
                )
                (unfiltered_field_mask, field_mask,
                 field_filter_details) = field_masks
                (unfiltered_canopy_mask, canopy_mask,
                 canopy_filter_details) = canopy_masks

                stem = slug(view["id"])
                today_path = image_dir / f"tone-{stem}-today.png"
                future_path = image_dir / f"tone-{stem}-2045.png"
                mask_path = image_dir / f"tone-{stem}-mask.png"
                reference_mask_path = (
                    image_dir / f"tone-{stem}-photographed-buildings.png")
                filtered_reference_mask_path = (
                    image_dir
                    / f"tone-{stem}-photographed-buildings-filtered.png")
                ground_target_mask_path = (
                    image_dir / f"tone-{stem}-2045-ground-mask.png")
                planting_target_mask_path = (
                    image_dir / f"tone-{stem}-future-trees-mask.png")
                meadow_roof_target_mask_path = (
                    image_dir / f"tone-{stem}-gchq-meadow-roof-mask.png")
                unfiltered_field_mask_path = (
                    image_dir / f"tone-{stem}-photographed-fields.png")
                field_mask_path = (
                    image_dir / f"tone-{stem}-photographed-fields-filtered.png")
                unfiltered_canopy_mask_path = (
                    image_dir / f"tone-{stem}-photographed-canopy.png")
                canopy_mask_path = (
                    image_dir / f"tone-{stem}-photographed-canopy-filtered.png")
                today.save(today_path)
                future.save(future_path)
                mask.save(mask_path)
                Image.fromarray(
                    np.uint8(unfiltered_building_mask) * 255,
                    "L",
                ).save(reference_mask_path)
                Image.fromarray(
                    np.uint8(building_mask) * 255,
                    "L",
                ).save(filtered_reference_mask_path)
                Image.fromarray(
                    np.uint8(unfiltered_field_mask) * 255,
                    "L",
                ).save(unfiltered_field_mask_path)
                Image.fromarray(
                    np.uint8(field_mask) * 255,
                    "L",
                ).save(field_mask_path)
                Image.fromarray(
                    np.uint8(unfiltered_canopy_mask) * 255,
                    "L",
                ).save(unfiltered_canopy_mask_path)
                Image.fromarray(
                    np.uint8(canopy_mask) * 255,
                    "L",
                ).save(canopy_mask_path)

                arrays = tone_arrays(today, future, mask)
                ground_target_mask = authored_target_mask(
                    arrays, ground_target_mask_image, threshold=8)
                planting_target_mask = authored_target_mask(
                    arrays, planting_target_mask_image)
                meadow_roof_target_mask = authored_target_mask(
                    arrays, meadow_roof_target_mask_image)
                building_occluders = dilated_screen_mask(mask)
                planting_occluders = dilated_screen_mask(
                    planting_target_mask_image)
                meadow_roof_occluders = dilated_screen_mask(
                    meadow_roof_target_mask_image)
                ground_target_mask &= ~(
                    building_occluders
                    | planting_occluders
                    | meadow_roof_occluders
                )
                planting_target_mask &= ~(
                    building_occluders | meadow_roof_occluders)
                meadow_roof_target_mask &= ~(
                    building_occluders | planting_occluders)
                for target_mask, target_path in (
                    (ground_target_mask, ground_target_mask_path),
                    (planting_target_mask, planting_target_mask_path),
                    (meadow_roof_target_mask, meadow_roof_target_mask_path),
                ):
                    Image.fromarray(
                        np.uint8(target_mask) * 255,
                        "L",
                    ).save(target_path)
                under_stats = under_footprint_statistics(arrays)
                photographed_stats = photographed_building_statistics(
                    arrays, building_mask, filter_details)
                ground_stats = photographed_surface_statistics(
                    arrays,
                    ground_target_mask,
                    field_mask,
                    field_filter_details,
                    "photographed fields outside all 2045 footprints and "
                    "future-ground areas",
                    "visible masked 2045 ground, excluding blocks, placed "
                    "models and future trees",
                )
                planting_stats = photographed_surface_statistics(
                    arrays,
                    planting_target_mask,
                    canopy_mask,
                    canopy_filter_details,
                    "photographed canopy outside all 2045 footprints",
                    "future trees",
                )
                meadow_roof_proxy_stats = photographed_surface_statistics(
                    arrays,
                    meadow_roof_target_mask,
                    field_mask,
                    field_filter_details,
                    "photographed fields (PROXY; no photographed meadow-roof "
                    "counterpart exists)",
                    "GCHQ 2045 meadow roof",
                    proxy=True,
                )
                tone_arrays_all.append(arrays)
                photographed_view_statistics.append(
                    (view["id"], photographed_stats))
                ground_view_statistics.append((view["id"], ground_stats))
                planting_view_statistics.append((view["id"], planting_stats))
                meadow_roof_proxy_view_statistics.append(
                    (view["id"], meadow_roof_proxy_stats))
                report["toneViews"][view["id"]] = {
                    "settled": settled,
                    "underFootprintReference": under_stats,
                    "photographedBuildingReference": photographed_stats,
                    "groundAgainstPhotographedFields": ground_stats,
                    "futureTreesAgainstPhotographedCanopy": planting_stats,
                    "gchqMeadowRoofAgainstPhotographedFieldsProxy": (
                        meadow_roof_proxy_stats),
                    "todayImage": str(today_path.relative_to(ROOT)),
                    "futureImage": str(future_path.relative_to(ROOT)),
                    "maskImage": str(mask_path.relative_to(ROOT)),
                    "unfilteredPhotographedBuildingMaskImage": str(
                        reference_mask_path.relative_to(ROOT)),
                    "photographedBuildingMaskImage": str(
                        filtered_reference_mask_path.relative_to(ROOT)),
                    "ground2045MaskImage": str(
                        ground_target_mask_path.relative_to(ROOT)),
                    "futureTreesMaskImage": str(
                        planting_target_mask_path.relative_to(ROOT)),
                    "gchqMeadowRoofMaskImage": str(
                        meadow_roof_target_mask_path.relative_to(ROOT)),
                    "unfilteredPhotographedFieldMaskImage": str(
                        unfiltered_field_mask_path.relative_to(ROOT)),
                    "photographedFieldMaskImage": str(
                        field_mask_path.relative_to(ROOT)),
                    "unfilteredPhotographedCanopyMaskImage": str(
                        unfiltered_canopy_mask_path.relative_to(ROOT)),
                    "photographedCanopyMaskImage": str(
                        canopy_mask_path.relative_to(ROOT)),
                }
                print(
                    f"  {(view['id'] + ' / UNDER-FOOTPRINT OLD'):42} "
                    f"{under_stats.get('medianDeltaStops', float('nan')):+10.3f} "
                    f"{under_stats.get('contrastDeltaStops', float('nan')):+12.3f} "
                    f"{'n/a':>9} "
                    f"{under_stats.get('underFootprintPixels', 0):9d} "
                    f"{under_stats.get('futureBuildingPixels', 0):9d}"
                )
                print(
                    f"  {(view['id'] + ' / PHOTOGRAPHED BUILDINGS'):42} "
                    f"{photographed_stats.get('medianDeltaStops', float('nan')):+10.3f} "
                    f"{photographed_stats.get('contrastDeltaStops', float('nan')):+12.3f} "
                    f"{'n/a':>9} "
                    f"{photographed_stats.get('photographedBuildingPixels', 0):9d} "
                    f"{photographed_stats.get('futureBuildingPixels', 0):9d}"
                )
                for label, statistics in (
                    ("GROUND / PHOTOGRAPHED FIELDS", ground_stats),
                    ("PLANTING / PHOTOGRAPHED CANOPY", planting_stats),
                    ("GCHQ MEADOW ROOF / FIELD PROXY",
                     meadow_roof_proxy_stats),
                ):
                    print(
                        f"  {(view['id'] + ' / ' + label):42} "
                        f"{statistics.get('medianDeltaStops', float('nan')):+10.3f} "
                        f"{statistics.get('contrastDeltaStops', float('nan')):+12.3f} "
                        f"{statistics.get('saturationDelta', float('nan')):+9.3f} "
                        f"{statistics.get('photographedReferencePixels', 0):9d} "
                        f"{statistics.get('authoredTargetPixels', 0):9d}"
                    )
                    if statistics["status"] != "ok":
                        print(f"    indeterminate: {statistics['reason']}")
                    if statistics["dominated"]:
                        fraction = statistics["filters"][
                            "dominantComponentFraction"]
                        print(
                            "    DOMINATED: component-1 supplies "
                            f"{fraction:.1%} of reference samples; excluded "
                            "from aggregate"
                        )
                error_distribution = filter_details[
                    "unfilteredBuildingGeometricErrorMetres"]
                buckets = error_distribution["cumulativeBucketCounts"]
                print(
                    "    geometric error m (unfiltered) "
                    f"n={error_distribution['samples']} p10/p50/p90/max "
                    f"{error_distribution['p10']}/"
                    f"{error_distribution['p50']}/"
                    f"{error_distribution['p90']}/"
                    f"{error_distribution['max']}; buckets "
                    f"<=2:{buckets['<=2']} "
                    f"<=4:{buckets['<=4']} "
                    f"<=6:{buckets['<=6']} "
                    f"<=8:{buckets['<=8']} "
                    f"<=12:{buckets['<=12']} "
                    f"<=16:{buckets['<=16']} "
                    f">16:{buckets['>16']}; PROVISIONAL "
                    f"<={args.max_geometric_error_m:g} m rejects "
                    f"{filter_details['overProvisionalGeometricErrorSamplesRejected']}"
                )
                if photographed_stats["status"] != "ok":
                    print(f"    indeterminate: {photographed_stats['reason']}")
                if photographed_stats["dominated"]:
                    fraction = photographed_stats["filters"][
                        "dominantComponentFraction"]
                    print(
                        f"    DOMINATED: component-1 supplies "
                        f"{fraction:.1%} of reference samples; excluded "
                        "from aggregate"
                    )

            if tone_arrays_all:
                report["toneAggregate"] = {
                    "underFootprintReference": under_footprint_statistics(
                        combine_tone_arrays(tone_arrays_all)),
                }
            aggregate = aggregate_photographed_building_statistics(
                photographed_view_statistics)
            report.setdefault("toneAggregate", {})[
                "photographedBuildingReference"] = aggregate
            surface_aggregates = (
                (
                    "groundAgainstPhotographedFields",
                    aggregate_photographed_surface_statistics(
                        ground_view_statistics,
                        "photographed fields outside all 2045 footprints and "
                        "future-ground areas",
                        "visible masked 2045 ground, excluding blocks, placed "
                        "models and future trees",
                    ),
                ),
                (
                    "futureTreesAgainstPhotographedCanopy",
                    aggregate_photographed_surface_statistics(
                        planting_view_statistics,
                        "photographed canopy outside all 2045 footprints",
                        "future trees",
                    ),
                ),
                (
                    "gchqMeadowRoofAgainstPhotographedFieldsProxy",
                    aggregate_photographed_surface_statistics(
                        meadow_roof_proxy_view_statistics,
                        "photographed fields (PROXY; no photographed meadow-"
                        "roof counterpart exists)",
                        "GCHQ 2045 meadow roof",
                        proxy=True,
                    ),
                ),
            )
            for key, surface_aggregate in surface_aggregates:
                report.setdefault("toneAggregate", {})[key] = surface_aggregate
            if aggregate["status"] == "ok":
                delta_spread = aggregate["medianDeltaSpreadStops"]
                contrast_spread = aggregate["contrastDeltaSpreadStops"]
                print(
                    f"\n  -> PHOTOGRAPHED-BUILDING median Δ "
                    f"{aggregate['medianDeltaStops']:+.3f} stops; "
                    f"first-pass light scale "
                    f"{aggregate['firstPassLightScale']:.3f}"
                )
                print(
                    f"     median of {aggregate['viewCount']} views; "
                    f"spread {delta_spread['minimum']:+.3f} to "
                    f"{delta_spread['maximum']:+.3f} stops "
                    f"(range {delta_spread['range']:.3f})"
                )
                print(
                    f"     contrast Δ {aggregate['contrastDeltaStops']:+.3f} "
                    f"stops; spread {contrast_spread['minimum']:+.3f} to "
                    f"{contrast_spread['maximum']:+.3f} "
                    f"(range {contrast_spread['range']:.3f})"
                )
                wb = aggregate.get("whiteBalance", {})
                if "firstPassRgbGain" in wb:
                    gain = wb["firstPassRgbGain"]
                    print(
                        f"     first-pass RGB gain "
                        f"{gain[0]:.3f}, {gain[1]:.3f}, {gain[2]:.3f}"
                    )
            else:
                print("\n  -> photographed-building tone indeterminate")

            for label, surface_aggregate in (
                ("GROUND / PHOTOGRAPHED FIELDS", surface_aggregates[0][1]),
                ("PLANTING / PHOTOGRAPHED CANOPY", surface_aggregates[1][1]),
                ("GCHQ MEADOW ROOF / PHOTOGRAPHED-FIELD PROXY",
                 surface_aggregates[2][1]),
            ):
                if surface_aggregate["status"] != "ok":
                    print(f"\n  -> {label} indeterminate")
                    continue
                luminance_spread = surface_aggregate[
                    "medianDeltaSpreadStops"]
                contrast_spread = surface_aggregate[
                    "contrastDeltaSpreadStops"]
                saturation_spread = surface_aggregate[
                    "saturationDeltaSpread"]
                print(
                    f"\n  -> {label}: median Δ "
                    f"{surface_aggregate['medianDeltaStops']:+.3f} stops, "
                    f"contrast Δ "
                    f"{surface_aggregate['contrastDeltaStops']:+.3f} stops, "
                    f"saturation Δ "
                    f"{surface_aggregate['saturationDelta']:+.3f}"
                )
                print(
                    f"     median of {surface_aggregate['viewCount']} views; "
                    f"luminance spread {luminance_spread['minimum']:+.3f} to "
                    f"{luminance_spread['maximum']:+.3f}; contrast spread "
                    f"{contrast_spread['minimum']:+.3f} to "
                    f"{contrast_spread['maximum']:+.3f}; saturation spread "
                    f"{saturation_spread['minimum']:+.3f} to "
                    f"{saturation_spread['maximum']:+.3f}"
                )

            browser.close()

    finally:
        srv.shutdown()

    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nsaved {args.out.relative_to(ROOT)}")
    print(f"diagnostics are in {image_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
