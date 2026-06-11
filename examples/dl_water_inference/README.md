# Deep-Learning Water Inference (geemap + WatNet) / 深度学习水体推理

End-to-end surface-water mapping with a pretrained CNN: export Sentinel-2 tiles
over the ROI with a fishnet (`geemap.download_ee_image`), run a pretrained **WatNet**
model on each tile in overlapping patches, and write a binary water-map GeoTIFF.
Uploading the result back to Earth Engine is a documented `geeup` step (no account
baked in).

Ported from `geospatial-study/geemap_colab_dl.ipynb`. Colab specifics
(`drive.mount`, `!pip`, `geeup cookie_setup`) removed; ROI / result asset / output
dir / model path are placeholders; the geeup email is removed; `COPERNICUS/S2_SR`
updated to `COPERNICUS/S2_SR_HARMONIZED`. The `imgPatch` class is by Xin Luo (2021),
kept with attribution.

## Run

```bash
python code.py --dry-run
python code.py --project PROJECT_ID --roi-asset users/you/roi --export-tiles --out-dir ./out
python code.py --infer --input ./out/0.tif --model ./watnet.h5 --output ./out/water_map.tif
```

## Prompt

> Use GEEMu to run deep-learning surface-water inference. Export Sentinel-2 tiles
> over my ROI with a fishnet, run a pretrained WatNet model on each tile in
> overlapping patches, and write a binary water-map GeoTIFF. Then show how to
> upload the result back to Earth Engine with geeup. Use S2_SR_HARMONIZED.

> 用 GEEMu 做深度学习地表水推理。用 fishnet 把我的 ROI 切块,导出 Sentinel-2 瓦片,
> 对每个瓦片用预训练 WatNet 模型分块推理,输出二值水体 GeoTIFF;再说明如何用 geeup
> 把结果上传回 Earth Engine。请使用 S2_SR_HARMONIZED。

## Caveat

Real run needs heavy deps — `tensorflow`, `gdal` (osgeo), `numpy`, `geemap` — and a
pretrained `watnet.h5` (see `sources.md`). This is a reference pipeline; adapt paths
and the model to your setup.
