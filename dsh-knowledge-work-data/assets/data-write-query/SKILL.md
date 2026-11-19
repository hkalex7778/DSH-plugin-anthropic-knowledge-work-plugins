---
name: data-write-query
description: 把自然语言的数据需求翻译成针对指定 SQL 方言优化、带注释的查询，并保存为 .sql 文件。适用场景：用户口述取数需求要生成 SQL、需要多 CTE + JOIN + 聚合的复杂分析查询、要在大数据量分区表上优化性能、或要 Snowflake / BigQuery / PostgreSQL / Redshift / Databricks / MySQL / SQL Server 等方言的具体写法。产出：完整查询 + 每段逻辑解释 + 性能说明 + 常见变体调整建议；若已配置数仓 MCP 可直接执行并分析结果，否则交付可自行运行的 .sql。
---

# data-write-query — 从自然语言写出优化 SQL

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

把用户口头描述的数据需求，翻译成针对**他所用方言**优化、遵循最佳实践的 SQL，最终落成 `.sql` 文件交付。本技能自包含：从问清口径到产出文件可以独立走完；需要具体方言语法时，用 `skill` 工具加载 `data-sql-queries`（纯知识技能，不进 `/` 菜单，只能由模型加载）。

## 执行步骤

### 1. 拆解需求

从用户描述里识别这几件事，缺哪一项就补问哪一项：

- **输出列**：结果要哪些字段？字段名叫什么（业务方看得懂的命名）？
- **过滤条件**：时间范围、人群/客群分段、状态枚举值分别是什么？
- **聚合**：有没有 GROUP BY？计数、求和还是求平均？分母是谁？
- **JOIN**：需要跨几张表？关联键是什么？一对多还是多对多？
- **排序**：按什么排？
- **限制**：是不是 top-N？要不要抽样？

口径含糊时（时间边界含不含端点、时区、活跃定义、去重粒度）用 `ask_user_question` 确认，**一次问清**，不要靠猜跑完一条长查询。

### 2. 确定 SQL 方言

如果方言未知，问用户用的是哪一种（并在本会话内记住，后续查询不再重复问）：

- **PostgreSQL**（含 Aurora PostgreSQL、RDS、Supabase、Neon）
- **Snowflake**
- **BigQuery**（Google Cloud）
- **Redshift**（Amazon）
- **Databricks SQL**
- **MySQL**（含 Aurora MySQL、PlanetScale）
- **SQL Server**（Microsoft）
- **DuckDB**
- **SQLite**
- **其他**（追问具体产品和版本）

MySQL 与 SQL Server 的关键差异速记：

```sql
-- MySQL：标识符用反引号；LIMIT n OFFSET m；CONCAT(a, b)
--   8.0+ 支持窗口函数与 JSON；无 FULL OUTER JOIN（用 LEFT JOIN UNION ALL 补 RIGHT JOIN 未匹配部分）
--   INTERVAL 语法：created_at - INTERVAL 7 DAY
-- SQL Server：标识符用 [brackets] 或双引号；TOP n 或 OFFSET ... ROWS FETCH NEXT ... ROWS ONLY
--   GETDATE()、DATEADD(day, 7, col)、DATEDIFF(day, a, b)、EOMONTH(col)
--   字符串拼接用 + 或 CONCAT(a, b)；ISNULL(x, y)（也有标准 COALESCE）
--   无原生 ILIKE：用 LIKE + 不区分大小写的 collation，或 LOWER(col) LIKE LOWER('...')
```

需要逐方言的日期/字符串/半结构化函数、性能手法与常用分析模板，加载 `data-sql-queries`。

### 3. 获取 schema

按以下优先级，不要凭空编表名列名：

1. **已配置数仓 MCP 服务器**（Snowflake / Databricks / BigQuery / PostgreSQL 等任一）：直接用它搜索相关表、读列名与类型、确认关联关系；检查分区键 / clustering key / distribution key 是否影响性能；看看有没有现成的 view 或 materialized view 可以省掉一大段逻辑。执行结果直接读回来迭代。
2. **无 MCP 连接**：请用户提供建表语句（`\d+ tablename` / `SHOW CREATE TABLE` 的输出）、列名清单，或先导一小批样本数据（CSV / Excel）过来。缺信息时明确说明「我需要 X 表的哪些列才能写下这一段」。
3. **完全拿不到 schema**：仍可产出 SQL，但所有表名与列名一律用尖括号占位（`<orders_table>.<created_at_col>`），并在文件顶部注释里列出需要替换的位置。

### 4. 写查询

**结构**

- 多逻辑步骤一律用 CTE（`WITH` 子句），一个 CTE 只做一件事
- CTE 名字描述业务含义：`daily_signups`、`active_users`、`revenue_by_product`
- 顶层最终 `SELECT` 只做拼装与排序

**性能**

- 生产查询**永远不用** `SELECT *`，只列出需要的列
- 尽早过滤：把 `WHERE` 推到最贴近基表的 CTE 里
- 有分区就用分区过滤（日期分区优先），确保过滤条件写成可裁剪的形式
- 大结果集的子查询用 `EXISTS` 代替 `IN`
- JOIN 类型选对：语义是内连接就不要写 `LEFT JOIN`
- 能用 JOIN 或窗口函数解决的，不要写相关子查询
- 警惕多对多 JOIN 造成行数爆炸
- 明确幂等性：查询是否可安全重跑？要不要参数化日期范围？

**可读性**

- 非直观的逻辑旁边加注释，解释**为什么**而不是「是什么」
- 缩进与格式全篇一致，每个主要子句单独一行
- 表别名要有意义（`o`、`evt`），不要用 `a`、`b`、`c`
- 文件头部写注释块：用途、作者/会话、口径定义、依赖表、预计扫描量、参数说明

**方言适配**

- 用该方言原生的日期函数、字符串函数、窗口语法（见 `data-sql-queries`），不要混用
- 顺带上该方言的性能特性：Snowflake clustering key、BigQuery 分区列过滤与 dry run、Redshift DISTKEY/SORTKEY、Databricks `OPTIMIZE`/`ZORDER`、PostgreSQL 索引与 `EXPLAIN ANALYZE`

### 5. 交付

产出顺序：

1. 在对话里给出**完整查询**（`sql` 代码块）+ 每个 CTE 在做什么的简短说明 + 性能说明（预计代价、是否命中分区、潜在瓶颈）+ 常见变体怎么改（换时间范围、换粒度、加过滤）
2. 用 `write` 把查询存成 `.sql` 文件（文件名体现内容，如 `cohort_retention_by_signup_month.sql`），放在工作区内，含第 4 步要求的注释块
3. 用 `present` 交付这个 `.sql` 文件

如果工作区里已有同类 `.sql`，先 `glob` / `grep` 找一遍能否复用或改参数，避免重复造；改用户已有文件前先确认。

### 6. 关于执行

- **有数仓 MCP**：主动提出直接跑，读回结果并继续分析（分布、异常值、下一步该看什么）。
- **无 MCP**：说明查询已可直接复制运行；请用户跑完把结果贴回来，或导出 CSV / Excel 上传，再用捆绑 Python（`load_workspace_dependencies` → pandas 读 CSV/XLSX）做后续分析。

> 方言细节与模板都在 `data-sql-queries` 里，需要时加载它，不要凭记忆猜函数名。

## 示例

**简单聚合**

```
把过去 30 天订单按状态分组计数
```

**复杂分析**

```
做同期群留存：按注册月份分群，看 1、3、6、12 个月后仍活跃（至少有一次事件）的用户占比。我们用 Snowflake。
```

**性能敏感**

```
events 表 5 亿行、按天分区。取最近 7 天事件数最多的前 100 个用户，并给出每人最近一次的事件类型。
```

## 提示

- 开口就说明方言，能一次拿到正确语法
- 知道表名就一并给出，省掉一轮 schema 追问
- 说明查询要幂等（可安全重跑）还是一次性
- 周期性取数请说明是否要参数化日期范围，并在注释里标出参数位置
- 数据量大时先问清「能不能在开发环境验一次再跑生产」
