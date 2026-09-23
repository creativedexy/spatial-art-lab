"""TouchDesigner 2025: build the HUD network for the spider, record 10 s, quit.

Runs inside TouchDesigner from the boot Execute DAT that td/mktoe.py injects:
    python3 td/mktoe.py td/spider_hud.toe td/build_hud.py && open -n -a TouchDesigner --args td/spider_hud.toe
Open the .toe afterwards (without the boot DAT firing again, see README) to study the network.

Network, left to right in /project1:
  plate (Movie File In) -> level -> thresh (Threshold)          the machine's eye: only bright points survive
  hud (Script TOP, numpy)                                        tracks the bright tip dots and draws brackets,
                                                                 callout elbows, sidebar trace and scan sweep
  labels (Text TOP + spec DAT)                                   every word on screen, positioned per frame
  over (Composite) -> glow (Bloom) -> out (Movie File Out)
The tracker is plain Python (nearest-neighbour matching of blobs frame to frame), so the Blob Track TOP can
replace it later without touching the drawing.
"""
import os, math

ROOT = '/Users/user/Projects/3D Design/.claude/worktrees/mood-board-dark-geometric-339848/experiments/003-spider-probe'
PLATE = ROOT + '/render/probe-a-v002-clean.mp4'
OUT = ROOT + '/render/probe-a-v003-td.mov'
W, H, FRAMES = 1280, 720, 240
_io = ROOT + '/td/shot_io.json'                      # written by make.py: this shot's plate, output and length
if os.path.exists(_io):
    import json
    _j = json.load(open(_io)); PLATE = _j.get('plate', PLATE); OUT = _j.get('out', OUT); FRAMES = int(_j.get('frames', FRAMES))
p = op('/project1')
for c in list(p.children):
    if c.name != 'boot':
        c.destroy()


def mk(kind, name, x, y):
    n = p.create(kind, name); n.nodeX, n.nodeY = x * 180, -y * 140
    return n


plate = mk(moviefileinTOP, 'plate', 0, 0)
plate.par.file = PLATE
plate.par.playmode = 'specify'
plate.par.indexunit = 'frames'
plate.par.index.expr = "max(0, op('recorder').fetch('n', 1) - 1)"
plate.par.resolutionw, plate.par.resolutionh = W, H

level = mk(levelTOP, 'level', 1, 0); level.inputConnectors[0].connect(plate)
level.par.brightness1 = 1.0
thresh = mk(thresholdTOP, 'thresh', 2, 0); thresh.inputConnectors[0].connect(level)
thresh.par.threshold = 0.78

# --- the tracker and the line work: a Script TOP drawing into a numpy canvas -------------------------------
spec = mk(tableDAT, 'label_spec', 3, 2)
hud = mk(scriptTOP, 'hud', 3, 1)
hud.par.outputresolution = 'custom'; hud.par.resolutionw, hud.par.resolutionh = W, H
cb = op(hud.par.callbacks.eval()) if hud.par.callbacks.eval() else mk(textDAT, 'hud_callbacks', 3, 3)
hud.par.callbacks = cb.name
cb.text = r'''
import numpy as np, math
W, H = 1280, 720
state = {'tracks': {}, 'next': 1, 'trace': []}

def blobs(mask, ctx=None):
    """Lone bright points (leg-tip markers) on a 4x-downsampled mask -> list of (x, y, area) in pixels, y down.
    A blob counts only if it is at least 3 cells and its surroundings in ctx (the lit image) are mostly dark,
    which rejects the white patches on the abdomen and the tiny moss specks."""
    m = mask[::4, ::4] > 0.5
    ys, xs = np.nonzero(m)
    seen, out = set(), []
    pts = set(zip(ys.tolist(), xs.tolist()))
    for s in list(pts):
        if s in seen: continue
        stack, comp = [s], []
        seen.add(s)
        while stack:
            y, x = stack.pop(); comp.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (y + dy, x + dx)
                    if q in pts and q not in seen: seen.add(q); stack.append(q)
        if len(comp) >= 3:
            cy = sum(c[0] for c in comp) / len(comp); cx = sum(c[1] for c in comp) / len(comp)
            if ctx is not None:
                w = ctx[max(0, int(cy) - 6):int(cy) + 7, max(0, int(cx) - 6):int(cx) + 7]
                if w.mean() > 0.16: continue
            out.append((cx * 4, cy * 4, len(comp)))
    return out

def line(a, x0, y0, x1, y1, v=0.9):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.linspace(x0, x1, n).astype(int); ys = np.linspace(y0, y1, n).astype(int)
    ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    a[ys[ok], xs[ok], :3] = v; a[ys[ok], xs[ok], 3] = 1

def bracket(a, x, y, r, v):
    g = max(4, r * 0.45)
    for sx in (-1, 1):
        for sy in (-1, 1):
            line(a, x + sx * r, y + sy * r, x + sx * (r - g), y + sy * r, v)
            line(a, x + sx * r, y + sy * r, x + sx * r, y + sy * (r - g), v)

def onCook(scriptOp):
    frame = int(op('recorder').fetch('n', 1))
    mask = op('thresh').numpyArray()[::-1, :, 0]                 # TD arrays are bottom-up
    ctx = (op('level').numpyArray()[::-1, :, 0] > 0.3)[::4, ::4]
    found = blobs(mask, ctx)
    tr = state['tracks']
    for t in tr.values(): t['seen'] = False
    for (x, y, area) in sorted(found, key=lambda b: -b[2])[:24]:
        best = min(tr.items(), key=lambda kv: (kv[1]['x'] - x) ** 2 + (kv[1]['y'] - y) ** 2, default=None)
        if best and (best[1]['x'] - x) ** 2 + (best[1]['y'] - y) ** 2 < 40 ** 2 and not best[1]['seen']:
            t = best[1]; t['vx'] = x - t['x']; t['vy'] = y - t['y']; t['x'], t['y'] = x, y; t['age'] += 1; t['seen'] = True; t['lost'] = 0
        else:
            tr[state['next']] = {'x': x, 'y': y, 'vx': 0, 'vy': 0, 'age': 0, 'seen': True, 'lost': 0}; state['next'] += 1
    for k in list(tr):
        if not tr[k]['seen']:
            tr[k]['lost'] += 1
            if tr[k]['lost'] > 6: del tr[k]
    a = np.zeros((H, W, 4), np.float32)
    live = sorted((k, t) for k, t in tr.items() if t['lost'] == 0)
    rows = [['x', 'y', 'text']]
    for k, t in live:                                             # 1. lock-on: brackets tighten with confidence
        conf = min(1.0, t['age'] / 20)
        r = 34 - 22 * conf
        bracket(a, t['x'], t['y'], r, 1.0 if t['age'] < 3 else 0.55 + 0.35 * conf)
    for i, (k, t) in enumerate(live[:3]):                          # 2. elbowed callouts with live values
        ex, ey = t['x'] + 34, t['y'] - 42 - 18 * i
        line(a, t['x'] + 10, t['y'] - 10, ex, ey, 0.6); line(a, ex, ey, ex + 150, ey, 0.6)
        v = math.hypot(t['vx'], t['vy'])
        rows.append([ex + 4, ey - 6, f'T{k:02d}  V {v:04.1f}  CONF {min(1, t["age"] / 20):.2f}'])
    my = sum(t['y'] for _, t in live) / len(live) if live else H / 2
    state['trace'] = (state['trace'] + [my])[-150:]                # 3. telemetry sidebar: cadence trace
    x0 = W - 210
    line(a, x0, 90, x0, H - 90, 0.25)
    tr_ = state['trace']
    if len(tr_) > 2:
        lo, hi = min(tr_), max(tr_) + 1e-3
        for j in range(1, len(tr_)):
            line(a, x0 + 20 + (j - 1), 300 - 60 * (tr_[j - 1] - lo) / (hi - lo), x0 + 20 + j, 300 - 60 * (tr_[j] - lo) / (hi - lo), 0.8)
    rows += [[x0 + 20, 110, 'TELEMETRY'], [x0 + 20, 140, f'TRACKS  {len(live):02d}'], [x0 + 20, 165, f'IDS     {state["next"] - 1:03d}'],
             [x0 + 20, 215, 'CADENCE'], [x0 + 20, 330, 'ARANEAE'], [x0 + 20, 355, 'SUBSTRATE  MOSS']]
    sx = int((frame % 96) / 96 * (W - 260)) + 20                    # 4. scan sweep
    line(a, sx, 60, sx, H - 60, 0.45)
    rows.append([sx + 8, 70, 'SURFACE RESPONSE | MOSS'])
    s, f = divmod(frame - 1, 24)
    rows += [[28, 36, 'TRACK 3'], [W - 190, H - 30, f'00:00:{s:02d}:{f:02d}']]
    spec = op('label_spec'); spec.clear()
    spec.appendRow(rows[0])
    for x, y, t in rows[1:]: spec.appendRow([x, H - y, t])      # Text TOP measures y up from the bottom
    # the Text TOP reads label_spec one cook late, so show last frame's line-work: text and lines stay locked
    prev = state.get('prev', a); state['prev'] = a
    scriptOp.copyNumpyArray(prev[::-1].copy())
    return
'''

labels = mk(textTOP, 'labels', 3, 2)
labels.par.resolutionw, labels.par.resolutionh = W, H
labels.par.specdat = spec.name
labels.par.font = 'Menlo'
labels.par.fontsizex = 11
labels.par.fontcolorr = labels.par.fontcolorg = labels.par.fontcolorb = 0.85
labels.par.bgalpha = 0

over = mk(overTOP, 'over_hud', 4, 1); over.inputConnectors[0].connect(labels); over.inputConnectors[1].connect(hud)
comp = mk(overTOP, 'over_plate', 5, 0); comp.inputConnectors[0].connect(over); comp.inputConnectors[1].connect(plate)
glow = mk(nullTOP, 'glow', 6, 0); glow.inputConnectors[0].connect(comp)   # glow is added at encode, like v001/v002
out = mk(moviefileoutTOP, 'out', 7, 0); out.inputConnectors[0].connect(glow)
out.par.file = OUT
out.par.type = 'movie'

# --- offline render: cook every frame, record 1..240, then quit ------------------------------------------
tick = mk(executeDAT, 'recorder', 7, 2)
tick.store('n', 0)
tick.par.framestart = True
tick.text = f'''
def onFrameStart(frame):
    # own counter, so start-up time on the global clock cannot skip the take
    n = me.fetch('n', 0) + 1
    me.store('n', n)
    o = op('out')
    if n == 3:
        o.par.record = True
    if n >= {FRAMES + 3}:
        o.par.record = False
        project.quit(force=True)
    return
'''
project.realTime = False
project.cookRate = 24
