"""Post pass for the v002 trail look: ghost copies of earlier frames (the path through time)
plus a sparse monospace annotation layer. python3 post_trail.py -> render/scratch/post-####.png"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageEnhance

R = Path(__file__).resolve().parent / 'render/scratch'
GHOSTS = ((18, 0.50), (36, 0.30), (54, 0.18), (72, 0.10))      # (frames back, opacity)
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
frames = {n: Image.open(R / f'trail-{n:04d}.png').convert('RGB') for n in range(1, 241)}


def spaced(d, xy, text, anchor='la'):
    d.text(xy, ' '.join(text), font=font, fill=(200, 200, 200), anchor=anchor)


for n, im in frames.items():
    out = im.copy()
    for back, a in GHOSTS:
        if n - back >= 1:
            g = frames[n - back]
            r_, _, b_ = g.split()                     # only warm (gold) pixels leave a trail, not white lines or labels
            mask = ImageChops.subtract(r_, b_).point(lambda v: 255 if v > 40 else 0)
            ghost = Image.composite(ImageEnhance.Brightness(g).enhance(a), Image.new('RGB', g.size), mask)
            out = ImageChops.lighter(out, ghost)
    d = ImageDraw.Draw(out)
    spaced(d, (28, 26), 'ARANEAE'); spaced(d, (1252, 26), 'TRACK 3', 'ra')
    spaced(d, (28, 694), 'ID 07', 'ls')
    s, f = divmod(n - 1, 24)
    spaced(d, (1252, 694), f'00:00:{s:02d}:{f:02d}', 'rs')
    out.save(R / f'post-{n:04d}.png')
print('post frames', len(frames))
