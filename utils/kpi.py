"""KPI 指标计算（纯计算，无 UI 依赖）。

返回原始数值，格式化交给 formatters / ui 层。
"""
from __future__ import annotations

import pandas as pd


def _clean(v):
    """numpy 标量 -> python 标量；非数值返回 None。"""
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except (TypeError, ValueError):
        return None


def brand_kpis(df: pd.DataFrame) -> dict:
    """品牌页 KPI：品牌数、CR10、占比第一品牌、AOSU 排名与份额。"""
    sales_share = df["市场份额-产品销量份额占比(%)"]
    revenue_share = df["市场份额-产品销售额份额占比(%)"]

    # 按销售额份额排名
    ranked = df.sort_values(
        "市场份额-产品销售额份额占比(%)", ascending=False
    ).reset_index(drop=True)
    top = ranked.iloc[0]

    # AOSU case-insensitive 匹配（数据中为小写 "aosu"）
    norm = ranked["品牌名称"].astype(str).str.strip().str.lower()
    aosu_rank = None
    aosu = None
    for i, n in enumerate(norm):
        if n == "aosu":
            aosu_rank = i + 1
            aosu = ranked.iloc[i]
            break

    out = {
        "品牌数量": len(df),
        "CR10销量份额%": round(float(sales_share.nlargest(10).sum()), 2),
        "Top品牌": str(top["品牌名称"]),
        "Top品牌销售额份额%": round(float(revenue_share.max()), 2),
        "Top品牌销售额": _clean(top["品牌产品listing月销额($)"]),
    }
    if aosu is not None:
        out.update({
            "AOSU排名": aosu_rank,
            "AOSU销售额份额%": round(float(aosu["市场份额-产品销售额份额占比(%)"]), 2),
            "AOSU销售额": _clean(aosu["品牌产品listing月销额($)"]),
            "AOSU销量份额%": round(float(aosu["市场份额-产品销量份额占比(%)"]), 2),
        })
    return out


def keyword_kpis(df: pd.DataFrame) -> dict:
    """关键词页 KPI：数量、平均搜索量、平均竞争度。"""
    return {
        "关键词数量": len(df),
        "平均月搜索量": _clean(df["月搜索量"].mean()),
        "平均竞品数量": _clean(df["竞品数量"].mean()),
        "平均CPC($)": _clean(df["cpc精准竞价($)"].mean()),
    }


def summary_kpis(summary: dict) -> dict:
    """把 '产品' 汇总 dict 转成干净的 KPI dict。"""
    keys = [
        "产品数", "月总销量", "月总销售额($)", "月均销售额($)",
        "品牌数量", "卖家数量", "平均价格($)", "平均星级", "平均评价数量",
        "亚马逊自营占比(%)", "新品占比(%)(默认三个月)", "A+占比(%)",
        "类目下产品数", "可售产品数",
    ]
    return {k: _clean(summary.get(k)) for k in keys}


def sales_trend_kpis(df: pd.DataFrame, value_col: str = "售出件数",
                     rev_col: str = "净销售额($)", date_col: str = "date") -> dict:
    """销量趋势的当月/上月（按时间升序取最后两月）。"""
    d = df.sort_values(date_col).reset_index(drop=True)
    if len(d) < 2:
        return {}
    cur, prev = d.iloc[-1], d.iloc[-2]
    return {
        "当月销量": _clean(cur[value_col]),
        "上月销量": _clean(prev[value_col]),
        "当月销售额": _clean(cur[rev_col]),
        "上月销售额": _clean(prev[rev_col]),
        "当月": str(cur[date_col])[:7],
        "上月": str(prev[date_col])[:7],
    }


def mom_yoy_table(df: pd.DataFrame, value_col: str, date_col: str = "date") -> pd.DataFrame:
    """追加 环比% / 同比% 两列（同比 = 与 12 个月前比较）。"""
    d = df[[date_col, value_col]].copy()
    d = d.sort_values(date_col).reset_index(drop=True)
    d["环比%"] = (d[value_col].pct_change() * 100).round(1)
    d["同比%"] = (d[value_col] / d[value_col].shift(12) - 1) * 100
    d["同比%"] = d["同比%"].round(1)
    return d


def market_trend_kpis(df: pd.DataFrame, month_col: str = "月份",
                      value_col: str = "类目销量") -> dict:
    """市场趋势概览 KPI：最新月指标 + 同比 + 环比。"""
    d = mom_yoy_table(df, value_col, month_col).dropna(subset=[value_col])
    if len(d) == 0:
        return {}
    last = d.iloc[-1]
    return {
        "最新月": str(last[month_col]),
        "最新值": _clean(last[value_col]),
        "环比%": _clean(last["环比%"]),
        "同比%": _clean(last["同比%"]),
    }


def seasonality_matrix(df: pd.DataFrame, month_col: str = "月份",
                       value_col: str = "类目销量") -> tuple[list, list, list]:
    """年份 × 月份 聚合矩阵（用于热力图）。

    Returns (years, months, matrix)：matrix 为 12 行 × len(years) 列，缺失为 None。
    """
    d = df[[month_col, value_col]].copy()
    d = d.dropna(subset=[value_col])
    d["年"] = d[month_col].astype(str).str[:4]
    d["月"] = d[month_col].astype(str).str[4:6].astype(int)
    years = sorted(d["年"].unique())
    months = list(range(1, 13))
    matrix = []
    for m in months:
        row = []
        for y in years:
            v = d[(d["月"] == m) & (d["年"] == y)][value_col]
            row.append(float(v.iloc[0]) if len(v) else None)
        matrix.append(row)
    return years, months, matrix
