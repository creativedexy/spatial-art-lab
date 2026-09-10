"""Convert an EA LiDAR GeoTIFF (WCS GetCoverage output) into a 16-bit PNG
heightmap plus a metadata JSON that records real-world extent and the
elevation range encoded into the PNG's 0-65535 values.

Usage: python3 lidar_to_heightmap.py input.tif output.png output.json E_MIN E_MAX N_MIN N_MAX
Data: Environment Agency National LiDAR Programme composite DTM,
Open Government Licence v3. Attribute: (c) Environment Agency copyright
and/or database right. All rights reserved.
"""
import json
import sys

import numpy as np
import tifffile
from PIL import Image


def main() -> None:
    tif_path, png_path, json_path = sys.argv[1:4]
    e_min, e_max, n_min, n_max = (float(v) for v in sys.argv[4:8])

    z = tifffile.imread(tif_path).astype(np.float64)
    # EA composites mark nodata with a large negative sentinel; sea/void
    # cells otherwise sit near 0. Treat anything implausibly low as nodata.
    nodata = z < -100
    valid = z[~nodata]
    z_lo, z_hi = float(valid.min()), float(valid.max())
    z_filled = np.where(nodata, z_lo, z)

    scaled = np.clip((z_filled - z_lo) / (z_hi - z_lo), 0, 1)
    png16 = (scaled * 65535).astype(np.uint16)
    Image.fromarray(png16, mode="I;16").save(png_path)

    meta = {
        "crs": "EPSG:27700",
        "easting": [e_min, e_max],
        "northing": [n_min, n_max],
        "widthMetres": e_max - e_min,
        "heightMetres": n_max - n_min,
        "elevationMinMetres": round(z_lo, 2),
        "elevationMaxMetres": round(z_hi, 2),
        "pixels": [int(png16.shape[1]), int(png16.shape[0])],
        "nodataFraction": round(float(nodata.mean()), 4),
        "source": "Environment Agency LIDAR Composite DTM 1m via WCS, "
                  "Open Government Licence v3",
    }
    with open(json_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
