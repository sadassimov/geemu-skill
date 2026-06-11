<p align="center">
  <img src="assets/geemu-banner-readme.png" alt="GEEMu banner">
</p>

<p align="center">
  <img src="assets/geemu-mark-128.png" alt="GEEMu logo" width="96">
</p>

<h1 align="center">GEEMu Skill</h1>

<p align="center">
  <a href="README_CN.md">🇨🇳 中文版</a>
</p>

**Google Earth Engine Master Utility (GEEMu)**.

Google Earth Engine Master Utility (GEEMu) is a compact full skill folder for OpenAI Codex and Claude Code. It helps
write Google Earth Engine (GEE) Python workflows with geemap. It is designed for
research-grade remote sensing tasks where the assistant must first check the
local environment, understand the study design, reason about data and
boundaries, then write reproducible GEE Python code.

## Compatibility

- OpenAI Codex: install GEEMu as a local skill folder, then ask Codex to use
  GEEMu for GEE/geemap tasks.
- Claude Code: install the same folder under the Claude skills directory, then
  ask Claude Code to use GEEMu.
- The skill is file-based. It does not require a separate vector-search server,
  embedding model download, private credentials, or the original development
  workspace.

## Installation

GitHub repository:

`https://github.com/sadassimov/geemu-skill`

> **Install the complete folder — do not skip any files.** The skill depends on
> the whole package, especially the local knowledge base
> `gee_vector_db/chunks.jsonl` and `gee_vector_db/documents.jsonl` (tens of MB):
> these JSONL files are what the retrieval workflow searches, so the skill will
> not work without them. `git clone` and GitHub's "Download ZIP" already include
> every file — just don't hand-pick files, exclude large/`.jsonl` files, or use a
> shallow/sparse/partial checkout.

### Option A: Clone From GitHub

For OpenAI Codex on Windows PowerShell:

```powershell
git clone https://github.com/sadassimov/geemu-skill.git "$env:USERPROFILE\.codex\skills\GEEMu"
```

For Claude Code on Windows PowerShell:

```powershell
git clone https://github.com/sadassimov/geemu-skill.git "$env:USERPROFILE\.claude\skills\GEEMu"
```

For OpenAI Codex on macOS/Linux:

```bash
git clone https://github.com/sadassimov/geemu-skill.git ~/.codex/skills/GEEMu
```

For Claude Code on macOS/Linux:

```bash
git clone https://github.com/sadassimov/geemu-skill.git ~/.claude/skills/GEEMu
```

### Option B: Download ZIP

1. Open `https://github.com/sadassimov/geemu-skill`.
2. Download the repository as a ZIP file.
3. Unzip it and rename the folder to `GEEMu`.
4. Put the folder here for Codex: `~/.codex/skills/GEEMu`.
5. Put the folder here for Claude Code: `~/.claude/skills/GEEMu`.

Windows users can use these equivalent locations:

- Codex: `%USERPROFILE%\.codex\skills\GEEMu`
- Claude Code: `%USERPROFILE%\.claude\skills\GEEMu`

## Architecture

GEEMu uses a layered design:

- `SKILL.md`: the main instruction layer. It tells the assistant how to start
  every GEE task, including project ID, authentication, geemap import, proxy
  reminders, research design, data-layer reasoning, boundary complexity, and run
  records.
- `references/`: focused reference layers for local environment checks, proxy
  setup, research design, data selection, administrative/vector boundaries, and
  export strategy.
- `gee_vector_db/`: a portable local knowledge database stored as JSONL text.
  It is searched by lightweight keyword scoring.
- `awesome-gee-community-datasets/community_datasets.csv`: a structured
  community dataset table used as one data-recommendation source.
- `templates/`: standard `RUN.md` and `DATA_LAYER.md` records for documenting
  parameter choices, data transforms, scale, region, export settings, and
  assumptions.
- `examples/`: complete reference tasks, including Sentinel-2 NDVI, tiled export,
  geemap local download, community dataset recommendation, NSW dNBR/NBR recovery,
  Landsat water-frequency mapping, Random Forest regression (GEE + scikit-learn),
  stratified 256x256 sample chips, and deep-learning water inference.
- `scripts/check_local_environment.py`: a deterministic checker for local
  Python, geemap, Earth Engine credentials, project ID, and geemap vector helper
  availability.

## Workflow

When a user asks GEEMu to write GEE code, the expected flow is:

1. Confirm or request the Google Cloud Project ID.
2. Check whether `ee`, `geemap`, credentials, and vector helpers are available.
3. Remind users in restricted networks to configure proxy environment variables
   before online GEE access.
4. Define the research question, study area, time windows, calculation scale,
   output products, and export destination.
5. Choose boundary data deliberately: administrative boundary, uploaded vector,
   local vector converted by geemap, or drawn geometry.
6. Assess boundary complexity and decide whether simplification, buffering,
   clipping, or tiled export is needed.
7. Choose data layers and transformations, then explain what each value or band
   represents before scaling, masking, thresholding, or exporting.
8. Write GEE Python code using geemap where appropriate.
9. Record the run and data layer decisions in Markdown.

## Prompt Examples

Use prompts like these with Codex or Claude Code after installing the skill.

### California Wildfire Recovery

> Use GEEMu to write a geemap-based Earth Engine Python workflow for the
> California wildfire region in the United States. First check the local Python
> environment, Earth Engine authentication, geemap availability, proxy reminder,
> and Google Cloud Project ID. Use GADM administrative boundaries to define the
> California study area, then narrow the analysis to the selected burned region
> or fire perimeter if one is provided. Use a pre-fire 3-year median NBR as the
> baseline, then evaluate post-fire recovery for 1 year after the fire. Compute
> dNBR to detect burned areas, then compute an NBR recovery ratio map relative to
> the baseline and post-fire condition. Use an appropriate scale for regional
> analysis, consider boundary complexity and whether tiled export is needed,
> export the recovery map, and write RUN.md plus DATA_LAYER.md documenting all
> choices.

### Sentinel-2 NDVI

> Use GEEMu to create a Sentinel-2 NDVI workflow for a user-provided study area.
> Check authentication and project ID first, choose a cloud-masking strategy,
> explain the scale and band transformations, make a median composite, export the
> NDVI raster, and record the run decisions.

### Tiled Export

> Use GEEMu to design a tiled export workflow for a large or complex boundary.
> Assess geometry complexity, recommend simplification or tiling, preserve the
> meaning of the boundary, and generate Earth Engine Python code that exports
> manageable tiles with documented scale and CRS choices.

### geemap Local Download

> Use GEEMu to write a geemap workflow that downloads ESA WorldCover 2020
> directly from Earth Engine to a local GeoTIFF. Check the local environment,
> authentication, proxy needs, and Google Cloud Project ID first. Let the user
> provide either an uploaded ROI asset or a simple lon/lat bbox. Use
> `ESA/WorldCover/v100`, select the `Map` band, preserve categorical class
> values with nearest-neighbor resampling, choose a safe scale and dtype, and
> explain when direct local download should be replaced by tiled or Drive export.
> Write RUN.md and DATA_LAYER.md documenting the ROI, output path, class data,
> scale, CRS, and risks.

### Community Dataset Recommendation

> Use GEEMu to recommend candidate GEE datasets for a drought, climate, fire, or
> vegetation-monitoring task. Search the local knowledge database and the
> community dataset table, compare spatial scale, temporal coverage, variables,
> limitations, and export suitability before writing code.

### Landsat Water-Frequency

> Use GEEMu to map multi-year surface-water frequency from Landsat surface
> reflectance for my study area: mask clouds, compute NDVI/NDWI/MNDWI/EVI, flag
> water, remove hill shadow / high HAND / steep slopes, aggregate a yearly water
> frequency, classify it into none/seasonal/permanent, overlay GAIA impervious
> surface, and export. Use Landsat Collection 2.

### Random Forest Regression (GEE + scikit-learn)

> Use GEEMu to train a Random Forest regression combining GEE and a local
> scikit-learn model: build a Landsat composite with spectral indices, sample it
> at my labelled points, export a training CSV, fit RandomForestRegressor, convert
> the trees to an Earth Engine classifier with geemap.ml, and apply it.

### Stratified Sample Chips

> Use GEEMu to generate 256x256 training chips by stratified sampling: use ESRI
> 10 m LULC water as the label and a Sentinel-2 median as the image; sample 100
> points over my ROI and download label + image chips in parallel.

### Deep-Learning Water Inference

> Use GEEMu to run deep-learning surface-water inference: export Sentinel-2 tiles
> over my ROI with a fishnet, run a pretrained WatNet model on each tile, write a
> binary water-map GeoTIFF, and show how to upload the result with geeup.

## License & Notices

GEEMu's own files (`SKILL.md`, `references/`, `templates/`, `examples/`,
`scripts/`, and this README) are released under the MIT License; see `LICENSE`.

Bundled third-party material keeps its original terms: the Awesome GEE Community
Datasets table (CC BY 4.0), Earth Engine documentation excerpts (CC BY 4.0 /
Apache 2.0), geemap (MIT), and other sources represented in the local knowledge
database. Review `THIRD_PARTY_NOTICES.md` before reuse or redistribution.
