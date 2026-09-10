"""Measure the two numbers the tiles layer needs, on a machine that has a key.

Task 002 asks for a melt threshold and a vertical offset, and asks for them
measured rather than guessed. Neither can be taken in the cloud session: there
is no key there and there should not be one. So this is the measurement,
written to be run once by whoever holds the key.

  python3 scripts/probe_tiles.py

Needs `experiments/002-living-map/golden-valley/key.js` on disk, holding
`window.GOOGLE_TILES_KEY`. It is gitignored; it must stay that way.

**The vertical offset.** Our ground is the Environment Agency's LiDAR, to
ordnance datum. Google's is photogrammetry over the ellipsoid, placed here by
a geoid separation of 48.6 m. Those two will not agree exactly, and every 2045
building stands on ours — so the difference is the height our scheme floats
above, or sinks into, the real town. Measured by dropping a ray onto the tiles
at points we can name and comparing with `heightAtLocal`.

**The melt threshold.** Photogrammetry is a picture taken from an aeroplane.
Come close enough and it stops resolving, because nothing ever photographed
the underside of that hedge. The honest definition of "close enough" is the
altitude below which the finest tiles that exist still cannot meet the
renderer's error target — at that point you are looking at stretched texels,
however long you wait. So: settle the loading at each altitude and read the
error the visible set actually achieves.

Both numbers go in `golden-valley/tiles.js` and in the commit that carries
them, replacing the deliberately generous placeholder there.
"""
import argparse
import http.server
import json
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
KEY = SITE / "golden-valley" / "key.js"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

# Places we can name, so a disagreement can be attributed rather than averaged.
# Local metres, x east, z south, origin at the box centre.
POINTS = {
    "GCHQ, the ring": [123, 64],
    "the campus field": [-138, -190],
    "the brook corridor": [-360, 120],
    "Princess Elizabeth Way": [730, -180],
}

# Altitudes above the ground to walk down through, in metres. RIDE is 14.
LADDER = [400, 300, 220, 160, 120, 90, 70, 55, 40, 30, 20, 14]


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


SETTLE = """async (ms) => {
  const m = window.__map;
  const t = m.tiles.tiles;
  const until = performance.now() + ms;
  // Settled means nothing left to fetch or parse, held for a moment — not
  // "waited a bit", which on a slow link measures the link.
  let quiet = 0;
  while (performance.now() < until) {
    await new Promise((r) => requestAnimationFrame(r));
    const busy = t.stats.downloading + t.stats.parsing;
    quiet = busy === 0 ? quiet + 1 : 0;
    if (quiet > 30) break;
  }
  return { downloading: t.stats.downloading, parsing: t.stats.parsing };
}"""

LOOK = """({ x, z, above }) => {
  const m = window.__map;
  const y = m.groundAt(x, z) + above;
  m.controls.enabled = false;
  m.camera.position.set(x, y, z + above * 1.2);
  m.camera.lookAt(x, m.groundAt(x, z) + 4, z);
  m.camera.updateMatrixWorld();
  m.tiles.setShowing(true);
  return y;
}"""

ERROR_NOW = """() => {
  const t = window.__map.tiles.tiles;
  let worst = 0, n = 0;
  // `__error` is the screen-space error the renderer computed for each tile
  // it chose to show. If the worst of them sits above the target after the
  // loading has settled, no finer tile exists: that is the melt.
  for (const tile of t.visibleTiles) {
    if (typeof tile.__error === 'number') { worst = Math.max(worst, tile.__error); n++; }
  }
  return { worst: +worst.toFixed(2), target: t.errorTarget, visible: n };
}"""

DROP = """({ x, z }) => {
  const m = window.__map;
  const THREE = m.renderer.__three ?? null;
  const group = m.tiles.group;
  const from = new m.camera.position.constructor(x, m.groundAt(x, z) + 400, z);
  const dir = new m.camera.position.constructor(0, -1, 0);
  const ray = new (window.__Raycaster)();
  ray.set(from, dir);
  ray.firstHitOnly = true;
  const hits = ray.intersectObject(group, true);
  return hits.length ? +hits[0].point.y.toFixed(3) : null;
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8270)
    ap.add_argument("--settle-ms", type=int, default=25000)
    args = ap.parse_args()

    if not KEY.exists():
        print(f"no key at {KEY.relative_to(ROOT)} — this probe needs one.\n"
              "See experiments/002-living-map/tiles-test/README.md for how to "
              "write it from the keychain. Never commit it.")
        return 1

    from playwright.sync_api import sync_playwright
    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)

    report = {"points": {}, "ladder": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        if not page.evaluate("() => !!window.__map.tiles"):
            print("the map came up with no tiles layer — is the key valid?")
            browser.close()
            srv.shutdown()
            return 1
        # A raycaster the page can reach without us importing three twice.
        page.evaluate("""async () => {
          const THREE = await import('three');
          window.__Raycaster = THREE.Raycaster;
        }""")

        print("\n  the vertical offset — our LiDAR against their photogrammetry\n")
        print(f"  {'point':26} {'ours':>9} {'theirs':>9} {'offset':>9}")
        for name, (x, z) in POINTS.items():
            page.evaluate(LOOK, {"x": x, "z": z, "above": 300})
            page.evaluate(SETTLE, args.settle_ms)
            ours = page.evaluate("([x, z]) => window.__map.groundAt(x, z)", [x, z])
            theirs = page.evaluate(DROP, {"x": x, "z": z})
            if theirs is None:
                print(f"  {name:26} {ours:9.2f} {'—':>9} {'no hit':>9}")
                continue
            report["points"][name] = {"ours": ours, "theirs": theirs,
                                      "offset": round(theirs - ours, 3)}
            print(f"  {name:26} {ours:9.2f} {theirs:9.2f} "
                  f"{theirs - ours:+9.2f}")

        offs = [p["offset"] for p in report["points"].values()]
        if offs:
            mid = sorted(offs)[len(offs) // 2]
            print(f"\n  median offset {mid:+.2f} m "
                  f"(spread {max(offs) - min(offs):.2f} m)")
            report["medianOffset"] = mid

        print("\n  the melt threshold — where the finest tile stops being fine "
              "enough\n")
        print(f"  {'above ground':>13} {'worst error':>12} {'target':>7} "
              f"{'visible':>8}")
        x, z = POINTS["GCHQ, the ring"]
        melt = None
        for above in LADDER:
            page.evaluate(LOOK, {"x": x, "z": z, "above": above})
            page.evaluate(SETTLE, args.settle_ms)
            e = page.evaluate(ERROR_NOW)
            report["ladder"].append({"above": above, **e})
            flag = ""
            if melt is None and e["worst"] > e["target"] * 1.5:
                melt = above
                flag = "   <- melts"
            print(f"  {above:11d} m {e['worst']:12.2f} {e['target']:7.1f} "
                  f"{e['visible']:8d}{flag}")
        report["meltMetres"] = melt
        print(f"\n  melts below about {melt} m above ground"
              if melt else "\n  no melt found down to 14 m")
        for e in errors[:3]:
            print(f"  page error: {e}")
        browser.close()
    srv.shutdown()

    out = SITE / "payload" / "tiles-probe.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"\nsaved {out.relative_to(ROOT)}")
    print("Put both numbers in golden-valley/tiles.js (MELT_METRES and the "
          "offset) and quote them in the commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
