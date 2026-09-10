"""The terrain codec, checked in both languages.

Phase 7. The heightmap is the one asset the whole map is built on — the ground
every building stands on, every path is draped over and every camera is aimed
at — and it is now written by python and read by JavaScript. A disagreement
between those two would not throw; it would just move Cheltenham.

So: decode the shipped file with node, decode it again with a python
implementation written from the same description, and require them to be
identical byte for byte. Then re-encode what came back and require the shipped
bytes exactly, which is only possible if the quantisation, the predictor, the
zigzag and the plane split all round-trip.
"""
import gzip
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
sys.path.insert(0, str(ROOT / "scripts"))

NODE = r"""
import { unpack } from '%s';
import { readFileSync, writeFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
const meta = JSON.parse(readFileSync('%s', 'utf8'));
const packed = gunzipSync(readFileSync('%s'));
const bits = Number(meta.binFormat.slice(5));
const out = unpack(new Uint8Array(packed), meta.binPixels[0], meta.binPixels[1], bits);
writeFileSync('%s', Buffer.from(out.buffer));
"""

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))


def python_unpack(packed, W, H, bits):
    n = W * H
    z = (packed[:n].astype(np.uint32) | (packed[n:2 * n].astype(np.uint32) << 8))
    d = ((z >> 1) ^ (-(z & 1)).astype(np.uint32)).astype(np.int32).reshape(H, W)
    q = np.zeros((H, W), dtype=np.int32)
    for y in range(H):
        row = q[y]
        prev = q[y - 1] if y else None
        for x in range(W):
            if x:
                left = row[x - 1]
                up = prev[x] if y else row[x - 1]
            else:
                left = up = prev[0] if y else 0
            row[x] = d[y, x] + ((left + up) >> 1)
    up_shift, down_shift = 16 - bits, 2 * bits - 16
    return ((q.astype(np.uint32) << up_shift)
            | (q.astype(np.uint32) >> down_shift)).astype(np.uint16)


def main():
    meta = json.loads((GV / "gv-meta.json").read_text())
    print("the terrain codec")
    if not str(meta.get("binFormat", "")).startswith("delta"):
        check("the heightmap is in the compressed format", False, meta.get("binFile"))
        return 1
    bits = int(meta["binFormat"][5:])
    W, H = meta["binPixels"]
    packed = np.frombuffer(gzip.decompress((GV / meta["binFile"]).read_bytes()),
                           dtype=np.uint8)
    check("the file unpacks to two byte planes", len(packed) == 2 * W * H,
          f"{len(packed)} bytes for {W}x{H}")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "heights.bin"
        src = Path(tmp) / "run.mjs"
        src.write_text(NODE % (GV / "heights.js", GV / "gv-meta.json",
                               GV / meta["binFile"], out))
        r = subprocess.run(["node", str(src)], capture_output=True, text=True)
        if r.returncode:
            check("node decodes the shipped file", False, r.stderr.strip()[:200])
            return 1
        js = np.frombuffer(out.read_bytes(), dtype="<u2").reshape(H, W)
    check("node decodes the shipped file", True, f"{js.shape[0]}x{js.shape[1]}")

    py = python_unpack(packed, W, H, bits)
    check("both languages decode it the same", bool(np.array_equal(js, py)),
          f"worst disagreement {int(np.abs(js.astype(int) - py.astype(int)).max())}")

    from compress_assets import encode_heights
    again, _ = encode_heights(js, bits)
    check("re-encoding what came back gives the shipped bytes exactly",
          again == (GV / meta["binFile"]).read_bytes(),
          f"{len(again)} vs {(GV / meta['binFile']).stat().st_size} bytes")

    span = meta["elevationMaxMetres"] - meta["elevationMinMetres"]
    metres = js.astype(np.float64) * span / 65535.0
    d = np.abs(np.diff(metres, axis=1))
    step = span / ((1 << bits) - 1)
    check("the ground is still rougher than the quantisation",
          float(np.median(d)) > step,
          f"median neighbour step {np.median(d) * 100:.2f} cm "
          f"against a {step * 100:.2f} cm quantisation")
    check("the decoded range reaches both ends of the survey",
          js.min() == 0 and js.max() == 65535, f"{js.min()}..{js.max()}")

    print(f"\n{sum(checks)}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
