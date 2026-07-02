import streamlit as st
import pandas as pd
from pathlib import Path

# 页面基础配置
st.set_page_config(
    page_title="Bullet Cameras类目分析报告",
    page_icon="📊",
    layout="wide"  # 宽屏布局更美观
)

st.title("Bullet Cameras 月度销售趋势看板 📈")
st.sidebar.success("Select a demo above.")

st.markdown(
    """
    <div style="
        background-color:#f5f5f5;
        border-left:4px solid #d9d9d9;
        padding:12px 16px;
        border-radius:8px;
        color:#666666;
        font-size:14px;
        line-height:1.8;
    ">
    💡 <b>使用说明</b><br>
    • 所有图表可以放大查看，鼠标悬停可查看详细数据。<br>
    • 右上角提供下载按钮，可导出为图片或 PDF。<br>
    • 支持拖动坐标轴范围进行缩放查看。
    </div>
    """,
    unsafe_allow_html=True
)


unit_seller = pd.read_excel("data/20260629_Bullet Cameras_售出件数趋势.xlsx")
BASE_DIR = Path(__file__).parent

ROOT = BASE_DIR.parent.parent

DATA_DIR = ROOT / "data"

unit_seller = pd.read_excel(DATA_DIR / "20260629_Bullet Cameras_售出件数趋势.xlsx")

# 清洗日期列，去除()
unit_seller["日期"] = unit_seller["日期"].str.replace("()", "", regex=False)
# 转为日期格式，方便绘图排序
unit_seller["date_dt"] = pd.to_datetime(unit_seller["日期"] + "-01")

# 数据预览
st.subheader("1.原始数据表")
if st.checkbox('展示原始数据'):
    st.dataframe(
        unit_seller.style.format({
            "售出件数": "{:,}",
            "净销售额($)": "{:,}"
        }),
        use_container_width=True
    )

# 顶部指标汇总
col1, col2, col3 = st.columns(3)
total_units = unit_seller["售出件数"].sum()
total_sales = unit_seller["净销售额($)"].sum()
avg_month_sales = unit_seller["净销售额($)"].mean()

with col1:
    st.metric("总售出件数", f"{total_units:,}")
with col2:
    st.metric("总净销售额($)", f"{total_sales:,}")
with col3:
    st.metric("月均销售额($)", f"{round(avg_month_sales):,}")

import plotly.express as px
st.divider()
st.subheader("2.月度销售趋势分析")
# 售出件数折线
fig_unit = px.line(
    unit_seller,
    x="date_dt",
    y="售出件数",
    title="月度售出件数趋势",
    markers=True
)
# 柔和曲线、渐变填充阴影、美化细节
fig_unit.update_traces(
    line_shape="spline",  # 柔和平滑曲线
    fill="tozeroy",       # 填充曲线下方区域
    line_color="#409EFF",
    fillcolor="rgba(64,158,255,0.2)",
    marker=dict(size=6, color="#409EFF", line=dict(width=1, color="white"))
)
fig_unit.update_layout(
    xaxis=dict(
        rangeslider=dict(visible=True),
        type="date"
    ),
    plot_bgcolor="white",
    hoverlabel=dict(font_size=12),
    margin=dict(l=40, r=20, t=40, b=20)
)
st.plotly_chart(fig_unit, use_container_width=True)

# 销售额折线
fig_sales = px.line(
    unit_seller,
    x="date_dt",
    y="净销售额($)",
    title="月度净销售额($)趋势",
    markers=True
)
fig_sales.update_traces(
    line_shape="spline",
    fill="tozeroy",
    line_color="#67C23A",
    fillcolor="rgba(103,194,58,0.2)",
    marker=dict(size=6, color="#67C23A", line=dict(width=1, color="white"))
)
fig_sales.update_layout(
    xaxis=dict(
        rangeslider=dict(visible=True),
        type="date"
    ),
    plot_bgcolor="white",
    hoverlabel=dict(font_size=12),
    margin=dict(l=40, r=20, t=40, b=20)
)
st.plotly_chart(fig_sales, use_container_width=True)
st.divider()

df_country = pd.read_excel("./data/20260702_Bullet Cameras_全球售卖对比分析.xlsx")

st.subheader("3.全球售卖对比分析")
df_country 