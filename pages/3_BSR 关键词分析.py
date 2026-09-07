"""BSR 关键词分析。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("BSR 关键词分析")

data = load_all()
kw = data["keyword"]
wc = data["wordcloud"]

# ---- KPI ----
k = kpi_mod.keyword_kpis(kw)
ui.kpi_cards([
    {"label": "关键词数量", "value": fmt.thousands(k["关键词数量"])},
    {"label": "平均月搜索量", "value": fmt.compact(k["平均月搜索量"])},
    {"label": "平均竞品数量", "value": fmt.thousands(k["平均竞品数量"])},
    {"label": "平均CPC", "value": fmt.usd(k["平均CPC($)"])},
])

# ---- 搜索量排行 / 分布 ----
ui.section("1. 搜索量排行与分布")
c1, c2 = st.columns(2)
with c1:
    d = kw.nlargest(20, "月搜索量")
    charts.hbar(d, x="月搜索量", y="关键词", title="Top20 关键词月搜索量")
with c2:
    charts.histogram(kw, x="月搜索量", title="月搜索量分布", nbins=40)

# ---- 搜索量 vs 竞争度 ----
ui.section("2. 搜索量 vs 竞争度")
c3, c4 = st.columns(2)
with c3:
    charts.scatter(kw, x="竞品数量", y="月搜索量", hover_name="关键词",
                   title="竞品数量 vs 搜索量")
with c4:
    d = kw.nlargest(50, "月搜索量")
    charts.treemap(d, path="关键词", values="月搜索量", title="Top50 关键词搜索量 Treemap")

# ---- 词云 ----
ui.section("3. 流量圈词云（重复次数 Treemap）")
if len(wc) > 0:
    wc_top = wc.nlargest(40, "重复次数")
    charts.treemap(wc_top, path="关键词", values="重复次数", title="词云关键词重复次数")
else:
    st.info("无词云数据")

# ---- 原始数据 ----
ui.section("4. 原始数据表")
cols = ["关键词", "旺季", "月搜索量", "年搜索量-2026年", "cpc精准竞价($)", "竞品数量",
        "周搜索排名", "90天购买量", "词搜索量复合增长率-近3个月(%)", "曝光点击垄断性(%)"]
st.dataframe(
    kw[cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "月搜索量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "年搜索量-2026年": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "cpc精准竞价($)": st.column_config.NumberColumn(format=fmt.USD_FMT),
        "竞品数量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "周搜索排名": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "90天购买量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "词搜索量复合增长率-近3个月(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "曝光点击垄断性(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
    },
)
