"""Bullet Cameras 类目分析 —— 市场总览。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title(
    "Bullet Cameras 市场总览",
    "数据来源：Sorftime 专业版导出（类目：Tools & Home Improvement → Bullet Cameras）",
)

data = load_all()
asin_summary = kpi_mod.summary_kpis(data["asin"]["summary"])
dt = data["data_time"]

# ---- 数据时间来源 ----
src = "数据导出时间：" + (dt.get("asin_export") or "—")
if dt.get("sales_latest"):
    src += f" · 销量趋势截至 {dt['sales_latest']}"
src += "（注：最近月份数据可能未完整统计）"
ui.data_source(src)

# 销量趋势（按时间升序，附「月份」标签）
trend = data["sales_trend"].sort_values("date").reset_index(drop=True).copy()
trend["月份"] = trend["date"].dt.strftime("%Y-%m")

tr = kpi_mod.sales_trend_kpis(data["sales_trend"])


def _delta(cur, prev):
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 1)


# ---- KPI 卡片（当月 + 上月 + 环比） ----
ui.kpi_cards([
    {
        "label": "市场月销量",
        "value": fmt.compact(tr["当月销量"]),
        "sub": f"上月 {fmt.compact(tr['上月销量'])}",
        "delta": _delta(tr["当月销量"], tr["上月销量"]),
    },
    {
        "label": "市场月销售额",
        "value": fmt.compact_usd(tr["当月销售额"]),
        "sub": f"上月 {fmt.compact_usd(tr['上月销售额'])}",
        "delta": _delta(tr["当月销售额"], tr["上月销售额"]),
    },
    {"label": "品牌数", "value": fmt.thousands(asin_summary["品牌数量"])},
    {"label": "ASIN数(Top100)", "value": fmt.thousands(asin_summary["产品数"])},
    {"label": "Seller数", "value": fmt.thousands(asin_summary["卖家数量"])},
])

# ---- 图1：销量 / 销售额趋势（双轴） ----
ui.section("1. 市场销量 & 销售额趋势")
charts.line(
    trend, x="月份", y="售出件数", y2="净销售额($)",
    title="月度售出件数 vs 净销售额",
)

# ---- 图2：环比 / 同比 ----
ui.section("2. 环比（按月） & 同比（按年）")
mom_yoy = kpi_mod.mom_yoy_table(trend, "售出件数", date_col="月份")
c1, c2 = st.columns(2)
with c1:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["环比%"].tolist(),
        title="销量环比 MoM（%）",
    )
with c2:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["同比%"].tolist(),
        title="销量同比 YoY（%）",
    )

# ---- 图3：全球市场 & 价格带 ----
ui.section("3. 全球市场 & 价格带")
c3, c4 = st.columns(2)
with c3:
    g = data["global"].dropna(subset=["Top100月销量"]).sort_values("Top100月销量", ascending=False)
    charts.hbar(g, x="Top100月销量", y="站点", title="各站点 Top100 月销量")
with c4:
    charts.histogram(data["asin"]["detail"], x="实际价格($)", title="价格带分布", nbins=30)

# ---- 图4：品牌份额 & Top10 ----
ui.section("4. 品牌份额 & Top10 品牌")
c5, c6 = st.columns(2)
with c5:
    charts.treemap(
        data["brand"], path="品牌名称", values="品牌产品listing月销额($)",
        title="品牌销售额 Treemap",
    )
with c6:
    top10 = data["brand"].nlargest(10, "品牌产品listing月销额($)")
    charts.hbar(top10, x="品牌产品listing月销额($)", y="品牌名称", title="Top10 品牌月销额")

# ---- 图5：Top20 产品（含 ASIN + 链接） ----
ui.section("5. Top20 产品")
detail = data["asin"]["detail"]
top20 = detail.nlargest(20, "预计Listing月销量")[
    ["产品名称", "ASIN", "URL", "品牌", "实际价格($)", "预计Listing月销量",
     "Listing月销售额($)", "评分星级", "评价数量"]
]
st.dataframe(
    top20,
    use_container_width=True,
    hide_index=True,
    column_config={
        "URL": st.column_config.LinkColumn("链接", display_text="Amazon ↗"),
        "实际价格($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "预计Listing月销量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "Listing月销售额($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "评分星级": st.column_config.NumberColumn(format="%.1f"),
        "评价数量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
    },
)

ui.usage_note()
