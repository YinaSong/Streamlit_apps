"""数字/百分比/货币统一格式化。

页面禁止裸写 f"{x:,}" 之类的魔法格式，统一从这里取。
"""
from __future__ import annotations

import math

import pandas as pd

# 统一格式字符串（供 st.column_config.NumberColumn 等直接使用）
NUM_FMT = "%,.0f"        # 千分位整数
NUM_FMT_2 = "%,.2f"      # 千分位两位小数
USD_FMT = "$%,.2f"       # 美元
PCT_FMT = "%.2f%%"       # 百分比（注意 %% 转义）

# 缺失值统一占位符
NA = "—"


def _isna(x) -> bool:
    try:
        return pd.isna(x)
    except (TypeError, ValueError):
        return x is None


def thousands(x) -> str:
    """千分位整数，缺失返回 —。"""
    if _isna(x):
        return NA
    return f"{float(x):,.0f}"


def thousands2(x) -> str:
    """千分位两位小数。"""
    if _isna(x):
        return NA
    return f"{float(x):,.2f}"


def usd(x) -> str:
    """美元金额。"""
    if _isna(x):
        return NA
    return f"${float(x):,.2f}"


def percent(x, digits: int = 2) -> str:
    """百分比。"""
    if _isna(x):
        return NA
    return f"{float(x):.{digits}f}%"


def compact(x) -> str:
    """大数缩写：1.2万 / 3.4亿 / 1234。"""
    if _isna(x):
        return NA
    x = float(x)
    if abs(x) >= 1e8:
        return f"{x / 1e8:.2f}亿"
    if abs(x) >= 1e4:
        return f"{x / 1e4:.1f}万"
    return f"{x:,.0f}"


def compact_usd(x) -> str:
    """金额缩写：$12.3万 / $3.4亿。"""
    if _isna(x):
        return NA
    x = float(x)
    if abs(x) >= 1e8:
        return f"${x / 1e8:.2f}亿"
    if abs(x) >= 1e4:
        return f"${x / 1e4:.1f}万"
    return f"${x:,.0f}"


def pct_change(cur, prev) -> str:
    """环比/同比变化率，如 '+12.3%'；缺失返回 —。"""
    if _isna(cur) or _isna(prev):
        return NA
    prev = float(prev)
    if prev == 0:
        return NA
    return f"{((float(cur) - prev) / abs(prev) * 100):+.1f}%"


def fmt_year_month(ym) -> str:
    """'202608' -> '2026-08'。"""
    s = str(ym).strip()
    if len(s) == 6 and s.isdigit():
        return f"{s[:4]}-{s[4:]}"
    return s
