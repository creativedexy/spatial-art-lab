"""Serve the repo locally so studio.html can load the plates and shots, with byte ranges so video loops and seeks.

    python3 experiments/004-specimen-studio/serve.py        # then open the printed URL
Python's own http.server has no Range support, so browsers cannot seek or loop video from it.
API (loopback only): GET /api/library lists plates, shots and audio; POST /api/presets merges into presets.json;
POST /api/shot writes shots/<name>.json. Drop new clips in plates/ and tracks in audio/; they appear on reload.
"""
import http.server, json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
HERE = ROOT / 'experiments/004-specimen-studio'
PLATE_DIRS = [ROOT / 'experiments/003-spider-probe/video/out', HERE / 'plates']
MEDIA = ('.mp4', '.mov', '.webm', '.m4v', '.png', '.jpg', '.jpeg')


def library():
    rel = lambda f: f.relative_to(ROOT).as_posix()
    plates = [{'label': f.stem, 'path': rel(f)} for d in PLATE_DIRS if d.exists() for f in sorted(d.iterdir()) if f.suffix.lower() in MEDIA]
    audio = [rel(f) for f in sorted((HERE / 'audio').glob('*')) if f.suffix.lower() in ('.wav', '.mp3', '.m4a', '.aif', '.aiff', '.flac', '.ogg')]
    return {'plates': plates, 'shots': sorted(f.stem for f in (HERE / 'shots').glob('*.json')), 'audio': audio}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes'); self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def _json(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.split('?')[0] == '/api/library':
            return self._json(200, library())
        if self.path.startswith('/api/beatmap?path='):                   # exact sidecar, or detected once and cached
            from urllib.parse import unquote
            f = (ROOT / unquote(self.path.split('=', 1)[1])).resolve()
            if ROOT not in f.parents or not f.exists():
                return self._json(404, {'error': 'no such audio'})
            sys.path.insert(0, str(HERE)); import beats
            return self._json(200, beats.beatmap(f))
        super().do_GET()

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        if self.path.startswith('/api/audio?name='):                   # a dropped track joins the library
            from urllib.parse import unquote
            name = re.sub(r'[^\w.-]+', '-', unquote(self.path.split('=', 1)[1]))[:120]
            if not name.lower().endswith(('.wav', '.mp3', '.m4a', '.aif', '.aiff', '.flac', '.ogg')):
                return self._json(400, {'error': 'not audio'})
            (HERE / 'audio' / name).write_bytes(raw); return self._json(200, {'path': f'experiments/004-specimen-studio/audio/{name}'})
        body = json.loads(raw or b'{}')
        if self.path == '/api/presets':                          # merge by name; never deletes
            f = HERE / 'presets.json'; cur = json.loads(f.read_text()) if f.exists() else {}
            cur.update(body); f.write_text(json.dumps(cur, indent=1)); return self._json(200, {'presets': len(cur)})
        if self.path == '/api/shot':
            name = re.sub(r'[^\w.-]+', '-', str(body.get('name', 'shot')))[:80] or 'shot'
            (HERE / 'shots' / f'{name}.json').write_text(json.dumps({**body, 'name': name}))
            return self._json(200, {'saved': f'shots/{name}.json'})
        self._json(404, {'error': 'unknown'})

    def send_head(self):
        m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range', ''))
        path = self.translate_path(self.path)
        if not m or not os.path.isfile(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2)))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        f = open(path, 'rb'); f.seek(start); self._left = end - start + 1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}'); self.send_header('Content-Length', str(self._left))
        self.end_headers()
        return f

    def copyfile(self, src, dst):
        try: self._copy(src, dst)
        except (BrokenPipeError, ConnectionResetError): pass                # the browser cancelled a video range: normal

    def _copy(self, src, dst):
        left = getattr(self, '_left', None)
        if left is None:
            return super().copyfile(src, dst)
        while left > 0:
            b = src.read(min(65536, left))
            if not b:
                break
            dst.write(b); left -= len(b)
        self._left = None

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    print(f'Specimen Studio: http://127.0.0.1:{PORT}/experiments/004-specimen-studio/studio.html', flush=True)
    http.server.ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
