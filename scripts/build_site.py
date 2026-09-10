"""Assemble the living map as a folder you can put on a static host.

Phase 7. The map has always been served straight out of the repository, which
works on this machine and nowhere else — the repository also holds LiDAR
intermediates, generation briefs, session notes, and other people's copyrighted
renders. This copies out the files the page actually loads, and nothing else.

**The models are internal-only.** `campus-block.glb` and `ncic.glb` were made
from drawings that derive from HBD's and Grimshaw's published renders of this
scheme, and `experiments/002-living-map/meshy/README.md` says in terms: pitch
work, do not publish. So they are left out unless you ask for them by name,
and asking for them means the folder is for a pitch, not for the open web. The
map is built to survive their absence — a family whose model is missing keeps
its extrusions — so the public build is a working map, just a blockier campus.

  python3 scripts/build_site.py                  # a folder anyone may see
  python3 scripts/build_site.py --internal       # with the models, for a pitch

Nothing here uploads anything. Where it goes is Dex's call.
"""
import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "experiments" / "002-living-map"
OUT = ROOT / "dist"

# Everything the page fetches, by the folder it lives in. Kept as an explicit
# list rather than a copy-the-lot-and-prune, because the failure that matters
# is shipping something we did not mean to, not missing a file — a missing
# file is loud on the first load and a shipped one is silent forever.
KEEP = {
    "golden-valley": ["index.html", "direction.css", "*.js", "*.json",
                      "*.webp", "*.bin", "*.bin.gz"],
    "terrain/vendor": ["*.js"],
    "terrain/vendor/fonts": ["*.woff2", "*.css"],
    "descent": ["path.js", "player.js", "hotspots.json", "descent-path.json"],
    "descent/clips": ["descent-control.webm"],
}
PHOTOS = "generate/*/out/*.webp"
MODELS = ["meshy/campus-block.glb", "meshy/ncic.glb"]

# Never, whatever a glob above may match.
FORBIDDEN = ("inspiration/", "meshy/src/", "-hq.webm", ".mp4", "LOCAL-SESSION",
             "LADDER-SESSION", "seam-report")


def copy(rel, dest_root, log):
    src = SITE / rel
    if any(f in str(rel) for f in FORBIDDEN):
        raise SystemExit(f"refusing to publish {rel}")
    dest = dest_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    log.append((str(rel), src.stat().st_size))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--internal", action="store_true",
                    help="include the HBD-derived campus models (pitch only)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    log = []
    for folder, globs in KEEP.items():
        for g in globs:
            for f in sorted((SITE / folder).glob(g)):
                copy(f.relative_to(SITE), out, log)
    for f in sorted(SITE.glob(PHOTOS)):
        copy(f.relative_to(SITE), out, log)

    if args.internal:
        for m in MODELS:
            copy(Path(m), out, log)
    else:
        print("models left out — they derive from HBD's renders and "
              "meshy/README.md says pitch work only.\n"
              "The campus falls back to its extrusions. Use --internal for a "
              "pitch build.\n")

    # The page is one folder down; a host wants something at the root.
    (out / "index.html").write_text(
        '<!doctype html><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=golden-valley/">'
        '<title>The Golden Valley</title>'
        '<a href="golden-valley/">The Golden Valley</a>\n')

    total = sum(n for _, n in log)
    log.sort(key=lambda r: -r[1])
    print(f"{len(log)} files, {total / 1048576:.2f} MB, in {out}")
    print("\n  ten heaviest")
    for name, n in log[:10]:
        print(f"    {n / 1048576:6.2f} MB  {name}")
    manifest = {"files": [{"file": f, "bytes": n} for f, n in log],
                "totalBytes": total, "models": bool(args.internal)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
