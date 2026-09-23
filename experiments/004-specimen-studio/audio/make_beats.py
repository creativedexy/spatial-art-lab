"""Synthesise heavy, loopable beat tracks for the studio's audio bindings: original, free, no samples.

    python3 experiments/004-specimen-studio/audio/make_beats.py        # writes the six WAVs beside this file
Each track is 16 bars, cut on the bar so it loops, peak-normalised to -1 dBFS. numpy only.
"""
import wave
from pathlib import Path
import numpy as np

SR = 44100
HERE = Path(__file__).resolve().parent
rng = np.random.default_rng(7)


def t(n):
    return np.arange(n) / SR


def env(n, a=0.002, d=0.2):                                       # attack then exponential decay (d = seconds to -60 dB-ish)
    x = t(n); e = np.exp(-x / max(d, 1e-4) * 6.9); k = int(a * SR)
    if k: e[:k] *= np.linspace(0, 1, k)
    return e


def lp(x, cut):                                                   # one-pole lowpass; cut may be an array (Hz) for sweeps
    cut = np.broadcast_to(np.asarray(cut, float), x.shape); a = 1 - np.exp(-2 * np.pi * cut / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def svf(x, cut, q=0.7):                                           # resonant state-variable lowpass (for wobble and acid)
    cut = np.broadcast_to(np.asarray(cut, float), x.shape); f = 2 * np.sin(np.pi * np.clip(cut, 20, SR / 6) / SR)
    lo = bp = 0.0; y = np.empty_like(x); d = 1 / q
    for i in range(len(x)):
        hi = x[i] - lo - d * bp; bp += f[i] * hi; lo += f[i] * bp; y[i] = lo
    return y


def hp(x, cut):
    return x - lp(x, cut)


def saw(freq, n, ph=0.0):
    f = np.broadcast_to(np.asarray(freq, float), (n,)); p = (np.cumsum(f) / SR + ph) % 1.0
    return 2 * p - 1


def sine(freq, n):
    f = np.broadcast_to(np.asarray(freq, float), (n,)); return np.sin(2 * np.pi * np.cumsum(f) / SR)


def drive(x, k):
    return np.tanh(x * k) / np.tanh(k)


# ---- drums ------------------------------------------------------------------------------------------
def kick(n=0.5, f0=160, f1=45, sweep=0.06, dist=1.5, click=0.4):
    m = int(n * SR); x = t(m); f = f1 + (f0 - f1) * np.exp(-x / sweep)
    k = sine(f, m) * env(m, 0.001, n)
    k[:int(0.004 * SR)] += click * rng.uniform(-1, 1, int(0.004 * SR))
    return drive(k, dist)


def snare(n=0.28, tone=190, noise=0.8, bright=1800):
    m = int(n * SR); body = sine(np.full(m, tone), m) * env(m, 0.001, 0.09)
    nz = hp(rng.uniform(-1, 1, m), bright) * env(m, 0.001, n) * noise
    return drive(body * 0.6 + nz, 1.8)


def clap(n=0.3):
    m = int(n * SR); nz = hp(rng.uniform(-1, 1, m), 1200); e = np.zeros(m)
    for o in (0, 0.011, 0.022):
        s = int(o * SR); e[s:] = np.maximum(e[s:], env(m - s, 0.0005, 0.12 if o == 0.022 else 0.02))
    return nz * e


def hat(n=0.05, cut=7000):
    m = int(n * SR); return hp(rng.uniform(-1, 1, m), cut) * env(m, 0.0005, n)


def clang(n=0.6, f=310):                                          # metallic FM hit
    m = int(n * SR); x = t(m); mod = np.sin(2 * np.pi * f * 2.41 * x) * 4 * env(m, 0, n * 0.5)
    return np.sin(2 * np.pi * f * x + mod) * env(m, 0.001, n)


def tom(n=0.7, f=85):
    m = int(n * SR); x = t(m); return drive(sine(f * (1 + 0.6 * np.exp(-x / 0.05)), m) * env(m, 0.002, n), 2.5)


# ---- sequencing -------------------------------------------------------------------------------------
class Track:
    def __init__(self, bpm, bars=16):
        self.bpm, self.bars = bpm, bars; self.step = 60 / bpm / 4; self.n = int(round(bars * 16 * self.step * SR))
        self.mix = np.zeros(self.n); self.duck = np.ones(self.n)

    def at(self, bar, step):                                      # sample index of a 16th step
        return int(round((bar * 16 + step) * self.step * SR))

    def put(self, s, i, g=1.0):
        if i >= self.n: return
        e = min(self.n, i + len(s)); self.mix[i:e] += s[:e - i] * g

    def pattern(self, sound, steps, g=1.0, bars=None, swing=0.0):
        for b in (bars if bars is not None else range(self.bars)):
            for st in steps:
                sh = int(swing * self.step * SR) if st % 2 else 0
                self.put(sound, self.at(b, st) + sh, g)

    def sidechain(self, steps, depth=0.7, rel=0.18, bars=None):
        for b in (bars if bars is not None else range(self.bars)):
            for st in steps:
                i = self.at(b, st); m = min(self.n - i, int(rel * SR * 1.5))
                if m > 0: self.duck[i:i + m] = np.minimum(self.duck[i:i + m], 1 - depth * np.exp(-t(m) / rel * 3))

    def layer(self, x, g=1.0, duck=True):
        x = x[:self.n]; self.mix[:len(x)] += x * g * (self.duck[:len(x)] if duck else 1)

    def write(self, name):
        x = self.mix - self.mix.mean(); x = drive(x / (np.abs(x).max() + 1e-9) * 1.4, 1.2)
        x = x / np.abs(x).max() * 10 ** (-1 / 20)
        st = np.stack([x, np.roll(x, int(0.00035 * SR)) * 0.98], 1)   # a hair of width
        with wave.open(str(HERE / name), 'wb') as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
        print(f'{name}: {self.bpm} bpm, {self.bars} bars, {self.n / SR:.1f}s')


def notes(tr, seq, f_of, dur_steps):                              # a per-sample frequency curve from a step sequence
    f = np.zeros(tr.n)
    for b in range(tr.bars):
        for st, note in seq(b):
            i = tr.at(b, st); f[i:min(tr.n, i + int(dur_steps * tr.step * SR))] = f_of(note)
    return f


hz = lambda m: 440 * 2 ** ((m - 69) / 12)


# ---- tracks -----------------------------------------------------------------------------------------
def pulse():                                                      # techno 128: four-on-the-floor, rumble, acid line opening up
    tr = Track(128); K = kick(0.45, 170, 48, 0.05, 2.2)
    tr.pattern(K, [0, 4, 8, 12], 1.0); tr.sidechain([0, 4, 8, 12], 0.75, 0.2)
    tr.pattern(hat(0.16, 6000), [2, 6, 10, 14], 0.35); tr.pattern(hat(0.03, 9000), range(16), 0.12, bars=range(4, 16))
    tr.pattern(clap(), [4, 12], 0.5, bars=range(4, 16))
    rumble = lp(rng.uniform(-1, 1, tr.n), 90) * 6; tr.layer(drive(rumble, 2) * 0.5)
    line = [36, 36, 48, 36, 39, 36, 36, 51, 36, 36, 48, 43, 36, 39, 36, 46]
    f = notes(tr, lambda b: [(s, line[s]) for s in range(16)] if b >= 4 else [], hz, 0.9)
    gate = (f > 0).astype(float); cut = 300 + 2600 * (0.5 + 0.5 * np.sin(2 * np.pi * t(tr.n) / (tr.n / SR / 2))) * np.linspace(0.2, 1, tr.n)
    tr.layer(drive(svf(saw(np.maximum(f, 1), tr.n) * gate, cut, 4), 2.5) * 0.45)
    tr.write('pulse-techno-128.wav')


def wobble():                                                     # halftime 140: kick, slam snare, distorted wobble bass
    tr = Track(140); K = kick(0.5, 150, 42, 0.07, 3); S = snare(0.35, 180, 1.0, 1500)
    tr.pattern(K, [0, 10], 1.0, bars=range(2, 16)); tr.pattern(S, [8], 1.0, bars=range(2, 16)); tr.sidechain([0, 10], 0.6, 0.15, bars=range(2, 16))
    tr.pattern(hat(0.04, 8000), [2, 6, 10, 14], 0.2); tr.pattern(hat(0.02, 9000), [3, 7, 11, 13, 15], 0.1, bars=range(8, 16))
    roots = [29, 29, 32, 27]
    f = notes(tr, lambda b: [(0, roots[b % 4])], hz, 16)
    rate = np.where((np.arange(tr.n) // int(tr.step * 8 * SR)) % 4 == 3, 3.0, 1.0)   # 1/4-note wobble, faster every 4th half-bar
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(rate * tr.bpm / 60 / 2) / SR)
    raw = saw(f, tr.n) + saw(f * 1.007, tr.n) + 0.6 * np.sign(sine(f / 2, tr.n))
    wob = drive(svf(raw, 120 + 2400 * lfo ** 2, 3), 3.5)
    sub = sine(f / 2, tr.n) * 0.8
    tr.layer((wob * 0.4 + sub) * np.r_[np.linspace(0, 1, tr.at(2, 0)), np.ones(tr.n - tr.at(2, 0))], 0.9)
    tr.write('wobble-halftime-140.wav')


def breakneck():                                                  # drum & bass 172: broken beat, ghost snares, reese bass
    tr = Track(172); K = kick(0.35, 180, 50, 0.04, 1.8); S = snare(0.25, 210, 1.0, 2200); G = snare(0.1, 230, 0.5, 3000)
    tr.pattern(K, [0, 10], 1.0); tr.pattern(S, [4, 12], 1.0); tr.pattern(G, [7, 9, 15], 0.28, bars=range(2, 16))
    tr.pattern(K, [2], 0.7, bars=range(1, 16, 2)); tr.pattern(hat(0.03, 8000), range(0, 16, 2), 0.22); tr.pattern(hat(0.015, 10000), range(1, 16, 2), 0.1)
    tr.sidechain([0, 10], 0.45, 0.12)
    roots = [26, 26, 29, 24]
    f = notes(tr, lambda b: [(0, roots[(b // 2) % 4])], hz, 32)
    reese = saw(f, tr.n) + saw(f * 1.012, tr.n, 0.3) + saw(f * 0.993, tr.n, 0.6)
    tr.layer(drive(lp(reese, 380 + 260 * np.sin(2 * np.pi * t(tr.n) * 0.25) ** 2), 2.2) * 0.5 + sine(f, tr.n) * 0.5, 0.9)
    tr.write('breakneck-dnb-172.wav')


def night808():                                                   # trap 140 (halftime feel): rolling hats, sliding 808s, hard snare
    tr = Track(140); S = snare(0.3, 200, 0.9, 1800)
    tr.pattern(S, [8], 1.0); tr.pattern(clap(), [8], 0.5)
    for b in range(tr.bars):                                      # hats: 8ths with triplet and 32nd rolls
        for st in range(0, 16, 2): tr.put(hat(0.03, 8500), tr.at(b, st), 0.25)
        if b % 2: [tr.put(hat(0.02, 9000), tr.at(b, 12) + int(k * tr.step / 3 * 2 * SR), 0.18) for k in range(6)]
        if b % 4 == 3: [tr.put(hat(0.015, 9500), tr.at(b, 14) + int(k * tr.step / 2 * SR), 0.16) for k in range(4)]
    hits = [(0, 31, 6), (6, 31, 3), (10, 34, 4), (14, 29, 2)]
    f = np.zeros(tr.n); gate = np.zeros(tr.n)
    for b in range(tr.bars):
        for st, m, dur in hits:
            i = tr.at(b, st); L = int(dur * tr.step * SR); e = min(tr.n, i + L)
            glide = hz(m) * (1 + 0.5 * np.exp(-t(e - i) / 0.03)) if st else np.full(e - i, hz(m))
            if st == 14 and b % 2: glide = np.linspace(hz(m), hz(m + 5), e - i)          # the slide
            f[i:e] = glide; gate[i:e] = env(e - i, 0.002, dur * tr.step * 1.2)
            tr.put(kick(0.12, 200, 60, 0.02, 1.2), i, 0.8)
    tr.layer(drive(sine(np.maximum(f, 1), tr.n) * gate, 3.0), 1.0, duck=False)
    tr.write('808-night-140.wav')


def hammer():                                                     # industrial hard 150: distorted kick tails, clangs, noise bursts
    tr = Track(150); K = kick(0.55, 200, 52, 0.035, 6.0)
    tr.pattern(K, [0, 4, 8, 12], 1.0, bars=range(1, 16)); tr.sidechain([0, 4, 8, 12], 0.5, 0.2, bars=range(1, 16))
    tr.pattern(clang(0.5, 330), [6], 0.45, bars=range(2, 16, 2)); tr.pattern(clang(0.7, 247), [14], 0.4, bars=range(3, 16, 2))
    burst = hp(rng.uniform(-1, 1, int(0.12 * SR)), 900) * env(int(0.12 * SR), 0.001, 0.12)
    tr.pattern(burst, [3, 11], 0.4, bars=range(4, 16)); tr.pattern(hat(0.05, 5000), [2, 6, 10, 14], 0.3)
    drone = drive(lp(saw(np.full(tr.n, hz(28)), tr.n) + saw(np.full(tr.n, hz(28) * 1.5 * 1.004), tr.n), 400), 4) * 0.25
    tr.layer(drone * np.linspace(0.3, 1, tr.n))
    tr.write('hammer-industrial-150.wav')


def braam():                                                      # cinematic heavy 90: braam hits, sub drops, war toms, riser
    tr = Track(90); chord = [26, 33, 38, 41]
    for b in range(0, tr.bars, 2):
        i = tr.at(b, 0); m = int(tr.step * 16 * 1.8 * SR); x = np.zeros(m)
        for n_ in chord:
            for dt in (1.0, 1.006, 0.994): x += saw(np.full(m, hz(n_) * dt), m)
        e = env(m, 0.02, 3.2); x = drive(lp(x, 350 + 3500 * e), 3) * e
        sub = sine(hz(26) / 2 * (1 + 0.8 * np.exp(-t(m) / 0.15)), m) * env(m, 0.005, 2.5)
        tr.put(x * 0.35 + sub * 0.9, i)
    tr.pattern(tom(0.8, 80), [0, 3, 6], 0.7, bars=range(4, 16)); tr.pattern(tom(0.6, 110), [10, 11, 13], 0.5, bars=range(8, 16))
    tr.pattern(snare(0.5, 150, 1.2, 1200), [8], 0.8, bars=range(8, 16))
    rise_n = tr.at(4, 0); riser = hp(rng.uniform(-1, 1, rise_n), 2000) * np.linspace(0, 1, rise_n) ** 3
    tr.put(riser * 0.4, tr.at(12, 0))
    tr.write('braam-cinematic-90.wav')


if __name__ == '__main__':
    for f in (pulse, wobble, breakneck, night808, hammer, braam):
        f()
