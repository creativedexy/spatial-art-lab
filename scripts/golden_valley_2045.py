"""West Cheltenham in 2045, on the grid the fields already had.

Phase 6. The map is surveyed to the metre; this is the only file in the
project that invents anything, so it is worth being exact about what it
invents and what it does not.

**Not invented:** where the ground is, where the brook runs, where the roads
and the rights of way are, which fields are open, how steep they are and which
way they face, and — the point of the whole thing — which way the hedgerows
run. Two independent measurements agree that the field grain here is 22°, with
its orthogonal at 112°: the surviving hedges and tree rows across the box
(35 % of their length between 20° and 30°), and the orientation of the
allocation's own boundary. The grid below is that bearing, at a spacing that
gives the 3–4 ha fields this landscape used to have.

**Invented:** what goes in the cells. The rules are written out rather than
hand-placed, so the reasoning is visible and an argument about it is an
argument about a rule.

The design move is a finding rather than a preference. `find_open_land.py` cut
54 hedgerows and watercourses through the allocation and it barely split —
89 ha became 78.8, still one field over a kilometre across. The grain a scheme
here would normally hold on to has already been ploughed out, so replanting it
is not mitigation, it is the plan: the hedges come back first, and everything
else sits in the cells they make.

Outputs are the same shapes as the present-day files, because the wave that
crosses the map blends between them:

  gv-2045-landcover.png   ground colour, changes only inside the allocation
  gv-2045-landclass.png   the same as class indices
  gv-2045-buildings.json  only what is NEW; today's 4,033 are still there
  gv-2045-trees.bin       new hedge, orchard and street trees, same 8-byte record
  gv-2045-meta.json       what changed, in hectares, and the rules that did it

Usage:  python3 scripts/golden_valley_2045.py [--dry-run]
"""
import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
GV = ROOT / "experiments" / "002-living-map" / "golden-valley"
VISION = GV.parent / "vision"
SS = 2                        # supersample for the colour overlay
SEED = 2045

# The grain, measured. Spacing gives ~3.7 ha cells, which is the size the
# fields around here were before they were amalgamated.
BEARING = 22.0
SPACING_A = 175.0             # along the grain
SPACING_B = 210.0             # across it

# New ground classes. APPENDED, never inserted: the class raster is an index
# image and everything already written against it would shift by one.
NEW_CLASSES = {
    "orchard":     0x6d8a4e,
    # Barely different from farmland on purpose. Agrivoltaics is a field with
    # panel rows over it, not a solar farm: the crop is still the ground, and
    # painting it as a dark slab is the difference between a landscape that
    # gained an industry and one that lost a field.
    "agrivoltaic": 0x7a8f63,
    # Damp meadow, not open water. The brook is already in the raster and stays
    # where it is; this is the ground either side of it letting go.
    "wetland":     0x86a06e,
}
PANEL = 0x59636b               # the panel rows themselves
PANEL_WIDTH = 2.2
PANEL_SPACING = 11.0
# The new ground is painted over today's, not instead of it: at less than full
# opacity the tramlines, the mown stripes and the slope shading underneath
# still come through, so a changed field still reads as that field.
FILL_ALPHA = 185

# What the ground of a built cell is made of, before buildings go on it.
# Courtyards and plazas, not "gardens and roofs averaged together":
# the buildings themselves are geometry standing on top of this.
BUILT_GROUND = "grass"

# 3-5 storeys, in metres, per the masterplan vocabulary already in vision/.
STOREY = 3.4


def load():
    meta = json.loads((GV / "gv-meta.json").read_text())
    cover = json.loads((GV / "gv-landcover.json").read_text())
    paths = json.loads((GV / "gv-paths.json").read_text())
    land = json.loads((VISION / "open-land.json").read_text())
    stamp = np.array(Image.open(VISION / "open-land-parcels.png"))
    cls = np.array(Image.open(GV / cover["classFile"]).convert("L"))
    heights = np.frombuffer((GV / meta["binFile"]).read_bytes(),
                            dtype="<u2").reshape(meta["binPixels"][1],
                                                 meta["binPixels"][0])
    return meta, cover, paths, land, stamp, cls, heights


# --- the grid ---------------------------------------------------------------

def grid_lines(mask_bounds, bearing, sa, sb, phase=(0.0, 0.0)):
    """Two families of parallel lines at `bearing` and its orthogonal.

    Returned in local metres as long segments; clipping happens by rasterising
    against the parcel, which is simpler than analytic clipping and is exactly
    as accurate at the metre the rest of the project works in.
    """
    x0, z0, x1, z1 = mask_bounds
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    r = math.hypot(x1 - x0, z1 - z0)
    t = math.radians(bearing)
    out = []
    for ang, spacing, ph, family in ((t, sb, phase[0], "a"),
                                     (t + math.pi / 2, sa, phase[1], "b")):
        # `ang` is the direction the LINES run; they are spaced along its normal.
        dx, dz = math.sin(ang), -math.cos(ang)
        nx, nz = -dz, dx
        k = int(r / spacing) + 2
        for i in range(-k, k + 1):
            ox, oz = cx + nx * (i * spacing + ph), cz + nz * (i * spacing + ph)
            out.append((family, (ox - dx * r, oz - dz * r),
                        (ox + dx * r, oz + dz * r)))
    return out


def alignment_score(lines, hedges, tol=18.0):
    """How much surviving hedge lies on the grid. Higher is better."""
    total = 0.0
    for _, a, b in lines:
        ax, az = a
        bx, bz = b
        dx, dz = bx - ax, bz - az
        n = math.hypot(dx, dz)
        if n < 1e-6:
            continue
        nx, nz = -dz / n, dx / n
        for px, pz in hedges:
            if abs((px - ax) * nx + (pz - az) * nz) < tol:
                total += 1
    return total


# --- rasterising helpers ----------------------------------------------------

def cell_polygons(lines, bounds):
    """The quadrilaterals two families of lines cut out of the plane."""
    fam_a = sorted((l for l in lines if l[0] == "a"), key=lambda l: l[1])
    fam_b = sorted((l for l in lines if l[0] == "b"), key=lambda l: l[1])
    cells = []
    for i in range(len(fam_a) - 1):
        for j in range(len(fam_b) - 1):
            corners = []
            ok = True
            for la in (fam_a[i], fam_a[i + 1]):
                for lb in (fam_b[j], fam_b[j + 1]):
                    p = intersect(la[1], la[2], lb[1], lb[2])
                    if p is None:
                        ok = False
                        break
                    corners.append(p)
                if not ok:
                    break
            if not ok or len(corners) != 4:
                continue
            # Order them round the quad rather than in the order found.
            cx = sum(p[0] for p in corners) / 4
            cz = sum(p[1] for p in corners) / 4
            corners.sort(key=lambda p: math.atan2(p[1] - cz, p[0] - cx))
            if any(not (bounds[0] - 300 <= p[0] <= bounds[2] + 300
                        and bounds[1] - 300 <= p[1] <= bounds[3] + 300)
                   for p in corners):
                continue
            cells.append(corners)
    return cells


def intersect(a1, a2, b1, b2):
    x1, y1 = a1
    x2, y2 = a2
    x3, y3 = b1
    x4, y4 = b2
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


# --- what goes in a cell ----------------------------------------------------

def near_mask_metres(mask, step=8):
    """Coordinates of a mask's set pixels, sampled, in local metres."""
    r, c = np.where(mask[::step, ::step])
    return np.stack([c * step - mask.shape[1] / 2,
                     r * step - mask.shape[0] / 2], 1).astype(np.float32)


def min_dist(pts, x, z):
    if len(pts) == 0:
        return 1e9
    d = np.hypot(pts[:, 0] - x, pts[:, 1] - z)
    return float(d.min())


def rasterise(poly, size, W, ss=1):
    """A polygon in local metres as a boolean image of `size` at `ss` scale."""
    img = Image.new("1", (size, size), 0)
    ImageDraw.Draw(img).polygon(
        [((x + W / 2) * ss, (z + W / 2) * ss) for x, z in poly], fill=1)
    return np.array(img, dtype=bool)


def programme(cells, parcel_1m, cls, index, heights, meta, W):
    """Assign each cell a use, from measured conditions rather than by hand.

    Order matters: the brook corridor is a constraint, so it is decided first
    and nothing else may take it. Then the things that want to be near
    something — homes near the existing edge, workspace near the road and
    GCHQ — then the slope-driven use, then the leftovers.
    """
    water = near_mask_metres(cls == index["water"])
    road = near_mask_metres(np.isin(cls, [index["road"], index["road_minor"]]))
    built = near_mask_metres(cls == index["residential"])
    zmin, zmax = meta["elevationMinMetres"], meta["elevationMaxMetres"]
    gchq = (123.0, 64.0)

    out = []
    for poly in cells:
        m = rasterise(poly, cls.shape[0], W) & parcel_1m
        area = int(m.sum())
        if area < 4000:                      # a sliver, not a field
            continue
        cx = sum(p[0] for p in poly) / 4
        cz = sum(p[1] for p in poly) / 4
        rows, colsi = np.where(m)
        hs = heights[rows[::37], colsi[::37]] / 65535 * (zmax - zmin) + zmin
        # Aspect from the cell's own least-squares plane: which way it faces.
        xs = colsi[::37].astype(float) - W / 2
        zs = rows[::37].astype(float) - W / 2
        A = np.stack([xs, zs, np.ones_like(xs)], 1)
        (ge, gn, _), *_ = np.linalg.lstsq(A, hs, rcond=None)
        bearing = (math.degrees(math.atan2(-ge, gn)) + 360) % 360
        slope = math.degrees(math.atan(math.hypot(ge, gn)))

        c = {
            "poly": poly, "areaM2": area, "centre": [round(cx), round(cz)],
            "toWater": round(min_dist(water, cx, cz)),
            "toRoad": round(min_dist(road, cx, cz)),
            "toBuilt": round(min_dist(built, cx, cz)),
            "toGchq": round(math.dist((cx, cz), gchq)),
            "slopeDegrees": round(slope, 2),
            "aspectDegrees": round(bearing),
        }
        west = 135 <= bearing <= 315        # anything with a south or west face
        # Order is the argument. The brook corridor is a constraint, so it is
        # settled first and nothing may take it. Workspace comes next, on the
        # ground within 520 m of GCHQ, because that adjacency is the entire
        # reason the allocation exists — and the survey says that same end is
        # also the one abutting Hesters Way, so the campus lands between the
        # two rather than in a field of its own. Homes extend the town behind
        # it. Slope decides the far west, and what nothing wants stays a
        # field until the cap and the orchard ring get to it.
        if c["toWater"] < 55:
            c["use"] = "wetland"
        elif c["toGchq"] < 520 and c["toRoad"] < 330:
            c["use"] = "campus"
        elif c["toBuilt"] < 310 and c["toRoad"] < 300:
            c["use"] = "homes"
        elif west and slope >= 0.8:
            c["use"] = "agrivoltaic"
        else:
            c["use"] = "arable"
        out.append(c)

    # Orchard is a thing you plant where people are, so it is a ring round the
    # built cells rather than a use in its own right. Everything beyond it
    # stays farmland — which is not laziness but the difference between a town
    # in a landscape and a masterplan that reached the red line and stopped.
    settled = [c["centre"] for c in out if c["use"] in ("homes", "campus")]
    for c in out:
        if c["use"] == "arable" and settled \
                and min(math.dist(c["centre"], k) for k in settled) < 150:
            c["use"] = "orchard"

    # Cap the built area. A scheme that takes more than a third of the
    # allocation stops being a town in a landscape and becomes a landscape in
    # a town, and the whole proposition here is the first one.
    total = sum(c["areaM2"] for c in out)
    built_cells = [c for c in out if c["use"] in ("homes", "campus")]
    built_cells.sort(key=lambda c: c["toRoad"], reverse=True)
    while sum(c["areaM2"] for c in out if c["use"] in ("homes", "campus")) \
            > total * 0.32 and built_cells:
        built_cells.pop(0)["use"] = "orchard"
    return out


# --- buildings --------------------------------------------------------------

def inset(poly, d):
    """Shrink a convex polygon by `d` along each edge's inward normal."""
    cx = sum(p[0] for p in poly) / len(poly)
    cz = sum(p[1] for p in poly) / len(poly)
    edges = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        ux, uz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(ux, uz)
        if n < 1e-6:
            return None
        nx, nz = -uz / n, ux / n
        if (cx - a[0]) * nx + (cz - a[1]) * nz < 0:
            nx, nz = -nx, -nz
        edges.append(((a[0] + nx * d, a[1] + nz * d),
                      (b[0] + nx * d, b[1] + nz * d)))
    out = []
    for e0, e1 in zip(edges[-1:] + edges[:-1], edges):
        p = intersect(e0[0], e0[1], e1[0], e1[1])
        if p is None:
            return None
        out.append(p)
    return out


def blocks_along(a, b, cx, cz, length, depth, gap):
    """Footprints laid along one edge of a block, facing its street."""
    ux, uz = b[0] - a[0], b[1] - a[1]
    span = math.hypot(ux, uz)
    if span < length + 2 * gap:
        return
    ux, uz = ux / span, uz / span
    nx, nz = -uz, ux
    if (cx - a[0]) * nx + (cz - a[1]) * nz < 0:
        nx, nz = -nx, -nz            # inward, towards the courtyard
    t = gap
    while t + length <= span - gap:
        p0 = (a[0] + ux * t, a[1] + uz * t)
        p1 = (a[0] + ux * (t + length), a[1] + uz * (t + length))
        yield [p0, p1,
               (p1[0] + nx * depth, p1[1] + nz * depth),
               (p0[0] + nx * depth, p0[1] + nz * depth)], (ux, uz)
        t += length + gap


def ground_at(heights, meta, x, z):
    W, H = meta["binPixels"]
    zmin, zmax = meta["elevationMinMetres"], meta["elevationMaxMetres"]
    c = min(max(int(x + meta["widthMetres"] / 2), 0), W - 1)
    r = min(max(int(z + meta["heightMetres"] / 2), 0), H - 1)
    return zmin + heights[r, c] / 65535 * (zmax - zmin)


SHAPES = {
    # length, depth, gap, storeys, roof, street inset
    "campus": (38, 17, 9, 4, "flat", 22),
    "homes": (24, 12, 6, 2.5, "gable", 18),
}


def make_buildings(cells, heights, meta, parcel_1m, W):
    out = []
    for c in cells:
        if c["use"] not in SHAPES:
            continue
        length, depth, gap, storeys, roof, street = SHAPES[c["use"]]
        ring = inset(c["poly"], street)
        if ring is None:
            continue
        cx, cz = c["centre"]
        for a, b in zip(ring, ring[1:] + ring[:1]):
            for foot, (ux, uz) in blocks_along(a, b, cx, cz, length, depth, gap):
                # Anything hanging outside the allocation is not ours to build.
                if not all(parcel_1m[
                        min(max(int(z + W / 2), 0), W - 1),
                        min(max(int(x + W / 2), 0), W - 1)] for x, z in foot):
                    continue
                n = storeys + (random.choice((-0.5, 0, 0, 0.5, 1))
                               if c["use"] == "campus" else
                               random.choice((-0.5, 0, 0.5)))
                h = round(max(2, n) * STOREY, 2)
                base = round(min(ground_at(heights, meta, x, z) for x, z in foot), 2)
                b2 = {
                    "ring": [[round(x, 2), round(z, 2)] for x, z in foot],
                    "holes": [], "base": base, "height": h,
                    "family": c["use"],
                }
                if roof == "flat":
                    b2.update(roof="flat", axis=None, eaves=h, ridge=h)
                else:
                    b2.update(roof="gable",
                              axis=round(math.degrees(math.atan2(uz, ux)), 1),
                              eaves=round(h * 0.7, 2), ridge=h)
                out.append(b2)
    return out


def make_glasshouses(cells, heights, meta, parcel_1m, W):
    """Long low glasshouses on the orchard cells beside the campus.

    The point is not the glass, it is where the heat comes from: data halls
    reject it and glasshouses want it, and that exchange is the clearest thing
    this place could say about being a countryside technology town.
    """
    campus = [c["centre"] for c in cells if c["use"] == "campus"]
    out = []
    for c in cells:
        if c["use"] != "orchard" or not campus:
            continue
        if min(math.dist(c["centre"], k) for k in campus) > 520:
            continue
        ring = inset(c["poly"], 34)
        if ring is None:
            continue
        a, b = ring[0], ring[1]
        for foot, _ in blocks_along(a, b, *c["centre"], 62, 13, 14):
            if not all(parcel_1m[
                    min(max(int(z + W / 2), 0), W - 1),
                    min(max(int(x + W / 2), 0), W - 1)] for x, z in foot):
                continue
            base = round(min(ground_at(heights, meta, x, z) for x, z in foot), 2)
            out.append({"ring": [[round(x, 2), round(z, 2)] for x, z in foot],
                        "holes": [], "base": base, "height": 6.5,
                        "family": "glasshouse", "roof": "flat", "axis": None,
                        "eaves": 6.5, "ridge": 6.5})
    return out


# --- trees ------------------------------------------------------------------

def tree_record(x, z, height, kind, spread, rot=None):
    """The same 8-byte record gv-trees.bin uses. No Y: the map computes it."""
    return (int(round(x * 10)), int(round(z * 10)),
            max(1, min(255, int(round(height / 0.25)))),
            random.randrange(256) if rot is None else rot,
            kind, max(1, min(255, int(spread))))


def clip_to_parcel(a, b, parcel_1m, W, step):
    """Walk a segment, yielding the points that land inside the allocation."""
    n = int(math.dist(a, b) / step)
    for i in range(n + 1):
        t = i / max(n, 1)
        x = a[0] + (b[0] - a[0]) * t
        z = a[1] + (b[1] - a[1]) * t
        c = int(x + W / 2)
        r = int(z + W / 2)
        if 0 <= r < W and 0 <= c < W and parcel_1m[r, c]:
            yield x, z


def make_trees(lines, cells, parcel_1m, W):
    """Hedges first, because they are the plan; then orchards and streets."""
    out, counts = [], Counter()
    for _, a, b in lines:
        for x, z in clip_to_parcel(a, b, parcel_1m, W, 2.6):
            x += random.uniform(-0.5, 0.5)
            z += random.uniform(-0.5, 0.5)
            out.append(tree_record(x, z, random.uniform(2.4, 3.8), 2,
                                   random.uniform(70, 110)))
            counts["hedge"] += 1
        # A standard oak every so often along a hedge, which is what makes an
        # English field boundary read as one from the air rather than as a wall.
        for x, z in clip_to_parcel(a, b, parcel_1m, W, 48):
            out.append(tree_record(x + random.uniform(-2, 2),
                                   z + random.uniform(-2, 2),
                                   random.uniform(9, 14), 0,
                                   random.uniform(85, 120)))
            counts["standard"] += 1

    for c in cells:
        if c["use"] == "orchard":
            ring = inset(c["poly"], 14)
            if ring is None:
                continue
            xs = [p[0] for p in ring]
            zs = [p[1] for p in ring]
            m = rasterise(ring, W, W)
            for x in np.arange(min(xs), max(xs), 8.0):
                for z in np.arange(min(zs), max(zs), 8.0):
                    r, cc = int(z + W / 2), int(x + W / 2)
                    if not (0 <= r < W and 0 <= cc < W) or not m[r, cc] \
                            or not parcel_1m[r, cc]:
                        continue
                    out.append(tree_record(x + random.uniform(-1, 1),
                                           z + random.uniform(-1, 1),
                                           random.uniform(4.5, 6.5), 0,
                                           random.uniform(60, 85)))
                    counts["orchard"] += 1
        elif c["use"] in SHAPES:
            ring = inset(c["poly"], SHAPES[c["use"]][5])
            if ring is None:
                continue
            for a, b in zip(ring, ring[1:] + ring[:1]):
                for x, z in clip_to_parcel(a, b, parcel_1m, W, 13):
                    out.append(tree_record(x, z, random.uniform(7, 10), 0,
                                           random.uniform(55, 80)))
                    counts["street"] += 1
    return out, counts


# --- the ground -------------------------------------------------------------

RGB = lambda v: ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def paint(cells, lines, cover, index, parcel_1m, W, palette):
    """A colour overlay and a class overlay, both only inside the allocation."""
    big = W * SS
    colour = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    dc = ImageDraw.Draw(colour)
    klass = Image.new("L", (W, W), 255)          # 255 = leave today's alone
    dk = ImageDraw.Draw(klass)

    def poly(pts, name, alpha=FILL_ALPHA):
        dc.polygon([((x + W / 2) * SS, (z + W / 2) * SS) for x, z in pts],
                   fill=RGB(palette[name]) + (alpha,))
        dk.polygon([(x + W / 2, z + W / 2) for x, z in pts], fill=index[name])

    def line(a, b, name, width):
        dc.line([((a[0] + W / 2) * SS, (a[1] + W / 2) * SS),
                 ((b[0] + W / 2) * SS, (b[1] + W / 2) * SS)],
                fill=RGB(palette[name]) + (255,), width=int(width * SS))
        dk.line([(a[0] + W / 2, a[1] + W / 2), (b[0] + W / 2, b[1] + W / 2)],
                fill=index[name], width=max(1, int(width)))

    ground = {"wetland": "wetland", "orchard": "orchard",
              "agrivoltaic": "agrivoltaic",
              "homes": BUILT_GROUND, "campus": BUILT_GROUND}
    for c in cells:
        # `arable` is retained farmland: it is in 2045 exactly as it is now, so
        # nothing is painted over it at all.
        if c["use"] in ground:
            poly(c["poly"], ground[c["use"]])

    # Panel rows, drawn across the grain so they read as rows from altitude
    # rather than as a flat wash — and clipped to their own field, which the
    # first version was not: unclipped rows striped a third of the vale.
    t = math.radians(BEARING + 90)
    for c in cells:
        if c["use"] != "agrivoltaic":
            continue
        rows_img = Image.new("RGBA", (W * SS, W * SS), (0, 0, 0, 0))
        dr = ImageDraw.Draw(rows_img)
        xs = [p[0] for p in c["poly"]]
        zs = [p[1] for p in c["poly"]]
        r = math.hypot(max(xs) - min(xs), max(zs) - min(zs))
        cx, cz = c["centre"]
        for k in np.arange(-r / 2, r / 2, PANEL_SPACING):
            ax = cx + math.cos(t) * -r / 2 - math.sin(t) * k
            az = cz + math.sin(t) * -r / 2 + math.cos(t) * k
            bx = cx + math.cos(t) * r / 2 - math.sin(t) * k
            bz = cz + math.sin(t) * r / 2 + math.cos(t) * k
            dr.line([((ax + W / 2) * SS, (az + W / 2) * SS),
                     ((bx + W / 2) * SS, (bz + W / 2) * SS)],
                    fill=RGB(PANEL) + (225,), width=int(PANEL_WIDTH * SS))
        clip = Image.new("L", (W * SS, W * SS), 0)
        ImageDraw.Draw(clip).polygon(
            [((x + W / 2) * SS, (z + W / 2) * SS) for x, z in c["poly"]], fill=255)
        rows_img.putalpha(Image.fromarray(
            (np.array(rows_img.getchannel("A")) *
             (np.array(clip) > 0)).astype(np.uint8), "L"))
        colour.alpha_composite(rows_img)
        dc = ImageDraw.Draw(colour)

    # Streets round the built blocks, then the hedges on every grid line.
    for c in cells:
        if c["use"] not in SHAPES:
            continue
        ring = inset(c["poly"], SHAPES[c["use"]][5] - 5)
        if ring is None:
            continue
        for a, b in zip(ring, ring[1:] + ring[:1]):
            line(a, b, "road_minor", 6.5)
    for _, a, b in lines:
        line(a, b, "scrub", 2.5)

    # Nothing outside the allocation changes. That is what makes the wave
    # honest: the future differs only where somebody designed it.
    mask = Image.fromarray((parcel_1m * 255).astype(np.uint8), "L")
    colour = colour.resize((W, W), Image.LANCZOS)
    colour.putalpha(Image.fromarray(
        (np.array(colour.getchannel("A")) * parcel_1m).astype(np.uint8), "L"))
    ka = np.array(klass)
    ka[~parcel_1m] = 255
    return colour, Image.fromarray(ka, "L"), mask


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default=str(GV))
    args = ap.parse_args()
    random.seed(SEED)

    meta, cover, paths, land, stamp, cls, heights = load()
    W = meta["widthMetres"]
    CELL = land["cellMetres"]
    index = {k: v["index"] for k, v in cover["classes"].items()}

    parcel = stamp == 1
    rows, colsi = np.where(parcel)
    bounds = (colsi.min() * CELL - W / 2, rows.min() * CELL - W / 2,
              colsi.max() * CELL - W / 2, rows.max() * CELL - W / 2)

    hedge_pts = [tuple(p) for lm in paths["landmarks"]
                 if lm["kind"] in ("hedge", "tree_row") for p in lm["points"]]

    # Phase the grid so it sits on as much surviving hedge as it can. A small
    # search, because the answer only has to be better than arbitrary.
    best, best_phase = -1, (0.0, 0.0)
    for pa in np.arange(0, SPACING_B, 15):
        for pb in np.arange(0, SPACING_A, 15):
            s = alignment_score(
                grid_lines(bounds, BEARING, SPACING_A, SPACING_B, (pa, pb)),
                hedge_pts)
            if s > best:
                best, best_phase = s, (float(pa), float(pb))
    lines = grid_lines(bounds, BEARING, SPACING_A, SPACING_B, best_phase)
    print(f"grid at {BEARING}deg, phase {best_phase[0]:.0f}/{best_phase[1]:.0f} m, "
          f"{best:.0f} surviving hedge points on it")

    cells = cell_polygons(lines, bounds)
    parcel_1m = np.array(Image.fromarray((parcel * 255).astype(np.uint8), "L")
                         .resize((W, W), Image.NEAREST)) > 0
    cells = programme(cells, parcel_1m, cls, index, heights, meta, W)
    by_use = Counter(c["use"] for c in cells)
    ha = Counter()
    for c in cells:
        ha[c["use"]] += c["areaM2"] / 10000
    total = sum(ha.values())
    print(f"\n{len(cells)} fields, {total:.1f} ha")
    for use, a in ha.most_common():
        print(f"   {use:<12} {by_use[use]:>2} fields  {a:6.1f} ha  "
              f"({a / total * 100:4.1f}%)")

    buildings = make_buildings(cells, heights, meta, parcel_1m, W)
    buildings += make_glasshouses(cells, heights, meta, parcel_1m, W)
    floor = sum(
        abs(sum(r[0][0] * r[1][1] - r[1][0] * r[0][1]
                for r in zip(b["ring"], b["ring"][1:] + b["ring"][:1]))) / 2
        * max(1, round(b["height"] / STOREY)) for b in buildings)
    fam = Counter(b["family"] for b in buildings)
    print(f"\n{len(buildings)} new buildings, {floor / 10000:.1f} ha of floor")
    for k, v in fam.most_common():
        print(f"   {k:<12} {v:>4}")

    trees, tree_counts = make_trees(lines, cells, parcel_1m, W)
    print(f"\n{len(trees)} new trees: " +
          ", ".join(f"{v} {k}" for k, v in tree_counts.most_common()))

    palette = {k: int(v["colour"].lstrip("#"), 16)
               for k, v in cover["classes"].items()}
    palette.update(NEW_CLASSES)
    next_index = max(index.values()) + 1
    for name in NEW_CLASSES:
        if name not in index:
            index[name] = next_index
            next_index += 1

    colour, klass, _ = paint(cells, lines, cover, index, parcel_1m, W, palette)

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return

    out = Path(args.out)
    base = Image.open(GV / cover["colourFile"]).convert("RGBA")
    Image.alpha_composite(base, colour).convert("RGB").save(
        out / "gv-2045-landcover.png")
    today = np.array(Image.open(GV / cover["classFile"]).convert("L"))
    ka = np.array(klass)
    merged = np.where(ka == 255, today, ka).astype(np.uint8)
    Image.fromarray(merged, "L").save(out / "gv-2045-landclass.png")

    (out / "gv-2045-buildings.json").write_text(
        json.dumps(buildings, separators=(",", ":")))
    rec = np.array(trees, dtype=[("x", "<i2"), ("z", "<i2"), ("h", "u1"),
                                 ("r", "u1"), ("k", "u1"), ("s", "u1")])
    (out / "gv-2045-trees.bin").write_bytes(rec.tobytes())

    doc = {
        "note": ("West Cheltenham in 2045. Only the allocation changes; "
                 "everything outside it is today's survey untouched, which is "
                 "what lets the wave blend the two honestly. Buildings here "
                 "are the NEW ones only — today's 4,033 are still standing in "
                 "2045 and are not repeated."),
        "generatedBy": "scripts/golden_valley_2045.py",
        "seed": SEED,
        "grid": {"bearingDegrees": BEARING, "phaseMetres": list(best_phase),
                 "spacingMetres": [SPACING_A, SPACING_B],
                 "why": ("measured, not chosen: 35% of surviving hedge length "
                         "in the box lies between 20 and 30 degrees, and the "
                         "allocation's own boundary agrees")},
        "colourFile": "gv-2045-landcover.png",
        "classFile": "gv-2045-landclass.png",
        "buildingFile": "gv-2045-buildings.json",
        "treeFile": "gv-2045-trees.bin",
        "classes": {k: {"index": index[k], "colour": f"#{palette[k]:06x}"}
                    for k in list(cover["classes"]) + list(NEW_CLASSES)},
        "families": {
            "campus": {"wall": "#e8dfcb", "roof": "#93a469"},
            "homes": {"wall": "#ece5d8", "roof": "#8a9b60"},
            "glasshouse": {"wall": "#cfd8d4", "roof": "#dfe8e4"},
        },
        "roofChanges": [{
            "name": "Government Communications Headquarters",
            "roof": "#93a469",
            "why": ("the ring re-roofed as a wildflower meadow — 3.6 ha of "
                    "south-facing ground at 20 m is parcel 5 in the open-land "
                    "survey, and this is the one image that says what the "
                    "place has become"),
        }],
        "areasHectares": {k: round(v, 1) for k, v in ha.items()},
        "fields": len(cells),
        "newBuildings": len(buildings),
        "floorHectares": round(floor / 10000, 1),
        "newTrees": len(trees),
        "treeCounts": dict(tree_counts),
        "sources": ["Environment Agency LiDAR (OGL v3)",
                    "OpenStreetMap contributors (ODbL)",
                    "everything else invented by this script"],
    }
    (out / "gv-2045-meta.json").write_text(json.dumps(doc, indent=2) + "\n")
    for f in ("gv-2045-landcover.png", "gv-2045-landclass.png",
              "gv-2045-buildings.json", "gv-2045-trees.bin",
              "gv-2045-meta.json"):
        print(f"  wrote {(out / f).relative_to(ROOT)}  "
              f"{(out / f).stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
