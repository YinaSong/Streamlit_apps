"""New Release 新品机会分析。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("New Release 新品分析")

data = load_all()
nr = data["new_release"]
detail = nr["detail"]
variants = nr["variants"]
summ = kpi_mod.summary_kpis(nr["summary"])

# ---- KPI ----
ui.kpi_cards([
    {"label": "新品数量", "value": fmt.thousands(summ["产品数"])},
    {"label": "新品月总销量", "value": fmt.compact(summ["月总销量"])},
    {"label": "新品月总销售额", "value": fmt.compact_usd(summ["月总销售额($)"])},
    {"label": "新品占比", "value": fmt.percent(summ["新品占比(%)(默认三个月)"])},
    {"label": "平均价格", "value": fmt.usd(summ["平均价格($)"])},
    {"label": "平均星级", "value": f'{summ["平均星级"]:.1f}' if summ["平均星级"] is not None else "—"},
])

# ---- 新品销量排行 / 上架时间分布 ----
ui.section("1. 新品销量排行与上架节奏")
c1, c2 = st.columns(2)
with c1:
    d = detail.nlargest(15, "预计Listing月销量").copy()
    d["品牌 · ASIN"] = d["品牌"].fillna("—").astype(str) + " · " + d["ASIN"].astype(str)
    charts.hbar(d, x="预计Listing月销量", y="品牌 · ASIN", title="新品销量 Top15")
with c2:
    charts.histogram(detail, x="上架时间", title="上架时间分布", nbins=20)

# ---- 价格带 / 变体 ----
ui.section("2. 新品价格带与变体分析")
c3, c4 = st.columns(2)
with c3:
    charts.histogram(detail, x="实际价格($)", title="新品价格带", nbins=25)
with c4:
    if len(variants) > 0:
        v = variants.dropna(subset=["子体销量"])
        charts.scatter(v, x="价格($)", y="子体销量", hover_name="变体ASIN",
                       title="变体价格 vs 子体销量")
    else:
        st.info("无变体数据")

# ---- 品牌/卖家新增 ----
ui.section("3. 品牌 / 卖家分布")
brand_cnt = detail["品牌"].value_counts().reset_index()
brand_cnt.columns = ["品牌", "新品数量"]
seller_cnt = detail["店铺"].value_counts().reset_index()
seller_cnt.columns = ["店铺", "新品数量"]
c5, c6 = st.columns(2)
with c5:
    charts.hbar(brand_cnt.head(15), x="新品数量", y="品牌", title="品牌新品数量 Top15")
with c6:
    charts.hbar(seller_cnt.head(15), x="新品数量", y="店铺", title="卖家新品数量 Top15")

# ---- 属性词挖掘 ----
ui.section("4. 属性词挖掘（新品卖点/属性）")
attr_cols = ["五点描述", "Special Feature", "Connectivity Technology",
             "Indoor/Outdoor Usage", "Recommended Uses For Product"]
attr = kpi_mod.attr_words(detail, attr_cols)
c7, c8 = st.columns(2)
with c7:
    charts.hbar(attr.nlargest(15, "覆盖产品数"), x="覆盖产品数", y="词",
                title="属性词覆盖新品数 Top15")
with c8:
    charts.hbar(attr.nlargest(15, "词月销量"), x="词月销量", y="词",
                title="属性词关联月销量 Top15")

# ---- 原始数据 ----
ui.section("5. 原始数据表")
cols = ["产品名称", "ASIN", "品牌", "店铺", "实际价格($)", "预计Listing月销量", "Listing月销售额($)",
        "评分星级", "评价数量", "上架时间", "上架天数", "国籍/地区"]
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
        "上架时间": st.column_config.DateColumn(format="YYYY-MM-DD"),
    },
)
