# Sources & Notes

## Ported from
- Repo: `github.com/sadassimov/geospatial-study`
- Notebook: `rfregression.ipynb`

## Datasets / tools
- Landsat 8 Surface Reflectance — original used Collection 1 (`LANDSAT/LC08/C01/T1_SR`).
- `geemap.ml` — converts a scikit-learn tree ensemble to an Earth Engine
  classifier (`rf_to_strings`, `strings_to_classifier`, `export_trees_to_fc`).
  Docs: https://geemap.org and the geemap `ml` module.
- `scikit-learn` `RandomForestRegressor`, `pandas` (local training).

## Collection 1 → Collection 2 migration
Switch to `LANDSAT/LC08/C02/T1_L2`: bands `SR_B*`, QA `QA_PIXEL`/`QA_RADSAT`,
scaling `DN * 0.0000275 - 0.2`. Update the index band references accordingly.

## Account info removed
- Training points asset → `--points-asset` / `POINTS_ASSET` placeholder.
- ROI asset → `--roi-asset` / `ROI_ASSET` placeholder.
- Output trees asset → `TREES_ASSET` placeholder.
- Hardcoded local proxy removed — use `HTTP(S)_PROXY` env vars.
