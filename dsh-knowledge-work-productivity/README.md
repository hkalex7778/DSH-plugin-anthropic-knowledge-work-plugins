# dsh-knowledge-work-productivity

效率助手岗位插件 for DeepSeek Harness — 对标 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的 `productivity` 插件，移植并中文化。

## 装完怎么用（给非技术同事）

1. 新建一个会话。
2. 在会话的**模式/Agent 预设选择器**里选 **「效率助手」**（不是 Standard）。
3. 第一次先说「`/start`」——它会建好 `TASKS.md`（任务清单）、`WORKPLACE.md`（工作记忆）、`memory/`（深层记忆）并把看板 `dashboard.html` 复制到你的工作目录。
4. 之后用大白话即可：「加个任务，周五前把预算提案 review 完」「记一下，todd 是财务的 Todd Martinez」「我今天有什么事」。

想省掉第 2 步：在 **设置 → Agent 预设** 里把「效率助手」设为新会话默认。

## 连接器：不接也能用（重要）

上游 productivity 重度依赖 9 个 MCP 连接器（Slack / Notion / Asana / Linear / Jira(Atlassian) / Monday / ClickUp / Google 日历 / Gmail）。本移植版**不强制任何连接器**，但各技能对连接器的依赖不同：

| 技能 | 不接连接器时 |
|---|---|
| `task-management` | **完整可用**（纯本地 `TASKS.md`，零依赖） |
| `memory-management` | 日常读写/解码记忆**完整可用**；仅「首次引导扫描」降级 |
| `start` | 核心建文件+解码速记**可用**；从 Notion/Asana/Linear/Jira/日历自动拉取降级 |
| `update` | 本地清理/填补缺口**可用**；外部同步与深度扫描降级 |

**一句话：** `memory-management` / `start` / `update` 在不接连接器时降级为**半自动**——外部内容需要你手动粘贴，助手照样能把记忆建起来、把任务理清。每个用到连接器的步骤，技能正文里都有一句「此步需在 设置→MCP 连接 `<服务名>`；未连接时改为手动提供内容/粘贴数据，或跳过此步」。

要接的话：在 **设置 → MCP** 自行添加对应服务的 MCP 服务器即可（上游用插件自带 `.mcp.json` 预配，这里改成用户自己加，符合 DSH 模型）。

## 隔离范围（说准确）

本插件的 4 个技能**只出现在选了「效率助手」的会话里**，普通 Standard 会话看不到它们。

但反过来不成立：「效率助手」会话里**还会**看到全局技能（`office*`、`memory` 等），因为岗位 preset 保留了 DSH 的技能文件系统与 Office 能力。所以这个 preset 是「Standard + 岗位技能 + 岗位人设」，不是封闭环境。

## 它带来什么

| | |
|---|---|
| Agent 预设 | `knowledge-work-productivity`（显示名「效率助手」，order 22） |
| 岗位技能 | `assets/*/SKILL.md`，通过 preset 作用域的 skill provider 注册 |
| 连接器 | 无强制依赖。要自动同步，自行在 **设置 → MCP** 添加服务器 |

### 4 个技能

| 技能 | 用途 | 连接器依赖（未接时降级点） |
|---|---|---|
| `start` | 初始化任务+记忆系统，打开看板，从现有待办引导职场记忆、解码速记 | Notion / Asana / Linear / Jira（第 5 步读任务）、日历（第 6 步深度扫描） |
| `task-management` | 共享 `TASKS.md` 的轻量任务管理：增删改查、提取待办、看板 | **无**（零依赖） |
| `update` | 同步外部任务、清理过期项、填补记忆缺口；`--comprehensive` 深度扫描 | Asana / Linear / Jira（第 2 步同步）、Slack / Gmail / Notion / 日历（深度扫描） |
| `memory-management` | 两层记忆：`WORKPLACE.md` 热缓存 + `memory/` 深层，解码绰号/缩写/代号 | Slack / Notion / Asana / Monday / 日历（仅引导/深度扫描场景） |

技能名保持上游英文目录名（`start` / `update` / `task-management` / `memory-management`），方便对照上游；均可在 `/` 菜单调用。

## 附带看板

`assets/dashboard.html` —— 本地可视化看板，读 `TASKS.md` + `WORKPLACE.md` + `memory/`，支持拖拽排序、任务与记忆双视图。`start` 会把它复制到你的工作目录，从文件管理器打开即可（离线、不联网）。

> 该看板原为 Claude 生态编写，已把其中的 `CLAUDE.md` 引用改为 `WORKPLACE.md`，与移植后的记忆文件名一致。

## 与上游的差异

- **中文优先**：上游正文偏英文，这里以中文为主，文件名/命令/术语保留英文。
- **不绑订阅**：模型走 DSH 自己的路由，与 Claude 订阅无关。
- **去 Claude 专属机制**：移除 `.claude-plugin/plugin.json`、`${CLAUDE_PLUGIN_ROOT}`、`argument-hint`、`/productivity:*` 命名空间（改为直接 `/start`、`/update`）；工作记忆文件由 `CLAUDE.md` 改名 `WORKPLACE.md`（含看板）。
- **MCP 连接器**：由「插件自带 `.mcp.json`」改为「用户在 DSH 设置 → MCP 自行添加」。
- **连接器降级提示**：每个用到连接器的步骤都显式标注「未连接时改为手动提供内容/粘贴数据，或跳过此步」，正文顶部加「⚠️ 连接器依赖」小节。
- **作用域**：上游靠 marketplace 逐个安装；这里靠 preset 作用域隔离，切换岗位 = 切换模式，不用装卸。

## 许可

技能内容移植自 `anthropics/knowledge-work-plugins`（Apache-2.0），保留来源说明，见 `NOTICE.md`。本 bundle 自身同样按 Apache-2.0 提供。
