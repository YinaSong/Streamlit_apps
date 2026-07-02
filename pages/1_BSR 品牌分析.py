import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_echarts import st_echarts

# 页面基础配置
st.set_page_config(
    page_title="Top100 分析报告",
    page_icon="📊",
    layout="wide"  # 宽屏布局更美观
)

color = [
    "#4E79A7",    "#A0CBE8",    "#59A14F",
    "#8CD17D",    "#F28E2B",    "#FFBE7D",
    "#76B7B2",    "#B6992D",
]

st.title("Bullet Cameras BSR-Top100 品牌分析报告 📈")

df_brand = pd.read_excel('./data/BSR品牌销量.xlsx')

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
if st.checkbox("查看原始品牌数据表"):
    st.markdown(
        "数据表中包含了各品牌的月销量、月销额以及市场份额占比等信息，方便进行品牌分析和比较。"
    )
    st.markdown(">注：此处排序是按照品牌产品数量从大到小排序，如果需要对利用其它指标排序，请在数据表中点击对应列标题进行排序即可。")
    st.dataframe(
        df_brand,
        use_container_width=True,
        column_config={
            "品牌产品listing月销量": st.column_config.NumberColumn(format="%,.0f"),
            "品牌产品listing月销额($)": st.column_config.NumberColumn(format="$%,.2f"),
            "市场份额-产品销量份额占比(%)": st.column_config.NumberColumn(format="%.2f%%"),
            "市场份额-产品销售额份额占比(%)": st.column_config.NumberColumn(format="%.2f%%"),
        }
    )
st.divider()
st.subheader("2.BSR品牌市场份额占比")
# 左右分栏放两张饼图
## 玫瑰图函数封装
def rose_option(data, title):
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
            "formatter": """
                <b>{b}</b><br/>
                市场份额：{c}%<br/>
                占整体：{d}%
            """
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

                # 改成玫瑰图
                "roseType": "radius",

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
                        "formatter": "{b}\n{c}%"
                    }
                }
            }
        ]
    }
col1, col2 = st.columns(2)

# 饼图1：销量市场份额
with col1:

    st.subheader("销量市场份额占比")

    data_qty = (
        df_brand.sort_values(
            "市场份额-产品销量份额占比(%)",
            ascending=False
        )[["品牌名称", "市场份额-产品销量份额占比(%)"]]
        .rename(columns={
            "品牌名称": "name",
            "市场份额-产品销量份额占比(%)": "value"
        })
        .to_dict("records")
    )

    st_echarts(
        options=rose_option(
            data_qty,
            "各品牌销量份额"
        ),
        height="550px"
    )

# 饼图2：销售额市场份额
with col2:

    st.subheader("销售额市场份额占比")

    data_amt = (
        df_brand.sort_values(
            "市场份额-产品销售额份额占比(%)",
            ascending=False
        )[["品牌名称", "市场份额-产品销售额份额占比(%)"]]
        .rename(columns={
            "品牌名称": "name",
            "市场份额-产品销售额份额占比(%)": "value"
        })
        .to_dict("records")
    )

    st_echarts(
        options=rose_option(
            data_amt,
            "各品牌销售额份额"
        ),
        height="550px"
    )

st.divider()
## 品牌月销售量分层
st.subheader("3.品牌规模分析")
col1, col2 = st.columns(2)
# ===========================
# 1. ECharts 横向条形图
with col1:
    st.markdown("### 各品牌月度销售额排名（$）")
    df_bar = df_brand.sort_values(
        "品牌产品listing月销额($)",
        ascending=True
    )
    option = {
        "animationDuration":1000,
        "tooltip":{
            "trigger":"axis",
            "axisPointer":{
                "type":"shadow"
            },
            "backgroundColor":"#fff",
            "borderColor":"#E5E7EB",
            "borderWidth":1,
            "textStyle":{
                "color":"#333"
            },
            "formatter":"{b}<br/>销售额：${c}"
        },

        "grid":{
            "left":"20%",
            "right":"8%",
            "top":"6%",
            "bottom":"5%"
        },

        "xAxis":{
            "type":"value",
            "splitLine":{
                "show":True,
                "lineStyle":{
                    "type":"dashed",
                    "color":"#EEF2F7"
                }
            }
        },

        "yAxis":{
            "type":"category",
            "data":df_bar["品牌名称"].tolist(),
            "axisTick":{"show":False}
        },

        "series":[
            {
                "type":"bar",

                "data":df_bar["品牌产品listing月销额($)"].tolist(),

                "barWidth":18,

                "label":{
                    "show":True,
                    "position":"right"
                },

                "itemStyle":{
                    "borderRadius":[0,8,8,0],

                    "color":{
                        "type":"linear",
                        "x":0,
                        "y":0,
                        "x2":1,
                        "y2":0,
                        "colorStops":[
                            {"offset":0,"color":"#4E79A7"},
                            {"offset":1,"color":"#A0CBE8"}
                        ]
                    }
                },

                "emphasis":{
                    "itemStyle":{
                        "shadowBlur":12,
                        "shadowColor":"rgba(0,0,0,.25)"
                    }
                }
            }
        ]
    }

    st_echarts(option,height="600px")

# ===========================
# 2. ECharts 散点图
# ===========================
# 2. ECharts 散点图
# ===========================
with col2:
    st.markdown("### 销量-销售额气泡图")
    top10 = (
        df_brand
        .nlargest(10,"品牌产品listing月销额($)")["品牌名称"]
        .tolist()
    )
    scatter_data=[]

    for _,row in df_brand.iterrows():
        share_val = row["市场份额-产品销量份额占比(%)"]
        bubble_size = int((share_val ** 0.5) * 20)
        scatter_data.append({
            "name": row["品牌名称"],
            "value": [
                row["品牌产品listing月销量"],
                row["品牌产品listing月销额($)"],
                share_val
            ],
            "symbolSize": bubble_size,
            "label":{
                "show": row["品牌名称"] in top10
            }
        })

    option={
        "animationDuration":1000,
        "tooltip":{
            "trigger":"item",
            "backgroundColor":"#fff",
            "borderColor":"#E5E7EB",
            "borderWidth":1,
            # "formatter": "{b}<br/>{c}"
        },
        "grid":{
            "left":"10%",
            "right":"6%",
            "bottom":"8%"
        },
        "xAxis":{
            "name":"月销量",
            "type":"value",
            "splitLine":{
                "lineStyle":{
                    "type":"dashed",
                    "color":"#EEF2F7"
                }
            }
        },
        "yAxis":{
            "name":"月销售额($)",
            "type":"value",
            "splitLine":{
                "lineStyle":{
                    "type":"dashed",
                    "color":"#EEF2F7"
                }
            }
        },
        "series":[{
            "type":"scatter",
            "data":scatter_data,
            "label":{
                "position":"top",
                "formatter": "{b}" # 固定展示品牌名称
            },
            "itemStyle":{
                "color":"#6CB2F3D1",
                "opacity":0.7,
                "borderColor":"#ffffff",
                "borderWidth":2
            },
            "emphasis":{
                "scale":1.3,
                "label":{
                    "show": True, 
                    "fontWeight":"bold",
                    "formatter": "{b}"
                },
                "itemStyle":{
                    "shadowBlur":20,
                    "shadowColor":"rgba(0,0,0,.25)"
                }
            }
        }]
    }

    st_echarts(options=option, height="600px")

#分割线
st.divider()


## 4. 品牌竞争分析
# 4. 分组柱状图：销量VS销售额份额对比 
st.subheader("4.品牌竞争分析") 
st.subheader("销量份额 vs 销售额份额对比") 
#数据宽表转换 
df_melt = pd.melt( 
    df_brand.sort_values(
        "市场份额-产品销售额份额占比(%)",
        ascending=False), 
        id_vars=["品牌名称"],
        value_vars=[ "市场份额-产品销售额份额占比(%)","市场份额-产品销量份额占比(%)" ], 
        var_name="份额类型", value_name="占比(%)" ) 
fig_group_bar = px.bar( 
    df_melt,
    x="品牌名称",
    y="占比(%)", 
    color="份额类型", 
    barmode="group", 
    color_discrete_sequence=["#225679", "#F7EF7F"] # 两种商务配色 
    ) 
fig_group_bar.update_traces( 
    hovertemplate="<b>%{x}</b><br>%{fullData.name}：%{y:.2f}%<extra></extra>",opacity=0.88 
    ) 
fig_group_bar.update_xaxes( 
    tickangle=-45,tickfont=dict(size=12),title_font=dict(size=18) 
    ) 
fig_group_bar.update_yaxes( 
    ticksuffix="%", title_font=dict(size=18), tickfont=dict(size=12), showgrid=True, gridcolor="rgba(180,180,180,0.35)" 
    )
fig_group_bar.update_layout( 
    height=600, bargap=0.25, bargroupgap=0.08, hoverlabel=dict(font_size=14),
    # 图例放顶部 
    legend=dict( orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, title=None, font=dict(size=13) ), 
    margin=dict(l=80, r=20, t=70, b=80), plot_bgcolor="white", paper_bgcolor="white" ) 

st.plotly_chart(fig_group_bar, use_container_width=True)


with st.sidebar:
    st.title("📑 页面导航")
    st.markdown("""
    ### 目录

    1. 原始数据
    2. 市场份额分析
    3. 品牌规模分析
    4. 品牌竞争分析
    """)