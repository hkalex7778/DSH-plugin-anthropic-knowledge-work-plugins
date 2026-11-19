# dsh-knowledge-work-operations

运营专员岗位插件 for DeepSeek Harness — 对标 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的 `operations` 插件，移植并中文化。

## 装完怎么用（给非技术同事）

1. 新建一个会话。
2. 在会话的**模式/Agent 预设选择器**里选 **「运营专员」**（不是 Standard）。
3. 直接用大白话提需求，例如：「帮我做下个季度的团队产能规划，这份数据是各人当前工作量」，把 Excel/CSV 拖进来或 `@` 引用文件；也可以直接敲 `/` 从菜单里挑一个运营技能（如 `/capacity-plan`、`/status-report`）。
4. 第一次让它出文档/表格时，如果弹出**命令授权**确认框，点确认——那是在本机本地生成，不联网。

想省掉第 2 步：在 **设置 → Agent 预设** 里把「运营专员」设为新会话默认。

不需要连任何外部系统。没配任何连接器时，插件走「你上传文件 / 你粘贴内容 / 你口述信息」的路径，功能一样完整。

## 隔离范围（说准确）

本插件的 9 个运营技能**只出现在选了「运营专员」的会话里**，普通 Standard 会话看不到它们。

但反过来不成立：「运营专员」会话里**还会**看到全局技能（`office*`、`memory` 等），因为岗位 preset 保留了 DSH 的技能文件系统与 Office 能力——出 SOP、出状态报告、出评审表正需要它们。所以这个 preset 是「Standard + 岗位技能 + 岗位人设」，**不是封闭环境**。

## 它带来什么

| | |
|---|---|
| Agent 预设 | `knowledge-work-operations`（显示名「运营专员」，order 21） |
| 岗位技能 | `assets/*/SKILL.md`，通过 preset 作用域的 skill provider 注册 |
| 入口方式 | 无强制入口技能——按需加载对应技能，或在 `/` 菜单直接调用 |
| 连接器 | 全部**可选**。要直连日历/ITSM/项目跟踪等，自行在 **设置 → MCP** 添加服务器 |

### 9 个技能（全部可 `/` 调用）

| 技能 | 用途 |
|---|---|
| `capacity-plan` | 团队产能规划：利用率、缺口、瓶颈、招人/砍需求建议 |
| `change-request` | 变更管理申请：影响分析、风险评估、实施与回滚计划、审批清单 |
| `compliance-tracking` | 合规跟踪与审计就绪：控制项盘点、审计日历、差距分析 |
| `process-doc` | 流程文档（SOP）：流程图、RACI、分步说明、例外与边界 |
| `process-optimization` | 流程优化：找浪费、设计未来状态、量化收益、实施计划 |
| `risk-assessment` | 运营风险评估：风险矩阵、风险登记表、缓解措施 |
| `runbook` | 运维手册：精确分步命令、验证、排障、回滚、升级路径 |
| `status-report` | 状态汇报：KPI、绿黄红健康度、风险、待决策、下期重点 |
| `vendor-review` | 供应商评审：TCO、风险评估、优劣势、建议、谈判要点 |

技能之间按需互相引用（例如 `status-report` 需要风险矩阵时指向 `risk-assessment`），但不强制依赖某条固定链路。

## 与上游的差异

- **中文优先**：上游模板偏英文，这里正文以中文为主，命令/术语保留英文。
- **不绑订阅**：模型走 DSH 自己的路由，与 Claude 订阅无关；去掉了 Claude 专属的 `.claude-plugin`、`$ARGUMENTS` 斜杠机制。
- **连接器全部可选**：上游的 `~~placeholder` 连接器假设改成「用户在 设置 → MCP 自行连接，未连接则手动提供内容」。
- **作用域**：上游靠 marketplace 逐个安装；这里靠 preset 作用域隔离，切换岗位 = 切换模式，不用装卸。

## 许可

技能内容移植自 `anthropics/knowledge-work-plugins` 的 operations 插件（Apache-2.0），保留来源说明，见 `NOTICE.md`。本 bundle 自身同样按 Apache-2.0 提供，`LICENSE` 为 apache.org 正版字节。

## 尚未实现

- 上游另外 10 个岗位（市场、销售、法务、财务、产品、客服、设计、工程、HR 等）。数据岗（`dsh-knowledge-work-data`）已单独发布；复制其目录结构即可继续扩展。
- 连接器不会自动授权——与上游一样，MCP 服务器需逐个在设置里配置。