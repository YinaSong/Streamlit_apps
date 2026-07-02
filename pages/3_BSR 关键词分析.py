import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

#页面基本设置
st.set_page_config(page_title="BSR关键词分析", page_icon=":bar_chart:", layout="wide")

st.title("BSR关键词分析")

df_keywords = pd.read_excel("./data/BSR相关关键词.xlsx")


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

st.subheader("1.原始数据表")
if st.checkbox("查看原始BSR关键词数据表"):
    st.markdown(
        "数据表中包含了BSR关键词的相关信息"
    )
    st.markdown(">注：此处排序是按照月搜索量从大到小排序，如果需要对利用其它指标排序，请在数据表中点击对应列标题进行排序即可。\n"
                ">鼠标悬停在表格上，右下角提供筛选字段功能、下载功能、搜索功能")
    st.dataframe(
        df_keywords,
        use_container_width=True,
        column_config={
            "月搜索量": st.column_config.NumberColumn(format="%,.0f"),
            "年搜索量-2026年": st.column_config.NumberColumn(format="%,.2f"),
            "年搜索量-2025年": st.column_config.NumberColumn(format="%,.2f"),
            "年搜索量-2024年": st.column_config.NumberColumn(format="%,.2f"),
            "竞品数量": st.column_config.NumberColumn(format="%,.0f"),
            "词搜索量复合增长率(%)": st.column_config.NumberColumn(format="%.2f%%"),
            "曝光点击/转化(%)": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )
st.divider()