"""主题与全局常量：配色、图表高度、字体。

所有图表/卡片从这里取色与高度，保证全局视觉统一、简约。
"""
from __future__ import annotations

# 主色（统一简约）
PRIMARY = "#4E79A7"

# 辅助色板（少量，用于多系列）
SECONDARY = [
    "#59A14F", "#F28E2B", "#E15759", "#76B7B2", "#A0CBE8", "#B6992D",
]

# 背景 / 文字 / 边框
BACKGROUND = "#FAFAFA"
CARD = "#FFFFFF"
TEXT = "#2F3B52"
MUTED = "#8A94A6"
GRID = "#EEF2F7"

# 涨跌色（环比 / 同比）
UP = "#59A14F"
DOWN = "#E15759"

# ECharts 系列色板
ECHARTS_COLORS = [PRIMARY] + SECONDARY

# 统一图表高度（px）
CHART_HEIGHT = 420
CHART_HEIGHT_LARGE = 480

# 统一字体
FONT_FAMILY = "-apple-system, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"
