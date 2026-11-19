---
name: data-explore-data
description: 对一张表或一个上传文件做数据画像与探索，摸清它的形状、质量与模式。当接触一张陌生的表或文件、检查空值率与列分布、排查重复值或可疑值等数据质量问题，或决定该分析哪些维度和指标时使用本技能。产出：结构化数据画像报告（列分类、质量告警、推荐切片与后续分析）。
whenToUse: 在写具体分析查询之前先跑本技能摸清数据底细；已有明确指标问题改用 data-analyze。
---

# data-explore-data — 数据画像与探索

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

为一张表或一个上传文件生成完整的数据画像：先搞清形状、质量与模式，再进入具体分析。本技能自包含，用 DSH 捆绑的 numpy/pandas 即可跑完全部画像检查；需要出图或深入统计时按第 6/7 步指向兄弟技能。

## 第 1 步：拿到数据（三分支）

**若已配置数仓类 MCP 服务器**（Snowflake / BigQuery / Databricks / Redshift / PostgreSQL / MySQL 等，可在设置 → MCP 查看）：

1. 解析表名：处理 schema 前缀，名字有歧义时列出候选让用户选。
2. 查元数据：列名、类型、注释（如可得）。PostgreSQL 系可直接查 `information_schema.columns`，表清单查 `information_schema.tables`。
3. 对活数据跑画像查询：优先把聚合留在库内做（COUNT / COUNT(DISTINCT) / PERCENTILE / GROUP BY），别把百万行明细拉回本地。
4. 大表（1 亿行以上）画像默认用采样（如 `TABLESAMPLE` 或按分区/时间切片），并在报告里显式说明"以下是采样结果，需要精确值请指定"。

**若用户提供文件（CSV / Excel / JSON）**：

1. CSV/TSV/JSON 用 `read` 与 `grep` 先看头几十行，确认分隔符、编码、表头是否齐整；Excel 交给捆绑 Python + openpyxl。
2. 用捆绑 Python 载入 DataFrame，从数据本身推断列类型（不要盲信声明类型）。
3. 载入即记录：总行数、总列数、是否有全空尾列、表头是否被当成数据。

**两者都没有**：

1. 用 `ask_user_question` 请用户提供表名（并在其数仓已连接时操作）或上传文件。
2. 若用户只口述了 schema，就给出该跑哪些画像查询的清单（照第 3 步各项写成 SQL 模板），让用户执行后把结果贴回来，你照样能产出画像。

## 第 2 步：理解结构

分析任何数据之前先回答这些**表级问题**：

- 多少行、多少列？
- **粒度（grain）**：一行代表什么？（写成一句 "one row per …"，写不出来就是后续所有分析的隐患）
- 主键是哪列？是否真的唯一（`df.duplicated(subset=[key]).sum()`）？
- 数据最后更新时间？
- 数据能回溯到多久以前？

**列分类**——把每一列归入一类，后续所有检查按类别走：

| 类别 | 特征 | 例子 |
|---|---|---|
| Identifier | 主键、外键、实体 ID | `user_id`, `order_id` |
| Dimension | 用于分组/过滤的分类属性 | `status`, `region`, `category` |
| Metric | 可度量的数值 | `revenue`, `duration`, `score` |
| Temporal | 日期与时间戳 | `created_at`, `event_date` |
| Text | 自由文本 | `description`, `notes` |
| Boolean | 真/假标记 | `is_churned` |
| Structural | JSON、数组、嵌套结构 | `properties` |

分类结果直接写进画像报告的 Overview。

## 第 3 步：生成数据画像（清单）

**环境准备**：调用 `load_workspace_dependencies` 取捆绑 Python 路径（返回的是本机绝对路径，形如 `.../.dsh/dsh-runtimes/dsh-primary-runtime/dependencies/python/python.exe`）。可用库**只有**：numpy、pandas、Pillow、openpyxl、XlsxWriter、lxml、python-docx、python-pptx、python-dateutil。**没有** scipy / statsmodels / sklearn / duckdb / pyarrow / plotly / matplotlib——以下全部画像指标用 pandas/numpy 手写即可（`Series.describe()`、`quantile()`、`value_counts()`、`corr()`），无需额外依赖。

**表级指标**：总行数；列数与类型分布；表大小（数仓元数据可得时）；日期列覆盖范围（min/max）。

**所有列**：
- 空值数与空值率
- 去重值数与 **cardinality ratio**（`nunique / len`）
- 最高频值 top 5-10 及其频次
- 最低频值 bottom 5（用来揪异常值）

**数值列（Metric）**：
```
min, max, mean, median (p50)
standard deviation
percentiles: p1, p5, p25, p75, p95, p99
zero count
negative count（若不该出现负值）
```

**字符串列（Dimension / Text）**：
```
min length, max length, avg length
空字符串计数
模式分析（值是否遵循某种格式？用 str.match / str.contains 正则统计）
大小写一致性（全大写 / 全小写 / 混合）
首尾空白计数
```

**日期/时间列**：
```
min date, max date
空日期数
未来日期数（若不该出现）
按月/按周的分布
时间序列断档（按预期频率重采样后找空桶）
```

**布尔列**：true 数、false 数、null 数、true rate。

**画像呈现为整洁的汇总表，按列类型分组**（Dimension / Metric / Temporal / Identifier），每行给：列名、类型、空值率、去重数，以及该类别最关键的一两个指标。

## 第 4 步：识别数据质量问题（带阈值）

逐项套用文末「质量评估框架」的判定标准，命中即按严重度告警：

- **高空值率**：>5% 空值 → warn；>20% 空值 → alert。
- **低 cardinality 意外**：本该高基数却不高（如只有 50 个去重值的 `user_id`）。
- **高 cardinality 意外**：本该是分类维度却去重值过多（如 status 有 10 万个值 → 大概率被误用）。
- **可疑值**：本该只正的地方出现负金额、历史数据里出现未来日期、明显占位值（`N/A`、`TBD`、`test`、`999999`、空串、`xxx`）。
- **重复检测**：找出自然键，检查它是否真有重复；有则报重复率与示例行。
- **分布偏斜**：极端右偏/左偏的数值分布会拉偏均值——报 mean 与 median 的比。
- **编码/一致性问题**：分类字段大小写混用、首尾空白、同一概念多种写法。

## 第 5 步：发现关系与模式

单列画像完成后，看列与列之间：

- **外键候选**：可能连到其他表的 ID 列（命名 `*_id`、与主键同格式）。
- **层级**：天然的下钻路径（country > state > city）。
- **相关性**：一起变动的数值列——`df[metrics].corr()` 直接算，无需 scipy；标记 |r| > 0.7 供深查，并显式注明"相关不等于因果"。
- **派生列**：看起来由其他列算出来的列（如 `total = price * qty`，抽样验证一下）。
- **冗余列**：信息相同或近似的列（去重率一致、与另一列相关性接近 1）。

**分布形态判定**（数值列逐个归类）：
- Normal：mean ≈ median，单峰
- Skewed right：高值长尾（收入、会话时长常见）
- Skewed left：低值长尾（较少见）
- Bimodal：双峰（提示两个不同总体）
- Power law：极少数极大值 + 大量小值（用户活跃度常见）
- Uniform：全区间频次接近（多为合成或随机数据）

**时间模式**（有时间序列时看）：trend（持续升降）、seasonality（周/月/季/年周期）、day-of-week 效应（工作日 vs 周末）、holiday 效应、change point（水平或趋势突变）、anomalies（破格单点）。

**分群发现**：找 3-20 个去重值的分类列 → 比较各取值上的指标分布 → 找行为显著不同的分群 → 再测分群内部是否还含子群。

## 第 6 步：推荐维度与指标

基于画像明确推荐：

- **最适合切片的 Dimension 列**：基数落在 3-50 的分类列。
- **核心 Metric 列**：分布有实际含义的数值列。
- **适合做趋势分析的 Temporal 列**。
- **数据中自然存在的分组/层级**。
- **潜在 join key**：ID 列、外键候选。

## 第 7 步：推荐 3-5 个后续分析

给具体、可直接执行的建议，套用模板：

1. "对 [metric] 按 [time_column] 做趋势分析，按 [dimension] 分组"
2. "对 [偏斜列] 做分布深挖，搞清离群值"
3. "对 [问题列] 做数据质量排查"
4. "[metric_a] 与 [metric_b] 的相关性分析"
5. "用 [date_column] 与 [status_column] 做 cohort 分析"

需要出图（直方图看分布、热力图看相关矩阵、柱图看分类频次）时：优先用 `skill` 工具加载 `data-create-viz` 选图表类型；兜底可直接用 `pwsh` 跑同插件自带的 `chart_pillow.py`（纯 Pillow 实现，中文标签正常，支持 line/bar/hbar/stackbar/hist/scatter/heat）。**用绝对路径**，相对路径会因 cwd 是用户工作区而找不到文件：

```powershell
$base = "<本技能 Base directory，形如 ...\assets\data-explore-data>"
$script = Resolve-Path "$base\..\data-create-viz\scripts\chart_pillow.py"
$py  = "<load_workspace_dependencies 返回的 python.exe 路径>"
# hist 只按 --y 分箱，不需要 --x
& $py $script --kind hist --csv orders.csv --y revenue --out rev_hist.png --title "revenue 分布" --bins 40
```

相关矩阵出图：`heat` 要**长表**（宽表只会画出对角线）。把 `df[metrics].corr()` 先 melt 成长表再渲染：

```python
corr = df[metrics].corr()
long = (corr.rename_axis(index="row", columns=None)
            .reset_index()
            .melt(id_vars="row", var_name="col", value_name="r"))
long.to_csv("corr_long.csv", index=False)   # 列：row, col, r
```

```powershell
& $py $script --kind heat --csv corr_long.csv --x col --y r,row --out corr_heat.png --title "指标相关矩阵"
```

图用 `present` 交付。

## 输出格式模板

```markdown
## Data Profile: [table_name]

### Overview
- Rows: 2,340,891
- Columns: 23（8 dimension, 6 metric, 4 temporal, 5 ID）
- Grain: one row per [订单 / 用户-事件 / …]
- Primary key: [列名] — unique: [yes/no, 重复率 x%]
- Date range: 2021-03-15 to 2024-01-22
- Source: [MCP 数仓 / 文件名 / 用户粘贴]  |  [是否采样]

### Column Details
| Column | Class | Type | Null % | Distinct | 关键指标 |
|---|---|---|---|---|---|
| revenue | Metric | float64 | 1.2% | 88,412 | median 24.9, p99 1,830, skew right |
| status | Dimension | object | 0.0% | 6 | top: "active" 62%, "UNKNOWN" 340 行 |

### Data Quality Issues
| 严重度 | 列 | 问题 | 证据 | 建议 |
|---|---|---|---|---|
| alert | email | 18% 空值 | 421,300 null | 追上游采集 |
| warn | country | 大小写混用 | "US"/"us"/"USA" | 归一化映射 |

### Relationships & Patterns
- Join keys: user_id → users, product_id → products
- Correlations: revenue ~ qty (r=0.83)；相关不等于因果
- Distribution: duration 右偏，mean/median = 3.1

### Recommended Explorations
1. [趋势分析建议]
2. [分布深挖建议]
3. [质量排查建议]
```

## 质量评估框架（判定标准）

**Completeness（逐列评级）**：
- **Complete**（>99% 非空）：Green
- **Mostly complete**（95-99%）：Yellow — 去查这些 null 从哪来
- **Incomplete**（80-95%）：Orange — 搞清为什么缺、是否影响使用
- **Sparse**（<80%）：Red — 不做插补基本不可用

**Consistency**：
- 值格式不一致：同一概念多种写法（"USA" / "US" / "United States" / "us"）
- 类型不一致：数字存成字符串、日期多种格式混存
- 引用完整性：外键找不到父记录
- 业务规则违反：数量为负、结束日期早于开始日期、百分比 > 100
- 跨列一致性：status = "completed" 但 completed_at 为 null

**Accuracy 红旗**：
- 占位值：0、-1、999999、"N/A"、"TBD"、"test"、"xxx"
- 默认值：单一值出现频率可疑地高
- 数据陈旧：活跃系统里 updated_at 长期无变化
- 不可能值：年龄 > 150、远期未来日期、负时长
- 整数偏好：所有值都以 0 或 5 结尾（像是估算而非实测）

**Timeliness**：表最后更新时间？预期更新频率？事件时间与装载时间之间的 lag？时间序列是否有断档？

## Schema 文档模板（画像顺手产出，交付团队复用）

```markdown
## Table: [schema.table_name]

**Description**: [这张表代表什么]
**Grain**: one row per [ … ]
**Primary Key**: [列（可复合）]
**Row Count**: [近似值 + 统计日期]
**Update Frequency**: [real-time / hourly / daily / weekly]
**Owner**: [负责团队或个人]

### Key Columns
| Column | Type | Description | Example Values | Notes |
|--------|------|-------------|----------------|-------|
| user_id | STRING | 用户唯一标识 | "usr_abc123" | FK to users.id |
| event_type | STRING | 事件类型 | "click", "view", "purchase" | 15 个去重值 |
| revenue | DECIMAL | 交易收入 (USD) | 29.99, 149.00 | 非购买事件为 null |
| created_at | TIMESTAMP | 事件发生时间 | 2024-01-15 14:23:01 | 该列做分区 |

### Relationships
- 通过 `user_id` join `users`
- 通过 `product_id` join `products`

### Known Issues
- [已知数据质量问题]
- [分析师需要注意的坑]

### Common Query Patterns
- [这张表的典型用法]
```

数仓连接下补充 schema 探索，可用 PostgreSQL 模式（其他方言按 `data-sql-queries` 换写法）：

```sql
-- 列出 schema 下所有表
SELECT table_name, table_type FROM information_schema.tables
WHERE table_schema = 'public' ORDER BY table_name;

-- 列明细
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'my_table' ORDER BY ordinal_position;

-- 表大小（PostgreSQL）
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

**血缘与依赖**（探索陌生数据环境时）：从报表/dashboard 消费的"输出表"入手 → 追上游：什么表喂给它 → 识别 raw/staging/mart 分层 → 画出从原始数据到分析表的转换链 → 记录数据在哪些环节被富化、过滤或聚合。

## 常见错误与对策

| 错误 | 对策 |
|---|---|
| 没定 grain 就开始算指标 | 第 2 步的 "one row per …" 必须写成一句话，写不出就先问用户 |
| 把百万行明细全拉到本地 | 数仓侧先聚合/采样；本地只处理结果集 |
| 采样画像却当精确值汇报 | 报告 Overview 里显式标注采样与否 |
| 只报"有 null"不报严重度 | 一律套用 >5% warn / >20% alert 阈值与 Green/Yellow/Orange/Red 评级 |
| 见 `nunique` 高就判定是 ID 列 | 结合基数比（distinct/total）与取值格式一起判 |
| 见到高相关就下因果结论 | 画像报告只报 r 值并标注"相关不等于因果" |
| 质量告警全当真理 | 告警是启发式，逐条快速看一眼即可；确认无关的降级为"已核查，非问题" |
| 调 matplotlib/scipy 出图或做检验 | 捆绑环境没有：出图走 chart_pillow.py，检验用 numpy/pandas 手写并注明近似 |
