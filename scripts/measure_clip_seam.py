"""Score any descent clip against the anchor frames it was meant to hit.

Session C established the floor with a control clip rendered from the map's
own scene: ~0.5% mean pixel difference at both seams, of which almost all is
the codec. A generated clip is good enough when it lands near that floor, and
suspect the moment it drifts — five metres of landing error showed up as
2.5%, and 12% of the frame visibly different.

This needs nothing but the clip and the two PNGs, so it works on a laptop, in
a cloud session, or against a clip someone e-mails you.

Usage:
  python3 scripts/measure_clip_seam.py CLIP FRAME_A FRAME_B [--json out.json]

Reference numbers for the control clip (descent-control.webm):
  in-seam  0.478%   out-seam 0.464%   see descent/seam-report.json
"""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def extract(clip, where, dest):
    """Pull the first or last frame of a clip out as a PNG.

    For the last frame, decode the lot and let `-update` overwrite the same
    file frame after frame: whatever survives is genuinely the final one.
    Seeking from the end lands a few frames short, which quietly doubles the
    measured out-seam — the very number this script exists to report.
    """
    cmd = [ffmpeg(), "-y", "-v", "error", "-i", str(clip)]
    if where == "first":
        cmd += ["-frames:v", "1"]
    cmd += ["-update", "1", str(dest)]
    subprocess.run(cmd, check=True, capture_output=True)


def diff(a_path, b_path):
    import numpy as np
    from PIL import Image
    a = Image.open(a_path).convert("RGB")
    b = Image.open(b_path).convert("RGB")
    if a.size != b.size:                       # a clip may be delivered scaled
        a = a.resize(b.size, Image.LANCZOS)
    d = np.abs(np.asarray(a, dtype=np.int16) - np.asarray(b, dtype=np.int16))
    return {
        "meanPercent": round(float(d.mean()) / 255 * 100, 3),
        "peakPercent": round(float(d.max()) / 255 * 100, 1),
        "visiblePixelsPercent": round(float((d.max(axis=2) > 8).mean()) * 100, 2),
    }


def verdict(seam):
    if seam["meanPercent"] < 1.0:
        return "at the control floor — the cut will not show"
    if seam["meanPercent"] < 2.0:
        return "close; a 200 ms cross-fade should carry it"
    return "drifted — the hand-back will be visible, re-generate or re-anchor"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("clip")
    ap.add_argument("frame_a")
    ap.add_argument("frame_b")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        first, last = Path(tmp) / "first.png", Path(tmp) / "last.png"
        extract(args.clip, "first", first)
        extract(args.clip, "last", last)
        report = {
            "clip": args.clip,
            "inSeam": diff(first, args.frame_a),
            "outSeam": diff(last, args.frame_b),
        }

    for name, key in (("in-seam ", "inSeam"), ("out-seam", "outSeam")):
        s = report[key]
        print(f"{name}  mean {s['meanPercent']:>6}%  peak {s['peakPercent']:>5}%  "
              f"visible {s['visiblePixelsPercent']:>5}%   {verdict(s)}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()
