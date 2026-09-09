"""Drive the hotspot descent the way a visitor does, and check what happened.

Headless Chromium's virtual-time mode fast-forwards timers but does not
advance media playback, so it can only ever exercise the fallback. This runs
in real time with real clicks, which is the only way to prove the clip route
itself works: the assertion that matters is that the video element's
currentTime actually moved.

Nothing here waits on the clock. The descent is driven by requestAnimationFrame
and this world renders through software WebGL on a machine with no GPU, at
seconds per frame rather than frames per second — so a 900 ms fly-in can take
half a minute of wall time, and every fixed `wait_for_timeout` that used to
stand in for "by now it must have arrived" was really measuring the renderer.
Waits are on state, with timeouts long enough that a slow renderer costs
patience rather than a false failure.

Usage:  python3 scripts/test_hotspot_flow.py [--port 8188] [--shots DIR]
"""
import argparse
import http.server
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")


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
    ap.add_argument("--port", type=int, default=8188)
    ap.add_argument("--shots", default=None, help="directory for stills")
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright
    from playwright.sync_api import TimeoutError as PWTimeout

    serve(args.port)
    url = f"http://127.0.0.1:{args.port}/golden-valley/index.html"
    shots = Path(args.shots) if args.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    failures = []

    def check(name, ok, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
        if not ok:
            failures.append(name)

    with sync_playwright() as pw:
        launch = {"args": ["--no-sandbox", "--use-gl=swiftshader", "--autoplay-policy=no-user-gesture-required"]}
        if CHROMIUM.exists():
            launch["executable_path"] = str(CHROMIUM)
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        # One frame can take several seconds here, and Playwright's default
        # 30 s action timeout is not enough to land a click between two of them.
        page.set_default_timeout(180_000)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(url)
        page.wait_for_function("window.__terrainReady === true", timeout=240_000)
        page.wait_for_selector(".hotspot", timeout=120_000)
        if shots:
            page.screenshot(path=str(shots / "01-map.png"))

        check("three hotspots are offered", page.locator(".hotspot:visible").count() == 3)

        # Click the one with a clip, exactly as a visitor would.
        page.get_by_role("button", name="GCHQ — the Doughnut").click()
        # The fallback never puts the video on screen at all, so "displayed and
        # its clock has moved" is what separates the two routes. Media decodes
        # off the main thread, so currentTime advances in real time even while
        # the renderer is crawling — this is the one thing here that is allowed
        # to depend on the clock.
        played = {"t": 0, "w": 0}
        try:
            page.wait_for_function(
                "() => { const v = document.querySelector('.descent-clip');"
                " return v && getComputedStyle(v).display !== 'none' && v.currentTime > 0.2; }",
                timeout=120_000)
            played = page.evaluate(
                "() => { const v = document.querySelector('.descent-clip');"
                " return { t: v.currentTime, w: v.videoWidth }; }")
        except PWTimeout:
            pass
        if shots:
            page.screenshot(path=str(shots / "02-descending.png"))
        check("the clip is playing, not the fallback", played["t"] > 0.2,
              f"currentTime={round(played['t'], 2)}s, {played['w']}px wide")

        page.wait_for_selector("#panel:not([hidden])", timeout=240_000)
        if shots:
            page.screenshot(path=str(shots / "03-arrived.png"))

        # Visibility, not the `hidden` property: an author rule can outrank the
        # user agent's [hidden] and leave an element on screen regardless.
        state = page.evaluate(
            "() => ({ title: document.getElementById('panel-title').textContent,"
            " clipShown: getComputedStyle(document.querySelector('.descent-clip')).display !== 'none',"
            " pills: [...document.querySelectorAll('.hotspot')]"
            "   .filter(b => getComputedStyle(b).display !== 'none').length })")
        check("the place panel names where we landed", state["title"] == "GCHQ — the Doughnut")
        check("the clip is off screen once it has handed back", state["clipShown"] is False)
        check("the place we are standing in stops offering itself", state["pills"] == 2)

        page.get_by_role("button", name="Return to the map").click()
        page.wait_for_selector("#panel", state="hidden", timeout=240_000)
        back = 0
        try:
            page.wait_for_function(
                "() => [...document.querySelectorAll('.hotspot')]"
                "  .filter(b => getComputedStyle(b).display !== 'none').length === 3",
                timeout=60_000)
            back = 3
        except PWTimeout:
            back = page.locator(".hotspot:visible").count()
        if shots:
            page.screenshot(path=str(shots / "04-returned.png"))
        check("every hotspot is back on the map", back == 3, f"{back} of 3 visible")

        # And the place with no clip should fly the same path live.
        page.get_by_role("button", name="Golden Valley — phase 1").click()
        page.wait_for_selector("#panel:not([hidden])", timeout=240_000)
        if shots:
            page.screenshot(path=str(shots / "05-live-descent.png"))
        note = page.locator("#panel-note").text_content()
        check("a place with no clip descends live and says so", "flown live" in note)

        check("no page errors", not errors, "; ".join(errors[:3]))
        browser.close()

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
