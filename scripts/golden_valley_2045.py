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


Re-running this writes PNG land cover and points the meta at it, which un-does phase 7's compression: run `scripts/compress_assets.py --write` afterwards or the map loads 1.7 MB it does not need. And expect the building bases to move by up to one quantisation step — about a centimetre — because the heightmap this now reads is the packed one. Trees and footprints come back byte-identical.
"""
import argparse
import json
import math
import random
from collections import Counter
from pathlib import Path

import numpy as np

from heightfield import load_heights
from PIL import Image, ImageDraw, ImageFilter

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
GCHQ = (123.0, 64.0)
CANOPY_RADIUS = 400.0
CANOPY_DEPTHS = (11.0, 5.5)  # paired bays first, then single perimeter bays
CANOPY_MIN_PARKING = 0.75
# Earlier fills were translucent so today's field detail showed through. That
# detail is not aligned with the new classes: pale stubble and dark crop marks
# survived as green-cyan blotches inside wetland, orchard and built cells. The
# shader now supplies use-specific detail in world metres, so class colour is
# opaque here and has one unambiguous median for KEYED_GRADE to preserve.
FILL_ALPHA = 255
CHANNEL_WIDTH = 2.5

# What the ground of a built cell is made of, before buildings go on it.
# Courtyards and plazas, not "gardens and roofs averaged together":
# the buildings themselves are geometry standing on top of this.
BUILT_GROUND = "grass"

# A storey is kept explicit because both the dwelling and campus-area checks
# are programme checks, not estimates recovered from rounded mesh heights.
STOREY = 3.4
HOME_STREET = 14.0
CAMPUS_STREET = 18.0


def load():
    meta = json.loads((GV / "gv-meta.json").read_text())
    cover = json.loads((GV / "gv-landcover.json").read_text())
    paths = json.loads((GV / "gv-paths.json").read_text())
    land = json.loads((VISION / "open-land.json").read_text())
    stamp = np.array(Image.open(VISION / "open-land-parcels.png"))
    cls = np.array(Image.open(GV / cover["classFile"]).convert("L"))
    heights = load_heights(meta, GV)
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


GRID_U = (math.cos(math.radians(BEARING)), math.sin(math.radians(BEARING)))
GRID_V = (math.cos(math.radians(BEARING + 90)),
          math.sin(math.radians(BEARING + 90)))


def to_grid(x, z):
    return x * GRID_U[0] + z * GRID_U[1], x * GRID_V[0] + z * GRID_V[1]


def from_grid(u, v):
    return (u * GRID_U[0] + v * GRID_V[0],
            u * GRID_U[1] + v * GRID_V[1])


def cell_frame(cell):
    q = [to_grid(*p) for p in cell["poly"]]
    return min(p[0] for p in q), max(p[0] for p in q), \
        min(p[1] for p in q), max(p[1] for p in q)


def grid_rect(u0, u1, v0, v1):
    return [from_grid(u0, v0), from_grid(u1, v0),
            from_grid(u1, v1), from_grid(u0, v1)]


def inside_parcel(poly, parcel_1m, W):
    """True when all corners and edge midpoints remain in the allocation."""
    probes = list(poly)
    probes += [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
               for a, b in zip(poly, poly[1:] + poly[:1])]
    for x, z in probes:
        r, c = int(z + W / 2), int(x + W / 2)
        if not (0 <= r < W and 0 <= c < W and parcel_1m[r, c]):
            return False
    return True


def edge_footprint(a, b, depth, start, length):
    """A street-facing footprint; its depth always points into the block."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    span = math.hypot(dx, dz)
    ux, uz = dx / span, dz / span
    nx, nz = -uz, ux                 # block rectangles are anticlockwise
    p0 = (a[0] + ux * start, a[1] + uz * start)
    p1 = (p0[0] + ux * length, p0[1] + uz * length)
    return [p0, p1, (p1[0] + nx * depth, p1[1] + nz * depth),
            (p0[0] + nx * depth, p0[1] + nz * depth)], (ux, uz)


def terrace_runs(span, corner=4.5, gap=3.0):
    """Runs of 4-10 houses, each with a 5.5-6.5 m street frontage."""
    usable = span - corner * 2
    nruns = max(1, int(round((usable + gap) / 32.0)))
    bay = (usable - gap * (nruns - 1)) / nruns
    out = []
    t = corner
    for _ in range(nruns):
        dwellings = max(4, min(10, int(round(bay / 6.0))))
        frontage = min(6.5, max(5.5, bay / dwellings))
        length = dwellings * frontage
        out.append((t + (bay - length) / 2, length, dwellings))
        t += bay + gap
    return out


def home_layout(cell):
    """Six 70 x 43 m perimeter blocks divided by 14 m internal streets."""
    u0, u1, v0, v1 = cell_frame(cell)
    bw, bd = 70.0, 43.0
    total_u = bw * 2 + HOME_STREET
    total_v = bd * 3 + HOME_STREET * 2
    su = (u0 + u1 - total_u) / 2
    sv = (v0 + v1 - total_v) / 2
    blocks = []
    for j in range(3):
        for i in range(2):
            a = su + i * (bw + HOME_STREET)
            b = sv + j * (bd + HOME_STREET)
            blocks.append({"poly": grid_rect(a, a + bw, b, b + bd),
                           "i": i, "j": j})
    streets = [
        (from_grid(su + bw + HOME_STREET / 2, sv),
         from_grid(su + bw + HOME_STREET / 2, sv + total_v), HOME_STREET),
        *[(from_grid(su, sv + j * bd + (j - 0.5) * HOME_STREET),
           from_grid(su + total_u,
                     sv + j * bd + (j - 0.5) * HOME_STREET), HOME_STREET)
          for j in (1, 2)],
    ]
    return blocks, streets


def campus_layout(cell, parcel_1m=None, W=None):
    """Four 17 m wings around a 66 x 54 m courtyard and 18 m streets."""
    u0, u1, v0, v1 = cell_frame(cell)
    ow, od, depth = 100.0, 88.0, 17.0
    cu, cv = (u0 + u1) / 2, (v0 + v1) / 2

    def wings(at_u, at_v):
        a, b = at_u - ow / 2, at_v - od / 2
        return [grid_rect(a, a + ow, b, b + depth),
                grid_rect(a + ow - depth, a + ow, b + depth, b + od - depth),
                grid_rect(a, a + ow, b + od - depth, b + od),
                grid_rect(a, a + depth, b + depth, b + od - depth)]

    # Boundary campus cells are clipped pieces of the measured grid. Find the
    # nearest position within the same cell that keeps all four wings on land
    # we are actually allocated; this changes no programme boundary.
    best = (None, -1, 1e9)
    for at_u in np.arange(u0 + ow / 2, u1 - ow / 2 + 0.1, 5):
        for at_v in np.arange(v0 + od / 2, v1 - od / 2 + 0.1, 5):
            fs = wings(at_u, at_v)
            score = sum(inside_parcel(f, parcel_1m, W) for f in fs) \
                if parcel_1m is not None else 4
            shift = abs(at_u - cu) + abs(at_v - cv)
            if score > best[1] or (score == best[1] and shift < best[2]):
                best = (fs, score, shift)
    fs = best[0]
    # Use the actual shifted wing bounds for the perimeter street.
    q = [to_grid(*p) for f in fs for p in f]
    au0, au1 = min(x[0] for x in q), max(x[0] for x in q)
    av0, av1 = min(x[1] for x in q), max(x[1] for x in q)
    off = CAMPUS_STREET / 2
    streets = [
        (from_grid(au0 - off, av0 - off), from_grid(au1 + off, av0 - off),
         CAMPUS_STREET),
        (from_grid(au1 + off, av0 - off), from_grid(au1 + off, av1 + off),
         CAMPUS_STREET),
        (from_grid(au1 + off, av1 + off), from_grid(au0 - off, av1 + off),
         CAMPUS_STREET),
        (from_grid(au0 - off, av1 + off), from_grid(au0 - off, av0 - off),
         CAMPUS_STREET),
    ]
    return fs, streets


def building_record(foot, family, cell, heights, meta, storeys, roof,
                    axis=None, **extra):
    h = round(storeys * STOREY, 2)
    base = round(min(ground_at(heights, meta, x, z) for x, z in foot), 2)
    b = {"ring": [[round(x, 2), round(z, 2)] for x, z in foot],
         "holes": [], "base": base, "height": h, "family": family,
         "cell": cell["centre"], "storeys": storeys}
    if roof == "flat":
        b.update(roof="flat", axis=None, eaves=h, ridge=h)
    else:
        depth = min(math.dist(a, q)
                    for a, q in zip(foot, foot[1:] + foot[:1]))
        eaves = max(2.0, storeys - 0.5) * STOREY
        ridge = eaves + depth / 2              # 45-degree Passivhaus roof
        b.update(roof="gable", axis=round(axis, 1),
                 eaves=round(eaves, 2), ridge=round(ridge, 2),
                 height=round(ridge, 2), roofPitchDegrees=45)
    b.update(extra)
    return b


def make_buildings(cells, heights, meta, parcel_1m, W, road, named_routes):
    out, campus = [], []
    for cell in cells:
        if cell["use"] == "homes":
            blocks, _ = home_layout(cell)
            for block in blocks:
                edges = list(zip(block["poly"], block["poly"][1:] + block["poly"][:1]))
                # Apartment blocks take the short outside edge of the four
                # corner blocks, facing the orchard/green edge of the cell.
                apt_edge = None
                if block["j"] in (0, 2):
                    apt_edge = 3 if block["i"] == 0 else 1
                for ei, (a, b) in enumerate(edges):
                    span = math.dist(a, b)
                    if ei == apt_edge:
                        length = 31.0
                        foot, _ = edge_footprint(a, b, 15.0,
                                                 (span - length) / 2, length)
                        if inside_parcel(foot, parcel_1m, W):
                            storeys = random.choice((4, 5, 5, 6))
                            area = length * 15.0 * storeys
                            out.append(building_record(
                                foot, "homes", cell, heights, meta, storeys,
                                "flat", dwellings=round(area / 80),
                                typology="apartments"))
                        continue
                    for start, length, dwellings in terrace_runs(span):
                        depth = random.uniform(9.0, 10.0)
                        foot, axis = edge_footprint(a, b, depth, start, length)
                        if not inside_parcel(foot, parcel_1m, W):
                            continue
                        storeys = random.choice((2.5, 2.5, 3))
                        out.append(building_record(
                            foot, "homes", cell, heights, meta, storeys,
                            "gable", math.degrees(math.atan2(axis[1], axis[0])),
                            dwellings=dwellings, typology="terrace"))
        elif cell["use"] == "campus":
            wings, _ = campus_layout(cell, parcel_1m, W)
            anchor = [round(sum(p[0] for f in wings for p in f) /
                            sum(len(f) for f in wings)),
                      round(sum(p[1] for f in wings for p in f) /
                            sum(len(f) for f in wings))]
            site = {"centre": anchor}
            for foot in wings:
                if not inside_parcel(foot, parcel_1m, W):
                    continue
                storeys = random.choice((4, 5, 5, 6))
                campus.append(building_record(
                    foot, "campus", site, heights, meta, storeys, "flat"))

    # Name the scheme's four buildings without changing the loader schema.
    # IDEA is a site marker on a perimeter wing: models.js still puts the
    # one-off meadow-roof model in this field's clear courtyard.
    campus_sites = {tuple(b["cell"]) for b in campus}
    route_cells = []
    for site in campus_sites:
        d = min(math.dist(site, p) for p in named_routes)
        if d <= 150:
            route_cells.append(site)
    pool = route_cells or campus_sites
    idea_cell = min(pool, key=lambda p: math.dist(p, (123, 64)))

    def centre(b):
        return (sum(p[0] for p in b["ring"]) / len(b["ring"]),
                sum(p[1] for p in b["ring"]) / len(b["ring"]))

    named = set()
    idea = min((b for b in campus if tuple(b["cell"]) == tuple(idea_cell)),
               key=lambda b: math.dist(centre(b), idea_cell))
    idea.update(name="IDEA", storeys=4, height=4 * STOREY,
                eaves=4 * STOREY, ridge=4 * STOREY)
    named.add(id(idea))
    router = min((b for b in campus if id(b) not in named),
                 key=lambda b: min_dist(road, *centre(b)))
    router.update(name="ROUTER", storeys=2, height=2 * STOREY,
                  eaves=2 * STOREY, ridge=2 * STOREY,
                  groundFloorUse="transport hub")
    named.add(id(router))
    output = max((b for b in campus if id(b) not in named),
                 key=lambda b: math.dist(centre(b), (123, 64)))
    output.update(name="OUTPUT", storeys=7, height=7 * STOREY,
                  eaves=7 * STOREY, ridge=7 * STOREY)
    named.add(id(output))
    input_b = min((b for b in campus if id(b) not in named),
                  key=lambda b: math.dist(centre(b), (123, 64)))
    input_b.update(name="INPUT", storeys=5, height=5 * STOREY,
                   eaves=5 * STOREY, ridge=5 * STOREY)
    out.extend(campus)
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
        for foot, axis in blocks_along(a, b, *c["centre"], 62, 13, 14):
            if not all(parcel_1m[
                    min(max(int(z + W / 2), 0), W - 1),
                    min(max(int(x + W / 2), 0), W - 1)] for x, z in foot):
                continue
            base = round(min(ground_at(heights, meta, x, z) for x, z in foot), 2)
            out.append({"ring": [[round(x, 2), round(z, 2)] for x, z in foot],
                        "holes": [], "base": base, "height": 6.5,
                        "family": "glasshouse", "roof": "gable",
                        "axis": round(math.degrees(math.atan2(
                            axis[1], axis[0])), 1),
                        "eaves": 4.2, "ridge": 6.5, "cell": c["centre"]})
    return out


def point_in_poly(point, poly):
    """Even-odd containment for the small convex footprints in this dataset."""
    x, z = point
    inside = False
    for a, b in zip(poly, poly[1:] + poly[:1]):
        if (a[1] > z) != (b[1] > z):
            at = a[0] + (z - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x < at:
                inside = not inside
    return inside


def segments_cross(a, b, c, d):
    if max(a[0], b[0]) < min(c[0], d[0]) \
            or max(c[0], d[0]) < min(a[0], b[0]) \
            or max(a[1], b[1]) < min(c[1], d[1]) \
            or max(c[1], d[1]) < min(a[1], b[1]):
        return False
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) \
            - (q[1] - p[1]) * (r[0] - p[0])
    return side(a, b, c) * side(a, b, d) <= 0 \
        and side(c, d, a) * side(c, d, b) <= 0


def polygons_overlap(a, b):
    if any(point_in_poly(p, b) for p in a) \
            or any(point_in_poly(p, a) for p in b):
        return True
    return any(segments_cross(p, q, r, s)
               for p, q in zip(a, a[1:] + a[:1])
               for r, s in zip(b, b[1:] + b[:1]))


def point_segment_distance(p, a, b):
    """Euclidean distance from a point to a finite segment."""
    dx, dz = b[0] - a[0], b[1] - a[1]
    n = dx * dx + dz * dz
    if n < 1e-12:
        return math.dist(p, a)
    t = max(0.0, min(1.0,
                     ((p[0] - a[0]) * dx + (p[1] - a[1]) * dz) / n))
    return math.dist(p, (a[0] + dx * t, a[1] + dz * t))


def polygon_distance(a, b):
    """Minimum edge distance between two polygons; zero when they overlap."""
    if polygons_overlap(a, b):
        return 0.0
    return min(
        min(point_segment_distance(p, r, s)
            for p in a for r, s in zip(b, b[1:] + b[:1])),
        min(point_segment_distance(p, r, s)
            for p in b for r, s in zip(a, a[1:] + a[:1])),
    )


def bbox_distance(a, b):
    """Minimum distance between polygon bounding boxes (a cheap reject)."""
    ax0, ax1 = min(p[0] for p in a), max(p[0] for p in a)
    az0, az1 = min(p[1] for p in a), max(p[1] for p in a)
    bx0, bx1 = min(p[0] for p in b), max(p[0] for p in b)
    bz0, bz1 = min(p[1] for p in b), max(p[1] for p in b)
    dx = max(0.0, ax0 - bx1, bx0 - ax1)
    dz = max(0.0, az0 - bz1, bz0 - az1)
    return math.hypot(dx, dz)


def today_obstacles():
    """Today's buildings, deliberately read from both authoritative files."""
    out = json.loads((GV / "gv-buildings.json").read_text())
    out += json.loads((GV / "gv-gchq.json").read_text())
    return out


def today_trees():
    """Tree centres and crown radii from the surveyed eight-byte records."""
    rec = np.frombuffer((GV / "gv-trees.bin").read_bytes(), dtype=[
        ("x", "<i2"), ("z", "<i2"), ("h", "u1"), ("r", "u1"),
        ("k", "u1"), ("s", "u1")])
    # The unit crown is 0.71 units across; match loadFutureTrees' scale.
    return [(r["x"] / 10, r["z"] / 10,
             max(2.0, r["h"] * 0.25 * r["s"] / 100 * 0.355)) for r in rec]


def obstacle_mask(shape, buildings, trees, clearance=3):
    """Raster guard used for fitting; the exact geometry is asserted below."""
    h, w = shape
    im = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(im)
    for b in buildings:
        ring = b["ring"]
        if max(x for x, _ in ring) < GCHQ[0] - CANOPY_RADIUS - 10 \
                or min(x for x, _ in ring) > GCHQ[0] + CANOPY_RADIUS + 10 \
                or max(z for _, z in ring) < GCHQ[1] - CANOPY_RADIUS - 10 \
                or min(z for _, z in ring) > GCHQ[1] + CANOPY_RADIUS + 10:
            continue
        # The outer ring is intentionally solid. For GCHQ this excludes the
        # courtyard as well as the occupied annulus, as the brief requires.
        draw.polygon([(x + w / 2, z + h / 2) for x, z in ring], fill=255)
    for x, z, radius in trees:
        if math.dist((x, z), GCHQ) > CANOPY_RADIUS + radius:
            continue
        r = radius + 0.5
        draw.ellipse((x + w / 2 - r, z + h / 2 - r,
                      x + w / 2 + r, z + h / 2 + r), fill=255)
    # Four raster metres is conservative for a three-metre geometric rule at
    # pixel centres; the assertion remains the final authority.
    size = 2 * (clearance + 1) + 1
    return np.array(im.filter(ImageFilter.MaxFilter(size)), dtype=bool)


def parking_components(parking, radius=CANOPY_RADIUS):
    """Four-connected parking patches around GCHQ, in local metres.

    The source is today's classified land rather than a drawn masterplan.
    Islands below 400 m2 are access aprons and fragments, not car parks.
    """
    h, w = parking.shape
    yy, xx = np.indices(parking.shape)
    near = parking & ((xx - w / 2 - GCHQ[0]) ** 2
                      + (yy - h / 2 - GCHQ[1]) ** 2 <= radius ** 2)
    seen = np.zeros_like(near, dtype=bool)
    out = []
    for sy, sx in zip(*np.where(near)):
        if seen[sy, sx]:
            continue
        todo = [(int(sy), int(sx))]
        seen[sy, sx] = True
        points = []
        while todo:
            y, x = todo.pop()
            points.append((x - w / 2, y - h / 2))
            for ny, nx in ((y - 1, x), (y + 1, x),
                           (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w \
                        and near[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    todo.append((ny, nx))
        if len(points) >= 400:
            out.append(np.asarray(points, dtype=float))
    return out


def make_canopies(cls, index, heights, meta, buildings, trees):
    """Fit continuous PV rows to every usable GCHQ parking-bay patch.

    OSM's parking polygons around the Doughnut are a mixture of straight and
    curved bay strips, sometimes joined by one-pixel necks. One PCA direction
    per connected polygon therefore missed most of the parking. Instead we
    test real 11 m paired rows and 5.5 m edge rows at ten-degree headings,
    then pack the longest candidates first. Mapped roads and footpaths are
    hard exclusions, leaving the classified 6-8 m circulation gaps open.
    """
    parking = cls == index["parking"]
    h, w = parking.shape
    yy, xx = np.indices(parking.shape)
    near = ((xx - w / 2 - GCHQ[0]) ** 2
            + (yy - h / 2 - GCHQ[1]) ** 2 <= CANOPY_RADIUS ** 2)
    source = parking & near
    blocked = obstacle_mask(parking.shape, buildings, trees)
    eligible = source & ~blocked
    forbidden_indices = [index[name]
                         for name in ("road", "road_minor", "path",
                                      "water", "rail") if name in index]
    forbidden = np.isin(cls, forbidden_indices) | blocked

    rows, cols = np.where(eligible)
    if not len(rows):
        return [], {"parkingAreaM2": int(source.sum()),
                    "eligibleParkingAreaM2": 0,
                    "parkingCoveredM2": 0, "coverageFraction": 0.0,
                    "parkingLots": 0, "parkingLotsCovered": 0}
    gy, gx = np.mgrid[rows.min():rows.max() + 1:2,
                      cols.min():cols.max() + 1:2]
    centres = np.stack([gx.ravel(), gy.ravel()], axis=1)
    centres = centres[eligible[centres[:, 1], centres[:, 0]]]
    candidates = []
    lengths = (60.0, 42.0, 28.0, 16.0, 10.0)

    # Candidate generation is vectorised in small batches: about thirty
    # thousand useful rectangles instead of millions of Python point tests.
    for depth in CANOPY_DEPTHS:
        for degrees in range(0, 180, 10):
            angle = math.radians(degrees)
            along = np.array([math.cos(angle), math.sin(angle)])
            across = np.array([-along[1], along[0]])
            for length in lengths:
                offsets = np.array([
                    along * u + across * v
                    for u in np.arange(-length / 2, length / 2 + 0.1, 1.0)
                    for v in np.arange(-depth / 2, depth / 2 + 0.1, 1.0)
                ])
                for start in range(0, len(centres), 800):
                    batch = centres[start:start + 800]
                    probes = np.rint(batch[:, None, :] + offsets).astype(int)
                    probes[:, :, 0] = np.clip(probes[:, :, 0], 0, w - 1)
                    probes[:, :, 1] = np.clip(probes[:, :, 1], 0, h - 1)
                    pr = probes[:, :, 1]
                    pc = probes[:, :, 0]
                    parking_share = parking[pr, pc].mean(axis=1)
                    clear = ~forbidden[pr, pc].any(axis=1)
                    for i in np.where(
                            (parking_share >= CANOPY_MIN_PARKING) & clear)[0]:
                        candidates.append((length * depth, length, depth,
                                           degrees, *batch[i]))

    candidates.sort(key=lambda c: (-c[0], -c[1], c[3], c[5], c[4]))
    occupied = np.zeros_like(parking)
    reserved = np.zeros_like(parking)
    chosen = []

    def rectangle_pixels(cx, cy, length, depth):
        pad = length / 2 + depth / 2 + 2
        x0, x1 = max(0, int(cx - pad)), min(w, int(cx + pad) + 1)
        y0, y1 = max(0, int(cy - pad)), min(h, int(cy + pad) + 1)
        ry, rx = np.mgrid[y0:y1, x0:x1]
        return x0, x1, y0, y1, rx - cx, ry - cy

    for _, length, depth, degrees, cx, cy in candidates:
        angle = math.radians(degrees)
        along = np.array([math.cos(angle), math.sin(angle)])
        across = np.array([-along[1], along[0]])
        x0, x1, y0, y1, dx, dz = rectangle_pixels(cx, cy, length, depth)
        u = dx * along[0] + dz * along[1]
        v = dx * across[0] + dz * across[1]
        inside = (np.abs(u) < length / 2 - 0.15) \
            & (np.abs(v) < depth / 2 - 0.15)
        if (reserved[y0:y1, x0:x1] & inside).any():
            continue
        # The source polygons are bay fields separated by mapped circulation;
        # road/path pixels are hard exclusions above. Reserving the canopy
        # itself (rather than buffering across those mapped gaps) lets paired
        # rows occupy both sides while the 6-8 m aisles remain open.
        reserve = inside
        p0 = np.array([cx, cy]) - along * length / 2 - across * depth / 2
        p1 = np.array([cx, cy]) + along * length / 2 - across * depth / 2
        p2 = np.array([cx, cy]) + along * length / 2 + across * depth / 2
        p3 = np.array([cx, cy]) - along * length / 2 + across * depth / 2
        foot = [(round(p[0] - w / 2, 2), round(p[1] - h / 2, 2))
                for p in (p0, p1, p2, p3)]
        # The raster guard is conservative, but keep the exact three-metre
        # rule here too so a rounded corner can never sneak through it.
        nearby = [b for b in buildings
                  if bbox_distance(foot, [tuple(p) for p in b["ring"]]) < 3.0
                  and polygon_distance(
                      foot, [tuple(p) for p in b["ring"]]) < 3.0]
        if nearby:
            continue
        post_count = max(2, math.ceil(length / 9))
        posts = []
        for i in range(post_count):
            t = 0.5 if post_count == 1 else 0.07 + i * 0.86 / (post_count - 1)
            point = (p0 * (1 - t) + p1 * t + p3 * (1 - t) + p2 * t) / 2
            x = round(point[0] - w / 2, 2)
            z = round(point[1] - h / 2, 2)
            posts.append({"x": x, "z": z,
                          "ground": round(ground_at(heights, meta, x, z), 2)})
        base = max(p["ground"] for p in posts)
        chosen.append({
            "ring": [[x, z] for x, z in foot], "holes": [],
            "base": base, "height": 3.5, "family": "canopy",
            "roof": "canopy", "axis": degrees, "eaves": 3.2,
            "ridge": 3.5, "underside": 3.2, "thickness": 0.3,
            "tiltDegrees": 6.0, "posts": posts,
        })
        occupied[y0:y1, x0:x1] |= inside
        reserved[y0:y1, x0:x1] |= reserve

    components = parking_components(source)
    # OSM contains five nominal parking polygons here that are almost wholly
    # under a building/courtyard or mature crown. They are the overlap bug,
    # not usable car parks. Count a lot only when 200 m2 remains eligible.
    usable_components = []
    for points in components:
        rr = (points[:, 1] + h / 2).astype(int)
        cc = (points[:, 0] + w / 2).astype(int)
        if int(eligible[rr, cc].sum()) >= 200:
            usable_components.append(points)
    covered_lots = sum(any(occupied[int(z + h / 2), int(x + w / 2)]
                           for x, z in points) for points in usable_components)
    if covered_lots != len(usable_components):
        raise AssertionError(
            f"canopies missed {len(usable_components) - covered_lots} usable car parks")
    covered = int((occupied & source).sum())
    stats = {
        "parkingAreaM2": int(source.sum()),
        "eligibleParkingAreaM2": int(eligible.sum()),
        "parkingCoveredM2": covered,
        "coverageFraction": covered / max(1, int(source.sum())),
        "parkingLots": len(usable_components),
        "parkingLotsCovered": covered_lots,
    }
    return chosen, stats


def assert_canopy_clearance(canopies, buildings, heights, meta, clearance=3.0):
    """No canopy or post may enter today's buildings or GCHQ courtyard."""
    obstacles = [([tuple(p) for p in b["ring"]], b.get("name"))
                 for b in buildings]
    gchq = next(b for b in buildings
                if b.get("name") == "Government Communications Headquarters")
    courtyards = [[tuple(p) for p in hole] for hole in gchq.get("holes", [])]
    for i, canopy in enumerate(canopies):
        foot = [tuple(p) for p in canopy["ring"]]
        for obstacle, name in obstacles:
            if bbox_distance(foot, obstacle) < clearance \
                    and polygon_distance(foot, obstacle) < clearance - 1e-6:
                raise AssertionError(
                    f"canopy {i} is within {clearance:g} m of {name or 'building'}")
        if any(polygons_overlap(foot, yard) for yard in courtyards):
            raise AssertionError(f"canopy {i} overlaps GCHQ courtyard")
        for post in canopy["posts"]:
            point = (post["x"], post["z"])
            if any(bbox_distance([point], obstacle) < clearance
                   and (point_in_poly(point, obstacle)
                        or min(point_segment_distance(point, a, b)
                               for a, b in zip(
                                   obstacle, obstacle[1:] + obstacle[:1]))
                        < clearance - 1e-6)
                   for obstacle, _ in obstacles):
                raise AssertionError(f"canopy {i} post enters building clearance")
            want = round(ground_at(heights, meta, *point), 2)
            if abs(post["ground"] - want) > 0.011:
                raise AssertionError(
                    f"canopy {i} post ground {post['ground']} != terrain {want}")
            if post["ground"] >= canopy["base"] + canopy["underside"]:
                raise AssertionError(f"canopy {i} post has no clear underside")


# --- trees ------------------------------------------------------------------

def tree_record(x, z, height, kind, spread, rot=None):
    """The same 8-byte record gv-trees.bin uses. No Y: the map computes it.

    `future.js` reads the last byte as spread/100 and scales X/Z by
    `height * spread`. The broadleaf unit crown is about 0.71 units across,
    so a 7 m orchard tree at spread=145 renders about 7.2 m across: neighbours
    on the 7.5 m rows nearly touch without turning the orchard into a wall.
    """
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


def internal_streets(cell, parcel_1m, W):
    if cell["use"] == "homes":
        return home_layout(cell)[1]
    if cell["use"] == "campus":
        return campus_layout(cell, parcel_1m, W)[1]
    return []


def orchard_points(cell, parcel_1m, W, spacing=7.5):
    """Rows on the measured grid, rather than a north/south point lattice."""
    ring = inset(cell["poly"], 14)
    if ring is None:
        return
    q = [to_grid(*p) for p in ring]
    u0, u1 = min(p[0] for p in q), max(p[0] for p in q)
    v0, v1 = min(p[1] for p in q), max(p[1] for p in q)
    m = rasterise(ring, W, W)
    for u in np.arange(math.ceil(u0 / spacing) * spacing, u1, spacing):
        for v in np.arange(math.ceil(v0 / spacing) * spacing, v1, spacing):
            x, z = from_grid(u + random.uniform(-0.45, 0.45),
                             v + random.uniform(-0.45, 0.45))
            r, cc = int(z + W / 2), int(x + W / 2)
            if 0 <= r < W and 0 <= cc < W and m[r, cc] and parcel_1m[r, cc]:
                yield x, z


def woodland_points(cell, settled, parcel_1m, W):
    """Irregular 20-40 m copses on the orchard edge facing open farmland."""
    cx, cz = cell["centre"]
    edges = list(zip(cell["poly"], cell["poly"][1:] + cell["poly"][:1]))
    a, b = max(edges, key=lambda e: min(
        math.dist(((e[0][0] + e[1][0]) / 2, (e[0][1] + e[1][1]) / 2), s)
        for s in settled))
    dx, dz = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dz)
    ux, uz = dx / length, dz / length
    nx, nz = -uz, ux
    if (cx - a[0]) * nx + (cz - a[1]) * nz < 0:
        nx, nz = -nx, -nz

    # Three loose clumps, leaving deliberate gaps along the outer edge. A
    # jittered 5 m lattice gives Poisson-like spacing without an O(n^2) pass.
    clumps = [(0.04, 0.27, 30), (0.36, 0.62, 38), (0.72, 0.94, 24)]
    for lo, hi, depth in clumps:
        start, stop = length * lo, length * hi
        row = 0
        d = 4.0
        while d <= depth:
            spacing = random.uniform(4.6, 5.8)
            t = start + (row % 2) * spacing / 2
            while t <= stop:
                x = a[0] + ux * (t + random.uniform(-1.0, 1.0)) \
                    + nx * (d + random.uniform(-1.0, 1.0))
                z = a[1] + uz * (t + random.uniform(-1.0, 1.0)) \
                    + nz * (d + random.uniform(-1.0, 1.0))
                r, cc = int(z + W / 2), int(x + W / 2)
                if 0 <= r < W and 0 <= cc < W and parcel_1m[r, cc]:
                    yield x, z
                t += spacing
            d += spacing
            row += 1


def make_trees(lines, cells, parcel_1m, W):
    """Mature hedges, orchards, outer copses and internal street avenues."""
    out, counts = [], Counter()
    for _, a, b in lines:
        for x, z in clip_to_parcel(a, b, parcel_1m, W, 2.6):
            x += random.uniform(-0.5, 0.5)
            z += random.uniform(-0.5, 0.5)
            out.append(tree_record(x, z, random.uniform(3.5, 5.0), 2,
                                   random.uniform(62, 90)))
            counts["hedge"] += 1
        # A standard oak every so often along a hedge, which is what makes an
        # English field boundary read as one from the air rather than as a wall.
        for x, z in clip_to_parcel(a, b, parcel_1m, W, 48):
            out.append(tree_record(x + random.uniform(-2, 2),
                                   z + random.uniform(-2, 2),
                                   random.uniform(12, 16), 0,
                                   random.uniform(90, 125)))
            counts["standard"] += 1

    settled = [c["centre"] for c in cells if c["use"] in ("homes", "campus")]
    for c in cells:
        if c["use"] == "orchard":
            for x, z in orchard_points(c, parcel_1m, W):
                out.append(tree_record(x, z, random.uniform(6, 8), 3,
                                       random.uniform(135, 155)))
                counts["orchard"] += 1
            for x, z in woodland_points(c, settled, parcel_1m, W):
                out.append(tree_record(x, z, random.uniform(12, 18), 1,
                                       random.uniform(75, 115)))
                counts["woodland"] += 1
        elif c["use"] in ("homes", "campus"):
            for a, b, width in internal_streets(c, parcel_1m, W):
                dx, dz = b[0] - a[0], b[1] - a[1]
                n = math.hypot(dx, dz)
                nx, nz = -dz / n, dx / n
                for side in (-1, 1):
                    off = width / 2 + 1.5
                    aa = (a[0] + nx * off * side, a[1] + nz * off * side)
                    bb = (b[0] + nx * off * side, b[1] + nz * off * side)
                    step = random.uniform(10, 12)
                    for x, z in clip_to_parcel(aa, bb, parcel_1m, W, step):
                        out.append(tree_record(x + random.uniform(-0.5, 0.5),
                                               z + random.uniform(-0.5, 0.5),
                                               random.uniform(8, 12), 4,
                                               random.uniform(75, 105)))
                        counts["street"] += 1
    if len(out) >= 30000:
        raise ValueError(f"tree budget exceeded: {len(out)} records")
    return out, counts


# --- the ground -------------------------------------------------------------

RGB = lambda v: ((v >> 16) & 255, (v >> 8) & 255, v & 255)


def stormwater_channels(cells, parcel_1m, W):
    """One 2.5 m open channel on the wetland side of every home street.

    The masterplan has no pipe network to pretend to know. Direction is the
    honest piece we can derive: choose the side and outfall end nearest the
    nearest wetland cell. The continuous street grid then conveys each short
    reach towards that wet meadow, in the Augustenborg manner, without a
    fictional diagonal ditch through homes or gardens.
    """
    wetlands = [c for c in cells if c["use"] == "wetland"]
    if not wetlands:
        return []
    channels = []
    for c in cells:
        if c["use"] != "homes":
            continue
        target = min(wetlands, key=lambda w: math.dist(c["centre"], w["centre"]))
        tx, tz = target["centre"]
        for a, b, width in internal_streets(c, parcel_1m, W):
            dx, dz = b[0] - a[0], b[1] - a[1]
            n = math.hypot(dx, dz)
            nx, nz = -dz / n, dx / n
            mx, mz = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            side = 1 if (tx - mx) * nx + (tz - mz) * nz >= 0 else -1
            # Inside the carriageway edge, where an open kerbside rain garden
            # remains legible but does not collide with the avenue trees.
            off = max(0.0, width / 2 - CHANNEL_WIDTH / 2)
            aa = (a[0] + nx * off * side, a[1] + nz * off * side)
            bb = (b[0] + nx * off * side, b[1] + nz * off * side)
            # Store the nearest-wetland end last so metadata and any future
            # flow arrows inherit the same direction without changing format.
            if math.dist(aa, (tx, tz)) < math.dist(bb, (tx, tz)):
                aa, bb = bb, aa
            channels.append((aa, bb, CHANNEL_WIDTH))
    return channels


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

    # The 14/18 m internal streets are part of the same measured grid as the
    # field cells. Block interiors remain grass gardens and shared courts.
    for c in cells:
        for a, b, width in internal_streets(c, parcel_1m, W):
            line(a, b, "road_minor", width)
    for _, a, b in lines:
        line(a, b, "scrub", 2.5)

    # Draw last so the silver water remains visible through road and hedge
    # crossings. Softening and sky reflection happen in future.js, not here.
    channels = stormwater_channels(cells, parcel_1m, W)
    for a, b, width in channels:
        line(a, b, "water", width)

    # Nothing outside the allocation changes. That is what makes the wave
    # honest: the future differs only where somebody designed it.
    mask = Image.fromarray((parcel_1m * 255).astype(np.uint8), "L")
    colour = colour.resize((W, W), Image.LANCZOS)
    colour.putalpha(Image.fromarray(
        (np.array(colour.getchannel("A")) * parcel_1m).astype(np.uint8), "L"))
    ka = np.array(klass)
    ka[~parcel_1m] = 255
    channel_length = sum(math.dist(a, b) for a, b, _ in channels)
    return colour, Image.fromarray(ka, "L"), mask, {
        "count": len(channels), "lengthMetres": round(channel_length),
        "widthMetres": CHANNEL_WIDTH,
    }


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

    road = near_mask_metres(np.isin(cls, [index["road"], index["road_minor"]]),
                            step=4)
    named_routes = [tuple(p) for route in paths["routes"]
                    if route["tier"] == "named" for p in route["points"]]
    buildings = make_buildings(cells, heights, meta, parcel_1m, W,
                               road, named_routes)
    buildings += make_glasshouses(cells, heights, meta, parcel_1m, W)
    present = today_obstacles()
    canopy_obstacles = present + buildings
    canopies, canopy_stats = make_canopies(
        cls, index, heights, meta, canopy_obstacles, today_trees())
    assert_canopy_clearance(canopies, present, heights, meta)
    buildings += canopies

    def footprint_area(b):
        r = b["ring"]
        return abs(sum(a[0] * q[1] - q[0] * a[1]
                       for a, q in zip(r, r[1:] + r[:1]))) / 2

    permanent = [b for b in buildings if b["family"] != "canopy"]
    floor = sum(footprint_area(b) * b.get(
        "storeys", max(1, round(b["height"] / STOREY))) for b in permanent)
    campus_floor = round(sum(footprint_area(b) * b["storeys"] for b in buildings
                             if b["family"] == "campus"))
    dwellings = sum(b.get("dwellings", 0) for b in buildings)
    fam = Counter(b["family"] for b in buildings)
    print(f"\n{len(permanent)} new buildings and {len(canopies)} canopies, "
          f"{floor / 10000:.1f} ha of floor")
    for k, v in fam.most_common():
        print(f"   {k:<12} {v:>4}")
    print(f"   dwellings    {dwellings:>4}")
    print(f"   campus floor {campus_floor:>7,} m2")
    canopy_area = sum(footprint_area(b) for b in canopies)
    print(f"   canopy area  {canopy_area / 10000:7.2f} ha")
    print(f"   parking      {canopy_stats['parkingAreaM2'] / 10000:7.2f} ha found; "
          f"{canopy_stats['parkingCoveredM2'] / 10000:.2f} ha "
          f"({canopy_stats['coverageFraction']:.1%}) directly covered; "
          f"{canopy_stats['parkingLotsCovered']}/{canopy_stats['parkingLots']} lots")
    if not 1000 <= dwellings <= 1200:
        raise ValueError(f"dwelling target missed: {dwellings}")
    if not 93000 <= campus_floor <= 120000:
        raise ValueError(f"campus floor target missed: {campus_floor} m2")
    if max(b.get("storeys", 0) for b in buildings) > 7:
        raise ValueError("seven-storey height cap exceeded")

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

    colour, klass, _, channel_stats = paint(
        cells, lines, cover, index, parcel_1m, W, palette)

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
            "campus": {"wall": "#aaa397", "roof": "#697456"},
            "homes": {"wall": "#d8c6a5", "roof": "#293139",
                      "flatRoof": "#6b7658"},
            "glasshouse": {"wall": "#9eafb2", "roof": "#b8c9cc"},
            "canopy": {"wall": "#34383a", "roof": "#17222c"},
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
        "newBuildings": len(permanent),
        "canopyCount": len(canopies),
        "canopyHectares": round(canopy_area / 10000, 2),
        "gchqParkingHectares": round(canopy_stats["parkingAreaM2"] / 10000, 2),
        "gchqEligibleParkingHectares": round(
            canopy_stats["eligibleParkingAreaM2"] / 10000, 2),
        "gchqParkingCoveredHectares": round(
            canopy_stats["parkingCoveredM2"] / 10000, 2),
        "gchqParkingCoverageFraction": round(
            canopy_stats["coverageFraction"], 3),
        "gchqParkingLots": canopy_stats["parkingLots"],
        "gchqParkingLotsCovered": canopy_stats["parkingLotsCovered"],
        "dwellings": dwellings,
        "campusFloorM2": campus_floor,
        "densityNote": ("Scheme-true density: about 1,100 homes and at least "
                        "93,000 m2 of campus floor area."),
        "floorHectares": round(floor / 10000, 1),
        "newTrees": len(trees),
        "treeCounts": dict(tree_counts),
        "treeKinds": {
            "0": "broad oak standard", "1": "mixed woodland clump",
            "2": "hedge", "3": "orchard", "4": "street lime",
        },
        "stormwaterChannels": channel_stats,
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
