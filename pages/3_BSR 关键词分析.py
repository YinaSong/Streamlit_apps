"""BSR 关键词分析。"""
import pandas as pd
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("BSR 关键词分析")

site = ui.site_selector()
data = load_all(site)
cur = data["currency"]
cfmt = data["currency_fmt"]
kw = data["keyword"]
wc = data["wordcloud"]

if kw is None:
    st.info("该站点无关键词数据。")
    st.stop()

# ---- KPI ----
k = kpi_mod.keyword_kpis(kw)
ui.kpi_cards([
    {"label": "关键词数量", "value": fmt.thousands(k["关键词数量"])},
    {"label": "平均月搜索量", "value": fmt.compact(k["平均月搜索量"])},
    {"label": "平均竞品数量", "value": fmt.thousands(k["平均竞品数量"])},
    {"label": "平均CPC", "value": fmt.money(k["平均CPC($)"], cur)},
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
if wc is not None and len(wc) > 0:
    wc_top = wc.nlargest(40, "重复次数")
    charts.treemap(wc_top, path="关键词", values="重复次数", title="词云关键词重复次数")
else:
    st.info("无词云数据")

# ---- 竞价与竞争度分析 ----
ui.section("4. 竞价与竞争度分析")
c5, c6 = st.columns(2)
with c5:
    if "cpc精准竞价($)" in kw.columns:
        charts.scatter(kw, x="月搜索量", y="cpc精准竞价($)", size="竞品数量",
                       hover_name="关键词", title="搜索量 vs CPC 竞价（气泡=竞品数量）")
    else:
        st.info("该站点无「cpc 竞价」字段")
with c6:
    comp = kw[["关键词", "自然位竞争", "广告位竞争", "月搜索量"]].copy()
    comp["自然位竞争度"] = kpi_mod.competition_ratio(comp["自然位竞争"])
    comp["广告位竞争度"] = kpi_mod.competition_ratio(comp["广告位竞争"])
    charts.scatter(comp, x="自然位竞争度", y="广告位竞争度", size="月搜索量",
                   hover_name="关键词", title="自然位 vs 广告位 竞争度（气泡=月搜索量）")

# ---- 转化率与垄断性分析（DE 等站点可能缺转化率列） ----
ui.section("5. 转化率与垄断性分析")
c7, c8 = st.columns(2)
with c7:
    if {"近90日搜索转化率（%）", "近90日点击转化率（%）"} <= set(kw.columns):
        charts.scatter(kw, x="近90日搜索转化率（%）", y="近90日点击转化率（%）",
                       size="月搜索量", hover_name="关键词",
                       title="搜索转化率 vs 点击转化率（气泡=月搜索量）")
    else:
        st.info("该站点无「近90日搜索/点击转化率」字段")
with c8:
    if {"曝光点击垄断性(%)", "曝光转化垄断性(%)"} <= set(kw.columns):
        charts.scatter(kw, x="曝光点击垄断性(%)", y="曝光转化垄断性(%)",
                       size="月搜索量", hover_name="关键词",
                       title="点击垄断性 vs 转化垄断性（气泡=月搜索量）")
    else:
        st.info("该站点无「曝光点击/转化垄断性」字段")

# ---- 增长趋势 ----
ui.section("6. 增长趋势（年度 & 复合增长率）")
c9, c10 = st.columns(2)
with c9:
    yearly = pd.DataFrame({
        "年份": ["2024年", "2025年", "2026年(年初至今)"],
        "总搜索量": [kw["年搜索量-2024年"].sum(),
                     kw["年搜索量-2025年"].sum(),
                     kw["年搜索量-2026年"].sum()],
    })
    charts.line(yearly, x="年份", y="总搜索量", title="关键词年度总搜索量")
with c10:
    g = kw[["关键词", "词搜索量复合增长率-近6个月(%)",
            "词搜索量复合增长率-近12个月(%)", "月搜索量"]].dropna().copy()
    for col in ["词搜索量复合增长率-近6个月(%)", "词搜索量复合增长率-近12个月(%)"]:
        lo, hi = g[col].quantile(0.01), g[col].quantile(0.99)
        g[col] = g[col].clip(lo, hi)
    charts.scatter(g, x="词搜索量复合增长率-近12个月(%)",
                   y="词搜索量复合增长率-近6个月(%)", size="月搜索量",
                   hover_name="关键词",
                   title="近6月 vs 近12月 复合增长率（已裁尾，气泡=月搜索量）")

# ---- 标题词分析 ----
ui.section("7. 标题词分析（从 Top100 标题挖词）")
detail = data["asin"]["detail"]
tw = kpi_mod.title_words(detail)
tb = kpi_mod.title_bigrams(detail)
c11, c12 = st.columns(2)
with c11:
    charts.treemap(tw.head(40), path="词", values="词频", title="标题高频词 Treemap")
with c12:
    charts.hbar(tb.head(20), x="词频", y="词", title="标题高频词组（bigram）Top20")

# ---- 原始数据 ----
ui.section("8. 原始数据表")
cols = ["关键词", "旺季", "月搜索量", "年搜索量-2024年", "年搜索量-2025年", "年搜索量-2026年",
        "cpc精准竞价($)", "cpc最低竞价($)", "cpc最高竞价($)", "竞品数量", "周搜索排名", "周搜索排名变化",
        "90天购买量", "近90日搜索转化率（%）", "近90日点击转化率（%）",
        "词搜索量复合增长率-近3个月(%)", "词搜索量复合增长率-近6个月(%)", "词搜索量复合增长率-近12个月(%)",
        "曝光点击垄断性(%)", "曝光转化垄断性(%)"]
cols = [c for c in cols if c in kw.columns]
st.dataframe(
    kw[cols],
    width="stretch",
    hide_index=True,
    column_config={
        "月搜索量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "年搜索量-2024年": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "年搜索量-2025年": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "年搜索量-2026年": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "cpc精准竞价($)": st.column_config.NumberColumn(format=cfmt),
        "cpc最低竞价($)": st.column_config.NumberColumn(format=cfmt),
        "cpc最高竞价($)": st.column_config.NumberColumn(format=cfmt),
        "竞品数量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "周搜索排名": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "周搜索排名变化": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "90天购买量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "近90日搜索转化率（%）": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "近90日点击转化率（%）": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "词搜索量复合增长率-近3个月(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "词搜索量复合增长率-近6个月(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "词搜索量复合增长率-近12个月(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "曝光点击垄断性(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "曝光转化垄断性(%)": st.column_config.NumberColumn(format=fmt.PCT_FMT),
    },
)
