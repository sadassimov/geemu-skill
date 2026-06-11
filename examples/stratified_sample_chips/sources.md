# Sources & Notes

## Ported from
- Repo: `github.com/sadassimov/geospatial-study`
- Notebook: `processimage.ipynb`

## Datasets / tools
- `projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m` — ESRI 10 m global
  land cover (water class used as the label). Public community asset. **Kept.**
- `COPERNICUS/S2_SR_HARMONIZED` — Sentinel-2 SR (the original `COPERNICUS/S2_SR`
  was deprecated; updated here).
- `Image.getThumbURL` / `getDownloadURL` for chip download; `requests` for I/O.

## Structure changes
- The Jupyter `%%writefile test.py` + `import test` worker trick was replaced by a
  normal `multiprocessing.Pool` with an initializer that re-initializes Earth Engine
  and rebuilds the (non-picklable) `ee` image objects in each worker process.

## Account info removed
- ROI asset → `--roi-asset` / `ROI_ASSET` placeholder.
- Hardcoded local proxy / custom init endpoint removed — use `HTTP(S)_PROXY` env
  vars and `geemap.ee_initialize(project=...)`.
