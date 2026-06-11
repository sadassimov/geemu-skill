# Random Forest Regression (GEE + scikit-learn) / 随机森林回归

Train a Random Forest **regression** that combines Earth Engine with a local
scikit-learn model, round-tripped to an EE classifier via `geemap.ml`: build a
Landsat composite with spectral indices → sample at labelled points → export a
training CSV → fit `RandomForestRegressor` → convert trees to an EE classifier →
apply server-side. Optionally export the trees to a FeatureCollection asset for
reuse in the cloud / JavaScript.

Ported from `geospatial-study/rfregression.ipynb`. Account info removed: points,
ROI, and the output trees asset are placeholders; proxy hard-code removed.

## Run

```bash
python code.py --dry-run
python code.py --project PROJECT_ID --roi-asset users/you/roi --points-asset users/you/points
python code.py --project PROJECT_ID --roi-asset users/you/roi --points-asset users/you/points --export
```

Needs a labelled points FeatureCollection with a numeric `landcover` property.

## Prompt

> Use GEEMu to train a Random Forest regression that combines GEE and a local
> scikit-learn model. Build a Landsat composite with spectral indices (NDVI, NDBI,
> MNDWI, NDWI, EWI, AWEI, LSWI, NBR2), sample it at my labelled points, export a
> training CSV, fit a RandomForestRegressor, convert the trees to an Earth Engine
> classifier with geemap.ml, apply it, and optionally save the trees to an asset.
> Use Landsat Collection 2.

> 用 GEEMu 做一个结合 GEE 和本地 scikit-learn 的随机森林回归。构建带光谱指数
> (NDVI、NDBI、MNDWI、NDWI、EWI、AWEI、LSWI、NBR2)的 Landsat 合成影像,在我的
> 标注样本点上采样,导出训练 CSV,训练 RandomForestRegressor,用 geemap.ml 把树
> 转成 Earth Engine 分类器并应用,可选地把树导出成 asset。请使用 Landsat C02。

## Caveat

Keeps the original Collection 1 SR id; migrate to Collection 2 L2 (see
`sources.md`). Requires `scikit-learn` and `pandas` (imported lazily, only for the
real run).
