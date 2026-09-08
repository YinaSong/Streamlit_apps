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

# ---- 销量集中度 ----
ui.section("4. 销量集中度（Listing 垄断）")
conc = kpi_mod.listing_concentration(detail, "预计Listing月销量")
charts.hbar(conc, x="累计份额%", y="TopN", title="Top N Listing 累计销量份额（%）")

# ---- 价格 / 评分区间 ----
ui.section("5. 价格区间 & 评分区间")
c7, c8 = st.columns(2)
with c7:
    charts.donut(kpi_mod.price_bands(detail), names="价格区间", values="ASIN数",
                 title="价格区间 ASIN 数占比")
with c8:
    rat = kpi_mod.rating_bands(detail).sort_values("ASIN数", ascending=False)
    charts.hbar(rat, x="ASIN数", y="评分区间", title="评分星级分布")

# ---- 店铺（卖家）对比 ----
ui.section("6. 店铺（卖家）对比")
seller = kpi_mod.seller_stats(detail)
c9, c10 = st.columns(2)
with c9:
    charts.scatter(seller, x="ASIN数", y="平均售价", size="月销量", hover_name="店铺",
                   title="店铺价格定位（x=ASIN数 · 气泡=月销量）")
with c10:
    charts.hbar(seller.head(15), x="月销量", y="店铺", title="店铺月销量 Top15")

# ---- ASIN 装修 & 卖家属性 ----
ui.section("7. ASIN 装修 & 卖家属性")
r1 = st.columns(3)
with r1[0]:
    charts.donut(kpi_mod.categorical_share(detail, "物流方式"), names="类别", values="ASIN数",
                 title="物流方式", height=300)
with r1[1]:
    charts.donut(kpi_mod.categorical_share(detail, "A+"), names="类别", values="ASIN数",
                 title="A+ 页面", height=300)
with r1[2]:
    charts.donut(kpi_mod.categorical_share(detail, "主图视频"), names="类别", values="ASIN数",
                 title="主图视频", height=300)
r2 = st.columns(2)
with r2[0]:
    charts.donut(kpi_mod.categorical_share(detail, "是否做品牌旗舰店"), names="类别", values="ASIN数",
                 title="品牌旗舰店", height=300)
with r2[1]:
    charts.donut(kpi_mod.categorical_share(detail, "BBX卖家属性"), names="类别", values="ASIN数",
                 title="卖家属性（自营/第三方）", height=300)

# ---- 原始数据 ----
ui.section("8. 原始数据表")
cols = ["产品名称", "ASIN", "品牌", "实际价格($)", "预计Listing月销量", "Listing月销售额($)",
        "评分星级", "评价数量", "上架时间", "上架天数", "单个产品毛利($)", "单个产品毛利率(%)"]
st.dataframe(
    detail[cols],
    width="stretch",
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
