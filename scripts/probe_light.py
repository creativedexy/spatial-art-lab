"""Measure the light the 2045 scheme has to stand in.

Phase 12 does not ask for a nicer sun. It asks for the sun already printed
into Google's photograph, and for our written geometry to arrive at the same
brightness and colour as that photograph. Neither answer can be taken in this
session: the tiles need a key, and the measurement needs their final pixels.

STATUS, 12 Sep 2026: written by Codex as a work package and NOT YET RUN end
to end. It parses, its CLI answers, its dependencies are present, and it
correctly defaults to a headed browser because headless software GL parses
Google's tiles at about one every five seconds. Its first real run is the next
step, and until that has happened no number it prints has been seen by anybody.

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
hidden for that auxiliary render, never edited. On the mask interior, the
probe compares median log luminance, the P10–P90 luminance span, and neutral
pixel chromaticity.

Run it in a visible browser on a real GPU. Settling means no tile downloads or
parses for thirty consecutive frames — not "waited a bit", which measures the
link. The report is saved beside the earlier tile probe, with diagnostic
images that must be looked at before any number is pasted into `look.js`.
"""
import argparse
import base64
import http.server
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
  while (performance.now() < until) {
    await new Promise((resolve) => requestAnimationFrame(resolve));
    t.update();
    const busy = t.stats.downloading + t.stats.parsing;
    quiet = busy === 0 ? quiet + 1 : 0;
    if (quiet > 30) break;
  }
  return {
    downloading: t.stats.downloading,
    parsing: t.stats.parsing,
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
  return true;
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
  return { heights, normalY, east, south };
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
    mask &= unclipped

    def saturation(rgb):
        high = np.max(rgb, axis=2)
        low = np.min(rgb, axis=2)
        return (high - low) / np.maximum(high, 1e-6)

    neutral = (
        mask
        & (saturation(today_rgb) < 0.22)
        & (saturation(future_rgb) < 0.22)
    )
    return today_rgb, future_rgb, mask, neutral


def tone_statistics(today_rgb, future_rgb, mask, neutral):
    if int(mask.sum()) < 100:
        return {
            "status": "indeterminate",
            "reason": "fewer than 100 visible future pixels",
            "pixels": int(mask.sum()),
        }

    weights = np.array([0.2126, 0.7152, 0.0722])
    ty = np.sum(today_rgb * weights, axis=2)[mask]
    fy = np.sum(future_rgb * weights, axis=2)[mask]
    tl = np.log2(np.maximum(ty, 1e-6))
    fl = np.log2(np.maximum(fy, 1e-6))

    def lum(value):
        p10, p50, p90 = np.percentile(value, [10, 50, 90])
        return {
            "p10Stops": round(float(p10), 4),
            "medianStops": round(float(p50), 4),
            "p90Stops": round(float(p90), 4),
            "p10P90SpanStops": round(float(p90 - p10), 4),
        }

    result = {
        "status": "ok",
        "pixels": int(mask.sum()),
        "neutralPixels": int(neutral.sum()),
        "tiles": lum(tl),
        "future": lum(fl),
        "medianDeltaStops": round(
            float(np.median(tl) - np.median(fl)), 4),
        "contrastDeltaStops": round(
            float((np.percentile(fl, 90) - np.percentile(fl, 10))
                  - (np.percentile(tl, 90) - np.percentile(tl, 10))), 4),
    }

    if int(neutral.sum()) >= 50:
        trgb = today_rgb[neutral]
        frgb = future_rgb[neutral]
        eps = 1e-6
        target_rg = np.median(np.log2(
            (trgb[:, 0] + eps) / (trgb[:, 1] + eps)))
        target_bg = np.median(np.log2(
            (trgb[:, 2] + eps) / (trgb[:, 1] + eps)))
        future_rg = np.median(np.log2(
            (frgb[:, 0] + eps) / (frgb[:, 1] + eps)))
        future_bg = np.median(np.log2(
            (frgb[:, 2] + eps) / (frgb[:, 1] + eps)))
        red_stops = float(target_rg - future_rg)
        blue_stops = float(target_bg - future_bg)
        result["whiteBalance"] = {
            "redVsGreenDeltaStops": round(red_stops, 4),
            "blueVsGreenDeltaStops": round(blue_stops, 4),
            "firstPassRgbGain": [
                round(2 ** red_stops, 4),
                1.0,
                round(2 ** blue_stops, 4),
            ],
        }
    else:
        result["whiteBalance"] = {
            "status": "indeterminate",
            "reason": "fewer than 50 paired neutral pixels",
        }

    result["firstPassLightScale"] = round(
        2 ** result["medianDeltaStops"], 4)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8271)
    parser.add_argument("--settle-ms", type=int, default=30000)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--out",
        type=Path,
        default=SITE / "payload" / "light-probe.json",
    )
    args = parser.parse_args()

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

            print("\n  the photograph's tone against our 2045 geometry\n")
            print(
                f"  {'view':27} {'median Δ':>10} {'contrast Δ':>12} "
                f"{'pixels':>9}"
            )

            viewpoint_data = json.loads(VIEWPOINTS.read_text())
            default_fov = viewpoint_data["defaults"].get("fov", 47)
            default_lift = viewpoint_data["defaults"].get("lift", 20)
            tone_arrays_all = []

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

                today = decode_data_url(page.evaluate(CAPTURE, 0))
                future = decode_data_url(page.evaluate(CAPTURE, 1))
                mask = decode_data_url(page.evaluate(FUTURE_MASK))

                stem = slug(view["id"])
                today_path = image_dir / f"tone-{stem}-today.png"
                future_path = image_dir / f"tone-{stem}-2045.png"
                mask_path = image_dir / f"tone-{stem}-mask.png"
                today.save(today_path)
                future.save(future_path)
                mask.save(mask_path)

                arrays = tone_arrays(today, future, mask)
                stats = tone_statistics(*arrays)
                if stats["status"] == "ok":
                    tone_arrays_all.append(arrays)
                report["toneViews"][view["id"]] = {
                    "settled": settled,
                    "statistics": stats,
                    "todayImage": str(today_path.relative_to(ROOT)),
                    "futureImage": str(future_path.relative_to(ROOT)),
                    "maskImage": str(mask_path.relative_to(ROOT)),
                }
                print(
                    f"  {view['id']:27} "
                    f"{stats.get('medianDeltaStops', float('nan')):+10.3f} "
                    f"{stats.get('contrastDeltaStops', float('nan')):+12.3f} "
                    f"{stats.get('pixels', 0):9d}"
                )

            if tone_arrays_all:
                today_rgb = np.concatenate([
                    item[0].reshape(-1, 3) for item in tone_arrays_all])
                future_rgb = np.concatenate([
                    item[1].reshape(-1, 3) for item in tone_arrays_all])
                masks = np.concatenate([
                    item[2].reshape(-1) for item in tone_arrays_all])
                neutrals = np.concatenate([
                    item[3].reshape(-1) for item in tone_arrays_all])
                report["toneAggregate"] = tone_statistics(
                    today_rgb.reshape(1, -1, 3),
                    future_rgb.reshape(1, -1, 3),
                    masks.reshape(1, -1),
                    neutrals.reshape(1, -1),
                )
                aggregate = report["toneAggregate"]
                print(
                    f"\n  -> median Δ "
                    f"{aggregate['medianDeltaStops']:+.3f} stops; "
                    f"first-pass light scale "
                    f"{aggregate['firstPassLightScale']:.3f}"
                )
                print(
                    f"     contrast Δ "
                    f"{aggregate['contrastDeltaStops']:+.3f} stops"
                )
                wb = aggregate.get("whiteBalance", {})
                if "firstPassRgbGain" in wb:
                    gain = wb["firstPassRgbGain"]
                    print(
                        f"     first-pass RGB gain "
                        f"{gain[0]:.3f}, {gain[1]:.3f}, {gain[2]:.3f}"
                    )
            else:
                report["toneAggregate"] = {
                    "status": "indeterminate",
                    "reason": "no viewpoint supplied enough future pixels",
                }
                print("\n  -> tone indeterminate")

            browser.close()

    finally:
        srv.shutdown()

    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nsaved {args.out.relative_to(ROOT)}")
    print(f"diagnostics are in {image_dir.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
