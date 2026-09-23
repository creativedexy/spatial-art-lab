"""Beat maps: when every kick, snare and hat lands, plus tempo and the first downbeat.

    python3 experiments/004-specimen-studio/beats.py audio/track.wav      # prints a summary, writes track.beats.json
Our own tracks get an exact map from make_beats.py (a sidecar <track>.beats.json). Any other music is analysed here:
spectral flux per band (kick 30-90 Hz, snare 150-2500 Hz with noise, hat above 6 kHz), peak-picked; tempo from the
autocorrelation of the kick onsets. Used by serve.py (/api/beatmap) and make.py (headless renders).
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np

SR, HOP, N = 22050, 256, 1024


def load(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def onsets(flux, fps, min_gap, k=1.4):
    """Peaks of an onset curve above an adaptive threshold (local mean + k * local std), at least min_gap s apart."""
    w = max(3, int(fps * 0.4)); pad = np.pad(flux, w, mode='edge')
    loc = np.lib.stride_tricks.sliding_window_view(pad, 2 * w + 1)[:len(flux)]
    th = loc.mean(1) + k * loc.std(1); out = []; last = -1e9
    for i in range(1, len(flux) - 1):
        if flux[i] > th[i] and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1] and (i / fps - last) >= min_gap:
            out.append(i / fps); last = i / fps
    return out


def analyse(path):
    x = load(path); dur = len(x) / SR; fps = SR / HOP
    frames = np.lib.stride_tricks.sliding_window_view(np.pad(x, (0, N)), N)[::HOP] * np.hanning(N)
    mag = np.abs(np.fft.rfft(frames, axis=1)); f = np.fft.rfftfreq(N, 1 / SR)
    band = lambda a, b: np.log1p(mag[:, (f >= a) & (f < b)] * 10)
    flux = lambda m: np.maximum(0, np.diff(m, axis=0, prepend=m[:1])).sum(1)
    kick = onsets(flux(band(30, 90)), fps, 0.2, 2.0)                             # tuned on our exact maps: ~0.5 recall, ~0.45 precision
    snare = onsets(flux(band(150, 2500)) * 0.5 + flux(band(2500, 6000)), fps, 0.12, 1.6)
    snare = [s for s in snare if all(abs(s - k) > 0.03 for k in kick)]           # a snare on a kick is the kick's click
    hat = onsets(flux(band(6000, 11000)), fps, 0.05, 1.2)
    bpm = tempo(kick or hat, dur)
    return {'bpm': round(bpm, 2), 'offset': round(kick[0] if kick else 0.0, 4), 'duration': round(dur, 4), 'source': 'detected',
            'kick': [round(v, 4) for v in kick], 'snare': [round(v, 4) for v in snare], 'hat': [round(v, 4) for v in hat]}


def tempo(times, dur, lo=70, hi=180):
    if len(times) < 4:
        return 120.0
    fps = 100; env = np.zeros(int(dur * fps) + 1); env[(np.array(times) * fps).astype(int)] = 1
    ac = np.correlate(env, env, 'full')[len(env) - 1:]
    lags = np.arange(int(fps * 60 / hi), int(fps * 60 / lo) + 1)
    best = lags[np.argmax(ac[lags])]; bpm = 60 * fps / best
    while bpm < 90: bpm *= 2                                                     # prefer the 90-180 octave
    return bpm


def beatmap(path):
    """The sidecar map if there is one (exact, from make_beats.py), else analyse once and cache it beside the audio."""
    p = Path(path); side = p.with_suffix('.beats.json')
    if side.exists() and side.stat().st_mtime >= p.stat().st_mtime:
        return json.loads(side.read_text())
    m = analyse(p); side.write_text(json.dumps(m)); return m


if __name__ == '__main__':
    m = beatmap(sys.argv[1])
    print(f"{m['source']}: {m['bpm']} bpm, offset {m['offset']}s, {len(m['kick'])} kicks, {len(m['snare'])} snares, {len(m['hat'])} hats, {m['duration']}s")
