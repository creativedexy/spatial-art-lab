"""Checks on the photographs-as-places, and on the models standing on 2045.

Task 001. Two claims are worth a test rather than a look:

  A photograph lands on the viewpoint it was generated from. Every plate
  carries the camera it was rendered from, and places.json repeats those
  numbers; if the two ever drift the crossfade stops being the same view of
  the same ground and becomes two pictures of roughly the same place, which is
  the entire idea gone without anything visibly breaking.

  A missing model falls back rather than vanishing. The extrusions are the
  floor under the type models, and a family that hides its blocks without
  placing anything leaves an empty field where a campus should be.

Usage:  python3 scripts/test_places.py [--port 8213]
"""
import argparse
import http.server
import json
import math
import socketserver
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
GV = SITE / "golden-valley"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PHONE = {"width": 390, "height": 844}
MIN_TAP = 44          # the smallest target a phone should be asked to hit

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

    def handle_error(self, *a):
        pass


# Every place, and the plate whose camera it claims to be standing at.
SIDECARS = {
    "gchq": "generate/gchq/plate.json",
    "cyber-central": "generate/golden-valley-2045/a-cyber-central.json",
    "campus-courtyards": "generate/golden-valley-2045/b-the-campus.json",
    "panels-and-glasshouses": "generate/golden-valley-2045/c-panels-and-glasshouses.json",
    "gchq-meadow": "generate/close-2045/gchq-meadow.json",
}


def check_files():
    doc = json.loads((GV / "places.json").read_text())
    places = {p["id"]: p for p in doc["places"]}
    check("every place has a sidecar to be checked against",
          set(places) == set(SIDECARS),
          f"{len(places)} places")

    missing = [p["photo"] for p in doc["places"]
               if not (GV / p["photo"]).resolve().exists()]
    check("every photograph is on disk", not missing, "; ".join(missing))

    drift = []
    for pid, rel in SIDECARS.items():
        if pid not in places:
            continue
        frame = json.loads((SITE / rel).read_text())["frames"][0]
        p = places[pid]
        dp = math.dist(p["pos"], frame["pos"])
        dl = math.dist(p["look"], frame["look"])
        if dp > 0.01 or dl > 0.01:
            drift.append(f"{pid}: pos {dp:.2f} m, look {dl:.2f} m")
    check("each place stands at the camera its plate was rendered from",
          not drift, "; ".join(drift))

    waves = []
    for pid, rel in SIDECARS.items():
        if pid not in places:
            continue
        want = json.loads((SITE / rel).read_text()).get("wave", 0)
        if abs(places[pid]["wave"] - want) > 1e-6:
            waves.append(f"{pid}: {places[pid]['wave']} vs plate's {want}")
    check("each place carries the year its plate was rendered in",
          not waves, "; ".join(waves))
    return doc


PROBE = """async () => {
  const m = window.__map;
  const out = {};

  // Phase 11 offers a different set of routes from each composed shot, and
  // the opening shot happens to offer descents rather than photographs. Walk
  // every shot so "every marker on offer" still means the whole piece rather
  // than whichever kind of route happens to be in the opening frame.
  const markers = [];
  const markerMetrics = [];
  const seen = new Set();
  const startShot = m.viewpoints.at;
  for (let i = 0; i < m.viewpoints.shots.length; i++) {
    m.viewpoints.fly(i, { instant: true });
    await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    const offered = [...document.querySelectorAll('.place-marker, .hotspot')]
      .filter((e) => !e.hidden);
    for (const el of offered) {
      if (seen.has(el)) continue;
      seen.add(el);
      markers.push(el);
      // The part of the marker a thumb can actually hit. Photograph-marker
      // stems and pins are pointer-events: none because they otherwise cover
      // the descent hotspot below; hotspot buttons deliberately keep their
      // whole drawn marker clickable. Measure whichever rule each one uses.
      const hit = [...el.children].filter(
        (c) => getComputedStyle(c).pointerEvents !== 'none');
      const boxes = (hit.length ? hit : [el]).map((c) => c.getBoundingClientRect());
      const top = Math.min(...boxes.map((r) => r.top));
      const bottom = Math.max(...boxes.map((r) => r.bottom));
      const r = el.getBoundingClientRect();
      markerMetrics.push({ w: Math.round(Math.max(...boxes.map((b) => b.width))),
                           h: Math.round(bottom - top), drawn: Math.round(r.height) });
    }
  }
  m.viewpoints.fly(startShot, { instant: true });
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  out.markers = markerMetrics;
  out.views = m.viewpoints.shots.length;

  out.models = { ...m.models.placed };
  out.built = { ...m.models.built };
  out.ncic = m.models.ncicSite && {
    cx: Math.round(m.models.ncicSite.cx), cz: Math.round(m.models.ncicSite.cz),
    toGchq: Math.round(m.models.ncicSite.toGchq),
    toRoute: Math.round(m.models.ncicSite.toRoute),
    fields: m.models.ncicSite.fields,
    fallback: m.models.ncicSite.usedFallback,
    clearance: Math.round(m.models.ncicSite.clearance),
  };
  const wedge = m.scene.getObjectByName('future:ncic');
  if (wedge) {
    wedge.geometry.computeBoundingBox();
    const bb = wedge.geometry.boundingBox;
    const surf = {};
    for (const v of wedge.geometry.attributes.aSurface.array) surf[v] = (surf[v] || 0) + 1;
    out.wedge = { rise: +(bb.max.y - bb.min.y).toFixed(2),
                  span: +Math.hypot(bb.max.x - bb.min.x, bb.max.z - bb.min.z).toFixed(1),
                  surfaces: Object.keys(surf).length,
                  built: m.models.built.ncic };
  }
  out.blocksVisible = {};
  for (const [family, mesh] of m.future.blocks) out.blocksVisible[family] = mesh.visible;
  const campus = m.future.blocks.get('campus');
  const attr = campus && campus.geometry.attributes;
  out.facade = attr ? {
    aFacade: !!attr.aFacade, aBay: !!attr.aBay, aWallTop: !!attr.aWallTop,
    maxU: attr.aFacade ? Math.max(...attr.aFacade.array.filter((_, i) => i % 2 === 0)) : 0,
    bay: attr.aBay ? attr.aBay.array[0] : 0,
  } : {};

  // Visit a 2045 place and drive the flight on a synthetic clock, because a
  // software renderer takes seconds a frame and real time would land the
  // assertions wherever it happened to get to.
  const place = m.places.places.find((p) => p.id === 'campus-courtyards');
  const before = { pos: m.camera.position.toArray(), wave: m.future.wave };
  m.places.visit(place);
  const t0 = performance.now();
  for (const t of [0, 1300, 2600, 2601]) m.places.update(t0 + t);
  // The fade-in class lands on the next animation frame — one frame before it
  // would be a cut rather than a crossfade — and the markers hide when the
  // page's own loop next places them, so both need a frame to have happened.
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  m.places.updateMarkers();
  const img = document.querySelector('.place-photo');
  out.arrived = {
    state: m.places.state,
    pos: m.camera.position.toArray().map((v) => +v.toFixed(2)),
    target: m.controls.target.toArray().map((v) => +v.toFixed(2)),
    wave: +m.future.wave.toFixed(3),
    photo: img && img.getAttribute('src'),
    hidden: img && img.hidden,
    shown: img && img.classList.contains('shown'),
    backVisible: !document.getElementById('place-back').hidden,
    markersHidden: markers.every((el) => el.hidden),
  };

  m.places.leave();
  const t1 = performance.now();
  for (const t of [0, 1000, 2100, 2101]) m.places.update(t1 + t);
  out.returned = {
    state: m.places.state,
    driftMetres: +Math.hypot(...m.camera.position.toArray()
      .map((v, i) => v - before.pos[i])).toFixed(3),
    wave: +m.future.wave.toFixed(3),
    wasWave: before.wave,
    photoHidden: img.hidden,
    controls: m.controls.enabled,
  };
  return out;
}"""


def check_map(port, doc):
    from playwright.sync_api import sync_playwright

    srv = Server(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # A shader that fails to compile does not throw. Three logs it and
        # carries on, the mesh quietly stops drawing, and its depth material
        # goes on casting shadows into an empty field.
        shader_errors = []
        page.on("console", lambda msg: shader_errors.append(msg.text)
                if msg.type == "error" and "Shader Error" in msg.text else None)
        page.goto(f"http://127.0.0.1:{port}/golden-valley/index.html?descend=x",
                  wait_until="load", timeout=300000)
        page.wait_for_function("window.__terrainReady === true", timeout=480000)
        page.wait_for_timeout(4000)
        out = page.evaluate(PROBE)
        browser.close()
    srv.shutdown()
    out["shaderErrors"] = shader_errors

    check("no page errors", not errors, "; ".join(errors[:2]))

    small = [m for m in out["markers"] if m["h"] < MIN_TAP]
    check(f"every marker on offer is at least {MIN_TAP} px tall "
          f"at {PHONE['width']} px wide",
          out["markers"] and not small,
          f"{len(out['markers'])} offered routes across {out['views']} views, "
          f"shortest {min((m['h'] for m in out['markers']), default=0)} px")

    place = next(p for p in doc["places"] if p["id"] == "campus-courtyards")
    a = out["arrived"]
    check("the flight lands on the place's own camera",
          a["state"] == "there"
          and math.dist(a["pos"], place["pos"]) < 0.05
          and math.dist(a["target"], place["look"]) < 0.05,
          f"{math.dist(a['pos'], place['pos']):.3f} m from it")
    check("the year arrives with the camera",
          abs(a["wave"] - place["wave"]) < 1e-3, f"wave {a['wave']}")
    check("the photograph is shown, and it is the right one",
          bool(a["photo"]) and a["photo"].endswith(place["photo"].split("/")[-1])
          and not a["hidden"] and a["shown"],
          a["photo"] or "no src")
    check("standing in a photograph offers the way back",
          a["backVisible"])
    check("standing in a photograph hides the markers",
          a["markersHidden"])

    r = out["returned"]
    check("backing out returns the map exactly where the viewer left it",
          r["state"] == "map" and r["driftMetres"] < 0.01
          and abs(r["wave"] - r["wasWave"]) < 1e-3 and r["controls"]
          and r["photoHidden"],
          f"{r['driftMetres']} m adrift, wave back to {r['wave']}")

    # --- part 2, rewritten 10 Sep: procedural facades, not Meshy placement ---
    # `placed` says something stands there; `built` says how it got there.
    # The wedge sets placed.ncic too, so parked has to be read off `built`.
    loaded = [k for k, v in out["built"].items() if v == "model"]
    check("the Meshy models stay parked",
          not loaded,
          f"loaded: {loaded}" if loaded else "nothing loaded from a GLB")
    check("every family keeps its own buildings",
          all(out["blocksVisible"].get(f) is True
              for f in ("campus", "homes", "glasshouse")),
          json.dumps(out["blocksVisible"]))
    # The facade is written in metres, so the geometry has to carry metres.
    # Without these attributes the shader silently falls back to zero and
    # every building comes out as one flat band.
    check("the campus carries a facade written in metres",
          all(out["facade"].get(k) for k in ("aFacade", "aBay", "aWallTop"))
          and out["facade"]["maxU"] > 10,
          f"walls up to {out['facade']['maxU']:.1f} m long, "
          f"bays of {out['facade']['bay']:.2f} m")
    # The bug that cost twenty buildings: a shader patched at the wrong chunk
    # fails to compile, the mesh does not draw, and its depth material — which
    # nothing patched — goes on casting shadows into an empty field. Nothing
    # throws. Nothing in any suite noticed.
    check("every shader compiled", not out["shaderErrors"],
          "; ".join(out["shaderErrors"][:1])[:160] or "no shader errors")

    n = out["ncic"]
    # The rule: campus field with frontage on a named route within 150 m, and
    # of those the one nearest GCHQ.
    check("the NCIC site is still the one the rule picks",
          n is not None
          and n["fields"] == 4 and not n["fallback"] and n["toRoute"] <= 150,
          f"({n['cx']},{n['cz']}) — {n['toGchq']} m to GCHQ, "
          f"{n['toRoute']} m to a named route, {n['fields']} fields"
          if n else "no site")
    w = out.get("wedge")
    check("the NCIC stands on it, written rather than modelled",
          w is not None and w["built"] == "written" and w["surfaces"] == 3
          and abs(w["rise"] - 16) < 0.1,
          f"a wedge {w['rise']} m at the high end, {w['span']} m corner to corner, "
          f"{w['surfaces']} surfaces" if w else "no wedge in the scene")

    # 60 m long and 26.6 m wide, so it needs the courtyard to be clear of the
    # blocks round it by more than half its diagonal.
    check("the NCIC fits the courtyard it was given",
          n is not None and n["clearance"] > 33,
          f"nearest block {n['clearance']} m from the courtyard centre" if n else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8213)
    args = ap.parse_args()

    print("places.json and the plates")
    doc = check_files()
    print("the map, at 390 px")
    check_map(args.port, doc)

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("failed: " + ", ".join(failed))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
