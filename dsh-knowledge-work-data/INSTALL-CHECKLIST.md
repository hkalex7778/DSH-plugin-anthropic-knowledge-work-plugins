# 安装与验证清单

装完这个插件后，用它 2 分钟确认一切正常。

## 安装

侧边栏 **Plugins** → **Add plugin** → 选择本仓库的 `dsh-knowledge-work-data/` 目录。
或让 agent 执行 `plugin_manager` → `install_bundle`，target 填该目录的绝对路径（需审批；会影响此 profile 的所有会话）。

也可以从 Discover 安装，见仓库根 README 的方式 B。

## 验证顺序

1. **安装结果**：返回的 `application` 应为 `applied`。若是 `restart-required`，重启 DSH 再看。
2. **预设出现在名册**：新开一个会话，模式 / Agent 预设选择器里应有 **「数据分析师」**。
3. **行已激活**：`plugin_manager` → `list_plugins`，找 `preset-knowledge-work-data`，其 `fiberPhase` 应为 `active`。
4. **技能进入目录**：在「数据分析师」会话里，应能看到 `data-workflow` 等工作流技能；输入 `/data-workflow` 应注入技能正文而不是报错。
5. **隔离性**：另开一个 **Standard** 会话，确认 `/` 菜单里**没有** `data-*`。
   注意反向不成立：「数据分析师」会话里**会**看到 `office*`、`memory` 等全局技能，这是设计如此（岗位预设 = Standard + 岗位技能 + 岗位人设），不是泄漏。
6. **真实跑一次**：给一份 CSV，说「分析这份数据，告诉我三个月趋势，出图」。期望：先问清口径 → 本机跑 pandas → 产出 PNG → 用 `present` 交付文件，而不是把长表贴回对话。第一次出图若弹出命令授权，确认即可（本机画图，不联网）。

## 这些已在开发机上验证过

| 项 | 结果 |
|---|---|
| 技能 provider 契约 | 10 个技能可列举与加载；8 个进 `/` 菜单，2 个知识型（`data-sql-queries`、`data-statistical-analysis`）标 `user-invocable: false` 只给模型加载 |
| 图表脚本 | 7 种图型回归通过；中文标题、副标题、图例、x/y 轴标签实测无豆腐块 |
| 统计函数数值 | t / χ² / F / 正态分位数与 scipy 参考值一致（已独立复现） |
| 仪表盘 guard | 数据未注入、数组为空、字段名不符三种情况都会显式报错，不会静默显示 0 |
| 打包完整性 | 全部文件被 manifest `files` 覆盖，零依赖，可离线安装 |

## 已知限制

- **连接器不自动授权**。要直连数仓，需自行在 **设置 → MCP** 添加服务器。**没连接器不影响可用性**：走「上传 CSV/Excel」或「贴查询结果」路径。
- 只做了 1 个岗位（数据）。其余 10 个未做。
- 详情页走 README 兜底（按 DSH 规则，只有含特性图的文档才声明 `meta.detail`）。
- 插件依赖 DSH 捆绑 Python 的实际库清单（无 matplotlib / scipy 等），若你的 DSH 版本改变了捆绑环境，出图与统计部分需要相应调整。
