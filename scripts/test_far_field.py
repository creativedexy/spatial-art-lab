"""The land beyond the box, and the joins that have to be invisible.

The map held two square kilometres and then stopped: the ground ran out at a
cliff and the sky started. Phase 11 could only compose around it — every
candidate shot that looked north-west was thrown out because the survey ends
270 m behind the new homes.

So there is now a horizon, built from OS Terrain 50 by scripts/far_field.py.
Almost all of what can go wrong with it is a join:

  the seam      two surveys of the same ground disagree by metres, and a step
                at the box boundary is a crack you cannot unsee
  the tuck      the far field runs UNDER the box rather than meeting it, so a
                50 m grid never fights a 2 m one along a line
  the grids     near and far have to divide exactly, or they meet at a second
                seam of their own
  the sky       the dome has to be bigger than the land and smaller than the
                camera's far plane, and getting that wrong does not draw a
                bigger sky, it draws NO sky — the first attempt came back
                with a black band across the top of every frame

And one thing that is not a join at all: the Earth curves away, 340 m of it at
75 km, which is the difference between distant hills standing on the horizon
and floating above it.

  python3 scripts/test_far_field.py
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
GV = SITE / "golden-valley"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8291)
    args = ap.parse_args()

    meta = json.loads((GV / "gv-far-meta.json").read_text())
    near, far = meta["grids"]["near"], meta["grids"]["far"]

    print("the land beyond the box")

    # --- what the build produced, before a browser is involved -------------
    step_n, step_f = near["stepMetres"], far["stepMetres"]
    half_n, half_f = near["halfExtentMetres"], far["halfExtentMetres"]
    box = meta["boxHalfMetres"]
    check("the near grid divides the box edge exactly",
          (half_n - box) % step_n == 0,
          f"{(half_n - box) / step_n:.0f} posts from the box to {half_n / 1000:.0f} km")
    check("the far grid divides the near grid's edge exactly",
          (half_f - half_n) % step_f == 0,
          f"{(half_f - half_n) / step_f:.0f} posts from {half_n / 1000:.0f} to "
          f"{half_f / 1000:.0f} km")
    size = sum((GV / g["binFile"]).stat().st_size for g in (near, far))
    check("a horizon costs under half a megabyte",
          size < 512 * 1024, f"{size / 1024:.0f} KB for {2 * half_f / 1000:.0f} km")
    check("the sources are named", len(meta["sources"]) >= 2,
          "; ".join(s.split("(")[0].strip() for s in meta["sources"]))

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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 900, "height": 520})
        page.set_default_timeout(300000)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html?clean=1",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)

        print("\n  in the scene")
        built = page.evaluate("""() => {
          const g = window.__map.scene.getObjectByName('far-field');
          if (!g) return null;
          let verts = 0, tris = 0;
          const names = [];
          g.traverse((o) => {
            if (!o.isMesh) return;
            names.push(o.name);
            verts += o.geometry.attributes.position.count;
            tris += o.geometry.index.count / 3;
            });
          return { meshes: names, verts, tris, visible: g.visible,
                   shadows: g.castShadow };
        }""")
        check("it is in the world", built and len(built["meshes"]) == 2,
              f"{built['meshes'] if built else 'nothing'}, "
              f"{built['verts'] if built else 0} vertices, "
              f"{int(built['tris']) if built else 0} triangles")
        check("it casts no shadows — the sun's map is 8 km and this is 150",
              built and not built["shadows"])

        # --- the joins ------------------------------------------------------
        print("\n  the joins")
        seam = page.evaluate("""(box) => {
          const g = window.__map.scene.getObjectByName('far-field');
          const THREE = window.__Three;
          // Read the far field's own surface by raycasting straight down, and
          // our LiDAR by asking the map — along the box edge, a metre either
          // side of it, all the way round.
          const out = [];
          for (let a = 0; a < 360; a += 7) {
            const t = a * Math.PI / 180;
            // A point ON the square edge at this bearing.
            const c = Math.cos(t), s = Math.sin(t);
            const k = box / Math.max(Math.abs(c), Math.abs(s));
            const x = c * k, z = s * k;
            // Just outside, where the far field is the visible surface.
            const ox = x * 1.02, oz = z * 1.02;
            out.push({ x: ox, z: oz, ours: window.__map.groundAt(
              Math.max(-box, Math.min(box, ox)),
              Math.max(-box, Math.min(box, oz))) });
          }
          return out;
        }""", meta["boxHalfMetres"])

        # Raycast the far field at those points and compare with our ground.
        page.evaluate("""async () => {
          const THREE = await import('three');
          window.__Ray = THREE.Raycaster; window.__V3 = THREE.Vector3;
        }""")
        gaps = page.evaluate("""(pts) => {
          const g = window.__map.scene.getObjectByName('far-field');
          const ray = new window.__Ray();
          const down = new window.__V3(0, -1, 0);
          const out = [];
          for (const p of pts) {
            ray.set(new window.__V3(p.x, 1200, p.z), down);
            const hit = ray.intersectObject(g, true);
            if (hit.length) out.push(hit[0].point.y - p.ours);
          }
          return out;
        }""", seam)
        worst = max((abs(v) for v in gaps), default=None)
        check("the far field meets our LiDAR at the box edge",
              worst is not None and worst < 4.0,
              f"worst {worst:.2f} m over {len(gaps)} points round the boundary"
              if worst is not None else "no far-field surface found outside the box")

        # --- curvature ------------------------------------------------------
        print("\n  the shape of the Earth")
        drop = page.evaluate("""(d) => {
          const g = window.__map.scene.getObjectByName('far-field');
          const ray = new window.__Ray();
          const down = new window.__V3(0, 4000, 0);
          // Straight down at d metres east, and at the same place in the data.
          const r = new window.__Ray(new window.__V3(d, 4000, 0),
                                     new window.__V3(0, -1, 0));
          const hit = r.intersectObject(g, true);
          return hit.length ? hit[0].point.y : null;
        }""", 70000)
        expect = 70000 ** 2 / (2 * 6371000 * 7 / 6)
        check("distant land is dropped by the curve of the Earth",
              drop is not None and drop < -expect * 0.5,
              f"70 km east reads {drop:.0f} m with a {expect:.0f} m curvature drop"
              if drop is not None else "nothing out there")

        # --- the sky --------------------------------------------------------
        print("\n  the sky, which is the one that bit")
        sky = page.evaluate("""() => {
          const cam = window.__map.camera;
          let dome = null;
          window.__map.scene.traverse((o) => {
            if (o.isMesh && o.geometry.type === 'SphereGeometry') dome = o;
          });
          return dome ? { r: dome.geometry.parameters.radius, far: cam.far }
                      : null;
        }""")
        reach = meta["grids"]["far"]["halfExtentMetres"] * math.sqrt(2)
        check("the sky is bigger than the land and inside the camera",
              sky and reach < sky["r"] < sky["far"],
              f"land reaches {reach / 1000:.0f} km, dome {sky['r'] / 1000:.0f} km, "
              f"camera far {sky['far'] / 1000:.0f} km" if sky else "no dome")

        # Nothing black where the sky should be — the failure the dome caused.
        top = page.evaluate("""() => {
          const m = window.__map;
          m.controls.enabled = false;
          m.camera.position.set(-640, 230, 300);
          m.camera.lookAt(-180, m.groundAt(-180, -126) + 20, -126);
          m.camera.updateMatrixWorld();
          m.renderer.render(m.scene, m.camera);
          const c = m.renderer.domElement;
          const g = document.createElement('canvas');
          g.width = c.width; g.height = c.height;
          g.getContext('2d').drawImage(c, 0, 0);
          const d = g.getContext('2d').getImageData(0, 0, c.width, 6).data;
          let lo = 255;
          for (let i = 0; i < d.length; i += 4)
            lo = Math.min(lo, (d[i] + d[i + 1] + d[i + 2]) / 3);
          return lo;
        }""")
        check("the top of the frame is sky, not a hole",
              top is not None and top > 80,
              f"darkest pixel in the top rows is {top:.0f} of 255")

        browser.close()
    srv.shutdown()

    check("no page errors", not errors, "; ".join(errors[:2]))
    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
