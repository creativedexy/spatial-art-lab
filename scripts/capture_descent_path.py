"""Render the descent path from the live scene and encode a control clip.

Why a control clip: the descent will eventually be generated video, and a
generated clip cannot be trusted to start and end exactly where the map is.
So first we prove the *machinery* with a clip that is perfect by construction
— rendered from the same WebGL scene the map runs — and measure what error
remains. Whatever that floor is (codec, colour, scaling), a generated clip
inherits it, and anything above it is the generator's drift.

Phases:
  1. capture  headless Chromium renders every frame of descent-path.json and
              POSTs each PNG here
  2. encode   ffmpeg builds a delivery WebM (VP9) + an MP4 for viewing, plus
              an all-but-lossless WebM used to separate codec error from
              geometry error
  3. measure  decode the clip with ffmpeg and compare its first and last
              frames against the renders — the seam, in numbers, written to
              seam-report.json

Measuring outside the browser is deliberate. The first version asked headless
Chromium to seek the clip and compare against its own canvas; 'seeked' fired
before the new frame was painted, so it compared frame 0 with the destination
and reported a 6.8% seam that did not exist. Decoding with ffmpeg has no such
ambiguity, and the browser render is bit-for-bit reproducible, so comparing
decoded frames against the captured renders measures the real thing.

Usage:  python3 scripts/capture_descent_path.py [--skip-capture] [--port 8137]
"""
import argparse
import http.server
import json
import shutil
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
DESCENT = SITE / "descent"
FRAMES = DESCENT / "path-frames"
CLIPS = DESCENT / "clips"
SHOT = "/tmp/claude-descent-last.png"
SHELL = Path("/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell")

state = {"done": None, "result": None, "frames": 0}


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(SITE), **kw)

    def log_message(self, *a):
        pass

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path.startswith("/__frame/"):
            (FRAMES / f"{self.path.rsplit('/', 1)[1]}.png").write_bytes(body)
            state["frames"] += 1
        elif self.path == "/__done":
            state["done"] = json.loads(body or b"{}")
        elif self.path == "/__result":
            state["result"] = json.loads(body or b"{}")
        self.send_response(204)
        self.end_headers()


def serve(port):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def browse(url, seconds=600):
    """Run one headless page long enough for it to finish posting."""
    return subprocess.Popen([
        str(SHELL), "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
        "--window-size=1400,900", f"--virtual-time-budget={seconds * 1000}",
        f"--screenshot={SHOT}", url,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_for(key, proc, label, timeout=600):
    t0 = time.time()
    while state[key] is None:
        if time.time() - t0 > timeout:
            proc.kill()
            raise SystemExit(f"timed out waiting for {label}")
        time.sleep(0.5)
    proc.kill()
    return state[key]


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def encode(spec):
    fps = spec["fps"]
    src = str(FRAMES / "%04d.png")
    CLIPS.mkdir(parents=True, exist_ok=True)
    out = {}
    jobs = [
        # Delivery: what a viewer would actually stream. crf 32 rather than
        # 24, measured rather than assumed — once the world had foliage and
        # roofs, crf 24 cost 5.09 MB for four seconds, and the whole curve is
        # this flat:
        #     crf 24  5.09 MB   in 0.644%  out 0.781%
        #     crf 32  2.87 MB   in 0.704%  out 0.940%
        # Halving the download costs 0.16 of a percentage point at the seam,
        # where five metres of landing drift costs seven. Bitrate is still not
        # what breaks a hand-off.
        ("descent-control.webm", ["-c:v", "libvpx-vp9", "-crf", "32", "-b:v", "0",
                                  "-row-mt", "1", "-pix_fmt", "yuv420p"]),
        # reference: codec error pushed as close to zero as VP9 goes
        ("descent-control-hq.webm", ["-c:v", "libvpx-vp9", "-lossless", "1",
                                     "-row-mt", "1", "-pix_fmt", "yuv420p"]),
        # portable: for viewing outside a Chromium build
        ("descent-control.mp4", ["-c:v", "libx264", "-crf", "18",
                                 "-preset", "slow", "-pix_fmt", "yuv420p"]),
    ]
    for name, args in jobs:
        dest = CLIPS / name
        cmd = [ffmpeg(), "-y", "-framerate", str(fps), "-i", src, *args, str(dest)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-1500:])
            raise SystemExit(f"ffmpeg failed for {name}")
        out[name] = dest.stat().st_size
        print(f"  {name}: {out[name] / 1e6:.2f} MB")
    return out


def frame_png(clip, index, dest):
    """Decode one frame of a clip to PNG, by frame number."""
    cmd = [ffmpeg(), "-y", "-v", "error", "-i", str(clip),
           "-vf", f"select=eq(n\\,{index})", "-vsync", "0", "-frames:v", "1", str(dest)]
    subprocess.run(cmd, check=True, capture_output=True)


def diff(a_path, b_path):
    """Mean and peak absolute RGB difference, plus how much of the frame a
    viewer could plausibly see as different (per-channel error over 3%)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(a_path).convert("RGB"), dtype=np.int16)
    b = np.asarray(Image.open(b_path).convert("RGB"), dtype=np.int16)
    d = np.abs(a - b)
    return {
        "meanPercent": round(float(d.mean()) / 255 * 100, 3),
        "peakPercent": round(float(d.max()) / 255 * 100, 1),
        "visiblePixelsPercent": round(float((d.max(axis=2) > 8).mean()) * 100, 2),
    }


def measure(spec, errors):
    frames = round(spec["durationSeconds"] * spec["fps"])
    tmp = FRAMES.parent / ".decoded"
    tmp.mkdir(exist_ok=True)
    rows = []
    for clip in ("descent-control.webm", "descent-control-hq.webm", "descent-control.mp4"):
        path = CLIPS / clip
        if not path.exists():
            continue
        first, last = tmp / "first.png", tmp / "last.png"
        frame_png(path, 0, first)
        frame_png(path, frames - 1, last)
        row = {
            "clip": clip,
            # in-seam: the clip's first frame against the map the viewer was
            # just looking at
            "inSeam": diff(first, FRAMES / "0000.png"),
            # out-seam: the clip's last frame against the map it hands back
            # to, at each landing error
            "outSeam": {e: diff(last, FRAMES / f"land-{e}.png") for e in errors
                        if (FRAMES / f"land-{e}.png").exists()},
        }
        rows.append(row)
    shutil.rmtree(tmp, ignore_errors=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8137)
    ap.add_argument("--skip-capture", action="store_true")
    ap.add_argument("--errors", default="0,5,10,20,40,60")
    args = ap.parse_args()

    spec = json.loads((DESCENT / "descent-path.json").read_text())
    base = f"http://127.0.0.1:{args.port}/descent/seam-test/index.html"
    serve(args.port)
    log = {"utc": datetime.now(timezone.utc).isoformat(), "path": spec}

    if not args.skip_capture:
        FRAMES.mkdir(parents=True, exist_ok=True)
        for old in FRAMES.glob("*.png"):
            old.unlink()
        print(f"capturing {round(spec['durationSeconds'] * spec['fps'])} frames…")
        proc = browse(f"{base}?capture=1&errors={args.errors}")
        done = wait_for("done", proc, "frame capture")
        print(f"  captured {state['frames']} frames ({done})")
        log["capture"] = {"frames": state["frames"]}

    print("encoding…")
    log["clipBytes"] = encode(spec)

    print("measuring seams…")
    log["seams"] = measure(spec, args.errors.split(","))
    for row in log["seams"]:
        print(f"  {row['clip']}: in-seam {row['inSeam']['meanPercent']}% "
              f"| out-seam at 0 m {row['outSeam']['0']['meanPercent']}%")

    (DESCENT / "seam-report.json").write_text(json.dumps(log, indent=2))
    print(f"wrote {DESCENT / 'seam-report.json'}")


if __name__ == "__main__":
    main()
