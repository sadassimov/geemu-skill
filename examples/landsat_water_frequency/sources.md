# Sources & Notes

## Ported from
- Repo: `github.com/sadassimov/geospatial-study`
- Notebook: `water-butoushui.ipynb`

## Datasets
- Landsat 5/7/8 Surface Reflectance — original used Collection 1
  (`LANDSAT/LT05/C01/T1_SR`, `LE07/C01/T1_SR`, `LC08/C01/T1_SR`).
- `users/gena/global-hand/hand-100` — HAND (Height Above Nearest Drainage), a
  public community asset by Gennadii Donchyts. **Kept** (public, not account info).
- `USGS/GMTED2010` — global DEM (slope / terrain).
- `Tsinghua/FROM-GLC/GAIA/v10` — GAIA global impervious surface (`change_year_index`).

## Collection 1 → Collection 2 migration
USGS retired Landsat Collection 1 in 2023. To run today, switch to Collection 2 L2:
- IDs: `LANDSAT/LC08/C02/T1_L2`, `LANDSAT/LE07/C02/T1_L2`, `LANDSAT/LT05/C02/T1_L2`.
- Optical bands: `SR_B*` (L8/9: SR_B2 blue … SR_B7 swir2; L4/5/7: SR_B1 blue … SR_B7 swir2).
- QA: `QA_PIXEL` (bit 3 cloud shadow, bit 4 snow, bit 5 cloud) + `QA_RADSAT`.
- Scaling: surface reflectance = `DN * 0.0000275 - 0.2` (not `/10000`).

## Account info removed
- ROI asset → placeholder `--roi-asset` / `ROI_ASSET`.
- Hardcoded local proxy removed — set `HTTP(S)_PROXY` env vars instead.
