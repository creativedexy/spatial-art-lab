"""The path network, as lines the map can touch.

Phase 5a. The footpaths are already *in* the map — golden_valley_landcover.py
paints them into gv-landcover.png at a metre a texel, which is the right way
to make them look correct and the wrong way to make them mean anything. A
texel has no identity: you cannot hover it, name it, light it or walk it.

So the same paths come out a second time here, as polylines. Two forms of the
same truth, each doing the job the other cannot:

  gv-landcover.png    what a path LOOKS like     (pixels, exact, free to draw)
  gv-paths.json       what a path IS             (a route, named, with ends)

Two tiers, because a hub view showing all 482 path fragments equally is a
diagram, not a place:

  named routes   the walking and cycling routes OSM carries as relations —
                 the Cheltenham Circular Footpath, the Gloucestershire Cycle
                 Spine. These are the ones that get a label and can be
                 chosen. They exist; we are revealing them, not inventing.
  strands        everything else above a length threshold, chained through
                 junctions into continuous runs. Drawn as a fainter web, so
                 the vale reads as somewhere with a grain to it.

No Y, for the same reason the trees carry no Y: the map computes ground
height from the height field, so a path cannot float or sink if either the
terrain or the route ever changes. See drapePath in golden-valley/paths.js.

Usage:  python3 scripts/golden_valley_paths.py [--out DIR] [--dry-run]

Path network: (c) OpenStreetMap contributors, ODbL.
"""
import argparse
import json
import math
import os
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "002-living-map" / "golden-valley"
OSM_CACHE = "/tmp/gv_osm.xml"
E0, E1 = 390400, 392400
N0, N1 = 221400, 223400
CX, CZ = E0 + (E1 - E0) / 2, N0 + (N1 - N0) / 2   # local origin, in BNG

# What counts as something you could walk or ride. `track` is in because a
# farm track across the Golden Valley fields is exactly the kind of route the
# site's own paths will one day continue; `steps` is in because leaving it out
# breaks the network at every footbridge.
KINDS = {
    "footway": "foot", "path": "foot", "pedestrian": "foot",
    "bridleway": "bridle", "cycleway": "cycle", "steps": "steps",
    "track": "track",
}
# A crossing is five metres of paint across a carriageway. It belongs in the
# graph — without it the network falls apart at every road — but it is not a
# route, so it never survives the length filter on its own.
STEP_METRES = 4.0        # resample spacing: fine enough to hug a hill
MIN_STRAND = 80.0        # metres; below this it is a driveway, not a way
BOX_MARGIN = 2.0         # metres of slack before a point counts as outside


def tags_of(el):
    return {t.get("k"): t.get("v") for t in el if t.tag == "tag"}


def fetch_osm():
    if not os.path.exists(OSM_CACHE):
        to_wgs = Transformer.from_crs(27700, 4326, always_xy=True)
        w, s = to_wgs.transform(E0, N0)
        e, n = to_wgs.transform(E1, N1)
        url = f"https://api.openstreetmap.org/api/0.6/map?bbox={w},{s},{e},{n}"
        print(f"fetching {url}")
        with urllib.request.urlopen(url, timeout=180) as r, \
                open(OSM_CACHE, "wb") as f:
            f.write(r.read())
    return ET.parse(OSM_CACHE).getroot()


# --- geometry ---------------------------------------------------------------

def inside(p):
    return abs(p[0]) <= (E1 - E0) / 2 + BOX_MARGIN and \
           abs(p[1]) <= (N1 - N0) / 2 + BOX_MARGIN


def runs_inside(pts):
    """Split a polyline into the runs that lie in the box.

    Dropped rather than clamped: clamping would draw a route running dead
    straight along the box edge, which is a line the ground does not have.
    """
    out, cur = [], []
    for p in pts:
        if inside(p):
            cur.append(p)
        elif cur:
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return [r for r in out if len(r) >= 2]


def length_of(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(pts, step=STEP_METRES):
    """Even spacing along the line, both original ends kept.

    Even spacing is what lets the map drape the route on the terrain without
    cutting corners through a hill: OSM records a straight field-edge path as
    two nodes 300 m apart, and a straight line between them would run through
    the rise in the middle of it.
    """
    if len(pts) < 2:
        return pts
    out = [pts[0]]
    carry = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        seg = math.dist(a, b)
        if seg <= 1e-9:
            continue
        t = step - carry
        while t <= seg:
            k = t / seg
            out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
            t += step
        carry = (carry + seg) % step
    if math.dist(out[-1], pts[-1]) > step * 0.35:
        out.append(pts[-1])
    else:
        out[-1] = pts[-1]
    return out


# --- the graph --------------------------------------------------------------

def read_paths():
    """Every walkable way in the box, as an undirected graph of nodes."""
    root = fetch_osm()
    to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
    nodes = {}
    for n in root.iter("node"):
        e, nn = to_bng.transform(float(n.get("lon")), float(n.get("lat")))
        # Local metres: x east, z south, origin at the box centre — the same
        # frame as gv-buildings.json and the tree instances.
        nodes[n.get("id")] = (e - CX, CZ - nn)

    ways = {}
    for w in root.iter("way"):
        tags = tags_of(w)
        kind = KINDS.get(tags.get("highway"))
        if kind is None:
            continue
        if tags.get("tunnel") in ("yes", "building_passage") or \
                tags.get("area") == "yes" or tags.get("access") in ("private", "no"):
            continue
        refs = [nd.get("ref") for nd in w if nd.tag == "nd"]
        refs = [r for r in refs if r in nodes]
        if len(refs) < 2:
            continue
        ways[w.get("id")] = {
            "kind": kind, "tags": tags, "refs": refs,
            "name": tags.get("name"),
            "crossing": tags.get("footway") == "crossing",
        }
    return nodes, ways, root


def trace_strands(nodes, ways):
    """Chain ways through their shared nodes into continuous runs.

    OSM splits a single footpath wherever a tag changes — surface, lit, a
    bridge — so the raw ways are fragments. What a walker experiences is the
    run between one junction and the next, which is what this recovers:
    contract every degree-2 node away, and keep what is left.
    """
    adj = defaultdict(list)          # node -> [(other, edge_id)]
    edges = {}                       # edge_id -> way id
    for wid, w in ways.items():
        for a, b in zip(w["refs"], w["refs"][1:]):
            if a == b:
                continue
            eid = len(edges)
            edges[eid] = wid
            adj[a].append((b, eid))
            adj[b].append((a, eid))

    seen = set()
    strands = []

    def walk(start, first_edge):
        chain = [start]
        used = []
        node, eid = start, first_edge
        while True:
            used.append(eid)
            seen.add(eid)
            nxt = next(o for o, e in adj[node] if e == eid)
            chain.append(nxt)
            node = nxt
            if len(adj[node]) != 2 or node == start:
                break
            nxt_edge = next((e for _, e in adj[node] if e != eid), None)
            if nxt_edge is None or nxt_edge in seen:
                break
            eid = nxt_edge
        return chain, used

    # Runs between junctions and dead ends.
    for node in list(adj):
        if len(adj[node]) == 2:
            continue
        for _, eid in adj[node]:
            if eid in seen:
                continue
            strands.append(walk(node, eid))

    # Closed loops with no junction on them at all — a circular path round a
    # park has no degree-2 exception to start from, so it needs its own pass.
    for eid in list(edges):
        if eid in seen:
            continue
        start = next(n for n, links in adj.items()
                     if any(e == eid for _, e in links))
        strands.append(walk(start, eid))

    out = []
    for chain, used in strands:
        wids = [edges[e] for e in used]
        kind = Counter(ways[w]["kind"] for w in wids).most_common(1)[0][0]
        names = [ways[w]["name"] for w in wids if ways[w]["name"]]
        crossing = all(ways[w]["crossing"] for w in wids)
        out.append({
            "pts": [nodes[n] for n in chain],
            "kind": kind,
            "name": Counter(names).most_common(1)[0][0] if names else None,
            "crossing": crossing,
        })
    return out


def read_routes(root, nodes, ways):
    """The named walking and cycling routes, chained in member order."""
    routes = []
    for rel in root.iter("relation"):
        tags = tags_of(rel)
        if tags.get("type") != "route" or \
                tags.get("route") not in ("foot", "hiking", "bicycle", "horse"):
            continue
        members = [m.get("ref") for m in rel
                   if m.tag == "member" and m.get("type") == "way"]
        # A route relation lists its ways in walking order but not in a
        # consistent direction: consecutive members meet head-to-head as often
        # as head-to-tail, so each one is flipped to match the chain so far.
        chain = []
        for ref in members:
            refs = ways.get(ref, {}).get("refs")
            if not refs:
                # Not a walkable way (a road section of a cycle route), or
                # outside what we hold. Break the chain rather than jump it.
                if chain:
                    routes.append((tags, chain))
                    chain = []
                continue
            if not chain:
                chain = list(refs)
                continue
            if chain[-1] == refs[0]:
                chain += refs[1:]
            elif chain[-1] == refs[-1]:
                chain += refs[-2::-1]
            elif chain[0] == refs[-1]:
                chain = refs[:-1] + chain
            elif chain[0] == refs[0]:
                chain = refs[::-1][:-1] + chain
            else:
                routes.append((tags, chain))
                chain = list(refs)
        if chain:
            routes.append((tags, chain))

    out = []
    for tags, chain in routes:
        pts = [nodes[n] for n in chain if n in nodes]
        for run in runs_inside(pts):
            out.append({
                "pts": run,
                "name": tags.get("name") or tags.get("ref"),
                "route": tags.get("route"),
                "network": tags.get("network"),
            })
    return out


# --- assembly ---------------------------------------------------------------

def slug(text, used):
    s = "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    base, i = s, 2
    while s in used:
        s, i = f"{base}-{i}", i + 1
    used.add(s)
    return s


def cells_of(points, size=12):
    """Coarse occupancy, for asking whether two routes are the same ground."""
    return {(round(x / size), round(z / size)) for x, z in points}


def dedupe(routes, overlap=0.85):
    """Drop a route whose ground another route already covers.

    Kept: the one with the more useful name. A bare `ref` like "41" is a
    designation; "Gloucestershire Cycle Spine" is what it is called.
    """
    routes = sorted(routes, key=lambda r: (-len(r["name"] or ""), -r["lengthMetres"]))
    out = []
    for r in routes:
        c = cells_of(r["points"])
        if any(len(c & cells_of(k["points"])) > len(c) * overlap for k in out):
            continue
        out.append(r)
    return out


def build():
    nodes, ways, root = read_paths()
    print(f"walkable ways {len(ways)}")

    used_ids = set()
    named, strands = [], []

    # Named routes first, so they own their slugs and so the strands that
    # duplicate them can be recognised and dropped.
    raw_named = read_routes(root, nodes, ways)
    by_name = defaultdict(list)
    for r in raw_named:
        by_name[r["name"] or "unnamed route"].append(r)
    for name, parts in by_name.items():
        parts.sort(key=lambda r: -length_of(r["pts"]))
        for i, r in enumerate(parts):
            L = length_of(r["pts"])
            if L < MIN_STRAND:
                continue
            pts = resample(r["pts"])
            named.append({
                "id": slug(name if i == 0 else f"{name} {i + 1}", used_ids),
                "name": name,
                "tier": "named",
                "kind": "cycle" if r["route"] == "bicycle" else "foot",
                "network": r["network"],
                "lengthMetres": round(L, 1),
                "points": [[round(x, 2), round(z, 2)] for x, z in pts],
            })

    # NCN 41 and the Gloucestershire Cycle Spine are the same tarmac here —
    # one route relation per designation, both listing the same ways. Two
    # lines drawn over each other is a brighter line, not a second route, so
    # the duplicate goes and the one with the name people use survives.
    named = dedupe(named)
    for name in {r["name"] for r in named}:
        parts = [r for r in named if r["name"] == name]
        # A route that leaves the box and comes back is genuinely two runs of
        # ground. Both are drawn; only the longest carries the label, so the
        # aerial does not say "Cheltenham Circular Footpath" twice.
        parts.sort(key=lambda r: -r["lengthMetres"])
        for i, r in enumerate(parts):
            r["primary"] = i == 0

    # Everything the named routes already cover, so the web underneath them is
    # the rest of the network rather than a second copy of the same lines.
    claimed = set()
    for r in named:
        for x, z in r["points"]:
            claimed.add((round(x / 12), round(z / 12)))

    for s in trace_strands(nodes, ways):
        if s["crossing"]:
            continue
        for run in runs_inside(s["pts"]):
            L = length_of(run)
            if L < MIN_STRAND:
                continue
            cells = {(round(x / 12), round(z / 12)) for x, z in run}
            if len(cells & claimed) > len(cells) * 0.75:
                continue
            pts = resample(run)
            strands.append({
                "id": slug(s["name"] or f"{s['kind']}-strand", used_ids),
                "name": s["name"],
                "tier": "strand",
                "kind": s["kind"],
                "lengthMetres": round(L, 1),
                "points": [[round(x, 2), round(z, 2)] for x, z in pts],
            })

    named.sort(key=lambda r: -r["lengthMetres"])
    strands.sort(key=lambda r: -r["lengthMetres"])
    return named, strands


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be written, write nothing")
    args = ap.parse_args()

    named, strands = build()
    routes = named + strands
    total = sum(r["lengthMetres"] for r in routes) / 1000
    pts = sum(len(r["points"]) for r in routes)

    print(f"\nnamed routes {len(named)}")
    for r in named:
        print(f"   {r['lengthMetres']:8.1f} m  {r['id']:<34s} {r['name']}")
    print(f"\nstrands {len(strands)}  (longest 8)")
    for r in strands[:8]:
        print(f"   {r['lengthMetres']:8.1f} m  {r['id']:<34s} {r['kind']}")
    by_kind = Counter(r["kind"] for r in routes)
    print(f"\nkinds {dict(by_kind)}")
    print(f"total {total:.2f} km over {pts} points")

    doc = {
        "note": ("Walkable routes in the Golden Valley box, as polylines "
                 "rather than texels, so a path can be named, lit, chosen and "
                 "walked. Points are local metres (x east, z south, origin at "
                 "the box centre) and carry no height: the map drapes them on "
                 "the same height field the terrain is built from. `named` "
                 "routes come from OSM route relations and are the ones "
                 "offered as destinations; `strand` routes are the rest of "
                 "the network, chained through junctions, drawn as context."),
        "generatedBy": "scripts/golden_valley_paths.py",
        "source": "OpenStreetMap contributors, ODbL",
        "frame": {"crs": "EPSG:27700", "easting": [E0, E1],
                  "northing": [N0, N1], "originEasting": CX,
                  "originNorthing": CZ},
        "stepMetres": STEP_METRES,
        "minStrandMetres": MIN_STRAND,
        "counts": {"named": len(named), "strands": len(strands),
                   "kilometres": round(total, 2), "points": pts},
        "routes": routes,
    }
    if args.dry_run:
        print("\n--dry-run: nothing written")
        return
    dest = Path(args.out) / "gv-paths.json"
    dest.write_text(json.dumps(doc, separators=(",", ":")))
    print(f"\nwrote {dest}  {dest.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
