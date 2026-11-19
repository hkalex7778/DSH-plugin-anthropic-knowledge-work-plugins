# 生成技能模板（DSH 版）

> Modified from the original work by Anthropic — 译自并改写自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)。原文件：`data/skills/data-context-extractor/references/skill-template.md`。

生成新的数据分析技能时以此为模板，替换所有 `[占位符]`。

> DSH frontmatter 硬约束（违反会被静默跳过）：`name` 必须等于技能目录名；每个键必须单行 `key: value`（禁止缩进、禁止 `|`/`>` 块标量、禁止空值）；`description` 单行、非空、≤400 字符，写清「什么时候用 + 用了得到什么」。上游的 `argument-hint` 键 DSH 不认，不要写。

---

````markdown
---
name: [company]-data-analyst
description: [COMPANY] 数据分析领域知识技能。提供查询 [WAREHOUSE_TYPE] 所需的上下文：实体定义、指标口径计算、常用查询模式与标准过滤条件。分析 [COMPANY] 的以下问题时使用：(1) [PRIMARY_USE_CASE_1]，(2) [PRIMARY_USE_CASE_2]，(3) [PRIMARY_USE_CASE_3]，或任何需要 [COMPANY] 专属上下文的数据问题。
---

# [COMPANY] 数据分析

## SQL 方言：[WAREHOUSE_TYPE]

[插入对应方言的注意点：日期函数、除法是否截断、STRUCT/ARRAY 访问、CTE 物化行为、分区裁剪写法等]

---

## 实体消歧

用户提到这些词时，先澄清指哪个实体：

[示例格式 —— 按实际抽取结果改写：]

**「User（用户）」可能指：**
- **Account（账号）**：个体登录 / 档案（[PRIMARY_TABLE]: [ID_FIELD]）
- **Organization（组织）**：计费主体，下挂多个账号（[ORG_TABLE]: [ORG_ID]）
- **[OTHER_TYPE]**：[DEFINITION]（[TABLE]: [ID]）

**关系：**
- [ENTITY_1] → [ENTITY_2]：[RELATIONSHIP_TYPE]（用 [JOIN_KEY] 关联）

---

## 业务术语表

| 术语 | 定义 | 备注 |
|------|------|------|
| [TERM_1] | [DEFINITION] | [CONTEXT/GOTCHA] |
| [TERM_2] | [DEFINITION] | [CONTEXT/GOTCHA] |
| [ACRONYM] | [FULL_NAME] —— [EXPLANATION] | |

---

## 标准过滤条件

除非明确要求，所有查询永远带上：

```sql
-- 排除测试 / 内部数据
WHERE [TEST_FLAG_COLUMN] = FALSE
  AND [INTERNAL_FLAG_COLUMN] = FALSE

-- 排除无效 / 欺诈
  AND [STATUS_COLUMN] != '[EXCLUDED_STATUS]'

-- [OTHER STANDARD EXCLUSIONS]
```

**何时可豁免：**
- [SCENARIO_1]：在 [CONDITION] 时保留 [NORMALLY_EXCLUDED]

---

## 关键指标

### [METRIC_1_NAME]

- **定义**：[平实语言解释]
- **公式**：`[EXACT_CALCULATION]`
- **来源**：`[TABLE_NAME].[COLUMN_NAME]`
- **时间粒度**：[DAILY/WEEKLY/MONTHLY]
- **Caveats**：[边界情况 / 坑]

### [METRIC_2_NAME]

[重复上述格式]

---

## 数据新鲜度

| 表 | 更新频率 | 典型延迟 |
|----|----------|----------|
| [TABLE_1] | [FREQUENCY] | [LAG] |
| [TABLE_2] | [FREQUENCY] | [LAG] |

检查数据新鲜度：
```sql
SELECT MAX([DATE_COLUMN]) AS latest_data
FROM [TABLE]
```

---

## 知识库导航

详细表文档见以下参考文件：

| 域 | 参考文件 | 用途 |
|----|----------|------|
| [DOMAIN_1] | `references/[domain1].md` | [BRIEF_DESCRIPTION] |
| [DOMAIN_2] | `references/[domain2].md` | [BRIEF_DESCRIPTION] |
| 实体 | `references/entities.md` | 实体定义与关系 |
| 指标 | `references/metrics.md` | KPI 计算与公式 |

---

## 常用查询模式

### [PATTERN_1_NAME]

```sql
[SAMPLE_QUERY]
```

### [PATTERN_2_NAME]

```sql
[SAMPLE_QUERY]
```

---

## 故障排查

### 常见错误

- **[MISTAKE_1]**：[EXPLANATION] → [CORRECT_APPROACH]
- **[MISTAKE_2]**：[EXPLANATION] → [CORRECT_APPROACH]

### 访问问题

- 若已配置的数仓 MCP 对 `[TABLE]` 报权限错误：[WORKAROUND]；未配置 MCP 时请用户导出该表样例 CSV。
- 涉及 PII 受限列：[ALTERNATIVE_APPROACH]

### 性能提示

- 先用 `[PARTITION_COLUMN]` 过滤以减少扫描量
- 大表探查阶段先 `LIMIT`
- 能用 `[AGGREGATED_TABLE]` 就别扫 `[RAW_TABLE]`
````

---

## 定制注意事项

生成技能时：

1. **填满所有占位符** —— 交付版不允许残留 `[PLACEHOLDER]` 文本
2. **删掉用不上的段落** —— 没有仪表盘就删那节
3. **写到具体** —— 泛泛建议不如具体列名和取值有用
4. **带真实示例** —— 示例查询要用真实表 / 列名
5. **保持可扫读** —— 多用表格与代码块
6. **落地路径** —— 产物放项目 `.dsh/skills/<name>/SKILL.md`（`<name>` = frontmatter `name`），或把核心口径浓缩进 `AGENTS.md`；DSH 不做 zip 打包交付，直接以文件 + `present` 交付
