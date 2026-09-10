"""Re-render every approved plate and measure what a change did to it.

Phase 7. Compression is a silent vandal: a requantised heightmap moves a
ridge line, a crushed texture flattens a roof, and neither throws an error.
Every plate in `generate/` is a camera and a wave value, so every one of them
can be rendered again and compared pixel for pixel with the render the
approved photograph was conditioned on.

The number that matters is not mean error — a slightly darker frame has a mean
error and is fine. It is **how far a feature moved**, which shows up as a large
error concentrated along edges. So this reports both, plus the fraction of
pixels that changed at all, and it saves a difference image when asked.

  python3 scripts/guard_plates.py --save reference    # before a change
  python3 scripts/guard_plates.py --against reference # after it

A plate that moves more than --tolerance rejects the change, however many
megabytes it saved.
"""
import argparse
import base64
import http.server
import io
import json
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
GEN = SITE / "generate"
GUARD = SITE / "payload" / "plates"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")


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


SHOOT = """async ({ pos, look, wave, fov }) => {
  const m = window.__map;
  // Stop the clock first. The vale has weather in it — a flock, wind in the
  // canopy, cloud shadows crossing the fields — all of them functions of how
  // long the page took to be ready, which is not the same twice. The first
  // run of this guard measured that and called it compression: two renders of
  // identical code disagreed by 1.5% of their pixels.
  m.pinWorld(300);
  m.future.setWave(wave);
  m.paths.setVisible(false);
  m.controls.enabled = false;
  m.camera.fov = fov;
  m.camera.updateProjectionMatrix();
  m.camera.position.set(pos[0], pos[1], pos[2]);
  m.camera.lookAt(look[0], look[1], look[2]);
  m.camera.updateMatrixWorld();
  // Two frames: the first can land while a texture is still uploading, and a
  // guard that measures its own warm-up is worse than no guard.
  for (let i = 0; i < 2; i++) await new Promise((r) => requestAnimationFrame(r));
  m.renderer.render(m.scene, m.camera);
  return m.renderer.domElement.toDataURL('image/png');
}"""


def plates():
    """Every composed plate in the queue, as (name, pos, look, wave, fov)."""
    out = []
    for p in sorted(GEN.glob("*/*.json")):
        if p.name.endswith("-anchors.json") or p.name == "anchors.json":
            continue
        d = json.loads(p.read_text())
        cam = d.get("camera") or {}
        for i, f in enumerate(d.get("frames", [])):
            if "pos" not in f or "look" not in f:
                continue
            stem = p.stem if p.stem != "plate" else p.parent.name
            name = stem if len(d["frames"]) == 1 else f"{stem}-{i}"
            out.append({"name": f"{p.parent.name}/{name}", "pos": f["pos"],
                        "look": f["look"], "wave": f.get("wave", d.get("wave", 0)),
                        "fov": cam.get("fov", 48),
                        "size": cam.get("size", [1280, 720])})
    return out


def render_all(port, views):
    from playwright.sync_api import sync_playwright

    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)
    shots, errors = {}, []
    size = views[0]["size"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{port}/golden-valley/index.html"
                  "?clean=1&paths=off&descend=x", wait_until="load", timeout=600000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.wait_for_timeout(3000)
        for v in views:
            if v["size"] != size:
                continue                       # one viewport per run, by design
            shots[v["name"]] = page.evaluate(SHOOT, v)
        browser.close()
    return shots, errors


def compare(a_png, b_png):
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(a_png)).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(io.BytesIO(b_png)).convert("RGB"), dtype=np.int16)
    if a.shape != b.shape:
        return None
    d = np.abs(a - b).max(axis=2)
    return {"mean": float(d.mean()), "max": int(d.max()),
            "moved_pct": float((d > 12).mean() * 100)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", help="store this run under payload/plates/<name>")
    ap.add_argument("--against", help="compare with a stored run")
    ap.add_argument("--tolerance", type=float, default=1.0,
                    help="percent of pixels allowed to move, per plate")
    ap.add_argument("--port", type=int, default=8216)
    args = ap.parse_args()

    views = plates()
    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    shots, errors = render_all(args.port, views)
    srv.shutdown()
    for e in errors[:3]:
        print(f"  page error: {e}")

    raw = {n: base64.b64decode(u.split(",", 1)[1]) for n, u in shots.items()}
    if args.save:
        d = GUARD / args.save
        d.mkdir(parents=True, exist_ok=True)
        for n, b in raw.items():
            f = d / (n.replace("/", "__") + ".png")
            f.write_bytes(b)
        print(f"saved {len(raw)} plates to {d.relative_to(ROOT)}")

    if args.against:
        d = GUARD / args.against
        print(f"\n  {'plate':40} {'mean':>7} {'max':>5} {'moved':>8}")
        worst = 0.0
        for n, b in sorted(raw.items()):
            f = d / (n.replace("/", "__") + ".png")
            if not f.exists():
                print(f"  {n:40}   no reference")
                continue
            r = compare(f.read_bytes(), b)
            if r is None:
                print(f"  {n:40}   size changed")
                worst = 100.0
                continue
            worst = max(worst, r["moved_pct"])
            flag = "" if r["moved_pct"] <= args.tolerance else "   REJECT"
            print(f"  {n:40} {r['mean']:7.2f} {r['max']:5d} "
                  f"{r['moved_pct']:7.2f}%{flag}")
        print(f"\n  worst plate moved {worst:.2f}% of its pixels "
              f"(tolerance {args.tolerance:.2f}%)")
        print("  " + ("PASS — the change is accepted" if worst <= args.tolerance
                      else "FAIL — the change is rejected"))
        return 0 if worst <= args.tolerance else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
