"""Where the map is still empty, and what is next to it.

Phase 6 groundwork. A brainstorm about "what could go here" is worth more when
"here" is measured: gv-landclass.png carries a class per square metre, so the
undeveloped parcels can be found rather than guessed at, sized in hectares, and
described by what they touch — a road for access, a footpath for arrival, a
stream for drainage, GCHQ for the reason any of this is happening.

Cells are 4 m, and a cell counts as open only if three quarters of its square
metres are. That is deliberate: it dissolves the one-pixel threads between
fields that would otherwise merge half the vale into a single blob, and it
throws away verges and garden strips, which are open ground but not sites.

Usage:  python3 scripts/find_open_land.py [--min-hectares 2] [--top 12]
"""
import argparse
import json
import math
from collections import deque
from pathlib import Path

import numpy as np

from heightfield import load_heights
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
CELL = 4                      # metres per analysis cell
OPEN_FRACTION = 0.75          # of a cell's square metres

# Genuinely undeveloped ground. `pitch` and `park` are open but already have a
# job, so they are reported as neighbours rather than as sites.
OPEN = ("farmland", "meadow", "grass", "scrub")
ACCESS = ("road", "road_minor")
# Hedgerows and watercourses are cut through the open mask before the parcels
# are found. Without it the whole allocation comes back as one 89 ha blob,
# which is true and useless: the field boundaries ARE the grain of the place,
# they are centuries old, and anything built here that ignores them will look
# like it was dropped from a helicopter. Cutting by them gives the parcels the
# landscape already has.
BARRIER_KINDS = ("hedge", "tree_row", "stream", "river", "ditch", "drain")


def load():
    meta = json.loads((GV / "gv-landcover.json").read_text())
    cls = np.array(Image.open(GV / meta["classFile"]).convert("L"))
    index = {k: v["index"] for k, v in meta["classes"].items()}
    return meta, cls, index


def cells_of(mask):
    """Downsample a 1 m boolean mask to CELL-metre cells."""
    h, w = mask.shape
    h, w = h // CELL * CELL, w // CELL * CELL
    blocks = mask[:h, :w].reshape(h // CELL, CELL, w // CELL, CELL)
    return blocks.mean(axis=(1, 3)) >= OPEN_FRACTION


def components(grid):
    """Four-connected components, as lists of (row, col). No scipy here."""
    seen = np.zeros_like(grid, dtype=bool)
    out = []
    rows, cols = grid.shape
    for r0 in range(rows):
        for c0 in range(cols):
            if not grid[r0, c0] or seen[r0, c0]:
                continue
            q = deque([(r0, c0)])
            seen[r0, c0] = True
            blob = []
            while q:
                r, c = q.popleft()
                blob.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < rows and 0 <= cc < cols \
                            and grid[rr, cc] and not seen[rr, cc]:
                        seen[rr, cc] = True
                        q.append((rr, cc))
            out.append(blob)
    return out


def cut_by_landmarks(mask, paths, width):
    """Erase a line of pixels along every hedge and watercourse."""
    mask = mask.copy()
    n = 0
    for lm in paths.get("landmarks", []):
        if lm["kind"] not in BARRIER_KINDS:
            continue
        n += 1
        pts = [(p[0] + width / 2, p[1] + width / 2) for p in lm["points"]]
        for (ax, az), (bx, bz) in zip(pts, pts[1:]):
            steps = max(int(math.dist((ax, az), (bx, bz))), 1)
            for i in range(steps + 1):
                t = i / steps
                col = int(round(ax + (bx - ax) * t))
                row = int(round(az + (bz - az) * t))
                # Three metres wide: a hedge is about that, and a one-pixel cut
                # can be stepped over diagonally by a flood fill.
                r0, r1 = max(row - 1, 0), min(row + 2, mask.shape[0])
                c0, c1 = max(col - 1, 0), min(col + 2, mask.shape[1])
                mask[r0:r1, c0:c1] = False
    print(f"cut by {n} hedgerows and watercourses")
    return mask


def terrain_of(blob, heights, zmin, zmax, width):
    """Mean height, slope and aspect of a parcel, from the height field."""
    hs, slopes, dz_n, dz_e = [], [], [], []
    step = max(len(blob) // 4000, 1)          # sample, do not survey
    H = heights.shape[0]
    at = lambda r, c: zmin + heights[min(max(r, 0), H - 1),
                                     min(max(c, 0), H - 1)] / 65535 * (zmax - zmin)
    for r, c in blob[::step]:
        row, col = r * CELL + CELL // 2, c * CELL + CELL // 2
        h = at(row, col)
        # Central differences over 20 m: fine enough to be a field's slope
        # rather than a molehill's.
        de = (at(row, col + 10) - at(row, col - 10)) / 20
        dn = (at(row - 10, col) - at(row + 10, col)) / 20
        hs.append(h)
        dz_e.append(de)
        dz_n.append(dn)
        slopes.append(math.degrees(math.atan(math.hypot(de, dn))))
    # Aspect is the compass bearing the ground faces, i.e. downhill.
    me, mn = sum(dz_e) / len(dz_e), sum(dz_n) / len(dz_n)
    bearing = (math.degrees(math.atan2(-me, -mn)) + 360) % 360
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return {
        "meanElevation": round(sum(hs) / len(hs), 1),
        "meanSlopeDegrees": round(sum(slopes) / len(slopes), 2),
        "aspect": points[int((bearing + 22.5) % 360 // 45)],
        "aspectDegrees": round(bearing),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-hectares", type=float, default=2.0)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--no-split", action="store_true",
                    help="do not cut the open mask by hedgerows and streams")
    ap.add_argument("--out", default=str(GV.parent / "vision" / "open-land.json"))
    args = ap.parse_args()

    meta, cls, index = load()
    gvmeta = json.loads((GV / "gv-meta.json").read_text())
    heights = load_heights(gvmeta, GV)
    paths = json.loads((GV / "gv-paths.json").read_text())
    E0, N0 = gvmeta["easting"][0], gvmeta["northing"][0]
    W = gvmeta["widthMetres"]

    # Pixel (0,0) is the north-west corner; local metres are x east, z south
    # from the box centre.
    to_local = lambda col, row: (col * CELL + CELL / 2 - W / 2,
                                 row * CELL + CELL / 2 - W / 2)

    open_mask = np.isin(cls, [index[c] for c in OPEN])
    if not args.no_split:
        open_mask = cut_by_landmarks(open_mask, paths, W)
    road_mask = np.isin(cls, [index[c] for c in ACCESS])
    water_mask = cls == index["water"]
    grid = cells_of(open_mask)
    roads = cells_of(road_mask)
    print(f"open ground {open_mask.mean() * 100:.1f}% of the box, "
          f"{grid.sum() * CELL * CELL / 10000:.0f} ha in {CELL} m cells")

    named = [r for r in paths["routes"] if r["tier"] == "named"]
    gchq = (123.0, 64.0)          # the Doughnut, in local metres
    gv_site = (-592.0, -215.0)    # Golden Valley phase 1

    sites, blobs = [], []
    for blob in components(grid):
        ha = len(blob) * CELL * CELL / 10000
        if ha < args.min_hectares:
            continue
        blobs.append(blob)
        rows = np.array([r for r, _ in blob])
        cols = np.array([c for _, c in blob])
        cx, cz = to_local(cols.mean(), rows.mean())
        x0, z0 = to_local(cols.min(), rows.min())
        x1, z1 = to_local(cols.max(), rows.max())

        # Road frontage: cells on the parcel edge with a road cell beside them.
        member = {(r, c) for r, c in blob}
        frontage = sum(
            1 for r, c in blob
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
            if (r + dr, c + dc) not in member
            and 0 <= r + dr < roads.shape[0] and 0 <= c + dc < roads.shape[1]
            and roads[r + dr, c + dc])

        # Water inside the parcel, in 1 m pixels — a stream corridor is a
        # constraint and an asset, and either way it is not a surprise.
        r0, r1 = rows.min() * CELL, (rows.max() + 1) * CELL
        c0, c1 = cols.min() * CELL, (cols.max() + 1) * CELL
        water = int(water_mask[r0:r1, c0:c1].sum())

        near_route, near_d = None, 1e9
        for rt in named:
            d = min(math.dist((cx, cz), p) for p in rt["points"])
            if d < near_d:
                near_route, near_d = rt["name"], d

        sites.append({
            "hectares": round(ha, 1),
            **terrain_of(blob, heights, gvmeta["elevationMinMetres"],
                         gvmeta["elevationMaxMetres"], W),
            "centreLocal": [round(cx), round(cz)],
            "centreBNG": [round(E0 + W / 2 + cx), round(N0 + W / 2 - cz)],
            "extentMetres": [round(x1 - x0), round(z1 - z0)],
            "roadFrontageMetres": frontage * CELL,
            "streamPixels": water,
            "nearestNamedRoute": near_route,
            "nearestNamedRouteMetres": round(near_d),
            "toGchqMetres": round(math.dist((cx, cz), gchq)),
            "toGoldenValleySiteMetres": round(math.dist((cx, cz), gv_site)),
        })

    order = sorted(range(len(sites)), key=lambda i: -sites[i]["hectares"])
    sites = [sites[i] for i in order]
    kept = [blobs[i] for i in order]
    print(f"\n{len(sites)} parcels of {args.min_hectares} ha or more\n")
    head = f"{'ha':>6}  {'local x,z':>14}  {'extent':>11}  {'road':>6}  " \
           f"{'slope':>6} {'face':>4}  {'GCHQ':>6}  {'GV':>6}  nearest named route"
    print(head)
    print("-" * len(head))
    for s in sites[:args.top]:
        print(f"{s['hectares']:>6.1f}  "
              f"{str(s['centreLocal'][0]) + ',' + str(s['centreLocal'][1]):>14}  "
              f"{str(s['extentMetres'][0]) + 'x' + str(s['extentMetres'][1]):>11}  "
              f"{s['roadFrontageMetres']:>5} m  "
              f"{s['meanSlopeDegrees']:>5.1f}° {s['aspect']:>4}  "
              f"{s['toGchqMetres']:>5} m  {s['toGoldenValleySiteMetres']:>5} m  "
              f"{s['nearestNamedRoute'] or '-'} "
              f"({s['nearestNamedRouteMetres']} m)")

    # An index image of the parcels themselves, so a plan can draw the shapes
    # rather than their bounding boxes. A bounding box round a field is a lie
    # about the field, and these are exactly the shapes worth arguing over.
    stamp = np.zeros(grid.shape, dtype=np.uint8)
    for i, blob in enumerate(kept, 1):
        if i > 255:
            break
        for r, c in blob:
            stamp[r, c] = i
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(stamp).save(dest.with_name("open-land-parcels.png"))
    dest.write_text(json.dumps({
        "note": ("Undeveloped parcels in the Golden Valley box, found in "
                 "gv-landclass.png at 4 m cells. Local metres are x east, "
                 "z south from the box centre; BNG is EPSG:27700. "
                 "`roadFrontageMetres` is parcel edge touching a road class, "
                 "which is a proxy for access, not a survey of it."),
        "cellMetres": CELL, "openClasses": list(OPEN),
        "minHectares": args.min_hectares,
        "count": len(sites), "sites": sites,
    }, indent=2) + "\n")
    print(f"\nwrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
