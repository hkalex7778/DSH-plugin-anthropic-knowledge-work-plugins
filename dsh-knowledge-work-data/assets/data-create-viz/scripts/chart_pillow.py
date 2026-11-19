"""用 Pillow 渲染 PNG 图表（无需 matplotlib/seaborn/plotly）。

DSH 捆绑 Python 有：numpy、pandas、Pillow、openpyxl、XlsxWriter、lxml。
没有：matplotlib、seaborn、scipy、statsmodels、plotly、duckdb。本脚本填补这个缺口，
支持 line / bar / hbar / stackbar / hist / scatter / heat 七种图型，中文标签正常渲染。

命令行（--csv 与 --y 必填；--x 除 hist 外必填，hist 只按 --y 分箱）:
    python chart_pillow.py --kind line --csv data.csv --x month --y rev,rev2 --out trend.png --title "各期收入趋势" --fmt currency
    python chart_pillow.py --kind hist --csv data.csv --y revenue --bins 40 --out rev_hist.png
    python chart_pillow.py --kind hbar --csv data.csv --x name --y score --sort --out rank.png

编程调用（形参名如下，注意 ylabel / yfmt，横向条形图是 hbar 不是 barh）:
    import pandas as pd
    from chart_pillow import save_chart
    save_chart("hbar", df, x="category", y="metric", out="rank.png",
               title="NPS 排名（2024 Q4）", ylabel="NPS", yfmt="number", sort=True)
"""
from __future__ import annotations

import argparse
import math
import os
import re
from PIL import Image, ImageDraw, ImageFont

# Colorblind-friendly categorical palette (Okabe-Ito / seaborn "deep" family)
PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
           "#937860", "#DA8BC3", "#8C8C8C"]
GRID = "#E3E6EA"
AXIS = "#555B63"
TEXT = "#212529"
MUTED = "#6C757D"

#: Currency prefix used by `--fmt currency`; override via the CLI flag.
CURRENCY_SYMBOL = "¥"

_CJK_RE = re.compile(
    r"[\u3000-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uff00-\uffef]")

# (name, path, has_cjk). YaHei leads so Chinese never falls back to a
# Latin-only face — Pillow does no cross-font glyph fallback, so a Segoe UI
# hit on Chinese text renders tofu boxes.
_FONT_CANDIDATES = [
    ("Microsoft YaHei", "C:\\Windows\\Fonts\\msyh.ttc", True),
    ("Microsoft YaHei Bold", "C:\\Windows\\Fonts\\msyhbd.ttc", True),
    ("Segoe UI", "C:\\Windows\\Fonts\\segoeui.ttf", False),
    ("Segoe UI Bold", "C:\\Windows\\Fonts\\segoeuib.ttf", False),
    ("Arial", "C:\\Windows\\Fonts\\arial.ttf", False),
    ("Arial Bold", "C:\\Windows\\Fonts\\arialbd.ttf", False),
    ("Noto Sans CJK", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", True),
    ("Noto Sans CJK Bold", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", True),
    ("DejaVu Sans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", False),
    ("DejaVu Sans Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", False),
]


def font(size: int, bold: bool = False, text: str = ""):
    """Load a Unicode-capable face with the correct weight for `text`.

    `text` selects the script: CJK text prefers a CJK-capable face; pure
    Latin text keeps the Segoe/Arial look. Weight is decided by the *name*,
    not by list position — msyh.ttc is the regular face and msyhbd.ttc is
    the bold one, so the old "reverse the list when not bold" trick made
    titles thin and body text bold.
    """
    ordered = list(_FONT_CANDIDATES)
    if bold:
        ordered.sort(key=lambda c: 0 if "Bold" in c[0] else 1)
    if text and not _CJK_RE.search(str(text)):
        ordered.sort(key=lambda c: 0 if not c[2] else 1)
    for _, path, _ in ordered:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # older Pillow
        return ImageFont.load_default()


def fmt_num(v, kind="number"):
    """Compact human formatting: 1.5M / 23K / 45.2% / 1,234.

    `currency` keeps its symbol at every magnitude, so an axis never mixes
    `$1,200` with a bare `1.5K`.
    """
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if kind == "percent":
        return f"{v:.1f}%"
    a = abs(v)
    sign = "-" if v < 0 else ""
    sym = CURRENCY_SYMBOL if kind == "currency" else ""
    if a >= 1e9:
        return f"{sign}{sym}{a/1e9:.1f}B"
    if a >= 1e6:
        return f"{sign}{sym}{a/1e6:.1f}M"
    if a >= 1e3:
        return f"{sign}{sym}{a/1e3:.1f}K"
    if kind == "currency":
        return f"{sign}{sym}{a:,.0f}" if a == int(a) else f"{sign}{sym}{a:,.2f}"
    return f"{sign}{a:,.0f}" if a >= 100 or a == int(a) else f"{sign}{a:,.1f}"


def nice_ticks(lo, hi, target=6):
    """Round-number axis ticks; always includes both ends of the data range."""
    if not (math.isfinite(lo) and math.isfinite(hi)) or lo == hi:
        base = lo if math.isfinite(lo) and lo else 0.0
        return [base - 1, base, base + 1]
    if hi < lo:
        lo, hi = hi, lo
    raw = (hi - lo) / max(1, target)
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    step = min((c for c in (1, 2, 2.5, 5, 10) if c * mag >= raw), default=10) * mag
    start = math.floor(lo / step) * step
    out, v = [], start
    while v <= hi + step * 1e-6 and len(out) < 40:
        out.append(round(v, 10))
        v += step
    if not out or out[0] > lo:
        out.insert(0, round(lo, 10))
    if out[-1] < hi:
        out.append(round(hi, 10))
    return out


class Figure:
    """Supersampled canvas: draw at 2x, downscale for clean edges."""

    def __init__(self, w=980, h=560, bg="#FFFFFF"):
        self.s = 2
        self.W, self.H = w * self.s, h * self.s
        self.img = Image.new("RGB", (self.W, self.H), bg)
        self.d = ImageDraw.Draw(self.img)
        self.f_title = font(15 * self.s, bold=True)
        self.f_sub = font(11 * self.s)
        self.f_axis = font(11 * self.s)
        self.f_tick = font(10 * self.s)
        self.f_lbl = font(10 * self.s)
        self.out_w = w

    def text_w(self, s, f):
        b = f.getbbox(str(s))
        return b[2] - b[0]

    def text_h(self, s, f):
        b = f.getbbox(str(s))
        return b[3] - b[1]

    def save(self, path, dpi=150):
        img = self.img.resize((self.out_w, self.H // self.s), Image.LANCZOS)
        img.save(path, dpi=(dpi, dpi))
        return path


def _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt, xcats=True):
    """Draw title, plot border, and y ticks. Returns (x0,y0,x1,y1) plot box."""
    s = fig.s
    # header
    y = 14 * s
    if title:
        fig.d.text((m["l"], y), title, font=fig.f_title, fill=TEXT)
        y += fig.text_h(title, fig.f_title) + 4 * s
    if subtitle:
        fig.d.text((m["l"], y), subtitle, font=fig.f_sub, fill=MUTED)
        y += fig.text_h(subtitle, fig.f_sub) + 2 * s
    x0, x1 = m["l"], fig.W - m["r"]
    y0, y1 = max(m["t"], y + 8 * s), fig.H - m["b"]
    if ylabel:
        # Draw the label horizontally in a strip sized to the *text*, then
        # rotate it upright. The strip must be as wide as the text or the
        # glyphs are clipped before rotation ever happens.
        tw = fig.text_w(ylabel, fig.f_axis)
        th = fig.text_h(ylabel, fig.f_axis)
        tmp = Image.new("RGBA", (tw + 6 * s, th + 6 * s), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        td.text((3 * s, 3 * s), ylabel, font=fig.f_axis, fill=TEXT)
        tmp = tmp.rotate(90, expand=True)
        # Anchor to the canvas edge, not to the plot box: the tick labels
        # already live in the left gutter beside m["l"], so a label placed
        # relative to m["l"] collides with them.
        fig.img.paste(tmp, (4 * s, (y0 + y1) // 2 - tmp.height // 2), tmp)
    return x0, y0, x1, y1


def _yticks(fig, x0, y0, x1, y1, lo, hi, yfmt):
    ticks = nice_ticks(lo, hi)
    span = ticks[-1] - ticks[0] or 1.0
    for t in ticks:
        yy = y1 - (t - ticks[0]) / span * (y1 - y0)
        fig.d.line([x0, yy, x1, yy], fill=GRID, width=fig.s)
        lab = fmt_num(t, yfmt)
        fig.d.text((x0 - fig.text_w(lab, fig.f_tick) - 6 * fig.s, yy - fig.text_h(lab, fig.f_tick) // 2),
                   lab, font=fig.f_tick, fill=MUTED)
    return ticks[0], span


def _xticks_cat(fig, labels, x0, y1, slot, rotate=False):
    s = fig.s
    for i, lab in enumerate(labels):
        cx = x0 + slot * (i + 0.5)
        txt = str(lab)
        w = fig.text_w(txt, fig.f_lbl)
        maxw = slot - 4 * s
        if w > maxw and len(txt) > 6:
            while fig.text_w(txt[:-2] + "…", fig.f_lbl) > maxw and len(txt) > 3:
                txt = txt[:-2] + "…"
            w = fig.text_w(txt, fig.f_lbl)
        if rotate:
            tmp = Image.new("RGBA", (fig.text_h(txt, fig.f_lbl) + 4 * s, w + 4 * s), (0, 0, 0, 0))
            ImageDraw.Draw(tmp).text((2 * s, 2 * s), txt, font=fig.f_lbl, fill=MUTED)
            tmp = tmp.rotate(45, expand=True)
            fig.img.paste(tmp, (int(cx - tmp.width / 2), int(y1 + 6 * s)), tmp)
        else:
            fig.d.text((cx - w / 2, y1 + 6 * s), txt, font=fig.f_lbl, fill=MUTED)


def _legend(fig, entries, x1, ytop):
    s = fig.s
    x = x1
    for label, color in reversed(entries):
        w = fig.text_w(label, fig.f_lbl)
        x -= w + 26 * s
        fig.d.rectangle([x, ytop, x + 12 * s, ytop + 12 * s], fill=color)
        fig.d.text((x + 16 * s, ytop + 6 * s - fig.text_h(label, fig.f_lbl) // 2),
                   label, font=fig.f_lbl, fill=TEXT)


def _autoscale(rows, cols):
    """Return (lo, hi) across given numeric columns."""
    vals = []
    for r in rows:
        for c in cols:
            v = r.get(c)
            if isinstance(v, (int, float)) and math.isfinite(v):
                vals.append(float(v))
    if not vals:
        return 0.0, 1.0
    lo, hi = min(vals), max(vals)
    if lo > 0:
        lo = 0.0            # bar-ish charts start at zero
    if hi == lo:
        hi = lo + 1
    return lo, hi


def _natural_key(v):
    """Sort numerically when the label parses as a number, else lexicographically.
    Keeps hour axes as 0,3,6,9,12 instead of 0,12,15,18,21,3,6,9."""
    try:
        return (0, float(v), "")
    except (TypeError, ValueError):
        return (1, 0.0, str(v))


def _ordered(values, explicit):
    if explicit:
        rest = [v for v in values if str(v) not in {str(e) for e in explicit}]
        return [v for v in explicit if str(v) in {str(x) for x in values}] + sorted(rest, key=_natural_key)
    return sorted(values, key=_natural_key)


def save_chart(kind, rows, x, y, out, title="", subtitle="", xlabel="",
               ylabel="", yfmt="number", width=980, height=560, sort=False,
               stacked=False, bins=30, note=None, xorder=None, yorder=None):
    """rows: list[dict] or pandas.DataFrame.  y: str or list[str] of numeric columns."""
    import pandas as pd
    if isinstance(rows, pd.DataFrame):
        rows = rows.to_dict("records")
    ycols = [y] if isinstance(y, str) else list(y)
    # stackbar implies stacking; the axis maximum must then cover row totals,
    # otherwise the tallest stack runs off the top of the canvas.
    if kind == "stackbar":
        stacked = True

    def col(rec, name, default=None):
        for k, v in rec.items():
            if str(k).lower() == name.lower():
                return v
        return default

    if kind in ("hbar", "bar", "stackbar"):
        if sort:
            # Descending everywhere: hbar rows are drawn top-to-bottom, so the
            # largest value must land at index 0 to appear on top — the
            # convention for a ranking chart.
            rows = sorted(rows, key=lambda r: sum(
                float(col(r, c, 0) or 0) for c in ycols),
                reverse=True)

    fig = Figure(width, height)
    s = fig.s
    m = {"l": 78 * s, "r": 26 * s, "t": 34 * s, "b": 56 * s}
    # hbar puts categories in the left gutter: widen it so long labels are not clipped
    if kind == "hbar":
        widest = max((fig.text_w(str(col(r, x))[:24], fig.f_lbl) for r in rows), default=0)
        m["l"] = int(min(260 * s, max(78 * s, widest + 14 * s)))

    if kind == "hist":
        vals = [float(col(r, ycols[0])) for r in rows
                if col(r, ycols[0]) is not None and math.isfinite(float(col(r, ycols[0])))]
        lo0, hi0 = (min(vals), max(vals)) if vals else (0, 1)
        if lo0 == hi0:
            hi0 = lo0 + 1
        cnt = [0] * bins
        for v in vals:
            i = min(bins - 1, int((v - lo0) / (hi0 - lo0) * bins))
            cnt[i] += 1
        x0, y0, x1, y1 = _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt)
        base, span = _yticks(fig, x0, y0, x1, y1, 0, max(cnt) or 1, "number")
        slot = (x1 - x0) / bins
        for i, c in enumerate(cnt):
            bx0 = x0 + slot * i + s
            bh = (c - 0) / (span or 1) * (y1 - y0)
            fig.d.rectangle([bx0, y1 - bh, x0 + slot * (i + 1) - s, y1], fill=PALETTE[0])
        for i in (0, bins // 2, bins - 1):
            lab = fmt_num(lo0 + (hi0 - lo0) * i / bins, yfmt)
            fig.d.text((x0 + slot * (i + 0.5) - fig.text_w(lab, fig.f_lbl) / 2, y1 + 6 * s),
                       lab, font=fig.f_lbl, fill=MUTED)
        fig.d.line([x0, y1, x1, y1], fill=AXIS, width=s)
        return fig.save(out)

    if kind == "scatter":
        pts = [(float(col(r, x)), float(col(r, ycols[0]))) for r in rows
               if col(r, x) is not None and col(r, ycols[0]) is not None]
        xls = [p[0] for p in pts]
        xlo, xhi = (min(xls), max(xls)) if xls else (0, 1)
        if xlo == xhi:
            xhi = xlo + 1
        ylo, yhi = _autoscale([{"a": p[1]} for p in pts], ["a"])
        x0, y0, x1, y1 = _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt)
        base, span = _yticks(fig, x0, y0, x1, y1, ylo, yhi, yfmt)
        for t in nice_ticks(xlo, xhi, 6):
            xx = x0 + (t - xlo) / (xhi - xlo or 1) * (x1 - x0)
            fig.d.line([xx, y0, xx, y1], fill=GRID, width=s)
            lab = fmt_num(t, "number")
            fig.d.text((xx - fig.text_w(lab, fig.f_lbl) / 2, y1 + 6 * s), lab,
                       font=fig.f_lbl, fill=MUTED)
        for xv, yv in pts:
            px = x0 + (xv - xlo) / (xhi - xlo or 1) * (x1 - x0)
            py = y1 - (yv - base) / (span or 1) * (y1 - y0)
            r = 4 * s
            fig.d.ellipse([px - r, py - r, px + r, py + r], fill=PALETTE[0])
        fig.d.line([x0, y1, x1, y1], fill=AXIS, width=s)
        return fig.save(out)

    if kind == "heat":
        zcol = ycols[0]
        kcol = ycols[1] if len(ycols) > 1 else x
        xs_ = _ordered(sorted({str(col(r, x)) for r in rows}, key=_natural_key), xorder)
        ys_ = _ordered(sorted({str(col(r, kcol)) for r in rows}, key=_natural_key), yorder)
        # Row labels sit left of x0 and the rotated ylabel is pinned near the
        # canvas edge; with long row names the two collide, so widen the gutter
        # until row labels clear the ylabel strip.
        widest_row = max((fig.text_w(str(v)[:18], fig.f_lbl) for v in ys_), default=0)
        ylabel_right = (4 * s + fig.text_h(str(ylabel), fig.f_axis) + 6 * s) if ylabel else 0
        m["l"] = int(min(320 * s, max(m["l"], ylabel_right + widest_row + 18 * s)))
        grid = {(str(col(r, x)), str(col(r, ycols[1]))): col(r, zcol) for r in rows}
        vals = [float(v) for v in grid.values() if v is not None and math.isfinite(float(v))] or [0.0]
        vmin, vmax = min(vals), max(vals)
        x0, y0, x1, y1 = _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt)
        cw, ch = (x1 - x0) / max(1, len(xs_)), (y1 - y0) / max(1, len(ys_))
        for i, yy in enumerate(ys_):
            for j, xx in enumerate(xs_):
                v = grid.get((xx, yy))
                t = 0.0 if v is None else (float(v) - vmin) / ((vmax - vmin) or 1)
                c = tuple(int(255 - (255 - k) * t) for k in (76, 114, 176))
                fig.d.rectangle([x0 + cw * j + s, y0 + ch * i + s,
                                 x0 + cw * (j + 1) - s, y0 + ch * (i + 1) - s], fill=c)
                if v is not None and cw > 30 * s:
                    fig.d.text((x0 + cw * (j + .5) - fig.text_w(fmt_num(v, yfmt), fig.f_lbl) / 2,
                                y0 + ch * (i + .5) - 6 * s), fmt_num(v, yfmt),
                               font=fig.f_lbl, fill="#FFFFFF" if t > .6 else TEXT)
            lab = str(yy)[:18]
            fig.d.text((x0 - fig.text_w(lab, fig.f_lbl) - 6 * s, y0 + ch * (i + .5) - 6 * s),
                       lab, font=fig.f_lbl, fill=MUTED)
        for j, xx in enumerate(xs_):
            lab = str(xx)[:14]
            fig.d.text((x0 + cw * (j + .5) - fig.text_w(lab, fig.f_lbl) / 2, y1 + 6 * s),
                       lab, font=fig.f_lbl, fill=MUTED)
        return fig.save(out)

    # --- cartesian, categorical x: line | bar | hbar | stackbar ---
    cats = [str(col(r, x)) for r in rows]
    if kind == "hbar":
        # horizontal: categories on y axis
        ylo, yhi = 0.0, 1.0
        vals = [float(col(r, c, 0) or 0) for r in rows for c in ycols]
        yhi = max(vals) * 1.08 if vals and max(vals) > 0 else (max(vals) if vals else 1)
        ylo = min(0.0, min(vals) * 1.08 if vals else 0)
        x0, y0, x1, y1 = _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt)
        slot = (y1 - y0) / max(1, len(rows))
        bar_h = min(slot * 0.72, 64 * s)   # never let 1-2 categories fill the whole canvas
        for t in nice_ticks(ylo, yhi, 6):
            xx = x0 + (t - ylo) / ((yhi - ylo) or 1) * (x1 - x0)
            fig.d.line([xx, y0, xx, y1], fill=GRID, width=s)
            lab = fmt_num(t, yfmt)
            fig.d.text((xx - fig.text_w(lab, fig.f_lbl) / 2, y1 + 6 * s), lab,
                       font=fig.f_lbl, fill=MUTED)
        for i, r in enumerate(rows):
            cy = y0 + slot * (i + 0.5)
            by0, by1 = cy - bar_h / 2, cy + bar_h / 2
            lab = cats[i][:24]
            fig.d.text((x0 - fig.text_w(lab, fig.f_lbl) - 6 * s, (by0 + by1) / 2 - 6 * s),
                       lab, font=fig.f_lbl, fill=MUTED)
            for k, c in enumerate(ycols):
                v = float(col(r, c, 0) or 0)
                xx = x0 + (v - ylo) / ((yhi - ylo) or 1) * (x1 - x0)
                fig.d.rectangle([x0, by0, xx, by1], fill=PALETTE[k % len(PALETTE)])
                vl = fmt_num(v, yfmt)
                fig.d.text((xx + 4 * s, (by0 + by1) / 2 - 6 * s), vl, font=fig.f_lbl, fill=TEXT)
        fig.d.line([x0, y0, x0, y1], fill=AXIS, width=s)
        if len(ycols) > 1:
            _legend(fig, [(c, PALETTE[k % len(PALETTE)]) for k, c in enumerate(ycols)], x1, y0 - 18 * s)
        return fig.save(out)

    lo, hi = _autoscale(rows, ycols)
    if stacked:
        sums = [sum(float(col(r, c, 0) or 0) for c in ycols) for r in rows]
        hi = max(sums) if sums else hi
    x0, y0, x1, y1 = _frame(fig, m, title, subtitle, xlabel, ylabel, yfmt)
    base, span = _yticks(fig, x0, y0, x1, y1, lo, hi, yfmt)
    slot = (x1 - x0) / max(1, len(rows))
    rotate = len(cats) > 8 or any(fig.text_w(c, fig.f_lbl) > slot - 6 * s for c in cats)
    _xticks_cat(fig, cats, x0, y1, slot, rotate=rotate and kind == "bar")

    if kind == "bar":
        inner = slot * 0.7
        bw = inner / len(ycols)
        for i, r in enumerate(rows):
            for k, c in enumerate(ycols):
                v = float(col(r, c, 0) or 0)
                bx0 = x0 + slot * i + (slot - inner) / 2 + bw * k
                h = (v - base) / (span or 1) * (y1 - y0)
                yy = y1 - h if v >= 0 else y1
                fig.d.rectangle([bx0 + s, min(yy, y1), bx0 + bw - s, max(yy, y1)],
                                fill=PALETTE[k % len(PALETTE)])
    elif kind == "stackbar":
        for i, r in enumerate(rows):
            acc = 0.0
            bx0 = x0 + slot * i + slot * 0.15
            bx1 = x0 + slot * (i + 1) - slot * 0.15
            for k, c in enumerate(ycols):
                v = float(col(r, c, 0) or 0)
                h0 = (acc - base) / (span or 1) * (y1 - y0)
                h1 = (acc + v - base) / (span or 1) * (y1 - y0)
                fig.d.rectangle([bx0, y1 - h1, bx1, y1 - h0], fill=PALETTE[k % len(PALETTE)])
                acc += v
    else:  # line / area
        for k, c in enumerate(ycols):
            pts = []
            for i, r in enumerate(rows):
                v = col(r, c)
                if v is None or not math.isfinite(float(v)):
                    continue
                pts.append((x0 + slot * (i + .5),
                            y1 - (float(v) - base) / (span or 1) * (y1 - y0)))
            if len(pts) > 1:
                fig.d.line(pts, fill=PALETTE[k % len(PALETTE)], width=3 * s, joint="curve")
            for px, py in pts:
                rr = 3 * s
                fig.d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=PALETTE[k % len(PALETTE)])
        if len(ycols) == 1 and len(rows) and hi > 0:
            # highlight the last point with its value
            v = float(col(rows[-1], ycols[0], 0) or 0)
            px, py = x0 + slot * (len(rows) - .5), y1 - (v - base) / (span or 1) * (y1 - y0)
            lab = fmt_num(v, yfmt)
            fig.d.text((min(px - fig.text_w(lab, fig.f_axis), x1 - fig.text_w(lab, fig.f_axis)),
                        py - 22 * s), lab, font=fig.f_axis, fill=TEXT)
    fig.d.line([x0, y1, x1, y1], fill=AXIS, width=s)
    if len(ycols) > 1:
        _legend(fig, [(c, PALETTE[k % len(PALETTE)]) for k, c in enumerate(ycols)], x1, y0 - 18 * s)
    if note:
        fig.d.text((m["l"], fig.H - 16 * s), note, font=fig.f_lbl, fill=MUTED)
    return fig.save(out)


def _main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", default="line",
                    choices=["line", "bar", "hbar", "stackbar", "hist", "scatter", "heat"])
    ap.add_argument("--csv", required=True, help="input CSV/XLSX path")
    ap.add_argument("--x", default=None,
                    help="category/time column; required except for hist")
    ap.add_argument("--y", required=True,
                    help="numeric columns, comma separated (hist: the one column to bin; "
                         "heat: value-column,row-dimension-column)")
    ap.add_argument("--out", default="chart.png")
    ap.add_argument("--title", default="")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--xlabel", default="")
    ap.add_argument("--ylabel", default="")
    ap.add_argument("--fmt", default="number", choices=["number", "currency", "percent"])
    ap.add_argument("--symbol", default="¥", help="currency symbol used by --fmt currency")
    ap.add_argument("--sort", action="store_true",
                    help="order categories by value, largest first (for ranking charts)")
    ap.add_argument("--bins", type=int, default=30)
    ap.add_argument("--note", default=None, help="footnote drawn under the plot")
    a = ap.parse_args()
    if a.kind != "hist" and not a.x:
        # ASCII only: argparse writes this to stderr, and a Windows console
        # codepage can mangle CJK into unreadable bytes.
        ap.error(f"--x is required for --kind {a.kind} (hist is the exception: it bins --y)")
    global CURRENCY_SYMBOL
    CURRENCY_SYMBOL = a.symbol
    import pandas as pd
    df = pd.read_excel(a.csv) if a.csv.lower().endswith((".xlsx", ".xls")) else pd.read_csv(a.csv)
    save_chart(a.kind, df, a.x or a.y.split(",")[0], a.y.split(","), a.out,
               title=a.title, subtitle=a.subtitle,
               xlabel=a.xlabel, ylabel=a.ylabel, yfmt=a.fmt, sort=a.sort, bins=a.bins,
               note=a.note)
    print(a.out)


if __name__ == "__main__":
    _main()
