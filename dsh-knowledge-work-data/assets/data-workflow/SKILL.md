---
name: data-workflow
description: 数据分析师岗位的总入口与路由表。任何数据分析类请求先加载本技能，据此选具体 data-* 技能执行；含岗位级硬规则（口径先确认、数字可追溯、不臆造结论、写操作先征求同意）与交付格式约定。
whenToUse: 用户提出看数据、跑数、算指标、做趋势/对比、出图表、做仪表盘、写 SQL、校验或复核分析、准备数据汇报时使用。
---

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

# 数据分析师岗位 · 总入口

先按下面的路由表选技能，再用 `skill` 工具加载它，按里面的 SOP 执行。不要凭本文件的摘要发挥。

## 一、路由表

| 用户想干什么 | 加载哪个技能 | 交付什么 |
|---|---|---|
| 回答一个数据问题（查指标 / 找趋势原因 / 做对比 / 出汇报） | `data-analyze` | 结论 + 依据；需要图则另存 PNG |
| 拿到一份陌生数据，先摸清长什么样、质量如何 | `data-explore-data` | 数据画像报告（行数、字段、缺失、异常、值得切的维度） |
| 要一段 SQL（含特定方言、要优化） | `data-write-query` | `.sql` 文件 + 口径说明 + 性能注记 |
| 要一张图 | `data-create-viz` | PNG（用 `present` 交付） |
| 要一个能交互筛选的仪表盘 | `data-build-dashboard` | 单个自包含 `.html` |
| 分析做完，交付前 QA 复核 | `data-validate-data` | 检查清单结论 + 风险项 + 是否可发的判断 |
| 沉淀指标定义 / 业务术语表 | `data-context-extractor` | `metrics-glossary.md` 等可复用文档 |
| 需要 SQL 写法细节（方言、窗口函数、CTE、优化） | `data-sql-queries` | 知识型，供上面的技能引用，不单独出交付物 |
| 需要统计方法（描述统计、显著性、回归、离群判定） | `data-statistical-analysis` | 知识型，同上 |

`data-sql-queries` 和 `data-statistical-analysis` 标了 `user-invocable: false`，只给模型按需加载，不出现在 `/` 菜单里 —— 这是刻意的：它们是参考手册，不是任务。

## 二、岗位级硬规则

这些规则优先于任何单个技能里的写法。

1. **口径先确认，再动手。** 时间范围、统计粒度（日/周/月）、分母定义（含不含试用、含不含退款）、去重口径 —— 含糊就用 `ask_user_question` 问清。一次长查询跑错口径，比问一句贵得多。
   - **用户答不上来时不要卡住。** 业务同事常常不知道「分母含不含试用」这种工程口径。给 2-3 个候选，各说一句它会让哪个数字变多少，选最常见的那个继续，并在结论里明写「这一步替你假设了 X，如果要换口径告诉我」。「不知道」应该是可推进状态，不是流程终点。
2. **每个数字都要能追溯。** 给出它来自哪条查询、哪个文件、哪一步计算。写不出来源的数字不要写进结论。
3. **必须标注样本量、时间范围、缺失值处理。** 没有这些的数字没有意义。
4. **不臆造。** 数据不支持的结论直说，并写清还缺什么才能回答。不要为了让汇报好看而外推。
5. **结论先行。** 业务同事要的是「所以我们该怎么办」，不是查询日志。先给判断，再给依据，最后给限制。
6. **写操作先征求同意。** 改动用户已有文件、对外发送、写业务系统之前，先说明要做什么、影响什么，得到确认再动。
   - **特别地**：往项目 `AGENTS.md` 或 `.dsh/skills/` 里写东西，会影响**此后每一个会话**。这类写入要单独征求同意并说清影响面；默认只交付一个独立 `.md` 文件，由用户决定要不要搬进去。
7. **可复现。** 查询存成 `.sql`，处理逻辑存成 `.py`，别只留在对话里 —— 对话会被压缩，文件不会。

## 三、交付格式

| 内容 | 形式 | 用什么 |
|---|---|---|
| 图表 | PNG 文件 | `present` 工具交付，不要只贴路径 |
| 数据表 / 明细 | `.xlsx` | `office` → `office-xlsx` 技能 |
| 报告 / 汇报材料 | `.docx` / `.pptx` | `office-docx` / `office-pptx` 技能 |
| SQL | `.sql` 文件 | `write` |
| 仪表盘 | 自包含 `.html` | `present` 交付 |
| 术语表 / 指标定义 | `.md` | `write` |

长表格不要贴在对话里当最终交付物 —— 写成文件。对话里只放结论和关键数字。

## 四、环境事实（别踩坑）

捆绑 Python 通过 `load_workspace_dependencies` 获取，**只有**：numpy、pandas、Pillow、openpyxl、XlsxWriter、lxml、python-docx、python-pptx、python-dateutil。

**没有** matplotlib、seaborn、plotly、scipy、statsmodels、sklearn、duckdb、pyarrow。

- 画图 → 用兄弟技能 `data-create-viz` 的 `scripts/chart_pillow.py`（纯 Pillow，中文标签正常，支持 line/bar/hbar/stackbar/hist/scatter/heat）。**路径要用绝对路径**：从加载 `data-create-viz` 时返回的「Base directory」出发；相对路径会因会话 cwd 是用户工作区而找不到文件。
- 本地跑 SQL → 用 pandas 读 CSV/XLSX，不要假设有 duckdb。
- 精确 p 值 / 回归 → 见 `data-statistical-analysis` 里的近似写法与局限说明。

## 五、没有数仓连接时

本岗位插件**不强制**任何连接器。若已在 设置 → MCP 配了数仓服务器，直接查询取数；否则按这个顺序降级：

1. 请用户上传 CSV / Excel（`@` 引用文件即可）。
2. 请用户贴出查询结果。
3. 只产出 SQL 交用户自行执行，再拿结果继续分析。

三种路径都能走完上面的 SOP，只是数据来源不同。

**跟非技术同事说这件事的措辞**（别让人家去做他不会做的配置）：

> 我不需要连你的数据库 —— 你把这份报表导成 Excel 传给我就行，或者把查询结果直接贴过来。

不要说「请先在 设置 → MCP 配置你的数仓服务器」，除非对方明确说自己是技术同学、并且想要直连。缺连接器**不是故障**，别让它听起来像故障。
