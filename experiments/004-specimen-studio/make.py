"""Render one shot headless: plate -> (TouchDesigner HUD) -> Specimen Studio geometry -> MP4 with audio.

    python3 experiments/004-specimen-studio/make.py experiments/004-specimen-studio/shots/k2-twin.json

shot.json (paths relative to the repo root):
  name      output stem
  plate     image or video the studio draws over
  td_hud    true: run the plate through TouchDesigner (003-spider-probe/td) first and use its HUD render
  preset    a Specimen Studio preset name; params override any field (Save shot in the studio writes these)
  format    "1280x720" | "720x1280" | "1080x1350" | "1080x1080";  fps, seconds
  audio     optional track: analysed offline into per-frame bass/mid/high for the bindings, then muxed in
  cues      optional [{bar, name, plate, params}]: the look (and clip) changes at each bar (the studio's timeline); hits come from beats.py
Output: render/<name>.mp4 and render/<name>-sheet.jpg in this folder. Adjust by opening studio.html,
tuning by hand and pressing Save shot; the saved file runs here unchanged.
"""
import json, os, socket, subprocess, sys, threading, time, shutil, functools, http.server
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
B = str(Path.home() / '.claude/skills/gstack/browse/dist/browse')
TD_DIR = ROOT / 'experiments/003-spider-probe/td'


def log(*a):
    print('[make]', *a, flush=True)


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode not in (0, None) and not kw.get('check_ok'):
        raise SystemExit(f'failed: {cmd[:3]}\n{r.stderr[-2000:]}')
    return r.stdout


def browse(*args):
    out = subprocess.run([B, *args], capture_output=True, text=True)
    return out.stdout + out.stderr


def serve():
    """Same-origin HTTP for the page and its media, so the canvas can be read back."""
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    handler.log_message = lambda *a, **k: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


def audio_signals(path, fps, frames):
    """Per-frame bass/mid/high in 0..1, smoothed like the live analyser."""
    import numpy as np
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', '22050', '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32); sr = 22050; hop = sr / fps; n = 2048
    freqs = np.fft.rfftfreq(n, 1 / sr); bands = [(40, 250), (250, 2000), (2000, 8000)]
    rows = []
    for i in range(frames):
        c = int(i * hop); seg = x[max(0, c - n // 2):c + n // 2]
        seg = np.pad(seg, (0, n - len(seg))) * np.hanning(n); mag = np.abs(np.fft.rfft(seg))
        rows.append([mag[(freqs >= a) & (freqs < b)].mean() for a, b in bands])
    m = np.array(rows); m = m / (np.percentile(m, 95, axis=0) + 1e-9); m = np.clip(m, 0, 1)
    for i in range(1, len(m)):
        m[i] = m[i - 1] * 0.6 + m[i] * 0.4
    return np.round(m, 3).tolist()


def td_pass(plate, frames, name):
    """Run the TouchDesigner HUD network on the plate, headless (boot DAT builds, records, quits)."""
    out = HERE / f'render/scratch/{name}-td.mov'
    (TD_DIR / 'shot_io.json').write_text(json.dumps({'plate': str(plate), 'out': str(out), 'frames': frames}))
    toe = TD_DIR / 'spider_hud.toe'
    sh([sys.executable, str(TD_DIR / 'mktoe.py'), str(toe), str(TD_DIR / 'build_hud.py')])
    if out.exists():
        out.unlink()
    subprocess.run(['open', '-n', '-a', 'TouchDesigner', '--args', str(toe)])
    t = time.time()
    time.sleep(8)
    while subprocess.run(['pgrep', '-f', f'MacOS/TouchDesigner {toe}'], capture_output=True).returncode == 0 and time.time() - t < 900:
        time.sleep(2)
    logf = TD_DIR / 'build_hud.py.log'
    if 'Traceback' in (logf.read_text() if logf.exists() else ''):
        raise SystemExit('TouchDesigner build failed:\n' + logf.read_text()[-2000:])
    if not out.exists():
        raise SystemExit('TouchDesigner produced no movie (licence dialog open?)')
    mp4 = out.with_suffix('.mp4')
    sh(['ffmpeg', '-y', '-v', 'error', '-i', str(out), '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', str(mp4)])
    return mp4


def main(shot_path):
    shot = json.loads(Path(shot_path).read_text())
    name, fps, secs = shot['name'], shot.get('fps', 24), shot.get('seconds', 8)
    frames = int(round(fps * secs))
    plate = (ROOT / shot['plate']).resolve()
    if not plate.exists():
        raise SystemExit(f'no plate: {plate}')
    work = HERE / f'render/scratch/{name}'; shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    if shot.get('td_hud'):
        log('stage 2: TouchDesigner HUD on', plate.name); plate = td_pass(plate, frames, name)
    signals = None
    if shot.get('audio'):
        log('audio: analysing', shot['audio']); signals = audio_signals(ROOT / shot['audio'], fps, frames)
    srv, port = serve()
    rel = lambda p: 'http://127.0.0.1:%d/%s' % (port, Path(p).resolve().relative_to(ROOT).as_posix().replace(' ', '%20'))
    page = rel(HERE / 'studio.html')
    log('stage 3: studio', page)
    browse('goto', page); time.sleep(2)
    cfg = {k: shot[k] for k in ('preset', 'params', 'format', 'cues') if k in shot}
    if shot.get('audio'):                                              # hits for the beat engine: exact sidecar or detected
        sys.path.insert(0, str(HERE)); import beats; cfg['beats'] = beats.beatmap(ROOT / shot['audio'])
    cues = shot.get('cues') or []; bm = cfg.get('beats'); seqs = {}
    for k, p in enumerate(dict.fromkeys([str(plate)] + [str((ROOT / c['plate']).resolve()) for c in cues if c.get('plate')])):
        p = Path(p)
        if p.suffix.lower() in ('.mp4', '.mov', '.webm', '.m4v'):          # unpack video: exact frames, no seeking; a short clip yields fewer and loops
            d = work / f'src{k}'; d.mkdir()
            sh(['ffmpeg', '-y', '-v', 'error', '-i', str(p), '-vf', f'fps={fps}', '-frames:v', str(frames), '-q:v', '2', str(d / '%04d.jpg')])
            seqs[str(p)] = sorted(d.glob('*.jpg')); log(f'plate {p.name}: {len(seqs[str(p)])} frames')
        else:
            seqs[str(p)] = [p]

    def plate_at(t):                                                   # the clip under the playhead: the latest cue's, as in the studio
        bl, off, cur = 240 / (bm['bpm'] if bm else 120), bm['offset'] if bm else 0, None
        for c in cues:
            if off + c['bar'] * bl <= t + 0.02 and (cur is None or c['bar'] >= cur['bar']): cur = c
        return str((ROOT / cur['plate']).resolve()) if cur and cur.get('plate') else str(plate)
    seq = seqs[str(plate)]
    cfg.update(source=rel(seq[0]), fps=fps, seconds=secs, signals=signals)
    (work / 'cfg.json').write_text(json.dumps(cfg))
    res = browse('js', f"studio.load({json.dumps(cfg)}).then(r => JSON.stringify(r))")
    log('loaded', res.strip().splitlines()[-1][:200])
    t0 = time.time()
    for i in range(frames):
        s = seqs[plate_at(i / fps)]; arg = f', {json.dumps(rel(s[i % len(s)]))}'          # each clip loops under the timeline
        browse('js', f'studio.frame({i}{arg})', '--out', str(work / f'f{i:04d}.png'))
        if i % 48 == 0:
            log(f'frame {i}/{frames}  {time.time() - t0:.0f}s')
    srv.shutdown()
    missing = [i for i in range(frames) if not (work / f'f{i:04d}.png').exists()]
    if missing:
        raise SystemExit(f'{len(missing)} frames missing, first {missing[:5]}')
    out = HERE / f'render/{name}.mp4'
    cmd = ['ffmpeg', '-y', '-v', 'error', '-framerate', str(fps), '-i', str(work / 'f%04d.png')]
    if shot.get('audio'):
        cmd += ['-i', str(ROOT / shot['audio']), '-shortest', '-c:a', 'aac', '-b:a', '192k']
    cmd += ['-c:v', 'libx264', '-crf', '20', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(out)]
    sh(cmd)
    from PIL import Image
    picks = [Image.open(work / f'f{i:04d}.png').convert('RGB') for i in (0, frames // 3, 2 * frames // 3, frames - 1)]
    for p in picks:
        p.thumbnail((640, 640))
    sheet = Image.new('RGB', (picks[0].width * 2, picks[0].height * 2))
    for k, p in enumerate(picks):
        sheet.paste(p, ((k % 2) * p.width, (k // 2) * p.height))
    sheet.save(HERE / f'render/{name}-sheet.jpg', quality=82)
    log(f'done: {out.relative_to(ROOT)} ({frames} frames, {time.time() - t0:.0f}s in the studio)')


if __name__ == '__main__':
    main(sys.argv[1])
