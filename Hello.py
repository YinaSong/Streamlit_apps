"""Bullet Cameras 类目分析 —— 市场总览（多站点）。"""
import streamlit as st

from utils import charts, formatters as fmt, kpi as kpi_mod
from utils.data_loader import load_all
from components import ui

ui.page_title("Bullet Cameras 市场总览")

site = ui.site_selector()
data = load_all(site)
cur = data["currency"]
cfmt = data["currency_fmt"]
meta = data["market_meta"]

st.caption(
    f"数据来源：Sorftime 专业版导出（{meta.get('一级大类', '—')} → {meta.get('类目名称', '—')} · 站点 {site}）"
)

asin_summary = kpi_mod.summary_kpis(data["asin"]["summary"])
dt = data["data_time"]

# ---- 数据时间来源 ----
src = "数据导出时间：" + (dt.get("asin_export") or "—")
if dt.get("sales_latest"):
    src += f" · 销量趋势截至 {dt['sales_latest']}"
src += "（注：最近月份数据可能未完整统计）"
ui.data_source(src)


def _last_two(df, date_col, val_col):
    d = df.sort_values(date_col).reset_index(drop=True)
    if len(d) < 2:
        return None, None
    return d.iloc[-1][val_col], d.iloc[-2][val_col]


def _delta(cur, prev):
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 1)


# ---- 销量/销售额趋势源：US/DE 用售出件数趋势，CA/FR 降级用市场趋势 ----
sales_trend = data["sales_trend"]
if sales_trend is not None:
    trend = sales_trend.sort_values("date").reset_index(drop=True).copy()
    trend["月份"] = trend["date"].dt.strftime("%Y-%m")
    x_col, sales_col, rev_col = "月份", "售出件数", "净销售额($)"
    sales_lbl, rev_lbl = "售出件数", "净销售额"
else:
    st.info("该站点无「售出件数趋势」，改用市场趋势的类目销量/销售额（口径略有差异）。")
    trend = data["market_trend"].copy()
    trend["月份"] = trend["月份"].astype(str)
    trend = trend.sort_values("月份").reset_index(drop=True)
    x_col, sales_col, rev_col = "月份", "类目销量", "类目销售额"
    sales_lbl, rev_lbl = "类目销量", "类目销售额"

cur_sales, prev_sales = _last_two(trend, x_col, sales_col)
cur_rev, prev_rev = _last_two(trend, x_col, rev_col)

# ---- KPI 卡片（当月 + 上月 + 环比） ----
ui.kpi_cards([
    {
        "label": f"市场月销量（{sales_lbl}）",
        "value": fmt.compact(cur_sales),
        "sub": f"上月 {fmt.compact(prev_sales)}",
        "delta": _delta(cur_sales, prev_sales),
    },
    {
        "label": f"市场月销售额（{rev_lbl}）",
        "value": fmt.money_compact(cur_rev, cur),
        "sub": f"上月 {fmt.money_compact(prev_rev, cur)}",
        "delta": _delta(cur_rev, prev_rev),
    },
    {"label": "品牌数", "value": fmt.thousands(asin_summary["品牌数量"])},
    {"label": "ASIN数(Top100)", "value": fmt.thousands(asin_summary["产品数"])},
    {"label": "Seller数", "value": fmt.thousands(asin_summary["卖家数量"])},
])

# ---- 图1：销量 / 销售额趋势（双轴） ----
ui.section("1. 市场销量 & 销售额趋势")
charts.line(
    trend, x=x_col, y=sales_col, y2=rev_col,
    title=f"月度{sales_lbl} vs {rev_lbl}",
)

# ---- 图2：环比 / 同比 ----
ui.section("2. 环比（按月） & 同比（按年）")
mom_yoy = kpi_mod.mom_yoy_table(trend, sales_col, date_col=x_col)
c1, c2 = st.columns(2)
with c1:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["环比%"].tolist(),
        title=f"{sales_lbl}环比 MoM（%）",
    )
with c2:
    charts.rise_fall_bar(
        mom_yoy["月份"].tolist(), mom_yoy["同比%"].tolist(),
        title=f"{sales_lbl}同比 YoY（%）",
    )

# ---- 图3：全球市场 & 价格带 ----
ui.section("3. 全球市场 & 价格带")
c3, c4 = st.columns(2)
with c3:
    g = data["global"].dropna(subset=["Top100月销量"]).sort_values("Top100月销量", ascending=False)
    charts.hbar(g, x="Top100月销量", y="站点", title="各站点 Top100 月销量")
with c4:
    charts.histogram(data["asin"]["detail"], x="实际价格($)", title="价格带分布", nbins=30)

# ---- 图4：品牌份额 & Top10（品牌销量仅 US 有） ----
ui.section("4. 品牌份额 & Top10 品牌")
if data["brand"] is not None:
    c5, c6 = st.columns(2)
    with c5:
        charts.treemap(
            data["brand"], path="品牌名称", values="品牌产品listing月销额($)",
            title="品牌销售额 Treemap",
        )
    with c6:
        top10 = data["brand"].nlargest(10, "品牌产品listing月销额($)")
        charts.hbar(top10, x="品牌产品listing月销额($)", y="品牌名称", title="Top10 品牌月销额")
else:
    st.info("该站点无品牌销量数据（品牌销量仅 US 有）。")

# ---- 图5：Top20 产品（含 ASIN + 链接） ----
ui.section("5. Top20 产品")
detail = data["asin"]["detail"]
top20 = detail.nlargest(20, "预计Listing月销量")[
    ["产品名称", "ASIN", "URL", "品牌", "实际价格($)", "预计Listing月销量",
     "Listing月销售额($)", "评分星级", "评价数量"]
]
st.dataframe(
    top20,
    width="stretch",
    hide_index=True,
    column_config={
        "URL": st.column_config.LinkColumn("链接", display_text="Amazon ↗"),
        "实际价格($)": st.column_config.NumberColumn(format=cfmt),
        "预计Listing月销量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "Listing月销售额($)": st.column_config.NumberColumn(format=cfmt),
        "评分星级": st.column_config.NumberColumn(format="%.1f"),
        "评价数量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
    },
)

ui.usage_note()
