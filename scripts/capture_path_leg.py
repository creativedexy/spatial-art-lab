"""Render the endpoints of a walkable leg, for a generator to bridge.

Phase 5. The leg is the unit: a few hundred metres of a real right of way,
walked at eye height, ~19 seconds. It is what the map already flies live, and
it is what a generated clip would stand in for — so the two ends of it are
exactly what an image-to-video model needs as `start_image` and `end_image`.

Three things this does that matter:

  It uses the map's own camera. `cameraOnLeg` is imported from walk.js, not
  reimplemented here, so a frame captured offline and the live camera the map
  hands back to cannot drift apart. Session C learned that lesson on the
  descent and it is the same lesson.

  It hides the path network. The amber ribbon is how you *choose* a route; a
  generator conditioned on it would paint a glowing strip down the middle of
  the finished footage. The plate is the world without the interface on it.

  It writes the leg beside the frames. `leg.json` carries the route, the
  distances, the camera at both ends and the duration, so whatever generates
  the clip and whatever plays it back are reading the same numbers.

Usage:
  python3 scripts/capture_path_leg.py --route cheltenham-circular-footpath \\
      --near 390808,222615 --metres 320 [--out DIR] [--port 8181]

  --near takes an easting,northing to centre the leg on; without it the leg is
  centred on the middle of the route.
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


# Runs in the page. Everything about where the camera goes comes from the
# map's own modules — this only asks, renders and hands back PNGs.
SHOOT = """async ({ routeId, near, metres }) => {
  const m = window.__map;
  const paths = await import('./paths.js');
  const walkMod = await import('./walk.js');
  const route = m.paths.routes.find((r) => r.id === routeId);
  if (!route) return { error: `no route "${routeId}"` };

  let index = Math.floor(route.pts.length / 2);
  if (near) {
    let best = 1e9;
    route.pts.forEach((p, i) => {
      const d = Math.hypot(p.x - near[0], p.z - near[1]);
      if (d < best) { best = d; index = i; }
    });
  }
  const leg = walkMod.measureLeg(paths.legAt(route, index, metres));

  // The plate has no interface on it.
  m.paths.setVisible(false);
  // And nothing else may touch the camera. The page's own frame loop calls
  // controls.update() on its own requestAnimationFrame, and the orbit limits
  // that are right for an aerial — keep sixty metres off the target, never
  // tilt within eleven degrees of level — will drag a camera standing on a
  // footpath back into the sky between placing it and rendering it.
  m.controls.enabled = false;

  const shots = [];
  for (const at of [0, leg.length]) {
    const { pos, look } = walkMod.cameraOnLeg(leg, at, m.groundAt);
    m.camera.position.copy(pos);
    m.camera.lookAt(look);
    m.camera.updateMatrixWorld();
    m.controls.target.copy(look);
    await new Promise((res) => requestAnimationFrame(res));
    m.renderer.render(m.scene, m.camera);
    shots.push({
      at,
      pos: pos.toArray().map((v) => +v.toFixed(3)),
      look: look.toArray().map((v) => +v.toFixed(3)),
      png: m.renderer.domElement.toDataURL('image/png'),
    });
  }
  m.paths.setVisible(true);

  return {
    route: { id: route.id, name: route.name, tier: route.tier,
             lengthMetres: route.lengthMetres },
    leg: { index, from: +leg.from.toFixed(2), to: +leg.to.toFixed(2),
           lengthMetres: +leg.length.toFixed(2),
           durationSeconds: +walkMod.legSeconds(leg).toFixed(2) },
    fov: m.camera.fov,
    ride: walkMod.RIDE,
    shots,
  };
}"""


def main():
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--route", default="cheltenham-circular-footpath")
    ap.add_argument("--near", help="easting,northing to centre the leg on")
    ap.add_argument("--metres", type=float, default=320)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--port", type=int, default=8181)
    args = ap.parse_args()

    meta = json.loads((SITE / "golden-valley" / "gv-meta.json").read_text())
    near = None
    if args.near:
        e, n = (float(v) for v in args.near.split(","))
        near = [e - (meta["easting"][0] + meta["widthMetres"] / 2),
                (meta["northing"][0] + meta["heightMetres"] / 2) - n]

    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": SIZE[0], "height": SIZE[1]})
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(
            f"http://127.0.0.1:{args.port}/golden-valley/index.html?clean=1&descend=x",
            wait_until="load", timeout=180000)
        page.wait_for_function("window.__terrainReady === true", timeout=300000)
        page.wait_for_timeout(3000)
        result = page.evaluate(SHOOT, {"routeId": args.route, "near": near,
                                       "metres": args.metres})
        browser.close()
    srv.shutdown()

    if result.get("error"):
        raise SystemExit(result["error"])
    for e in errors[:5]:
        print(f"  page error: {e}")

    dest = Path(args.out) / args.route
    dest.mkdir(parents=True, exist_ok=True)
    names = ["a-start", "b-end"]
    frames = []
    for name, shot in zip(names, result["shots"]):
        f = dest / f"{name}.png"
        f.write_bytes(base64.b64decode(shot["png"].split(",", 1)[1]))
        frames.append({"file": f.name, "atMetres": round(shot["at"], 2),
                       "pos": shot["pos"], "look": shot["look"]})
        print(f"  wrote {f.relative_to(ROOT)}  {f.stat().st_size / 1024:.0f} KB")

    doc = {
        "note": ("The two ends of one walkable leg, rendered from the map with "
                 "the path network hidden. Camera positions come from "
                 "cameraOnLeg in golden-valley/walk.js, which is also what the "
                 "live walk uses — so a clip generated between these frames "
                 "hands back to a camera that is already where the clip left "
                 "it. Local metres, x east, z south, origin at the box centre."),
        "route": result["route"],
        "leg": result["leg"],
        # Read back from walk.js rather than repeated here: the ride height is
        # a look decision that has already changed once, and a number copied
        # into a sidecar file is a number that goes stale in silence.
        "camera": {"fov": result["fov"], "size": list(SIZE),
                   "eyeMetres": result["ride"]["eye"],
                   "lookAheadMetres": result["ride"]["lookAhead"]},
        "frames": frames,
    }
    (dest / "leg.json").write_text(json.dumps(doc, indent=2) + "\n")
    print(f"  wrote {(dest / 'leg.json').relative_to(ROOT)}")
    print(f"\n{result['route']['name']}: {result['leg']['lengthMetres']} m, "
          f"{result['leg']['durationSeconds']} s")


if __name__ == "__main__":
    main()
