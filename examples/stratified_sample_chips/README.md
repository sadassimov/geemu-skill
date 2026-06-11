# Stratified 256x256 Sample Chips / 分层抽样生成样本切片

Build a deep-learning training set by **stratified sampling**: use an existing
land-cover product (ESRI 10 m global LULC, water class) as the label and a
Sentinel-2 median composite as the image, stratified-sample N points over the ROI,
and download a label chip and an image chip around each point (via `getThumbURL`),
in parallel with `multiprocessing`.

Ported from `geospatial-study/processimage.ipynb`. The Jupyter `%%writefile` +
`import test` worker trick is replaced by a normal multiprocessing pool; ROI is a
placeholder asset; proxy hard-code removed; `COPERNICUS/S2_SR` updated to
`COPERNICUS/S2_SR_HARMONIZED`.

## Run

```bash
python code.py --dry-run
python code.py --project PROJECT_ID --roi-asset users/you/roi --count 100 --out-dir ./out
```

Output: `out/label/tile_*.png` and `out/image/tile_*.png`.

## Prompt

> Use GEEMu to generate 256x256 training chips by stratified sampling. Use ESRI
> 10 m LULC (water class) as the label and a Sentinel-2 median as the image,
> stratified-sample 100 points over my ROI, and download a label chip and an image
> chip around each point in parallel. Save them under label/ and image/ folders.

> 用 GEEMu 通过分层抽样生成 256x256 训练切片。用 ESRI 10m 土地覆盖(水体类)作为
> label,Sentinel-2 median 作为影像,在我的 ROI 上分层抽样 100 个点,并行下载每个
> 点周围的 label 切片和影像切片,分别存到 label/ 和 image/ 目录。

## Caveat

`getThumbURL`/`getDownloadURL` are rate-limited; keep `processes` modest. Requires
`requests` (imported lazily). Writes many files locally.
