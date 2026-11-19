# dsh-knowledge-work-data

数据分析师岗位插件 for DeepSeek Harness — 对标 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的 `data` 插件，移植并中文化。

## 装完怎么用（给非技术同事）

1. 新建一个会话。
2. 在会话的**模式/Agent 预设选择器**里选 **「数据分析师」**（不是 Standard）。
3. 直接用大白话提需求，例如：「帮我看看这份销售数据，告诉我最近三个月的趋势」，然后把 Excel/CSV 拖进来或 `@` 引用文件。
4. 第一次让它出图时，如果弹出**命令授权**确认框，点确认——那是在本机本地画图，不联网。

想省掉第 2 步：在 **设置 → Agent 预设** 里把「数据分析师」设为新会话默认。

不需要连数据库。没配任何连接器时，插件走「你上传文件 / 你贴查询结果」的路径，功能一样完整。

## 隔离范围（说准确）

本插件的 `data-*` 技能**只出现在选了「数据分析师」的会话里**，普通 Standard 会话看不到它们。

但反过来不成立：「数据分析师」会话里**还会**看到全局技能（`office*`、`memory` 等），因为岗位 preset 保留了 DSH 的技能文件系统与 Office 能力——出报告、出表格正需要它们。所以这个 preset 是「Standard + 岗位技能 + 岗位人设」，不是封闭环境。

## 它带来什么

| | |
|---|---|
| Agent 预设 | `knowledge-work-data`（显示名「数据分析师」，order 20） |
| 岗位技能 | `assets/*/SKILL.md`，通过 preset 作用域的 skill provider 注册 |
| 入口技能 | `data-workflow` —— 先加载它，按路由表选具体技能 |
| 连接器 | 无强制依赖。要直连数仓，自行在 **设置 → MCP** 添加服务器 |

技能名统一加 `data-` 前缀，避免和已装的 `office*` 等技能重名。

### 10 个技能

**工作流技能**（模型可加载 + 出现在 `/` 斜杠菜单）：

| 技能 | 用途 |
|---|---|
| `data-workflow` | 岗位总入口与路由表 + 岗位级硬规则 |
| `data-analyze` | 回答数据问题：单次指标查询 → 完整分析 → 正式报告 |
| `data-explore-data` | 陌生表/文件的数据画像与质量评估 |
| `data-write-query` | 自然语言 → 方言优化的带注释 SQL，存 `.sql` |
| `data-create-viz` | 出图（含图型选择、配色、可读性准则） |
| `data-build-dashboard` | 自包含 HTML + Chart.js 交互仪表盘 |
| `data-validate-data` | 交付前 QA：方法论、聚合口径、偏差、可复现性 |
| `data-context-extractor` | 抽取指标定义与业务术语表，沉淀可复用文档 |

**知识技能**（`user-invocable: false`，只给模型按需加载，不进斜杠菜单 —— 照搬上游语义）：

| 技能 | 内容 |
|---|---|
| `data-sql-queries` | 9 种方言最佳实践（PostgreSQL/Snowflake/BigQuery/Redshift/Databricks/MySQL/SQL Server/DuckDB/SQLite）+ 窗口/CTE/cohort/漏斗/去重模板 |
| `data-statistical-analysis` | 描述统计、显著性检验、回归（纯 numpy/pandas 实现） |

### 附带脚本

`assets/data-create-viz/scripts/chart_pillow.py` —— 纯 Pillow 图表渲染器，7 种图型（line/bar/hbar/stackbar/hist/scatter/heat），填补捆绑 Python 没有 matplotlib 的缺口。中文标题与轴标签已实测正常渲染。


## 与上游的差异

- **中文优先**：上游模板偏英文，这里正文以中文为主，SQL / Python / 术语保留英文。
- **不绑订阅**：模型走 DSH 自己的路由，与 Claude 订阅无关。
- **交付物落地**：图表出 PNG 并用 `present` 交付；报告/表格走 `office` 技能产出 `.docx` / `.xlsx` / `.pptx`；查询另存 `.sql`。
- **工具名换成 DSH 实际能力**：不引用 Claude 专有工具。
- **作用域**：上游靠 marketplace 逐个安装；这里靠 preset 作用域隔离，切换岗位 = 切换模式，不用装卸。

## 许可

技能内容移植自 `anthropics/knowledge-work-plugins`（Apache-2.0），保留来源说明，见 `NOTICE.md`。本 bundle 自身同样按 Apache-2.0 提供。

## 尚未实现

- 上游另外 10 个岗位（市场、销售、法务、财务、产品、客服、设计、工程、HR、运营）。复制本目录结构即可扩展：新 `assets/` 技能 + 新 preset 声明。
- 连接器不会自动授权 —— 与上游一样，MCP 服务器需逐个配置。
