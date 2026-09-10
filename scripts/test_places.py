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

  const markers = [...document.querySelectorAll('.place-marker')];
  out.markers = markers.map((el) => {
    const r = el.getBoundingClientRect();
    return { w: Math.round(r.width), h: Math.round(r.height) };
  });

  out.models = { ...m.models.placed };
  out.ncic = m.models.ncicSite && {
    cx: Math.round(m.models.ncicSite.cx), cz: Math.round(m.models.ncicSite.cz),
    toGchq: Math.round(m.models.ncicSite.toGchq),
    toRoute: Math.round(m.models.ncicSite.toRoute),
    fields: m.models.ncicSite.fields,
    fallback: m.models.ncicSite.usedFallback,
    clearance: Math.round(m.models.ncicSite.clearance),
  };
  out.blocksVisible = {};
  for (const [family, mesh] of m.future.blocks) out.blocksVisible[family] = mesh.visible;

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
        page.goto(f"http://127.0.0.1:{port}/golden-valley/index.html?descend=x",
                  wait_until="load", timeout=300000)
        page.wait_for_function("window.__terrainReady === true", timeout=480000)
        page.wait_for_timeout(4000)
        out = page.evaluate(PROBE)
        browser.close()
    srv.shutdown()

    check("no page errors", not errors, "; ".join(errors[:2]))

    small = [m for m in out["markers"] if m["h"] < MIN_TAP]
    check(f"every marker is at least {MIN_TAP} px tall at {PHONE['width']} px wide",
          len(out["markers"]) == len(doc["places"]) and not small,
          f"{len(out['markers'])} markers, shortest "
          f"{min((m['h'] for m in out['markers']), default=0)} px")

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

    # --- part 2 ---
    check("a type model stands on every campus footprint",
          out["models"].get("campus") == 20, f"{out['models']}")
    check("the campus extrusions stand down, the others do not",
          out["blocksVisible"].get("campus") is False
          and out["blocksVisible"].get("homes") is True
          and out["blocksVisible"].get("glasshouse") is True,
          json.dumps(out["blocksVisible"]))

    n = out["ncic"]
    # The rule: campus field with frontage on a named route within 150 m, and
    # of those the one nearest GCHQ.
    check("the NCIC site is the one the rule picks",
          n is not None and out["models"].get("ncic") == 1
          and n["fields"] == 4 and not n["fallback"] and n["toRoute"] <= 150,
          f"({n['cx']},{n['cz']}) — {n['toGchq']} m to GCHQ, "
          f"{n['toRoute']} m to a named route, {n['fields']} fields"
          if n else "no site")
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
