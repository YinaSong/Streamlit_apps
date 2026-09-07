"""图表工厂 —— Streamlit 原生图表 + ECharts（streamlit-echarts）。

职责分配：
- 折线 / 面积 / 纵向柱 / 直方图 → Streamlit 原生图表（自动千分位、主题随 config.toml）。
- 横向条 / 环形 / Treemap / 帕累托 / 双轴折线 / 散点(气泡) / 热力图 / 涨跌柱 → ECharts。

页面只调用这些函数，不直接写 st.* 或 st_echarts，保证视觉统一、简约。
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts, JsCode

from utils import theme


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _title(title: str | None):
    if title:
        st.markdown(f"**{title}**")


def _num_js() -> JsCode:
    """JS 千分位格式化（ECharts tooltip / 轴标签）。"""
    return JsCode(
        "function(v){ if (v == null || v === '') return '-'; "
        "if (typeof v === 'number') return v.toLocaleString('en-US', {maximumFractionDigits: 2}); "
        "return v; }"
    )


def _tooltip(trigger: str = "axis") -> dict:
    return {
        "trigger": trigger,
        "valueFormatter": _num_js(),
        "backgroundColor": "#fff",
        "borderColor": theme.GRID,
        "textStyle": {"color": theme.TEXT},
    }


def _vals(series) -> list:
    """Series -> list，NaN 转 None（JSON null），供 ECharts 使用。"""
    return [None if pd.isna(v) else float(v) for v in series]


def _echarts(options: dict, height: int | None = None, key: str | None = None):
    h = height or theme.CHART_HEIGHT
    st_echarts(options=options, height=f"{h}px", width="100%", key=key)


# ---------------------------------------------------------------------------
# Streamlit 原生图表
# ---------------------------------------------------------------------------

def line(df, x, y, title=None, y2=None, height=None):
    """折线图；y 可为单列名或列名列表。y2 传入时切换为 ECharts 双轴。"""
    if y2:
        return dual_line(df, x, y, y2, title=title, height=height)
    _title(title)
    ys = list(y) if isinstance(y, list) else [y]
    d = df[[x] + ys]
    st.line_chart(d, x=x, y=ys, height=height or theme.CHART_HEIGHT)


def area(df, x, y, title=None, height=None):
    _title(title)
    st.area_chart(df[[x, y]], x=x, y=y, height=height or theme.CHART_HEIGHT)


def bar(df, x, y, title=None, height=None):
    """纵向柱状图（Streamlit 原生）。"""
    _title(title)
    st.bar_chart(df[[x, y]], x=x, y=y, height=height or theme.CHART_HEIGHT)


def histogram(df, x, title=None, nbins=None, height=None):
    """直方图：numpy 分箱后交给 st.bar_chart。"""
    _title(title)
    s = df[x].dropna()
    if len(s) == 0:
        st.info("无数据")
        return
    bins = nbins or 30
    if pd.api.types.is_datetime64_any_dtype(s):
        # numpy 2.x 无法直接对 datetime64 分箱，先转成整数纳秒再分箱。
        ns = s.astype("int64").to_numpy()
        counts, edges = np.histogram(ns, bins=bins)
        edges_dt = pd.to_datetime(edges.astype("int64"), unit="ns")
        labels = [e.strftime("%Y-%m") for e in edges_dt[:-1]]
    else:
        counts, edges = np.histogram(s, bins=bins)
        labels = [f"{edges[i]:,.0f}–{edges[i + 1]:,.0f}" for i in range(len(counts))]
    hist = pd.DataFrame({"区间": labels, "数量": counts})
    st.bar_chart(hist, x="区间", y="数量", height=height or theme.CHART_HEIGHT)


# ---------------------------------------------------------------------------
# ECharts 图表
# ---------------------------------------------------------------------------

def dual_line(df, x, y, y2, title=None, height=None):
    """双轴折线：左轴 y、右轴 y2。"""
    _title(title)
    options = {
        "tooltip": _tooltip("axis"),
        "legend": {"data": [y, y2], "top": 0},
        "grid": {"left": "3%", "right": "6%", "bottom": "8%", "containLabel": True},
        "xAxis": {"type": "category", "data": df[x].astype(str).tolist()},
        "yAxis": [
            {"type": "value", "name": y, "axisLabel": {"formatter": _num_js()}},
            {"type": "value", "name": y2, "axisLabel": {"formatter": _num_js()}},
        ],
        "series": [
            {"name": y, "type": "line", "smooth": True, "data": _vals(df[y]),
             "lineStyle": {"color": theme.PRIMARY}, "itemStyle": {"color": theme.PRIMARY}},
            {"name": y2, "type": "line", "smooth": True, "yAxisIndex": 1, "data": _vals(df[y2]),
             "lineStyle": {"color": theme.SECONDARY[1]}, "itemStyle": {"color": theme.SECONDARY[1]}},
        ],
    }
    _echarts(options, height)


def hbar(df, x, y, title=None, color=None, height=None):
    """横向条形图：x 数值、y 分类（首行显示在最上方）。"""
    _title(title)
    d = df.dropna(subset=[x, y])
    options = {
        "tooltip": _tooltip("axis"),
        "grid": {"left": "3%", "right": "6%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value", "axisLabel": {"formatter": _num_js()}},
        "yAxis": {"type": "category", "data": d[y].astype(str).tolist(), "inverse": True},
        "series": [{
            "type": "bar",
            "data": _vals(d[x]),
            "itemStyle": {"color": color or theme.PRIMARY},
            "barMaxWidth": 22,
        }],
    }
    _echarts(options, height)


def donut(df, names, values, title=None, height=None):
    """环形图（饼图 hole）。"""
    _title(title)
    d = df.dropna(subset=[values])
    data = [{"name": str(r[names]), "value": float(r[values])} for _, r in d.iterrows()]
    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function(p){ return p.name + '<br/>' + p.value.toLocaleString('en-US')"
                " + ' (' + p.percent + '%)'; }"
            ),
        },
        "legend": {"type": "scroll", "orient": "vertical", "right": 8, "top": "middle"},
        "series": [{
            "type": "pie",
            "radius": ["42%", "72%"],
            "center": ["38%", "50%"],
            "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": False},
            "color": theme.ECHARTS_COLORS,
            "data": data,
        }],
    }
    _echarts(options, height)


def treemap(df, path, values, title=None, height=None):
    """Treemap。"""
    _title(title)
    d = df.dropna(subset=[values])
    data = [{"name": str(r[path]), "value": float(r[values])} for _, r in d.iterrows()]
    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function(p){ return p.name + '<br/>' + p.value.toLocaleString('en-US'); }"
            ),
        },
        "series": [{
            "type": "treemap",
            "roam": False,
            "label": {"show": True, "formatter": "{b}"},
            "upperLabel": {"show": False},
            "itemStyle": {"borderColor": "#fff", "borderWidth": 1, "gapWidth": 1},
            "color": theme.ECHARTS_COLORS,
            "data": data,
        }],
    }
    _echarts(options, height or theme.CHART_HEIGHT_LARGE)


def scatter(df, x, y, title=None, size=None, color=None, hover_name=None, height=None):
    """散点/气泡图（ECharts）。size 提供时按第三维映射气泡半径。"""
    _title(title)
    cols = [c for c in (x, y, size, hover_name) if c and c in df.columns]
    d = df.dropna(subset=[c for c in (x, y, size) if c in df.columns]).copy()
    if len(d) == 0:
        st.info("无数据")
        return

    name_col = hover_name if hover_name in d.columns else None
    if size and size in d.columns:
        sizes = d[size].astype(float)
        smin, smax = float(sizes.min()), float(sizes.max())
        span = (smax - smin) if smax > smin else 1.0
        norm = ((sizes - smin) / span * 34 + 6).tolist()
        data = [
            {"value": [float(r[x]), float(r[y]), norm[i]],
             "name": str(r[name_col]) if name_col else None}
            for i, (_, r) in enumerate(d.iterrows())
        ]
        symbol_size = JsCode("function(val){ return val[2]; }")
    else:
        data = [
            {"value": [float(r[x]), float(r[y])],
             "name": str(r[name_col]) if name_col else None}
            for _, r in d.iterrows()
        ]
        symbol_size = 11

    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": JsCode(
                "function(p){ var v=p.value; var head = p.name ? (p.name + '<br/>') : '';"
                " return head + v[0].toLocaleString('en-US') + ' , ' + v[1].toLocaleString('en-US'); }"
            ),
        },
        "grid": {"left": "3%", "right": "5%", "bottom": "8%", "top": "6%", "containLabel": True},
        "xAxis": {"type": "value", "name": x, "axisLabel": {"formatter": _num_js()}},
        "yAxis": {"type": "value", "name": y, "axisLabel": {"formatter": _num_js()}},
        "series": [{
            "type": "scatter",
            "data": data,
            "symbolSize": symbol_size,
            "itemStyle": {"color": theme.PRIMARY, "opacity": 0.72},
        }],
    }
    _echarts(options, height)


def pareto(df, x, y, title=None, height=None):
    """帕累托图：降序柱 + 累计百分比线。"""
    _title(title)
    d = df.sort_values(y, ascending=False).reset_index(drop=True)
    cum = (d[y].cumsum() / d[y].sum() * 100).round(1).tolist()
    options = {
        "tooltip": _tooltip("axis"),
        "grid": {"left": "3%", "right": "6%", "bottom": "8%", "containLabel": True},
        "xAxis": {"type": "category", "data": d[x].astype(str).tolist(),
                  "axisLabel": {"rotate": 45}},
        "yAxis": [
            {"type": "value", "name": y, "axisLabel": {"formatter": _num_js()}},
            {"type": "value", "name": "累计%", "max": 100, "axisLabel": {"formatter": "{value}%"}},
        ],
        "series": [
            {"name": y, "type": "bar", "data": _vals(d[y]),
             "itemStyle": {"color": theme.PRIMARY}, "barMaxWidth": 20},
            {"name": "累计占比%", "type": "line", "yAxisIndex": 1, "data": cum,
             "lineStyle": {"color": theme.SECONDARY[2]}, "itemStyle": {"color": theme.SECONDARY[2]}},
        ],
    }
    _echarts(options, height)


def rise_fall_bar(x_values, y_values, title=None, height=None):
    """涨跌柱状图：>=0 绿色、<0 红色（环比/同比）。"""
    _title(title)
    data = [
        {"value": None if pd.isna(v) else float(v),
         "itemStyle": {"color": theme.UP if (pd.notna(v) and v >= 0) else theme.DOWN}}
        for v in y_values
    ]
    options = {
        "tooltip": _tooltip("axis"),
        "grid": {"left": "3%", "right": "4%", "bottom": "8%", "containLabel": True},
        "xAxis": {"type": "category", "data": [str(x) for x in x_values],
                  "axisLabel": {"rotate": 45}},
        "yAxis": {"type": "value", "name": "%", "axisLabel": {"formatter": "{value}%"}},
        "series": [{"type": "bar", "data": data, "barMaxWidth": 24}],
    }
    _echarts(options, height)


def heatmap(x_labels, y_labels, values, title=None, height=None):
    """热力图：values 为 2D 列表（行=y_labels，列=x_labels），缺失跳过。"""
    _title(title)
    flat = [v for row in values for v in row if v is not None and not pd.isna(v)]
    vmin = min(flat) if flat else 0
    vmax = max(flat) if flat else 1
    data = []
    for yi in range(len(y_labels)):
        for xi in range(len(x_labels)):
            v = values[yi][xi]
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            data.append([xi, yi, float(v)])
    options = {
        "tooltip": {"position": "top", "valueFormatter": _num_js()},
        "grid": {"left": "3%", "right": "4%", "bottom": "10%", "top": "3%", "containLabel": True},
        "xAxis": {"type": "category", "data": [str(x) for x in x_labels], "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": [str(y) for y in y_labels], "splitArea": {"show": True}},
        "visualMap": {
            "min": vmin, "max": vmax, "calculable": True,
            "orient": "horizontal", "left": "center", "bottom": 0,
            "inRange": {"color": ["#EAF2F8", theme.PRIMARY]},
        },
        "series": [{"type": "heatmap", "data": data, "label": {"show": False}}],
    }
    _echarts(options, height or theme.CHART_HEIGHT_LARGE)
