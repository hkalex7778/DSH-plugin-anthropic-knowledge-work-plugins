---
name: data-create-viz
description: 当需要把查询结果、CSV/Excel 或粘贴的数据变成图表（趋势、对比、排名、分布、相关性、热力图）并以 PNG 交付时使用。内置图型选择指南、配色与可读性准则，并调用同目录 scripts/chart_pillow.py（纯 Pillow 渲染，无需 matplotlib/seaborn/plotly），中文标题与轴标签正常渲染。
---

# /data-create-viz - 创建数据图表

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

从数据生成出版级（publication-quality）图表：先选对图型，再套用设计与可读性准则，最后用捆绑 Python 脚本渲染 PNG 并以 `present` 交付。

## 关键环境事实（先读）

- 用 `load_workspace_dependencies` 获取捆绑 Python 的绝对路径，再用 `pwsh` 调用。
- 捆绑 Python **没有** matplotlib、seaborn、plotly、scipy、statsmodels、duckdb、sklearn、pyarrow；只有 numpy、pandas、Pillow、openpyxl、XlsxWriter、lxml、python-docx、python-pptx。
- 因此**不要写 matplotlib/seaborn/plotly 代码**。所有静态图表一律通过同目录脚本渲染：
  `assets/data-create-viz/scripts/chart_pillow.py`（纯 Pillow 实现，已实测中文渲染正常）。
- 交付图片一律用 `present` 工具，不要只在对话里贴文件路径。

## 工作流

### 1. 弄清需求

确定：

- **数据来源**：查询结果、粘贴的数据、CSV/Excel 文件，还是需要去取数
- **图型**：用户明确指定，还是需要你推荐（见第 3 步指南）
- **用途**：探索、汇报、报告配图、仪表盘组件
- **受众**：技术团队 / 高管 / 外部干系人（影响字号与对比度）

### 2. 拿到数据

- **若已配置数仓 / BI 类 MCP 服务器**（看当前会话可用工具里是否有对应查询工具）：直接写 SQL 取数，落成 CSV 再画图。
- **否则**：请用户上传 CSV/Excel，或把查询结果粘贴进来。不要假装有数据库连接。
- 数据在 pandas 里清洗（类型转换、缺失值处理）后，`to_csv` 落盘，供脚本读取。

### 3. 选对图型

| 你要表达的关系 | 首选图型 | 备选 | 对应 `--kind` |
|---|---|---|---|
| 时间趋势 | 折线图 | 面积图（累计/构成） | `line` |
| 类别对比 | 柱状图 | 类别多时用横向条形图 | `bar` / `hbar` |
| 排名 | 横向条形图 | 点图、坡度图（两期对比） | `hbar --sort` |
| 部分-整体构成 | 堆叠柱状图 | 华夫图；类别 <6 才考虑饼/环 | `stackbar` |
| 随时间的构成 | 堆叠面积/堆叠柱 | 100% 堆叠柱（看占比时） | `stackbar` |
| 分布 | 直方图 | 箱线图、小提琴图（无现成脚本，改用表格或文字描述） | `hist` |
| 双变量相关性 | 散点图 | 气泡图（第三变量映射大小） | `scatter` |
| 多变量相关矩阵 | 热力图 | 配对图 | `heat` |
| 两变量随时间对比 | 双折线 / 分组柱 | — | `line` / `bar`（多 `--y` 列） |
| 地理分布 | 分级统计地图 | —（脚本不支持，建议 HTML 仪表盘或说明限制） |
| 流量 / 过程 | Sankey 图 | 漏斗图（顺序阶段） | —（不支持，可降级为 hbar） |
| 实际 vs 目标 | 子弹图 | 仪表盘图（仅限单个 KPI） | —（不支持，可用 hbar+参考线注记） |

**什么时候不要用某种图：**

- **饼图**：除非类别 <6 且粗略比较即可。人眼不擅长比较角度，改用条形图。
- **3D 图**：永远不用。扭曲感知且不带新信息。
- **双轴图**：慎用，会暗示不存在的相关性；用则必须清楚标注两个轴。
- **多类别堆叠柱**：中间段没法比较。改用 small multiples（多张小图）或分组柱。
- **环形图**：比饼图略好但问题相同，最多用于展示单个 KPI。

### 4. 渲染图表

#### 方式 A：命令行（推荐，数据已在 CSV/XLSX 里）

脚本路径**不要用相对路径**——会话的 cwd 是用户工作区，不是插件目录。用本技能加载结果里那行「Base directory for this skill」：

```powershell
$skillDir = "<上面 Base directory 的绝对路径>"      # 例：...\assets\data-create-viz
$py  = "<load_workspace_dependencies 返回的 python.exe>"
& $py "$skillDir\scripts\chart_pillow.py" --kind line --csv data.csv --x month --y rev,cost --out trend.png --title "各期收入与成本趋势" --subtitle "单位：万元" --xlabel 月份 --ylabel "金额（万元）" --fmt currency
```

- `--kind`：`line` / `bar` / `hbar` / `stackbar` / `hist` / `scatter` / `heat`
- `--csv`、`--y` 必填；`--x` 除 `hist` 外必填
- `--x`：X 轴（类别/时间）列名；`--y`：数值列名，多列用逗号分隔
- `--fmt`：`number` / `currency` / `percent`（自动 1.5K/2.3M 紧凑格式）；`--symbol` 配 `currency` 的符号，默认 `¥`
- `--sort`：按数值**从大到小**排序（排名图用）。bar / hbar / stackbar 都是降序
- 可选 `--bins`（直方图分箱数）、`--note`（图脚注：数据来源与日期范围）
- 特例：
  - `hist`：`--y` 传要分箱的那一数值列
  - `scatter`：`--x`/`--y` 各传一个数值变量
  - `heat`：`--x` 传列维度，`--y` 传 `数值列,行维度列`（两列，逗号分隔）

#### 方式 B：编程调用（需要自定义热力图行列顺序、非 CSV 来源时）

```python
from chart_pillow import save_chart  # 需把 scripts 目录加入 sys.path 或在其下运行
save_chart("hbar", rows, x="category", y="metric", out="rank.png",
           title="NPS 排名（2024 Q4）", subtitle="样本 n=1,240",
           ylabel="NPS", yfmt="number", sort=True, note="数据来源：客服系统导出，2024-12-31")
```

签名：`save_chart(kind, rows, x, y, out, title='', subtitle='', xlabel='', ylabel='', yfmt='number', width=980, height=560, sort=False, stacked=False, bins=30, note=None, xorder=None, yorder=None)`。`rows` 接受 `list[dict]` 或 pandas DataFrame；`xorder`/`yorder` 仅对 `heat` 生效，可显式指定行列类别顺序（如月份序）。堆叠柱直接用 CLI 的 `--kind stackbar`，不必走编程接口。

需要 matplotlib 才能做的图（箱线图、Sankey、地图等）：如实告知用户当前环境不支持，提出用 `data-build-dashboard` 技能产出 HTML 交互图，或以表格 + 文字结论替代。

### 5. 套用设计准则

**配色（Color）**

- 颜色编码数据，不做装饰；脚本内置色盲友好分类色板（`#4C72B0 #DD8452 #55A868 #C44E52 #8172B3 #937860`），超过 6-8 个类别会开始混淆，先合并或改 small multiples
- 强调主结论：关键序列用亮色，参考数据灰化
- 有序数值用单色渐变（浅→深）；有语义中心点的用双色调渐变
- 不要只靠红/绿区分：约 8% 男性红绿色弱，首选蓝/橙组合

**文字（Typography）**

- **标题写结论，不只写指标**：「收入同比增长 23%」优于「各月收入」
- 副标题补上下文：时间范围、筛选条件、单位、数据来源
- 轴标签必须带单位；能避免就避免旋转 90°
- 关键数据点加数值标签，不必每根柱子都标

**布局（Layout）**

- 去掉图表垃圾：不承载信息的网格线、边框、背景一律删
- 类别按数值排序（`--sort`），除非有天然顺序（月份、阶段）
- 时间序列宽高比 3:1～2:1；对比图可以更接近方形
- 留白是好事，别让图挤在一起

**准确性（Accuracy）**

- 柱状图 Y 轴必须从零开始（脚本已强制）；折线图可以不从零开始，当波动范围才是重点时
- 不做无标注的断轴
- 多面板对比时保持同一刻度
- 精度适中：不要显示 10 位小数
- 数据不确定时展示不确定性（区间、范围），并标注样本量

**无障碍清单（发布前自检）**

- [ ] 不靠颜色也能读懂（线型、直接标注区分序列）
- [ ] 正常缩放下文字可读（标签 ≥10pt、标题 ≥12pt 等效）
- [ ] 标题描述的是洞察，不只是数据
- [ ] 轴标签带单位
- [ ] 图例清晰且不遮挡数据
- [ ] 图注里写明数据来源与日期范围（用 `--note`）

### 6. 交付

1. PNG 用描述性文件名保存在工作区（如 `trend_revenue_12m.png`）
2. 用 `present` 工具交付该文件
3. 简述图上能看出的 1-2 个结论
4. 主动提议变体：换图型、换分组维度、缩放时间范围、导出为仪表盘（转 `/data-build-dashboard`）

## 示例

```
/data-create-viz 把最近 12 个月的月度收入画成折线图，标出趋势
/data-create-viz 这是我们各产品的 NPS 数据：[粘贴数据]。按分数排名画横向条形图
/data-create-viz 用 orders 查询结果画「星期 × 小时」订单量热力图
```

## 提示

- 想要**交互式**图表（悬停、缩放、筛选）：本技能只出静态 PNG；请改用 `data-build-dashboard`（HTML + Chart.js，浏览器打开即交互）。
- 汇报用途请说明，会加大字号、提高对比度。
- 多张图就多次调用脚本，每张一个 PNG，一起 `present`。
