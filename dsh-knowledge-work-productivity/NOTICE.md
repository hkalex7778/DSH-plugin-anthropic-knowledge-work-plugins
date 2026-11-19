# Attribution / NOTICE

本目录（DSH 效率助手岗位插件）包含改编自下列作品的素材：

- Repository: https://github.com/anthropics/knowledge-work-plugins
- Directory: `productivity/`（Productivity plugin）
- License: Apache License 2.0 — https://www.apache.org/licenses/LICENSE-2.0
- Copyright: Anthropic

## 关于 §4(d) 的 NOTICE 义务（实测说明）

上游 `productivity/` 目录**不提供** NOTICE 文件（已核对其完整文件清单：`.claude-plugin/plugin.json`、`.mcp.json`、`CONNECTORS.md`、`LICENSE`、`README.md`、`skills/*`，无 `NOTICE`）。
因此 Apache-2.0 §4(d) 所附条件在本作品中**不被触发**。本文件是主动提供的归属说明，不是履行 §4(d)。

## §4(b) 修改声明

所有衍生的 SKILL.md 文件都在正文顶部带有醒目的修改声明：

> Modified from the original work by Anthropic.

已带该声明的文件：`assets/start/SKILL.md`、`assets/task-management/SKILL.md`、`assets/update/SKILL.md`、`assets/memory-management/SKILL.md`（共 4 个）。

`assets/dashboard.html` 是上游同一文件的改编版（未加 markdown 声明行，改动见下），其来源同属上述仓库 `productivity/` 插件。

## 改编内容（不是逐字复制）

1. **中文化**：4 个 SKILL.md 正文由英文改写为中文优先，文件名、命令、代码、专业术语保留英文。
2. **加连接器降级提示**：每个 SKILL.md 正文顶部新增「⚠️ 连接器依赖」小节，列出该技能用到哪些服务（Slack / Notion / Asana / Linear / Jira(Atlassian) / Monday / ClickUp / Google 日历 / Gmail）、哪些步骤在未连接时会降级；每处连接器操作前显式加一句「此步需在 设置→MCP 连接 `<服务名>`；未连接时改为手动提供内容/粘贴数据，或跳过此步」。
3. **去 Claude 专属机制**：移除 `.claude-plugin/plugin.json`、`${CLAUDE_PLUGIN_ROOT}` 路径变量、frontmatter 的 `argument-hint`、`/productivity:*` 命名空间（`/productivity:start` → `/start`、`/productivity:update` → `/update`）；工作记忆文件由 `CLAUDE.md` 改名 `WORKPLACE.md`（`assets/dashboard.html` 内的读取逻辑同步改名）；正文里 Claude 作为产品名的指代改为「助手」。
4. **MCP 连接器由「插件自带 `.mcp.json`」改为「用户在 DSH 设置 → MCP 自行添加」**；`CONNECTORS.md` 的「工具类别占位符」说明并入各技能的「连接器依赖」小节，不单独携带上游文件。
5. **frontmatter 适配**：`description`/`whenToUse` 改为中文，`name` 保留英文目录名，统一默认 `user-invocable: true`（上游 `task-management`/`memory-management` 为 `false`）。
6. **技能改为通过 DSH 的 Agent 预设（preset）作用域分发**，取代上游的 marketplace 逐个安装模型。

## 非衍生文件

`index.js`、`cordis.patch.yml`、`locale/*.json`、`icon.svg`、`INSTALL-CHECKLIST.md`、本目录的 `README.md`，以及「效率助手」preset 的 persona 文字，由本插件作者撰写（非上游内容），同样以 Apache-2.0 提供。

`LICENSE` 文件为 Apache License 2.0 官方正版文本（未修改）。

## 商标

Apache-2.0 §6 不授予任何商标使用权。本作品与 Anthropic 无隶属或背书关系；「Claude」「Anthropic」为各自所有者的商标。
