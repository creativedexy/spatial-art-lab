"""Make the living map small enough to open on a phone.

Phase 7. Every choice here is argued from the data rather than from a preset,
because the one thing this experiment cannot afford is a saving that quietly
moves the ground. `scripts/guard_plates.py` is the check; this is the change.

  terrain     7.63 MB -> ~2.0 MB. The heightmap is uint16 over a 34.96 m
              elevation span, which is a step of 0.53 mm — three orders of
              magnitude finer than the survey it came from. Twelve bits gives
              0.85 cm, and the measured median difference between neighbouring
              cells in this very file is 2.19 cm, so the quantisation step is
              2.6x smaller than the ground's own roughness and cannot terrace
              anything the LiDAR has not already terraced. Ten bits (3.42 cm)
              would be larger than that median and is the reason this is not
              simply "as small as possible".

              Then: predict each sample from the average of its left and upper
              neighbours, zigzag the residual, split the low and high bytes
              into separate planes so like sits with like, and gzip. The
              browser undoes it with DecompressionStream and a loop. No image
              decode, no canvas readback, no colour management anywhere near
              the terrain.

  land class  lossless WebP. These are class indices read with NearestFilter;
              a lossy byte here is a field changing crop.

  land cover  lossy WebP. This one is colour, stretched over two kilometres.

  photographs lossy WebP. Not first-load — a place fetches its own — but a
              2 MB PNG is two seconds of waiting after a click.

  models      handled by gltf-transform, which is node rather than python:
              see MODELS below. Textures to 1024 WebP, geometry to meshopt.

Usage:
  python3 scripts/compress_assets.py            # report what it would do
  python3 scripts/compress_assets.py --write
"""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
GEN = ROOT / "experiments" / "002-living-map" / "generate"

BITS = 12
COVER_QUALITY = 90
PHOTO_QUALITY = 86

MODELS = """  cd <a scratch dir> && npm i @gltf-transform/cli
  gltf-transform resize  in.glb  a.glb --width 1024 --height 1024
  gltf-transform webp    a.glb    b.glb --quality 82
  gltf-transform weld    b.glb    c.glb
  gltf-transform meshopt c.glb   out.glb --level medium"""


def encode_heights(a, bits=BITS):
    """uint16 heightmap -> gzipped predicted residuals. Lossy by `bits` only."""
    top = (1 << bits) - 1
    q = np.rint(a.astype(np.float64) * top / 65535.0).astype(np.int32)
    left = np.zeros_like(q)
    left[:, 1:] = q[:, :-1]
    left[1:, 0] = q[:-1, 0]
    up = np.zeros_like(q)
    up[1:, :] = q[:-1, :]
    up[0, 1:] = q[0, :-1]
    d = q - ((left + up) >> 1)
    z = ((d << 1) ^ (d >> 31)).astype(np.uint32)
    if z.max() > 0xFFFF:
        raise ValueError("residual does not fit in 16 bits")
    lo = (z & 255).astype(np.uint8).tobytes()
    hi = (z >> 8).astype(np.uint8).tobytes()
    # mtime=0 so the same heightmap always gives the same file: a build that
    # is not reproducible cannot be checked against itself, which is the whole
    # of test_heightmap.py's last assertion. Python 3.13 changed gzip.compress
    # to write 255 rather than zlib's platform OS byte; pin the shipped Unix
    # value too so the wrapper stays reproducible across Python versions.
    encoded = bytearray(gzip.compress(lo + hi, 9, mtime=0))
    encoded[9] = 3
    return bytes(encoded), q


def decoded_error(a, q, bits=BITS):
    """What the browser will reconstruct, and how far off it is, in metres."""
    top = (1 << bits) - 1
    back = (q.astype(np.uint32) << (16 - bits)) | (q.astype(np.uint32) >> (2 * bits - 16))
    return np.abs(back.astype(np.int32) - a.astype(np.int32)).max() / 65535.0, back


def mb(n):
    return f"{n / 1048576:.2f} MB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="actually replace files")
    args = ap.parse_args()
    saved = 0
    say = "writing" if args.write else "would write"

    # --- terrain -----------------------------------------------------------
    meta = json.loads((GV / "gv-meta.json").read_text())
    src = GV / meta["binFile"].replace(".gz", "")
    if src.suffix == ".bin" and src.exists():
        W, H = meta["binPixels"]
        a = np.frombuffer(src.read_bytes(), dtype="<u2").reshape(H, W)
        blob, q = encode_heights(a)
        span = meta["elevationMaxMetres"] - meta["elevationMinMetres"]
        err, _ = decoded_error(a, q)
        out = GV / (src.name + ".gz")
        print(f"terrain   {mb(src.stat().st_size)} -> {mb(len(blob))}   "
              f"worst height error {err * span * 100:.2f} cm")
        saved += src.stat().st_size - len(blob)
        if args.write:
            out.write_bytes(blob)
            meta["binFile"] = out.name
            meta["binFormat"] = f"delta{BITS}"
            meta["binQuantisationCentimetres"] = round(span / ((1 << BITS) - 1) * 100, 3)
            (GV / "gv-meta.json").write_text(json.dumps(meta, indent=2) + "\n")
            src.unlink()

    # --- land cover and land class -----------------------------------------
    for metafile, key in (("gv-landcover.json", None), ("gv-2045-meta.json", None)):
        p = GV / metafile
        d = json.loads(p.read_text())
        changed = False
        for field, lossless, quality in (("classFile", True, 100),
                                         ("colourFile", False, COVER_QUALITY)):
            name = d.get(field)
            if not name or not name.endswith(".png"):
                continue
            f = GV / name
            if not f.exists():
                continue
            im = Image.open(f)
            out = f.with_suffix(".webp")
            im.save(out, format="WEBP", lossless=lossless, quality=quality,
                    method=6, exact=lossless)
            was, now = f.stat().st_size, out.stat().st_size
            print(f"{field:9} {mb(was)} -> {mb(now)}   "
                  f"{'lossless' if lossless else f'q{quality}'}  {name}")
            saved += was - now
            if args.write:
                d[field] = out.name
                f.unlink()
                changed = True
            else:
                out.unlink()
        if changed:
            p.write_text(json.dumps(d, indent=2) + "\n")

    # --- the photographs ---------------------------------------------------
    for f in sorted(GEN.glob("*/out/*.png")):
        im = Image.open(f).convert("RGB")
        out = f.with_suffix(".webp")
        im.save(out, format="WEBP", quality=PHOTO_QUALITY, method=6)
        was, now = f.stat().st_size, out.stat().st_size
        print(f"photo     {mb(was)} -> {mb(now)}   {f.parent.parent.name}/{f.name}")
        saved += was - now
        if not args.write:
            out.unlink()
        # The PNG stays: it is the approved original, and the queue's briefs
        # point at it. Only the map is served the WebP.

    print(f"\n{say}: {mb(saved)} saved")
    print(f"\nmodels are a separate, node-side step:\n{MODELS}")


if __name__ == "__main__":
    main()
