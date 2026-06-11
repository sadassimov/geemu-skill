"""Deep-learning surface-water inference with geemap + a pretrained WatNet model.

Ported from the geospatial-study notebook `geemap_colab_dl.ipynb` into a runnable
script: Colab specifics (drive.mount, !pip, geeup cookie_setup) removed, account
info replaced with placeholders, project-ID gate + `--dry-run` added. Heavy deps
(tensorflow, GDAL) are imported lazily so `--dry-run` works without them.

Pipeline (two steps):
  1) --export-tiles : build a cloud-masked Sentinel-2 composite, split the ROI with
     a fishnet, and download each tile to a local GeoTIFF (geemap.download_ee_image).
  2) --infer        : run the pretrained WatNet on a downloaded tile and write a
     binary water-map GeoTIFF.
Uploading the result back to Earth Engine is left as a documented `geeup` step so
no account/email is baked into the code.

Requires (for the real run): tensorflow, gdal (osgeo), numpy, geemap, a pretrained
`watnet.h5`. See sources.md for the model and dataset references.
The imgPatch class below is by Xin Luo (2021), kept with attribution.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if sys.path and Path(sys.path[0]).resolve() == SCRIPT_DIR:
    sys.path.pop(0)

import numpy as np

PROJECT_ID = (
    os.environ.get("EE_PROJECT")
    or os.environ.get("GOOGLE_CLOUD_PROJECT")
    or os.environ.get("EE_PROJECT_ID")
    or "PROJECT_ID"
)
ROI_ASSET = "users/your_username/roi"
RESULT_ASSET = "projects/PROJECT_ID/assets/water_result"  # where you'd upload results
OUT_DIR = str(SCRIPT_DIR / "out")
MODEL_PATH = str(SCRIPT_DIR / "watnet.h5")
S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
SCALE = 10
CRS = "EPSG:4326"
WORKLOAD_TAG = "geemu-dl-water"


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


def export_tiles(project, roi_asset, out_dir, max_tiles):
    import ee
    import geemap
    try:
        geemap.ee_initialize(project=project)
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine/geemap init failed. Check HTTP(S)_PROXY first, then auth."
        ) from exc

    roi = ee.FeatureCollection(roi_asset)

    def rm_cloud(image):
        qa = image.select("QA60")
        mask = qa.bitwiseAnd(1 << 10).eq(0).And(qa.bitwiseAnd(1 << 11).eq(0))
        return image.updateMask(mask)

    s2 = (
        ee.ImageCollection(S2_COLLECTION)
        .filterDate("2021-01-01", "2022-01-01")
        .filterBounds(roi)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
        .map(rm_cloud)
        .median()
        .select(["B2", "B3", "B4", "B8", "B11", "B12"])
        .toInt32()
    )

    fishnet = geemap.fishnet(roi, rows=10, cols=10, delta=1)
    feats = fishnet.toList(fishnet.size())
    n = min(int(fishnet.size().getInfo()), max_tiles)
    os.makedirs(out_dir, exist_ok=True)
    for i in range(n):
        cell = ee.Feature(feats.get(i)).bounds()
        out = os.path.join(out_dir, f"{i}.tif")
        print("downloading", out)
        geemap.download_ee_image(
            s2.clip(cell.geometry()), filename=out, scale=SCALE,
            region=cell.geometry(), crs=CRS,
        )
    print(f"Downloaded {n} tile(s) to {out_dir}.")


class imgPatch:
    """Tile a raster into overlapping patches and stitch them back.
    Author: Xin Luo, 2021-03-19 (kept with attribution)."""

    def __init__(self, img, patch_size, edge_overlay):
        self.patch_size = patch_size
        self.edge_overlay = edge_overlay
        self.img = img[:, :, np.newaxis] if img.ndim == 2 else img
        self.img_row, self.img_col = img.shape[0], img.shape[1]

    def toPatch(self):
        patch_list, start_list = [], []
        step = self.patch_size - self.edge_overlay
        expand = np.pad(self.img, ((self.edge_overlay, step), (self.edge_overlay, step), (0, 0)), "constant")
        rows = (expand.shape[0] - self.edge_overlay) // step
        cols = (expand.shape[1] - self.edge_overlay) // step
        for i in range(rows):
            for j in range(cols):
                patch_list.append(expand[i * step:i * step + self.patch_size, j * step:j * step + self.patch_size, :])
                start_list.append([i * step - self.edge_overlay, j * step - self.edge_overlay])
        return patch_list, start_list, rows, cols

    def toImage(self, patch_list, rows, cols):
        ov = self.edge_overlay
        patch_list = [p[ov // 2:-ov // 2, ov // 2:-ov // 2, :] for p in patch_list]
        merged = [np.hstack(patch_list[i * cols:i * cols + cols]) for i in range(rows)]
        img = np.vstack(merged)
        return img[ov // 2:self.img_row + ov // 2, ov // 2:self.img_col + ov // 2, :]


def read_tiff(path_in):
    from osgeo import gdal, osr
    ds = gdal.Open(path_in)
    cols, rows, bands = ds.RasterXSize, ds.RasterYSize, ds.RasterCount
    geotrans, proj = ds.GetGeoTransform(), ds.GetProjection()
    arr = ds.ReadAsArray(0, 0, cols, rows).astype(np.float32)
    espg = osr.SpatialReference(wkt=proj).GetAttrValue("AUTHORITY", 1)
    info = {"geotrans": geotrans, "geosrs": espg, "row": rows, "col": cols, "bands": bands}
    if bands > 1:
        arr = np.transpose(arr, (1, 2, 0))
    return arr, info


def write_tiff(im_data, geotrans, geosrs, path_out):
    from osgeo import gdal
    im_data = np.squeeze(im_data)
    dtype = gdal.GDT_Byte if "int8" in im_data.dtype.name else gdal.GDT_Float32
    if im_data.ndim == 3:
        im_data = np.transpose(im_data, (2, 0, 1))
        bands, h, w = im_data.shape
    else:
        bands, (h, w) = 1, im_data.shape
    ds = gdal.GetDriverByName("GTiff").Create(path_out, w, h, bands, dtype)
    ds.SetGeoTransform(geotrans)
    ds.SetProjection("EPSG:" + str(geosrs))
    if bands > 1:
        for i in range(bands):
            ds.GetRasterBand(i + 1).WriteArray(im_data[i])
    else:
        ds.GetRasterBand(1).WriteArray(im_data)
    del ds


def watnet_infer(rsimg, model_path):
    import tensorflow as tf
    model = tf.keras.models.load_model(model_path, compile=False)
    ip = imgPatch(rsimg, patch_size=512, edge_overlay=80)
    patches, _starts, rows, cols = ip.toPatch()
    results = [np.squeeze(model(p[np.newaxis, :]), axis=0) for p in patches]
    pro_map = ip.toImage(results, rows, cols)
    return np.where(pro_map > 0.5, 1, 0)


def infer(input_tif, model_path, output_tif):
    img, info = read_tiff(input_tif)
    img = np.float32(np.clip(img / 10000.0, 0, 1))   # SR -> reflectance 0..1
    water_map = watnet_infer(img, model_path)
    os.makedirs(os.path.dirname(output_tif) or ".", exist_ok=True)
    write_tiff(water_map.astype(np.int8), info["geotrans"], info["geosrs"], output_tif)
    print(f"Wrote water map: {output_tif}")
    print("To publish back to Earth Engine, upload with geeup (no account is stored here):")
    print(f'  geeup upload --source "<folder>" --dest "{RESULT_ASSET}" --user "<your-email>"')


def print_dry_run(args):
    print("case=dl_water_inference")
    print(f"roi_asset={args.roi_asset}")
    print("project=PROJECT_ID (required for --export-tiles)")
    print(f"image={S2_COLLECTION} median, bands B2,B3,B4,B8,B11,B12  scale={SCALE}")
    print("step1=--export-tiles: fishnet 10x10 -> geemap.download_ee_image per tile")
    print(f"step2=--infer: WatNet on a tile -> binary water GeoTIFF (model={args.model})")
    print(f"out_dir={args.out_dir}  result_asset={RESULT_ASSET} (upload via geeup)")
    print("deps for real run: tensorflow, gdal(osgeo), numpy, geemap, pretrained watnet.h5")


def parse_args():
    p = argparse.ArgumentParser(description="Deep-learning water inference example (geemap + WatNet).")
    p.add_argument("--dry-run", action="store_true", help="Print the plan; no EE / TF / GDAL imports.")
    p.add_argument("--project", help="Earth Engine Cloud Project ID (for --export-tiles).")
    p.add_argument("--roi-asset", default=ROI_ASSET, help="Study-area FeatureCollection asset.")
    p.add_argument("--export-tiles", action="store_true", help="Step 1: download S2 tiles for the ROI.")
    p.add_argument("--infer", action="store_true", help="Step 2: run WatNet on --input.")
    p.add_argument("--input", help="Input tile GeoTIFF for --infer.")
    p.add_argument("--model", default=MODEL_PATH, help="Pretrained watnet.h5 path.")
    p.add_argument("--output", default=str(Path(OUT_DIR) / "water_map.tif"), help="Output water-map GeoTIFF.")
    p.add_argument("--out-dir", default=OUT_DIR, help="Tile output directory.")
    p.add_argument("--max-tiles", type=int, default=4, help="Max tiles to download.")
    return p.parse_args()


def main():
    args = parse_args()
    if args.dry_run or not (args.export_tiles or args.infer):
        print_dry_run(args)
        if not args.dry_run:
            print("\nNothing to do. Pass --export-tiles and/or --infer (or --dry-run).")
        return 0

    if args.export_tiles:
        try:
            project = require_project(args.project)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        export_tiles(project, args.roi_asset, args.out_dir, args.max_tiles)

    if args.infer:
        if not args.input:
            print("ERROR: --infer requires --input <tile.tif>", file=sys.stderr)
            return 2
        infer(args.input, args.model, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
