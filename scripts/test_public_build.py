"""What we publish is what we tested.

Phase 7. `build_site.py` leaves the campus models out of a public build,
because they derive from HBD's renders and `meshy/README.md` says pitch work
only. The map is meant to survive that: a family whose model is missing keeps
the untextured extrusions it had before, so the campus reads as blocks rather
than as an empty field.

"Meant to" is not a check. This builds the public folder, serves only that
folder, and looks at what a stranger would get: nothing 404s, nothing errors,
no model is placed, and the campus blocks are standing. It also states the
first-load weight of the published thing, which is not the same number as the
repository's — the repository has the models in it.

  python3 scripts/test_public_build.py
"""
import argparse
import http.server
import socketserver
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PHONE = {"width": 390, "height": 844}
BUDGET_MB = 9.0

checks = []


def json_models(dist):
    import json
    return json.loads((dist / "golden-valley" / "models.json").read_text())["available"]


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8234)
    ap.add_argument("--dist", default=str(ROOT / "dist"))
    args = ap.parse_args()

    dist = Path(args.dist)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "build_site.py"),
                        "--out", str(dist)], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        return 1

    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(dist), **kw)

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
    errors, missing, bytes_in = [], [], 0

    print("the public build")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        page.on("pageerror", lambda e: errors.append(str(e)))

        def seen(r):
            nonlocal bytes_in
            if r.status >= 400:
                missing.append(f"{r.status} {r.url.rsplit('/', 1)[-1]}")
            if r.url.startswith("http"):
                try:
                    bytes_in += int(r.header_value("content-length") or 0)
                except Exception:
                    pass

        page.on("response", seen)
        # The root is a redirect to the map, which is what a visitor hits.
        page.goto(f"http://127.0.0.1:{args.port}/", wait_until="load",
                  timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.wait_for_timeout(2000)
        state = page.evaluate("""() => ({
          placed: window.__map.models?.placed ?? {},
          blocks: Object.fromEntries([...window.__map.future.blocks]
            .map(([k, m]) => [k, m.visible])),
          markers: document.querySelectorAll('.place-marker').length,
          hotspots: window.__map.hotspots.length,
        })""")
        # And the wave still crosses the vale without the models in it.
        page.evaluate("window.__map.future.setWave(1)")
        page.wait_for_timeout(1500)
        wave = page.evaluate("window.__map.future.wave")
        browser.close()
    srv.shutdown()

    check("the root url reaches the map", True)
    check("nothing is missing", not missing, ", ".join(missing[:4]) or "no 4xx")
    check("the map knows it has no models rather than asking for them",
          not any(".glb" in m for m in missing),
          "models.json says " + str(json_models(dist)))
    check("no page errors", not errors, "; ".join(errors[:2]))
    check("no campus model is placed", not state["placed"], str(state["placed"]))
    check("the campus keeps its extrusions instead",
          state["blocks"].get("campus") is True,
          ", ".join(f"{k}={v}" for k, v in state["blocks"].items()))
    check("every place is still on the map", state["markers"] == 5,
          f"{state['markers']} markers, {state['hotspots']} hotspots")
    check("2045 still arrives", wave == 1, f"wave {wave}")
    check(f"first load is under {BUDGET_MB:.0f} MB",
          bytes_in / 1048576 < BUDGET_MB, f"{bytes_in / 1048576:.2f} MB")

    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
