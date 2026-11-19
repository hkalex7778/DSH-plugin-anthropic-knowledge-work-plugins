---
name: data-analyze
description: 回答数据问题，从单次指标查询到完整分析再到正式报告。当需要查一个指标数值、排查趋势上涨/下跌的原因、对比不同分组随时间的变化，或为业务方准备一份正式数据报告（季度复盘、数据质量评估等）时使用本技能。产出：带验证结论的答案/分析/报告，必要时附 PNG 图表。
whenToUse: 用户提出任何数据问题时优先用本技能；单纯给新表/文件做画像改用 data-explore-data；只要一段 SQL 改用 data-write-query。
---

# data-analyze — 回答数据问题

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

回答一个数据问题：快速查询、完整分析，或正式报告。本技能自包含，可独立跑完整个流程；涉及 SQL 规范、统计方法、出图时按第 3/5 步指向兄弟技能，但不依赖它们也能降级完成。

## 第 1 步：理解问题，判定复杂度

先给用户的问题分级，这决定后面走哪条分支：

| 复杂度 | 判定特征 | 例子 | 交付形态 |
|---|---|---|---|
| **Quick answer** | 单一指标、简单过滤、事实查询 | "上周新增多少用户？" | 一句话答案 + 所用查询 |
| **Full analysis** | 多维探索、趋势分析、分组对比、归因 | "转化率下跌是什么驱动的？" | 结论先行 + 表格/图 + 方法说明 + 后续问题 |
| **Formal report** | 需要方法论、caveats、建议的正式材料 | "准备订阅指标的季度业务复盘" | 结构化文档（.docx/.xlsx），含执行摘要与局限性 |

同时确定三件事，缺失任何一项且无法合理推断时，用 `ask_user_question` 一次性问清（不要连环追问）：

- **数据需求**：需要哪些表/字段/指标/维度/时间范围。
- **输出格式**：数字、表格、图、叙述，还是组合。
- **对比基准**：环比/同比/vs 目标值，不明确时默认环比并在结论里注明假设。

## 第 2 步：取数（连接器分支）

**若已配置数仓类 MCP 服务器**（Snowflake、BigQuery、Databricks、Redshift、PostgreSQL、MySQL 等任一 SQL 服务器，可在设置 → MCP 查看）：

1. 先探索 schema：`information_schema.tables` / `information_schema.columns`，找到相关表和列；表名有歧义时列出候选让用户确认。
2. 写 SQL 提取所需数据。方言细节、CTE/窗口函数/性能最佳实践用 `skill` 工具加载 `data-sql-queries`；该技能不可用时按通用 ANSI SQL 写并显式标注方言假设。
3. 执行并取回结果。查询失败时调试重试：先查列名、表引用，再查该方言的语法差异。
4. 结果不符合预期时，先跑第 4 步的 sanity check 再继续，不要直接进分析。

**若没有数仓连接**（默认情况）：

1. 用 `ask_user_question` 请用户按以下任一方式提供数据：
   - 直接粘贴查询结果（TSV/CSV 文本均可解析）；
   - 上传 CSV 或 Excel 文件（用 `read`/`grep` 检查文本文件；Excel 用捆绑 Python + openpyxl 读取，见第 3 步环境准备）；
   - 口述 schema，由你写好 SQL 交用户自行执行后回贴结果——写 SQL 时遵循 `data-sql-queries` 的规范，写好的查询用 `write` 存为 `.sql` 文件交付。
2. 拿到数据前不要开始编造分析；但可以先把分析计划（要算哪些指标、怎么验证）列给用户确认。

## 第 3 步：分析

**环境准备（一次性）**：调用 `load_workspace_dependencies` 取捆绑 Python 路径（返回的是本机绝对路径，形如 `.../.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe`）。可用库**只有**：numpy、pandas、Pillow、openpyxl、XlsxWriter、lxml、python-docx、python-pptx、python-dateutil。**没有** matplotlib、seaborn、scipy、statsmodels、sklearn、duckdb、pyarrow、plotly——上游模板中用到这些库的地方，按本技能替代方案执行。

分析动作清单：

- 计算相关指标、聚合与对比（聚合逻辑写在 pandas 里，脚本经 `pwsh` 调用捆绑 Python 执行；脚本文件用 `write` 落盘，避免超长 `-Command` 内联）。
- 识别模式、趋势、离群值与异常。**离群检测/趋势显著性等统计方法**优先用 `skill` 加载 `data-statistical-analysis`；不可用时降级为 numpy/pandas 手写实现：z-score 用 `(x - x.mean()) / x.std()`，分位数用 `Series.quantile([...])`，两比例差异用正态近似手算，不做 p 值精确检验（无 scipy），并在结论里注明检验方法的近似性质。
- 跨维度对比（时间段、分组、类别）。
- 复杂问题拆成子问题逐个解决；子问题彼此独立且工作量大时，可用 `subagent` 并行处理，结果汇总前统一口径。

## 第 4 步：呈现前验证（强制）

分享任何结果之前，逐项跑一遍：

- **行数 sanity**：记录数与预期量级是否一致？
- **空值检查**：是否存在可能扭曲结果的意外 null？
- **量级检查**：数值落在合理区间？（收入的"总数"不会是负几十亿）
- **时间序列连续性**：是否有意外断档？
- **聚合逻辑**：小计之和是否等于总计？（分组求和后与全表聚合对账）

任何一项可疑：先调查，调查不清就写进 caveats，不许静默放行。

## 第 5 步：按复杂度呈现结果

**Quick answer**：
- 直接给答案 + 必要上下文（时间范围、口径）。
- 附上所用查询或计算脚本路径，保证可复现。

**Full analysis**：
- 关键结论/洞察先行，不要 bury the lead。
- 用数据表和图支撑。
- 说明方法与 caveats。
- 结尾给 2-4 个建议的后续问题。

**Formal report**（结构模板，用 python-docx 生成 `.docx`，或经 `skill` 加载 `office` 技能；表格数据可另出 `.xlsx`）：

```markdown
# [报告标题]

## 执行摘要
- [3-5 条关键要点，每条一句话]

## 方法论
- 数据来源：[表/文件/查询范围]
- 口径定义：[指标怎么算、时间窗、过滤条件]
- 分析步骤：[做了什么]

## 详细发现
### 发现 1：[标题]
[证据：表格/图 + 解读]

## Caveats 与局限
- [数据质量问题、方法近似性、样本限制]

## 建议与下一步
1. [可执行建议]
```

完成后把最终交付物（PNG/docx/xlsx）用 `present` 交付。

## 第 6 步：需要出图时

表格表达不如图直观时（趋势、对比、分布）：

- 优先用 `skill` 工具加载 `data-create-viz` 选图表类型并出图。
- 快速兜底方案（不加载兄弟技能也能出图）：把整理好的数据存成 CSV，用 `pwsh` 调 `chart_pillow.py`（纯 Pillow 实现，中文标签正常，支持 line/bar/hbar/stackbar/hist/scatter/heat）。脚本在插件目录里，**用绝对路径**（相对路径会因 cwd 是用户工作区而找不到文件）：从本技能加载结果那行「Base directory for this skill」出发，脚本就在同级的兄弟技能目录下：

```powershell
$base = "<本技能 Base directory，形如 ...\assets\data-analyze>"
$script = Resolve-Path "$base\..\data-create-viz\scripts\chart_pillow.py"
$py  = "<load_workspace_dependencies 返回的 python.exe 路径>"
& $py $script --kind line --csv trend.csv --x month --y revenue --out trend.png --title "月度收入趋势" --ylabel "收入（万元）"
```

- 出图后用 `read_image` 或直接把 PNG 路径交给 `present` 交付，并在正文里引用该图。

## 常见错误与对策

| 错误 | 对策 |
|---|---|
| 用户只给了指标名没给时间范围，直接开算 | 时间窗是口径的一部分：问，或明确声明所用假设 |
| 没连数仓却假装能查库 | 走第 2 步"无连接"分支，让用户贴数或传文件 |
| 结果有意外 null/断档但没提 | 第 4 步五项验证是强制的，caveat 必须写出来 |
| 分析里用了 matplotlib/scipy | 环境没有这些库：出图用 chart_pillow.py，统计用 numpy/pandas 手写并注明近似 |
| Quick answer 写成了三段报告 | 按第 1 步分级交付，别过度交付 |
| 相关当因果下结论 | 归因表述用"与…同步变化/驱动证据包括…"，并列出备择解释 |
| 把中间 CSV/脚本直接扔给用户 | 只 `present` 最终交付物；中间文件留在工作目录备查 |
