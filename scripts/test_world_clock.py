"""Prove the animated world is a pure function of its clock.

Phase 4 put weather, wind and a flock of birds into the map. All of it is
lovely and all of it is a threat to the one thing this project has measured
from the start: the descent hands a pre-rendered clip to a live canvas and
the join is compared pixel by pixel. Anything driven by `performance.now()`
would put the clip's last frame and the live canvas at different moments of
the same afternoon, and no fade hides a cloud shadow in the wrong place.

So the world has one clock, and the contract is that time — not elapsed time,
not frame count, not how you got there — decides what is drawn. This checks
exactly that, and it is the test that has to keep passing if anything else
moving is ever added:

  1. the same instant renders identically, even after time has run backwards
  2. a different instant renders differently (or nothing is moving at all)
  3. the flock rewinds rather than drifting — the hard case, because it is a
     simulation and simulations remember

Usage:  python3 scripts/test_world_clock.py [--port 8189]
"""
import argparse
import hashlib
import http.server
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

# Pin the clock through the module the page itself imported: ES modules are
# cached per resolved URL, so this is the same instance the map is driving,
# not a second copy with its own state.
PIN = """
async (t) => {
  const m = await import('/golden-valley/scene.js');
  m.pinWorld(t);
  await new Promise(requestAnimationFrame);
  await new Promise(requestAnimationFrame);
}
"""


def serve(port):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(SITE), **kw)

        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8189)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    serve(args.port)
    url = (f"http://127.0.0.1:{args.port}/golden-valley/index.html"
           "?clean&cam=-260,180,470&look=123,64")
    failures = []

    def check(name, ok, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    with sync_playwright() as pw:
        launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
        if CHROMIUM.exists():
            launch["executable_path"] = str(CHROMIUM)
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 640, "height": 400})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_function("window.__terrainReady === true", timeout=240_000)
        page.set_default_timeout(180_000)

        def shot(t):
            page.evaluate(PIN, t)
            return hashlib.sha256(page.locator("canvas").screenshot()).hexdigest()[:16]

        first = shot(2.0)
        forward = shot(2.5)
        rewound = shot(0.25)
        again = shot(2.0)

        check("the same instant renders identically after a rewind",
              again == first, f"{first} vs {again}")
        check("a different instant renders differently",
              forward != first, f"{first} vs {forward}")
        check("running time backwards actually changes the frame",
              rewound not in (first, forward), rewound)
        check("no page errors", not errors, "; ".join(errors[:3]))
        browser.close()

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
