"""Land cover, roads and trees for the living map, from the OSM we already hold.

Phase 2 of plans/living-map-lookdev-plan.md, plus the tree half of Phase 3.

The terrain is real and the buildings are measured, but the ground between
them has been one green blanket, so the vale reads as a lawn with boxes on
it. OSM already carries what is actually there — woods, playing fields,
farmland, water, car parks and the whole road network — inside the same
2 x 2 km box the buildings came from.

Three outputs, and the split matters:

  gv-landcover.png   a 1 m/texel colour image of the ground, roads baked in
                     as drawn lines. Roads as *texture* rather than geometry
                     is deliberate: a 4 m service road is thinner than the
                     terrain mesh's 2 m triangles, so as geometry it would
                     shimmer and z-fight, while as texels it is exact and
                     costs one draw call for the entire network.
  gv-trees.bin       tree instances as 8-byte records, for InstancedMesh.
                     No Y: the map computes it from the height field, so the
                     trees cannot drift from the terrain if either changes.
  gv-landclass.png   the same rasterisation as class indices rather than
                     colour. Nothing renders it yet; it is what Phase 4 needs
                     to know where the vegetation is that the wind moves and
                     where the water is that ripples, and it costs 170 KB to
                     keep rather than a rebuild to recover.

All three are keyed to the box in gv-meta.json: pixel (0,0) is the north-west
corner, one pixel is one metre, and local metres are x east, z south from the
box centre — the same frame as gv-buildings.json.

Usage:  python3 scripts/golden_valley_landcover.py [--out DIR]

Land cover, roads and trees: (c) OpenStreetMap contributors, ODbL.
"""
import argparse
import json
import math
import os
import random
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from pyproj import Transformer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "experiments" / "002-living-map" / "golden-valley"
OSM_CACHE = "/tmp/gv_osm.xml"
E0, E1 = 390400, 392400
N0, N1 = 221400, 223400
SS = 2                      # supersample factor for the colour image

# The palette. Flat colours on purpose: large uniform regions is what makes a
# 2000 px PNG compress to a few hundred KB, and the variation that stops it
# reading as a paint-by-numbers comes from light and slope in the scene, not
# from noise baked into the texture.
BASE = "farmland"
CLASSES = {
    "farmland":    0x7d9460,
    "meadow":      0x93a566,
    "grass":       0x8ca767,
    "pitch":       0x7fa457,   # mown, watered, and a shade bluer than pasture
    "park":        0x86a05c,
    "scrub":       0x74855a,
    "wood":        0x4a6440,   # the floor under a canopy, not the canopy
    "residential": 0x8d947a,   # gardens, drives and roofs averaged together
    "hardstanding":0x9c9c94,
    "parking":     0x7d7d78,
    "water":       0x5c7f8c,
    "path":        0x9a9083,
    "road_minor":  0x6f6f6a,
    "road":        0x64645f,
    "rail":        0x5f5b54,
    # Appended rather than inserted, because the class index is written into
    # gv-landclass.png and read by name elsewhere — a new class in the middle
    # would silently renumber every texel already shipped.
    "concrete":    0xa9a59b,
    # Desaturated hard. A farm track is a pale grey-brown, and under a low
    # warm sun anything with real ochre in it comes out as a red scratch
    # drawn across a green field.
    "unpaved":     0x8d8676,
}
INDEX = {name: i for i, name in enumerate(CLASSES)}
# PIL reads an integer fill lowest-byte-first, so 0x7d9460 paints as BGR.
RGB_OF = lambda v: ((v >> 16) & 255, (v >> 8) & 255, v & 255)
RGB = {name: RGB_OF(v) for name, v in CLASSES.items()}

# tag -> class, tried in this order. First match wins, so put the specific
# tags above the general ones.
AREA_TAGS = [
    (("natural", "wood"), "wood"),
    (("landuse", "forest"), "wood"),
    (("natural", "scrub"), "scrub"),
    (("natural", "water"), "water"),
    (("natural", "wetland"), "water"),
    (("landuse", "reservoir"), "water"),
    (("landuse", "basin"), "water"),
    (("waterway", "riverbank"), "water"),
    (("amenity", "parking"), "parking"),
    (("leisure", "pitch"), "pitch"),
    (("leisure", "playground"), "hardstanding"),
    (("leisure", "park"), "park"),
    (("leisure", "garden"), "park"),
    (("leisure", "recreation_ground"), "park"),
    (("leisure", "golf_course"), "park"),
    (("landuse", "cemetery"), "park"),
    (("amenity", "grave_yard"), "park"),
    (("landuse", "grass"), "grass"),
    (("landuse", "village_green"), "grass"),
    (("landuse", "meadow"), "meadow"),
    (("landuse", "farmland"), "farmland"),
    (("landuse", "orchard"), "meadow"),
    (("landuse", "allotments"), "meadow"),
    (("landuse", "farmyard"), "hardstanding"),
    (("landuse", "industrial"), "hardstanding"),
    (("landuse", "retail"), "hardstanding"),
    (("landuse", "commercial"), "hardstanding"),
    (("landuse", "construction"), "hardstanding"),
    (("landuse", "brownfield"), "scrub"),
    (("landuse", "residential"), "residential"),
    (("landuse", "school"), "grass"),
    (("amenity", "school"), "grass"),
]
# highway/railway -> (class, carriageway width in metres). Widths are the
# metalled surface plus its verge shoulder, which is what you actually see
# from the air.
WAY_WIDTHS = {
    "trunk": ("road", 15.0), "trunk_link": ("road", 9.0),
    "primary": ("road", 12.0), "primary_link": ("road", 8.0),
    "secondary": ("road", 10.0), "secondary_link": ("road", 7.0),
    "tertiary": ("road", 8.5), "tertiary_link": ("road", 6.5),
    "unclassified": ("road_minor", 6.5), "residential": ("road_minor", 6.5),
    "living_street": ("road_minor", 5.5), "service": ("road_minor", 4.0),
    "pedestrian": ("path", 4.0), "footway": ("path", 1.8),
    "path": ("path", 1.6), "cycleway": ("path", 2.4),
    "bridleway": ("path", 1.8), "track": ("path", 3.0), "steps": ("path", 1.6),
}
# Minor first so a trunk road is never cut by the service road joining it.
ROAD_ORDER = ["path", "road_minor", "rail", "road", "concrete", "unpaved"]

# OSM's `surface` tag, on 577 ways in this box. It is the closest thing to a
# material the data actually carries — building:material appears zero times —
# and it is worth having, because a gravel farm track and a resurfaced trunk
# road are the same width and nothing like the same colour from the air.
SURFACE = {
    "asphalt": None, "paved": None, "chipseal": None, "tarmac": None,
    "concrete": "concrete", "concrete:plates": "concrete",
    "paving_stones": "concrete", "sett": "concrete", "cobblestone": "concrete",
    "unpaved": "unpaved", "gravel": "unpaved", "fine_gravel": "unpaved",
    "compacted": "unpaved", "ground": "unpaved", "dirt": "unpaved",
    "earth": "unpaved", "sand": "unpaved",
    "grass": "grass",
}
# A lane is about 3.1 m of running surface, plus a shoulder either side. Used
# only where OSM says how many there are — 134 ways here — because a guessed
# lane count is just the default width wearing a hat.
LANE_METRES = 3.1
LANE_MARKED = {"trunk", "primary", "secondary", "tertiary"}
MARKING = 0xbdb9ae

# Where trees come from, and how thick. `spacing` is metres between trunks on
# a jittered grid, so a wood at 6.5 m is roughly 24 stems per 1000 m2 — thick
# enough to read as canopy from the air without generating a quarter of a
# million instances.
SCATTER = {
    "wood":        {"spacing": 6.5, "height": (11, 19), "kind": 0},
    "scrub":       {"spacing": 9.0, "height": (3.5, 6.5), "kind": 1},
    "park":        {"spacing": 17.0, "height": (7, 14), "kind": 0},
    "residential": {"spacing": 26.0, "height": (5, 10), "kind": 0},
}
HEDGE_SPACING = 2.2
HEDGE_HEIGHT = (1.6, 2.6)


def fetch_osm():
    if not os.path.exists(OSM_CACHE):
        to_wgs = Transformer.from_crs(27700, 4326, always_xy=True)
        lon0, lat0 = to_wgs.transform(E0, N0)
        lon1, lat1 = to_wgs.transform(E1, N1)
        urllib.request.urlretrieve(
            "https://api.openstreetmap.org/api/0.6/map?bbox="
            f"{lon0:.4f},{lat0:.4f},{lon1:.4f},{lat1:.4f}", OSM_CACHE)
    return ET.parse(OSM_CACHE).getroot()


def tags_of(el):
    return {t.get("k"): t.get("v") for t in el.iter("tag")}


def classify(tags):
    if tags.get("building"):
        return None            # buildings are geometry, not ground
    for (k, v), cls in AREA_TAGS:
        if tags.get(k) == v:
            return cls
    return None


def stitch(rings):
    """Join open member ways into closed rings (OSM multipolygon outers)."""
    out, pool = [], [list(r) for r in rings if len(r) >= 2]
    while pool:
        cur = pool.pop(0)
        changed = True
        while changed and (cur[0] != cur[-1]):
            changed = False
            for i, other in enumerate(pool):
                for seq in (other, other[::-1]):
                    if seq[0] == cur[-1]:
                        cur += seq[1:]
                        pool.pop(i)
                        changed = True
                        break
                    if seq[-1] == cur[0]:
                        cur = seq[:-1] + cur
                        pool.pop(i)
                        changed = True
                        break
                if changed:
                    break
        if len(cur) >= 4:
            out.append(cur)
    return out


def ring_area(ring):
    a = 0.0
    for (x0, y0), (x1, y1) in zip(ring, ring[1:] + ring[:1]):
        a += x0 * y1 - x1 * y0
    return abs(a) / 2


def read_world():
    """Everything the box holds, in pixels: (0,0) is the north-west corner."""
    root = fetch_osm()
    to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
    nodes = {}
    tree_points = []
    for n in root.iter("node"):
        e, nn = to_bng.transform(float(n.get("lon")), float(n.get("lat")))
        p = (e - E0, N1 - nn)
        nodes[n.get("id")] = p
        if tags_of(n).get("natural") == "tree":
            tree_points.append(p)

    ways = {}
    for w in root.iter("way"):
        pts = [nodes[nd.get("ref")] for nd in w.iter("nd") if nd.get("ref") in nodes]
        if pts:
            ways[w.get("id")] = {"tags": tags_of(w), "pts": pts}

    areas, lines, claimed = [], [], set()
    for r in root.iter("relation"):
        tags = tags_of(r)
        cls = classify(tags)
        if cls is None or tags.get("type") not in ("multipolygon", "boundary"):
            continue
        members = {"outer": [], "inner": []}
        for m in r.iter("member"):
            ref, role = m.get("ref"), m.get("role") or "outer"
            if m.get("type") == "way" and ref in ways and role in members:
                members[role].append(ways[ref]["pts"])
                claimed.add(ref)
        for ring in stitch(members["outer"]):
            areas.append({"cls": cls, "ring": ring,
                          "holes": stitch(members["inner"])})

    for wid, w in ways.items():
        tags, pts = w["tags"], w["pts"]
        highway = tags.get("highway")
        if highway in WAY_WIDTHS:
            cls, width = WAY_WIDTHS[highway]
            if tags.get("tunnel") in ("yes", "building_passage"):
                continue
            lanes = tags.get("lanes", "")
            if lanes.isdigit() and 0 < int(lanes) <= 8:
                width = max(width, int(lanes) * LANE_METRES + 1.4)
            if tags.get("width", "").replace(".", "", 1).isdigit():
                width = max(width, float(tags["width"]) + 1.0)
            surface = SURFACE.get(tags.get("surface", ""), "keep")
            if surface != "keep" and surface is not None:
                cls = surface
            lines.append({"cls": cls, "pts": pts, "width": width,
                          # Painted lines are a tenth of a metre wide on a
                          # one-metre grid, so they are drawn at 2x and left
                          # to the downsample to make them as faint as they
                          # actually look from three hundred metres up.
                          "marked": highway.split("_")[0] in LANE_MARKED
                                    or (lanes.isdigit() and int(lanes) >= 2)})
            continue
        if tags.get("railway") in ("rail", "light_rail", "disused"):
            lines.append({"cls": "rail", "pts": pts, "width": 4.0})
            continue
        if tags.get("waterway") in ("stream", "river", "ditch", "drain"):
            lines.append({"cls": "water", "pts": pts,
                          "width": 6.0 if tags.get("waterway") == "river" else 2.5})
            continue
        if tags.get("barrier") == "hedge" or tags.get("natural") == "tree_row":
            lines.append({"cls": "hedge", "pts": pts,
                          "width": 2.5 if tags.get("natural") == "tree_row" else 1.5})
            continue
        if wid in claimed:
            continue
        cls = classify(tags)
        if cls and len(pts) >= 4 and pts[0] == pts[-1]:
            areas.append({"cls": cls, "ring": pts, "holes": []})

    # Largest first, so a pitch inside a park lands on top of the park rather
    # than under it.
    areas.sort(key=lambda a: -ring_area(a["ring"]))
    return areas, lines, tree_points


# Every field in England is worked in lines, and from the air that is most of
# what a field looks like: tramlines in the arable, mower stripes on the
# pitches. The *direction* is not in OSM — nothing is tagged for it — so it
# comes from the field's own shape, because a farmer drives the long way.
STRIPED = {"farmland": (11.0, 0.055), "meadow": (11.0, 0.045),
           "grass": (7.0, 0.035), "pitch": (6.0, 0.05), "park": (9.0, 0.03)}


def principal_angle(ring):
    """The long axis of a polygon, by the covariance of its vertices."""
    xs = np.array([p[0] for p in ring], dtype=float)
    ys = np.array([p[1] for p in ring], dtype=float)
    xs -= xs.mean()
    ys -= ys.mean()
    cxx, cyy, cxy = (xs * xs).mean(), (ys * ys).mean(), (xs * ys).mean()
    return 0.5 * math.atan2(2 * cxy, cxx - cyy)


def stripe(img, ring, cls):
    """Rule working lines across one field, clipped to it."""
    spacing, contrast = STRIPED[cls]
    xs = [p[0] * SS for p in ring]
    ys = [p[1] * SS for p in ring]
    x0, y0 = int(min(xs)) - 1, int(min(ys)) - 1
    x1, y1 = int(max(xs)) + 2, int(max(ys)) + 2
    if x1 - x0 < 8 or y1 - y0 < 8:
        return
    mask = Image.new("1", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).polygon([(x - x0, y - y0) for x, y in zip(xs, ys)], fill=1)
    tile = img.crop((x0, y0, x1, y1))
    draw = ImageDraw.Draw(tile)
    base = RGB[cls]
    dark = tuple(max(0, min(255, int(c * (1 - contrast)))) for c in base)
    ang = principal_angle(ring)
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy, ux
    cx, cy = (x1 - x0) / 2, (y1 - y0) / 2
    reach = math.hypot(x1 - x0, y1 - y0)
    step = spacing * SS
    for k in range(-int(reach / step) - 1, int(reach / step) + 2):
        mx, my = cx + px * k * step, cy + py * k * step
        draw.line([(mx - ux * reach, my - uy * reach),
                   (mx + ux * reach, my + uy * reach)],
                  fill=dark, width=max(1, int(SS * 1.4)))
    img.paste(tile, (x0, y0), mask)


def paint(areas, lines):
    """Rasterise to a colour image (supersampled) and a 1 m class map."""
    W = E1 - E0
    rgb = Image.new("RGB", (W * SS, W * SS), RGB[BASE])
    lab = Image.new("L", (W, W), INDEX[BASE])
    drgb, dlab = ImageDraw.Draw(rgb), ImageDraw.Draw(lab)

    def poly(ring, holes, cls):
        drgb.polygon([(x * SS, y * SS) for x, y in ring], fill=RGB[cls])
        dlab.polygon(ring, fill=INDEX[cls])
        for hole in holes:
            drgb.polygon([(x * SS, y * SS) for x, y in hole], fill=RGB[BASE])
            dlab.polygon(hole, fill=INDEX[BASE])

    for a in areas:
        poly(a["ring"], a["holes"], a["cls"])
        # Only worth it on a field you could see the lines in; below about a
        # third of a hectare they are one texel apart and read as noise.
        if a["cls"] in STRIPED and ring_area(a["ring"]) > 3000:
            stripe(rgb, a["ring"], a["cls"])

    hedges = [l for l in lines if l["cls"] == "hedge"]
    for cls in ROAD_ORDER + ["grass", "water"]:
        for l in lines:
            if l["cls"] != cls or len(l["pts"]) < 2:
                continue
            w = max(l["width"], 1.0)
            drgb.line([(x * SS, y * SS) for x, y in l["pts"]],
                      fill=RGB[cls], width=max(1, round(w * SS)), joint="curve")
            dlab.line(l["pts"], fill=INDEX[cls], width=max(1, round(w)),
                      joint="curve")
    # Markings last, over every carriageway, and only in the colour image:
    # a painted line is a material, not a land class, and putting it in the
    # class raster would tell the segmentation that the middle of the A40 is
    # a different kind of ground from its edges.
    for l in lines:
        if not l.get("marked") or len(l["pts"]) < 2:
            continue
        drgb.line([(x * SS, y * SS) for x, y in l["pts"]],
                  fill=RGB_OF(MARKING), width=1, joint="curve")

    # Downsampling is what gives the roads clean edges: at 1x, PIL's line
    # drawing is hard-aliased and a diagonal service road reads as a staircase.
    return rgb.resize((W, W), Image.BOX), lab, hedges


def blocked_mask(lab, lines):
    """Where a tree must not stand: on tarmac, in water, or through a roof."""
    W = lab.size[0]
    img = Image.new("1", (W, W), 0)
    d = ImageDraw.Draw(img)
    for l in lines:
        if l["cls"] in ("road", "road_minor", "rail", "water"):
            d.line(l["pts"], fill=1, width=max(1, round(l["width"] + 3)),
                   joint="curve")
    for b in json.loads((OUT / "gv-buildings.json").read_text()):
        # gv-buildings.json is in local metres from the box centre; the raster
        # is metres from the north-west corner, and z already runs south.
        d.polygon([(x + W / 2, z + W / 2) for x, z in b["ring"]], fill=1)
    blocked = np.array(img, dtype=bool)
    arr = np.array(lab)
    for cls in ("water", "road", "road_minor", "parking", "rail", "path",
                "concrete", "unpaved"):
        blocked |= arr == INDEX[cls]
    return blocked


def scatter(lab, blocked, hedges, tree_points, seed=7):
    """Tree instances: woods and gardens by area, hedges by length, plus OSM's
    individually surveyed trees."""
    rng = random.Random(seed)
    W = lab.size[0]
    arr = np.array(lab)
    trees = []

    def add(x, y, height, kind, spread):
        if not (0 <= x < W and 0 <= y < W) or blocked[int(y), int(x)]:
            return
        trees.append((x - W / 2, y - W / 2, height, rng.random() * 360, kind, spread))

    for cls, spec in SCATTER.items():
        step = spec["spacing"]
        lo, hi = spec["height"]
        ys, xs = np.nonzero(arr == INDEX[cls])
        if not len(xs):
            continue
        cells = set(zip((ys // step).astype(int), (xs // step).astype(int)))
        for cy, cx in cells:
            # One stem per cell, jittered inside it: a plain grid reads as an
            # orchard from the air even at 6 m spacing.
            x = (cx + rng.random()) * step
            y = (cy + rng.random()) * step
            if not (0 <= x < W and 0 <= y < W) or arr[int(y), int(x)] != INDEX[cls]:
                continue
            add(x, y, rng.uniform(lo, hi), spec["kind"], rng.uniform(0.8, 1.25))

    for h in hedges:
        row = h["cls"] == "hedge" and h["width"] > 2
        for (x0, y0), (x1, y1) in zip(h["pts"], h["pts"][1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            steps = max(1, int(length / (6.0 if row else HEDGE_SPACING)))
            for i in range(steps):
                t = (i + rng.uniform(0.2, 0.8)) / steps
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                if row:
                    add(x, y, rng.uniform(8, 13), 0, rng.uniform(0.7, 1.0))
                else:
                    add(x, y, rng.uniform(*HEDGE_HEIGHT), 2, rng.uniform(1.0, 1.6))

    for x, y in tree_points:
        # Surveyed by a human, so no blocked test: if OSM says a tree stands
        # in a car park, a tree stands in a car park.
        if 0 <= x < W and 0 <= y < W:
            trees.append((x - W / 2, y - W / 2, rng.uniform(8, 15),
                          rng.random() * 360, 0, rng.uniform(0.9, 1.3)))
    return trees


def encode(trees):
    """8 bytes a tree. Position in decimetres (0.1 m over a 2 km box is far
    finer than anyone can see), height in 0.25 m steps, rotation in 1.4 deg
    steps. Y is deliberately absent — the map reads it from the height field."""
    buf = bytearray()
    import struct
    for x, z, h, rot, kind, spread in trees:
        buf += struct.pack("<hhBBBB",
                           int(round(x * 10)), int(round(z * 10)),
                           min(255, int(round(h / 0.25))),
                           int(rot / 360 * 255) & 0xFF,
                           kind, min(255, int(round(spread * 100))))
    return bytes(buf)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    areas, lines, tree_points = read_world()
    print(f"areas {len(areas)}  lines {len(lines)}  surveyed trees {len(tree_points)}")
    rgb, lab, hedges = paint(areas, lines)
    rgb.save(out / "gv-landcover.png", optimize=True)
    lab.save(out / "gv-landclass.png", optimize=True)

    blocked = blocked_mask(lab, lines)
    trees = scatter(lab, blocked, hedges, tree_points)
    (out / "gv-trees.bin").write_bytes(encode(trees))

    counts = {}
    for t in trees:
        counts[t[4]] = counts.get(t[4], 0) + 1
    arr = np.array(lab)
    cover = {name: round(float((arr == i).mean()) * 100, 2)
             for name, i in INDEX.items()}
    meta = {
        "note": "Land cover and trees for the Golden Valley box. Pixel (0,0) "
                "is the north-west corner, one pixel is one metre. Tree "
                "records are 8 bytes little-endian: int16 x, int16 z (local "
                "decimetres from the box centre, x east, z south), uint8 "
                "height (0.25 m steps), uint8 rotation (1/256 turn), uint8 "
                "kind, uint8 canopy spread (percent).",
        "colourFile": "gv-landcover.png",
        "classFile": "gv-landclass.png",
        "treeFile": "gv-trees.bin",
        "metresPerPixel": 1,
        "pixels": list(rgb.size),
        "classes": {name: {"index": i, "colour": f"#{CLASSES[name]:06x}",
                           "coverPercent": cover[name]}
                    for name, i in INDEX.items()},
        "treeKinds": {"0": "broadleaf", "1": "scrub", "2": "hedge"},
        "trees": len(trees),
        "treesByKind": {str(k): v for k, v in sorted(counts.items())},
        "sources": ["OpenStreetMap contributors (ODbL)"],
    }
    (out / "gv-landcover.json").write_text(json.dumps(meta, indent=2))
    for f in ("gv-landcover.png", "gv-landclass.png", "gv-trees.bin"):
        print(f"{f:22} {(out / f).stat().st_size / 1024:8.1f} KB")
    print("trees", len(trees), counts)
    print("cover %", {k: v for k, v in sorted(cover.items(), key=lambda kv: -kv[1]) if v})


if __name__ == "__main__":
    main()
