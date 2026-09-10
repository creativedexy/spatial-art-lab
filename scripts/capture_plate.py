"""Render one framed plate from the map, for a generation brief.

Phase 5. `capture_path_leg.py` renders the two ends of a leg; this renders a
single deliberately composed view, because Dex's interesting-imagery rule says
a frame has to earn its place with a named place of interest, buildings that
fill a real share of it, and visible life. An empty route between two of those
is not worth generating, so the plates worth making are the destinations.

Writes the same shape `leg.json` has, so `measure_leg_anchors.py` can project
the surveyed features into it without knowing which kind of plate it is.

Usage:
  python3 scripts/capture_plate.py --name gchq \\
      --cam 0,110,230 --look 123,64 --lift 10
"""
import argparse
import base64
import http.server
import json
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
OUT = SITE / "generate"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
SIZE = (1280, 720)


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


SHOOT = """async ({ cam, look, lift }) => {
  const m = window.__map;
  // No interface in the plate, and nothing else touching the camera: the
  // page's own frame loop calls controls.update() on its own animation frame
  // and the orbit limits will drag a composed shot back to something else.
  m.paths.setVisible(false);
  m.controls.enabled = false;
  const target = new (m.camera.position.constructor)(
    look[0], m.groundAt(look[0], look[1]) + lift, look[1]);
  m.camera.position.set(cam[0], cam[1], cam[2]);
  m.camera.lookAt(target);
  m.camera.updateMatrixWorld();
  m.controls.target.copy(target);
  await new Promise((res) => requestAnimationFrame(res));
  m.renderer.render(m.scene, m.camera);
  return {
    png: m.renderer.domElement.toDataURL('image/png'),
    fov: m.camera.fov,
    pos: m.camera.position.toArray().map((v) => +v.toFixed(3)),
    look: target.toArray().map((v) => +v.toFixed(3)),
  };
}"""


def main():
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True, help="folder to write under generate/")
    ap.add_argument("--cam", required=True, help="x,y,z in local metres")
    ap.add_argument("--look", required=True, help="x,z in local metres")
    ap.add_argument("--lift", type=float, default=0,
                    help="metres above the ground the look target sits")
    ap.add_argument("--file", default="plate.png")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--port", type=int, default=8185)
    args = ap.parse_args()

    cam = [float(v) for v in args.cam.split(",")]
    look = [float(v) for v in args.look.split(",")]

    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": SIZE[0], "height": SIZE[1]})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html"
                  "?clean=1&descend=x", wait_until="load", timeout=180000)
        page.wait_for_function("window.__terrainReady === true", timeout=300000)
        page.wait_for_timeout(3000)
        shot = page.evaluate(SHOOT, {"cam": cam, "look": look, "lift": args.lift})
        browser.close()
    srv.shutdown()
    for e in errors[:5]:
        print(f"  page error: {e}")

    dest = Path(args.out) / args.name
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / args.file
    f.write_bytes(base64.b64decode(shot["png"].split(",", 1)[1]))
    doc = {
        "note": ("One composed plate from the map, rendered with the path "
                 "network hidden. Local metres, x east, z south, origin at the "
                 "box centre. Same shape as a leg's sidecar so "
                 "measure_leg_anchors.py can read either."),
        "camera": {"fov": shot["fov"], "size": list(SIZE)},
        "frames": [{"file": f.name, "atMetres": 0,
                    "pos": shot["pos"], "look": shot["look"]}],
    }
    (dest / "plate.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"  wrote {f.relative_to(ROOT)}  {f.stat().st_size / 1024:.0f} KB")
    print(f"  wrote {(dest / 'plate.json').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
