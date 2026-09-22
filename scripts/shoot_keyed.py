"""Shoot candidate frames on the keyed map, both ends of the switch.

Phase 12, M1. `compose_viewpoints.py` renders the keyless map under
swiftshader, which is right for plates and wrong for choosing shots now that
today is Google's photograph: the photograph is the half of the pair that
matters, and swiftshader parses about one tile every five seconds. So this
opens the real page, with the gitignored key.js, in a real window on the GPU.

A candidate is written as the thing a photographer decides: what to look at,
from which compass bearing, how far away and how steeply down. The camera
position follows. The melt gate is left alone: if a frame is too close for the
photograph to stay on, the sheet says so rather than hiding it.

  .venv/bin/python scripts/shoot_keyed.py experiments/002-living-map/generate/m1/candidates.json

It never reads or prints the key; the page loads it the way it always does.
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
GV = SITE / "golden-valley"

PREPARE = """async () => {
  const m = window.__map;
  m.controls.enabled = false;
  document.getElementById('intro')?.dispatchEvent(new Event('dismiss'));
  m.viewpoints?.hold?.(true);
  m.paths?.setVisible?.(false);
  return !!m.tiles;
}"""

FRAME = """({ look, bearing, slant, pitch, fov, lift }) => {
  const m = window.__map;
  const V = m.camera.position.constructor;
  const gy = m.groundAt(look[0], look[1]) + (lift || 0);
  const b = bearing * Math.PI / 180, p = pitch * Math.PI / 180;
  // Compass bearing the camera faces: 0 north (-z), 90 east (+x).
  const dx = Math.sin(b), dz = -Math.cos(b);
  const h = slant * Math.cos(p);
  const pos = [look[0] - dx * h, gy + slant * Math.sin(p), look[1] - dz * h];
  m.camera.fov = fov;
  m.camera.updateProjectionMatrix();
  m.camera.position.set(...pos);
  m.camera.lookAt(new V(look[0], gy, look[1]));
  m.camera.updateMatrixWorld(true);
  m.controls.target.set(look[0], gy, look[1]);
  window.__shootCam = m.camera.position.clone();
  return { pos: pos.map((v) => Math.round(v * 10) / 10),
           above: Math.round(pos[1] - m.groundAt(pos[0], pos[2])) };
}"""

SETTLE = """async ({ ms, wave }) => {
  const m = window.__map;
  m.future.setWave(wave);
  const t = m.tiles?.tiles;
  const until = performance.now() + ms;
  let quiet = 0, frames = 0;
  while (performance.now() < until) {
    await new Promise((r) => requestAnimationFrame(r));
    frames++;
    if (!t) { if (frames > 60) break; continue; }
    const started = !!t.root && t.visibleTiles.size > 0 && frames > 30;
    const busy = t.stats.downloading + t.stats.parsing;
    quiet = started && busy === 0 ? quiet + 1 : 0;
    if (quiet > 40) break;
  }
  // Let the wave finish arriving before the picture is taken.
  await new Promise((r) => setTimeout(r, 1500));
  for (let i = 0; i < 3; i++) await new Promise((r) => requestAnimationFrame(r));
  const p = m.camera.position, w = window.__shootCam;
  m.renderer.render(m.scene, m.camera);
  return {
    png: m.renderer.domElement.toDataURL('image/png'),
    showing: !!m.tiles?.showing,
    settled: quiet > 40,
    drift: w ? Math.hypot(p.x - w.x, p.y - w.y, p.z - w.z) : 0,
  };
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--port", type=int, default=8299)
    ap.add_argument("--size", default="1280,720")
    ap.add_argument("--settle-ms", type=int, default=90000)
    ap.add_argument("--only", default="")
    ap.add_argument("--keyless", action="store_true",
                    help="?clean=1: our own model only, no Google tiles. Use this for "
                         "anything that goes to a generator (tiles may never be fed to one)")
    args = ap.parse_args()
    if not args.keyless and not (GV / "key.js").is_file():
        raise SystemExit("golden-valley/key.js is required (its contents are never read here)")

    src = Path(args.candidates)
    doc = json.loads(src.read_text())
    shots = [s for s in doc["shots"]
             if not args.only or s["id"] in args.only.split(",")]
    out = src.parent
    width, height = (int(v) for v in args.size.split(","))

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(SITE), **kw)

        def log_message(self, *a):
            pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    server = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright
    results = []
    with sync_playwright() as pw:
        # A real GPU in a real window: see test_keyed_fallback.py for why.
        browser = pw.chromium.launch(headless=False, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_default_timeout(900000)
        # A shader that fails to compile draws nothing, and over the tiles that
        # is invisible: M5's keyed terrain never compiled and every frame showed
        # Google's photograph where our ground should have been. So any shader
        # error stops the shoot rather than producing plausible pictures.
        shader_errors = []
        page.on("console", lambda msg: shader_errors.append(msg.text)
                if msg.type == "error" and "Shader Error" in msg.text else None)
        query = "?clean=1" if args.keyless else ""
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html{query}",
                  wait_until="load")
        page.wait_for_function("window.__terrainReady === true")
        has_tiles = page.evaluate(PREPARE)
        if args.keyless and has_tiles:
            raise SystemExit("keyless shoot found a tiles layer: refusing (plates must not contain Google imagery)")
        if not args.keyless and not has_tiles:
            raise SystemExit("no tiles layer: is key.js present and valid?")
        if args.keyless:
            page.wait_for_timeout(8000)   # the full measured world streams in after first paint
        for s in shots:
            if shader_errors:
                raise SystemExit("shader failed to compile:\n" + shader_errors[0][-1500:])
            cam = page.evaluate(FRAME, s)
            row = {"id": s["id"], "pillar": s.get("pillar", ""), **cam,
                   "slant": s["slant"], "bearing": s["bearing"]}
            for wave, name in ((0, "today"), (1, "2045")):
                r = page.evaluate(SETTLE, {"ms": args.settle_ms, "wave": wave})
                if r["drift"] > 1:
                    raise SystemExit(f"{s['id']}: camera moved {r['drift']:.1f} m during settle")
                Image.open(io.BytesIO(base64.b64decode(r["png"].split(",", 1)[1]))) \
                    .convert("RGB").save(out / f"{s['id']}-{name}.png")
                row[name] = {"showing": r["showing"], "settled": r["settled"]}
            print(f"  {s['id']:24s} {row['above']:>4} m up  tiles "
                  f"{'keyless' if args.keyless else ('on' if row['today']['showing'] else 'OFF')}"
                  f"{'' if row['today']['settled'] else '  (not settled)'}")
            results.append(row)
        if shader_errors:
            raise SystemExit("shader failed to compile:\n" + shader_errors[0][-1500:])
        browser.close()
    server.shutdown()

    (out / "shots.json").write_text(json.dumps(results, indent=2))
    tw, th = 640, 360
    sheet = Image.new("RGB", (tw * 2, (th + 28) * len(results)), "white")
    d = ImageDraw.Draw(sheet)
    for i, row in enumerate(results):
        y = i * (th + 28)
        for j, name in enumerate(("today", "2045")):
            im = Image.open(out / f"{row['id']}-{name}.png").resize((tw, th))
            sheet.paste(im, (j * tw, y + 28))
        warn = "" if (args.keyless or row["today"]["showing"]) else "   TILES OFF: inside the melt line"
        d.text((8, y + 8), f"{row['id']}  ·  {row['pillar']}  ·  {row['slant']} m  ·  "
               f"bearing {row['bearing']}°  ·  {row['above']} m up{warn}", fill="black")
    sheet.save(out / "contact-sheet.jpg", quality=86)
    print(f"\n{len(results)} candidates -> {out / 'contact-sheet.jpg'}")


if __name__ == "__main__":
    raise SystemExit(main())
