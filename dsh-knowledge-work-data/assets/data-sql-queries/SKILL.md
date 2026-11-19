---
name: data-sql-queries
description: SQL 方言知识库，收录 Snowflake、BigQuery、Databricks、Redshift、PostgreSQL、MySQL、SQL Server、DuckDB、SQLite 的日期/字符串/半结构化函数写法、各自性能优化手法，以及窗口函数、CTE、同期群留存、漏斗、去重等常用分析模板与报错排查清单。用于按需查阅：写查询要确认某方言的具体语法、优化慢 SQL、在方言之间互转、或搭复杂的 CTE/窗口函数/聚合分析。供 data-write-query 等工作流技能加载，不由用户直接调用。
user-invocable: false
---

# data-sql-queries — SQL 方言知识库

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

正确、高效、可读的 SQL，覆盖主流数仓与 OLTP 方言。这是**查阅型知识技能**：写查询前对照本文件的方言小节取正确语法，不要凭记忆猜函数名。工作流（问清口径 → 产出带注释 SQL → 存 `.sql` 交付）见 `data-write-query`。

## 连接器前提

DSH 不预置数仓连接。若用户已在 **设置 → MCP** 配置了对应数仓服务器，可直接执行查询、读回 schema 与结果并迭代；否则产出可复制运行的 SQL 交给用户自行执行，或让用户贴回结果 / 上传 CSV·Excel，再用捆绑 Python 分析。

**环境事实（实测）**：DSH 捆绑 Python 只有 `numpy` / `pandas` / `Pillow` / `openpyxl` / `XlsxWriter` / `lxml` / `python-docx` / `python-pptx`；**没有** `duckdb`、`pyarrow`、`matplotlib`、`scipy`、`statsmodels`、`sklearn`。所以：

- 别指望在本地用 duckdb 跑 SQL。要在本地验逻辑，用 pandas 读 CSV/XLSX 做等价计算，或明确告知用户需自备 duckdb / 本地库环境。
- 本地 CSV 分析可用 pandas 的 `read_csv` / `read_excel`（引擎 openpyxl）、`groupby`、`merge`、`pivot_table`。

---

## 方言参考

### PostgreSQL（含 Aurora PostgreSQL、RDS、Supabase、Neon）

**日期/时间**

```sql
-- 当前日期/时间
CURRENT_DATE, CURRENT_TIMESTAMP, NOW()

-- 日期运算
date_column + INTERVAL '7 days'
date_column - INTERVAL '1 month'

-- 截断到周期
DATE_TRUNC('month', created_at)

-- 提取字段
EXTRACT(YEAR FROM created_at)
EXTRACT(DOW FROM created_at)  -- 0 = Sunday

-- 格式化
TO_CHAR(created_at, 'YYYY-MM-DD')
```

**字符串函数**

```sql
-- 拼接
first_name || ' ' || last_name
CONCAT(first_name, ' ', last_name)

-- 模式匹配
column ILIKE '%pattern%'      -- 不区分大小写
column ~ '^regex_pattern$'    -- 正则

-- 字符串处理
LEFT(str, n), RIGHT(str, n)
SPLIT_PART(str, delimiter, position)
REGEXP_REPLACE(str, pattern, replacement)
```

**数组与 JSON**

```sql
-- JSON 访问
data->>'key'                  -- 取 text
data->'nested'->'key'         -- 取 json
data#>>'{path,to,key}'        -- 深层路径取 text

-- 数组操作
ARRAY_AGG(column)
ANY(array_column)
array_column @> ARRAY['value']
```

**性能要点**

- 用 `EXPLAIN ANALYZE` 剖析查询（看实际行数与估算行数的偏离）
- 在高频过滤/JOIN 的列上建索引
- 相关子查询用 `EXISTS` 代替 `IN`
- 对常见过滤条件用 partial index（`WHERE` 带条件的索引）
- 表达式索引可让 `WHERE DATE_TRUNC('day', created_at) = ...` 这类写法命中索引；把函数挪到常量一侧通常更省
- 并发访问用连接池
- 加索引/改 schema 属于写操作，先征得用户同意

---

### Snowflake

**日期/时间**

```sql
-- 当前日期/时间
CURRENT_DATE(), CURRENT_TIMESTAMP(), SYSDATE()

-- 日期运算
DATEADD(day, 7, date_column)
DATEDIFF(day, start_date, end_date)

-- 截断到周期
DATE_TRUNC('month', created_at)

-- 提取字段
YEAR(created_at), MONTH(created_at), DAY(created_at)
DAYOFWEEK(created_at)

-- 格式化
TO_CHAR(created_at, 'YYYY-MM-DD')
```

**字符串与半结构化**

```sql
-- 大小写不敏感取决于 collation
column ILIKE '%pattern%'
REGEXP_LIKE(column, 'pattern')

-- 解析 JSON
column:key::string            -- VARIANT 的点式访问
PARSE_JSON('{"key": "value"}')
GET_PATH(variant_col, 'path.to.key')

-- 展开数组/对象
SELECT f.value FROM table, LATERAL FLATTEN(input => array_col) f
```

**半结构化数据（VARIANT）**

```sql
-- 类型化访问
data:customer:name::STRING
data:items[0]:price::NUMBER

-- 展开嵌套结构
SELECT
  t.id,
  item.value:name::STRING AS item_name,
  item.value:qty::NUMBER AS quantity
FROM my_table t,
LATERAL FLATTEN(input => t.data:items) item
```

**性能要点**

- 大表用 clustering key（不是传统索引）；`CLUSTER BY` 列要与高频过滤列对齐才能裁剪微分区
- 在 clustering key 列上过滤才有 partition pruning 效果
- 按查询复杂度选 warehouse size（扫全表与取几行不该用同一个 warehouse）
- 用 `RESULT_SCAN(LAST_QUERY_ID())` 复用上一条昂贵查询的结果，避免重跑
- staging / 临时数据用 transient table（免 time travel 存储费）
- `SEARCH OPTIMIZATION` 可加速非 clustering 列的点查

---

### BigQuery（Google Cloud）

**日期/时间**

```sql
-- 当前日期/时间
CURRENT_DATE(), CURRENT_TIMESTAMP()

-- 日期运算
DATE_ADD(date_column, INTERVAL 7 DAY)
DATE_SUB(date_column, INTERVAL 1 MONTH)
DATE_DIFF(end_date, start_date, DAY)
TIMESTAMP_DIFF(end_ts, start_ts, HOUR)

-- 截断到周期（注意参数顺序与 PG 相反：列在前，单位在后）
DATE_TRUNC(created_at, MONTH)
TIMESTAMP_TRUNC(created_at, HOUR)

-- 提取字段
EXTRACT(YEAR FROM created_at)
EXTRACT(DAYOFWEEK FROM created_at)  -- 1 = Sunday

-- 格式化
FORMAT_DATE('%Y-%m-%d', date_column)
FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', ts_column)
```

**字符串函数**

```sql
-- 没有 ILIKE，用 LOWER()
LOWER(column) LIKE '%pattern%'
REGEXP_CONTAINS(column, r'pattern')
REGEXP_EXTRACT(column, r'pattern')

-- 字符串处理
SPLIT(str, delimiter)          -- 返回 ARRAY
ARRAY_TO_STRING(array, delimiter)
```

**数组与 STRUCT**

```sql
-- 数组操作
ARRAY_AGG(column)
UNNEST(array_column)
ARRAY_LENGTH(array_column)
value IN UNNEST(array_column)

-- STRUCT 访问
struct_column.field_name
```

**性能要点**

- **一定要在分区列（通常是日期）上过滤**，否则按扫描量计费会爆炸
- 分区内再用 clustering 加速高频过滤列
- 大规模基数估计用 `APPROX_COUNT_DISTINCT()`
- 避免 `SELECT *`：按字节扫描计费
- 脚本化参数用 `DECLARE` / `SET`
- 大查询先用 dry run 预估扫描字节再执行
- 无 `ILIKE`、无 `LIMIT n OFFSET m`（用 `LIMIT m OFFSET n`）；`SAFE_DIVIDE` / `SAFE_CAST` 是 BigQuery 特色，用来避免整列报错

---

### Redshift（Amazon）

**日期/时间**

```sql
-- 当前日期/时间
CURRENT_DATE, GETDATE(), SYSDATE

-- 日期运算
DATEADD(day, 7, date_column)
DATEDIFF(day, start_date, end_date)

-- 截断到周期
DATE_TRUNC('month', created_at)

-- 提取字段
EXTRACT(YEAR FROM created_at)
DATE_PART('dow', created_at)
```

**字符串函数**

```sql
-- 大小写不敏感
column ILIKE '%pattern%'
REGEXP_INSTR(column, 'pattern') > 0

-- 字符串处理
SPLIT_PART(str, delimiter, position)
LISTAGG(column, ', ') WITHIN GROUP (ORDER BY column)
```

**性能要点**

- 设计 DISTKEY 让常 JOIN 的表落在同一节点（colocated join），避免跨节点重分布
- 高频过滤/排序列设为 SORTKEY
- 用 `EXPLAIN` 看执行计划
- 关注 `DS_BCAST` / `DS_DIST` 算子——它们意味着跨节点数据搬迁，通常能通过改 DISTKEY 消掉
- 定期跑 `ANALYZE` 与 `VACUUM`（删除/更新多时尤其）
- 需要 schema 灵活性时用 late-binding view

---

### Databricks SQL

**日期/时间**

```sql
-- 当前日期/时间
CURRENT_DATE(), CURRENT_TIMESTAMP()

-- 日期运算
DATE_ADD(date_column, 7)
DATEDIFF(end_date, start_date)
ADD_MONTHS(date_column, 1)

-- 截断到周期
DATE_TRUNC('MONTH', created_at)
TRUNC(date_column, 'MM')

-- 提取字段
YEAR(created_at), MONTH(created_at)
DAYOFWEEK(created_at)
```

**Delta Lake 特性**

```sql
-- Time travel
SELECT * FROM my_table TIMESTAMP AS OF '2024-01-15'
SELECT * FROM my_table VERSION AS OF 42

-- 查看历史
DESCRIBE HISTORY my_table

-- Merge（upsert）
MERGE INTO target USING source ON target.id = source.id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

**性能要点**

- 用 Delta Lake 的 `OPTIMIZE` 与 `ZORDER` 提升查询性能
- 计算密集型查询走 Photon 引擎
- 高频访问的数据集用 `CACHE TABLE`
- 按低基数日期列分区（分区过细反而拖慢）
- 注意 Spark 系语法里 `RLIKE` 代替正则、`to_date` / `from_unixtime` 等函数风格

---

### MySQL

**日期/时间**

```sql
-- 当前日期/时间
CURDATE(), NOW(), SYSDATE()

-- 日期运算
DATE_ADD(created_at, INTERVAL 7 DAY)
DATE_SUB(created_at, INTERVAL 1 MONTH)
DATEDIFF(end_date, start_date)          -- 只给天数
TIMESTAMPDIFF(MONTH, start_ts, end_ts)  -- 指定单位

-- 截断到周期（无 DATE_TRUNC，手工构造）
DATE_FORMAT(created_at, '%Y-%m-01')     -- 月初
LAST_DAY(created_at)                    -- 月末
```

**字符串与 JSON**

```sql
-- 标识符用反引号；字符串可单引号
CONCAT(a, b, c)                           -- 注意 CONCAT_WS(sep, ...) 更实用
col LIKE '%pattern%'                      -- collation 常为不区分大小写

-- JSON
JSON_EXTRACT(data, '$.key')
data->>'$.key'                            -- 取 unquoted text
data->'$.nested.key'
JSON_UNQUOTE(JSON_EXTRACT(data, '$.key'))
```

**性能要点**

- `EXPLAIN FORMAT=JSON` / `EXPLAIN ANALYZE`（8.0.18+）看计划
- 覆盖索引（index-only scan）能省掉回表
- 窗口函数、CTE、JSON 都要求 **8.0+**；5.7 需要改写成变量/自连接
- 无 `FULL OUTER JOIN`：用 `LEFT JOIN ... UNION ... RIGHT JOIN` 手工拼
- 深分页 `LIMIT 1000000, 20` 很慢：改用游标式条件 `WHERE id > last_seen_id LIMIT 20`
- `utf8mb4` 字符集与 `COLLATE` 影响大小写与索引使用

---

### SQL Server（Microsoft）

**日期/时间**

```sql
-- 当前日期/时间
GETDATE(), SYSDATETIME(), SYSUTCDATETIME()

-- 日期运算
DATEADD(day, 7, created_at)
DATEDIFF(day, start_date, end_date)     -- 边界跨越次数，不是精确时长
EOMONTH(created_at)                      -- 月末

-- 截断到周期（旧写法）
DATEADD(month, DATEDIFF(month, 0, created_at), 0)
-- 2022+ 直接
DATE_TRUNC(month, created_at)

-- 提取字段
YEAR(created_at), MONTH(created_at), DAY(created_at)
DATEPART(weekday, created_at)            -- 受 DATEFIRST 设置影响

-- 格式化
CONVERT(varchar(10), created_at, 23)     -- 样式码 23 = yyyy-mm-dd
FORMAT(created_at, 'yyyy-MM-dd')         -- 可读但慢，别在大结果上用
```

**字符串与 JSON**

```sql
-- 标识符用 [brackets] 或双引号
+ -- 或 CONCAT(a, b)
ISNULL(x, y)                             -- 或标准 COALESCE(x, y)
LOWER(col) LIKE '%pattern%'              -- 无原生 ILIKE（大小写通常由 collation 决定）

-- JSON
JSON_VALUE(data, '$.key')
JSON_QUERY(data, '$.items')
OPENJSON(data) WITH (id INT '$.id', name NVARCHAR(100) '$.name')
```

**性能要点**

- 分页用 `OFFSET n ROWS FETCH NEXT m ROWS ONLY`（必须带 `ORDER BY`），或旧式 `TOP n`
- `SET STATISTICS IO ON` / 实际执行计划看逻辑读
- 索引视图与索引化统计；临时表用 `#temp`，避免在 OLTP 大表上跑长查询
- `DATEDIFF` 按边界计数：跨零点即算 1 天，算精确时长要用 `DATEDIFF(second, ...)` 或 `DATETIME2` 相减

---

### DuckDB

```sql
-- 直接查文件（需用户自备 duckdb 环境；DSH 捆绑 Python 未包含 duckdb）
SELECT * FROM 'data/*.parquet';
SELECT * FROM read_csv_auto('orders.csv');
SELECT * FROM sqlite_scan('app.db', 'users');

-- 友好语法：列名可用位置/正则选择，GROUP BY ALL 省略未聚合列
SELECT country, COUNT(*) FROM events GROUP BY ALL;

-- QUALIFY 直接过滤窗口结果（省去外层 CTE）
SELECT * FROM src QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY updated_at DESC) = 1;
```

用途：本地快速验证 SQL 逻辑与 CSV 分析。DSH 环境**没有** duckdb，需要用户自行安装；否则改用 pandas 复算。

---

### SQLite

- 弱类型：列类型只是亲和性（affinity），比较前显式 `CAST`
- 日期靠函数族：`date()`, `datetime()`, `strftime('%Y-%m', ts)`；无原生 `DATE_TRUNC`
- JSON1 扩展：`json_extract(data, '$.key')`
- 窗口函数与 CTE 需 3.25+ / 3.8.3+
- 写并发弱（单写者），大分析别放 SQLite 上跑

---

## 常用 SQL 模式

### 窗口函数

```sql
-- 排名
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)
RANK() OVER (PARTITION BY category ORDER BY revenue DESC)
DENSE_RANK() OVER (ORDER BY score DESC)

-- 累计 / 移动平均
SUM(revenue) OVER (ORDER BY date_col ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
AVG(revenue) OVER (ORDER BY date_col ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS moving_avg_7d

-- Lag / Lead
LAG(value, 1) OVER (PARTITION BY entity ORDER BY date_col) AS prev_value
LEAD(value, 1) OVER (PARTITION BY entity ORDER BY date_col) AS next_value

-- First / Last value（默认 frame 只到当前行，取整分区必须显式写 frame）
FIRST_VALUE(status) OVER (PARTITION BY user_id ORDER BY created_at ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
LAST_VALUE(status) OVER (PARTITION BY user_id ORDER BY created_at ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)

-- 占比
revenue / SUM(revenue) OVER () AS pct_of_total
revenue / SUM(revenue) OVER (PARTITION BY category) AS pct_of_category
```

### CTE 组织可读性

```sql
WITH
-- 第 1 步：定义基础人群
base_users AS (
  SELECT user_id, created_at, plan_type
  FROM users
  WHERE created_at >= DATE '2024-01-01'
    AND status = 'active'
),

-- 第 2 步：算用户级指标
user_metrics AS (
  SELECT
    u.user_id,
    u.plan_type,
    COUNT(DISTINCT e.session_id) AS session_count,
    SUM(e.revenue) AS total_revenue
  FROM base_users u
  LEFT JOIN events e ON u.user_id = e.user_id
  GROUP BY u.user_id, u.plan_type
),

-- 第 3 步：汇总到报表层
summary AS (
  SELECT
    plan_type,
    COUNT(*) AS user_count,
    AVG(session_count) AS avg_sessions,
    SUM(total_revenue) AS total_revenue
  FROM user_metrics
  GROUP BY plan_type
)

SELECT user_count, avg_sessions, total_revenue, plan_type
FROM summary
ORDER BY total_revenue DESC;
```

> 注：最外层这里刻意不用 `SELECT *`，逐列写出便于下游消费与视图依赖管理。

### 同期群留存（cohort retention）

```sql
WITH cohorts AS (
  SELECT
    user_id,
    DATE_TRUNC('month', first_activity_date) AS cohort_month
  FROM users
),
activity AS (
  SELECT
    user_id,
    DATE_TRUNC('month', activity_date) AS activity_month
  FROM user_activity
)

SELECT
  c.cohort_month,
  COUNT(DISTINCT c.user_id) AS cohort_size,
  COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month THEN a.user_id END) AS month_0,
  COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '1 month' THEN a.user_id END) AS month_1,
  COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '3 months' THEN a.user_id END) AS month_3
FROM cohorts c
LEFT JOIN activity a ON c.user_id = a.user_id
GROUP BY c.cohort_month
ORDER BY c.cohort_month;
```

方言替换：`DATE_TRUNC('month', x)` → BigQuery `DATE_TRUNC(x, MONTH)`；Snowflake/Redshift 同 PG 写法；MySQL 用 `DATE_FORMAT(x, '%Y-%m-01')`；SQL Server 用 `DATEADD(month, DATEDIFF(month, 0, x), 0)`。月份偏移用各方言的 `DATEADD` / `DATE_ADD` 形式，不要写 `+ INTERVAL` 到不支持的方言上。

### 漏斗分析

```sql
WITH funnel AS (
  SELECT
    user_id,
    MAX(CASE WHEN event = 'page_view' THEN 1 ELSE 0 END) AS step_1_view,
    MAX(CASE WHEN event = 'signup_start' THEN 1 ELSE 0 END) AS step_2_start,
    MAX(CASE WHEN event = 'signup_complete' THEN 1 ELSE 0 END) AS step_3_complete,
    MAX(CASE WHEN event = 'first_purchase' THEN 1 ELSE 0 END) AS step_4_purchase
  FROM events
  WHERE event_date >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY user_id
)

SELECT
  COUNT(*) AS total_users,
  SUM(step_1_view) AS viewed,
  SUM(step_2_start) AS started_signup,
  SUM(step_3_complete) AS completed_signup,
  SUM(step_4_purchase) AS purchased,
  ROUND(100.0 * SUM(step_2_start) / NULLIF(SUM(step_1_view), 0), 1) AS view_to_start_pct,
  ROUND(100.0 * SUM(step_3_complete) / NULLIF(SUM(step_2_start), 0), 1) AS start_to_complete_pct,
  ROUND(100.0 * SUM(step_4_purchase) / NULLIF(SUM(step_3_complete), 0), 1) AS complete_to_purchase_pct
FROM funnel;
```

严格漏斗（要求按顺序、且带时间先后）需要自连接或窗口：先取每人各步最早时间戳，再比较 `t1 <= t2 <= t3`。

### 去重（取每个 key 的最新一条）

```sql
-- 保留每个 key 最新的一条记录
WITH ranked AS (
  SELECT
    entity_id,
    updated_at,
    <需要的列>,
    ROW_NUMBER() OVER (
      PARTITION BY entity_id
      ORDER BY updated_at DESC
    ) AS rn
  FROM source_table
)
SELECT entity_id, updated_at, <需要的列>
FROM ranked
WHERE rn = 1;
```

- 并列风险：`updated_at` 有重复时间戳时结果不稳定，追加 `id` 作次序键
- 大表上先按分区过滤再排序，或改用方言原生的等效手段（Snowflake / BigQuery / DuckDB 的 `QUALIFY`、PG 的 `DISTINCT ON (entity_id)`）

### 分区裁剪检查清单

- 分区/聚簇过滤条件写在**基表所在的最内层 CTE**，不要等到最外层再筛
- 过滤形式要可裁剪：`event_date BETWEEN ... AND ...` 或 `event_date >= ...`；对分区列套函数（`DATE_TRUNC(partition_col,...) = ...`）常导致裁剪失效，改成对常量侧做变换
- 日期分区列的类型要对齐：`DATE` 分区配字符串常量需 `CAST`，否则可能退化成全表扫
- 分区表 JOIN 非分区表时，先裁分区再 JOIN
- 上线前用 `EXPLAIN` / BigQuery dry run / Snowflake query profile 确认扫了多少数据

---

## 报错与调试

查询失败时按这个顺序排查：

1. **语法错误**：检查是否为方言特有语法（BigQuery 没有 `ILIKE`；`SAFE_DIVIDE` 只在 BigQuery；`DISTINCT ON` 只在 PG；`QUALIFY` 只在 DuckDB/Snowflake/BigQuery 系）
2. **列找不到**：对着 schema 核列名——查拼写、查大小写（PostgreSQL 中加双引号的标识符区分大小写）
3. **类型不匹配**：跨类型比较显式转换（`CAST(col AS DATE)`、`col::DATE`）
4. **除零**：用 `NULLIF(分母, 0)`，或方言的安全除法（BigQuery `SAFE_DIVIDE`）
5. **列名歧义**：JOIN 中所有列都用表别名限定
6. **GROUP BY 报错**：非聚合列必须全部出现在 `GROUP BY` 里（BigQuery 允许按别名分组是例外）
7. **结果行数异常**：先单独跑每个 CTE 看基数，定位是哪一步 JOIN 放大或过滤掉了
8. **结果太慢**：确认分区过滤是否生效、JOIN 键类型是否一致（隐式转换会让索引失效）、是否误用了 `SELECT *`

## DSH 侧的落地方式

- 需要跨多个来源核对表结构或字段口径时，可用 `grep` / `glob` 搜工作区里已有的 `.sql`、dbt model、schema 文件，复用既有定义而不是重新发明
- 复杂取数任务可用 `todo_write` 拆步骤；需要并行探查多张表时用 `subagent` 分发
- 无 MCP 时：`write` 存 `.sql` → 用户执行 → 用户贴回结果或上传 CSV/XLSX → `load_workspace_dependencies` 拿捆绑 Python 路径 → pandas 分析
