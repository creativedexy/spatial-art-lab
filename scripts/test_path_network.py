"""Checks on the path network — the file, and the map that draws it.

Phase 5. Six things, and the third is the one that protects work already
done: an unlit network must be *pixel-identical* to no network at all, or
every descent clip rendered before Phase 5 opens a seam it did not have.

Usage:  python3 scripts/test_path_network.py [--port 8171]
"""
import argparse
import base64
import http.server
import json
import math
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
PATHS = SITE / "golden-valley" / "gv-paths.json"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *a):     # a client that hangs up mid-file is not news
        pass


def cells(points, size=12):
    return {(round(x / size), round(z / size)) for x, z in points}


def check_file():
    doc = json.loads(PATHS.read_text())
    routes = doc["routes"]
    counts = doc["counts"]

    check("counts in the file match the routes in it",
          counts["named"] == sum(1 for r in routes if r["tier"] == "named")
          and counts["strands"] == sum(1 for r in routes if r["tier"] == "strand")
          and counts["points"] == sum(len(r["points"]) for r in routes),
          f"{counts['named']} named, {counts['strands']} strands, "
          f"{counts['points']} points")

    half_x = (doc["frame"]["easting"][1] - doc["frame"]["easting"][0]) / 2
    half_z = (doc["frame"]["northing"][1] - doc["frame"]["northing"][0]) / 2
    stray = [r["id"] for r in routes
             if any(abs(x) > half_x + 3 or abs(z) > half_z + 3 for x, z in r["points"])]
    check("every point is inside the box", not stray, f"{len(stray)} strayed")

    # A route with a doubled point makes a zero-length segment, which makes a
    # zero direction, which makes a ribbon quad with no width.
    dupes = []
    for r in routes:
        for a, b in zip(r["points"], r["points"][1:]):
            if math.dist(a, b) < 1e-6:
                dupes.append(r["id"])
                break
    check("no repeated points", not dupes, f"{len(dupes)} routes with a doubled point")

    # NCN 41 and the Gloucestershire Cycle Spine are the same tarmac. If the
    # dedupe ever stops working, the map draws one of them twice as bright and
    # offers it to you twice.
    named = [r for r in routes if r["tier"] == "named"]
    overlaps = []
    for i, a in enumerate(named):
        for b in named[i + 1:]:
            ca, cb = cells(a["points"]), cells(b["points"])
            share = len(ca & cb) / max(1, min(len(ca), len(cb)))
            if share > 0.85:
                overlaps.append(f"{a['id']} ~ {b['id']} ({share:.0%})")
    check("no named route duplicates another", not overlaps, "; ".join(overlaps))
    return doc


PROBE = """async () => {
  const m = window.__map;
  const { legAt } = await import('./paths.js');
  const walkMod = await import('./walk.js');
  const out = {};
  out.routeCount = m.paths.routes.length;
  out.meshCount = m.paths.group.children.length;

  // unlit must be invisible: same picture with the group on and off
  m.paths.routes.forEach(r => {
    r.progress = 0; r.igniteAt = null; r.material.uniforms.uProgress.value = 0;
  });
  m.paths.setVisible(true);
  m.renderer.render(m.scene, m.camera);
  const lit0 = m.renderer.domElement.toDataURL('image/png');
  m.paths.setVisible(false);
  m.renderer.render(m.scene, m.camera);
  const none = m.renderer.domElement.toDataURL('image/png');
  out.unlitIdentical = lit0 === none;

  // ignition takes every route to 1 and leaves it there
  m.paths.setVisible(true);
  m.paths.igniteNow();
  out.allLit = m.paths.routes.every(r => r.progress >= 1);
  m.paths.update(1e6);
  out.staysLit = m.paths.routes.every(r => r.progress >= 1);

  // picking finds the route under a point projected from one of its own points
  const r = m.paths.routes.find(x => x.id === 'cheltenham-circular-footpath');
  const idx = Math.floor(r.pts.length / 2);
  const v = r.pts[idx].clone().project(m.camera);
  const px = (v.x * 0.5 + 0.5) * innerWidth;
  const py = (-v.y * 0.5 + 0.5) * innerHeight;
  const hit = m.paths.pick(px, py, m.camera, innerWidth, innerHeight);
  out.pickedId = hit && hit.route.id;
  out.pickedNear = hit ? Math.abs(hit.index - idx) : null;

  // a leg is the stretch around the click, clamped to the route
  const leg = legAt(r, idx, 320);
  out.legLength = leg.length;
  out.legInsideRoute = leg.from >= -0.01 && leg.to <= r.length + 0.01;

  // walking it puts the camera on the ground and gets to the far end
  m.walk.walk(leg);
  const base = performance.now();
  const drive = m.walk.update;
  m.walk.update = () => false;
  const samples = [];
  for (const t of [1800, 8000, 15000, 21000]) {
    drive.call(m.walk, base + t);
    samples.push({ t, state: m.walk.state,
                   above: +(m.camera.position.y - m.groundAt(m.camera.position.x,
                                                             m.camera.position.z)).toFixed(2) });
  }
  m.walk.update = drive;
  out.samples = samples;
  out.rideEye = walkMod.RIDE.eye;
  return out;
}"""


def check_map(port):
    from playwright.sync_api import sync_playwright

    srv = Server(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(
            f"http://127.0.0.1:{port}/golden-valley/index.html"
            "?cam=-980,300,-620&look=-592,-215&paths=on&descend=x",
            wait_until="load", timeout=180000)
        page.wait_for_function("window.__terrainReady === true", timeout=300000)
        page.wait_for_timeout(4000)
        out = page.evaluate(PROBE)
        browser.close()
    srv.shutdown()

    check("no page errors", not errors, "; ".join(errors[:3]))
    check("a mesh per route", out["routeCount"] == out["meshCount"],
          f"{out['routeCount']} routes, {out['meshCount']} meshes")
    # The claim scene.js makes: a world with the network in it is the same
    # world until something lights it, so every clip rendered before Phase 5
    # still cuts cleanly.
    check("an unlit network is invisible", out["unlitIdentical"],
          "identical frames" if out["unlitIdentical"] else "the unlit ribbons drew")
    check("ignition lights every route and stays", out["allLit"] and out["staysLit"])
    check("picking finds the route under the pointer",
          out["pickedId"] == "cheltenham-circular-footpath" and out["pickedNear"] <= 1,
          f"{out['pickedId']}, {out['pickedNear']} vertices off")
    check("a leg is the stretch asked for, inside the route",
          abs(out["legLength"] - 320) < 1 and out["legInsideRoute"],
          f"{out['legLength']:.1f} m")

    states = [s["state"] for s in out["samples"]]
    above = [s["above"] for s in out["samples"]]
    check("the walk gets to the far end",
          states[0] == "walking" and states[-1] == "arrived",
          " -> ".join(states))
    # RIDE.eye in walk.js, read from the page rather than repeated here so the
    # two cannot drift. A metre either side is slack for the terrain sampling;
    # more than that means the camera has left the route it is meant to be on.
    ride = out["rideEye"]
    check("the walk stays at its ride height above the ground",
          all(abs(a - ride) < 1.2 for a in above),
          f"ride {ride} m: " + "  ".join(f"{a:.1f}m" for a in above))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8171)
    args = ap.parse_args()

    print("gv-paths.json")
    check_file()
    print("the map")
    check_map(args.port)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("failed: " + ", ".join(failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
