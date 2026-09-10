"""Build the Golden Valley vertical-slice dataset.

Fetches EA LiDAR DTM and DSM (1 m, EPSG:27700) for a 2x2 km box around
GCHQ / the Golden Valley site, pulls OSM building footprints via Overpass,
measures each building's height as median(DSM - DTM) inside its footprint,
and writes:
  experiments/002-living-map/golden-valley/gv-height-<N>.bin  (uint16 LE)
  experiments/002-living-map/golden-valley/gv-meta.json
  experiments/002-living-map/golden-valley/gv-buildings.json

Terrain: Environment Agency LIDAR Composite DTM/DSM 1m, OGL v3.
Footprints: (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
import os
import urllib.parse
import urllib.request

import numpy as np
import tifffile
from PIL import Image, ImageDraw
from pyproj import Transformer

E0, E1 = 390400, 392400
N0, N1 = 221400, 223400
OUT = "experiments/002-living-map/golden-valley"
WCS = ("https://environment.data.gov.uk/spatialdata/{slug}/wcs"
       "?service=WCS&version=2.0.1&request=GetCoverage&coverageId={cov}"
       f"&subset=E({E0},{E1})&subset=N({N0},{N1})&format=image/tiff")
DATASETS = {
    "dtm": ("lidar-composite-digital-terrain-model-dtm-1m",
            "13787b9a-26a4-4775-8523-806d13af58fc__Lidar_Composite_Elevation_DTM_1m"),
    "dsm": ("lidar-composite-digital-surface-model-last-return-dsm-1m",
            "9ba4d5ac-d596-445a-9056-dae3ddec0178__Lidar_Composite_Elevation_LZ_DSM_1m"),
}


def fetch_grid(kind):
    slug, cov = DATASETS[kind]
    path = f"/tmp/gv_{kind}.tif"
    if not os.path.exists(path):
        urllib.request.urlretrieve(WCS.format(slug=slug, cov=cov), path)
    z = tifffile.imread(path).astype(np.float64)
    z = np.where(z < -100, np.nan, z)
    print(kind, z.shape, np.nanmin(z), np.nanmax(z),
          "nan frac", round(float(np.isnan(z).mean()), 4))
    return z


def fetch_footprints():
    # The OSM map API returns everything in a small bbox as XML; Overpass is
    # unreachable from this environment's proxy.
    import xml.etree.ElementTree as ET
    to_wgs = Transformer.from_crs(27700, 4326, always_xy=True)
    lon0, lat0 = to_wgs.transform(E0, N0)
    lon1, lat1 = to_wgs.transform(E1, N1)
    path = "/tmp/gv_osm.xml"
    if not os.path.exists(path):
        urllib.request.urlretrieve(
            "https://api.openstreetmap.org/api/0.6/map?bbox="
            f"{lon0:.4f},{lat0:.4f},{lon1:.4f},{lat1:.4f}", path)
    root = ET.parse(path).getroot()
    nodes = {n.get("id"): (float(n.get("lon")), float(n.get("lat")))
             for n in root.iter("node")}
    to_bng = Transformer.from_crs(4326, 27700, always_xy=True)
    ways = {}
    for w in root.iter("way"):
        ways[w.get("id")] = {
            "tags": {t.get("k"): t.get("v") for t in w.iter("tag")},
            "ring": [to_bng.transform(*nodes[nd.get("ref")])
                     for nd in w.iter("nd") if nd.get("ref") in nodes],
        }
    # Building relations (e.g. GCHQ's doughnut) carry an outer ring and
    # courtyard holes; their member ways must not double-count as buildings.
    out, claimed = [], set()
    for r in root.iter("relation"):
        tags = {t.get("k"): t.get("v") for t in r.iter("tag")}
        if "building" not in tags:
            continue
        outers = [m.get("ref") for m in r.iter("member")
                  if m.get("type") == "way" and m.get("role") == "outer"]
        inners = [m.get("ref") for m in r.iter("member")
                  if m.get("type") == "way" and m.get("role") == "inner"]
        if len(outers) != 1 or outers[0] not in ways:
            continue  # multi-segment outers not needed in this box
        claimed.update(outers + inners)
        out.append({"id": r.get("id"), "tags": tags,
                    "ring": ways[outers[0]]["ring"],
                    "holes": [ways[i]["ring"] for i in inners if i in ways]})
    for wid, w in ways.items():
        if "building" in w["tags"] and wid not in claimed and len(w["ring"]) >= 4:
            out.append({"id": wid, "tags": w["tags"],
                        "ring": w["ring"], "holes": []})
    print("footprints", len(out))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    dtm, dsm = fetch_grid("dtm"), fetch_grid("dsm")
    H, W = dtm.shape  # row 0 = north edge
    diff = dsm - dtm

    lo, hi = float(np.nanmin(dtm)), float(np.nanmax(dtm))
    filled = np.where(np.isnan(dtm), lo, dtm)
    u16 = np.clip((filled - lo) / (hi - lo), 0, 1)
    (u16 * 65535).astype("<u2").tofile(f"{OUT}/gv-height-{W}.bin")

    def px(e, n):  # BNG -> raster pixel
        return (e - E0) * (W / (E1 - E0)), (N1 - n) * (H / (N1 - N0))

    buildings = []
    for b in fetch_footprints():
        mask = Image.new("1", (W, H), 0)
        draw = ImageDraw.Draw(mask)
        draw.polygon([px(e, n) for e, n in b["ring"]], fill=1)
        for hole in b.get("holes", []):
            draw.polygon([px(e, n) for e, n in hole], fill=0)
        m = np.array(mask, dtype=bool)
        if m.sum() < 4:
            continue
        heights = diff[m]
        heights = heights[~np.isnan(heights)]
        base = dtm[m]
        base = base[~np.isnan(base)]
        if not len(heights) or not len(base):
            continue
        h = float(np.median(heights))
        if h < 2:  # noise, sheds measured into hedges, demolished stock
            h = 3.0
        buildings.append({
            "name": b["tags"].get("name"),
            "holes": [[[round(e - (E0 + E1) / 2, 1), round((N0 + N1) / 2 - n, 1)]
                       for e, n in hole] for hole in b.get("holes", [])],
            # local metres, origin at box centre: x east, z south
            "ring": [[round(e - (E0 + E1) / 2, 1), round((N0 + N1) / 2 - n, 1)]
                     for e, n in b["ring"]],
            "base": round(float(np.median(base)), 1),
            "height": round(h, 1),
        })

    with open(f"{OUT}/gv-buildings.json", "w") as f:
        json.dump(buildings, f)
    with open(f"{OUT}/gv-meta.json", "w") as f:
        json.dump({
            "crs": "EPSG:27700", "easting": [E0, E1], "northing": [N0, N1],
            "widthMetres": E1 - E0, "heightMetres": N1 - N0,
            "elevationMinMetres": round(lo, 2), "elevationMaxMetres": round(hi, 2),
            "binFile": f"gv-height-{W}.bin", "binPixels": [W, H],
            "buildings": len(buildings),
            "sources": ["EA LIDAR Composite DTM/DSM 1m (OGL v3)",
                        "OpenStreetMap contributors (ODbL)"],
        }, f, indent=2)
    hs = sorted(b["height"] for b in buildings)
    print("buildings kept", len(buildings),
          "height median", hs[len(hs) // 2], "max", hs[-1])


if __name__ == "__main__":
    main()
