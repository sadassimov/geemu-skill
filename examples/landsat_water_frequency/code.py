"""Multi-year Landsat water-frequency mapping + impervious-surface overlay.

Ported from the geospatial-study notebook `water-butoushui.ipynb` into the GEEMu
example format: account info removed (ROI is a placeholder asset), proxy hard-code
removed, project-ID gate + `--dry-run`/`--export` guards added.

Method: per-sensor cloud masking (Landsat 5/7/8 SR), compute NDVI/NDWI/MNDWI/EVI,
flag water with an ARWDR-style index rule, remove hill shadow + high HAND + steep
slope, aggregate the per-scene water flags into a yearly water *frequency*, classify
into {0 none, 1 seasonal, 2 permanent}, and overlay GAIA impervious surface.

CAVEAT: the original used Landsat Collection 1 SR (`LANDSAT/LC0*/C01/T1_SR`), which
USGS retired in 2023. Migrate to Collection 2 L2 (`LANDSAT/LC08/C02/T1_L2` etc.):
optical bands become `SR_B*`, QA becomes `QA_PIXEL`, and SR scaling is
`DN * 0.0000275 - 0.2`. See sources.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)

import os

import ee
import geemap


PROJECT_ID = (
    os.environ.get("EE_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("EE_PROJECT_ID")
    or "PROJECT_ID"
)
ROI_ASSET = "users/your_username/roi"   # replace with your study-area FeatureCollection
YEAR = 2015
SCALE = 30
CRS = "EPSG:4326"
EXPORT_FOLDER = "GEEMu_water_frequency"
WORKLOAD_TAG = "geemu-water-frequency"

# Collection 1 SR ids (retired). For Collection 2 use the C02/T1_L2 ids in sources.md.
L8_COLLECTION = "LANDSAT/LC08/C01/T1_SR"
L7_COLLECTION = "LANDSAT/LE07/C01/T1_SR"
L5_COLLECTION = "LANDSAT/LT05/C01/T1_SR"


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


def initialize_ee(project):
    # Restricted network? Set HTTP_PROXY / HTTPS_PROXY before running (see
    # references/network_proxy.md). Do not hard-code a local proxy port here.
    try:
        geemap.ee_initialize(project=project)
        ee.data.getAssetRoots()
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine/geemap initialization failed. Check the HTTP(S)_PROXY env "
            "vars first, then authentication and Cloud Project permissions."
        ) from exc
    try:
        ee.data.setDefaultWorkloadTag(WORKLOAD_TAG)
    except Exception:
        pass


def _add_indices(image, bands):
    blue, green, red, nir, swir1 = bands
    ndvi = image.normalizedDifference([nir, red]).rename("NDVI")
    ndwi = image.normalizedDifference([green, nir]).rename("NDWI")
    mndwi = image.normalizedDifference([green, swir1]).rename("MNDWI")
    evi = image.expression(
        "2.5 * (NIR - R) / (NIR + 6*R - 7.5*B + 1)",
        {"NIR": image.select(nir), "R": image.select(red), "B": image.select(blue)},
    ).rename("EVI")
    return image.addBands([ndvi, ndwi, mndwi, evi])


def _calc_water(image):
    mndwi = image.select("MNDWI")
    ndwi = image.select("NDWI")
    ndvi = image.select("NDVI")
    evi = image.select("EVI")
    water = ndwi.gt(0).And(
        mndwi.gt(0.1).And(evi.lt(0.1)).And(mndwi.gt(ndvi)).Or(mndwi.gt(evi))
    )
    return image.addBands(water.rename("water"))


def _mask_qa(image):
    qa = image.select("pixel_qa")
    cloud_shadow = qa.bitwiseAnd(1 << 3).eq(0)
    snow = qa.bitwiseAnd(1 << 4).eq(0)
    cloud = qa.bitwiseAnd(1 << 5).eq(0)
    return image.updateMask(cloud_shadow.And(snow).And(cloud))


def _sensor_water(collection_id, bands, start, end, region):
    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(start, end)
        .filterBounds(region)
        .filter(ee.Filter.lte("CLOUD_COVER", 10))
        .map(_mask_qa)
        .map(lambda img: img.divide(10000).copyProperties(img, img.propertyNames()))
        .map(lambda img: _add_indices(img, bands))
        .map(_calc_water)
        .select("water")
    )
    return collection


def build_water_frequency(region, year):
    start = ee.Date.fromYMD(year, 1, 1)
    end = ee.Date.fromYMD(year + 1, 1, 1)
    l5 = _sensor_water(L5_COLLECTION, ["B1", "B2", "B3", "B4", "B5"], start, end, region)
    l7 = _sensor_water(L7_COLLECTION, ["B1", "B2", "B3", "B4", "B5"], start, end, region)
    l8 = _sensor_water(L8_COLLECTION, ["B2", "B3", "B4", "B5", "B6"], start, end, region)
    water = l5.merge(l7).merge(l8)

    frequency = water.sum().divide(water.count()).clip(region)

    hand = ee.ImageCollection("users/gena/global-hand/hand-100").mosaic().focal_mean(0.1)
    dem = ee.Image("USGS/GMTED2010").select(0)
    slope = ee.Terrain.slope(dem)
    frequency = frequency.updateMask(hand.lte(50)).updateMask(slope.lt(20)).unmask(0)

    water_class = (
        frequency.where(frequency.gt(0).And(frequency.lte(0.25)), 0)
        .where(frequency.gt(0.25).And(frequency.lte(0.75)), 1)
        .where(frequency.gt(0.75), 2)
        .toUint8()
        .clip(region)
        .rename("water_class")
    )
    # GAIA impervious surface for the same year (change_year_index 1=2018 .. 34=1985).
    impervious = (
        ee.Image("Tsinghua/FROM-GLC/GAIA/v10")
        .select("change_year_index")
        .eq(year - 1985)
        .rename("impervious")
        .clip(region)
    )
    return water_class.addBands(impervious)


def start_export(image, region):
    task = ee.batch.Export.image.toDrive(
        image=image.toFloat(),  # uniform dtype so multi-band export does not fail
        description=f"water_class_{YEAR}",
        folder=EXPORT_FOLDER,
        fileNamePrefix=f"water_class_{YEAR}",
        region=region,
        scale=SCALE,
        crs=CRS,
        maxPixels=1e13,
    )
    task.start()
    return task


def print_dry_run(args):
    print("case=landsat_water_frequency")
    print(f"roi_asset={args.roi_asset}")
    print("project=PROJECT_ID (required before online Earth Engine run)")
    print(f"year={args.year}  scale={SCALE}  crs={CRS}")
    print(f"collections={L5_COLLECTION}, {L7_COLLECTION}, {L8_COLLECTION} (C01 retired -> use C02/T1_L2)")
    print("indices=NDVI,NDWI,MNDWI,EVI -> ARWDR-style water flag")
    print("masks=cloud/shadow/snow QA, HAND<=50, slope<20")
    print("output=water_class {0,1,2} + GAIA impervious band")
    print(f"export=Drive folder '{EXPORT_FOLDER}' (only with --export)")


def parse_args():
    p = argparse.ArgumentParser(description="Landsat water-frequency mapping example.")
    p.add_argument("--dry-run", action="store_true", help="Print the plan; no Earth Engine call.")
    p.add_argument("--project", help="Earth Engine Cloud Project ID.")
    p.add_argument("--roi-asset", default=ROI_ASSET, help="Study-area FeatureCollection asset.")
    p.add_argument("--year", type=int, default=YEAR, help="Analysis year.")
    p.add_argument("--export", action="store_true", help="Start the Drive export task.")
    return p.parse_args()


def main():
    args = parse_args()
    if args.dry_run:
        print_dry_run(args)
        return 0
    try:
        project = require_project(args.project)
        initialize_ee(project)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    region = ee.FeatureCollection(args.roi_asset).geometry()
    products = build_water_frequency(region, args.year)

    if args.export:
        task = start_export(products, region)
        print(f"Started export task: {task.id}")
    else:
        print("Water-frequency products built. Re-run with --export to write the GeoTIFF.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
