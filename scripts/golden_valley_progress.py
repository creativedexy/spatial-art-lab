"""How much of the scheme has arrived, by class, as the front crosses.

Phase 8. The map can already show 2045; what it cannot do is say what 2045 IS.
The figures exist — 77.4 hectares over 29 fields, 29% of it orchard, built
area capped at a third — and they are the argument a client is actually being
asked to buy. They were in a JSON file nobody reading the map can see.

Putting them on screen as a fixed legend would be the easy version and the
wrong one: the wave is the piece, and a number that does not move while the
thing it describes sweeps across the vale is furniture. So this measures the
scheme column by column, and the map reads off how much has arrived at
whatever position the dial is holding.

Measured, not interpolated. Tweening the totals with the wave would be close
to right and impossible to defend — the fields are not spread evenly, and the
orchards ring the built area rather than sitting west of it. This compares the
two class maps square metre by square metre, bins the differences by easting,
and writes the running total per class. What the map then shows at any dial
position is what is actually behind the front.

  python3 scripts/golden_valley_progress.py
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
BINS = 200            # 10 m of easting each, over the 2 km box


def main():
    cover = json.loads((GV / "gv-landcover.json").read_text())
    future = json.loads((GV / "gv-2045-meta.json").read_text())
    today = np.array(Image.open(GV / cover["classFile"]).convert("L"))
    then = np.array(Image.open(GV / future["classFile"]).convert("L"))
    h, w = today.shape
    changed = today != then

    names = {v["index"]: k for k, v in future["classes"].items()}
    # Only the classes 2045 introduces, plus the ground it stands its
    # buildings on: those are the scheme. A field that was grass and is still
    # grass is not a proposal.
    wanted = sorted({int(i) for i in np.unique(then[changed])})

    edges = np.linspace(0, w, BINS + 1).astype(int)
    out = {}
    for idx in wanted:
        mask = changed & (then == idx)
        # Sum down each column, then across the bin: a square metre per pixel,
        # so this is hectares once divided by ten thousand.
        per_column = mask.sum(axis=0)
        running, total = [], 0.0
        for i in range(BINS):
            total += per_column[edges[i]:edges[i + 1]].sum() / 10000.0
            running.append(round(total, 3))
        if running[-1] < 0.2:
            continue          # below a fifth of a hectare is not a finding
        out[names.get(idx, str(idx))] = running

    doc = {
        "note": ("How much of the 2045 scheme lies west of each easting, by "
                 "class, in hectares. Written by scripts/golden_valley_progress.py "
                 "from the two class maps: this is measured area, not the "
                 "totals tweened with the wave. Bin i covers x from "
                 "-1000 + i*10 to -1000 + (i+1)*10 in local metres, and each "
                 "value is the running total up to the RIGHT edge of that bin."),
        "bins": BINS,
        "metresPerBin": round(2000 / BINS, 3),
        "fromMetres": -1000,
        "classes": out,
        "totalHectares": round(sum(v[-1] for v in out.values()), 2),
    }
    path = GV / "gv-2045-progress.json"
    path.write_text(json.dumps(doc) + "\n")

    print(f"{doc['totalHectares']:.1f} ha of scheme, {len(out)} classes, "
          f"{BINS} bins of {doc['metresPerBin']:.0f} m")
    for k, v in sorted(out.items(), key=lambda kv: -kv[1][-1]):
        half = next(i for i, t in enumerate(v) if t >= v[-1] / 2)
        print(f"  {k:14} {v[-1]:6.1f} ha   half of it west of "
              f"x = {-1000 + half * 10:+5d} m")
    print(f"\nwrote {path.relative_to(ROOT)}  {path.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
