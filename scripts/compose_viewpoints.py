"""Look at the shots, rather than reasoning about coordinates.

Phase 11. The piece stops being a map you fly and becomes a set of frames you
are moved between — which makes choosing those frames a composition job, not a
maths one. So this renders every candidate in `golden-valley/viewpoints.json`
at both ends of the switch and tiles them into one contact sheet, because the
pair is the thing being judged: the same frame, once as it is and once as
proposed. A shot that is beautiful at 2045 and empty at 2026 has failed.

Two rules a candidate fails on, and both are visible rather than computable:
the edge of the box must never appear, and there must be horizon in the frame.

  python3 scripts/compose_viewpoints.py              # all of them
  python3 scripts/compose_viewpoints.py --only the-vale,the-brook

One page load for every shot. `capture_plate.py` established why: the map takes
half a minute to come up, and Playwright's own screenshot waits on a compositor
that software rendering keeps busy — so the page renders to a data URL itself
and hands the pixels back.
"""
import argparse
import base64
import http.server
import io
import json
import socketserver
import threading
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
VIEWPOINTS = SITE / "golden-valley" / "viewpoints.json"
OUT = SITE / "generate" / "phase-11"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

SHOOT = """async ({ pos, look, fov, lift, wave }) => {
  const m = window.__map;
  m.future.setWave(wave);
  m.paths.setVisible(false);
  m.controls.enabled = false;
  const V = m.camera.position.constructor;
  const target = new V(look[0], m.groundAt(look[0], look[1]) + lift, look[1]);
  m.camera.fov = fov;
  m.camera.updateProjectionMatrix();
  m.camera.position.set(pos[0], pos[1], pos[2]);
  m.camera.lookAt(target);
  m.camera.updateMatrixWorld();
  m.controls.target.copy(target);
  // Two frames: the first lets anything that watches the camera (tiles, the
  // marker layer) react, the second is the one worth keeping.
  await new Promise((r) => requestAnimationFrame(r));
  m.renderer.render(m.scene, m.camera);
  await new Promise((r) => requestAnimationFrame(r));
  m.renderer.render(m.scene, m.camera);
  return m.renderer.domElement.toDataURL('image/png');
}"""


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *a):
        pass


def decode(url):
    return Image.open(io.BytesIO(base64.b64decode(url.split(",", 1)[1]))).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8272)
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=405)
    ap.add_argument("--only", default="", help="comma-separated ids")
    ap.add_argument("--out", default="contact-sheet.png")
    args = ap.parse_args()

    spec = json.loads(VIEWPOINTS.read_text())
    d = spec["defaults"]
    shots = spec["viewpoints"]
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        shots = [v for v in shots if v["id"] in want]
    OUT.mkdir(parents=True, exist_ok=True)

    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    from playwright.sync_api import sync_playwright
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    pairs = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.set_default_timeout(300000)
        # clean=1: no interface, no splash. The composition is being judged,
        # not the chrome over it.
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html?clean=1",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        # Pin the clock, so two runs of the same candidates differ only where
        # the candidates differ — the flock and the cloud shadows are functions
        # of time and would otherwise be the loudest thing in a comparison.
        page.evaluate("() => window.__map.pinWorld(300)")
        for v in shots:
            arg = {"pos": v["pos"], "look": v["look"],
                   "fov": v.get("fov", d["fov"]), "lift": v.get("lift", d["lift"])}
            today = decode(page.evaluate(SHOOT, {**arg, "wave": 0}))
            later = decode(page.evaluate(SHOOT, {**arg, "wave": 1}))
            pairs.append((v, today, later))
            print(f"  shot {v['id']}")
        browser.close()
    srv.shutdown()

    w, h, pad, cap = args.width, args.height, 8, 26
    sheet = Image.new("RGB", (2 * w + 3 * pad, len(pairs) * (h + cap + pad) + pad),
                      (24, 28, 26))
    draw = ImageDraw.Draw(sheet)
    for i, (v, today, later) in enumerate(pairs):
        y = pad + i * (h + cap + pad)
        draw.text((pad + 2, y + 6), f"{v['id']}  —  today", fill=(210, 205, 190))
        draw.text((2 * pad + w + 2, y + 6), f"{v['id']}  —  2045", fill=(210, 205, 190))
        sheet.paste(today, (pad, y + cap))
        sheet.paste(later, (2 * pad + w, y + cap))
    out = OUT / args.out
    sheet.save(out)
    print(f"\n{len(pairs)} pairs -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
