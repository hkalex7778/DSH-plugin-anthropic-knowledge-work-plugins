# Attribution / NOTICE

本仓库包含改编自下列作品的素材：

- Repository: https://github.com/anthropics/knowledge-work-plugins
- License: Apache License 2.0 — https://www.apache.org/licenses/LICENSE-2.0
- Copyright: Anthropic
- 衍生的上游插件目录：`data/`（数据分析师）、`operations/`（运营专员）、`productivity/`（效率助手）

## 关于 §4(d) 的 NOTICE 义务（实测说明）

上游仓库**不提供** NOTICE 文件（已逐个核对其完整文件清单：`data/`、`operations/`、`productivity/` 三个插件目录下都只有 `LICENSE`，无 `NOTICE`）。
因此 Apache-2.0 §4(d) 所附条件在本作品中**不被触发**。本文件是主动提供的归属说明，不是履行 §4(d)。

## §4(b) 修改声明

所有衍生文件都在正文顶部带有醒目的修改声明：

> Modified from the original work by Anthropic.

各 bundle 内的 `NOTICE.md` 逐条列出该岗位的具体改动文件清单。概览：

| 岗位 bundle | 衍生的上游技能数 | 说明 |
|---|---|---|
| `dsh-knowledge-work-data/` | 10 | 见其 `NOTICE.md` |
| `dsh-knowledge-work-operations/` | 9 | 见其 `NOTICE.md` |
| `dsh-knowledge-work-productivity/` | 4 | 见其 `NOTICE.md` |

## 改编内容（不是逐字复制，三个岗位共有）

1. 正文由英文改写为中文优先，代码与专业术语保留英文。
2. 移除 Claude 专有机制：`.claude-plugin/plugin.json`、`allowed-tools`、`argument-hint`、Claude 内部工具名、`claude plugin marketplace` 安装流程。
3. MCP 连接器由「插件自带 `.mcp.json`」改为「用户在 DSH 设置 → MCP 自行添加」。
4. 可视化/文件产出改用 DSH 捆绑的 Python 环境与 `present` / Office 工具。
5. 技能改为通过 DSH 的 Agent 预设（preset）作用域分发，取代上游的 marketplace 逐个安装模型。

### 岗位特有改动

- **数据分析师**：可视化另建纯 Pillow 渲染脚本（捆绑 Python 无 matplotlib）；统计检验改为 numpy/pandas 手写实现并注明精度与局限；技能统一 `data-` 前缀并合并部分「命令 + 知识」技能；新增总入口技能 `data-workflow`。
- **运营专员**：涉及日历的技能（capacity-plan / compliance-tracking / status-report）标注为「连接器可选」，未连接时改为手动提供内容。
- **效率助手**：上游重度依赖 Slack / Notion / Asana / Linear / Jira / 日历等 SaaS 连接器。本移植**在每处连接器操作前显式标注降级路径**（未连接时手动提供内容或跳过），并在技能顶部加「连接器依赖」小节；未连接时 `task-management` 完整可用，其余三个技能降级为半自动。

## 非衍生文件

各 bundle 的 `index.js`、`cordis.patch.yml`、`locale/*.json`、`icon.svg`、`INSTALL-CHECKLIST.md`、各岗位 README 与 preset 的 persona 文字，以及本仓库根的 `README.md` 与本文件，由本插件作者撰写（非上游内容），同样以 Apache-2.0 提供。

## 商标

Apache-2.0 §6 不授予任何商标使用权。本作品与 Anthropic 无隶属或背书关系；「Claude」「Anthropic」为各自所有者的商标。
