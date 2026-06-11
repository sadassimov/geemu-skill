"""Generate 256x256 image/label chips by stratified sampling, in parallel.

Ported from the geospatial-study notebook `processimage.ipynb`: ROI is now a
placeholder asset, proxy hard-code removed, the Jupyter `%%writefile`/`import test`
trick replaced by a normal multiprocessing worker, project-ID gate + `--dry-run`
added.

Method: use an existing land-cover product (ESRI 10 m global LULC, water class) as
the label and a Sentinel-2 median composite as the image; stratified-sample N
points; for each point download a `dimensions`-sized chip of the label and of the
image via getThumbURL. Useful for building deep-learning training sets.

Public datasets are kept as-is (ESRI LULC on sat-io, Sentinel-2). Note S2_SR was
deprecated, so this uses `COPERNICUS/S2_SR_HARMONIZED`.
"""
from __future__ import annotations

import argparse
import multiprocessing
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)

PROJECT_ID = (
    os.environ.get("EE_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("EE_PROJECT_ID")
    or "PROJECT_ID"
)
ROI_ASSET = "users/your_username/roi"
ESRI_LULC = "projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m"
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
PARAMS = {
    "count": 100,          # how many chips
    "buffer": 2560,        # buffer (m) around each point -> chip extent
    "scale": 100,          # stratified-sampling scale
    "seed": 1,
    "dimensions": "256x256",
    "format": "png",       # png | jpg | GEO_TIFF | NPY
    "prefix": "tile_",
    "processes": 8,
}

# Per-process EE objects, rebuilt in each worker (ee objects can't be pickled).
_LABEL = None
_IMAGE = None


def resolve_project(cli_project):
    project = cli_project or PROJECT_ID
    return None if project == "PROJECT_ID" else project


def require_project(cli_project):
    project = resolve_project(cli_project)
    if project:
        return project
    raise RuntimeError(
        "Cloud Project ID is required before any Earth Engine request. "
        "Run with --project PROJECT_ID or set EE_PROJECT/GOOGLE_CLOUD_PROJECT/EE_PROJECT_ID."
    )


def _build_layers(roi_asset):
    import ee
    region = ee.FeatureCollection(roi_asset).geometry()
    label = ee.ImageCollection(ESRI_LULC).mean().eq(1).selfMask().clip(region)
    image = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(region)
        .filterDate("2020", "2021")
        .select("B8", "B4", "B3")
        .median()
        .visualize(min=0, max=4000)
        .clip(region)
    )
    return region, label, image


def _init_worker(project, roi_asset):
    global _LABEL, _IMAGE
    import geemap
    geemap.ee_initialize(project=project)
    _region, _LABEL, _IMAGE = _build_layers(roi_asset)


def _download_one(job):
    """job = (index, coords, kind, out_dir)."""
    import ee
    import requests

    index, coords, kind, out_dir = job
    src = _LABEL if kind == "label" else _IMAGE
    point = ee.Geometry.Point(coords)
    region = point.buffer(PARAMS["buffer"]).bounds()
    opts = {"region": region, "dimensions": PARAMS["dimensions"], "format": PARAMS["format"]}
    url = src.getThumbURL(opts) if PARAMS["format"] in ("png", "jpg") else src.getDownloadURL(opts)
    ext = "tif" if PARAMS["format"] == "GEO_TIFF" else PARAMS["format"]
    os.makedirs(out_dir, exist_ok=True)
    basename = str(index).zfill(len(str(PARAMS["count"])))
    filename = os.path.join(out_dir, f"{PARAMS['prefix']}{basename}.{ext}")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename


def sample_points(project, roi_asset):
    import geemap
    import ee
    geemap.ee_initialize(project=project)
    _region, label, _image = _build_layers(roi_asset)
    points = label.stratifiedSample(
        numPoints=PARAMS["count"], region=_region, scale=PARAMS["scale"],
        seed=PARAMS["seed"], geometries=True,
    )
    return [f["geometry"]["coordinates"] for f in points.getInfo()["features"]]


def print_dry_run(args):
    print("case=stratified_sample_chips")
    print(f"roi_asset={args.roi_asset}")
    print("project=PROJECT_ID (required before online Earth Engine run)")
    print(f"label={ESRI_LULC} (water class)  image={S2_COLLECTION} median")
    print(f"count={PARAMS['count']}  dimensions={PARAMS['dimensions']}  format={PARAMS['format']}")
    print(f"buffer={PARAMS['buffer']} m  sampling_scale={PARAMS['scale']}  processes={PARAMS['processes']}")
    print(f"out_dir={args.out_dir} (label/ and image/ subfolders)")


def parse_args():
    p = argparse.ArgumentParser(description="Stratified 256x256 chip generator example.")
    p.add_argument("--dry-run", action="store_true", help="Print the plan; no Earth Engine call.")
    p.add_argument("--project", help="Earth Engine Cloud Project ID.")
    p.add_argument("--roi-asset", default=ROI_ASSET, help="Study-area FeatureCollection asset.")
    p.add_argument("--out-dir", default=str(SCRIPT_DIR / "out"), help="Output root directory.")
    p.add_argument("--count", type=int, help="Override number of chips.")
    return p.parse_args()


def main():
    args = parse_args()
    if args.count:
        PARAMS["count"] = args.count
    if args.dry_run:
        print_dry_run(args)
        return 0
    try:
        project = require_project(args.project)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    coords = sample_points(project, args.roi_asset)
    label_dir = os.path.join(args.out_dir, "label")
    image_dir = os.path.join(args.out_dir, "image")
    jobs = [(i, c, "label", label_dir) for i, c in enumerate(coords)]
    jobs += [(i, c, "image", image_dir) for i, c in enumerate(coords)]

    with multiprocessing.Pool(
        PARAMS["processes"], initializer=_init_worker, initargs=(project, args.roi_asset)
    ) as pool:
        for done in pool.imap_unordered(_download_one, jobs):
            print("saved", done)
    print(f"Done. {len(coords)} label + {len(coords)} image chips under {args.out_dir}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
