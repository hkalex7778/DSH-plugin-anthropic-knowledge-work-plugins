---
name: memory-management
description: 两层记忆系统，让助手成为真正懂行的职场协作者。解码速记、缩写、绰号和内部行话，使助手能像同事一样理解你的请求。WORKPLACE.md 作为工作记忆，memory/ 目录作为完整知识库。
whenToUse: 需要记住人物/项目/术语、解码用户说的缩写或绰号、查某人是谁或某代号指什么、或要维护长期职场记忆时使用。
user-invocable: true
---

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins（productivity 插件，Apache-2.0），正文已中文化并适配 DeepSeek Harness。

# 记忆管理

记忆让助手成为你的职场协作者——一个会说你的内部语言的人。

## ⚠️ 连接器依赖

本技能的**核心（读写本地 `WORKPLACE.md` 与 `memory/`）完全不依赖连接器**，解码、增删、回忆记忆都能开箱即用。连接器只在以下场景用到：

| 服务 | 用在哪个场景 | 未连接时怎么办 |
|---|---|---|
| **Slack** | 通过 `/start` 或 `/update --comprehensive` 引导/深度扫描时，扫描聊天记录、频道、私信 | 改为用户手动粘贴聊天内容，或跳过聊天来源 |
| **Notion** | 深度扫描时读取知识库/文档 | 改为用户手动贴文档内容，或跳过 |
| **Asana / Monday** | 深度扫描时读取项目跟踪数据 | 改为用户手动提供，或跳过 |
| **日历** | 深度扫描时读取会议、参会人 | 跳过日历来源 |

**降级原则：** 日常的记忆**读写与解码**（本技能主体）无需任何连接器，始终完整可用。只有**首次引导（bootstrap）**和**深度扫描**会用到连接器；未连接时这些场景降级为半自动——用户手动粘贴内容，助手照样能把记忆建立起来。

此步需在 设置→MCP 连接 `<服务名>`；未连接时改为手动提供内容/粘贴数据，或跳过此步。

## 目标

把速记变成理解：

```
用户："让 todd 把 oracle 的 PSR 做一下"
              ↓ 助手解码
"让 Todd Martinez（财务负责人）为 Oracle Systems 这单
 （230 万美元，Q2 关单）准备 Pipeline Status Report"
```

没有记忆时，这个请求毫无意义。有了记忆，助手知道：

- **todd** → Todd Martinez，财务负责人，偏好用 Slack
- **PSR** → Pipeline Status Report（每周销售文档）
- **oracle** → Oracle Systems 这一单，不是那家公司

## 架构

```
WORKPLACE.md        ← 热缓存（约 30 个人物、常用术语）
memory/
  glossary.md       ← 完整解码表（所有内容）
  people/           ← 完整个人档案
  projects/         ← 项目详情
  context/          ← 公司、团队、工具
```

**WORKPLACE.md（热缓存）：**
- 你最常打交道的约 30 个人
- 约 30 个最常用的缩写/术语
- 活跃项目（5-15 个）
- 你的偏好
- **目标：覆盖 90% 的日常解码需求**

**memory/glossary.md（完整术语表）：**
- 完整解码表——每个人、每个术语
- 当 WORKPLACE.md 里查不到时才搜索它
- 可以无限增长

**memory/people/、projects/、context/：**
- 需要执行时的丰富细节
- 完整档案、历史、上下文

## 查找流程

```
用户："让 todd 处理 phoenix 的 PSR"

1. 查 WORKPLACE.md（热缓存）
   → Todd? ✓ Todd Martinez，财务
   → PSR? ✓ Pipeline Status Report
   → Phoenix? ✓ 数据库迁移项目

2. 没找到 → 搜 memory/glossary.md
   → 完整术语表里有所有人/所有事

3. 还没找到 → 问用户
   → "X 是什么意思？我记下来。"
```

这种分层方式让 WORKPLACE.md 保持精简（约 100 行），同时 memory/ 支持无限规模。

## 文件位置

- **工作记忆：** 当前工作目录下的 `WORKPLACE.md`
- **深层记忆：** `memory/` 子目录

## 工作记忆格式（WORKPLACE.md）

用表格以保持紧凑。目标总共约 50-80 行。

```markdown
# Memory

## Me
[名字]，[团队] 的 [职位]。[一句话说明我做什么。]

## People
| 谁 | 角色 |
|-----|------|
| **Todd** | Todd Martinez，财务负责人 |
| **Sarah** | Sarah Chen，工程（平台） |
| **Greg** | Greg Wilson，销售 |
→ 完整列表：memory/glossary.md，档案：memory/people/

## Terms
| 术语 | 含义 |
|------|---------|
| PSR | Pipeline Status Report |
| P0 | 天塌下来级别的优先级 |
| standup | 每天早上 9 点的同步会 |
→ 完整术语表：memory/glossary.md

## Projects
| 代号 | 是什么 |
|------|------|
| **Phoenix** | 数据库迁移，Q2 上线 |
| **Horizon** | 移动应用改版 |
→ 详情：memory/projects/

## Preferences
- 会议 25 分钟，留缓冲
- 异步优先，Slack 而非邮件
- 周五下午不开会
```

## 深层记忆格式（memory/）

**memory/glossary.md** —— 解码表：

```markdown
# Glossary

职场速记、缩写和内部行话。

## Acronyms
| 术语 | 含义 | 上下文 |
|------|---------|---------|
| PSR | Pipeline Status Report | 每周销售文档 |
| OKR | 目标与关键结果 | 季度规划 |
| P0/P1/P2 | 优先级 | P0 = 天塌下来 |

## Internal Terms
| 术语 | 含义 |
|------|---------|
| standup | 工程频道里每天 9 点的同步 |
| the migration | Phoenix 项目的数据库工作 |
| ship it | 部署到生产 |
| escalate | 拉领导进来 |

## Nicknames → Full Names
| 绰号 | 人物 |
|----------|--------|
| Todd | Todd Martinez（财务） |
| T | 也是 Todd Martinez |

## Project Codenames
| 代号 | 项目 |
|----------|---------|
| Phoenix | 数据库迁移 |
| Horizon | 新移动应用 |
```

**memory/people/{name}.md：**

```markdown
# Todd Martinez

**又称：** Todd、T
**职位：** 财务负责人
**团队：** 财务
**汇报给：** CFO（Michael Chen）

## 沟通方式
- 偏好 Slack 私信
- 回复很快，非常直接
- 最佳时间：上午

## 上下文
- 负责所有 PSR 和财务报告
- 50 万美元以上的交易审批关键联系人
- 与销售紧密合作做预测

## 备注
- 小熊队球迷，喜欢聊棒球
```

**memory/projects/{name}.md：**

```markdown
# Project Phoenix

**代号：** Phoenix
**又叫：** "the migration"
**状态：** 活跃，Q2 上线

## 是什么
从旧 Oracle 迁移到 PostgreSQL 的数据库迁移。

## 关键人物
- Sarah - 技术负责人
- Todd - 预算负责人
- Greg - 利益相关方（销售影响）

## 上下文
120 万美元预算，6 个月时间线。Horizon 项目的关键路径。
```

**memory/context/company.md：**

```markdown
# Company Context

## 工具与系统
| 工具 | 用途 | 内部叫法 |
|------|----------|---------------|
| Slack | 沟通 | - |
| Asana | 工程任务 | - |
| Salesforce | CRM | "SF" 或 "the CRM" |
| Notion | 文档/维基 | - |

## 团队
| 团队 | 做什么 | 关键人物 |
|------|--------------|------------|
| Platform | 基础设施 | Sarah（负责人） |
| Finance | 钱的事 | Todd（负责人） |
| Sales | 收入 | Greg |

## 流程
| 流程 | 含义 |
|---------|---------------|
| Weekly sync | 周一 10 点全员会 |
| Ship review | 周四部署审批 |
```

## 如何交互

### 解码用户输入（分层查找）

**在处理请求之前，始终先解码速记：**

```
1. WORKPLACE.md（热缓存）     → 先查，覆盖 90% 的情况
2. memory/glossary.md        → 热缓存里没有就查完整术语表
3. memory/people/、projects/ → 需要执行细节时查
4. 问用户                  → 未知术语？学过来。
```

例：

```
用户："让 todd 把 oracle 的 PSR 做一下"

WORKPLACE.md 查找：
  "todd" → Todd Martinez，财务 ✓
  "PSR" → Pipeline Status Report ✓
  "oracle" → （热缓存里没有）

memory/glossary.md 查找：
  "oracle" → Oracle Systems 这单（230 万美元）✓

现在助手可以带着完整上下文行动了。
```

### 添加记忆

当用户说「记住这个」或「X 的意思是 Y」时：

1. **术语表条目**（缩写、术语、速记）：
   - 加到 memory/glossary.md
   - 如果常用，加到 WORKPLACE.md 的 Quick Glossary

2. **人物：**
   - 新建/更新 memory/people/{name}.md
   - 重要的话加到 WORKPLACE.md 的 Key People
   - **一定要记绰号** —— 对解码至关重要

3. **项目：**
   - 新建/更新 memory/projects/{name}.md
   - 当前项目加到 WORKPLACE.md 的 Active Projects
   - **一定要记代号** —— "Phoenix"、"the migration" 之类

4. **偏好：** 加到 WORKPLACE.md 的 Preferences 分区

### 回忆记忆

当用户问「X 是谁」或「X 是什么意思」时：

1. 先查 WORKPLACE.md
2. 再查 memory/ 看完整细节
3. 还没有就说：「我还不知道 X 是什么意思，你能告诉我吗？」

### 渐进披露

1. 加载 WORKPLACE.md 快速解析任何请求
2. 需要完整执行上下文时深入 memory/
3. 例：给 todd 起草一封关于 PSR 的邮件
   - WORKPLACE.md 告诉你 Todd = Todd Martinez，PSR = Pipeline Status Report
   - memory/people/todd-martinez.md 告诉你他偏好 Slack、说话直接

## 引导（Bootstrap）

用 `/start` 通过扫描你的聊天、日历、邮件和文档来初始化，提取人物、项目，开始建立术语表。

> **连接器提示：** 引导扫描此步需在 设置→MCP 连接 `<Slack / 日历 / Gmail / Notion>`；未连接时改为用户手动粘贴这些内容，或只用本地任务清单引导，或跳过扫描直接手写记忆文件。

## 约定

- WORKPLACE.md 里的术语用**加粗**便于扫读
- WORKPLACE.md 控制在 100 行以内（"热 30"原则）
- 文件名：小写、连字符（`todd-martinez.md`、`project-phoenix.md`）
- 始终记下绰号和别名
- 用术语表表格便于查找
- 常用的东西提升到 WORKPLACE.md
- 过时的东西降级到 memory/

## 什么放哪里

| 类型 | WORKPLACE.md（热缓存） | memory/（完整存储） |
|------|----------------------|------------------------|
| 人物 | 最常联系的约 30 个 | glossary.md + people/{name}.md |
| 缩写/术语 | 约 30 个最常用 | glossary.md（完整列表） |
| 项目 | 仅活跃项目 | glossary.md + projects/{name}.md |
| 绰号 | 前 30 的话放 Key People | glossary.md（所有绰号） |
| 公司上下文 | 仅快速参考 | context/company.md |
| 偏好 | 所有偏好 | - |
| 历史/过时 | ✗ 移除 | ✓ 留在 memory/ |

## 提升 / 降级

**在以下情况提升到 WORKPLACE.md：**
- 你频繁使用某个术语/人物
- 它属于当前工作的一部分

**仅在以下情况降级到 memory/：**
- 项目已完成
- 某人不再是频繁联系人
- 术语很少用了

这让 WORKPLACE.md 保持新鲜和相关。