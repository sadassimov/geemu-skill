<p align="center">
  <img src="assets/geemu-banner-readme.png" alt="GEEMu banner">
</p>

<p align="center">
  <img src="assets/geemu-mark-128.png" alt="GEEMu logo" width="96">
</p>

<h1 align="center">GEEMu Skill</h1>

<p align="center">
  <a href="README.md">🇬🇧 English</a>
</p>

**Google Earth Engine Master Utility (GEEMu)**

GEEMu 是一个面向 Google Earth Engine、Earth Engine Python API 和 geemap 的
skill 文件夹，可用于 OpenAI Codex 和 Claude Code。它不是单纯的代码片段库，
而是一个研究流程助手：先检查本地环境和认证，再理解研究区、分辨率、数据层、
边界复杂度和输出目标，最后写出可以运行、可以复现、可以记录的 GEE Python
代码。

## 兼容性

- OpenAI Codex：将 GEEMu 安装为本地 skill 文件夹，然后让 Codex 使用 GEEMu
  处理 GEE/geemap 任务。
- Claude Code：将同一文件夹安装到 Claude skills 目录下，然后让 Claude Code
  使用 GEEMu。
- 该 skill 完全基于文件。不需要独立的向量搜索服务器、嵌入模型下载、私有凭证
  或原始开发工作区。

GEEMu 的核心是 `SKILL.md` 加参考资料、模板、示例和本地知识库，所以同一份
GitHub 包可以被 Codex 和 Claude Code 读取。两边的区别主要是安装目录不同。

## 安装教程

GitHub 仓库：

`https://github.com/sadassimov/geemu-skill`

> **必须完整安装，不要遗漏任何文件。** skill 依赖整个包，尤其是本地知识库
> `gee_vector_db/chunks.jsonl` 和 `gee_vector_db/documents.jsonl`（几十 MB）：
> 检索就是搜索这两个 JSONL 文件，缺了它们 skill 无法工作。`git clone` 和 GitHub
> 的 "Download ZIP" 本来就包含所有文件——只要不要手动挑选文件、不要排除大文件或
> `.jsonl`、也不要用 shallow/sparse/partial checkout 即可。

### 方式 A：从 GitHub 克隆

OpenAI Codex（Windows PowerShell）：

```powershell
git clone https://github.com/sadassimov/geemu-skill.git "$env:USERPROFILE\.codex\skills\GEEMu"
```

Claude Code（Windows PowerShell）：

```powershell
git clone https://github.com/sadassimov/geemu-skill.git "$env:USERPROFILE\.claude\skills\GEEMu"
```

OpenAI Codex（macOS/Linux）：

```bash
git clone https://github.com/sadassimov/geemu-skill.git ~/.codex/skills/GEEMu
```

Claude Code（macOS/Linux）：

```bash
git clone https://github.com/sadassimov/geemu-skill.git ~/.claude/skills/GEEMu
```

### 方式 B：下载 ZIP

1. 打开 `https://github.com/sadassimov/geemu-skill`。
2. 下载仓库的 ZIP 文件。
3. 解压后将文件夹重命名为 `GEEMu`。
4. Codex 用户放到：`~/.codex/skills/GEEMu`。
5. Claude Code 用户放到：`~/.claude/skills/GEEMu`。

Windows 用户可以使用以下等效路径：

- Codex：`%USERPROFILE%\.codex\skills\GEEMu`
- Claude Code：`%USERPROFILE%\.claude\skills\GEEMu`

## 架构

GEEMu 的核心架构：

- **主指令层** (`SKILL.md`)：规定每次 GEE 任务必须先检查 project ID、认证、
  geemap、代理和研究设计。
- **参考层** (`references/`)：把环境、代理、数据层、边界层、导出策略等细节拆到
  独立文件。
- **本地知识层** (`gee_vector_db/`)：把本地经验和参考资料清洗成
  `chunks.jsonl` / `documents.jsonl`，用关键词检索。
- **数据建议层** (`awesome-gee-community-datasets/community_datasets.csv`)：
  使用社区数据表辅助选择 GEE 数据集。
- **记录层** (`templates/`)：每次代码任务都应留下 `RUN.md` 和 `DATA_LAYER.md`，
  说明研究区、数据变换、分辨率、阈值、导出参数和关键假设。
- **示例** (`examples/`)：完整参考任务，包括 Sentinel-2 NDVI、分块导出、geemap
  本地下载、社区数据推荐、NSW dNBR/NBR 恢复、Landsat 水体频率、随机森林回归
  （GEE + scikit-learn）、分层抽样 256x256 切片、深度学习水体推理。
- **环境检查** (`scripts/check_local_environment.py`)：确定性地检查本地 Python、
  geemap、Earth Engine 凭证、project ID 和 geemap 向量助手可用性。

## 工作流

GEEMu 的工作流不是"直接写代码"，而是先把研究问题落地：

1. 确认或请求 Google Cloud Project ID。
2. 检查 `ee`、`geemap`、凭证和向量助手是否可用。
3. 提醒受限网络中的用户在访问 GEE 前配置代理环境变量。
4. 定义研究问题、研究区、时间窗口、计算分辨率、输出产品和导出目标。
5. 谨慎选择边界数据：行政边界、已上传矢量、geemap 转换的本地矢量或手绘几何。
6. 评估边界复杂度，决定是否需要简化、缓冲、裁剪或分块导出。
7. 选择数据层和变换，在缩放、掩膜、阈值化或导出前先解释每个值或波段的含义。
8. 使用 geemap 编写 GEE Python 代码。
9. 用 Markdown 记录运行和数据层决策。

## Prompt 示例

安装 skill 后可以直接用类似下面的 prompt 触发 GEEMu。

### 加州大火恢复监测

> 用 GEEMu 帮我写一个 geemap + Earth Engine Python 工作流，研究美国加州大火
> 区域的植被恢复。开头先检查本地 Python 环境、Earth Engine 认证、geemap
> 是否安装、是否需要代理，以及 Google Cloud Project ID。研究区先用 GADM
> 行政边界提取 California，再根据指定火场或火烧边界缩小分析范围。用火前
> 3 年 median NBR 作为 baseline，火后 1 年做恢复评估。先用 dNBR 检测火烧区，
> 再用 NBR 恢复比例表达恢复情况，导出恢复比例图。请考虑合适分辨率、边界
> 复杂度、是否需要分块导出，并写 RUN.md 和 DATA_LAYER.md 记录参数、数据层
> 和变换逻辑。

### Sentinel-2 植被指数

> 用 GEEMu 写一个 Sentinel-2 NDVI 任务。先检查认证和 project ID，再根据研究区
> 选择云掩膜策略，说明分辨率和波段变换，生成 median composite，导出 NDVI
> 栅格，并记录这次运行的参数。

### 分块导出

> 用 GEEMu 给一个大范围复杂边界设计分块导出流程。请评估边界复杂度，判断
> 是否需要简化、buffer、clip 或 tile，保持边界属性含义不变，生成可管理的
> Earth Engine Python 导出代码，并记录 scale 和 CRS 选择。

### geemap 直接导出到本地

> 用 GEEMu 写一个 geemap 直接从 Earth Engine 下载到本地 GeoTIFF 的流程。先检查
> 本地环境、认证、代理需求和 Google Cloud Project ID。研究区可以让用户提供
> 已上传的 ROI asset，也可以用简单经纬度 bbox。使用 `ESA/WorldCover/v100`，
> 选择 `Map` 波段，土地覆盖类别要用 nearest-neighbor，避免类别值被插值破坏。
> 请说明什么时候适合直接本地下载，什么时候应该改成分块导出或 Drive 导出，
> 并写 RUN.md 和 DATA_LAYER.md 记录 ROI、输出路径、类别数据、scale、CRS 和风险。

### 社区数据推荐

> 用 GEEMu 帮我为干旱、气候、火灾或植被监测任务推荐 GEE 数据集。请检索本地
> 知识库和社区数据表，比较空间分辨率、时间覆盖、变量含义、局限性和导出
> 可行性，再决定是否写代码。

### Landsat 水体频率

> 用 GEEMu 基于 Landsat 地表反射率做多年水体频率制图：去云，算 NDVI/NDWI/MNDWI/EVI，
> 判定水体，去除山体阴影/高 HAND/陡坡，聚合逐年频率，分 无/季节/永久 三类，叠加 GAIA
> 不透水面并导出。请用 Landsat C02。

### 随机森林回归

> 用 GEEMu 训练结合 GEE 与本地 scikit-learn 的随机森林回归：构建带光谱指数的 Landsat
> 合成影像，在标注点采样，导出训练 CSV，训练 RandomForestRegressor，用 geemap.ml 转成
> Earth Engine 分类器并应用。

### 分层抽样切片

> 用 GEEMu 通过分层抽样生成 256x256 训练切片：用 ESRI 10m 土地覆盖（水体）作 label，
> Sentinel-2 median 作影像，在 ROI 上抽 100 个点，并行下载 label 和影像切片。

### 深度学习水体推理

> 用 GEEMu 做深度学习地表水推理：用 fishnet 切块导出 Sentinel-2 瓦片，对每块用预训练
> WatNet 推理，输出二值水体 GeoTIFF，并说明如何用 geeup 上传结果。

## 许可与声明

GEEMu 自有文件（`SKILL.md`、`references/`、`templates/`、`examples/`、`scripts/`
和本 README）按 MIT 许可发布，详见 `LICENSE`。

打包的第三方内容仍遵循各自的原始许可：Awesome GEE Community Datasets 表
（CC BY 4.0）、Earth Engine 文档摘录（CC BY 4.0 / Apache 2.0）、geemap（MIT）
以及本地知识库中的其他来源。再使用或再分发前请查看 `THIRD_PARTY_NOTICES.md`。
