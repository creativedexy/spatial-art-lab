"""Every shot at both ends of the switch, with the interface on.

Phase 11. `compose_viewpoints.py` renders the bare compositions so they can be
chosen; this one renders what a visitor actually sees — title card, dots,
markers, the switch — so the chrome can be judged against the frame it sits on
rather than against a blank.

  python3 scripts/shoot_shots.py --view phone
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
SPEC = SITE / "golden-valley" / "viewpoints.json"
OUT = SITE / "generate" / "phase-11"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
VIEWS = {"phone": (390, 844), "wide": (1280, 720)}


class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, *a):
        pass


class S(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8274)
    ap.add_argument("--view", default="phone", choices=list(VIEWS))
    args = ap.parse_args()

    w, h = VIEWS[args.view]
    shots = json.loads(SPEC.read_text())["viewpoints"]
    OUT.mkdir(parents=True, exist_ok=True)
    srv = S(("127.0.0.1", args.port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    frames = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(**launch)
        page = b.new_page(viewport={"width": w, "height": h})
        page.set_default_timeout(300000)
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.evaluate("() => document.getElementById('intro-go')?.click()")
        page.wait_for_function("() => document.getElementById('intro').hidden")
        page.evaluate("() => window.__map.pinWorld(300)")
        for i, v in enumerate(shots):
            page.evaluate("(i) => window.__map.viewpoints.fly(i)", i)
            page.wait_for_function(
                "(id) => { const p = window.__map.viewpoints;"
                " return !p.flying && p.current.id === id; }", arg=v["id"])
            for wave, label in ((0, "today"), (1, "2045")):
                page.evaluate("(k) => window.__map.future.setWave(k)", wave)
                page.wait_for_timeout(900)
                shot = page.screenshot(timeout=300000)
                frames.append((f"{v['id']} — {label}",
                               Image.open(io.BytesIO(shot)).convert("RGB")))
                print(f"  {v['id']} {label}")
        b.close()
    srv.shutdown()

    pad, cap = 8, 24
    cols = 2
    rows = len(shots)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad,
                              rows * (h + cap + pad) + pad), (24, 28, 26))
    draw = ImageDraw.Draw(sheet)
    for n, (label, img) in enumerate(frames):
        r, c = divmod(n, cols)
        x = pad + c * (w + pad)
        y = pad + r * (h + cap + pad)
        draw.text((x + 2, y + 5), label, fill=(210, 205, 190))
        sheet.paste(img, (x, y + cap))
    out = OUT / f"shots-{args.view}.png"
    sheet.save(out)
    print(f"\n{len(frames)} frames -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
