# 安装与验证清单（效率助手岗位插件）

本清单面向任意安装者。按下面的步骤装好并逐项确认即可；每项都给了**客观判据**，能在你自己的环境里复现。

## 一、安装

1. 打开 DSH 侧边栏的 **Plugins** → **Add plugin**，选择本 bundle 目录 `dsh-knowledge-work-productivity`。
   - 或让 agent 执行 `plugin_manager` → `install_bundle`（需审批，会影响此 profile 的所有会话）。
2. 安装完成后，在插件列表里确认 `dsh-knowledge-work-productivity` 显示为 **enabled**。

> 若以 `link:` 方式安装（junction 指向源目录），**改源目录里的文件即改插件本体**；但 patch 与 JS 模块的重新加载需要**重启 DSH** 才确定生效。

## 二、安装后立即确认（有客观判据）

| 项 | 怎么验 | 期望 |
|---|---|---|
| 插件激活 | Plugins 列表里本 bundle 的状态 | `enabled: true`；preset 行 `include:preset-knowledge-work-productivity` 为 active |
| preset 出现 | 会话的**模式/Agent 预设选择器** | 能看到「效率助手」（order 22） |
| 技能可列举 | 选「效率助手」后在 `/` 菜单里看 | 能看到 `start`、`task-management`、`update`、`memory-management` |
| 隔离方向 | 新开一个 **Standard** 会话看 `/` 菜单 | **没有**这 4 个技能 |
| 图标/标题 | Plugins 详情页 | 显示本 bundle 的 icon 与「效率助手」描述（明暗主题各看一眼） |

> 反向隔离不成立：「效率助手」会话里**会**看到 `office*`、`memory` 等全局技能——这是设计如此（出文档/表格正需要），不是泄漏。

## 三、端到端跑一次（建议）

1. 选「效率助手」新建会话，输入 `/start`。
   - 期望：工作目录出现 `TASKS.md`、`WORKPLACE.md`、`memory/`，并把 `dashboard.html` 复制过来；助手引导你解码待办里的速记。
2. 说「加个任务：周五前把预算提案 review 完，给 Sarah」。
   - 期望：`TASKS.md` 的 Active 分区出现一条带上下文和截止日期的任务。
3. 说「记一下，todd 是财务的 Todd Martinez」。
   - 期望：`memory/people/todd-martinez.md` 建好，`WORKPLACE.md` 的 People 表出现一行。
4. 打开工作目录里的 `dashboard.html`（从文件管理器，不是让助手 `open`）。
   - 期望：看板显示任务和记忆，且与 `TASKS.md` 同步。

## 四、连接器（可选）

本插件**不强制**任何 MCP 连接器。默认行为：

- **`task-management` 完整可用**（纯本地 `TASKS.md`，零依赖）。
- **`memory-management` / `start` / `update` 降级为半自动**：外部内容需你手动粘贴，核心功能（建文件、解码、清理、填补缺口）照常工作。

要启用自动同步 / 深度扫描，在 **设置 → MCP** 自行添加对应服务的 MCP 服务器（Slack / Notion / Asana / Linear / Jira(Atlassian) / Monday / ClickUp / Google 日历 / Gmail）。每个用到连接器的步骤，技能正文里都有「此步需在 设置→MCP 连接 `<服务名>`；未连接时改为手动提供内容/粘贴数据，或跳过此步」的提示。

> 缺连接器**不是故障**。别为了「配齐」去连你用不上的服务。

## 五、已知限制

- 连接器不自动授权，需逐个在 设置 → MCP 手动添加。
- 上游 `productivity` 的深度扫描（`/update --comprehensive`）重度依赖连接器；未连接时按技能正文降级为手动提供内容。
- 工作记忆文件沿用上游两层结构，但文件名由 `CLAUDE.md` 改为 `WORKPLACE.md`（去 Claude 专属命名）。若你同时装有其它依赖 `CLAUDE.md` 的工具，两者互不冲突。
- 本 bundle 只做了 productivity 一个岗位；数据岗见 `dsh-knowledge-work-data`，其余岗位可按同结构扩展。
