# Sources & Notes

## Ported from
- Repo: `github.com/sadassimov/geospatial-study`
- Notebook: `geemap_colab_dl.ipynb`

## Method / model
- **WatNet** — pretrained CNN for surface-water mapping from Sentinel-2 by Xin Luo
  et al. Model + paper: https://github.com/xinluo2018/WatNet . You must supply the
  pretrained `watnet.h5` yourself (`--model`).
- The `imgPatch` patch/stitch class is by Xin Luo (2021), kept with attribution.
- Input bands expected by WatNet: blue, green, red, NIR, SWIR-1, SWIR-2
  (here S2 `B2,B3,B4,B8,B11,B12`), reflectance scaled to 0–1.

## Datasets / tools
- `COPERNICUS/S2_SR_HARMONIZED` (original used the deprecated `COPERNICUS/S2_SR`).
- `geemap.download_ee_image` (tile download), `geemap.fishnet` (grid).
- Real run deps: `tensorflow`, `gdal` (osgeo), `numpy`, `geemap`. Publishing the
  result back uses `geeup` (documented step, not run by this script).

## Colab specifics removed
- `google.colab.drive.mount`, `!pip install ...`, `geeup cookie_setup`.

## Account info removed
- ROI asset → `--roi-asset` / `ROI_ASSET` placeholder.
- Result asset → `RESULT_ASSET` placeholder (`projects/PROJECT_ID/assets/water_result`).
- geeup `--user <email>` → `<your-email>` placeholder.
- Personal Google Drive paths → local `out/` + `--model` / `--output`.
