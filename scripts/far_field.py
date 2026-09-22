"""The land beyond the box, so the world stops ending in mid-air.

The map holds two square kilometres of Environment Agency LiDAR and nothing
else, which means the ground runs out at a cliff and the sky starts. Phase 11
could only avoid it: of sixteen candidate shots, every one that looked
north-west was thrown out because the survey ends 270 m behind the new homes,
and the best establishing frame we had was rejected for being a plan view with
no sky in it. Composition was paying for a data problem.

What is actually missing is the skyline this place has. Cleeve Hill is 330 m
and six kilometres north-east; the Cotswold escarpment runs the whole eastern
horizon; the Malverns stand twenty-five kilometres north-west and the Black
Mountains seventy beyond them. The developer's own hero photograph has all of
it, and says so — "Severn Vale and the Welsh hills on the far horizon".

So: OS Terrain 50, Ordnance Survey's open 50 m terrain model of Great Britain,
under the same Open Government Licence as the LiDAR already here. Two grids
rather than one, because resolution should follow distance:

    near   28 km across at 100 m   the escarpment, Bredon, Churchdown
    far   150 km across at 560 m   the Malverns, May Hill, Wales

**The seam is the craft.** Two surveys of the same ground do not agree — a
national 50 m model and a 1 m LiDAR composite differ by metres at any given
point — and a step at the box boundary is a crack you cannot unsee. So every
far-field sample within the blend band is corrected toward what our own LiDAR
says at the nearest point on the box edge, at full strength on the boundary
itself and fading out over half a kilometre. The join is then exact by
construction rather than by luck.

Heights stay true elevations above ordnance datum. Earth curvature is a
property of looking, not of the ground, so it is applied by the view — see
farfield.js — and never baked in here.

    python3 scripts/far_field.py --asc /path/to/asc
"""
import argparse
import gzip
import json
import math
from pathlib import Path

import numpy as np

from heightfield import GV, load, load_heights

ROOT = Path(__file__).resolve().parent.parent
CELL = 50.0                      # OS Terrain 50 post spacing, metres

# The box, from gv-meta.json: 2 km centred on BNG 391400 222400.
ORIGIN_E, ORIGIN_N = 391400.0, 222400.0
HALF_BOX = 1000.0

# How far the correction toward our own LiDAR reaches past the box edge. Long
# enough that the fix is invisible, short enough that it is not inventing
# terrain: 500 m is five OS posts.
BLEND_METRES = 500.0

# Resolution follows distance, and the two extents have to divide exactly or
# the grids meet at a second seam of their own: 12000 is 220 near posts out
# from the box edge, and 126 far posts in from the horizon.
GRIDS = {
    # name: (half extent in metres, post spacing in metres)
    "near": (12000.0, 50.0),      # native OS resolution, out past the escarpment
    "far": (75000.0, 500.0),      # the Malverns, May Hill, the Black Mountains
}
BITS = 12                        # the codec heights.js already reads


def mosaic(asc_dir, e0, e1, n0, n1):
    """Every OS tile overlapping the window, pasted into one array."""
    w = int(round((e1 - e0) / CELL))
    h = int(round((n1 - n0) / CELL))
    out = np.full((h, w), np.nan, dtype=np.float32)
    used = 0
    for path in sorted(Path(asc_dir).glob("*.asc")):
        head = {}
        with path.open() as f:
            for _ in range(5):
                k, v = f.readline().split()
                head[k] = float(v)
            body = np.loadtxt(f, dtype=np.float32)
        cols, rows = int(head["ncols"]), int(head["nrows"])
        xll, yll, cs = head["xllcorner"], head["yllcorner"], head["cellsize"]
        if xll + cols * cs <= e0 or xll >= e1 or yll + rows * cs <= n0 or yll >= n1:
            continue
        # ASCII grids run north to south; our array runs south to north, so the
        # rows are flipped once here rather than reasoned about twice later.
        body = body[::-1]
        # Tiles are on the same 50 m lattice as the window, so this is a slice
        # rather than a resample — and a slice rather than ten million python
        # iterations, which is what the first draft of this cost.
        i0 = int(round((xll - e0) / CELL))
        j0 = int(round((yll - n0) / CELL))
        si, di = max(0, -i0), max(0, i0)
        sj, dj = max(0, -j0), max(0, j0)
        ni = min(cols - si, w - di)
        nj = min(rows - sj, h - dj)
        if ni <= 0 or nj <= 0:
            continue
        out[dj:dj + nj, di:di + ni] = body[sj:sj + nj, si:si + ni]
        used += 1
    return out, used


def build(name, half, step, os_grid, e0, n0, lidar_at):
    """One square grid of true elevations, seam-corrected near the box."""
    n = int(round(2 * half / step)) + 1
    xs = np.linspace(-half, half, n)              # local metres, x east
    zs = np.linspace(-half, half, n)              # local metres, z SOUTH
    out = np.zeros((n, n), dtype=np.float32)
    seam = np.zeros((n, n), dtype=np.float32)

    def sample_os(e, nn):
        i = (e - e0) / CELL
        j = (nn - n0) / CELL
        i0, j0 = int(np.floor(i)), int(np.floor(j))
        if not (0 <= i0 < os_grid.shape[1] - 1 and 0 <= j0 < os_grid.shape[0] - 1):
            return math.nan
        fi, fj = i - i0, j - j0
        q = os_grid[j0:j0 + 2, i0:i0 + 2]
        if np.isnan(q).any():
            return math.nan
        return float((q[0, 0] * (1 - fi) + q[0, 1] * fi) * (1 - fj)
                     + (q[1, 0] * (1 - fi) + q[1, 1] * fi) * fj)

    for jz, z in enumerate(zs):
        north = ORIGIN_N - z                      # z is south, so north falls
        for ix, x in enumerate(xs):
            east = ORIGIN_E + x
            v = sample_os(east, north)
            out[jz, ix] = v

            # How far outside the box this sample sits, as a square distance —
            # the box is square, so the ring around it is square too.
            d = max(abs(x), abs(z)) - HALF_BOX
            if d >= BLEND_METRES or math.isnan(v):
                continue
            # The nearest point ON the box edge, and what each survey says
            # about it. The difference is the step we would otherwise show.
            ex = max(-HALF_BOX, min(HALF_BOX, x))
            ez = max(-HALF_BOX, min(HALF_BOX, z))
            if abs(x) >= abs(z):
                ex = math.copysign(HALF_BOX, x)
            else:
                ez = math.copysign(HALF_BOX, z)
            theirs = sample_os(ORIGIN_E + ex, ORIGIN_N - ez)
            if math.isnan(theirs):
                continue
            k = 1.0 - max(0.0, d) / BLEND_METRES   # 1 on the edge, 0 at 500 m
            k = k * k * (3 - 2 * k)                # eased, so no crease
            fix = (lidar_at(ex, ez) - theirs) * k
            out[jz, ix] = v + fix
            seam[jz, ix] = fix

    return out, seam


def pack(field, bits):
    """The delta-12 codec from phase 7, so heights.js reads this unchanged."""
    lo, hi = float(np.nanmin(field)), float(np.nanmax(field))
    field = np.nan_to_num(field, nan=lo)
    q = np.round((field - lo) / max(hi - lo, 1e-9) * ((1 << bits) - 1)).astype(np.int32)
    h, w = q.shape
    d = np.zeros_like(q)
    for y in range(h):
        for x in range(w):
            if x == 0 and y == 0:
                pred = 0
            elif y == 0:
                pred = q[0, x - 1]
            elif x == 0:
                pred = q[y - 1, 0]
            else:
                pred = (q[y, x - 1] + q[y - 1, x]) >> 1
            d[y, x] = q[y, x] - pred
    z = ((d << 1) ^ (d >> 31)).astype(np.uint32)     # zigzag
    assert z.max() < 65536, f"residual {z.max()} will not fit two bytes"
    flat = z.ravel()
    packed = np.concatenate([(flat & 0xFF).astype(np.uint8),
                             ((flat >> 8) & 0xFF).astype(np.uint8)])
    return gzip.compress(packed.tobytes(), 9, mtime=0), lo, hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asc", required=True, help="folder of OS Terrain 50 .asc tiles")
    args = ap.parse_args()

    meta = load()
    heights = load_heights(meta)
    h, w = heights.shape
    elo, ehi = meta["elevationMinMetres"], meta["elevationMaxMetres"]

    def lidar_at(x, z):
        px = min(max(int((x / 2000 + 0.5) * (w - 1)), 0), w - 1)
        pz = min(max(int((z / 2000 + 0.5) * (h - 1)), 0), h - 1)
        return elo + heights[pz, px] / 65535 * (ehi - elo)

    biggest = max(half for half, _ in GRIDS.values())
    e0, e1 = ORIGIN_E - biggest - CELL, ORIGIN_E + biggest + CELL
    n0, n1 = ORIGIN_N - biggest - CELL, ORIGIN_N + biggest + CELL
    print(f"mosaicking {int(e1 - e0) // 1000} x {int(n1 - n0) // 1000} km of "
          f"OS Terrain 50")
    os_grid, used = mosaic(args.asc, e0, e1, n0, n1)
    covered = 100 * np.isfinite(os_grid).mean()
    print(f"  {used} tiles, {covered:.1f}% of the window has land "
          f"(the rest is sea or off the edge of Britain)")

    out = {"note": "The land beyond the box. Elevations above ordnance datum, "
                   "true — Earth curvature is applied by the view, not baked "
                   "here. Local metres, x east, z SOUTH, origin at the box "
                   "centre (BNG 391400 222400). Built by scripts/far_field.py.",
           "origin": [ORIGIN_E, ORIGIN_N],
           "boxHalfMetres": HALF_BOX,
           "blendMetres": BLEND_METRES,
           "sources": ["OS Terrain 50 © Crown copyright and database right "
                       "2026 (OGL v3)",
                       "Environment Agency LiDAR composite DTM (OGL v3), "
                       "for the seam correction"],
           "grids": {}}

    for name, (half, step) in GRIDS.items():
        field, seam = build(name, half, step, os_grid, e0, n0, lidar_at)
        blob, lo, hi = pack(field, BITS)
        path = GV / f"gv-far-{name}.bin.gz"
        path.write_bytes(blob)
        touched = seam != 0
        out["grids"][name] = {
            "binFile": path.name,
            "binPixels": [field.shape[1], field.shape[0]],
            "binFormat": f"delta{BITS}",
            "halfExtentMetres": half,
            "stepMetres": step,
            "elevationMinMetres": round(lo, 2),
            "elevationMaxMetres": round(hi, 2),
        }
        print(f"  {name:5} {field.shape[1]}x{field.shape[0]} at {step:g} m, "
              f"{lo:.0f}..{hi:.0f} m AOD, {len(blob) / 1024:.0f} KB")
        if touched.any():
            print(f"        seam: {touched.sum()} samples corrected, "
                  f"worst {np.abs(seam).max():.2f} m, "
                  f"mean {np.abs(seam[touched]).mean():.2f} m")

    (GV / "gv-far-meta.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {(GV / 'gv-far-meta.json').relative_to(ROOT)}")

    # Somewhere to check the answer against. If Cleeve Hill is not 330 m and
    # north-east of here, the frame or the mosaic is wrong and every hill on
    # the horizon is in the wrong place.
    for place, (e, n, expect) in {
        # Checked against the data on 12 Sep: the highest point in the near
        # grid is 330 m at BNG 399700 224600, which is Cleeve Common — the
        # highest ground in the Cotswolds, 8.6 km out on a bearing of 75.
        "Cleeve Common": (399700, 224600, 330),
        "Leckhampton Hill": (394700, 218400, 270),
        "Worcestershire Beacon": (376800, 245200, 425),
        "May Hill": (369500, 221200, 296),
    }.items():
        i = int((e - e0) / CELL)
        j = int((n - n0) / CELL)
        got = os_grid[j, i]
        d = math.hypot(e - ORIGIN_E, n - ORIGIN_N) / 1000
        print(f"  {place:22} {got:6.0f} m  (expected about {expect}), "
              f"{d:.0f} km away")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
