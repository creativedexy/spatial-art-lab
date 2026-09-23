"""Serve the repo locally so studio.html can load the plates and shots, with byte ranges so video loops and seeks.

    python3 experiments/004-specimen-studio/serve.py        # then open the printed URL
Python's own http.server has no Range support, so browsers cannot seek or loop video from it.
"""
import http.server, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8790


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def end_headers(self):
        self.send_header('Accept-Ranges', 'bytes'); self.send_header('Cache-Control', 'no-store')
        super().end_headers()

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
