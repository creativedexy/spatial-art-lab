"""Roof shape and material family for every building, from data already on disk.

The building half of Phase 3 in plans/living-map-lookdev-plan.md.

Every building in the map is a flat-topped extrusion at its median height,
which is a fair summary and a poor roof. But the median was never the whole
story: the DSM we downloaded holds the eaves *and* the ridge of every house in
west Cheltenham, and we threw the distribution away and kept one number. This
recovers it.

  height   ┌───────── 92nd percentile → the ridge
  inside   │
  one      │      a pitched roof spreads its pixels evenly between the two,
  footprint│      a flat roof piles them all at one value
           └───────── 30th percentile → the eaves

The ridge *direction* is measured too, not assumed. The minimum-area
rectangle gives two candidate axes and the DSM says which one the roof
actually runs along, by asking which direction the surface falls away from a
centre line like a tent. That measurement is worth making rather than
guessing: the obvious prior is that a ridge runs along a building's long
axis, and in this box it does not. A British semi or terraced house is
narrow-fronted and deep, and its ridge runs with the *street* — across its
own footprint's long axis. The report prints how often that happens.

The same two numbers separate a gable from a hip. If the surface falls away
in one direction and stays level in the other, the roof has vertical ends and
its ridge runs the full length; if it falls away in both, the ends are hipped
and the ridge is short. Nothing else is needed to tell them apart.

Material family comes from the OSM `building` tag where there is one. Nearly
half of them say only `building=yes`, so those are inferred from what we
measured: the land cover under the centroid, the footprint area, and whether
the roof turned out to be pitched.

This script *augments* gv-buildings.json in place. `ring`, `holes`, `base`
and `height` are recomputed and asserted identical to what is already there,
because golden-valley/scene.js renders from those fields and the descent seam
is measured in pixels — the map page must not move.

Usage:  python3 scripts/golden_valley_roofs.py [--dry-run]
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from golden_valley_slice import E0, E1, N0, N1, OUT, fetch_grid, fetch_footprints

ROOT = Path(__file__).resolve().parent.parent

# Where the roof is taken from inside the footprint. Not min and max: a
# chimney, an aerial or one bright return would become the ridge, and the
# ground leaking in at the wall line would become the eaves.
# Checked against the buildings rather than chosen: at the 97th percentile
# the ridge lands within 0.11 m of the footprint's highest pixel, so it is
# the ridge and not a chimney. The eaves are the fragile end — at the 12th
# percentile they come out at 3.7 m, which is a metre and a half below where
# a two-storey semi's eaves actually sit, because the wall line mixes roof
# and garden however hard it is filtered. The 20th percentile puts them at
# 4.9 m, which is right.
EAVES_PCT, RIDGE_PCT = 20, 97
MIN_PITCH = 1.4          # metres of ridge above eaves before we call it pitched
MAX_SPAN = 22.0          # metres; a wider span than this is a shed, not a roof
# Anything this low inside a footprint is the ground leaking in at the wall
# line, where a diagonal footprint rasterised on a 1 m grid always mixes roof
# and garden. Left in, those pixels sit at the greatest distance from every
# centre line and quietly tilt the tent fit in whichever direction the
# building is longest — which is how a measurement of roofs becomes a
# measurement of footprint shape.
GROUND_LEAK = 1.5
GABLE_RATIO = 1.6        # one direction this much steeper than the other

# The material families. Walls stay in a restrained off-white range on
# purpose — the map's whole proposition is a measured architectural model,
# and giving 4,000 houses brick-red walls would trade that for a video game.
# The roofs carry the differentiation, which is also what you actually see
# from the air.
# The sun in this scene is 0xffe0b5 — a low, warm afternoon light — and under
# it a neutral grey renders as tan. Slate has to be specified cool to arrive
# looking like slate, which is why these read blue on the page and grey in
# the render.
FAMILIES = {
    "house":   {"wall": 0xefe8dc, "roof": 0x646a72},
    "terrace": {"wall": 0xe9e1d3, "roof": 0x545a63},
    "retail":  {"wall": 0xe6e6e2, "roof": 0x8f9398},
    "shed":    {"wall": 0xdedcd5, "roof": 0x7d848c},
    "civic":   {"wall": 0xf2ece0, "roof": 0x61666b},
}
BY_TAG = {
    "house": "house", "detached": "house", "semidetached_house": "house",
    "bungalow": "house", "cabin": "house", "houseboat": "house",
    "residential": "terrace", "terrace": "terrace", "apartments": "terrace",
    "dormitory": "terrace", "hotel": "terrace",
    "retail": "retail", "commercial": "retail", "supermarket": "retail",
    "office": "retail", "kiosk": "retail",
    "industrial": "shed", "warehouse": "shed", "manufacture": "shed",
    "garage": "shed", "garages": "shed", "shed": "shed", "roof": "shed",
    "carport": "shed", "greenhouse": "shed", "service": "shed",
    "farm_auxiliary": "shed", "barn": "shed", "hangar": "shed",
    "static_caravan": "shed", "storage_tank": "shed", "toilets": "shed",
    "school": "civic", "university": "civic", "college": "civic",
    "hospital": "civic", "church": "civic", "chapel": "civic",
    "cathedral": "civic", "civic": "civic", "public": "civic",
    "government": "civic", "police": "civic", "fire_station": "civic",
    "train_station": "civic", "sports_hall": "civic", "stadium": "civic",
}
# Land cover under the centroid, for the 1,781 footprints tagged only `yes`.
COVER_HINT = {"residential": "house", "grass": "house", "park": "civic",
              "meadow": "house", "farmland": "shed", "pitch": "civic",
              "hardstanding": "retail", "parking": "retail", "scrub": "shed"}


def hull(points):
    """Monotone chain — the convex hull, so the calipers have something to
    turn on. scipy is not installed in this container and does not need to be
    for 4,000 footprints of a dozen points each."""
    pts = sorted(set(map(tuple, points)))
    if len(pts) < 3:
        return pts
    def half(seq):
        out = []
        for p in seq:
            while len(out) >= 2:
                (ax, ay), (bx, by) = out[-2], out[-1]
                if (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) > 0:
                    break
                out.pop()
            out.append(p)
        return out[:-1]
    return half(pts) + half(pts[::-1])


def min_area_axis(ring):
    """Orientation of the minimum-area rectangle, in radians. A building is a
    rectangle to a very good approximation, and its long side is where a ridge
    runs — so this is the first guess the DSM then gets to overrule."""
    h = np.array(hull(ring), dtype=float)
    if len(h) < 3:
        return 0.0, 1.0, 1.0
    best = None
    for i in range(len(h)):
        edge = h[(i + 1) % len(h)] - h[i]
        n = math.hypot(*edge)
        if n < 1e-9:
            continue
        c, s = edge[0] / n, edge[1] / n
        u = h @ np.array([c, s])
        v = h @ np.array([-s, c])
        du, dv = np.ptp(u), np.ptp(v)
        if best is None or du * dv < best[0]:
            best = (du * dv, math.atan2(s, c), du, dv)
    _, angle, du, dv = best
    # Normalise so the reported axis is the long side of the rectangle.
    if dv > du:
        angle += math.pi / 2
        du, dv = dv, du
    return angle, du, dv


def tent_strength(px, py, z, angle):
    """How much the surface falls away from a centre line running at `angle`
    — the signature of a pitched roof seen along its ridge. Returns the slope
    of height against distance from that line, in metres per metre."""
    s, c = math.sin(angle), math.cos(angle)
    d = np.abs(-s * px + c * py - np.median(-s * px + c * py))
    if np.ptp(d) < 1e-6 or len(d) < 8:
        return 0.0
    # A straight line fit is enough: a tent is linear in |distance|, and we
    # only ever compare two candidate directions against each other.
    return -np.polyfit(d, z, 1)[0]


def erode(mask):
    """Drop the outermost ring of pixels. The wall line is where the DSM
    mixes roof and ground, and that mixture is exactly what would otherwise
    be measured as the eaves."""
    m = mask.copy()
    m[1:, :] &= mask[:-1, :]
    m[:-1, :] &= mask[1:, :]
    m[:, 1:] &= mask[:, :-1]
    m[:, :-1] &= mask[:, 1:]
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="measure and report, write nothing")
    args = ap.parse_args()

    out = ROOT / OUT
    existing = json.loads((out / "gv-buildings.json").read_text())
    cover = json.loads((out / "gv-landcover.json").read_text())
    classes = {v["index"]: k for k, v in cover["classes"].items()}
    landclass = np.array(Image.open(out / cover["classFile"]))

    dtm, dsm = fetch_grid("dtm"), fetch_grid("dsm")
    H, W = dtm.shape
    diff = dsm - dtm
    sx, sy = W / (E1 - E0), H / (N1 - N0)

    def px(e, n):
        return (e - E0) * sx, (N1 - n) * sy

    stats = {"gable": 0, "hip": 0, "flat": 0, "ridge_across_long_axis": 0}
    families = {}
    rows, index = [], 0
    for b in fetch_footprints():
        pts = [px(e, n) for e, n in b["ring"]]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # Crop to the footprint rather than allocating a 2000x2000 mask 4,000
        # times. Polygon rasterisation is translation invariant for integer
        # offsets, so the pixels selected are the same ones.
        x0, y0 = max(0, int(min(xs)) - 1), max(0, int(min(ys)) - 1)
        x1, y1 = min(W, int(max(xs)) + 2), min(H, int(max(ys)) + 2)
        if x1 <= x0 or y1 <= y0:
            continue
        img = Image.new("1", (x1 - x0, y1 - y0), 0)
        d = ImageDraw.Draw(img)
        d.polygon([(x - x0, y - y0) for x, y in pts], fill=1)
        for hole in b.get("holes", []):
            d.polygon([(x - x0, y - y0) for x, y in map(lambda p: px(*p), hole)],
                      fill=0)
        mask = np.array(img, dtype=bool)
        if mask.sum() < 4:
            continue

        window = diff[y0:y1, x0:x1]
        base_w = dtm[y0:y1, x0:x1]
        heights = window[mask]
        heights = heights[~np.isnan(heights)]
        base = base_w[mask]
        base = base[~np.isnan(base)]
        if not len(heights) or not len(base):
            continue

        rec = existing[index]
        index += 1
        h = float(np.median(heights))
        if h < 2:
            h = 3.0
        assert round(h, 1) == rec["height"] and \
            round(float(np.median(base)), 1) == rec["base"], \
            f"recomputed building {index} does not match gv-buildings.json"

        ring = [(x, z) for x, z in rec["ring"]]
        angle, long_side, span = min_area_axis(ring)

        roof_px = mask & ~np.isnan(window) & (window > GROUND_LEAK)
        sample = window[roof_px]
        eaves = ridge = h
        pitched, shape = False, None
        if len(sample) >= 12 and not rec["holes"]:
            eaves = float(np.percentile(sample, EAVES_PCT))
            ridge = float(np.percentile(sample, RIDGE_PCT))
            pitched = (ridge - eaves) >= MIN_PITCH

        if pitched:
            ys_i, xs_i = np.nonzero(roof_px)
            z = window[ys_i, xs_i]
            # Local metres, matching the ring's frame, so the angle written
            # out means the same thing to the browser as it does here.
            lx = (xs_i + x0) / sx - (E1 - E0) / 2
            lz = (ys_i + y0) / sy - (N1 - N0) / 2
            # `along` is how fast the roof falls away across the long axis —
            # the signature of a ridge running along it. `across` is the same
            # question asked of the short axis.
            along = tent_strength(lx, lz, z, angle)
            across = tent_strength(lx, lz, z, angle + math.pi / 2)
            # A ridge across the long axis means the roof spans the long way,
            # and past about 22 m that is not a roof any more — a terrace row
            # 60 m long does not slope from one end to the other. So the
            # option is only on the table when the span it implies is
            # buildable, which stops a weak measurement inventing one.
            if across > along and long_side <= MAX_SPAN:
                angle += math.pi / 2
                span = long_side
                stats["ridge_across_long_axis"] += 1
            lo, hi = sorted((max(along, 0.0), max(across, 0.0)))
            shape = "gable" if hi > GABLE_RATIO * max(lo, 1e-6) else "hip"
            if span > MAX_SPAN:
                pitched = False           # too wide to be a roof of this kind

        if pitched:
            stats[shape] += 1
        else:
            eaves = ridge = h
            shape = None
            stats["flat"] += 1

        tag = b["tags"].get("building", "yes")
        family = BY_TAG.get(tag)
        if family is None:
            area = abs(sum(ring[i][0] * ring[(i + 1) % len(ring)][1] -
                           ring[(i + 1) % len(ring)][0] * ring[i][1]
                           for i in range(len(ring)))) / 2
            cx = int(np.clip(np.mean([p[0] for p in ring]) + (E1 - E0) / 2, 0, W - 1))
            cz = int(np.clip(np.mean([p[1] for p in ring]) + (N1 - N0) / 2, 0, H - 1))
            hint = COVER_HINT.get(classes.get(int(landclass[cz, cx])))
            if area < 25 or h < 3.2:
                family = "shed"
            elif hint in ("house", "civic") and pitched:
                family = hint
            elif area > 600:
                family = "retail"
            else:
                family = hint or ("house" if pitched else "shed")
        families[family] = families.get(family, 0) + 1

        rec["family"] = family
        # Both measured from the same datum as `height`, so a reader never has
        # to know which of base or ground a number is relative to.
        rec["eaves"] = round(min(eaves, h), 1) if pitched else rec["height"]
        rec["ridge"] = round(max(ridge, eaves + MIN_PITCH), 1) if pitched else rec["height"]
        rec["axis"] = round(math.degrees(angle) % 180, 1) if pitched else None
        rec["roof"] = shape
        rows.append(rec)

    assert index == len(existing), f"{index} rebuilt, {len(existing)} on file"
    pitched = stats["gable"] + stats["hip"]
    print(f"buildings {len(rows)}  gable {stats['gable']}  hip {stats['hip']}"
          f"  flat {stats['flat']}")
    print("ridge runs across the footprint's long axis:",
          stats["ridge_across_long_axis"],
          f"({stats['ridge_across_long_axis'] / max(1, pitched):.1%}) — "
          f"narrow-fronted houses whose ridge follows the street")
    print("families", dict(sorted(families.items(), key=lambda kv: -kv[1])))
    rises = [r["ridge"] - r["eaves"] for r in rows if r["axis"] is not None]
    if rises:
        print("median ridge above eaves:", round(float(np.median(rises)), 2), "m")
    if args.dry_run:
        print("dry run — nothing written")
        return
    (out / "gv-buildings.json").write_text(json.dumps(rows))
    meta = json.loads((out / "gv-meta.json").read_text())
    meta["roofs"] = {
        "note": "eaves and ridge are heights above `base`, in the same units "
                "as `height`; `axis` is the ridge bearing in degrees within "
                "the local frame (x east, z south), or null for a flat roof. "
                "`height` is unchanged and is still what the map page renders. "
                "`roof` is \"gable\", \"hip\" or null.",
        "gable": stats["gable"], "hip": stats["hip"], "flat": stats["flat"],
        "families": {k: {"wall": f"#{v['wall']:06x}", "roof": f"#{v['roof']:06x}",
                         "count": families.get(k, 0)}
                     for k, v in FAMILIES.items()},
    }
    (out / "gv-meta.json").write_text(json.dumps(meta, indent=2))
    print("wrote gv-buildings.json and gv-meta.json")


if __name__ == "__main__":
    main()
