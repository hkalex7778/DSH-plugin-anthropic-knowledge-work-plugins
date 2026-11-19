---
name: data-statistical-analysis
description: 统计学方法知识库：描述统计、趋势与季节性分析、移动平均、同比环比、离群值/异常检测（IQR、z-score）、假设检验（t、卡方、比例 z、ANOVA、Mann-Whitney）、相关与回归，以及在无 scipy/statsmodels 的捆绑 Python 中用 numpy/pandas 手写等价计算的方法与近似局限。供分析类技能引用；分析分布、判断显著性、检测异常、算相关性或解读统计结论时使用。
user-invocable: false
---

> Modified from the original work by Anthropic.
> 移植自 anthropics/knowledge-work-plugins (data 插件, Apache-2.0)，正文已本地化并适配 DeepSeek Harness 工具。

# 统计分析（知识型技能）

描述统计、趋势分析、离群值检测、假设检验，以及对统计主张何时该谨慎的指导。

## 环境硬约束（先读）

先调 `load_workspace_dependencies` 拿捆绑 Python 路径，用 `pwsh` 执行。捆绑环境**只有** numpy 2.3.5 / pandas 3.0.1（外加 Pillow、openpyxl、lxml、python-docx、python-pptx）。

**没有 scipy、statsmodels、sklearn、matplotlib、seaborn、duckdb、pyarrow。**

因此：

- 描述统计、趋势、移动平均、同比环比、离群值检测（IQR / z-score）、相关性系数、简单线性回归的**点估计**——numpy/pandas 完全够用，照常用。
- **精确 p 值与分布分位数**需要分布函数。本文件下方给出可直接使用的手写实现（基于 `math.erf` 与不完全 Beta/Gamma 连分式）。这些实现**已在本机 numpy/pandas 环境实测通过**，与已知参考值一致。
- 需要更严格的东西（多重比较的精确校正、非中心分布、混合效应模型、bootstrap 置信区间的工业级实现、时间序列 ARIMA）时**别硬凑**：明确告诉用户这超出可计算范围，建议 `pip install scipy statsmodels` 到自备环境后重跑，或直接升级为「交给数据科学家」。
- 画图用 `assets/data-create-viz/scripts/chart_pillow.py`（纯 Pillow），不要 `import matplotlib`。

诚实原则：**近似就是近似**。报告里要写清用的是近似算法与其误差量级，不要假装 numpy 原生能算所有分布。

## 描述统计方法论

### 集中趋势

| 情形 | 用什么 | 为什么 |
|---|---|---|
| 对称分布、无离群值 | Mean | 最有效的估计量 |
| 偏态分布 | Median | 对离群值稳健 |
| 类别 / 有序数据 | Mode | 非数值唯一选择 |
| 高偏态带离群（如人均收入） | Median + Mean 并报 | 二者差距体现偏度 |

**业务指标永远 mean 与 median 一起报。** 差距明显就说明数据有偏，只报 mean 会误导。

### 离散与变异

- **标准差**：偏离均值的典型距离，配近正态数据用。
- **四分位距 IQR**：p25 到 p75，对离群稳健，配偏态数据用。
- **变异系数 CV**：std/mean，跨量纲比较离散度。
- **极差**：max−min，对离群敏感但可快速感知数据跨度。

### 业务语境下的分位数

```
p1  底部 1%（地板 / 最小典型值）
p5  正常区间低端
p25 第一四分位
p50 中位数（典型用户）
p75 第三四分位
p90 顶部 10% / 重度用户
p95 正常区间高端
p99 顶部 1% / 极端用户
```

**叙事示例**：「会话时长中位数 4.2 分钟，但前 10% 用户单次超 22 分钟，把均值拉高到 7.8 分钟。」

### 描述一个分布

对每个分析的数值分布刻画：**形态**（正态 / 右偏 / 左偏 / 双峰 / 均匀 / 重尾）、**中心**（mean 与 median 及差距）、**离散**（std 或 IQR）、**离群值**（多少个、多极端）、**边界**（是否有自然下限 0 或上限 100%）。

```python
import pandas as pd, numpy as np

def describe(s: pd.Series) -> dict:
    """描述统计 + 简易形态判断（纯 pandas/numpy，无需 scipy）。"""
    s = pd.to_numeric(s, errors="coerce").dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    skew = ((s - s.mean()) ** 3).mean() / s.std(ddof=0) ** 3   # 样本偏度（numpy 无内置 skew）
    if abs(skew) < 0.5:   shape = "近似对称"
    elif skew > 1:        shape = "强右偏"
    elif skew > 0.5:      shape = "右偏"
    elif skew < -1:       shape = "强左偏"
    else:                 shape = "左偏"
    return {
        "n": int(s.size), "mean": s.mean(), "median": s.median(),
        "std": s.std(ddof=1), "cv": s.std(ddof=1) / s.mean() if s.mean() else float("nan"),
        "min": s.min(), "max": s.max(),
        "p1": s.quantile(0.01), "p5": s.quantile(0.05), "q1": q1, "q3": q3,
        "p95": s.quantile(0.95), "p99": s.quantile(0.99),
        "skew": skew, "shape": shape,
        "outliers_iqr": int(((s < lo) | (s > hi)).sum()),
    }
```

## 趋势分析与预测

### 识别趋势

**移动平均**平滑噪声：

```python
df["ma_7d"] = df["metric"].rolling(window=7, min_periods=1).mean()    # 日数据配周季节性
df["ma_28d"] = df["metric"].rolling(window=28, min_periods=1).mean()  # 平滑周 + 月模式
```

**期间对比**：WoW（上周同日）、MoM（上月）、YoY（季节性业务金标准）、same-day-last-year。

**增长率**：

```
简单增长: (current - previous) / previous
CAGR:    (ending / beginning) ** (1 / years) - 1
对数增长: ln(current / previous)   # 波动大的序列更稳
```

```python
s = df.set_index("date")["metric"]
yoy = s.pct_change(periods=365)                 # 日频数据同比（需满一年）
mom = s.resample("ME").last().pct_change(1)     # 月环比
cagr = (end / begin) ** (1 / years) - 1
```

### 季节性检测

1. 先看原始序列（用 `chart_pillow.py` 出 line 图）——先目视
2. 算星期几均值：有明显周模式吗？
3. 算月份均值：有年周期吗？
4. 对比期间时优先 YoY 或同期对比，别把趋势和季节性混为一谈

### 预测（简单方法）

给业务分析师用的直白方法：**朴素预测**（明天=今天，作基线）、**季节朴素**（明天=上周/去年同日）、**线性趋势**（只对明显线性的趋势拟合）、**移动平均预测**（用尾部均值）。

```python
import numpy as np
slope, intercept = np.polyfit(np.arange(len(y)), y, 1)   # 一次线性拟合，够用
# 残差区间代替置信区间：
resid = y - (intercept + slope * np.arange(len(y)))
band = 1.96 * resid.std(ddof=1)     # 近似：±1.96 倍残差标准差，非精确预测区间
```

**必须传达不确定性**，给区间不给点值：「按近 3 个月趋势，下月注册预计 1.0 万–1.2 万」，而不是「下月将正好有 11,234 个注册」。

**该升级给数据科学家的信号**：非线性趋势、多重季节性、外部因素（营销投放、节假日）、或预测精度直接影响资源分配。

## 离群值与异常检测

### 统计方法

**z-score 法**（近正态数据）：

```python
z = (df["value"] - df["value"].mean()) / df["value"].std()
outliers = df[z.abs() > 3]           # 超过 3 个标准差
```

注意小样本局限：n 较小时 |z| 有理论上界 `(n-1)/sqrt(n)`（n=10 时约 2.85），所以「|z|>3」在小样本里可能永远不触发，此时改用 IQR 法。

**IQR 法**（对非正态稳健）：

```python
q1, q3 = df["value"].quantile(0.25), df["value"].quantile(0.75)
iqr = q3 - q1
lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
outliers = df[(df["value"] < lower) | (df["value"] > upper)]
```

**分位法**（最简）：

```python
outliers = df[(df["value"] < df["value"].quantile(0.01)) | (df["value"] > df["value"].quantile(0.99))]
```

### 处理离群值

**不要自动删除**。先：① **调查**——是数据错误、真实极端值、还是另一个总体？② **数据错误**：修或删（负年龄、1970 年的时间戳）。③ **真实极端**：保留，但改用稳健统计（median 取代 mean）。④ **不同总体**：单独切出来分别分析（如企业客户 vs 中小客户）。

**报告你做了什么**：「剔除了 47 条（0.3%）交易金额 > $50K 的记录，它们是企业批量订单，已单独分析。」

### 时间序列异常检测

1. 算期望值（移动平均 或 去年同期）
2. 算实际对期望的偏离
3. 超出阈值就标记（通常是残差的 2–3 倍标准差）
4. 区分点异常（单点异常值）与变点（持续位移）

```python
expected = s.rolling(28, min_periods=7).mean()
resid = (s - expected).dropna()
flag = (s - expected).abs() > 3 * resid.std(ddof=1)
```

## 假设检验基础

### 何时用

需要判断观察到的差异是真实的还是随机波动时：A/B 测试结果、改动前后对比、分组差异（企业客户留存真的高吗）。

### 框架

1. **原假设 H0**：无差异（默认假设）
2. **备择假设 H1**：有差异
3. **选显著性水平 α**：通常 0.05（5% 假阳性概率）
4. **算检验统计量与 p 值**
5. **解读**：p < α 则拒绝 H0（有真实差异的证据）

### 常用检验

| 场景 | 检验 | 适用条件 |
|---|---|---|
| 比两组均值 | 独立样本 t 检验 | 近正态、两组 |
| 比两组比例 | 比例 z 检验 | 转化率、二元结果 |
| 同实体前后配对 | 配对 t 检验 | 同对象 before/after |
| 比 3+ 组均值 | ANOVA | 多分组 / 多变体 |
| 非正态两组 | Mann-Whitney U | 偏态指标、有序数据 |
| 类别间关联 | 卡方检验 | 两个分类变量 |
| 两连续变量关联 | Pearson r 的 t 检验 | 近正态、线性 |

### 手写分布函数（已实测，直接复制使用）

无 scipy 时的等价实现。核心是两个特殊函数，其余检验都建立在它们之上：

```python
import math

def norm_cdf(z):
    """标准正态 CDF，math.erf 精确计算。"""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def norm_p_two_sided(z):
    """双侧正态 p 值；erfc 在大 z 时不丢精度。"""
    return math.erfc(abs(z) / math.sqrt(2.0))

def norm_ppf(p, lo=-9.9, hi=9.9):
    """标准正态分位数（逆 CDF）：对精确 CDF 二分求根，误差 < 1e-6。
    例：norm_ppf(0.975) = 1.959964"""
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if norm_cdf(mid) < p: lo = mid
        else: hi = mid
    return 0.5 * (lo + hi)

def _betacf(a, b, x, maxit=300, eps=3e-13):
    """不完全 Beta 的连分式（Lentz 法）。"""
    FPMIN = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, maxit + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps: break
    return h

def betainc(a, b, x):
    """正则化不完全 Beta 函数 I_x(a,b)。"""
    if x <= 0.0: return 0.0
    if x >= 1.0: return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log1p(-x) + a * math.log(x)) * _betacf(b, a, 1.0 - x) / b

def _gammainc_P(a, x, maxit=500, eps=3e-13):
    """正则化下不完全 Gamma P(a,x)：x<a+1 用级数，否则用连分式。"""
    if x == 0: return 0.0
    FPMIN = 1e-300
    if x < a + 1.0:
        term = s = 1.0 / a
        for n in range(1, maxit):
            term *= x / (a + n)
            s += term
            if abs(term) < abs(s) * eps: break
        return s * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b0 = x + 1.0 - a
    c, d = 1.0 / FPMIN, 1.0 / b0
    h = d
    for i in range(1, maxit):
        an = -i * (i - a)
        b0 += 2.0
        d = an * d + b0
        if abs(d) < FPMIN: d = FPMIN
        c = b0 + an / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < eps: break
    return 1.0 - math.exp(-x + a * math.log(x) - math.lgamma(a)) * h

def t_p_two_sided(t, df):
    """学生 t 双侧 p 值（精确到连分式收敛，非近似查表）。"""
    return betainc(df / 2.0, 0.5, df / (df + t * t))

def f_p_one_sided(F, d1, d2):
    """F 分布右尾 p 值（ANOVA / 回归整体 F 检验）。"""
    if F <= 0: return 1.0
    return betainc(d2 / 2.0, d1 / 2.0, d2 / (d2 + d1 * F))

def chi2_p_right_tail(x, df):
    """卡方分布右尾 p 值。"""
    return 1.0 - _gammainc_P(df / 2.0, x / 2.0)
```

上述实现是标准的数值算法（与 scipy 底层同源思路），实测与已知参考值一致：`t_p_two_sided(2.228, 10) ≈ 0.0500`、`chi2_p_right_tail(3.8415, 1) ≈ 0.05`、`f_p_one_sided(3.3541, 2, 27) ≈ 0.049`、`norm_ppf(0.975) ≈ 1.959964`。

> 说明：这些函数给出**分布的 p 值**，不检验数据是否满足检验前提（正态性、方差齐性）。前提不满足时结论本身就不牢，见下方「谨慎清单」与 Mann-Whitney 备选。

### 各检验的手写实现

**两比例 z 检验**（转化率对比，无 scipy 完全精确）：

```python
def two_prop_ztest(x1, n1, x2, n2):
    """合并方差 z 检验 + 差值 95% CI。实测 x=100/1000 vs 130/1000 -> z=2.1027, p=0.0355."""
    p1, p2 = x1 / n1, x2 / n2
    pp = (x1 + x2) / (n1 + n2)
    se_pool = math.sqrt(pp * (1 - pp) * (1 / n1 + 1 / n2))
    z = (p2 - p1) / se_pool
    se_unp = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    ci = (p2 - p1 - 1.959964 * se_unp, p2 - p1 + 1.959964 * se_unp)
    return z, norm_p_two_sided(z), ci
```

**Welch t 检验**（两组均值，不假设方差齐性；p 值靠上面的 `t_p_two_sided`）：

```python
def welch_ttest(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    na, nb = a.size, b.size
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se2 = va / na + vb / nb
    t = (b.mean() - a.mean()) / math.sqrt(se2)
    df = se2 ** 2 / ((va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))
    return t, df, t_p_two_sided(abs(t), df)
```

**配对 t 检验**：

```python
def paired_ttest(d):
    """d = 每对的前后差值。"""
    d = np.asarray(d, float); n = d.size
    t = d.mean() / (d.std(ddof=1) / math.sqrt(n))
    return t, n - 1, t_p_two_sided(abs(t), n - 1)
```

**卡方独立性检验**：

```python
def chi2_independence(obs):
    """obs = 观测频数二维数组。实测 [[10,90],[30,70]] -> chi2=12.5, dof=1, p≈0.00041."""
    obs = np.asarray(obs, float)
    exp = np.outer(obs.sum(1), obs.sum(0)) / obs.sum()
    stat = ((obs - exp) ** 2 / exp).sum()
    dof = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    return stat, dof, chi2_p_right_tail(stat, dof)
```

小样本提醒：期望频数 < 5 的格子过多时卡方近似不可靠，pandas 里可改 Fisher 精确检验——**但 Fisher 的精确 p 值这里算不动（需要超几何级数累加，且数值不稳），建议 `pip install scipy` 或改用更大样本**。

**单因素 ANOVA**（3+ 组均值）：

```python
def anova_f(*groups):
    g = [np.asarray(x, float) for x in groups]
    k, n = len(g), sum(len(x) for x in g)
    grand = np.concatenate(g).mean()
    ssb = sum(len(x) * (x.mean() - grand) ** 2 for x in g)
    ssw = sum(((x - x.mean()) ** 2).sum() for x in g)
    F = (ssb / (k - 1)) / (ssw / (n - k))
    return F, k - 1, n - k, f_p_one_sided(F, k - 1, n - k)
```

（本环境无 `scipy.stats.f_oneway`，上面等价。事后两两比较要自己做 Bonferroni：把每对 Welch t 的 p 乘以比较次数。）

**Mann-Whitney U**（偏态 / 有序数据；用正态近似 + 结点校正）：

```python
def mannwhitney_u(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    n1, n2 = a.size, b.size
    allv = np.concatenate([a, b])
    ranks = pd.Series(allv).rank(method="average").to_numpy()
    U1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    U2 = n1 * n2 - U1
    U = min(U1, U2)
    _, counts = np.unique(allv, return_counts=True)
    ties = counts[counts > 1].astype(float)
    N = n1 + n2
    sU = math.sqrt(n1 * n2 / 12.0 * ((N + 1) - (ties ** 3 - ties).sum() / (N * (N - 1.0))))
    if sU == 0: return U1, U2, float("nan"), float("nan")
    z = (U - n1 * n2 / 2) / sU
    return U1, U2, z, norm_p_two_sided(z)
```

**局限必须说清**：这是**正态近似**的 Mann-Whitney，未做精确分布。n1、n2 都 ≥ 10 时结果可靠；小样本时 p 值偏差可能明显（scipy 的精确版会给出更大/更保守的 p）。报告时写「Mann-Whitney U（正态近似）」，别写成精确检验。

### 相关与回归

```python
def pearson_p(x, y):
    """Pearson r 及其显著性（t 检验，dof=n-2）。"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = x.size
    r = np.corrcoef(x, y)[0, 1]
    t = r * math.sqrt((n - 2) / max(1e-12, 1 - r * r))
    return r, t_p_two_sided(abs(t), n - 2)

def ols_simple(x, y):
    """一元线性回归：系数、标准误、t、p、R^2。用 np.linalg，不需要 statsmodels。"""
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = x.size
    X = np.column_stack([np.ones(n), x])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    resid = y - X @ beta
    dof = n - 2
    s2 = resid @ resid / dof
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    r2 = 1 - resid @ resid / ((y - y.mean()) @ (y - y.mean()))
    return beta, se, beta / se, [t_p_two_sided(abs(t), dof) for t in beta / se], r2
```

多元回归同理：把 `X` 换成设计矩阵（虚拟变量用 `pd.get_dummies`），`np.linalg.lstsq` + `(X.T@X)^-1` 给系数与标准误。**但稳健标准误、多重共线性诊断、残差正态性检验需要 statsmodels**——需要这些时让用户自备环境。相关 ≠ 因果，见下节。

### 实际显著性 vs 统计显著性

- **统计显著**：差异不太可能是随机造成。
- **实际显著**：差异大到足以影响业务决策。

样本很大时差异可以统计显著但业务上毫无意义。永远报：**效应量**（多大：「B 版把转化提升 0.3 个百分点」）、**置信区间**（真效应的合理范围）、**业务影响**（折算成收入 / 用户）。

### 样本量考量

- 小样本结果不可靠，即使 p 值显著
- 比例的经验法则：每组至少 30 个事件才有基本可靠性
- 检测小效应（如 1% 转化率变化）可能需要每组上千观测
- 样本小就直说：「每组仅 200 个观测，检测小于 X% 的效应功效不足」

近似所需样本量（正态近似，α=0.05 双侧、power=0.8）：

```python
def n_per_group(p1, p2, alpha=0.05, power=0.80):
    za, zb = norm_ppf(1 - alpha / 2), norm_ppf(power)
    return math.ceil((za + zb) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2)) / (p1 - p2) ** 2)
```

（实测 20%→25% 需每组约 748；这是简化公式，未用合并/非合并方差的严格版，结论量级正确。）

## 何时该对统计主张保持谨慎

### 相关不是因果

发现相关时明确考虑：**反向因果**（也许是 B 导致 A）、**混杂变量**（C 同时导致 A 和 B）、**巧合**（变量够多必然出现伪相关）。

**可以这样说**：「使用功能 X 的用户留存高 30%」
**没有更多证据不能说**：「功能 X 导致留存高 30%」

### 多重比较问题

测很多假设时，总会有一些「显著」纯属偶然：20 个指标在 α=0.05 下约 1 个假阳性。若你翻了很多分组才找到一个不同的，要注明。校正用 Bonferroni（α 除以检验次数，上面代码可直接做），或至少报告一共跑了多少次检验。

### 辛普森悖论

汇总数据的趋势在分组后可能反转：总体转化率上升，但每个分组内都下降——因为结构占比移向了高转化分组。检查结论在关键分组内是否成立。

### 幸存者偏差

只能分析「活到」进入数据集的实体：分析活跃用户忽略了流失者。永远问：「谁不在这个数据集里，加进来会不会改变结论？」

### 生态谬误

汇总层面的规律未必适用于个体：「X 越高的国家 Y 越高」不等于「X 越高的个人 Y 越高」。别把组级结论套到个体。

### 对具体数字的锚定

警惕伪精确：「下季度流失率将是 4.73%」暗示了不该有的确定性。改成区间：「按历史规律，流失率预计在 4%–6%」。「约 5%」往往比「4.73%」更诚实。

## 输出与交付

- 统计结论写进报告时，附：**样本量、时间范围、缺失值处理、所用方法与近似说明**。
- 计算脚本用 `write` 存成 `.py` 放在工作区（保证可复现），不要用 `pwsh` 里的临时一次性长命令。
- 需要图表时用 `assets/data-create-viz/scripts/chart_pillow.py` 出 PNG 并 `present` 交付。
- 校验这份分析能不能发 → 用 `data-validate-data` 技能。
