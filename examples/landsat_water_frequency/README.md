# Landsat Water-Frequency Mapping / Landsat 水体频率制图

Multi-year surface-water **frequency** from Landsat 5/7/8 surface reflectance,
with an impervious-surface (GAIA) overlay. Per-scene cloud masking → NDVI/NDWI/
MNDWI/EVI → ARWDR-style water flag → hill-shadow / HAND / slope masks → yearly
water frequency → classify into {0 none, 1 seasonal, 2 permanent}.

Ported from `geospatial-study/water-butoushui.ipynb`. Account info removed: the
ROI is a placeholder asset (`--roi-asset`), the local proxy hard-code is gone.

## Run

```bash
python code.py --dry-run                              # show the plan, no EE call
python code.py --project PROJECT_ID --roi-asset users/you/roi          # build
python code.py --project PROJECT_ID --roi-asset users/you/roi --export # + GeoTIFF
```

## Prompt

> Use GEEMu to map multi-year surface-water frequency for my study area from
> Landsat surface reflectance. Check the Cloud Project ID and environment first,
> mask clouds, compute NDVI/NDWI/MNDWI/EVI, flag water with an index rule, remove
> hill shadow, high HAND and steep slopes, aggregate a yearly water frequency,
> classify it into none/seasonal/permanent, overlay GAIA impervious surface, and
> export the result. Use Landsat Collection 2 (C02/T1_L2).

> 用 GEEMu 基于 Landsat 地表反射率做多年水体频率制图。先确认 project ID 和环境,
> 去云,计算 NDVI/NDWI/MNDWI/EVI,用指数规则判定水体,去除山体阴影、高 HAND 和
> 陡坡,聚合逐年水体频率,分为 无/季节性/永久 三类,叠加 GAIA 不透水面,导出结果。
> 请使用 Landsat Collection 2(C02/T1_L2)。

## Caveat

The code keeps the original Collection 1 SR ids, which USGS retired in 2023.
Migrate to Collection 2 L2 (bands `SR_B*`, QA `QA_PIXEL`, scale `DN*0.0000275-0.2`).
See `sources.md`.
