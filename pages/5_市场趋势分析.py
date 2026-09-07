"""类目市场历史趋势分析（趋势 / 季节性 / 增速 三层结构）。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title(
    "市场历史趋势分析",
    "参考 Power BI 类目报告的分析角度：规模趋势 · 季节性 · 同比环比增速",
)

data = load_all()
mt = data["market_trend"].copy()
meta = data["market_meta"]

# 月份归一为 YYYYMM 字符串，按时间升序
mt["月份"] = mt["月份"].astype(str)
mt = mt.sort_values("月份").reset_index(drop=True)

# ---- 头部：类目元信息 + 数据截至 ----
meta_text = (
    f"类目：{meta.get('类目名称', '—')} · {meta.get('一级大类', '—')} · NODEID {meta.get('NODEID', '—')}"
)
latest = fmt.fmt_year_month(mt["月份"].iloc[-1])
ui.data_source(f"{meta_text} · 数据截至 {latest}（最近月份数据可能未完整统计）")

# ---- 概览 KPI ----
ov = kpi_mod.market_trend_kpis(mt, "月份", "类目销量")


def _pct_signed(x):
    return f"{x:+.1f}%" if x is not None else "—"


ui.kpi_cards([
    {"label": "最新月类目销量", "value": fmt.compact(ov["最新值"]),
     "sub": f"截至 {fmt.fmt_year_month(ov['最新月'])}"},
    {"label": "类目销量环比 (MoM)", "value": _pct_signed(ov["环比%"])},
    {"label": "类目销量同比 (YoY)", "value": _pct_signed(ov["同比%"])},
])

# ---- 时间范围筛选（影响趋势类图表，季节性热力图始终全历史） ----
range_opt = st.radio(
    "时间范围", ["全部历史", "最近 24 个月", "最近 12 个月"], horizontal=True,
)
if range_opt == "最近 24 个月":
    view = mt.tail(24).reset_index(drop=True)
elif range_opt == "最近 12 个月":
    view = mt.tail(12).reset_index(drop=True)
else:
    view = mt

# ---- 模块 A：规模趋势（双轴） ----
ui.section("A. 类目规模趋势（销量 & 销售额）")
charts.line(view, x="月份", y="类目销量", y2="类目销售额", title="类目月销量 vs 月销售额")

# ---- 模块 B：同比 / 环比 ----
ui.section("B. 同比 / 环比增速")
mom_yoy = kpi_mod.mom_yoy_table(mt, "类目销量", "月份").tail(len(view))
c1, c2 = st.columns(2)
with c1:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["环比%"].tolist(), title="类目销量环比 MoM（%）",
    )
with c2:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["同比%"].tolist(), title="类目销量同比 YoY（%）",
    )

# ---- 模块 C：季节性热力图（全历史） ----
ui.section("C. 季节性（年份 × 月份）")
years, months, matrix = kpi_mod.seasonality_matrix(mt, "月份", "类目销量")
month_labels = [f"{m}月" for m in months]
charts.heatmap(x_labels=years, y_labels=month_labels, values=matrix,
               title="类目销量季节性热力图（识别旺季 / 淡季）")

# ---- 模块 D：指标自由选择 ----
ui.section("D. 指标自由选择（多指标叠加）")
metric_groups = {
    "规模": ["类目销量", "类目销售额"],
    "价格/评价": ["平均售价", "平均评价", "平均星级"],
    "竞争": ["平均品牌数量", "平均卖家数量", "平均大类排名"],
    "流量": ["核心词流量"],
    "利润": ["平均单个利润"],
}
all_metrics = [m for v in metric_groups.values() for m in v]
selected = st.multiselect(
    "选择要展示的指标", all_metrics, default=["类目销量", "类目销售额"],
)
if selected:
    st.caption("提示：不同指标量纲差异较大，建议选择量纲相近的指标进行对比。")
    charts.line(view, x="月份", y=selected, title="多指标趋势对比")

# ---- 模块 E：价格与评价 ----
ui.section("E. 价格与评价")
c3, c4 = st.columns(2)
with c3:
    charts.line(view, x="月份", y="平均售价", title="平均售价趋势")
with c4:
    charts.line(view, x="月份", y="平均星级", title="平均星级趋势")
charts.line(view, x="月份", y="平均评价", title="平均评价趋势")

# ---- 模块 F：竞争格局 ----
ui.section("F. 竞争格局")
c5, c6 = st.columns(2)
with c5:
    charts.line(view, x="月份", y="平均品牌数量", title="平均品牌数量趋势")
with c6:
    charts.line(view, x="月份", y="平均卖家数量", title="平均卖家数量趋势")

# ---- 原始数据 ----
ui.section("原始数据表")
_int_cols = {"类目销量", "核心词流量", "平均评价"}
col_config = {
    c: st.column_config.NumberColumn(format=fmt.NUM_FMT if c in _int_cols else fmt.NUM_FMT_2)
    for c in mt.columns if c != "月份"
}
st.dataframe(mt, use_container_width=True, hide_index=True, column_config=col_config)
