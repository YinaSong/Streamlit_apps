"""BSR 品牌竞争分析。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("BSR 品牌竞争分析")

data = load_all()
brand = data["brand"]

# ---- KPI（占比第一品牌 + AOSU） ----
b = kpi_mod.brand_kpis(brand)
ui.kpi_cards([
    {"label": "品牌数量", "value": fmt.thousands(b["品牌数量"])},
    {"label": "CR10(销量份额)", "value": f'{b["CR10销量份额%"]}%'},
    {"label": "占比第一品牌", "value": b["Top品牌"],
     "sub": f'销售额份额 {b["Top品牌销售额份额%"]}% · {fmt.compact_usd(b["Top品牌销售额"])}'},
    {"label": "AOSU", "value": f'排名 #{b["AOSU排名"]}',
     "sub": f'销售额份额 {b["AOSU销售额份额%"]}% · {fmt.compact_usd(b["AOSU销售额"])}'},
])

# ---- 排行 ----
ui.section("1. 品牌销量 / 销售额排行")
c1, c2 = st.columns(2)
with c1:
    d = brand.nlargest(15, "品牌产品listing月销量")
    charts.hbar(d, x="品牌产品listing月销量", y="品牌名称", title="品牌月销量排行")
with c2:
    d = brand.nlargest(15, "品牌产品listing月销额($)")
    charts.hbar(d, x="品牌产品listing月销额($)", y="品牌名称", title="品牌月销额排行")

# ---- 份额 ----
ui.section("2. 市场份额")
c3, c4 = st.columns(2)
with c3:
    charts.donut(brand, names="品牌名称", values="品牌产品listing月销量", title="销量份额")
with c4:
    charts.donut(brand, names="品牌名称", values="品牌产品listing月销额($)", title="销售额份额")

# ---- 规模 & 帕累托 ----
ui.section("3. 品牌规模与集中度")
c5, c6 = st.columns(2)
with c5:
    charts.scatter(
        brand, x="品牌产品listing月销量", y="品牌产品listing月销额($)",
        size="市场份额-产品销量份额占比(%)", hover_name="品牌名称",
        title="销量 vs 销额（气泡=销量份额）",
    )
with c6:
    charts.pareto(brand, x="品牌名称", y="品牌产品listing月销量", title="品牌销量帕累托图")

# ---- 品牌价格定位 ----
ui.section("4. 品牌价格定位（ASP）")
asp = kpi_mod.brand_asp(data["asin"]["detail"])
c7, c8 = st.columns(2)
with c7:
    charts.hbar(asp[asp["ASIN数"] >= 2].nlargest(15, "平均售价"),
                x="平均售价", y="品牌", title="品牌平均售价 ASP（Top15）")
with c8:
    charts.scatter(asp, x="ASIN数", y="平均售价", size="月销量", hover_name="品牌",
                   title="品牌价格定位（气泡=月销量）")

# ---- 原始数据 ----
ui.section("5. 原始数据表")
st.dataframe(
    brand,
    width="stretch",
    hide_index=True,
    column_config={
        "品牌产品listing月销量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "品牌产品listing月销额($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "市场份额-产品销量份额占比(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "市场份额-产品销售额份额占比(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "品牌下新品份额(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
    },
)
