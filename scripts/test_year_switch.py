"""The switch that carries the argument, and the interface around it at 390 px.

Phase 11. The wave had a dial, on the reasoning that stopping the future half
way across the vale was the idea of the piece. It is not: a field caught half
built is neither the ground as it is nor the scheme as proposed, and those are
the only two states a room argues about. So the interface offers two, and the
sweep between them is a transition rather than a place you can park in.

What matters, in the order it matters: that pressing it actually moves the
front in the world (not just a label), that it comes back as well as goes,
that it tells the truth even when something other than the switch moved the
wave, that it settles at an end rather than wherever it was let go, and that a
thumb can work it at 390 px.

The shader is untouched and still takes a continuous front — `?wave=` holds it
half way for a capture, which is the one caller that wants it, and that is
checked here too.

The second half is legibility, which phase 8 found by looking rather than by
reasoning: every marker in this map had been checked on its own — big enough
to hit, planted on the right ground — and at 390 px they came out as five
overlapping plates in one band with the doughnut's name buried under three
others, while four lines of licence text ran through the panel and off the
side. Each part was right and the screen was unreadable. These are the checks
that would have caught it.

  python3 scripts/test_year_switch.py
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


# Press it the way a thumb does, rather than calling the handler: a control
# that only works when JavaScript pokes it is not a control.
PRESS = """() => document.getElementById('year-toggle').click()"""

# Straight from the world, not from the caption. `k` is what the knob is
# actually drawn at, so a knob that agrees with the label but not the vale
# fails here.
STATE = """() => {
  const t = document.getElementById('year-toggle');
  const on = [...t.querySelectorAll('.end')].filter((e) =>
    e.classList.contains('on')).map((e) => e.textContent.trim());
  return {
    wave: window.__map.future.wave,
    checked: t.getAttribute('aria-checked') === 'true',
    on,
    knob: Number(t.style.getPropertyValue('--k')),
    arrived: document.getElementById('year-dial').classList.contains('arrived'),
  };
}"""


def settle(page, to, timeout=90000):
    """Wait for the sweep to land, rather than guessing how long it takes.

    Measured while writing this: with the splash open, headless software
    rendering runs this scene at **0.66 fps** — two frames in three seconds.
    A fixed sleep there measures swiftshader, not the control, and that is
    exactly what the first draft of this file did: four failures, all of them
    the renderer. So the switch half opens the map the way a visitor does,
    and every wait is a poll on the world.
    """
    page.wait_for_function(
        f"() => Math.abs(window.__map.future.wave - {to}) < 0.002",
        timeout=timeout)


def open_map(page, port, query=""):
    """Open it and get past the splash, because a control behind a full-screen
    panel is not a control and cannot be pressed by anyone, test or visitor."""
    page.goto(f"http://127.0.0.1:{port}/golden-valley/index.html{query}",
              wait_until="load", timeout=900000)
    page.wait_for_function("window.__terrainReady === true", timeout=900000)
    page.evaluate("() => document.getElementById('intro-go')?.click()")
    page.wait_for_function(
        "() => document.getElementById('intro').hidden", timeout=30000)


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
    print("today, or 2045 — at 390 px")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch)
        page = browser.new_page(viewport=PHONE)
        page.on("pageerror", lambda e: errors.append(str(e)))
        open_map(page, args.port)
        page.wait_for_timeout(800)

        start = page.evaluate(STATE)
        check("it opens in the present",
              start["wave"] == 0 and start["on"] == ["Today"]
              and not start["checked"],
              f"wave {start['wave']}, lit: {', '.join(start['on']) or 'nothing'}")

        # The two halves of "it sweeps rather than cuts", and neither depends
        # on catching a frame: the press must NOT set the wave (no frame has
        # run yet when this reads it), and the wave must arrive on its own.
        page.evaluate(PRESS)
        immediate = page.evaluate("window.__map.future.wave")
        check("a press starts a crossing rather than setting the year",
              immediate < 0.5, f"wave {immediate:.4f} the instant it is pressed")
        settle(page, 1)
        end = page.evaluate(STATE)
        check("it arrives at 2045 on its own",
              end["wave"] >= 0.999 and end["checked"] and end["on"] == ["2045"]
              and end["arrived"],
              f"wave {end['wave']}, lit: {', '.join(end['on'])}")

        # Back the other way. A one-way control is the button we already had.
        page.evaluate(PRESS)
        settle(page, 0)
        back = page.evaluate(STATE)
        check("it comes back as well as goes",
              back["wave"] <= 0.001 and not back["checked"]
              and back["on"] == ["Today"],
              f"wave {back['wave']}, lit: {', '.join(back['on'])}")

        # Pressed twice before a single frame has run — which is what a
        # double tap is — it must end up where the second press asked, not
        # committed to 2045 because the first press got there first.
        page.evaluate(PRESS)
        page.evaluate(PRESS)
        settle(page, 0)
        turned = page.evaluate(STATE)
        check("pressed again mid-crossing it turns round",
              turned["wave"] <= 0.001 and not turned["checked"],
              f"wave {turned['wave']}")

        # Half a vale changed and half not is still what the shader does, and
        # a capture can still ask for it. Checked by driving the world rather
        # than the switch, since the switch no longer offers it.
        page.evaluate("window.__map.future.setWave(0.5)")
        page.wait_for_timeout(400)
        front = page.evaluate("window.__map.future.frontX")
        check("half way still leaves the front standing in the vale",
              -1000 < front < 300, f"x={front:.0f} m, box is -1000..1000")

        # The knob is not animated alongside the vale, it is drawn FROM it.
        # Asked for a position the switch cannot produce, it still tells the
        # truth — which is the property that stops it ever disagreeing.
        page.evaluate("window.__map.future.setWave(0.37)")
        page.wait_for_function(
            "() => Math.abs(Number(document.getElementById('year-toggle')"
            ".style.getPropertyValue('--k')) - 0.37) < 0.01", timeout=60000)
        odd = page.evaluate(STATE)
        check("the knob is drawn where the front actually is",
              abs(odd["knob"] - 0.37) < 0.01 and odd["on"] == ["Today"],
              f"knob at {odd['knob']:.3f} for wave {odd['wave']:.3f}")

        # Phase 11's actual decision, asserted rather than described: there is
        # no way to ask the interface for 2034.
        offered = page.evaluate("""() => ({
          range: document.querySelectorAll('#year-dial input[type=range]').length,
          ends: document.querySelectorAll('#year-toggle .end').length,
        })""")
        check("the interface offers two states and no third",
              offered["range"] == 0 and offered["ends"] == 2,
              f"{offered['ends']} ends, {offered['range']} sliders")

        # Something other than the switch moves the wave: flying to a place.
        page.evaluate("window.__map.future.setWave(1)")
        page.wait_for_function(
            "() => document.getElementById('year-toggle')"
            ".getAttribute('aria-checked') === 'true'", timeout=60000)
        elsewhere = page.evaluate(STATE)
        check("it follows the world, not its own input",
              elsewhere["checked"] and elsewhere["on"] == ["2045"]
              and abs(elsewhere["knob"] - 1) < 0.01,
              f"lit: {', '.join(elsewhere['on'])}, knob {elsewhere['knob']:.3f}")

        box = page.evaluate("""() => {
          const b = document.getElementById('year-toggle');
          const t = b.getBoundingClientRect();
          const d = document.getElementById('year-dial').getBoundingClientRect();
          const mid = document.elementFromPoint((t.left + t.right) / 2,
                                                (t.top + t.bottom) / 2);
          return { tall: Math.round(t.height), wide: Math.round(t.width),
                   mine: b.contains(mid) || mid === b,
                   over: mid ? (mid.id || mid.className || mid.tagName) : 'nothing',
                   bottom: Math.round(innerHeight - d.bottom) };
        }""")
        check(f"a thumb can work it — {MIN_TAP} px, and it is what you hit",
              box["tall"] >= MIN_TAP and box["wide"] >= 2 * MIN_TAP
              and box["mine"],
              f"{box['over']} is on top" if not box["mine"]
              else f"{box['wide']}x{box['tall']} px, "
                   f"{box['bottom']} px clear of the bottom edge")

        # --- the scheme band ------------------------------------------------
        # Driven through `setWave` rather than the switch, deliberately. The
        # switch no longer offers a half-way, but the wave still passes through
        # one on every press and a capture can hold it there, so the band has
        # to be right at every position — not only at the two it can be left in.
        print("\n  what the scheme is, while it arrives")
        page.evaluate("window.__map.future.setWave(0)")
        page.wait_for_timeout(300)
        at0 = page.evaluate("() => ({ ha: window.__map.scheme.arrivedHectares(),"
                            " say: document.querySelector('#scheme .say').textContent })")
        check("at 2026 nothing has changed and it says so",
              at0["ha"] == 0 and "2045" in at0["say"], f"{at0['say']!r}")

        page.evaluate("window.__map.future.setWave(1)")
        page.wait_for_timeout(400)
        at1 = page.evaluate("() => ({ ha: window.__map.scheme.arrivedHectares(),"
                            " total: window.__map.scheme.grandHectares,"
                            " say: document.querySelector('#scheme .say').textContent })")
        check("at 2045 the whole scheme is counted",
              abs(at1["ha"] - at1["total"]) < 0.05,
              f"{at1['ha']:.1f} of {at1['total']:.1f} ha — {at1['say']!r}")

        # The check that matters: measured, not tweened. The scheme is not
        # spread evenly — the wetland follows the brook and is westernmost —
        # so a linear ramp would be wrong here by a lot.
        page.evaluate("window.__map.future.setWave(0.5)")
        page.wait_for_timeout(400)
        half = page.evaluate("() => window.__map.scheme.arrivedHectares()")
        linear = at1["total"] / 2
        check("half way across is measured area, not half the total",
              abs(half - linear) > 1.0,
              f"{half:.1f} ha behind the front, against {linear:.1f} if it "
              f"were tweened")

        opened = page.evaluate("""() => {
          document.getElementById('scheme').click();
          const s = document.getElementById('scheme-sheet');
          return { open: !s.hidden, rows: s.querySelectorAll('tbody tr').length,
                   text: s.textContent.replace(/\s+/g, ' ').slice(0, 80) };
        }""")
        check("the band opens the figures behind it",
              opened["open"] and opened["rows"] >= 5,
              f"{opened['rows']} land-use rows")
        page.evaluate("() => document.getElementById('scheme').click()")

        # --- legibility -----------------------------------------------------
        open_map(page, args.port)
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
