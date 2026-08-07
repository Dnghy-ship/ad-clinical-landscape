# Alzheimer's Disease Clinical Trial Competitive Landscape

**Version: 0.1.0**

这是一个面向 **阿尔茨海默病产业/投研观察** 的 ClinicalTrials.gov API v2 全流程 Python 项目。

## 能做什么

- 自动分页抓取 `Alzheimer Disease`
- 默认只保留 INTERVENTIONAL study
- 抽取：
  - Phase
  - Lead sponsor / sponsor class
  - Intervention
  - Eligibility
  - Primary outcomes
  - Countries / trial sites
  - Recruitment status
  - Primary completion / completion date
- 机制分类：
  - API 原始 intervention text 保留
  - 人工 curated override 优先
  - 关键词/正则 heuristic 次之
  - 输出 confidence/source，避免把推断当成 API 事实
- 生成：
  - CSV
  - Excel
  - SQLite
  - raw JSON snapshot
  - changes.csv（第二次运行起追踪变化）
  - Plotly HTML report
  - Streamlit interactive dashboard

---

# 1. 先检查你现在的 Conda 环境

你贴出的 `conda list` 明确显示：

```text
python 3.10.19
```

而且大量包是 `py310` build，所以你当前 `mcm_py` 环境本体看起来是 Python 3.10。

先在 PowerShell 执行：

```powershell
python --version
where.exe python
python -c "import sys; print(sys.executable); print(sys.version)"
```

理想结果应包含：

```text
Python 3.10.x
C:\Miniconda3\envs\mcm_py\python.exe
```

项目也附带：

```powershell
.\scripts\check_env.ps1
```

## 你那个 Conda.psm1 报错

你开 PowerShell 时出现的：

```text
AppData\Local\Temp\_MEI...\shell\condabin\Conda.psm1
```

说明 PowerShell profile 中有一个过期的临时 Conda 初始化路径。

先尝试：

```powershell
& "C:\Miniconda3\Scripts\conda.exe" init powershell
```

关闭 PowerShell 后重新打开。

如果仍然报 `_MEI...`，检查：

```powershell
notepad $PROFILE
```

备份后删除/注释掉指向 `AppData\Local\Temp\_MEI...` 的旧 Conda 初始化段，再执行一次：

```powershell
& "C:\Miniconda3\Scripts\conda.exe" init powershell
```

---

# 2. 安装项目

进入解压后的项目目录：

```powershell
cd D:\Clinical_trials\ad_clinical_landscape
conda activate mcm_py
python -m pip install -e .
```

你已有 requests / pandas / plotly / openpyxl / PyYAML 等。
最可能缺的是 Streamlit，`pip install -e .` 会一起安装。

如果希望完全独立环境：

```powershell
conda env create -f environment.yml
conda activate ad_trials
```

---

# 3. 先跑离线测试

```powershell
python -m unittest discover -s tests -v
```

这个测试不联网。

---

# 4. 环境 + API 诊断

```powershell
adtrial doctor
```

或：

```powershell
python -m adtrial doctor
```

它会打印：

- 实际 Python executable
- Python version
- 依赖包版本
- ClinicalTrials.gov API 连通性
- API `dataTimestamp`

---

# 5. 第一次只抓 100 条做 smoke test

```powershell
adtrial collect --max-studies 100
adtrial report
```

然后查看：

```text
output\ad_competitive_landscape.html
```

---

# 6. 完整抓取

```powershell
adtrial all
```

默认查询：

```text
query.cond = Alzheimer Disease
```

并在本地过滤为：

```text
study_type == INTERVENTIONAL
```

没有强制只保留 DRUG，因为阿尔茨海默病竞争格局中还可能包含：

- biological
- device
- neuromodulation
- behavioral intervention

你可以之后在 dashboard 或 CSV 中细分。

---

# 7. 启动交互式 Dashboard

```powershell
adtrial dashboard
```

可筛：

- status
- phase
- sponsor class
- sponsor
- mechanism
- country
- 文本关键词

图表：

- Phase × Status
- Top Lead Sponsors
- Mechanism Landscape
- Primary Completion Timeline
- Geographic Footprint

还能点开单条 NCT 查看：

- interventions
- mechanism annotation
- primary outcomes
- eligibility
- completion dates
- ClinicalTrials.gov link

---

# 8. 输出目录

```text
data/
├─ raw/
│  └─ ctgov_alzheimer_YYYYMMDD_HHMMSS.json
└─ processed/
   ├─ studies.csv
   ├─ interventions.csv
   ├─ primary_outcomes.csv
   ├─ locations.csv
   ├─ changes.csv
   ├─ run_metadata.json
   ├─ alzheimer_trials.xlsx
   └─ alzheimer_trials.sqlite

output/
└─ ad_competitive_landscape.html
```

---

# 9. 为什么机制字段要单独处理？

ClinicalTrials.gov 能结构化提供 intervention 的：

- type
- name
- description
- other names

但“统一、标准化、可直接拿来做赛道统计的药理机制标签”并不是一个可靠的原生字段。

所以项目输出：

```text
mechanism_category
mechanism_confidence
mechanism_matched_terms
mechanism_source
```

其中：

```text
curated_override
```

代表在：

```text
config/mechanism_overrides.csv
```

人工维护过。

```text
heuristic_rule
```

代表通过：

```text
config/mechanisms.yml
```

的规则推断。

做正式行业/金融研究时，对核心资产务必继续用：

- 公司 pipeline
- clinical readout
- 论文
- 专利
- FDA / EMA / CDE

核实机制和资产定位。

---

# 10. Changes：怎么持续追前沿

第一次：

```powershell
adtrial collect
```

建立 baseline。

过一周再次：

```powershell
adtrial collect
```

`changes.csv` 会记录：

- NEW_STUDY
- overall_status changed
- phase changed
- primary_completion_date changed
- completion_date changed
- last_update_post_date changed

这比每次手动浏览几十个 trial 更适合长期追踪。

---

# 11. 产业/金融分析怎么接上去

这个包首先解决：

```text
Clinical landscape
```

下一步推荐你建立资产卡：

```text
Mechanism
→ Phase
→ Trial design
→ Primary endpoint
→ Biomarker enrichment
→ Competitors
→ Upcoming readout
→ Sponsor/company
→ Cash runway
→ Licensing / M&A
→ Valuation / market expectation
```

这样才真正从“生物医学信息学”进入“biotech industry / healthcare investment research”。

---

# 12. 常用命令

```powershell
# 当前解释器检查
.\scripts\check_env.ps1

# 安装
python -m pip install -e .

# 离线测试
python -m unittest discover -s tests -v

# API 诊断
adtrial doctor

# 100 条测试
adtrial collect --max-studies 100
adtrial report

# 完整运行
adtrial all

# Dashboard
adtrial dashboard
```



## v0.2 update

This release focuses on making the project safer and more useful for industry-oriented analysis:

- partial `--max-studies` smoke runs now write to `data/smoke/` and no longer overwrite the full baseline;
- change tracking now compares only full runs;
- adds `pipeline_view.csv` for active therapeutic candidates;
- adds `data_quality.csv` to monitor missing fields and mechanism annotation quality;
- Streamlit deprecated `use_container_width` calls are replaced by `width="stretch"`;
- map visualization uses ISO-3 country codes;
- dashboard includes research presets:
  - All interventional studies
  - Active therapeutics
  - Industry active therapeutics
- adds GitHub Actions tests, MIT license, contributing guide, and a thinking guide.

After upgrading/installing v0.2:

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m adtrial all
python -m adtrial dashboard
```

### Publishing to GitHub

Create a new **empty** repository on GitHub first (do not initialize it with README/license/gitignore because this project already contains them).

Then in PowerShell:

```powershell
git --version
git init
git add .
git status
git commit -m "Initial release: AD clinical landscape v0.2"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

If Git asks you to authenticate, use GitHub's browser/credential-manager flow rather than putting a password or token into project files.

Before the first commit, inspect:

```powershell
git status
```

and make sure downloaded raw data, processed CSV/Excel/SQLite files, and generated HTML reports are not staged.


## v0.2.1 hotfix

Fixes Streamlit dashboard startup under:

```powershell
python -m adtrial dashboard
```

The dashboard is launched by Streamlit as a script, so package-relative import:

```python
from .industry import country_to_iso3
```

was replaced with the package-absolute import:

```python
from adtrial.industry import country_to_iso3
```


## v0.2.2 hotfix

Small UI/repository stabilization release before the first GitHub push.

- Replaces the `×` glyph in chart titles with ASCII wording (`Phase by Status`) to avoid Windows/browser font rendering issues.
- Keeps the Streamlit absolute-import hotfix from v0.2.1.
- Adds `CHANGELOG.md` and a lightweight project-management guide.
- No changes to ClinicalTrials.gov data collection or analytical filtering logic.
