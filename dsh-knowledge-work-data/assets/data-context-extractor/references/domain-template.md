# 域参考文件模板

> Modified from the original work by Anthropic — 译自并改写自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)。原文件：`data/skills/data-context-extractor/references/domain-template.md`。

为具体数据域（如收入 revenue、用户 users、市场 marketing）创建参考文件时使用本模板。产物建议放在知识文档目录的 `references/[domain].md`。

---

````markdown
# [DOMAIN_NAME] 表

本文档包含 [域] 相关的表、指标与查询模式。

---

## 速查

### 业务背景
[两三句话说明这个域覆盖什么、关键概念是什么]

### 实体澄清

**「[AMBIGUOUS_TERM]」可能指：**
- **[MEANING_1]**：[DEFINITION]（[TABLE]: [ID_FIELD]）
- **[MEANING_2]**：[DEFINITION]（[TABLE]: [ID_FIELD]）

查询前务必澄清指的是哪一个。

### 标准过滤

[域] 查询永远带上：
```sql
WHERE [STANDARD_FILTER_1]
  AND [STANDARD_FILTER_2]
```

---

## 核心表

### [TABLE_1_NAME]

**位置**：`[project.dataset.table]` 或 `[schema.table]`
**说明**：这张表装什么、什么时候用
**主键**：[COLUMN(S)]
**更新频率**：[每日/每小时/实时]（延迟 [LAG]）
**分区方式**：[PARTITION_COLUMN]（如适用）

| 列 | 类型 | 说明 | 备注 |
|----|------|------|------|
| **[column_1]** | [TYPE] | [DESCRIPTION] | [GOTCHA_OR_CONTEXT] |
| **[column_2]** | [TYPE] | [DESCRIPTION] | |
| **[column_3]** | [TYPE] | [DESCRIPTION] | 可空 |

**关联关系**：
- 通过 `[JOIN_KEY]` 与 `[OTHER_TABLE]` join
- 是 `[CHILD_TABLE]` 的父表（外键 `[FOREIGN_KEY]`）

**嵌套 / STRUCT 字段**（如适用）：
- `[struct_name].[field_1]`：[DESCRIPTION]
- `[struct_name].[field_2]`：[DESCRIPTION]

---

### [TABLE_2_NAME]

[重复上述格式]

---

## 关键指标

| 指标 | 定义 | 表 | 公式 | 备注 |
|------|------|----|------|------|
| [METRIC_1] | [DEFINITION] | [TABLE] | `[FORMULA]` | [CAVEATS] |
| [METRIC_2] | [DEFINITION] | [TABLE] | `[FORMULA]` | |

---

## 示例查询

### [QUERY_PURPOSE_1]

```sql
-- [简述这个查询干什么]
SELECT [columns]
FROM [table]
WHERE [standard_filters]
GROUP BY [grouping]
ORDER BY [ordering]
```

### [QUERY_PURPOSE_2]

```sql
[ANOTHER_COMMON_QUERY]
```

### [QUERY_PURPOSE_3]：[更复杂的模式]

```sql
WITH [cte_name] AS (
    [CTE_LOGIC]
)
SELECT [final_columns]
FROM [cte_name]
[joins_and_filters]
```

---

## 常见坑

1. **[GOTCHA_1]**：[EXPLANATION]
   - 错误写法：`[INCORRECT_APPROACH]`
   - 正确写法：`[CORRECT_APPROACH]`

2. **[GOTCHA_2]**：[EXPLANATION]

---

## 相关仪表盘（如适用）

| 仪表盘 | 链接 | 用途 |
|--------|------|------|
| [DASHBOARD_1] | [URL] | [DESCRIPTION] |
| [DASHBOARD_2] | [URL] | [DESCRIPTION] |
````

---

## 写域文件的建议

1. **从被查得最多的表开始** —— 不求大而全
2. **只对重要列写列级细节** —— `created_at` 这种显而易见的列跳过
3. **真实查询示例 > 抽象描述** —— show, don't tell
4. **坑要放在显眼位置** —— 它们最省时间
5. **示例查询要能直接跑** —— 用真实表 / 列名
6. **嵌套 / STRUCT 字段显式标注** —— 这些最坑新人
7. **无 MCP 直连时** —— 表结构与示例查询作为「知识」记录即可，注明需要用户导出样例数据来验证口径

## 建议的域文件划分

常见要文档化的域（每个单独一个文件）：

- `revenue.md` —— 账单、订阅、ARR、交易
- `users.md` —— 账号、认证、用户属性
- `product.md` —— 功能使用、事件、会话
- `growth.md` —— DAU/WAU/MAU、留存、激活
- `sales.md` —— CRM、pipeline、商机
- `marketing.md` —— 投放、归因、线索
- `support.md` —— 工单、CSAT、响应时长
