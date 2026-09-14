"""The keyed subtraction, including the no-hole hand-off.

This needs the gitignored golden-valley/key.js and a browser. It never reads or
prints the key; the local page loads it exactly as it does in normal use.

  "/Users/user/Projects/3D Design/.venv/bin/python" scripts/test_keyed_fallback.py
"""
import argparse
import http.server
import socketserver
import threading
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
GV = SITE / "golden-valley"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
DEFERRED = {
    "gv-far-meta.json", "gv-far-near.bin.gz", "gv-far-far.bin.gz",
    "gv-trees.bin", "gv-buildings.json", "gv-landcover.webp",
}

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8298)
    args = ap.parse_args()
    if not (GV / "key.js").is_file():
        raise SystemExit("golden-valley/key.js is required (its contents are never read by this test)")

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
    # A real GPU, in a real window. Google's tiles parse at about one every
    # five seconds under swiftshader, so a keyed test launched the way the
    # keyless suites are never settles: it crawls until something kills it,
    # and the killed Python reaches the Node driver as an EPIPE that looks like
    # a flaky test rather than an impossible one.
    launch = {"headless": False, "args": ["--no-sandbox"]}
    requested = []
    errors = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 900, "height": 520})
        page.set_default_timeout(900000)
        page.on("request", lambda r: requested.append(Path(urlparse(r.url).path).name))
        page.on("pageerror", lambda e: errors.append(str(e)))
        # A shader that fails to compile is NOT a page error: WebGL reports it
        # on the console and the mesh simply stops drawing. The fallback patches
        # materials by hand after the world is built, so a double patch would
        # take GCHQ's meadow roof off the screen with no exception anywhere.
        shader_errors = []
        page.on("console", lambda msg: shader_errors.append(msg.text)
                if msg.type == "error" and any(k in msg.text for k in (
                    "WebGL", "shader", "Shader", "GL_INVALID", "THREE.WebGLProgram"))
                else None)
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true")

        before = page.evaluate("""() => {
          const m = window.__map;
          const ground = m.scene.getObjectByName('terrain');
          const buildings = m.scene.getObjectByName('buildings');
          const image = ground.material.map?.source?.data;
          return {
            tiles: !!m.tiles,
            showing: m.tiles?.showing,
            fallbackReady: m.scene.userData.fallback?.ready,
            far: !!m.scene.getObjectByName('far-field'),
            trees: !!m.scene.getObjectByName('trees'),
            buildingNames: buildings?.children.map((o) => o.name) ?? [],
            map: image?.currentSrc || image?.src || '',
            vertexColors: ground.material.vertexColors,
          };
        }""")
        early = sorted(DEFERRED.intersection(requested))
        check("the keyed first load omits every measured fallback asset",
              not early and before["fallbackReady"] is False,
              ", ".join(early) or "none requested")
        check("only GCHQ is built over the tiles",
              before["tiles"] and before["showing"]
              and set(before["buildingNames"]) == {"gchq:wall", "gchq:roof"}
              and not before["far"] and not before["trees"],
              ", ".join(before["buildingNames"]))
        check("keyed terrain uses the future map directly",
              before["map"].endswith("gv-2045-landcover.webp")
              and before["vertexColors"] is False,
              Path(urlparse(before["map"]).path).name or "no map")

        # One frame after a zero-warning jump, requests may only just have
        # begun. The interlock must still be showing tiles in that frame.
        immediate = page.evaluate("""async () => {
          const m = window.__map;
          // End the opening drift first. It writes the camera every frame for
          // fifteen seconds, so without this the jump below is undone before it
          // is rendered: the tiles stay on because the camera never got low,
          // this check passes for the wrong reason, and the wait after it for
          // the tiles to leave never resolves.
          document.getElementById('intro')?.dispatchEvent(new Event('dismiss'));
          m.viewpoints.hold(true);
          const y = m.groundAt(0, 0);
          m.camera.position.set(0, y + 14, 0);
          m.camera.lookAt(0, y + 10, -70);
          m.camera.updateMatrixWorld(true);
          await new Promise(requestAnimationFrame);
          return { showing: m.tiles.showing,
                   ready: m.scene.userData.fallback.ready,
                   above: m.camera.position.y - m.groundAt(0, 0) };
        }""")
        check("a zero-warning jump cannot open the tile gate onto a hole",
              immediate["showing"] and immediate["above"] < 20,
              f"camera {immediate['above']:.1f} m up; "
              + ("fallback already ready" if immediate["ready"] else "fallback loading"))

        page.wait_for_function("""() => {
          const m = window.__map;
          return m.scene.userData.fallback.ready && !m.tiles.showing;
        }""")
        after = page.evaluate("""() => {
          const m = window.__map;
          const ground = m.scene.getObjectByName('terrain');
          const far = m.scene.getObjectByName('far-field');
          const trees = m.scene.getObjectByName('trees');
          const buildings = m.scene.getObjectByName('buildings');
          const image = ground.material.map?.source?.data;
          let instances = 0;
          trees?.traverse((o) => { if (o.isInstancedMesh) instances += o.count; });
          return {
            far: far?.visible,
            trees: trees?.visible,
            instances,
            fallbackBuildings: buildings?.children.filter(
              (o) => !o.name.startsWith('gchq:') && o.visible).length ?? 0,
            map: image?.currentSrc || image?.src || '',
            vertexColors: ground.material.vertexColors,
          };
        }""")
        late = sorted(DEFERRED.difference(requested))
        check("the complete measured fallback is ready before tiles leave",
              after["far"] and after["trees"] and after["instances"] == 9216
              and after["fallbackBuildings"] > 0
              and after["map"].endswith("gv-landcover.webp")
              and after["vertexColors"] is True and not late,
              f"{after['instances']} trees, {after['fallbackBuildings']} building meshes; "
              + ("all assets requested" if not late else "missing " + ", ".join(late)))
        check("no shader failed to compile across the hand-off",
              not shader_errors,
              "clean console" if not shader_errors else shader_errors[0][:200])
        check("the keyed hand-off raises no page error", not errors,
              "; ".join(errors[:2]))
        browser.close()

    server.shutdown()
    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
