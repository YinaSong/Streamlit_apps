"""KPI 指标计算（纯计算，无 UI 依赖）。

返回原始数值，格式化交给 formatters / ui 层。
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

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


# ---------------------------------------------------------------------------
# 分析聚合：品牌/店铺价格定位、集中度、价格/评分区间、标题与属性词频
# （供各页新增图表使用，纯计算，无 UI 依赖）
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "of", "to", "in", "on", "by",
    "is", "are", "was", "were", "be", "been", "being", "as", "at", "from", "into",
    "than", "that", "this", "these", "those", "it", "its", "your", "you", "our",
    "their", "will", "can", "may", "also", "up", "out", "no", "not", "per", "via",
    "use", "used", "using", "etc", "com", "amazon", "https", "http",
}


def _words(text) -> list[str]:
    """英文文本 -> 小写分词（去除停用词与过短词）。"""
    if pd.isna(text):
        return []
    t = str(text).lower()
    return [w for w in re.findall(r"[a-z0-9][a-z0-9\-.']*", t)
            if w not in _STOPWORDS and len(w) > 1]


def _word_metrics(df, text_cols, sales_col, bigram=False, top=50) -> pd.DataFrame:
    """从若干文本列提取 词频 / 覆盖产品数 / 词月销量（英文分词）。"""
    freq: Counter = Counter()
    products: Counter = Counter()
    sales: defaultdict = defaultdict(float)
    has_sales = sales_col in df.columns
    for _, row in df.iterrows():
        parts = [str(row[c]) for c in text_cols if c in df.columns and pd.notna(row[c])]
        tokens = _words(" ".join(parts))
        if bigram:
            tokens = [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]
        seen: set = set()
        for t in tokens:
            freq[t] += 1
            if t not in seen:
                seen.add(t)
                products[t] += 1
                if has_sales:
                    v = row[sales_col]
                    if pd.notna(v):
                        sales[t] += float(v)
    items = sorted(freq.items(), key=lambda kv: -kv[1])[:top]
    return pd.DataFrame({
        "词": [t for t, _ in items],
        "词频": [freq[t] for t, _ in items],
        "覆盖产品数": [products[t] for t, _ in items],
        "词月销量": [sales[t] for t, _ in items],
    })


def title_words(df, title_col="产品名称", sales_col="预计Listing月销量", top=50):
    """标题分词词频（词云）。"""
    return _word_metrics(df, [title_col], sales_col, bigram=False, top=top)


def title_bigrams(df, title_col="产品名称", sales_col="预计Listing月销量", top=50):
    """标题二元词组词频。"""
    return _word_metrics(df, [title_col], sales_col, bigram=True, top=top)


def attr_words(df, text_cols, sales_col="预计Listing月销量", top=30):
    """属性词挖掘：从五点描述/属性列提取词频与销量。"""
    return _word_metrics(df, text_cols, sales_col, bigram=False, top=top)


def _asp_stats(df, name_col, price_col="实际价格($)", sales_col="预计Listing月销量"):
    """按某维度（品牌/店铺）聚合：ASIN 数、平均售价、月销量。"""
    g = df.dropna(subset=[name_col, price_col])
    out = g.groupby(name_col).agg(
        平均售价=(price_col, "mean"),
        ASIN数=(price_col, "count"),
        月销量=(sales_col, "sum"),
    ).reset_index()
    out["平均售价"] = out["平均售价"].round(2)
    out["月销量"] = out["月销量"].fillna(0).astype(float)
    return out


def brand_asp(df, name_col="品牌", price_col="实际价格($)", sales_col="预计Listing月销量"):
    """品牌 ASP（平均售价）与规模排行。"""
    out = _asp_stats(df, name_col, price_col, sales_col)
    return out.sort_values("平均售价", ascending=False).reset_index(drop=True)


def seller_stats(df, name_col="店铺", price_col="实际价格($)", sales_col="预计Listing月销量"):
    """店铺（卖家）聚合：ASIN 数、平均售价、月销量与占比。"""
    out = _asp_stats(df, name_col, price_col, sales_col)
    out = out.sort_values("月销量", ascending=False).reset_index(drop=True)
    total = out["月销量"].sum()
    out["销量占比%"] = (out["月销量"] / total * 100).round(1) if total else 0.0
    return out


def listing_concentration(df, value_col="预计Listing月销量"):
    """Top N listing 累计销量份额（快照）。"""
    s = df[value_col].dropna().sort_values(ascending=False)
    total = s.sum()
    if not total:
        return pd.DataFrame(columns=["TopN", "累计份额%"])
    out = []
    for n in (1, 3, 5, 10, 20):
        n = min(n, len(s))
        share = s.head(n).sum() / total * 100
        out.append({"TopN": f"Top {n}", "累计份额%": round(float(share), 1)})
    return pd.DataFrame(out)


def price_bands(df, price_col="实际价格($)", sales_col="预计Listing月销量"):
    """价格区间分布（ASIN 数 + 月销量）。"""
    s = df[price_col].dropna()
    bins = [0, 25, 50, 100, 150, 250, float("inf")]
    labels = ["$0–25", "$25–50", "$50–100", "$100–150", "$150–250", "$250+"]
    band = pd.cut(s, bins=bins, labels=labels, right=False)
    d = pd.DataFrame({"价格区间": band, "销量": df.loc[s.index, sales_col]})
    out = d.groupby("价格区间", observed=True).agg(
        ASIN数=("销量", "size"),
        月销量=("销量", "sum"),
    ).reset_index()
    out["月销量"] = out["月销量"].fillna(0)
    return out[out["ASIN数"] > 0].reset_index(drop=True)


def rating_bands(df, rating_col="评分星级"):
    """评分区间分布（ASIN 数）。"""
    s = df[rating_col].dropna()
    bins = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5]
    labels = ["3.0–3.5", "3.5–4.0", "4.0–4.5", "4.5–5.0", "5.0"]
    band = pd.cut(s, bins=bins, labels=labels, right=False)
    out = band.value_counts(sort=False).rename_axis("评分区间").reset_index(name="ASIN数")
    return out[out["ASIN数"] > 0].reset_index(drop=True)


def categorical_share(df, col):
    """分类列 -> 各类别 ASIN 数（供环形图）。"""
    vc = df[col].astype(str).str.strip().value_counts().reset_index()
    vc.columns = ["类别", "ASIN数"]
    return vc
