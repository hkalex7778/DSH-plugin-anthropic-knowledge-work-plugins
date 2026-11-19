# DSH 岗位插件

给 **DeepSeek Harness** 的非技术岗位插件，移植并中文化自 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（Apache-2.0）。

每个岗位是一个**独立可安装**的 bundle：装完后会话的模式选择里多出对应预设，把该岗位的日常工作变成可加载的中文 SOP 技能，交付真实文件而不是对话里的长表格。

## 当前岗位

| 岗位 | 预设显示名 | 技能数 | 连接器 | 目录 |
|---|---|---|---|---|
| 数据分析师 | 数据分析师 | 10 | 无强制依赖 | [`dsh-knowledge-work-data/`](dsh-knowledge-work-data/) |
| 运营专员 | 运营专员 | 9 | 仅日历（可选） | [`dsh-knowledge-work-operations/`](dsh-knowledge-work-operations/) |
| 效率助手 | 效率助手 | 4 | **重度**（Slack/Notion/Asana/Linear/Jira/日历等） | [`dsh-knowledge-work-productivity/`](dsh-knowledge-work-productivity/) |

> 每个岗位各自独立安装，按需取用。数据岗与运营岗基本开箱即用；效率岗不接连接器时会降级为半自动（详见其 README）。

## 我是非技术同事，怎么用？

1. 新建一个会话。
2. 在会话的**模式 / Agent 预设**选择器里选一个岗位（不是 Standard），例如「数据分析师」。
3. 用大白话提需求，例如：「帮我看看这份销售数据，告诉我最近三个月的趋势」，然后把 Excel/CSV 拖进来或用 `@` 引用文件。
4. 第一次让它出图/跑脚本时，若弹出**命令授权**确认框，点确认 —— 那是在你本机本地执行，不联网。

想省掉第 2 步：在 **设置 → Agent 预设** 里把常用岗位设为新会话默认。

## 安装

### 方式 A：从本地目录装（最简单）

侧边栏 **Plugins** → **Add plugin** → 选择本仓库里对应岗位的目录（如 `dsh-knowledge-work-data/`）。

### 方式 B：加本仓库为插件索引，从 Discover 装

1. 在 DSH 里开启 **Plugins** 页的 **Discover** 标签（实验项 *Custom plugin indexes*）。
2. **Add index source** → 填：
   `https://raw.githubusercontent.com/hkalex7778/DSH-plugin-anthropic-knowledge-work-plugins/main/market-index/index.json`
3. 在 Discover 里找到想要的岗位 → **Install**。

## 隔离范围（说准确）

每个岗位插件的技能**只出现在选了该岗位预设的会话里**，普通 Standard 会话看不到。

但反过来不成立：岗位会话里**还会**看到全局技能（`office*`、`memory` 等），因为岗位预设保留了 DSH 的技能文件系统与 Office 能力 —— 出报告、出表格正需要它们。所以岗位预设是「Standard + 岗位技能 + 岗位人设」，不是封闭环境。

## 与上游的差异

- **中文优先**：上游模板偏英文，这里正文以中文为主，SQL / Python / 术语保留英文。
- **不绑订阅**：模型走 DSH 自己的路由，与 Claude 订阅无关。
- **交付物落地**：图表出 PNG 并用 `present` 交付；报告/表格走 `office` 技能产出 `.docx` / `.xlsx` / `.pptx`。
- **工具名换成 DSH 实际能力**：不引用 Claude 专有工具。
- **作用域**：上游靠 marketplace 逐个安装；这里靠 preset 作用域隔离，切换岗位 = 切换模式，不用装卸。

## 目录结构

```
dsh-knowledge-work-data/          ← 数据分析师 bundle（安装这个目录）
dsh-knowledge-work-operations/    ← 运营专员 bundle
dsh-knowledge-work-productivity/  ← 效率助手 bundle
market-index/index.json           ← Discover 用的插件索引（三个岗位都在里面）
LICENSE / NOTICE.md               ← Apache-2.0 合规
```

## 连接器说明

连接器**不会自动授权** —— 与上游一样，MCP 服务器需逐个在 **设置 → MCP** 配置。

- **数据分析师**：无强制依赖，上传文件 / 贴查询结果即可完整使用。
- **运营专员**：仅个别技能可选接日历，不接不影响主体功能。
- **效率助手**：核心价值在于替你操作 Slack / Notion / Asana / Linear / Jira 等 SaaS。**不接连接器时，`task-management` 完整可用，其余三个技能降级为半自动**（需手动粘贴内容）。技能正文里已在每处连接器操作前标注了降级路径。

## 许可与归属

本仓库是 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（Apache-2.0，Copyright Anthropic）的**衍生作品**。

- 完整的 Apache-2.0 许可证文本见 [LICENSE](LICENSE)。
- 修改说明与归属见 [NOTICE.md](NOTICE.md)。
- 每个衍生文件顶部都带有醒目的 `Modified from the original work by Anthropic.` 声明。

本作品与 Anthropic 无隶属或背书关系。「Claude」「Anthropic」为各自所有者的商标。
