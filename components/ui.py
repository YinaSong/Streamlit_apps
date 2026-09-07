"""可复用 UI 组件：页面配置、标题、KPI 卡片、数据来源、使用说明、分节标题。"""
from __future__ import annotations

import streamlit as st

from utils import theme


def page_title(title: str, subtitle: str | None = None):
    """每页顶部入口：set_page_config + 标题 + 副标题。

    Streamlit multipage 下各页面是独立脚本，set_page_config 不跨页继承，
    因此每页都必须调用；且必须作为页内第一个 st 命令。
    """
    st.set_page_config(page_title=title, page_icon="📊", layout="wide")
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def data_source(text: str):
    """数据时间来源说明（标题下方灰色小字）。"""
    st.markdown(
        f'<div style="color:{theme.MUTED};font-size:13px;margin:2px 0 14px 0;">{text}</div>',
        unsafe_allow_html=True,
    )


def usage_note():
    """统一的使用说明卡片（各页面复用，消除重复代码）。"""
    st.markdown(
        f"""
        <div style="
            background-color:{theme.BACKGROUND};
            border-left:4px solid {theme.PRIMARY};
            padding:12px 16px;
            border-radius:8px;
            color:{theme.MUTED};
            font-size:14px;
            line-height:1.8;
        ">
        💡 <b>使用说明</b><br>
        • 所有图表可悬停查看详细数据，可缩放、点击图例隐藏系列。<br>
        • 数据表点击列标题可排序，右上角可下载 CSV。
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str):
    st.divider()
    st.subheader(title)


def kpi_cards(items):
    """KPI 卡片行。

    items: list[dict]，字段：
      - label（必填）
      - value（必填，字符串）
      - sub（可选，辅助说明字符串，如「上月 53.9万」或「销售额份额 29.45%」）
      - delta（可选，环比/同比数值，单位 %，自动带 ▲▼ 与涨跌色）
    """
    cols = st.columns(len(items))
    for col, it in zip(cols, items):
        with col:
            _kpi_card_html(it)


def _kpi_card_html(it: dict):
    label = it["label"]
    value = it.get("value", "—")
    sub = it.get("sub")
    delta = it.get("delta")

    parts = []
    if sub is not None:
        parts.append(f'<span style="color:{theme.MUTED};">{sub}</span>')
    if delta is not None:
        try:
            d = float(delta)
            color = theme.UP if d >= 0 else theme.DOWN
            arrow = "▲" if d >= 0 else "▼"
            parts.append(
                f'<span style="color:{color};font-weight:600;">{arrow} {abs(d):.1f}%</span>'
            )
        except (TypeError, ValueError):
            pass
    sub = "　·　".join(parts)

    st.markdown(
        f"""
        <div style="
            background:{theme.CARD};
            border:1px solid {theme.GRID};
            border-radius:12px;
            padding:14px 18px;
            min-height:96px;
        ">
            <div style="color:{theme.MUTED};font-size:13px;margin-bottom:6px;">{label}</div>
            <div style="font-size:26px;font-weight:700;color:{theme.TEXT};line-height:1.2;">{value}</div>
            <div style="font-size:12px;margin-top:6px;line-height:1.5;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_toc(items: list[str]):
    """侧边栏目录。"""
    with st.sidebar:
        st.markdown("### 📑 目录")
        for i, it in enumerate(items, 1):
            st.markdown(f"{i}. {it}")
