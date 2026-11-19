---
name: data-context-extractor
description: 从你（或团队分析师）的业务头脑中抽取公司专属的数据领域知识：实体定义、指标口径公式、术语表、标准过滤条件、常见坑，产出可复用的领域知识文档（工作区 markdown，如 metrics-glossary.md）。两种模式——Bootstrap（从零建立某数据域的知识文档）、Iteration（给已有文档补新领域）。产出物可放进项目 .dsh/skills/ 或写入 AGENTS.md，让后续会话自动继承。当分析师想让助手理解本公司数仓/指标/黑话、或发现每次都要重复解释口径时使用。
---

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

# 数据上下文抽取器（/data-context-extractor）

一个元技能：把口头流传的公司数据知识（tribal knowledge）抽出来，变成结构化、可复用、可进版本控制的领域知识文档。

## 在 DSH 里的落地形态

上游版本让 Claude「生成一个新的 skill 并打包 zip」。DSH 里对应落地为：

1. **产出物 = 工作区 markdown 文件**（如 `metrics-glossary.md`，或按域拆分的 `references/revenue.md`），用 `write` 写入工作区，用 `present` 交付。
2. **复用方式**：文档写好后提示用户两条路——
   - 放进项目 **`.dsh/skills/`** 目录（做成带合规 frontmatter 的技能，后续会话经 `skill` 加载），结构模板见 [references/skill-template.md](references/skill-template.md)；
   - 或把最关键的口径与术语浓缩进项目 **`AGENTS.md`**，让每个会话自动继承。
3. **数据侧接入**：若已在 设置 → MCP 配置了数仓 / BI 服务器，用其 schema/query 工具直接探查表结构、验证口径；否则请用户上传样例数据的 CSV/Excel（`@` 引用）或贴出建表语句 / 查询结果，从文档与对话中抽取。

两种模式：

1. **Bootstrap 模式**：从零建立一个新的领域知识文档
2. **Iteration 模式**：给已有文档补充新领域 / 修补缺口

---

## Bootstrap 模式

适用：用户想为某个数据域（收入、用户、增长……）建立第一份知识文档。

### 阶段 1：数据源发现

**Step 1：确认数据源形态**

问：「你们的数据放在哪里？是什么系统？」（数仓 / 数据库 / 只有导出的表格文件都算。）

- 若已配置对应 MCP 服务器：用其 schema 工具列出租户 / 库 / 表。
- 否则：请用户上传 CSV/Excel 或贴出查询结果 / DDL，作为抽取素材。

**Step 2：定位核心表**

问：「分析师最常查的 3–5 张表是哪些？」然后逐张拉 schema 或请用户贴字段清单。

有数仓 MCP 时可按方言探查（无 MCP 时把语法作为知识记入文档即可）：

```sql
-- BigQuery: 列出数据集
SELECT schema_name FROM INFORMATION_SCHEMA.SCHEMATA

-- BigQuery: 列出某数据集中的表
SELECT table_name FROM `project.dataset.INFORMATION_SCHEMA.TABLES`

-- Snowflake: 列出 schema
SHOW SCHEMAS IN DATABASE my_database

-- Snowflake: 列出表
SHOW TABLES IN SCHEMA my_schema
```

### 阶段 2：核心提问（要问出口）

发现数据源后，用对话方式逐个问下面这些问题（不要一次甩出全部；一次一个，跟进对方回答里的线索）。需要正式选项时用 `ask_user_question`。

**实体消歧（最关键）**
> 「在我们公司说『用户』或『客户』时，具体指什么？有几种不同的『用户』吗？」

听什么：多种实体类型（user vs account vs organization）；它们之间的关系（1:1 / 1:many / many:many）；用哪些 ID 字段关联。

**主键与业务标识**
> 「一个 [客户/用户/账户] 的主标识是什么？同一实体会有多个 ID 吗？」

听什么：主键 vs 业务键；UUID 与整型 ID 并存；历史 ID 体系 / 映射表。

**核心指标**
> 「大家最常问的 2–3 个指标是什么？每个是怎么算的？」

听什么：精确公式（如 `ARR = monthly_revenue × 12`）；每个指标来自哪些表 / 列；时间窗惯例（滚动 7 天、自然月、财月）。

**数据卫生（标准过滤）**
> 「查询时必须过滤掉什么？（测试数据、欺诈、内部账号等）

听什么：永远要带的 WHERE 条件；标记列（`is_test`、`is_internal`、`is_fraud`）；要排除的具体值（`status = 'deleted'`）。

**常见踩坑**
> 「新分析师在这份数据上最常犯什么错？」

听什么：起混淆作用的列名；时区问题；NULL 处理怪癖；历史快照表 vs 当前状态表。

### 阶段 3：生成文档

把答案整理成结构化 markdown，用 `write` 写入工作区。推荐布局（可按规模裁剪——单文件 `metrics-glossary.md` 起步完全可以，域多了再拆）：

```
metrics-glossary.md          # 或 <company>-data-context/
├── 实体定义与关系            # entities 段
├── 业务术语表                # glossary 段
├── 指标口径                  # 每个指标：定义/公式/来源/时间粒度/caveats
├── 标准过滤条件              # 永远要带的 WHERE
├── 数据新鲜度                # 各表更新频率与延迟
├── 常见坑与纠错              # gotchas
└── references/               # 按域拆分的详表（可选）
    └── [domain].md           # 用 references/domain-template.md 的格式
```

单文件段落模板与完整版技能模板见 **[references/skill-template.md](references/skill-template.md)**；按域拆分的参考文件格式见 **[references/domain-template.md](references/domain-template.md)**。

### 阶段 4：交付与接入

1. 用 `write` 写好全部文件，`present` 交付主文档。
2. 给用户一段「接入指引」：
   - 想让后续会话自动加载 → 把文档目录做成 `.dsh/skills/<name>/SKILL.md`（frontmatter 要求：`name` 等于目录名、单行 `key: value`、`description` 非空单行 ≤400 字符），模板见 references/skill-template.md；
   - 想全局轻量生效 → 把核心口径（实体消歧 + 标准过滤 + top 指标公式）浓缩成 10–20 行贴进项目 `AGENTS.md`。
3. 附一句总结：这次抽出了哪些内容、还缺哪些没问。

---

## Iteration 模式

适用：已有知识文档，但要补新领域或修补缺口。

### Step 1：加载现有文档

用 `read` 找到并读取工作区（或 `.dsh/skills/`）里已有的文档；不在工作区就请用户上传或贴出。先弄清哪些内容已经写过了，避免重复提问。

### Step 2：定位缺口

问：「这次要补哪个域 / 主题？最近哪些查询失败或算错了？」

常见缺口：新数据域（市场、财务、产品……）、缺指标定义、没写表关系、新出现的业务术语、改了口径没同步。

### Step 3：定向追问

针对该域：

1. 有数仓 MCP 就探查相关表；没有就请用户贴该域的典型表清单 / 样例数据。
2. 问域级问题：「[域] 分析用哪些表？」「[域] 的关键指标是什么？」「[域] 数据有什么特殊过滤或坑？」
3. 按 [references/domain-template.md](references/domain-template.md) 格式生成 `references/[domain].md`。

### Step 4：更新与交付

1. 新增参考文件；
2. 更新主文档的「知识导航」表，把新域登记进去；
3. 同步更新已放进 `.dsh/skills/` 的那份（若有），保持一致——两处内容漂移是最常见的失效方式；
4. `present` 交付更新后的文档，说明本次新增/修改了什么。

---

## 参考文件写作标准

### 表文档应包含

- **位置**：完整表路径
- **说明**：这张表装什么、何时用
- **主键**：如何唯一定位一行
- **更新频率**：刷新节奏与延迟
- **关键列**：列名 / 类型 / 说明 / 注意事项表格
- **关联关系**：与其他表怎么 join
- **示例查询**：2–3 个常用查询模式

### 指标文档应包含

- **指标名**：人类可读的名字
- **定义**：平实语言解释
- **公式**：精确计算式（带列引用）
- **来源表**：数据来自哪里
- **Caveats**：边界情况、排除项、坑

### 实体文档应包含

- **实体名**
- **定义**：它在业务里代表什么
- **主表**：去哪里找这个实体
- **标识字段**
- **关联关系**
- **常用过滤**：标准排除项（内部、测试等）

## 交付前质量清单

- [ ] 主文档 frontmatter / 标题结构完整（若做成技能：`name` = 目录名、`description` 单行非空）
- [ ] 实体消歧段落清晰（「用户」的每种含义都列出）
- [ ] 关键术语都有定义
- [ ] 标准过滤 / 排除条件已文档化
- [ ] 每个域至少 2–3 个示例查询
- [ ] SQL 用了正确的方言语义（按用户实际数仓）
- [ ] 参考文件在主文档导航表中有登记
- [ ] 没有遗留未替换的 `[占位符]`
- [ ] 已向用户说明如何放进 `.dsh/skills/` 或 `AGENTS.md` 完成复用

## 提示

- 一次别想抽全：先抽分析师每周都在解释的 2–3 个域，其余靠 Iteration 模式滚动补齐。
- 具体 > 抽象：写 `is_test = false AND plan != 'internal'` 比写「要排除测试数据」有用十倍。
- 抽取过程中听到的公式，若能用用户提供的样例数据在 pandas 里复算验证，就验证一下再写进文档——错口径进了 AGENTS.md 会污染所有后续会话。
- 文档进版本控制（git），口径变更要留变更记录（何时改、为什么改）。
