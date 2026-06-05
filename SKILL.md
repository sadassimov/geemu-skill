---
name: geemu-skill
description: Use when Codex needs to answer questions or write Python code for Google Earth Engine (GEE), the Earth Engine Python API, geemap, ee.Image/ImageCollection/FeatureCollection workflows, remote-sensing scripts, exports, reducers, cloud masking, dataset lookup, or Qiongwei's local GEE/geemap knowledge and practical experience.
---

# GEEMu Skill

Use this skill to write practical Google Earth Engine and geemap workflows from
the bundled GEEMu references and local vector knowledge base.

## Included Knowledge

- `gee_vector_db/`: portable local knowledge database derived from the full
  GEEMu bundle and practical experience notes.
- `awesome-gee-community-datasets/community_datasets.csv`: structured community
  dataset index.
- `references/`: GEEMu workflow gates for environment, proxy, research design,
  data semantics, boundaries, local vectors, and compute strategy.
- `templates/`: run-log and data-layer templates.
- `examples/`: compact runnable examples.

This compact full GitHub package keeps the complete usable GEEMu workflow through
the bundled local knowledge DB, references, examples, and community CSV. It does
not carry the redundant raw `google-earth-engine/` or `geemap/` documentation
snapshots. Search is keyword-based and does not require an embedding model
download. Prefer the bundled local knowledge DB first; use source URLs or
official online docs when a direct API detail must be verified.

## Retrieval Workflow

For non-trivial questions, search local knowledge before answering or coding:

```powershell
python _gee_vector_db.py search "<query>" --db gee_vector_db --limit 8
```

For community dataset lookup:

```powershell
rg -n "<term>" awesome-gee-community-datasets/community_datasets.csv
```

Prefer evidence in this order:

1. Official Earth Engine behavior found in vector hits or source URLs.
2. geemap usage patterns found in vector hits or examples.
3. Qiongwei's local practical experience represented in the knowledge DB.
4. Community dataset catalog rows, after checking license and docs links.

## Required Gates

Before writing final code, run the relevant gates:

- Startup gate: open `references/local_environment.md`; confirm Python can import
  `ee` and `geemap`, Earth Engine credentials exist, a Cloud Project ID is known,
  and online initialization succeeds. If the Project ID is missing, stop and ask.
- Network/proxy: for restricted networks, open `references/network_proxy.md`.
- Research design: for open-ended tasks, open `references/research_design.md`;
  decide study area, analysis scale/resolution, and output target. Use local
  knowledge to suggest options when the user has not specified them.
- Local vector ROI: for shapefile, GeoJSON, GeoPackage, or GeoDataFrame inputs,
  open `references/local_vector_roi.md`.
- Data semantics: for dataset choice, bands, units, scale/offset, QA masks, or
  transformations, open `references/data_layer.md`.
- Boundary and compute: for ROI complexity, bbox, clipping, tiling, exports,
  memory, or EECU risk, open `references/boundary_compute.md`.
- Traceability: save generated scripts and Markdown logs under
  `runs/YYYYMMDD-HHMM-task-name/`.

Ask clarifying questions when missing information changes correctness, cost,
network access, or data meaning. If a missing value is routine, use an explicit
placeholder and record the assumption.

## Output Artifacts

Every generated or revised GEE/geemap task should save:

```text
runs/YYYYMMDD-HHMM-task-name/
  code.py
  RUN.md
  DATA_LAYER.md
  sources.md
```

Use `templates/RUN.md` and `templates/DATA_LAYER.md` as starting points. Do not
overwrite old run folders.

## Coding Rules

- Write Python-first GEE code unless the user explicitly asks for JavaScript.
- Use explicit `import ee` and `import geemap` in runnable Python scripts.
- The saved script is named `code.py`, which shadows Python's standard-library
  `code` module that geemap loads through ipywidgets/IPython. Before importing
  geemap, drop the script directory from `sys.path[0]` so the stdlib module wins;
  otherwise `import geemap` crashes with
  `AttributeError: module 'code' has no attribute 'InteractiveConsole'`:

  ```python
  import sys
  from pathlib import Path
  if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
      sys.path.pop(0)
  import ee
  import geemap
  ```
- Initialize with `geemap.ee_initialize(project="PROJECT_ID")` or an equivalent
  `ee.Initialize(project="PROJECT_ID")` check before building ROI,
  ImageCollection, reducers, exports, or maps.
- Do not hard-code private project IDs, asset IDs, local paths, proxy
  credentials, tokens, or cookies. Use placeholders like `PROJECT_ID`,
  `ROI_ASSET`, `TILE_ASSET`, and `EXPORT_FOLDER`.
- If local vector data is provided, prefer `geemap.shp_to_ee`,
  `geemap.geojson_to_ee`, or `geemap.gdf_to_ee` after checking CRS, geometry
  type, and feature count.
- Keep heavy work server-side with Earth Engine objects. Avoid `.getInfo()` on
  large objects.
- Prefer `filterDate`, `filterBounds`, `select`, `map`, reducers, and exports
  over client-side loops.
- For exports, include `scale`, `region`, `crs`, and destination. Make exports
  opt-in: provide a `--dry-run` mode that prints the resolved parameters with no
  Earth Engine call, and only call `task.start()` when the user passes
  `--export`. Never auto-start an export on a plain run.
- Before exporting a multi-band image, cast every band to one dtype, e.g.
  `image.toFloat()`. Otherwise Earth Engine rejects the task with
  `Exported bands must have compatible data types; found inconsistent types:
  Float32 and Byte`. This happens whenever a float index band (NBR, dNBR, NDVI,
  recovery ratio) is combined with a Byte mask or class band produced by
  `.gte(...)`, `.selfMask()`, or `.toByte()`. Cast at export time, or export the
  integer/categorical products in a separate task that keeps their Byte dtype.
- For direct local GeoTIFF downloads, use `geemap.download_ee_image` only after
  checking that the region is small or controlled. Set `scale`, `region`,
  categorical/continuous dtype, resampling, and local output path deliberately.
  For large or complex ROIs, prefer Drive export, Asset export, or tiled export.
- Verify dataset IDs, band names, units, valid ranges, scale factors, offsets,
  nodata/mask values, QA bit rules, and dtype before numeric transformations.
- If a workflow may exceed Earth Engine limits, provide a tiled, batched, or
  intermediate-Asset pattern.

## Output Style

- Give complete runnable code with a short note about placeholders.
- Mention local file paths or source URLs when citing retrieved evidence.
- If local retrieval finds no direct support, say so and proceed from general
  Earth Engine/geemap knowledge or official online docs.
