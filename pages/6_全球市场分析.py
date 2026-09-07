"""全球市场对比分析（14 个站点）。"""
import streamlit as st

from utils import charts, formatters as fmt
from utils.data_loader import load_all
from components import ui

ui.page_title("全球市场对比分析")

data = load_all()
g = data["global"]

has_data = g[g["是否有数据"]]
no_data = g[~g["是否有数据"]]

top_site = has_data.loc[has_data["Top100月销量"].idxmax(), "站点"] if len(has_data) else "—"
top_val = has_data.loc[has_data["Top100月销量"].idxmax(), "Top100月销量"] if len(has_data) else None

# ---- 概览 ----
ui.kpi_cards([
    {"label": "覆盖站点数", "value": fmt.thousands(len(has_data)),
     "sub": f"共 {len(g)} 个站点"},
    {"label": "销量最高站点", "value": top_site,
     "sub": f"Top100月销量 {fmt.compact(top_val)}"},
    {"label": "无数据站点", "value": fmt.thousands(len(no_data)),
     "sub": "、".join(no_data["站点"].tolist()) if len(no_data) else "无"},
])

# ---- 销量 / 销额排行 ----
ui.section("1. 各站点销量 / 销额排行")
c1, c2 = st.columns(2)
with c1:
    d = has_data.sort_values("Top100月销量")
    charts.hbar(d, x="Top100月销量", y="站点", title="各站点 Top100 月销量")
with c2:
    d = has_data.sort_values("Top100月销额")
    charts.hbar(d, x="Top100月销额", y="站点", title="各站点 Top100 月销额（本地货币）")

# ---- 垄断 / 新品占比 ----
ui.section("2. 垄断系数与新品占比")
c3, c4 = st.columns(2)
with c3:
    d = has_data.sort_values("垄断系数")
    charts.hbar(d, x="垄断系数", y="站点", title="前3产品销量垄断系数(%)")
with c4:
    d = has_data.dropna(subset=["新品占比"]).sort_values("新品占比")
    charts.hbar(d, x="新品占比", y="站点", title="3个月内新品占比(%)")

# ---- 原始数据 ----
ui.section("3. 站点概览表")
st.dataframe(
    g[["站点", "相似类目", "货币", "Top100月销量", "Top100月销额", "垄断系数", "新品占比"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Top100月销量": st.column_config.NumberColumn(format=fmt.NUM_FMT),
        "Top100月销额": st.column_config.NumberColumn(format=fmt.NUM_FMT_2),
        "垄断系数": st.column_config.NumberColumn(format=fmt.PCT_FMT),
        "新品占比": st.column_config.NumberColumn(format=fmt.PCT_FMT),
    },
)

if len(no_data):
    st.info(f"以下站点未找到相似类目，无销量数据：{'、'.join(no_data['站点'].tolist())}")
