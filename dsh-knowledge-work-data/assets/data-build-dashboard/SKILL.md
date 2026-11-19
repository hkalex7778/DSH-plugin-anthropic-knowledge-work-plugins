---
name: data-build-dashboard
description: 当需要把一个或多个数据主题做成可交互的 HTML 仪表盘（KPI 卡片、Chart.js 图表、下拉/日期筛选、可排序明细表）时使用。产出单个自包含 .html 文件，数据内联为 JS 常量，用户浏览器直接打开即可，无需本地 Python 绘图库；用 present 交付。
---

# /data-build-dashboard - 构建交互式 HTML 仪表盘

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

构建**单个自包含 HTML 文件**的交互仪表盘：图表、筛选器、表格、专业样式。浏览器直接打开即用，不需要服务器。静态 PNG 图表请用 `data-create-viz`；本技能负责「可点、可筛、可悬停」的交付物。

## 为什么这条路在 DSH 里可行

捆绑 Python 没有 matplotlib/plotly，但仪表盘不依赖它们：图表由浏览器里的 **Chart.js（CDN 引入）** 渲染，Python 端只用 pandas（捆绑已有）做数据清洗与聚合。所以方案与上游一致，原样保留。

**离线提醒**：CDN 脚本需要联网。若用户要完全离线打开，把 Chart.js 源码内联进 `<script>` 标签（用 `web_fetch` 拉取 CDN 文件后嵌入，或提示用户放到同目录改相对路径引用），交付前说明差异。

## 工作流

### 1. 弄清需求

- **用途**：高管总览 / 运营监控 / 专题分析 / 团队周报
- **受众**：谁会打开这个文件
- **核心指标**：哪些数字最重要（进 KPI 卡）
- **维度**：用户要按什么筛选（地区、品类、时间段）
- **数据来源**：见下步

### 2. 取数并内联

- **若已配置数仓 / BI 类 MCP 服务器**：直接查询取数。
- **否则**：请用户上传 CSV/Excel 或粘贴查询结果；只给了描述没给数据时，造一份贴合 schema 的示例数据，并在页面显著位置标注「示例数据」+ 写明替换真实数据的方法。

**「数据内联进 HTML」的具体做法**（核心步骤）：用捆绑 Python 把 CSV 转成 JS 常量再嵌入模板——

```python
import json, pandas as pd
df = pd.read_csv("orders.csv")
# 模板消费的字段名固定为 date / region / product / revenue / orders
# —— 聚合结果的列名必须与它们一致，否则 KPI 会静默变成 0。
need = ["date", "region", "product", "revenue", "orders"]
df = df.rename(columns={"rev": "revenue"})          # 按你的原始列名映射过来
missing = [c for c in need if c not in df.columns]
if missing:
    raise SystemExit(f"数据缺少模板需要的列：{missing}；请改列名或改模板，不要硬塞空值")
# 小表：整表内联
DATA = json.dumps(df[need].to_dict("records"), ensure_ascii=False)
html = TEMPLATE.replace("__DATA__", DATA)  # TEMPLATE 里写 const RAW_DATA = __DATA__;
open("sales_dashboard.html", "w", encoding="utf-8").write(html)
```

要点：`ensure_ascii=False` 保留中文；用 `json.dumps` 而不是手写，避免引号转义事故；日期列转成 `"YYYY-MM-DD"` 字符串以便 `<input type="date">` 比较。

### 3. 布局

```
┌──────────────────────────────────────────────────┐
│ 标题                                 [筛选器 ▼]  │
├───────────┬───────────┬───────────┬──────────────┤
│ KPI 卡片  │ KPI 卡片  │ KPI 卡片  │ KPI 卡片     │
├───────────┴───────────┬───────────┴──────────────┤
│   主图（最大面积）     │   次图                    │
├───────────────────────┴──────────────────────────┤
│   明细表（可排序、可滚动）                        │
└──────────────────────────────────────────────────┘
```

顶部 2-4 张 KPI 卡、中部 1-3 张图、底部可选明细表；筛选器放头部或侧栏。

### 4. 写文件

单文件结构：语义化 HTML5 + CSS Grid 响应式布局 + 内联 `<style>` + CDN Chart.js + 内联数据与逻辑。以下模板是**完整可用的骨架**（上游片段在本机抓取时被剥离，此处分页版按上游 CSS/JS 重写并补齐）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>销售概览仪表盘</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
:root{--bg:#f8f9fa;--card:#fff;--head:#1a1a2e;--t1:#212529;--t2:#6c757d;
--pos:#28a745;--neg:#dc3545;--gap:16px;--r:8px;
--c1:#4C72B0;--c2:#DD8452;--c3:#55A868;--c4:#C44E52;--c5:#8172B3;--c6:#937860}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Microsoft YaHei',sans-serif;background:var(--bg);color:var(--t1);line-height:1.5}
.wrap{max-width:1400px;margin:0 auto;padding:var(--gap)}
header{background:var(--head);color:#fff;padding:20px 24px;border-radius:var(--r);margin-bottom:var(--gap);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
header h1{font-size:20px;font-weight:600}
.filters{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.filters label{font-size:12px;color:rgba(255,255,255,.7)}
.filters select,.filters input[type=date]{padding:6px 10px;border:1px solid rgba(255,255,255,.2);border-radius:4px;background:rgba(255,255,255,.1);color:#fff;font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.kpi{background:var(--card);border-radius:var(--r);padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.kpi .l{font-size:13px;color:var(--t2);letter-spacing:.5px;text-transform:uppercase}
.kpi .v{font-size:28px;font-weight:700}
.kpi .d{font-size:13px;font-weight:500}.kpi .d.up{color:var(--pos)}.kpi .d.down{color:var(--neg)}
.charts{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:var(--gap);margin-bottom:var(--gap)}
.panel{background:var(--card);border-radius:var(--r);padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.panel h3{font-size:14px;font-weight:600;margin-bottom:16px}
.panel canvas{max-height:300px}
.table-sec{background:var(--card);border-radius:var(--r);padding:20px 24px;box-shadow:0 1px 3px rgba(0,0,0,.08);overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
thead th{text-align:left;padding:10px 12px;border-bottom:2px solid #dee2e6;color:var(--t2);font-size:12px;text-transform:uppercase;cursor:pointer;user-select:none;white-space:nowrap}
tbody td{padding:10px 12px;border-bottom:1px solid #f0f0f0}
tbody tr:hover{background:var(--bg)}
@media(max-width:768px){header{flex-direction:column;align-items:flex-start}.kpis{grid-template-columns:repeat(2,1fr)}.charts{grid-template-columns:1fr}}
@media print{body{background:#fff}.filters{display:none}.panel{break-inside:avoid}.kpi{border:1px solid #dee2e6;box-shadow:none}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>销售概览 <small id="stamp" style="font-weight:400;opacity:.7"></small></h1>
    <div class="filters">
      <label>地区 <select id="f-region"><option value="all">全部</option></select></label>
      <label>从 <input type="date" id="f-from"></label>
      <label>至 <input type="date" id="f-to"></label>
    </div>
  </header>
  <div class="kpis">
    <div class="kpi"><div class="l">总收入</div><div class="v" id="k-rev">–</div><div class="d" id="k-rev-change"></div></div>
    <div class="kpi"><div class="l">订单数</div><div class="v" id="k-orders">–</div><div class="d" id="k-orders-change"></div></div>
    <div class="kpi"><div class="l">客单价</div><div class="v" id="k-aov">–</div><div class="d"></div></div>
  </div>
  <div class="charts">
    <div class="panel"><h3>月度收入与成本趋势</h3><canvas id="c-trend"></canvas></div>
    <div class="panel"><h3>各地区收入排名</h3><canvas id="c-region"></canvas></div>
  </div>
  <div class="table-sec"><h3 style="font-size:14px;margin-bottom:12px">明细</h3><table id="tbl"></table></div>
</div>
<script>
const COLORS = ['#4C72B0','#DD8452','#55A868','#C44E52','#8172B3','#937860'];
const RAW_DATA = __DATA__;   // Python 注入的行对象数组：[{date,region,product,revenue,orders}, ...]
let filtered = RAW_DATA, charts = {};

// 显式失败：数据没注入或列名不对时，页面顶部红字说清楚，而不是静默显示 0。
(function guard(){
  const need = ['date','region','product','revenue','orders'];
  const why = !Array.isArray(RAW_DATA) || RAW_DATA.length === 0
    ? 'RAW_DATA 为空：Python 内联步骤没跑成功（__DATA__ 未被替换，或聚合结果为空）。'
    : (need.some(k => !(k in RAW_DATA[0]))
        ? '字段名不匹配：模板需要 ' + need.join('/') + '，实际是 ' + Object.keys(RAW_DATA[0]).join('/') + '。'
        : null);
  if (why) document.body.insertAdjacentHTML('afterbegin',
    '<div style="background:#C44E52;color:#fff;padding:10px 14px;font:13px system-ui">' + why + '</div>');
})();

function fmt(v, kind='number'){
  if(kind==='percent') return v.toFixed(1)+'%';
  const a=Math.abs(v);
  if(a>=1e6) return (v/1e6).toFixed(1)+'M';
  if(a>=1e3) return (v/1e3).toFixed(1)+'K';
  return kind==='currency' ? '¥'+v.toLocaleString(undefined,{maximumFractionDigits:0}) : v.toLocaleString();
}
const sum = (rows,k)=>rows.reduce((s,r)=>s+(+r[k]||0),0);
const groupSum = (rows,key,val)=>{const m={};rows.forEach(r=>m[r[key]]=(m[r[key]]||0)+(+r[val]||0));return m;};

function applyFilters(){
  const region = document.getElementById('f-region').value;
  const from = document.getElementById('f-from').value, to = document.getElementById('f-to').value;
  filtered = RAW_DATA.filter(r=>{
    if(region!=='all' && r.region!==region) return false;
    if(from && r.date<from) return false;
    if(to && r.date>to) return false;
    return true;
  });
  renderKPIs(); renderCharts(); renderTable();
}
function renderKPIs(){
  document.getElementById('k-rev').textContent = fmt(sum(filtered,'revenue'),'currency');
  document.getElementById('k-orders').textContent = fmt(sum(filtered,'orders'));
  const o=sum(filtered,'orders')||1;
  document.getElementById('k-aov').textContent = fmt(sum(filtered,'revenue')/o,'currency');
}
function upsert(id, cfg){ if(charts[id]) charts[id].destroy(); charts[id]=new Chart(document.getElementById(id), cfg); }
function renderCharts(){
  const byM = {};   // 按 'YYYY-MM' 聚合（直接取自 date 列，无需单独月份列）
  filtered.forEach(r=>{const m=String(r.date).slice(0,7); byM[m]=(byM[m]||0)+(+r.revenue||0);});
  const labels = Object.keys(byM).sort();
  upsert('c-trend', {type:'line', data:{labels, datasets:[{label:'收入', data:labels.map(l=>byM[l]),
      borderColor:COLORS[0], backgroundColor:COLORS[0]+'20', fill:true, tension:.3, pointRadius:3}]},
    options:{responsive:true, maintainAspectRatio:false,
      plugins:{legend:{position:'top',labels:{usePointStyle:true}}},
      scales:{x:{grid:{display:false}}, y:{beginAtZero:true, ticks:{callback:v=>fmt(v,'currency')}}}}});
  const byR = groupSum(filtered,'region','revenue');
  const rl = Object.keys(byR).sort((a,b)=>byR[b]-byR[a]);
  upsert('c-region', {type:'bar', data:{labels:rl, datasets:[{label:'收入', data:rl.map(r=>byR[r]),
      backgroundColor:COLORS[0]+'CC', borderRadius:4}]},
    options:{indexAxis: rl.length>8?'y':'x', responsive:true, maintainAspectRatio:false,
      plugins:{legend:{display:false}}, scales:{x:{beginAtZero:true}}}});
}
let sortCol='revenue', sortDir=-1;
function renderTable(){
  const cols=[['date','日期','date'],['region','地区','s'],['product','产品','s'],['revenue','收入','currency'],['orders','订单','n']];
  const rows=[...filtered].sort((a,b)=>{const x=a[sortCol],y=b[sortCol];return (x<y?-1:x>y?1:0)*sortDir;});
  const page=rows.slice(0,200);
  let h='<thead><tr>'+cols.map(c=>`<th onclick="sortBy('${c[0]}')">${c[1]}${sortCol===c[0]?(sortDir<0?' ▼':' ▲'):''}</th>`).join('')+'</tr></thead><tbody>';
  page.forEach(r=>h+='<tr>'+cols.map(c=>`<td>${c[2]==='currency'?fmt(r[c[0]],'currency'):c[2]==='n'?fmt(r[c[0]]):r[c[0]]}</td>`).join('')+'</tr>');
  document.getElementById('tbl').innerHTML=h+'</tbody>';
}
window.sortBy=f=>{ if(sortCol===f) sortDir=-sortDir; else {sortCol=f; sortDir=-1;} renderTable(); };

function initFilters(){
  const sel=document.getElementById('f-region');
  [...new Set(RAW_DATA.map(r=>r.region))].sort().forEach(v=>{const o=document.createElement('option');o.value=o.textContent=v;sel.appendChild(o);});
  sel.onchange=applyFilters;
  document.getElementById('f-from').onchange=applyFilters;
  document.getElementById('f-to').onchange=applyFilters;
  document.getElementById('stamp').textContent='数据截至 '+RAW_DATA.reduce((m,r)=>r.date>m?r.date:m,'');
}
initFilters(); applyFilters();
</script>
</body>
</html>
```

**图表选型（Chart.js）**：折线=时间趋势；柱=类别对比；堆叠柱=随时间构成；doughnut=占比（仅 <6 类，`cutout:'60%'`）；bar+line 混合=量+率。配色用上表分类色板，饼图 tooltip 里带百分比。doughnut 示例：

```javascript
new Chart(ctx, {type:'doughnut', data:{labels, datasets:[{data, backgroundColor:COLORS.map(c=>c+'CC'), borderColor:'#fff', borderWidth:2}]},
  options:{cutout:'60%', plugins:{legend:{position:'right'}, tooltip:{callbacks:{label:c=>{
    const t=c.dataset.data.reduce((a,b)=>a+b,0);
    return `${c.label}: ${fmt(c.parsed)} (${(c.parsed/t*100).toFixed(1)}%)`;}}}}}});
```

### 5. 大数据量守则

| 数据规模 | 做法 |
|---|---|
| <1,000 行 | 原表直接内联，全交互 |
| 1,000–10,000 行 | 可内联；图表数据先用 pandas 预聚合 |
| 10,000–100,000 行 | 只内联聚合结果（KPI、分组汇总），不内联原表 |
| >100,000 行 | 不适合客户端仪表盘；建议 BI 工具或分页静态报告 |

其他：折线每序列 <500 点（超出抽样）；柱状 <50 类；散点 ≤1,000 点；多图仪表盘设 `animation:false`；表格只渲染前 100–200 行 + 分页控件（「显示 1–50，共 2,340」）。

### 6. 保存与交付

1. `write` 保存为单个 `.html`（描述性文件名，如 `sales_dashboard.html`）
2. 用 `present` 交付；告知用户浏览器直接打开
3. 说明：筛选器怎么用、数据截至日期、如何替换数据（重跑第 2 步的内联脚本即可）
4. 提醒：文件里的图表依赖 CDN；完全离线场景见开头「离线提醒」

## 示例

```
/data-build-dashboard 月度销售仪表盘：收入趋势、Top 产品、地区拆分，数据在 orders.csv
/data-build-dashboard [粘贴 CSV] 做工单仪表盘：按优先级的量、响应时间趋势、解决率
/data-build-dashboard 给 SaaS 公司做高管仪表盘模板：MRR、流失、新客、NPS，用示例数据
```

## 提示

- 产物就是单个 HTML，发给任何人都能打开——它是**时点快照**，不是实时看板；要实时请接 BI 工具。
- 用户要「深色模式 / 演示模式 / 品牌配色」时，改 `:root` CSS 变量即可。
- 静态图片版（贴 PPT/报告用）转 `data-create-viz` 出 PNG。
