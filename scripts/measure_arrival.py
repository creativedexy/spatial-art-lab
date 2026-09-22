"""What a person standing at a candidate arrival would actually see.

Phase 13. The arrival design (plans/phase-13-arrival.md) was written against
the model at `665efcd`, before phase 12 put 1,030 dwellings, real agrivoltaic
rows, 180 GCHQ canopies and widened stormwater channels into it. A standing
position that was a crop gap then may be under a panel row now, and a
footprint quoted then may not exist. So the design is re-measured against the
data on disk before a single plate is rendered.

For each candidate this reports, from the eye point at 1.6 m:

  * the ground it stands on: height AOD, and the 2045 land class under foot
  * the buildings inside the frame, nearest first, with distance, how far off
    centre, and how tall they stand in the picture
  * what the ground in frame is made of, sampled as a fan of rays
  * the trees standing in the frame, which is what decides whether any of the
    rest of it can be seen: three of the first seven plates came back as a wall
    of leaves from positions this script had called clear
  * whether the flight in from the parent viewpoint clears the terrain

    .venv/bin/python scripts/measure_arrival.py experiments/002-living-map/generate/m8/arrivals.json
"""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

import heightfield as hf

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
EYE = 1.6


def load_class():
    meta = json.loads((GV / "gv-2045-meta.json").read_text())
    names = {v["index"]: k for k, v in meta["classes"].items()}
    img = np.asarray(Image.open(GV / meta["classFile"]).convert("L"))
    base = json.loads((GV / "gv-meta.json").read_text())
    sx, sz = base["widthMetres"], base["heightMetres"]
    h, w = img.shape

    def at(x, z):
        px = min(max(int((x / sx + 0.5) * (w - 1)), 0), w - 1)
        pz = min(max(int((z / sz + 0.5) * (h - 1)), 0), h - 1)
        return names.get(int(img[pz, px]), f"#{img[pz, px]}")

    return at


def load_trees():
    """The 2045 trees as (x, z, height, spread), 8 bytes each.

    The mirror of `loadFutureTrees` in future.js. Trees are instanced rather
    than painted into the class raster, so a fan of class samples says
    `orchard 80%` for a position whose view is entirely blocked by the trunks
    and canopies of that orchard.
    """
    meta = json.loads((GV / "gv-2045-meta.json").read_text())
    raw = (GV / meta["treeFile"]).read_bytes()
    a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 8)
    x = a[:, 0:2].copy().view("<i2").ravel() / 10
    z = a[:, 2:4].copy().view("<i2").ravel() / 10
    h = a[:, 4] * 0.25
    spread = a[:, 7] / 100
    return np.stack([x, z, h, spread], 1)


def bearing_of(dx, dz):
    """Compass bearing of a direction: 0 north (-z), 90 east (+x)."""
    return math.degrees(math.atan2(dx, -dz)) % 360


def offset(a, b):
    """Signed degrees from bearing b to bearing a, in (-180, 180]."""
    return (a - b + 180) % 360 - 180


def ring_centroid(ring):
    xs = [p[0] for p in ring]
    zs = [p[1] for p in ring]
    return sum(xs) / len(xs), sum(zs) / len(zs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--reach", type=float, default=260.0,
                    help="how far to look for things, in metres")
    args = ap.parse_args()

    base = json.loads((GV / "gv-meta.json").read_text())
    ground = hf.sampler(base)
    klass = load_class()
    buildings = json.loads((GV / "gv-2045-buildings.json").read_text())
    trees = load_trees()
    agri = json.loads((GV / "gv-2045-agrivoltaics.json").read_text())
    vps = {v["id"]: v for v in
           json.loads((GV / "viewpoints.json").read_text())["viewpoints"]}

    doc = json.loads(Path(args.candidates).read_text())
    for c in doc["candidates"]:
        x, z = c["stand"]
        gy = ground(x, z)
        eye = np.array([x, gy + EYE, z])
        lx, lz = c["look"]
        bearing = bearing_of(lx - x, lz - z)
        fov = c.get("fov", 48.0)
        # Horizontal half-angle of a 16:9 frame at this vertical fov.
        halfh = math.degrees(math.atan(math.tan(math.radians(fov / 2)) * 16 / 9))

        print(f"\n=== {c['id']}  ·  {c.get('why', '')}")
        print(f"  stand ({x:.1f}, {z:.1f})  ground {gy:.2f} m AOD  eye "
              f"{gy + EYE:.2f}  under foot: {klass(x, z)}")
        print(f"  looks at ({lx:.1f}, {lz:.1f})  bearing {bearing:.0f}°  "
              f"fov {fov:.0f}° vertical, {2 * halfh:.0f}° wide")

        rows = []
        for b in buildings:
            cx, cz = ring_centroid(b["ring"])
            dist = math.hypot(cx - x, cz - z)
            if dist > args.reach:
                continue
            off = offset(bearing_of(cx - x, cz - z), bearing)
            if abs(off) > halfh + 6:
                continue
            top = b["base"] + b["height"]
            rows.append((dist, off, b, top,
                         math.degrees(math.atan2(top - eye[1], dist))))
        rows.sort()
        print(f"  {len(rows)} buildings in frame within {args.reach:.0f} m:")
        for dist, off, b, top, ang in rows[:8]:
            print(f"    {dist:6.0f} m  {off:+6.1f}° off centre  "
                  f"{b['height']:5.1f} m {b['family']:9s} {b.get('typology') or b['roof']:11s}"
                  f"  rises {ang:+5.1f}° in frame")
        if len(rows) > 8:
            print(f"    ... and {len(rows) - 8} more")

        # What the ground in frame is made of: a fan of rays, sampled every 2 m.
        counts = {}
        near = {}
        for k in range(-8, 9):
            a = math.radians(bearing + halfh * k / 8)
            dx, dz = math.sin(a), -math.cos(a)
            for m in np.arange(2, args.reach, 2.0):
                name = klass(x + dx * m, z + dz * m)
                counts[name] = counts.get(name, 0) + 1
                if name not in near or m < near[name]:
                    near[name] = float(m)
        total = sum(counts.values())
        share = sorted(counts.items(), key=lambda kv: -kv[1])
        print("  ground in frame: " + ", ".join(
            f"{n} {100 * v / total:.0f}% (nearest {near[n]:.0f} m)"
            for n, v in share[:6]))

        # The trees, which decide whether anything else is visible. A canopy
        # is treated as a disc of `spread * height` across, centred on the
        # trunk: crude, but it is the same shape the renderer instances.
        tx, tz, th, tsp = trees.T
        td = np.hypot(tx - x, tz - z)
        keep = td < args.reach
        blocking = []
        for cx, cz, ch, csp, dist in zip(tx[keep], tz[keep], th[keep],
                                         tsp[keep], td[keep]):
            off_t = offset(bearing_of(cx - x, cz - z), bearing)
            half = math.degrees(math.atan2(max(ch * csp, 1.0) / 2, max(dist, 1)))
            if abs(off_t) - half > halfh:
                continue
            blocking.append((dist, off_t, ch, half * 2))
        blocking.sort()
        wide = sum(b[3] for b in blocking[:40])
        print(f"  {len(blocking)} trees in frame; nearest "
              + (", ".join(f"{b[0]:.0f} m ({b[2]:.0f} m tall, {b[3]:.0f}° wide)"
                           for b in blocking[:4]) if blocking else "none")
              + f"; the nearest 40 cover about {min(100, 100 * wide / (2 * halfh)):.0f}%"
                " of the frame's width")
        # A tree 13 m away at the edge of a street frames the picture; the
        # same tree in the middle of it is a wall. So the number that decides
        # a camera is how much of the CENTRAL 40 degrees — where the subject
        # is — is covered by canopy nearer than 60 m.
        cover = np.zeros(400)
        for dist, off_t, _, wide_t in blocking:
            if dist > 60:
                continue
            lo = (off_t - wide_t / 2 + 20) / 40 * 400
            hi = (off_t + wide_t / 2 + 20) / 40 * 400
            cover[max(0, int(lo)):max(0, int(hi))] = 1
        blocked = 100 * cover.mean()
        gap = min((b[0] for b in blocking), default=float("inf"))
        # Deliberately not a verdict. The canopy is modelled here as a flat
        # disc at the trunk, which says a street lined with trees is 100%
        # blocked when standing in it shows a street. It is a warning that the
        # camera is inside planting; the plate is what decides.
        print(f"  nearest tree {gap:.0f} m; canopy inside 60 m spans "
              f"{blocked:.0f}% of the middle of the frame (a warning, not a "
              "verdict: the plate decides)")

        # Nearest panel row, whatever direction it lies in.
        best = None
        a_rad = math.radians(agri["bearingDegrees"])
        for sx, sz, length, *_ in agri["segments"]:
            ex, ez = sx + math.sin(a_rad) * length, sz - math.cos(a_rad) * length
            for px, pz in ((sx, sz), (ex, ez), ((sx + ex) / 2, (sz + ez) / 2)):
                dist = math.hypot(px - x, pz - z)
                if best is None or dist < best[0]:
                    best = (dist, offset(bearing_of(px - x, pz - z), bearing))
        if best:
            print(f"  nearest panel row end {best[0]:.0f} m, "
                  f"{best[1]:+.0f}° off centre  "
                  f"(rows {agri['rowCentresMetres']:.0f} m apart, "
                  f"{agri['panelHeightMetres']:.1f} m tall, "
                  f"bottom {agri['panelBottomMetres']:.2f} m)")

        # The flight in: does the straight line clear the ground?
        vp = vps.get(c.get("from"))
        if vp:
            a = np.array(vp["pos"], dtype=float)
            worst = None
            for t in np.linspace(0, 1, 400):
                p = a + (eye - a) * t
                g = ground(p[0], p[2])
                room = p[1] - g
                if worst is None or room < worst[0]:
                    worst = (room, float(t))
            print(f"  flight from {c['from']}: closest the straight line comes "
                  f"to the ground is {worst[0]:.1f} m, {100 * worst[1]:.0f}% "
                  f"of the way in")


if __name__ == "__main__":
    raise SystemExit(main())
