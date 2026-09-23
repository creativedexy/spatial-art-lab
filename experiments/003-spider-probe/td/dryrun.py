"""Run build_hud.py's Script TOP callback outside TouchDesigner, on the clean plate frames, to test the
tracker and preview the HUD. Stubs stand in for op() and absTime; labels are drawn with PIL as the Text TOP
would. python3 td/dryrun.py [first last] -> render/scratch/dry-####.png"""
import re, sys, types
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent; R = HERE.parent / 'render/scratch'
src = (HERE / 'build_hud.py').read_text()
code = re.search(r"cb\.text = r'''(.*?)'''", src, re.S).group(1)
a, b = (int(x) for x in sys.argv[1:3]) if len(sys.argv) > 2 else (1, 240)


class Spec:
    rows = []
    def clear(self): self.rows = []
    def appendRow(self, r): self.rows.append(r)


class Thresh:
    arr = None
    def numpyArray(self): return self.arr


spec, thresh, level = Spec(), Thresh(), Thresh()
clock = types.SimpleNamespace(frame=1)
rec = types.SimpleNamespace(fetch=lambda k, dflt=None: clock.frame)
g = {'op': lambda n: {'label_spec': spec, 'thresh': thresh, 'level': level, 'recorder': rec}[n], 'absTime': clock}
exec(code, g)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
counts = []
for n in range(a, b + 1):
    clock.frame = n
    plate = Image.open(R / f'trail-clean-{n:04d}.png').convert('RGB')
    lum = np.asarray(plate, np.float32).mean(2) / 255
    thresh.arr = (lum > 0.82).astype(np.float32)[::-1, :, None].repeat(4, 2)   # TD arrays are bottom-up
    level.arr = lum[::-1, :, None].repeat(4, 2)
    out = {}
    g['onCook'](types.SimpleNamespace(copyNumpyArray=lambda arr: out.setdefault('a', arr)))
    hud = (out['a'][::-1] * 255).astype(np.uint8)
    im = plate.copy(); im.paste(Image.fromarray(hud[..., :3]), (0, 0), Image.fromarray(hud[..., 3]))
    d = ImageDraw.Draw(im)
    for x, y, t in spec.rows[1:]:
        d.text((x, y), str(t), font=font, fill=(215, 215, 215))
    im.save(R / f'dry-{n:04d}.png')
    counts.append(sum(1 for r in spec.rows if str(r[2]).startswith('TRACKS')) and int([r for r in spec.rows if str(r[2]).startswith('TRACKS')][0][2].split()[-1]))
print('frames', b - a + 1, 'tracks per frame min/mean/max', min(counts), round(sum(counts) / len(counts), 1), max(counts))
