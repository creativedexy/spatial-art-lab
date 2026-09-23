"""Break test: drive the live studio through random actions and check nothing breaks.

    python3 experiments/004-specimen-studio/test_fuzz.py [steps] [seed]
Starts its own server, opens studio.html in the gstack headless browser, then plays a seeded random sequence of what
a person does: play, pause, scrub, jump bars, add and delete cues, change preset, plate, track, sliders, bindings,
format, load a shot. After every step it renders and checks: no errors, a non-blank frame, a valid form, and that
the form never jumps more than 20 degrees between frames unless a kick just landed or the playhead jumped.
Exit code 1 on any failure.
"""
import json, subprocess, sys, threading, http.server
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import serve

B = str(Path.home() / '.claude/skills/gstack/browse/dist/browse')
JS = r"""
(async () => { if (window.__fz) return 'ready';
  const errs = []; let seed = %SEED%;
  const rnd = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; }, pick = a => a[Math.floor(rnd() * a.length)];
  addEventListener('error', e => errs.push(e.message)); addEventListener('unhandledrejection', e => errs.push(String(e.reason)));
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const lib = await (await fetch('/api/library')).json();
  const keys = Object.keys(RANGE), presets = Object.keys({...PRESETS, ...stored()});
  const tiny = document.createElement('canvas'); tiny.width = 16; tiny.height = 28; const tx = tiny.getContext('2d', {willReadFrequently: true});
  const fails = []; let jumped = true, lastA = null, lastT = null, steps = 0;
  const frame = () => { const t0 = performance.now(); render(t0);
    tx.drawImage(cv, 0, 0, 16, 28); const d = tx.getImageData(0, 0, 16, 28).data; let s = 0; for (let i = 0; i < d.length; i += 4) s += d[i] + d[i + 1] + d[i + 2];
    const why = [];
    if (src && s === 0) why.push('blank frame');
    if (P.hyper !== 'OFF' && (!formPts.length || formPts.some(p => !isFinite(p.x) || !isFinite(p.y)))) why.push('form missing or NaN');
    if (!isFinite(formA)) why.push('form angle NaN');
    const dt = lastT === null ? 0 : Math.abs(spinT - lastT), spin = Math.abs(P.speed * P.hspin) * 4 * dt;   // allow the fastest legit spin (bass boost x4)
    if (lastA !== null && !jumped && BEAT.kickAge > 0.25) { const dA = Math.abs(formA - lastA) - spin; if (dA > 0.35) why.push(`form jolted ${(dA * 57.3).toFixed(0)} deg beyond its spin`); }
    lastA = formA; lastT = spinT; jumped = false; return why; };
  const acts = {
    play: () => setPlaying(true), pause: () => setPlaying(false),
    scrub: () => { seek(rnd() * tlLength()); jumped = true; }, bar: () => { seek((BM ? BM.offset : 0) + (BEAT.bar + 1) * barLen() + 0.01); jumped = true; },
    cue: () => $('addcue').onclick(), uncue: () => { if (cues.length) { cues.splice(Math.floor(rnd() * cues.length), 1); cueOn = -2; } },
    preset: () => { $('preset').value = pick(presets); $('preset').onchange(); },
    plate: async () => { if (lib.plates.length) { const p = pick(lib.plates).path; $('plate').value = p; loadPlate(p); await wait(250); } },
    track: async () => { const a = pick(['', ...lib.audio]); $('track').value = a; $('track').onchange(); await wait(300); jumped = true; },
    slider: () => { const k = pick(keys), [mn, mx] = RANGE[k]; P[k] = mn + rnd() * (mx - mn); changed(k); },
    bind: () => { const k = pick(BINDABLE); P.bind[k] = pick(SIGNALS.slice(1)); keepInCue(); },
    form: () => { P.hyper = pick(['TESSERACT', 'NESTED FRAMES', 'BOTH', '16-CELL', '24-CELL', 'HOPF RINGS', 'LATTICE', 'GOLDEN SPIRAL', 'SHARDS', 'SLICES', 'ARMILLARY', 'CELL + SHARDS']); changed('hyper'); },
    format: () => { $('format').value = pick(['1080x1920', '720x1280', '1280x720']); $('format').onchange(); },
    shot: async () => { if (lib.shots.length) { $('shot').value = pick(lib.shots); await $('shot').onchange(); await wait(300); jumped = true; } },
  };
  const names = Object.keys(acts), tally = {};
  window.__fz = {async run(n) {                                             // chunks: the browser tool times out on long scripts
    for (let j = 0; j < n; j++) {
      const i = steps, a = pick(names); tally[a] = (tally[a] || 0) + 1;
      try { await acts[a](); } catch (e) { errs.push(`${a}: ${e.message}`); }
      for (let f = 0; f < 3; f++) { await wait(45); const why = frame(); if (why.length) fails.push(`step ${i} after ${a}: ${why.join(', ')}`); }
      steps++;
    }
    return JSON.stringify({steps, tally, errors: [...new Set(errs)].slice(0, 12), fails: fails.slice(0, 12), failCount: fails.length});
  }};
  return 'ready';
})()
"""


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 200; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler); port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    def run(*a):
        r = subprocess.run([B, *a], capture_output=True, text=True); return r.stdout + ('\n[stderr] ' + r.stderr.strip() if r.stderr.strip() else '')
    run('goto', f'http://127.0.0.1:{port}/experiments/004-specimen-studio/studio.html'); run('wait', '1500')
    setup = run('js', JS.replace('%SEED%', str(seed))).strip()
    if 'ready' not in setup: srv.shutdown(); raise SystemExit(f'setup failed: {setup[-400:]}')
    out = ''
    for _ in range(0, steps, 4):                                         # small chunks: each js call must finish within the tool's timeout
        lines = run('js', 'window.__fz.run(4)').strip().splitlines()
        lines = [l for l in lines if not l.startswith('[stderr]')] or lines
        if not lines or not lines[-1].lstrip('"').startswith('{'):
            srv.shutdown(); raise SystemExit(f'browser did not answer: {lines[-3:] if lines else "(nothing)"}')
        out = lines[-1]
    srv.shutdown()
    r = json.loads(json.loads(out) if out.startswith('"') else out)
    print(f"{r['steps']} steps  {json.dumps(r['tally'])}")
    for e in r['errors']: print('  ERROR', e)
    for f in r['fails']: print('  FAIL ', f)
    ok = not r['errors'] and not r['failCount']
    print('PASS' if ok else f"FAIL ({len(r['errors'])} errors, {r['failCount']} bad frames)")
    return ok


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
