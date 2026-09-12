"""The shots, and the fact that you cannot leave them.

Phase 11. The note that started it was "it's still a 3d map that we can move
around — I don't really want this", and the fix is not a smaller map, it is
taking the camera back. So what is checked here is mostly *absence*: no pan,
no dolly, no way to swing a composed frame into the void, and no line of text
telling anyone to drag.

The one positive claim is that the shots are shots — that moving between them
actually moves, lands where the file says, and hands back a frame with the
right places offered in it. The compositions themselves are not checked here
and cannot be: a shot is judged by looking, which is what
`scripts/compose_viewpoints.py` and generate/phase-11/ are for.

Every wait is a poll. Headless software rendering runs this scene at under a
frame a second and a fixed sleep would be measuring swiftshader.

  python3 scripts/test_viewpoints.py
"""
import argparse
import http.server
import json
import math
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
SPEC = SITE / "golden-valley" / "viewpoints.json"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PHONE = {"width": 390, "height": 844}

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


WHERE = """() => {
  const m = window.__map;
  const v = m.viewpoints;
  const c = m.controls;
  return {
    at: v.at,
    id: v.current.id,
    flying: v.flying,
    pos: m.camera.position.toArray().map((n) => +n.toFixed(2)),
    target: c.target.toArray().map((n) => +n.toFixed(2)),
    radius: +m.camera.position.distanceTo(c.target).toFixed(2),
    minD: +c.minDistance.toFixed(2), maxD: +c.maxDistance.toFixed(2),
    pan: c.enablePan, zoom: c.enableZoom,
    azimuth: [c.minAzimuthAngle, c.maxAzimuthAngle],
    polar: [c.minPolarAngle, c.maxPolarAngle],
    name: document.getElementById('shot-name').textContent.trim(),
    says: document.getElementById('shot-says').textContent.trim(),
    dots: [...document.querySelectorAll('#shot-dots .dot')]
      .map((d) => d.classList.contains('on')),
    // Both layers: the photographs and the clipped descents are two systems
    // to us and one thing to a viewer, so they are counted as one thing here.
    offered: [...document.querySelectorAll('.place-marker, .hotspot')]
      .filter((e) => !e.hidden).map((e) => e.querySelector('.label').textContent.trim()),
  };
}"""


def landed(page, shot_id):
    page.wait_for_function(
        "(id) => { const v = window.__map.viewpoints;"
        " return !v.flying && v.current.id === id; }",
        arg=shot_id, timeout=120000)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8263)
    args = ap.parse_args()

    spec = json.loads(SPEC.read_text())
    shots = spec["viewpoints"]

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

    srv = S(("127.0.0.1", args.port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    from playwright.sync_api import sync_playwright
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)
    errors = []

    print(f"the shots — {len(shots)} of them, at 390 px")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        page.set_default_timeout(180000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.evaluate("() => document.getElementById('intro-go')?.click()")
        page.wait_for_function("() => document.getElementById('intro').hidden")
        landed(page, shots[0]["id"])
        page.evaluate("() => window.__map.pinWorld(300)")

        one = page.evaluate(WHERE)
        want = shots[0]
        check("it opens standing in the first shot",
              one["id"] == want["id"]
              and max(abs(a - b) for a, b in zip(one["pos"], want["pos"])) < 0.5,
              f"{one['id']} at {one['pos']}")
        check("the card says where you are and what it is for",
              one["name"] == want["name"] and one["says"] == want["says"],
              f"{one['name']!r} — {one['says'][:48]}…")
        check("the dots say which shot, and there is one per shot",
              len(one["dots"]) == len(shots) and one["dots"].count(True) == 1
              and one["dots"][0],
              f"{len(one['dots'])} dots, lit {one['dots'].index(True)}")

        # Only what this frame is actually looking at can be descended to.
        named = {p for p in shots[0]["places"]}
        check("only the places this shot names are offered",
              len(one["offered"]) <= len(named),
              f"offered {one['offered'] or 'nothing'} of {len(named)} named")

        # The one that bit. Four of the eight markers in this map stand on the
        # same ground — three photographs of the Doughnut and a descent into
        # it — and declutter had been silently discarding the losers since the
        # markers landed. Naming two of them on one shot does not offer a
        # choice, it offers a coin toss: the meadow roof listed the descent,
        # declutter kept the photograph, and the descent could not be reached.
        clashes = page.evaluate("""() => {
          const m = window.__map;
          const at = {};
          for (const p of m.places.places) at[p.id] = [p.anchor.x, p.anchor.z];
          for (const h of m.hotspots) at[h.id] = [h.anchor.x, h.anchor.z];
          const out = [];
          for (const s of m.viewpoints.shots) {
            for (let i = 0; i < s.places.length; i++)
              for (let j = i + 1; j < s.places.length; j++) {
                const a = at[s.places[i]], b = at[s.places[j]];
                if (!a || !b) continue;
                const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
                if (d < 60) out.push(s.id + ": " + s.places[i] + "/"
                  + s.places[j] + " " + d.toFixed(0) + " m apart");
              }
          }
          return out;
        }""")
        check("no shot offers two ways into the same ground",
              not clashes, "; ".join(clashes) or "every marker is its own place")

        # And every name a shot uses has to exist, in one layer or the other.
        unknown = page.evaluate("""() => {
          const m = window.__map;
          const known = new Set([...m.places.places.map((p) => p.id),
                                 ...m.hotspots.map((h) => h.id)]);
          return m.viewpoints.shots.flatMap((s) =>
            s.places.filter((p) => !known.has(p)).map((s2) => s.id + ": " + s2));
        }""")
        check("every name a shot offers is a real place",
              not unknown, "; ".join(unknown) or "all resolved")

        # --- moving ---------------------------------------------------------
        page.evaluate("() => window.__map.viewpoints.fly(1)")
        landed(page, shots[1]["id"])
        two = page.evaluate(WHERE)
        want = shots[1]
        check("moving lands where the file says it lands",
              max(abs(a - b) for a, b in zip(two["pos"], want["pos"])) < 0.5
              and two["name"] == want["name"],
              f"{two['id']} at {two['pos']}")
        check("the move is a move, not a cut",
              math.dist(one["pos"], two["pos"]) > 50,
              f"{math.dist(one['pos'], two['pos']):.0f} m between the two shots")

        # The set wraps, so neither end is a dead stop.
        page.evaluate("() => window.__map.viewpoints.fly(-1)")
        landed(page, shots[-1]["id"])
        last = page.evaluate(WHERE)
        check("the set wraps rather than ending",
              last["id"] == shots[-1]["id"],
              f"back from the first lands on {last['id']}")

        # --- what you cannot do ---------------------------------------------
        print("\n  what you cannot do to a composed frame")
        check("no dolly: the distance is fenced to the shot's own",
              abs(last["minD"] - last["maxD"]) < 0.01
              and abs(last["minD"] - last["radius"]) < 0.5,
              f"{last['minD']:.0f} m, fixed")
        check("no pan, no zoom", not last["pan"] and not last["zoom"])
        swing = math.degrees(last["azimuth"][1] - last["azimuth"][0])
        tilt = math.degrees(last["polar"][1] - last["polar"][0])
        check("the lean is bounded — a look round, not a flight",
              5 < swing < 90 and 3 < tilt < 45,
              f"{swing:.0f}° of swing, {tilt:.0f}° of tilt")

        # And the fence has to hold against the real control, not just read
        # well in the object: a wheel is how anyone would try to leave.
        before = page.evaluate("() => window.__map.camera.position.distanceTo("
                               "window.__map.controls.target)")
        page.evaluate("""() => {
          const c = window.__map.renderer.domElement;
          for (let i = 0; i < 8; i++)
            c.dispatchEvent(new WheelEvent('wheel', {
              deltaY: -240, bubbles: true, cancelable: true }));
        }""")
        page.wait_for_timeout(1200)
        after = page.evaluate("() => window.__map.camera.position.distanceTo("
                              "window.__map.controls.target)")
        check("scrolling cannot zoom out of the shot",
              abs(after - before) < 1.0,
              f"{before:.1f} m before, {after:.1f} m after eight scrolls")

        gone = page.evaluate("""() => ({
          hint: !!document.getElementById('hint'),
          text: document.body.innerText.toLowerCase(),
        })""")
        check("nothing on screen tells anyone to drag, pan or zoom",
              not gone["hint"] and "drag:" not in gone["text"]
              and "scroll:" not in gone["text"])

        # --- the capture path -----------------------------------------------
        # Every plate in generate/ was made with ?clean=1&cam=, and a page that
        # flew to shot one on load would have re-framed all of them.
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html"
                  f"?clean=1&cam=141,505,757&look=-201,327",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.wait_for_timeout(1200)
        cap = page.evaluate("""() => ({
          pos: window.__map.camera.position.toArray().map((n) => Math.round(n)),
          chrome: !!document.querySelector('#shot-dots, .shot-arrow'),
        })""")
        check("a capture keeps the camera it asked for, and gets no chrome",
              cap["pos"] == [141, 505, 757] and not cap["chrome"],
              f"camera at {cap['pos']}")
        browser.close()
    srv.shutdown()

    check("no page errors", not errors, "; ".join(errors[:2]))
    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
