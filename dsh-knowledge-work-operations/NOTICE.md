# Attribution / NOTICE

本目录（DSH 运营专员岗位插件）包含改编自下列作品的素材：

- Repository: https://github.com/anthropics/knowledge-work-plugins
- Directory: `operations/`（Operations plugin）
- License: Apache License 2.0 — https://www.apache.org/licenses/LICENSE-2.0
- Copyright: Anthropic

## 关于 §4(d) 的 NOTICE 义务（实测说明）

上游 `operations/` 插件**不提供** NOTICE 文件（已核对其完整文件清单：`operations/` 下只有 `LICENSE`、`README.md`、`CONNECTORS.md`、`.mcp.json`、`.claude-plugin/plugin.json` 与 `skills/*/SKILL.md`，无 `NOTICE`）。仓库根目录的 `LICENSE` 为上游 Apache-2.0 文本。

因此 Apache-2.0 §4(d) 所附条件（保留原作品 NOTICE 中的归属声明）在本作品中**不被触发**——本文件是主动提供的归属说明，不是履行 §4(d)。

## §4(b) 修改声明

所有衍生文件都在正文顶部带有醒目的修改声明：

> Modified from the original work by Anthropic.

已带该声明的文件：`assets/*/SKILL.md`（9 个）。

## 改编内容（不是逐字复制）

1. 正文由英文改写为中文优先，命令、框架缩写（SOC 2、ISO 27001、GDPR、TCO、SLA、RACI 等）与专有名词保留英文。
2. 移除 Claude 专有机制：`.claude-plugin/plugin.json`、`argument-hint`、`/skill $ARGUMENTS` 斜杠参数机制、以及 `claude plugin marketplace` 安装流程。
3. 移除对 `CONNECTORS.md` 与 `~~category` 占位符体系的引用，改为在各技能内直接用中文说明「连接器为可选，需在 设置 → MCP 连接」。
4. 连接器依赖改写：上游假设 `.mcp.json` 预配置了 Slack / Google Calendar / Gmail / Notion / Atlassian / Asana 等服务器；本 bundle 不自带 `.mcp.json`，改为「用户在 DSH 设置 → MCP 自行添加」，并在 `capacity-plan`、`compliance-tracking`、`status-report` 等涉日历处明确「未连接时改为手动提供内容/粘贴数据」。
5. 新增 `whenToUse` 中文触发说明，并把部分上游 `description` 里的 "Trigger with ..." 提示整理为 `whenToUse`。
6. 技能改为通过 DSH 的 Agent 预设（preset）作用域分发，取代上游的 marketplace 逐个安装模型。
7. 目录名保持与上游一致的英文 kebab（`capacity-plan` 等），`frontmatter.name` 与目录名一致，便于跨技能引用。

## 非衍生文件

`index.js`、`cordis.patch.yml`、`locale/*.json`、`icon.svg`、`INSTALL-CHECKLIST.md`、本目录的 `README.md`，以及「运营专员」preset 的 persona 文字，由本插件作者撰写（非上游内容），同样以 Apache-2.0 提供。

## 商标

Apache-2.0 §6 不授予任何商标使用权。本作品与 Anthropic 无隶属或背书关系；「Claude」「Anthropic」为各自所有者的商标。