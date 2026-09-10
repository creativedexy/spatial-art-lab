"""Render the structure passes a generator is conditioned on.

The bet this exists to test: an image or video model does not need our render
to be realistic, it needs it to be unambiguous. It can invent brick, slate,
tarmac wear and undergrowth. It cannot invent that GCHQ is 14.8 m tall on a
52.7 m base, or the shape of the ground under all of it — and those we have,
measured. These are the images that say so.

For each named view it writes, into experiments/002-living-map/passes/out/:

  <view>-beauty.png   the map as it renders
  <view>-depth.png    linear view depth, near white, far black
  <view>-normal.png   world-space normals
  <view>-mask.png     flat colour by category
  <view>.json         camera, field of view, depth planes in metres, and the
                      mask palette — so every pixel can be read back as a
                      number rather than guessed at

All four come from one camera at one instant, with the wind off and the birds
hidden. A pass that disagrees with the beauty frame is worse than no pass.

Usage:  python3 scripts/capture_passes.py [--views aerial,approach] [--port 8190]
"""
import argparse
import http.server
import json
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
OUT = SITE / "passes" / "out"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PASSES = ("beauty", "depth", "metric", "normal", "mask")

# The number that diagnosed Session K's failure, made into a standing check.
# A depth pass carrying a smooth ramp and 1.07 grey levels of building relief
# looks perfectly reasonable and is useless: the control net sees the ramp,
# reproduces it faithfully, and invents the town on top. So every pass is
# measured, and a thin one says so out loud.
MIN_RELIEF_LEVELS = 4.0

# Two views on purpose, because Session B's finding is that the generator's
# error tracks detail density: the wide aerial holds thousands of tiny
# buildings it cannot redraw, the low approach holds a few large masses it
# can. If the ladder works at one altitude and not the other, that is the
# answer rather than a disappointment.
VIEWS = {
    "aerial": {
        "cam": "-420,300,650", "look": "123,64", "lift": "0",
        "note": "Camera A of the doughnut descent — the wide, dense one.",
    },
    "approach": {
        "cam": "-60,92,300", "look": "123,64", "lift": "8",
        "note": "Camera B of the same descent — low, sparse, a few big masses.",
    },
    "gv-site": {
        "cam": "-482,133,-75", "look": "-592,-215", "lift": "5",
        "note": "The Golden Valley site itself, which is the one a client "
                "cares about and currently an empty field.",
    },
}


def serve(port):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(SITE), **kw)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def relief_levels(path):
    """Mean local relief in grey levels — how much of the image is *detail*
    rather than gradient. Measured the way Session K measured it: the mean
    absolute difference from a 9-pixel box blur, over the middle band where
    the buildings are."""
    from PIL import Image, ImageFilter
    import numpy as np
    im = Image.open(path).convert("L")
    w, h = im.size
    band = im.crop((0, int(h * 0.35), w, int(h * 0.85)))
    a = np.asarray(band, dtype=float)
    b = np.asarray(band.filter(ImageFilter.BoxBlur(4)), dtype=float)
    return float(np.abs(a - b).mean())


def capture(browser, url, dest, size):
    """Screenshot one pass and bring back what the page says about it — the
    fitted depth range and the mask palette are decided in the browser, so
    reading them back beats writing them down twice and hoping."""
    page = browser.new_page(viewport={"width": size[0], "height": size[1]})
    try:
        page.goto(url)
        page.wait_for_function("window.__terrainReady === true", timeout=300_000)
        meta = page.evaluate("() => window.__pass")
        page.locator("canvas").screenshot(path=str(dest))
        return meta
    finally:
        page.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", default=",".join(VIEWS))
    ap.add_argument("--size", default="1280,720")
    ap.add_argument("--port", type=int, default=8190)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    size = [int(v) for v in args.size.split(",")]
    OUT.mkdir(parents=True, exist_ok=True)
    serve(args.port)
    time.sleep(0.5)

    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        for name in args.views.split(","):
            view = VIEWS.get(name.strip())
            if view is None:
                sys.exit(f"unknown view {name!r}; known: {', '.join(VIEWS)}")
            query = "&".join(f"{k}={v}" for k, v in view.items() if k != "note")
            sidecar = {
                "view": name,
                "note": view["note"],
                "camera": {
                    "positionLocalMetres": [float(v) for v in view["cam"].split(",")],
                    "lookAtLocalMetres": [float(v) for v in view["look"].split(",")],
                    "lookLiftMetres": float(view["lift"]),
                    "fovDegrees": 48,
                },
                "sizePixels": size,
                "frame": "local metres from the box centre, x east, z south "
                         "(the same frame as gv-buildings.json)",
                "files": {},
            }
            for p in PASSES:
                url = (f"http://127.0.0.1:{args.port}/passes/index.html"
                       f"?{query}&pass={p}&size={size[0]},{size[1]}")
                dest = OUT / f"{name}-{p}.png"
                meta = capture(browser, url, dest, size)
                sidecar["files"][p] = dest.name
                if meta and meta.get("depth"):
                    sidecar["depth"] = meta["depth"]
                if meta and meta.get("maskColours"):
                    sidecar["maskColours"] = meta["maskColours"]
                note = ""
                if p in ("depth", "metric"):
                    lv = relief_levels(dest)
                    sidecar.setdefault("reliefGreyLevels", {})[p] = round(lv, 2)
                    note = f"  relief {lv:5.2f} levels"
                    if p == "depth" and lv < MIN_RELIEF_LEVELS:
                        note += "  <-- TOO FLAT to condition on"
                print(f"  ok   {dest.name}  {dest.stat().st_size // 1024:4} KB{note}")
            (OUT / f"{name}.json").write_text(json.dumps(sidecar, indent=2))
            print(f"wrote {OUT / (name + '.json')}")
        browser.close()


if __name__ == "__main__":
    main()
