"""Sync test: do the picture's jolts land on the kicks?

    python3 experiments/004-specimen-studio/test_sync.py shots/beat-crystal-to-shards.json [--render]
Reads the rendered frames in render/scratch/<name>/ (--render runs make.py first). Motion energy = mean absolute
difference between consecutive frames. For every kick inside the shot, look within +-3 frames for the motion peak:
a hit if it stands clear of the local median (1.5x), lag = peak frame - kick frame. Passes at >= 80% hits and a
median lag within 1 frame. Exit code 1 on fail, so it can gate a batch.
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import beats


def motion(frames):
    prev, out = None, [0.0]
    for f in frames:
        a = np.asarray(Image.open(f).convert('L').resize((180, 320)), np.float32)
        if prev is not None: out.append(float(np.abs(a - prev).mean()))
        prev = a
    return np.array(out)


def main(argv):
    shot_path = Path(argv[0]) if Path(argv[0]).exists() else HERE / argv[0]
    shot = json.loads(shot_path.read_text())
    if '--render' in argv:
        subprocess.run([sys.executable, str(HERE / 'make.py'), str(shot_path)], check=True, capture_output=True)
    fps = shot.get('fps', 24); frames = sorted((HERE / 'render/scratch' / shot['name']).glob('f*.png'))
    if not shot.get('audio') or not frames:
        raise SystemExit('needs a shot with audio, rendered (add --render)')
    kicks = [k for k in beats.beatmap(ROOT / shot['audio'])['kick'] if 3 / fps < k < len(frames) / fps - 3 / fps]
    m = motion(frames); hits, lags = 0, []
    for k in kicks:
        f = int(round(k * fps)); lo, hi = max(1, f - 3), min(len(m), f + 4)
        j = lo + int(np.argmax(m[lo:hi])); base = np.median(m[max(1, f - 12):min(len(m), f + 12)]) + 1e-6
        if m[j] > 1.5 * base: hits += 1; lags.append(j - f)
    rate = hits / max(1, len(kicks)); lag = float(np.median(lags)) if lags else float('nan')
    ok = rate >= 0.8 and abs(lag) <= 1
    print(f"{shot['name']}: {len(kicks)} kicks, {hits} land ({rate:.0%}), median lag {lag:+.1f} frames -> {'PASS' if ok else 'FAIL'}")
    return ok


if __name__ == '__main__':
    sys.exit(0 if main(sys.argv[1:]) else 1)
