"""Where the surveyed features land in a leg's frames, in normalised coordinates.

Phase 5. Session M's finding was that Codex, given references and told to
inspect its own work, drafts, names its own drift and writes itself
coordinate-locked correction prompts — and beats the paid models at £0. Its one
honest complaint was registration: "closely aligned visually, but not
survey-exact", with the woodland rounder, the hedge higher and the stream wider
than the survey says.

That drift is measurable before a single frame is generated, because we know
where everything is. This projects the surveyed features through the leg's own
camera and reports them as normalised image coordinates — the same form the
correction prompts were written in, except derived from the survey rather than
from eyeballing the output. A prompt can then lock them on the FIRST pass.

Usage:
  python3 scripts/measure_leg_anchors.py \\
      experiments/002-living-map/generate/cheltenham-circular-footpath/leg.json
"""
import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"


def load(name):
    return json.loads((GV / name).read_text())


class Camera:
    """The same perspective three.js builds: vertical fov, right-handed."""

    def __init__(self, pos, look, fov_deg, size):
        self.pos = pos
        f = normalise(sub(look, pos))
        # World up is +Y. right = f x up, then a true up orthogonal to both.
        r = normalise(cross(f, (0.0, 1.0, 0.0)))
        self.f, self.r, self.u = f, r, cross(r, f)
        self.tan_half = math.tan(math.radians(fov_deg) / 2)
        self.aspect = size[0] / size[1]

    def project(self, p):
        """Normalised image coordinates, or None if behind or off frame.

        u runs 0 (left) to 1 (right), v runs 0 (top) to 1 (bottom) — the
        convention the correction prompts already use.
        """
        d = sub(p, self.pos)
        z = dot(d, self.f)
        if z <= 0.1:
            return None
        u = 0.5 + (dot(d, self.r) / z) / (self.tan_half * self.aspect) / 2
        v = 0.5 - (dot(d, self.u) / z) / self.tan_half / 2
        return (round(u, 3), round(v, 3), round(z, 1))


sub = lambda a, b: (a[0] - b[0], a[1] - b[1], a[2] - b[2])
dot = lambda a, b: a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
cross = lambda a, b: (a[1] * b[2] - a[2] * b[1],
                      a[2] * b[0] - a[0] * b[2],
                      a[0] * b[1] - a[1] * b[0])


def normalise(v):
    n = math.sqrt(dot(v, v)) or 1.0
    return (v[0] / n, v[1] / n, v[2] / n)


def on_frame(p, margin=0.02):
    return p and -margin <= p[0] <= 1 + margin and -margin <= p[1] <= 1 + margin


def height_field(meta):
    raw = (GV / meta["binFile"]).read_bytes()
    w, h = meta["binPixels"]
    lo, hi = meta["elevationMinMetres"], meta["elevationMaxMetres"]
    sx, sz = meta["widthMetres"], meta["heightMetres"]

    def at(x, z):
        # Nearest sample is enough here: this is for describing a picture, not
        # for standing anything on the ground.
        px = min(max(int((x / sx + 0.5) * (w - 1)), 0), w - 1)
        pz = min(max(int((z / sz + 0.5) * (h - 1)), 0), h - 1)
        i = (pz * w + px) * 2
        return lo + (raw[i] | (raw[i + 1] << 8)) / 65535 * (hi - lo)

    return at


def describe(leg_file):
    leg = json.loads(Path(leg_file).read_text())
    meta = load("gv-meta.json")
    paths = load("gv-paths.json")
    buildings = load("gv-buildings.json")
    # A plate rendered with the wave up also has the 2045 blocks standing in
    # it, and they are most of what the frame is about. They carry no names —
    # nothing invented gets to be a landmark — so they are reported as a band
    # and a few largest blocks rather than as places.
    future = []
    if leg.get("wave", 0) >= 0.5 and (GV / "gv-2045-buildings.json").exists():
        future = load("gv-2045-buildings.json")
    ground = height_field(meta)

    # A composed plate has no route through it; a leg does. Everything else
    # here is the same measurement either way.
    route = next((r for r in paths["routes"]
                  if r["id"] == leg.get("route", {}).get("id")), None)
    size = leg["camera"]["size"]

    out = []
    for frame in leg["frames"]:
        cam = Camera(tuple(frame["pos"]), tuple(frame["look"]),
                     leg["camera"]["fov"], size)
        anchors = {}

        # The horizon: a point at the camera's own height, effectively at
        # infinity. Where it lands is the single strongest lock in the prompt,
        # because a generator that raises it has invented landscape.
        far = tuple(cam.pos[i] + cam.f[i] * 20000 for i in range(3))
        h = cam.project((far[0], cam.pos[1], far[2]))
        anchors["horizonV"] = h[1] if h else None

        # The path itself, at fixed distances ahead. This is the line the
        # picture is about, and the thing a generator most wants to straighten.
        track = []
        if route is not None:
            here = leg["leg"]["from"] + frame["atMetres"]
            arc = [0.0]
            pts = [(p[0], ground(p[0], p[1]), p[1]) for p in route["points"]]
            for a, b in zip(pts, pts[1:]):
                arc.append(arc[-1] + math.dist(a, b))
            aheads = (20, 40, 80, 160, 320)
        else:
            here, arc, pts, aheads = 0, [0.0], [], ()
        for ahead in aheads:
            d = here + ahead
            if d > arc[-1]:
                break
            i = next(k for k in range(1, len(arc)) if arc[k] >= d)
            t = (d - arc[i - 1]) / max(arc[i] - arc[i - 1], 1e-6)
            p = tuple(pts[i - 1][k] + (pts[i][k] - pts[i - 1][k]) * t for k in range(3))
            q = cam.project(p)
            if on_frame(q):
                track.append({"metresAhead": ahead, "u": q[0], "v": q[1]})
        anchors["path"] = track

        # Streams and hedges: the two features Session M watched drift every
        # time. Reported as where the line crosses the frame, because "the
        # stream leaves the right edge at v=0.41" is a lock and "there is a
        # stream" is an invitation.
        marks = []
        for lm in paths.get("landmarks", []):
            hit = []
            for x, z in lm["points"]:
                q = cam.project((x, ground(x, z), z))
                if on_frame(q, 0.0) and q[2] < 900:
                    hit.append(q)
            if len(hit) < 3:
                continue
            marks.append({
                "kind": lm["kind"],
                "nearestMetres": round(min(q[2] for q in hit)),
                "enters": {"u": hit[0][0], "v": hit[0][1]},
                "leaves": {"u": hit[-1][0], "v": hit[-1][1]},
                "spanU": [round(min(q[0] for q in hit), 3),
                          round(max(q[0] for q in hit), 3)],
            })
        marks.sort(key=lambda m: m["nearestMetres"])
        anchors["landmarks"] = marks[:4]

        # The 2045 development, if this plate has it.
        if future:
            seen = []
            for b in future:
                ring = b["ring"]
                cx2 = sum(p[0] for p in ring) / len(ring)
                cz2 = sum(p[1] for p in ring) / len(ring)
                base = cam.project((cx2, b["base"], cz2))
                top = cam.project((cx2, b["base"] + b["height"], cz2))
                if on_frame(base) and base[2] < 2000:
                    seen.append((b, base, top))
            if seen:
                fam = {}
                for b, base, top in seen:
                    fam[b["family"]] = fam.get(b["family"], 0) + 1
                big = sorted(seen, key=lambda x: -x[0]["height"])[:3]
                anchors["development"] = {
                    "blocksInFrame": len(seen),
                    "byFamily": fam,
                    "uFrom": round(min(x[1][0] for x in seen), 3),
                    "uTo": round(min(1.0, max(x[1][0] for x in seen)), 3),
                    "vFrom": round(min(x[2][1] for x in seen if x[2]), 3),
                    "vTo": round(max(x[1][1] for x in seen), 3),
                    "nearestMetres": round(min(x[1][2] for x in seen)),
                    "tallest": [{"family": b["family"], "heightMetres": b["height"],
                                 "u": base[0], "vBase": base[1],
                                 "vRoof": top[1] if top else None}
                                for b, base, top in big],
                }

        # Buildings, split by distance, because the two groups are different
        # instructions. Anything close is an individual object a generator can
        # delete or invent; the mass beyond is a band whose roofline height is
        # the lock — raise it and the settlement has grown, lower it and the
        # field has.
        near, far_ = [], []
        for b in buildings:
            ring = b["ring"]
            cx = sum(p[0] for p in ring) / len(ring)
            cz = sum(p[1] for p in ring) / len(ring)
            base = cam.project((cx, b["base"], cz))
            top = cam.project((cx, b["base"] + b["height"], cz))
            if not on_frame(base) or base[2] > 1600:
                continue
            (near if base[2] < 200 else far_).append((b, base, top))

        # Named buildings, wherever they are. GCHQ sits 764 m from the start of
        # this leg and is edge-on, a low dark band a few pixels tall — and a
        # generator asked to interpret a low dark band made it a long pale
        # shed. Naming it, and saying exactly which pixels it occupies, is the
        # difference between a material instruction and an invitation.
        named_b = []
        for b, base, top in near + far_:
            if not b.get("name"):
                continue
            ring = b["ring"]
            us, vs = [], []
            for x, z in ring:
                for y in (b["base"], b["base"] + b["height"]):
                    q = cam.project((x, y, z))
                    if q:
                        us.append(q[0])
                        vs.append(q[1])
            if not us:
                continue
            entry = {
                "name": b["name"], "metres": base[2],
                "u": [round(min(us), 3), round(max(us), 3)],
                "v": [round(min(vs), 3), round(max(vs), 3)],
            }
            # A courtyard is a hole in the footprint, and it is the one part of
            # GCHQ a generator reliably gets wrong — Session M had to tell it
            # twice not to enlarge the hole, and once not to fill it with water.
            hu, hv = [], []
            for hole in b.get("holes") or []:
                for x, z in hole:
                    q = cam.project((x, b["base"] + b["height"], z))
                    if q:
                        hu.append(q[0])
                        hv.append(q[1])
            if hu:
                entry["courtyardU"] = [round(min(hu), 3), round(max(hu), 3)]
                entry["courtyardV"] = [round(min(hv), 3), round(max(hv), 3)]
            named_b.append(entry)
        # One entry per name: a campus arrives as many footprints and the
        # prompt wants the box round all of them.
        merged = {}
        for n in named_b:
            m = merged.setdefault(n["name"], dict(n))
            m["u"] = [min(m["u"][0], n["u"][0]), max(m["u"][1], n["u"][1])]
            m["v"] = [min(m["v"][0], n["v"][0]), max(m["v"][1], n["v"][1])]
            m["metres"] = min(m["metres"], n["metres"])
            for k in ("courtyardU", "courtyardV"):
                if k in n:
                    m[k] = n[k]
        # Only the ones that are actually a shape in the picture. OSM names
        # every shop on Coronation Square, and a kebab house 1.5 km away
        # occupying four thousandths of the frame is noise in a prompt, not a
        # lock — it buries the one entry that matters.
        anchors["namedBuildings"] = sorted(
            (n for n in merged.values()
             if n["u"][1] - n["u"][0] >= 0.035 and n["metres"] <= 1200),
            key=lambda n: -(n["u"][1] - n["u"][0]))[:4]

        anchors["nearBuildings"] = [
            {"name": b.get("name"), "metres": base[2],
             "u": base[0], "vBase": base[1], "vRoof": top[1] if top else None}
            for b, base, top in sorted(near, key=lambda x: x[1][2])[:5]
        ]
        if far_:
            # The visible top of the settlement is the highest roof, not the
            # average of them: that is the line the eye reads as the edge.
            roofs = sorted(t[1] for _, _, t in far_ if t)
            anchors["settlementEdge"] = {
                "count": len(far_),
                "uFrom": round(min(b[1][0] for b in far_), 3),
                "uTo": round(min(1.0, max(b[1][0] for b in far_)), 3),
                "vRooflineTop": round(roofs[max(0, len(roofs) // 40)], 3),
                "vBaseTypical": round(
                    sorted(b[1][1] for b in far_)[len(far_) // 2], 3),
                "nearestMetres": round(min(b[1][2] for b in far_)),
            }
        out.append({"file": frame["file"], "anchors": anchors})
    return leg, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("leg", help="path to a leg.json written by capture_path_leg.py")
    args = ap.parse_args()

    leg, frames = describe(args.leg)
    # Named after its input unless the input is the canonical `leg.json` or
    # `plate.json`, whose sidecars two published briefs already point at. A
    # fixed name was fine while a folder held one plate and silently wrong the
    # moment it held three: each run overwrote the last and every table in the
    # brief came out identical.
    src = Path(args.leg).resolve()
    dest = src.with_name("anchors.json" if src.stem in ("leg", "plate")
                         else f"{src.stem}-anchors.json")
    dest.write_text(json.dumps({
        "note": ("Surveyed features projected through this leg's own camera, "
                 "as normalised image coordinates: u is 0 at the left edge and "
                 "1 at the right, v is 0 at the top and 1 at the bottom. These "
                 "are what a generated frame must not move."),
        "route": leg.get("route", {}).get("name"),
        "frames": frames,
    }, indent=2) + "\n")

    for f in frames:
        a = f["anchors"]
        print(f"\n{f['file']}")
        print(f"  horizon        v={a['horizonV']}")
        for p in a["path"]:
            print(f"  path {p['metresAhead']:>4} m ahead   u={p['u']:<7} v={p['v']}")
        if a.get("development"):
            d2 = a["development"]
            print(f"  DEVELOPMENT    {d2['blocksInFrame']} blocks {d2['byFamily']}, "
                  f"u={d2['uFrom']}..{d2['uTo']}  v={d2['vFrom']}..{d2['vTo']}, "
                  f"nearest {d2['nearestMetres']} m")
            for t in d2["tallest"]:
                print(f"     {t['family']:<11} {t['heightMetres']:>5.1f} m   "
                      f"u={t['u']}  base v={t['vBase']}  roof v={t['vRoof']}")
        for m in a.get("landmarks", []):
            print(f"  {m['kind']:<14} {m['nearestMetres']:>4} m   enters "
                  f"u={m['enters']['u']},v={m['enters']['v']}  leaves "
                  f"u={m['leaves']['u']},v={m['leaves']['v']}")
        for n in a.get("namedBuildings", []):
            print(f"  NAMED          {n['metres']:>5.0f} m   u={n['u'][0]}..{n['u'][1]}  "
                  f"v={n['v'][0]}..{n['v'][1]}   {n['name']}")
            if "courtyardU" in n:
                print(f"     courtyard             u={n['courtyardU'][0]}..{n['courtyardU'][1]}  "
                      f"v={n['courtyardV'][0]}..{n['courtyardV'][1]}")
        for n in a.get("nearBuildings", []):
            print(f"  near building  {n['metres']:>5.0f} m   u={n['u']:<7} "
                  f"base v={n['vBase']:<7} roof v={n['vRoof']}"
                  + (f"   {n['name']}" if n.get("name") else ""))
        if a.get("settlementEdge"):
            b = a["settlementEdge"]
            print(f"  settlement     {b['count']} buildings, u={b['uFrom']}..{b['uTo']}, "
                  f"roofline top v={b['vRooflineTop']}, base v={b['vBaseTypical']}, "
                  f"nearest {b['nearestMetres']} m")
    print(f"\nwrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
