import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts
import plotly.express as px


# 页面基础配置
st.set_page_config(
    page_title="Top100 ASIN分析报告",
    page_icon="📊",
    layout="wide"  # 宽屏布局更美观
)

color = px.colors.sequential.Pinkyl

st.title("Bullet Cameras BSR-Top100 ASIN分析报告 📈")

df_product = pd.read_excel('./data/BSR ASIN产品列表.xlsx')

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
if st.checkbox("查看原始ASIN数据表"):
    st.markdown(
        "数据表中包含了各ASIN的月销量、月销额以及市场份额占比等信息，方便进行ASIN分析和比较。"
    )
    st.markdown(">注：此处排序是按照ASIN月度预估销量从大到小排序，如果需要对利用其它指标排序，请在数据表中点击对应列标题进行排序即可。\n"
                ">鼠标悬停在表格上，右下角提供筛选字段功能、下载功能、搜索功能")
    st.dataframe(
        df_product,
        use_container_width=True,
        column_config={
            "ASIN产品listing月销量": st.column_config.NumberColumn(format="%,.0f"),
            "ASIN产品listing月销额($)": st.column_config.NumberColumn(format="$%,.2f"),
            "市场份额-产品销量份额占比(%)": st.column_config.NumberColumn(format="%.2f%%"),
            "市场份额-产品销售额份额占比(%)": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )
st.divider()

st.subheader("2. BSR ASIN月销量占比")
show_num = st.segmented_control(
    "展示范围",
    options=["全部", "Top50", "Top20", "Top10"],
    default="Top20"
)
if show_num == "全部":
    df_qty = df_product
    df_amt = df_product
else:
    n = int(show_num.replace("Top", ""))

    df_qty = (
        df_product
        .nlargest(n, "预计Listing月销量")
    )

    df_amt = (
        df_product
        .nlargest(n, "Listing月销售额($)")
    )
def rose_option(data, title, value_name, value_format="number"):
    return {
        "color": color,

        "title": {
            "text": title,
            "left": "center",
            "top": 10,
            "textStyle": {
                "fontSize": 18,
                "fontWeight": "bold",
                "color": "#2F3B52"
            }
        },

        "tooltip": {
            "trigger": "item",
            "backgroundColor": "#ffffff",
            "borderColor": "#E5E7EB",
            "borderWidth": 1,
            "textStyle": {
                "color": "#333",
                "fontSize": 13
            },
            "formatter":
                f"<b>{{b}}</b><br/>{value_name}：{{c}}<br/>占整体：{{d}}%"
        },

        "legend": {
            "type": "scroll",
            "orient": "vertical",
            "right": 5,
            "top": 40,
            "bottom": 20,
            "icon": "circle",
            "textStyle": {
                "fontSize": 12
            }
        },

        "animationDuration": 1000,

        "series": [
            {
                "type": "pie",
                # "roseType": "radius",

                "radius": ["0%", "72%"],
                "center": ["38%", "55%"],

                "data": data,

                "label": {
                    "show": False
                },

                "itemStyle": {
                    "borderColor": "#ffffff",
                    "borderWidth": 2
                },

                "emphasis": {
                    "scale": True,
                    "scaleSize": 10,

                    "itemStyle": {
                        "shadowBlur": 18,
                        "shadowColor": "rgba(0,0,0,0.25)"
                    },

                    "label": {
                        "show": True,
                        "fontSize": 14,
                        "fontWeight": "bold",
                        "formatter":
                            f"{{b}}\n{value_name}：{{c}}\n{{d}}%"
                    }
                }
            }
        ]
    }
col1, col2 = st.columns(2)

# 饼图1：销量市场份额
with col1:

    st.subheader("预计月销量市场份额占比")
    
    data_qty = (
        df_qty.sort_values(
            "预计Listing月销量",
            ascending=False
        )[["ASIN", "预计Listing月销量"]]
        .rename(columns={
            "ASIN": "name",
            "预计Listing月销量": "value"
        })
        .to_dict("records")
    )

    st_echarts(
        options=rose_option(
            data_qty,
            "各asin预计月销量份额",
            "预计月销量"
        ),
        height="550px"
    )

# 饼图2：销售额市场份额
with col2:

    st.subheader("月销售额市场份额占比")

    data_amt = (
        df_amt.sort_values(
            "Listing月销售额($)",
            ascending=False
        )[["ASIN", "Listing月销售额($)"]]
        .rename(columns={
            "ASIN": "name",
            "Listing月销售额($)": "value"
        })
        .to_dict("records")
    )

    st_echarts(
        options=rose_option(
            data_amt,
            "各asin预计月销售额份额",
            "Listing月销售额($)"
        ),
        height="550px"
    )

st.divider()

st.subheader("3. BSR ASIN月销量趋势分析")
# ---------------------- 数据清洗 ----------------------
df_product_clean = df_product.copy()
# 清洗销量数值列，脏值统一替换为0
num_cols = ["预计Listing月销量", "Listing年销量"]
for c in num_cols:
    df_product_clean[c] = pd.to_numeric(df_product_clean[c], errors="coerce").fillna(0)

# 1. 品牌聚合计算
brand_agg = df_product_clean.groupby("品牌").agg(
    ASIN数量=("ASIN", "count"),
    合计月销量=("预计Listing月销量", "sum"),
    合计年销量=("Listing年销量", "sum")
).reset_index()

st.subheader("品牌对比：总月销量(柱状) + ASIN数量(折线)")
brand_agg = (
    brand_agg
    .sort_values("合计月销量", ascending=False)
    .reset_index(drop=True)
)

option1 = {
    "animationDuration": 1000,

    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "shadow"}
    },

    "legend": {
        "top": 5,
        "data": ["品牌总月销量", "ASIN数量"]
    },

    "grid": {
        "left": "5%",
        "right": "5%",
        "bottom": "10%",
        "containLabel": True
    },

    "xAxis": {
        "type": "category",
        "data": brand_agg["品牌"].tolist(),
        "axisLabel": {
            "rotate": 30
        }
    },

    "yAxis": [
        {
            "type": "value",
            "name": "月销量",
            "splitLine": {
                "lineStyle": {
                    "type": "dashed",
                    "color": "#EEEEEE"
                }
            }
        },
        {
            "type": "value",
            "name": "ASIN数"
        }
    ],

    "series": [
        {
            "name": "品牌总月销量",
            "type": "bar",
            "data": brand_agg["合计月销量"].tolist(),

            "barWidth": "45%",

            "itemStyle": {
                "borderRadius": [6,6,0,0],
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#5B8FF9"},
                        {"offset": 1, "color": "#BDD7FF"}
                    ]
                }
            },

            "emphasis": {
                "focus": "series"
            }
        },

        {
            "name": "ASIN数量",
            "type": "line",

            "smooth": True,

            "yAxisIndex": 1,

            "data": brand_agg["ASIN数量"].tolist(),

            "symbol": "circle",
            "symbolSize": 8,

            "lineStyle": {
                "width": 3
            },

            "itemStyle": {
                "color": "#F6BD16"
            }
        }
    ],

    "dataZoom":[
    {
        "type":"inside"
    },
    {
        "type":"slider",
        "height":18,
        "bottom":0
    }
],
}

st_echarts(option1, height="520px")


# ========== 第二张图：柱状=合计年销量，折线=ASIN数量（仅年销量>0品牌） ==========


brand_agg_year = (
    brand_agg[brand_agg["合计年销量"] > 0]
    .sort_values("合计年销量", ascending=False)
    .reset_index(drop=True)
)
option2 = {
    "animationDuration":1000,

    "tooltip":{
        "trigger":"axis",
        "axisPointer":{
            "type":"shadow"
        }
    },

    "legend":{
        "top":5,
        "data":[
            "品牌总年销量",
            "ASIN数量"
        ]
    },

    "grid":{
        "left":"5%",
        "right":"5%",
        "bottom":"10%",
        "containLabel":True
    },

    "xAxis":{
        "type":"category",
        "data":brand_agg_year["品牌"].tolist(),
        "axisLabel":{
            "rotate":30
        }
    },

    "yAxis":[
        {
            "type":"value",
            "name":"年销量",
            "splitLine":{
                "lineStyle":{
                    "type":"dashed",
                    "color":"#EEEEEE"
                }
            }
        },
        {
            "type":"value",
            "name":"ASIN数"
        }
    ],

    "series":[
        {
            "name":"品牌总年销量",

            "type":"bar",

            "data":brand_agg_year["合计年销量"].tolist(),

            "barWidth":"45%",

            "itemStyle": {
                "borderRadius": [6,6,0,0],
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#4E79A7"},
                        {"offset": 1, "color": "#A0CBE8"}
                    ]
                }
            }
        },

        {
            "name":"ASIN数量",

            "type":"line",

            "smooth":True,

            "yAxisIndex":1,

            "data":brand_agg_year["ASIN数量"].tolist(),

            "symbol":"circle",

            "symbolSize":8,

            "lineStyle":{
                "width":3
            },

            "itemStyle":{
                "color":"#F28E2B"
            }
        }
    ],
    "dataZoom":[
    {
        "type":"inside"
    },
    {
        "type":"slider",
        "height":18,
        "bottom":0
    }
    ]
}

st_echarts(option2, height="520px")

st.divider()

# ---------------------- 数据清洗 ----------------------
df_product_clean = df_product.copy()
# 清洗销量数值列，脏值统一替换为0
num_cols = ["预计Listing月销量", "Listing年销量"]
for c in num_cols:
    df_product_clean[c] = pd.to_numeric(df_product_clean[c], errors="coerce").fillna(0)

# 1. 店铺聚合计算
shop_agg = df_product_clean.groupby("店铺").agg(
    ASIN数量=("ASIN", "count"),
    合计月销量=("预计Listing月销量", "sum"),
    合计年销量=("Listing年销量", "sum")
).reset_index()

st.subheader("店铺对比：总月销量(柱状) + ASIN数量(折线)")
shop_agg = (
    shop_agg
    .sort_values("合计月销量", ascending=False)
    .reset_index(drop=True)
)

option1 = {
    "animationDuration": 1000,

    "tooltip": {
        "trigger": "axis",
        "axisPointer": {"type": "shadow"}
    },

    "legend": {
        "top": 5,
        "data": ["店铺总月销量", "ASIN数量"]
    },

    "grid": {
        "left": "5%",
        "right": "5%",
        "bottom": "10%",
        "containLabel": True
    },

    "xAxis": {
        "type": "category",
        "data": shop_agg["店铺"].tolist(),
        "axisLabel": {
            "rotate": 30
        }
    },

    "yAxis": [
        {
            "type": "value",
            "name": "月销量",
            "splitLine": {
                "lineStyle": {
                    "type": "dashed",
                    "color": "#EEEEEE"
                }
            }
        },
        {
            "type": "value",
            "name": "ASIN数"
        }
    ],

    "series": [
        {
            "name": "店铺总月销量",
            "type": "bar",
            "data": shop_agg["合计月销量"].tolist(),

            "barWidth": "45%",

            "itemStyle": {
                "borderRadius": [6,6,0,0],
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#5B8FF9"},
                        {"offset": 1, "color": "#BDD7FF"}
                    ]
                }
            },

            "emphasis": {
                "focus": "series"
            }
        },

        {
            "name": "ASIN数量",
            "type": "line",

            "smooth": True,

            "yAxisIndex": 1,

            "data": shop_agg["ASIN数量"].tolist(),

            "symbol": "circle",
            "symbolSize": 8,

            "lineStyle": {
                "width": 3
            },

            "itemStyle": {
                "color": "#F6BD16"
            }
        }
    ],

    "dataZoom":[
    {
        "type":"inside"
    },
    {
        "type":"slider",
        "height":18,
        "bottom":0
    }
],
}

st_echarts(option1, height="520px")


# ========== 第二张图：柱状=合计年销量，折线=ASIN数量（仅年销量>0品牌） ==========


shop_agg_year = (
    shop_agg[shop_agg["合计年销量"] > 0]
    .sort_values("合计年销量", ascending=False)
    .reset_index(drop=True)
)
option2 = {
    "animationDuration":1000,

    "tooltip":{
        "trigger":"axis",
        "axisPointer":{
            "type":"shadow"
        }
    },

    "legend":{
        "top":5,
        "data":[
            "店铺总年销量",
            "ASIN数量"
        ]
    },

    "grid":{
        "left":"5%",
        "right":"5%",
        "bottom":"10%",
        "containLabel":True
    },

    "xAxis":{
        "type":"category",
        "data":shop_agg_year["店铺"].tolist(),
        "axisLabel":{
            "rotate":30
        }
    },

    "yAxis":[
        {
            "type":"value",
            "name":"年销量",
            "splitLine":{
                "lineStyle":{
                    "type":"dashed",
                    "color":"#EEEEEE"
                }
            }
        },
        {
            "type":"value",
            "name":"ASIN数"
        }
    ],

    "series":[
        {
            "name":"店铺总年销量",

            "type":"bar",

            "data":shop_agg_year["合计年销量"].tolist(),

            "barWidth":"45%",

            "itemStyle": {
                "borderRadius": [6,6,0,0],
                "color": {
                    "type": "linear",
                    "x": 0,
                    "y": 0,
                    "x2": 0,
                    "y2": 1,
                    "colorStops": [
                        {"offset": 0, "color": "#4E79A7"},
                        {"offset": 1, "color": "#A0CBE8"}
                    ]
                }
            }
        },

        {
            "name":"ASIN数量",

            "type":"line",

            "smooth":True,

            "yAxisIndex":1,

            "data":shop_agg_year["ASIN数量"].tolist(),

            "symbol":"circle",

            "symbolSize":8,

            "lineStyle":{
                "width":3
            },

            "itemStyle":{
                "color":"#F28E2B"
            }
        }
    ],
    "dataZoom":[
    {
        "type":"inside"
    },
    {
        "type":"slider",
        "height":18,
        "bottom":0
    }
    ]
}

st_echarts(option2, height="520px")
st.divider()

# 4.星级分布+价格分布
# 打造顶端指标卡
st.subheader("4. BSR ASIN星级分布 + 价格分布")
col1,col2,col3= st.columns(3)
with col1:
    st.metric("平均星级", f"{df_product_clean['评分星级'].mean():.2f} 星")

with col2:
    st.metric("平均价格", f"${df_product['目前销售价($)'].mean():.2f}")

with col3:
    st.metric("平均评论数", f"{df_product_clean['评价数量'].mean():.0f} 条")

col1, col2 = st.columns(2)
# ========== 左侧：星级分布 ==========
with col1:
    st.subheader("BSR 星级分布")
    star_counts = df_product_clean["评分星级"].value_counts().sort_index()
    star_percentages = (star_counts / star_counts.sum() * 100).round(2)

    star_df = pd.DataFrame({
        "评分星级": star_counts.index,
        "产品数量": star_counts.values,
        "占比(%)": star_percentages.values
    })

    # Streamlit原生柱状图：X=星级，Y=产品数量
    st.bar_chart(
        data=star_df,
        x="评分星级",
        y="产品数量",
        use_container_width=True,
        height=300
    )

# ========== 右侧：价格分布 ==========
with col2:
    st.subheader("BSR 价格分布")
    price_counts = df_product["目前销售价($)"].value_counts().sort_index()
    price_percentages = (price_counts / price_counts.sum() * 100).round(2)

    price_df = pd.DataFrame({
        "目前销售价($)": price_counts.index,
        "产品数量": price_counts.values,
        "占比(%)": price_percentages.values
    })

    # Streamlit原生柱状图：X=售价，Y=产品数量
    st.bar_chart(
        data=price_df,
        x="目前销售价($)",
        y="产品数量",
        use_container_width=True,
        height=300
    )
