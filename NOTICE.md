# Attribution / NOTICE

本目录（DSH 数据分析师岗位插件）包含改编自下列作品的素材：

- Repository: https://github.com/anthropics/knowledge-work-plugins
- Directory: `data/`（Data Analyst plugin）
- License: Apache License 2.0 — https://www.apache.org/licenses/LICENSE-2.0
- Copyright: Anthropic

## 关于 §4(d) 的 NOTICE 义务（实测说明）

上游仓库**不提供** NOTICE 文件（已核对其完整文件清单，`data/` 下只有 `LICENSE`，无 `NOTICE`）。
因此 Apache-2.0 §4(d) 所附条件在本作品中**不被触发**。本文件是主动提供的归属说明，不是履行 §4(d)。

## §4(b) 修改声明

所有衍生文件都在正文顶部带有醒目的修改声明：

> Modified from the original work by Anthropic.

已带该声明的文件：`assets/*/SKILL.md`（10 个）与 `assets/data-context-extractor/references/*.md`（2 个）。

## 改编内容（不是逐字复制）

1. 正文由英文改写为中文优先，代码与专业术语保留英文。
2. 移除 Claude 专有机制：`.claude-plugin/plugin.json`、`allowed-tools`、`argument-hint`、Claude 内部工具名、`claude plugin marketplace` 安装流程。
3. MCP 连接器由「插件自带 `.mcp.json`」改为「用户在 DSH 设置 → MCP 自行添加」。
4. 可视化/文件产出改为使用 DSH 捆绑的 Python 环境与 `present` / Office 工具；因捆绑环境无 matplotlib，另建纯 Pillow 渲染脚本 `assets/data-create-viz/scripts/chart_pillow.py`。
5. 统计检验因捆绑环境无 scipy/statsmodels，改为 numpy/pandas 手写实现并注明精度与局限。
6. 技能合并与重命名：统一 `data-` 前缀（避免与已安装技能重名），部分「命令 + 知识」技能合并为自包含技能。
7. 技能改为通过 DSH 的 Agent 预设（preset）作用域分发，取代上游的 marketplace 逐个安装模型。

## 非衍生文件

`index.js`、`cordis.patch.yml`、`locale/*.json`、`icon.svg`、`INSTALL-CHECKLIST.md`、本目录的 `README.md`，以及「数据分析师」preset 的 persona 文字，由本插件作者撰写（非上游内容），同样以 Apache-2.0 提供。

## 商标

Apache-2.0 §6 不授予任何商标使用权。本作品与 Anthropic 无隶属或背书关系；「Claude」「Anthropic」为各自所有者的商标。
