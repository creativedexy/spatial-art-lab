"""What the living map costs to open, measured rather than estimated.

Phase 7. The map runs on this container and nowhere else, and the first
question anyone sensible asks about a 2 km world in a browser is what it
weighs on a phone. This answers that with three numbers per run:

  bytes      every response the page fetched, by kind. Absolute truth,
             independent of the machine measuring it.
  timings    the load milestones from golden-valley/stage.js, over a
             throttled connection with an empty cache. Network-dominated
             and therefore honest here.
  frame      median frame time once the map is up.

One caveat, stated because a number without it would be a lie: this container
renders through SwiftShader, on the CPU. A frame time from here is NOT a phone
frame time, and no scaling factor makes it one. It is a *relative* measure —
same renderer before and after a change — and nothing more. Bytes and the
network-bound part of the timings are the numbers that transfer.

Usage:
  python3 scripts/measure_payload.py --label before
  python3 scripts/measure_payload.py --label after --compare before
"""
import argparse
import collections
import gzip
import http.server
import io
import json
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
RUNS = SITE / "payload"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

# A mid-range 4G connection: what someone opening a link on the train has.
# Chrome's own "Fast 4G" preset, in bytes per second and milliseconds.
NETWORK = {"offline": False, "downloadThroughput": 9000 * 1024 // 8,
           "uploadThroughput": 9000 * 1024 // 8, "latency": 85}
PHONE = {"width": 390, "height": 844}

KINDS = {".bin": "terrain and trees", ".glb": "models", ".png": "textures",
         ".webp": "textures", ".avif": "textures", ".jpg": "textures",
         ".json": "data", ".js": "code", ".css": "code", ".html": "code",
         ".woff2": "fonts", ".webm": "video"}


# Every static host gzips text on the way out, so a measurement that does not
# is not measuring what a phone receives — it would bill 0.94 MB for footprints
# that arrive as 0.16, and send us optimising a file that is already small.
GZIP = (".json", ".js", ".css", ".html", ".svg")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def send_head(self):
        path = self.translate_path(self.path)
        if (not path.endswith(GZIP)
                or "gzip" not in self.headers.get("Accept-Encoding", "")):
            return super().send_head()
        try:
            body = gzip.compress(Path(path).read_bytes(), 6)
        except OSError:
            return super().send_head()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return io.BytesIO(body)

    def end_headers(self):
        # No caching, so every run measures a cold open. A warm one measures
        # the disk this script is running on, which is nobody's phone.
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def handle_error(self, *a):
        pass


FRAMES = """() => new Promise((done) => {
  // 90 frames of the map as it stands, then the middle one. A mean would be
  // dragged around by the first frame after a texture upload; the median is
  // what the thing actually feels like.
  const dt = []; let last = performance.now(); let n = 0;
  const step = (now) => {
    dt.push(now - last); last = now;
    if (++n < 90) requestAnimationFrame(step);
    else { dt.sort((a, b) => a - b); done(dt[dt.length >> 1]); }
  };
  requestAnimationFrame(step);
})"""


def measure(port, url_params=""):
    from playwright.sync_api import sync_playwright

    launch = {"args": ["--no-sandbox", "--use-gl=swiftshader"]}
    if CHROMIUM.exists():
        launch["executable_path"] = str(CHROMIUM)
    seen, errors = {}, []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        cdp = page.context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.emulateNetworkConditions", NETWORK)
        page.on("pageerror", lambda e: errors.append(str(e)))

        def on_response(r):
            # A texture embedded in a GLB is handed to the loader as a blob:
            # URL and comes back through here as if it had been downloaded.
            # Counting it would bill the GLB's own bytes twice — which is what
            # the first run of this script did, to the tune of 8 MB.
            if not r.url.startswith("http"):
                return
            try:
                n = int(r.header_value("content-length") or 0)
            except Exception:
                n = 0
            # A URL is counted once: a re-request of the same file is the
            # browser's business, not a second download of the site.
            seen[r.url.split("?")[0]] = n

        page.on("response", on_response)
        page.goto(f"http://127.0.0.1:{port}/golden-valley/index.html{url_params}",
                  wait_until="load", timeout=600000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.wait_for_function("window.__stage.timeline()"
                               ".some((m) => m.name === 'first frame')", timeout=120000)
        timeline = page.evaluate("window.__stage.timeline()")
        frame_ms = page.evaluate(FRAMES)
        browser.close()

    by_kind = collections.Counter()
    files = []
    for u, n in seen.items():
        name = u.rsplit("/", 1)[-1]
        # `.gz` is a wrapper, not a kind: the heightmap is still terrain.
        stem = name[:-3] if name.endswith(".gz") else name
        kind = KINDS.get("." + stem.rsplit(".", 1)[-1].lower(), "other")
        by_kind[kind] += n
        files.append({"file": name, "bytes": n, "kind": kind})
    files.sort(key=lambda f: -f["bytes"])
    return {"total": sum(by_kind.values()), "by_kind": dict(by_kind),
            "files": files, "timeline": timeline,
            "frame_ms": round(frame_ms, 2), "errors": errors[:5]}


def mb(n):
    return f"{n / 1048576:.2f} MB"


def report(run, before=None):
    print(f"\nCold open at {PHONE['width']}×{PHONE['height']}, "
          f"{NETWORK['downloadThroughput'] * 8 / 1024 / 1024:.0f} Mbit/s, "
          f"{NETWORK['latency']} ms RTT, no cache\n")
    print(f"  {'':22} {'bytes':>10}")
    for kind, n in sorted(run["by_kind"].items(), key=lambda kv: -kv[1]):
        print(f"  {kind:22} {mb(n):>10}")
    print(f"  {'TOTAL':22} {mb(run['total']):>10}"
          + (f"   (was {mb(before['total'])})" if before else ""))

    print(f"\n  {'milestone':22} {'at':>9} {'took':>9}")
    for m in run["timeline"]:
        print(f"  {m['name']:22} {m['at'] / 1000:8.2f}s {m['took'] / 1000:8.2f}s")

    first = next((m for m in run["timeline"] if m["name"] == "first frame"), None)
    if first:
        line = f"\n  first frame at {first['at'] / 1000:.2f}s"
        if before:
            was = next((m for m in before["timeline"]
                        if m["name"] == "first frame"), None)
            if was:
                line += f"   (was {was['at'] / 1000:.2f}s)"
        print(line)
    print(f"  median frame {run['frame_ms']:.1f} ms under SwiftShader "
          f"— relative only, not a phone")
    print("\n  ten heaviest files")
    for f in run["files"][:10]:
        print(f"    {mb(f['bytes']):>10}  {f['file']}")
    for e in run["errors"]:
        print(f"  page error: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="what to save this run as")
    ap.add_argument("--compare", help="an earlier label to show alongside")
    ap.add_argument("--params", default="", help="query string for the page")
    ap.add_argument("--port", type=int, default=8214)
    ap.add_argument("--site", help="serve this folder instead of the experiment "
                                   "— point it at dist/ to measure what is "
                                   "actually published")
    args = ap.parse_args()

    if args.site:
        global SITE
        SITE = Path(args.site).resolve()
    srv = Server(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    run = measure(args.port, args.params)
    srv.shutdown()

    RUNS.mkdir(exist_ok=True)
    out = RUNS / f"{args.label}.json"
    out.write_text(json.dumps(run, indent=2) + "\n")
    before = None
    if args.compare:
        p = RUNS / f"{args.compare}.json"
        if p.exists():
            before = json.loads(p.read_text())
        else:
            print(f"no earlier run called {args.compare}")
    report(run, before)
    print(f"\nsaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
