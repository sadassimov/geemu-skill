"""GEE + local scikit-learn Random Forest, round-tripped to an Earth Engine
classifier via geemap.ml.

Ported from the geospatial-study notebook `rfregression.ipynb`: account info
removed (points / ROI / output trees are placeholder assets), proxy hard-code
removed, project-ID gate + `--dry-run` + opt-in asset export added.

Flow: build a Landsat composite with spectral indices -> sample it at labelled
points -> export a training CSV -> train sklearn RandomForestRegressor locally ->
convert the trees to an Earth Engine classifier with geemap.ml -> apply it server
side. Optionally export the trees to a FeatureCollection asset for reuse in the
cloud / JavaScript.

CAVEAT: the original used Landsat Collection 1 SR (retired 2023). Migrate to
Collection 2 L2 (`LANDSAT/LC08/C02/T1_L2`, bands `SR_B*`, QA `QA_PIXEL`, scale
`DN*0.0000275-0.2`). See sources.md.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)

import ee
import geemap


PROJECT_ID = (
    os.environ.get("EE_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("EE_PROJECT_ID")
    or "PROJECT_ID"
)
ROI_ASSET = "users/your_username/roi"            # study-area FeatureCollection
POINTS_ASSET = "users/your_username/training_points"  # labelled points (property 'landcover')
TREES_ASSET = "users/your_username/rf_trees"     # output: exported tree FeatureCollection
L8_COLLECTION = "LANDSAT/LC08/C01/T1_SR"         # C01 retired -> use LANDSAT/LC08/C02/T1_L2
START_DATE = "2021-01-01"
END_DATE = "2022-01-01"
SCALE = 30
N_TREES = 10
LABEL = "landcover"
TRAIN_CSV = str(SCRIPT_DIR / "out" / "rf_train.csv")
BANDS = ["B2", "B3", "B4", "B5", "B6", "B7"]
FEATURES = BANDS + ["MNDWI", "NDBI", "NDVI", "EWI", "NDWI", "AWEI", "LSWI", "NBR2"]
WORKLOAD_TAG = "geemu-rf-regression"


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
    # Restricted network? Set HTTP_PROXY / HTTPS_PROXY first (references/network_proxy.md).
    try:
        geemap.ee_initialize(project=project)
        ee.data.getAssetRoots()
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine/geemap initialization failed. Check HTTP(S)_PROXY first, "
            "then authentication and Cloud Project permissions."
        ) from exc
    try:
        ee.data.setDefaultWorkloadTag(WORKLOAD_TAG)
    except Exception:
        pass


def mask_l8(image):
    qa = image.select("pixel_qa")
    mask = qa.bitwiseAnd(1 << 3).eq(0).And(qa.bitwiseAnd(1 << 5).eq(0))
    return image.updateMask(mask).toFloat().divide(10000).copyProperties(image, image.propertyNames())


def build_image(region):
    image = (
        ee.ImageCollection(L8_COLLECTION)
        .map(mask_l8)
        .filterDate(START_DATE, END_DATE)
        .filterBounds(region)
        .filter(ee.Filter.lte("CLOUD_COVER", 5))
        .mean()
        .clip(region)
    )
    ndvi = image.normalizedDifference(["B5", "B4"]).rename("NDVI")
    ndbi = image.normalizedDifference(["B6", "B5"]).rename("NDBI")
    mndwi = image.normalizedDifference(["B3", "B6"]).rename("MNDWI")
    ndwi = image.normalizedDifference(["B3", "B5"]).rename("NDWI")
    lswi = image.normalizedDifference(["B5", "B6"]).rename("LSWI")
    nbr2 = image.normalizedDifference(["B6", "B7"]).rename("NBR2")
    ewi = image.expression(
        "(G - NIR - SWIR1) / (G + NIR + SWIR1)",
        {"G": image.select("B3"), "NIR": image.select("B5"), "SWIR1": image.select("B6")},
    ).rename("EWI")
    awei = image.expression(
        "4*(G - SWIR1) - (0.25*NIR + 2.75*SWIR2)",
        {
            "G": image.select("B3"),
            "NIR": image.select("B5"),
            "SWIR1": image.select("B6"),
            "SWIR2": image.select("B7"),
        },
    ).rename("AWEI")
    return image.addBands([ndvi, ndbi, mndwi, ndwi, lswi, nbr2, ewi, awei])


def train_and_classify(image, points, export_trees):
    import pandas as pd
    from sklearn import ensemble
    from geemap import ml

    training = image.select(FEATURES).sampleRegions(
        collection=points, properties=[LABEL], scale=SCALE
    )
    os.makedirs(os.path.dirname(TRAIN_CSV), exist_ok=True)
    geemap.ee_to_csv(training, TRAIN_CSV)

    df = pd.read_csv(TRAIN_CSV)
    rf = ensemble.RandomForestRegressor(N_TREES).fit(df[FEATURES], df[LABEL])
    trees = ml.rf_to_strings(rf, FEATURES, output_mode="REGRESSION")
    classifier = ml.strings_to_classifier(trees)

    predicted = image.select(FEATURES).classify(classifier, "predicted")

    if export_trees:
        ml.export_trees_to_fc(trees, TREES_ASSET)
        print(f"Exporting trees to FeatureCollection asset: {TREES_ASSET}")
    return predicted


def print_dry_run(args):
    print("case=random_forest_regression")
    print(f"roi_asset={args.roi_asset}")
    print(f"points_asset={args.points_asset}  label={LABEL}")
    print("project=PROJECT_ID (required before online Earth Engine run)")
    print(f"collection={L8_COLLECTION} (C01 retired -> use C02/T1_L2)  time={START_DATE}/{END_DATE}")
    print(f"features={FEATURES}")
    print(f"model=sklearn RandomForestRegressor(n_estimators={N_TREES}) -> geemap.ml classifier")
    print(f"training_csv={TRAIN_CSV}")
    print(f"trees_asset={TREES_ASSET} (only with --export)")


def parse_args():
    p = argparse.ArgumentParser(description="GEE + sklearn Random Forest regression example.")
    p.add_argument("--dry-run", action="store_true", help="Print the plan; no Earth Engine / sklearn call.")
    p.add_argument("--project", help="Earth Engine Cloud Project ID.")
    p.add_argument("--roi-asset", default=ROI_ASSET, help="Study-area FeatureCollection asset.")
    p.add_argument("--points-asset", default=POINTS_ASSET, help="Labelled training points asset.")
    p.add_argument("--export", action="store_true", help="Export the trained trees to TREES_ASSET.")
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
    points = ee.FeatureCollection(args.points_asset)
    image = build_image(region)
    train_and_classify(image, points, args.export)
    print("Trained RF and built the predicted (regression) image.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
