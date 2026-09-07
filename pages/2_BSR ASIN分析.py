"""BSR ASIN 竞争分析（Top100 产品）。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("BSR ASIN 竞争分析")

data = load_all()
detail = data["asin"]["detail"]
summ = kpi_mod.summary_kpis(data["asin"]["summary"])

# ---- KPI ----
ui.kpi_cards([
    {"label": "产品数", "value": fmt.thousands(summ["产品数"])},
    {"label": "月总销量", "value": fmt.compact(summ["月总销量"])},
    {"label": "月总销售额", "value": fmt.compact_usd(summ["月总销售额($)"])},
    {"label": "平均价格", "value": fmt.usd(summ["平均价格($)"])},
    {"label": "平均星级", "value": f'{summ["平均星级"]:.1f}' if summ["平均星级"] else "—"},
])

# ---- Top 排行 ----
ui.section("1. Top100 销量 / 销额")
c1, c2 = st.columns(2)
with c1:
    d = detail.nlargest(15, "预计Listing月销量")
    charts.hbar(d, x="预计Listing月销量", y="ASIN", title="Top15 月销量")
with c2:
    d = detail.nlargest(15, "Listing月销售额($)")
    charts.hbar(d, x="Listing月销售额($)", y="ASIN", title="Top15 月销额")

# ---- 价格 / 评分 / 评论 与销量关系 ----
ui.section("2. 价格 / 评分 / 评论 与销量关系")
c3, c4 = st.columns(2)
with c3:
    charts.scatter(detail, x="实际价格($)", y="预计Listing月销量", hover_name="ASIN",
                   title="价格 vs 销量")
with c4:
    charts.scatter(detail, x="评分星级", y="预计Listing月销量", hover_name="ASIN",
                   title="评分 vs 销量")

c5, c6 = st.columns(2)
with c5:
    charts.scatter(detail, x="评价数量", y="预计Listing月销量", hover_name="ASIN",
                   title="评论数 vs 销量")
with c6:
    charts.scatter(detail, x="上架天数", y="预计Listing月销量", hover_name="ASIN",
                   size="评价数量", title="生命周期（上架天数 vs 销量）")

# ---- 毛利四象限 ----
ui.section("3. 毛利 × 销量")
charts.scatter(
    detail, x="预计Listing月销量", y="单个产品毛利($)", hover_name="ASIN",
    size="单个产品毛利率(%)", title="销量 vs 毛利（气泡=毛利率）",
)

# ---- 原始数据 ----
ui.section("4. 原始数据表")
cols = ["产品名称", "ASIN", "品牌", "实际价格($)", "预计Listing月销量", "Listing月销售额($)",
        "评分星级", "评价数量", "上架时间", "上架天数", "单个产品毛利($)", "单个产品毛利率(%)"]
st.dataframe(
    detail[cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "实际价格($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "预计Listing月销量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "Listing月销售额($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "评分星级": st.column_config.NumberColumn(format="%.1f"),
        "评价数量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "上架天数": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "单个产品毛利($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "单个产品毛利率(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "上架时间": st.column_config.DateColumn(format="YYYY-MM-DD"),
    },
)
