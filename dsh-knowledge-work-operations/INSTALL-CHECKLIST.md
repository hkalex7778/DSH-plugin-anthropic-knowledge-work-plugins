# 安装与验证清单

本清单面向任意安装者，用于在装好后逐项确认插件可用。清单不假设具体安装路径——按你自己的 profile / 工作区位置替换即可。

## 安装方式

侧边栏 **Plugins** → **Add plugin** → 选择本 bundle 目录（`dsh-knowledge-work-operations`）；或让 agent 执行 `plugin_manager` → `install_bundle`（需审批，会影响该 profile 的所有会话）。

若以 `link:` 方式安装（junction 指向 bundle 目录），则**改 bundle 目录里的文件即改插件本体**；但 patch 与 JS 模块的重新加载通常需要重启 DSH 才确定生效。

## 打包自检（应在安装前/后都通过）

以下脚本位于工作区 `tools/`，用 `$env:DSH_NODE_EXECUTABLE` 运行，全部应 exit 0：

| 项 | 命令 | 期望 |
|---|---|---|
| 语法 | `node --check index.js` | exit 0 |
| preset 声明 | `node tools/check-patch.cjs dsh-knowledge-work-operations/cordis.patch.yml out.json` | exit 0，`order=21`，`configId=knowledge-work-operations`，24 个插件行 |
| 打包完整性 | `node tools/check-packaging.mjs dsh-knowledge-work-operations` | exit 0，所有文件被 `files[]` 覆盖，零依赖 |
| 技能 provider | `node tools/test-provider-ops.mjs dsh-knowledge-work-operations report.txt` | exit 0，9 个技能可列举与加载 |

> 说明：`tools/test-provider.mjs` 与 `tools/check-crossrefs.mjs` 是为数据岗 bundle 写死的（断言 `data-` 前缀与 `data-workflow` 入口技能），运营岗不含这些，故本 bundle 提供等价的 `tools/test-provider-ops.mjs` 做校验。

## 安装后需要你在界面里确认

1. **插件卡片**：Plugins 页显示标题「运营专员岗位插件」、描述与齿轮图标（明暗主题都看一下）。
2. **preset 出现**：会话的模式/Agent 预设选择器里出现 **「运营专员」**（order 21，排在数据岗之后）。
3. **隔离方向**：新开一个 **Standard** 会话，确认 `/` 菜单里**没有** `capacity-plan`、`status-report` 等。
   注意：反向不成立——「运营专员」会话里**会**看到 `office*`、`memory` 等全局技能，因为 preset 保留了 DSH 的技能文件系统与 Office 能力（出 SOP、出报告正需要）。这是设计如此，不是泄漏。
4. **斜杠菜单**：在「运营专员」会话里敲 `/`，能看到 9 个运营技能。
5. **端到端跑一次**：说「帮我做季度产能规划」，拖一份人员/工作量表格进去。期望：先问清范围 → 产出利用率表与缺口 → 用 `present` 交付文档。
6. **权限弹窗**：第一次出文档/表格若弹出命令授权，点确认（本机生成，不联网）。

## 已知限制

- **连接器全部可选、不自动授权**：要直连日历/ITSM/项目跟踪/知识库等，需自行在 **设置 → MCP** 添加服务器。**没连接器不影响可用性**：涉日历的技能（`capacity-plan`、`compliance-tracking`、`status-report`）在未连接时会明确提示改为手动提供内容/粘贴数据。
- `meta.detail` 有意省略（按 DSH 规则，只有含特性图的文档才声明它），详情页走 README 兜底。
- 上游 11 个岗位里只做了运营（数据岗单独发布），其余未做。