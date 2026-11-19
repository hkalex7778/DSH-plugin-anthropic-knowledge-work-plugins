# DSH 岗位插件 — 数据分析师

给 **DeepSeek Harness** 的非技术岗位插件，移植并中文化自 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) 的 `data` 插件（Apache-2.0）。

装完后，会话的模式选择里会多出一个 **「数据分析师」** 预设。它把「探索数据、写 SQL、出图表、做仪表盘、校验结论」变成可加载的中文 SOP 技能，交付的是真实文件（PNG / .xlsx / .docx / .pptx / .html / .sql），不是对话里的长表格。

## 我是非技术同事，怎么用？

1. 新建一个会话。
2. 在会话的**模式 / Agent 预设**选择器里选 **「数据分析师」**（不是 Standard）。
3. 用大白话提需求，例如：「帮我看看这份销售数据，告诉我最近三个月的趋势」，然后把 Excel/CSV 拖进来或用 `@` 引用文件。
4. 第一次让它出图时，如果弹出**命令授权**确认框，点确认 —— 那是在你本机本地画图，不联网。

想省掉第 2 步：在 **设置 → Agent 预设** 里把「数据分析师」设为新会话默认。

**不需要连数据库。** 没配任何连接器时，插件走「你上传文件 / 你贴查询结果」的路径，功能一样完整。

## 安装

### 方式 A：从本地目录装（最简单）

侧边栏 **Plugins** → **Add plugin** → 选择本仓库里的 `dsh-knowledge-work-data/` 目录。

### 方式 B：加本仓库为插件索引，从 Discover 装

1. 在 DSH 里开启 **Plugins** 页的 **Discover** 标签（实验项 *Custom plugin indexes*）。
2. **Add index source** → 填：
   `https://raw.githubusercontent.com/hkalex7778/DSH-plugin-anthropic-knowledge-work-plugins/main/market-index/index.json`
3. 在 Discover 里找到「数据分析师岗位插件」→ **Install**。

## 它带来什么

| | |
|---|---|
| Agent 预设 | `knowledge-work-data`（显示名「数据分析师」） |
| 岗位技能 | 10 个中文技能，通过 preset 作用域注册 |
| 入口技能 | `data-workflow` —— 先加载它，按路由表选具体技能 |
| 附带脚本 | `chart_pillow.py`：纯 Pillow 出图器（7 种图型），填补捆绑 Python 没有 matplotlib 的缺口 |
| 连接器 | 无强制依赖。要直连数仓，自行在 **设置 → MCP** 添加服务器 |

8 个工作流技能会出现在 `/` 斜杠菜单（等价上游的 `/analyze` 等命令）；2 个知识型技能（`data-sql-queries`、`data-statistical-analysis`）标了 `user-invocable: false`，只给模型按需加载，不占菜单。

## 隔离范围（说准确）

本插件的 `data-*` 技能**只出现在选了「数据分析师」的会话里**，普通 Standard 会话看不到它们。

但反过来不成立：「数据分析师」会话里**还会**看到全局技能（`office*`、`memory` 等），因为岗位预设保留了 DSH 的技能文件系统与 Office 能力 —— 出报告、出表格正需要它们。所以这个预设是「Standard + 岗位技能 + 岗位人设」，不是封闭环境。

## 与上游的差异

- **中文优先**：上游模板偏英文，这里正文以中文为主，SQL / Python / 术语保留英文。
- **不绑订阅**：模型走 DSH 自己的路由，与 Claude 订阅无关。
- **交付物落地**：图表出 PNG 并用 `present` 交付；报告/表格走 `office` 技能产出 `.docx` / `.xlsx` / `.pptx`；查询另存 `.sql`。
- **工具名换成 DSH 实际能力**：不引用 Claude 专有工具。
- **作用域**：上游靠 marketplace 逐个安装；这里靠 preset 作用域隔离，切换岗位 = 切换模式，不用装卸。

## 目录结构

```
dsh-knowledge-work-data/     ← DSH bundle（安装这个目录）
  cordis.patch.yml           ← 「数据分析师」Agent 预设声明
  index.js                   ← 技能 provider
  assets/<skill>/SKILL.md    ← 10 个岗位技能
  locale/{zh,en}.json        ← 插件页显示文案
market-index/index.json      ← Discover 用的插件索引
LICENSE / NOTICE.md          ← Apache-2.0 合规
```

## 尚未实现

- 上游另外 10 个岗位（市场、销售、法务、财务、产品、客服、设计、工程、HR、运营）。复制 `dsh-knowledge-work-data/` 的结构即可扩展：新 `assets/` 技能 + 新 preset 声明。
- 连接器不会自动授权 —— 与上游一样，MCP 服务器需逐个配置。

## 许可与归属

本仓库是 [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)（Apache-2.0，Copyright Anthropic）的**衍生作品**。

- 完整的 Apache-2.0 许可证文本见 [LICENSE](LICENSE)。
- 修改说明与归属见 [NOTICE.md](NOTICE.md)。
- 每个衍生文件顶部都带有醒目的 `Modified from the original work by Anthropic.` 声明。

本作品与 Anthropic 无隶属或背书关系。「Claude」「Anthropic」为各自所有者的商标。
