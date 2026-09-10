"""Read the Golden Valley heightmap, whatever shape it is on disk.

Phase 7 packed `gv-height-2000.bin` down from 7.63 MB to 1.98 by quantising to
twelve bits, predicting each sample from its left and upper neighbours and
gzipping the residual. The browser learned to read that; **three python
scripts did not**, and every one of them went on indexing the file as if it
were four million uint16s:

    measure_leg_anchors.py   IndexError, reported from a plate
    golden_valley_2045.py    the generator for the entire 2045 scheme
    find_open_land.py        the survey the scheme's siting rests on

Only the first one crashed loudly enough to be noticed, and it was reported as
a plate looking over the edge of the box. It was not. `test_heightmap.py`
checked that node and python agreed about the format — and they did, because
the python it checked was a copy written inside the test rather than the code
anything actually calls.

So there is one reader now, this one, and the test points at it.
"""
import gzip
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"


def unpack(packed, w, h, bits):
    """Undo the predictor. The mirror of `golden-valley/heights.js`."""
    n = w * h
    if packed.size != 2 * n:
        raise ValueError(f"heightmap is {packed.size} bytes, expected {2 * n}")
    z = (packed[:n].astype(np.uint32)
         | (packed[n:2 * n].astype(np.uint32) << 8))
    # Zigzag back to signed residuals.
    d = ((z >> 1) ^ (-(z & 1)).astype(np.uint32)).astype(np.int32).reshape(h, w)

    q = np.zeros((h, w), dtype=np.int32)
    # Serial by construction: every sample is predicted from two it has to
    # wait for. Two seconds on four million samples, once per script run.
    for y in range(h):
        row = q[y]
        drow = d[y]
        if y == 0:
            acc = 0
            for x in range(w):
                acc = drow[x] + (acc if x else 0)
                row[x] = acc
        else:
            prev = q[y - 1]
            row[0] = drow[0] + prev[0]
            for x in range(1, w):
                row[x] = drow[x] + ((row[x - 1] + prev[x]) >> 1)

    up, down = 16 - bits, 2 * bits - 16
    return ((q.astype(np.uint32) << up)
            | (q.astype(np.uint32) >> down)).astype(np.uint16)


def load_heights(meta, folder=GV):
    """uint16 heights as (h, w), from a meta dict that names the file."""
    path = Path(folder) / meta["binFile"]
    w, h = meta["binPixels"]
    fmt = str(meta.get("binFormat", ""))
    if not fmt.startswith("delta"):
        return np.frombuffer(path.read_bytes(), dtype="<u2").reshape(h, w)
    packed = np.frombuffer(gzip.decompress(path.read_bytes()), dtype=np.uint8)
    return unpack(packed, w, h, int(fmt[5:]))


def load(name="gv-meta.json", folder=GV):
    return json.loads((Path(folder) / name).read_text())


def sampler(meta, heights=None, folder=GV):
    """`at(x, z)` in local metres, giving height above ordnance datum.

    Clamped at the edges on purpose. A plate composed to look across the box —
    which is now normal, since the horizon matters — projects features whose
    ground sample falls outside the survey, and the nearest edge is a better
    answer than a crash.
    """
    if heights is None:
        heights = load_heights(meta, folder)
    h, w = heights.shape
    lo, hi = meta["elevationMinMetres"], meta["elevationMaxMetres"]
    sx, sz = meta["widthMetres"], meta["heightMetres"]

    def at(x, z):
        px = min(max(int((x / sx + 0.5) * (w - 1)), 0), w - 1)
        pz = min(max(int((z / sz + 0.5) * (h - 1)), 0), h - 1)
        return lo + heights[pz, px] / 65535 * (hi - lo)

    return at
