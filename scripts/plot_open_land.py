"""A site plan of the undeveloped parcels, for arguing over.

Phase 6 groundwork. find_open_land.py produces a table, and a table is the
wrong shape for deciding where something should go. This draws the same data
as a plan: the surveyed land cover underneath, every parcel of 1.5 ha or more
picked out and numbered, the two named routes that cross the box, and GCHQ,
which is the reason any of it is happening.

Usage:  python3 scripts/plot_open_land.py [--min-hectares 1.5]
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
VISION = GV.parent / "vision"
FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-{}.ttf"
SCALE = 0.55                  # output pixels per metre of ground
PANEL = 430                   # width of the legend panel, in output pixels

INK = (41, 48, 42)
PAPER = (247, 242, 230)
AMBER = (164, 97, 31)
SLATE = (74, 111, 138)


def font(weight="Regular", size=13):
    return ImageFont.truetype(FONT.format(weight), size)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-hectares", type=float, default=1.5)
    ap.add_argument("--out", default=str(VISION / "open-land.png"))
    args = ap.parse_args()

    meta = json.loads((GV / "gv-landcover.json").read_text())
    gvmeta = json.loads((GV / "gv-meta.json").read_text())
    paths = json.loads((GV / "gv-paths.json").read_text())
    sites = json.loads((VISION / "open-land.json").read_text())["sites"]
    sites = [s for s in sites if s["hectares"] >= args.min_hectares]

    W = gvmeta["widthMetres"]
    size = int(W * SCALE)
    # The land cover itself as the base, lifted towards paper so that anything
    # drawn on top reads as annotation rather than as more landscape.
    base = Image.open(GV / meta["colourFile"]).convert("RGB").resize(
        (size, size), Image.LANCZOS)
    base = Image.blend(base, Image.new("RGB", base.size, PAPER), 0.55)

    img = Image.new("RGB", (size + PANEL, size), PAPER)
    img.paste(base, (0, 0))
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    # Local metres (x east, z south from the centre) to output pixels.
    to_px = lambda x, z: ((x + W / 2) * SCALE, (z + W / 2) * SCALE)

    # True parcel shapes, from the index image find_open_land.py stamps.
    stamp = np.array(Image.open(VISION / "open-land-parcels.png"))
    shapes = Image.fromarray(
        np.where(stamp[:, :, None] > 0,
                 np.array(AMBER + (58,), dtype=np.uint8),
                 np.zeros(4, dtype=np.uint8)).astype(np.uint8), "RGBA")
    over.alpha_composite(shapes.resize((size, size), Image.NEAREST))
    # Edges, found by comparing each cell with its neighbour.
    edge = np.zeros(stamp.shape, bool)
    edge[:-1, :] |= stamp[:-1, :] != stamp[1:, :]
    edge[:, :-1] |= stamp[:, :-1] != stamp[:, 1:]
    edge &= stamp > 0
    outline = Image.fromarray(
        np.where(edge[:, :, None],
                 np.array(AMBER + (235,), dtype=np.uint8),
                 np.zeros(4, dtype=np.uint8)).astype(np.uint8), "RGBA")
    over.alpha_composite(outline.resize((size, size), Image.NEAREST))
    d = ImageDraw.Draw(over)

    for lm in paths.get("landmarks", []):
        if lm["kind"] in ("stream", "river", "ditch", "drain"):
            d.line([to_px(*p) for p in lm["points"]], fill=SLATE + (190,), width=2)
    for r in paths["routes"]:
        if r["tier"] == "named":
            d.line([to_px(*p) for p in r["points"]], fill=(120, 62, 16, 255), width=3)

    gx, gz = to_px(123, 64)
    for i, s in enumerate(sites, 1):
        x, z = s["centreLocal"]
        cx, cz = to_px(x, z)
        # Parcel 5 is GCHQ's own grounds, so its centre and the building's
        # marker are the same point. Nudge the badge rather than stack them.
        if math.hypot(cx - gx, cz - gz) < 34:
            cx, cz = cx - 30, cz - 26
        d.ellipse([cx - 15, cz - 15, cx + 15, cz + 15], fill=PAPER + (240,),
                  outline=INK + (255,), width=2)
        t = str(i)
        tb = d.textbbox((0, 0), t, font=font("Bold", 16))
        d.text((cx - (tb[2] - tb[0]) / 2, cz - (tb[3] - tb[1]) / 2 - 3), t,
               font=font("Bold", 16), fill=INK + (255,))

    d.ellipse([gx - 9, gz - 9, gx + 9, gz + 9], outline=INK + (255,), width=3)
    d.text((gx + 16, gz + 12), "GCHQ", font=font("Bold", 15), fill=INK + (255,))

    img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
    d = ImageDraw.Draw(img)

    # --- the panel ---------------------------------------------------------
    x = size + 26
    y = 30
    d.text((x, y), "West Cheltenham", font=font("Bold", 22), fill=INK)
    y += 30
    d.text((x, y), "undeveloped parcels, 1.5 ha and over",
           font=font("Regular", 14), fill=(98, 107, 94))
    y += 24
    d.text((x, y), "measured from the land-cover survey at 4 m cells,",
           font=font("Regular", 12), fill=(98, 107, 94))
    y += 16
    d.text((x, y), "cut by every hedgerow and watercourse",
           font=font("Regular", 12), fill=(98, 107, 94))
    y += 34

    cols = [(0, "#"), (26, "ha"), (76, "slope"), (132, "face"), (176, "to GCHQ"), (250, "road")]
    for dx, label in cols:
        d.text((x + dx, y), label, font=font("Bold", 11), fill=INK)
    y += 18
    d.line([x, y, x + PANEL - 52, y], fill=(41, 48, 42, 60), width=1)
    y += 8
    for i, s in enumerate(sites, 1):
        vals = [str(i), f"{s['hectares']:.1f}", f"{s['meanSlopeDegrees']:.1f}°",
                s["aspect"], f"{s['toGchqMetres']} m",
                f"{s['roadFrontageMetres']} m"]
        for (dx, _), v in zip(cols, vals):
            d.text((x + dx, y), v, font=font("Regular", 12), fill=INK)
        y += 20

    y += 18
    d.line([x, y, x + PANEL - 52, y], fill=(41, 48, 42, 60), width=1)
    y += 14
    for swatch, label in (((120, 62, 16), "named route — Circular, Cycle Spine"),
                          (SLATE, "watercourse")):
        d.line([x, y + 7, x + 22, y + 7], fill=swatch, width=3)
        d.text((x + 32, y), label, font=font("Regular", 12), fill=INK)
        y += 22

    y += 10
    for line in ("Parcel 1 is the allocation itself: 79 ha, and it barely",
                 "splits. Fifty-four hedgerows were cut through the mask",
                 "and it stayed one field over a kilometre across — the",
                 "grain a scheme here would normally hold on to has",
                 "already been ploughed out."):
        d.text((x, y), line, font=font("Regular", 12), fill=(98, 107, 94))
        y += 17

    d.text((x, size - 40), "Environment Agency LiDAR · OpenStreetMap",
           font=font("Regular", 10), fill=(140, 146, 136))

    out = Path(args.out)
    img.save(out)
    print(f"wrote {out.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}, "
          f"{out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
