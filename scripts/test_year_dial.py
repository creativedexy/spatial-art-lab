"""The dial that carries the argument, and the interface around it at 390 px.

Phase 8. The wave was a button that fired once. The claim the map makes to a
client is that you can take the future in your hand and stop it half way —
one field already an orchard while the next is still stubble — so the dial is
not decoration on the feature, it *is* the feature, and it gets checked like
one.

What matters, in the order it matters: that dragging it actually moves the
front in the world (not just a number on screen), that it goes back as well as
forward, that the readout tells the truth even when something other than the
dial moved the wave, and that a thumb can work it at 390 px.

The second half is legibility, which phase 8 found by looking rather than by
reasoning: every marker in this map had been checked on its own — big enough
to hit, planted on the right ground — and at 390 px they came out as five
overlapping plates in one band with the doughnut's name buried under three
others, while four lines of licence text ran through the dial and off the
side. Each part was right and the screen was unreadable. These are the checks
that would have caught it.

  python3 scripts/test_year_dial.py
"""
import argparse
import http.server
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
CHROMIUM = Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")
PHONE = {"width": 390, "height": 844}
MIN_TAP = 44

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


SET = """(v) => {
  const r = document.getElementById('year-range');
  r.value = String(v);
  r.dispatchEvent(new Event('input', { bubbles: true }));
}"""

STATE = """() => ({
  wave: window.__map.future.wave,
  read: document.getElementById('year-read').textContent.trim(),
  slider: document.getElementById('year-range').valueAsNumber,
  arrived: document.getElementById('year-dial').classList.contains('arrived'),
})"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8238)
    args = ap.parse_args()

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
    print("the year dial, at 390 px")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.wait_for_timeout(1500)

        start = page.evaluate(STATE)
        check("it opens in the present", start["wave"] == 0 and start["read"] == "2026",
              f"wave {start['wave']}, reads {start['read']}")

        # The thing that would make all of this decoration: a dial that moves a
        # label and not the ground.
        page.evaluate(SET, 500)
        page.wait_for_timeout(400)
        half = page.evaluate(STATE)
        front = page.evaluate("window.__map.future.frontX")
        check("dragging it moves the front in the world, not just a number",
              abs(half["wave"] - 0.5) < 0.01 and front is not None,
              f"wave {half['wave']:.3f}, front at x={front:.0f} m")
        check("half way reads a year half way", half["read"] == "2036",
              f"reads {half['read']}")

        # Half a vale changed and half did not is the whole proposition, so
        # check the front is actually inside the box rather than past it.
        check("half way leaves the front standing in the vale",
              -1000 < front < 300, f"x={front:.0f} m, box is -1000..1000")

        page.evaluate(SET, 1000)
        page.wait_for_timeout(400)
        end = page.evaluate(STATE)
        check("it reaches 2045", end["wave"] >= 0.999 and end["read"] == "2045"
              and end["arrived"], f"wave {end['wave']}, reads {end['read']}")

        # Back the other way. A one-way control is the button we already had.
        page.evaluate(SET, 220)
        page.wait_for_timeout(400)
        back = page.evaluate(STATE)
        check("it goes back as well as forward",
              abs(back["wave"] - 0.22) < 0.01 and back["read"] == "2030",
              f"wave {back['wave']:.3f}, reads {back['read']}")

        # Something other than the dial moves the wave: flying to a place.
        page.evaluate("window.__map.future.setWave(1)")
        page.wait_for_timeout(400)
        elsewhere = page.evaluate(STATE)
        check("the readout follows the world, not its own input",
              elsewhere["read"] == "2045" and elsewhere["slider"] == 1000,
              f"reads {elsewhere['read']}, slider at {elsewhere['slider']}")

        box = page.evaluate("""() => {
          const r = document.getElementById('year-play').getBoundingClientRect();
          const t = document.getElementById('year-range').getBoundingClientRect();
          const d = document.getElementById('year-dial').getBoundingClientRect();
          return { play: Math.round(Math.min(r.width, r.height)),
                   track: Math.round(t.height),
                   right: Math.round(innerWidth - d.right),
                   bottom: Math.round(innerHeight - d.bottom) };
        }""")
        check(f"a thumb can work it — {MIN_TAP} px targets",
              box["play"] >= MIN_TAP and box["track"] >= 24,
              f"play {box['play']} px, track {box['track']} px, "
              f"{box['bottom']} px clear of the bottom edge")

        # --- legibility -----------------------------------------------------
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        page.evaluate("() => { const i = document.getElementById('intro');"
                      " if (i) i.hidden = true;"
                      " document.body.classList.remove('intro-open'); }")
        page.wait_for_timeout(2500)
        print("\n  the interface at 390 px")

        labels = page.evaluate("""() => {
          const els = [...document.querySelectorAll('.place-marker, .hotspot')]
            .filter((e) => !e.hidden);
          const boxes = els.map((e) => {
            const r = e.querySelector('.label').getBoundingClientRect();
            return { name: e.querySelector('.label').textContent.trim(),
                     l: r.left, r: r.right, t: r.top, b: r.bottom };
          });
          const clashes = [];
          for (let i = 0; i < boxes.length; i++)
            for (let j = i + 1; j < boxes.length; j++) {
              const a = boxes[i], b = boxes[j];
              if (!(a.r < b.l || a.l > b.r || a.b < b.t || a.t > b.b))
                clashes.push(`${a.name} / ${b.name}`);
            }
          return { showing: boxes.map((b) => b.name), clashes };
        }""")
        check("no two names sit on top of each other",
              not labels["clashes"],
              "; ".join(labels["clashes"][:3])
              or f"showing {', '.join(labels['showing'])}")
        check("something is still offered", len(labels["showing"]) >= 1,
              f"{len(labels['showing'])} of 8 markers")

        hit = page.evaluate("""() => {
          const b = document.getElementById('credit-toggle');
          const r = b.getBoundingClientRect();
          if (!r.width) return { shown: false };
          const top = document.elementFromPoint((r.left + r.right) / 2,
                                                (r.top + r.bottom) / 2);
          return { shown: true, tall: Math.round(r.height),
                   mine: b.contains(top) || top === b,
                   over: top ? (top.id || top.className || top.tagName) : 'nothing' };
        }""")
        check("the sources control is the thing you hit when you tap it, "
              f"at {MIN_TAP} px",
              hit.get("shown") and hit.get("mine")
              and hit.get("tall", 0) >= MIN_TAP,
              f"{hit.get('over')} is on top" if not hit.get("mine")
              else f"{hit.get('tall')} px tall")
        check("no mouse instructions on a phone",
              page.evaluate("() => getComputedStyle("
                            "document.getElementById('hint')).display === 'none'"))

        # And it must be out of the way of a capture, or every plate since
        # phase 5 would suddenly have a slider across it.
        page.goto(f"http://127.0.0.1:{args.port}/golden-valley/index.html?clean=1&wave=0.5",
                  wait_until="load", timeout=900000)
        page.wait_for_function("window.__terrainReady === true", timeout=900000)
        hidden = page.evaluate(
            "() => document.getElementById('year-dial').hidden")
        wave = page.evaluate("window.__map.future.wave")
        check("a capture still gets a map with no interface on it",
              hidden and abs(wave - 0.5) < 1e-6, f"hidden={hidden}, wave {wave}")
        browser.close()
    srv.shutdown()

    check("no page errors", not errors, "; ".join(errors[:2]))
    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
