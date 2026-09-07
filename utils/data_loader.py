"""数据加载与清洗模块 —— 唯一 read_excel 入口。

原则：
- 所有 Excel 只读一次，用 @st.cache_data 缓存「清洗后的 DataFrame」。
- 页面只调用 load_all()，禁止在页面里直接 read_excel。
- 文件带日期前缀的用 glob 匹配，取最新（mtime）。

清洗规则（与设计文档 §3.3 对应）：
1. 日期 "2023-12()" -> 去 "()" -> datetime
2. 千分位字符串 "302,305" -> 302305
3. "--" / "该站点未找到相似类目" -> NaN
4. 市场趋势宽表转置为长表（月份 × 指标）
5. 销量/销额趋势宽表转置为长表
6. 词云表跳过前 2 行（标题/制表日期）
7. "产品" 汇总表 key-value -> dict
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 文件解析映射：key -> 相对 data 的 glob pattern
FILE_MAP = {
    "brand": "BSR品牌销量.xlsx",
    "asin": "BSR ASIN产品列表.xlsx",
    "keyword": "BSR相关关键词.xlsx",
    "new_release": "New Realese 产品列表.xlsx",
    "sales_trend": "*_售出件数趋势.xlsx",
    "market_trend": "*_市场趋势.xlsx",        # 不含 "(1)"
    "market_trend_2": "*_市场趋势 (1).xlsx",
    "global": "*_全球售卖对比分析.xlsx",
    "wordcloud": "*_Sorftime流量圈词云详情表-*.xlsx",
}

# 关键词表需要数值化的列
KEYWORD_NUM_COLS = [
    "cpc精准竞价($)", "cpc最低竞价($)", "cpc最高竞价($)",
    "周搜索排名", "月搜索量",
    "年搜索量-2026年", "年搜索量-2025年", "年搜索量-2024年",
    "近90日搜索转化率（%）", "近90日点击转化率（%）",
    "词搜索转换比(%)", "90天购买量", "竞品数量", "周搜索排名变化",
    "词搜索量复合增长率-近3个月(%)", "词搜索量复合增长率-近6个月(%)", "词搜索量复合增长率-近12个月(%)",
    "曝光点击垄断性(%)", "曝光转化垄断性(%)",
]

# 产品详情表需要数值化的列
DETAIL_NUM_COLS = [
    "实际价格($)", "预计Listing月销量", "Listing月销售额($)", "Listing年销量",
    "单个产品毛利($)", "单个产品毛利率(%)", "评分星级", "评价数量",
    "上架天数", "FBA费用($)", "大类排名", "平均大类排名", "排名变化", "排名变化率",
    "细分类目排名", "单个产品跟卖数量", "单个产品变体数量",
    "体积（in³）", "重量(g)", "体积重量", "目前销售价($)", "优惠($)",
    "月度同品牌销量占比(市场份额%)", "月度流量圈销量占比(%)",
]


def _resolve(pattern: str) -> Path:
    """按 pattern 匹配文件，取 mtime 最新。"""
    matches = sorted(DATA_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"未找到匹配 '{pattern}' 的数据文件（目录：{DATA_DIR}）")
    return matches[-1]


def _to_num(series: pd.Series) -> pd.Series:
    """去千分位逗号、把 '--' 视为缺失，转数值。"""
    s = series.astype(str).str.replace(",", "", regex=False)
    s = s.str.strip().replace({"--": None, "": None, "nan": None})
    return pd.to_numeric(s, errors="coerce")


def _melt_trend(path: Path, sheet_name: str, value_name: str) -> pd.DataFrame:
    """销量/销额趋势宽表 -> 长表（ASIN, ParentASIN, 月份, value）。"""
    raw = pd.read_excel(path, sheet_name=sheet_name)
    id_vars = [c for c in ("ASIN", "ParentASIN") if c in raw.columns]
    month_cols = [c for c in raw.columns if c not in id_vars]
    df = raw.melt(id_vars=id_vars, value_vars=month_cols, var_name="月份", value_name=value_name)
    df[value_name] = _to_num(df[value_name])
    return df


def _summary_to_dict(path: Path, sheet_name: str) -> dict:
    """'产品' 汇总表（key-value 两列重复布局）-> 扁平 dict。"""
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    d: dict = {}
    for i in range(len(raw)):
        row = raw.iloc[i]
        for j in range(0, len(row) - 1, 2):
            k = row.iloc[j]
            v = row.iloc[j + 1]
            if pd.isna(k):
                continue
            key = str(k).strip()
            if not key or "\n" in key or "导出时间" in key:
                continue
            d[key] = v
    return d


def _extract_export_time(path: Path, sheet_name: str) -> str | None:
    """从 '产品' 汇总表首行抽取「导出时间：YYYY-MM-DD HH:MM:SS」。"""
    try:
        raw = pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=1)
        txt = str(raw.iloc[0, 0])
        m = re.search(r"导出时间[:：]\s*([0-9\-: ]+)", txt)
        return m.group(1).strip() if m else None
    except Exception:
        return None


def _load_sales_trend() -> pd.DataFrame:
    df = pd.read_excel(_resolve(FILE_MAP["sales_trend"]), sheet_name="全部月份")
    df["日期"] = df["日期"].astype(str).str.replace("()", "", regex=False).str.strip()
    df["date"] = pd.to_datetime(df["日期"] + "-01", errors="coerce")
    df["售出件数"] = _to_num(df["售出件数"])
    df["净销售额($)"] = _to_num(df["净销售额($)"])
    return df


def _load_market_trend() -> tuple[pd.DataFrame, dict]:
    """合并两份市场趋势文件 -> (长表, 类目元信息)。"""
    meta: dict = {}
    frames: list[pd.DataFrame] = []
    for key in ("market_trend", "market_trend_2"):
        try:
            path = _resolve(FILE_MAP[key])
        except FileNotFoundError:
            continue
        raw = pd.read_excel(path, sheet_name="类目历史数据", header=None)
        meta = {
            "NODEID": raw.iloc[1, 0],
            "一级大类": raw.iloc[1, 1],
            "类目名称": raw.iloc[1, 2],
            "BSR链接": raw.iloc[1, 3],
            "Listing月销量": raw.iloc[1, 4],
        }
        # 找月份行：第 2 列是 6 位 YYYYMM
        month_row = None
        for i in range(len(raw)):
            if re.fullmatch(r"\d{6}", str(raw.iloc[i, 1]).strip().replace(".0", "")):
                month_row = i
                break
        if month_row is None:
            continue
        # 月份可能是 int/float/str 混合，统一归一化为 'YYYYMM'
        raw_months = [
            str(int(float(v))) if pd.notna(v) else ""
            for v in raw.iloc[month_row, 1:].tolist()
        ]
        # 剔除尾部空月份（月份行之后可能有多余空单元格）
        n = len(raw_months)
        while n > 0 and raw_months[n - 1] == "":
            n -= 1
        months = raw_months[:n]
        df = pd.DataFrame({"月份": months})
        for i in range(month_row + 1, len(raw)):
            name = raw.iloc[i, 0]
            if pd.isna(name) or not str(name).strip():
                continue
            df[str(name).strip()] = raw.iloc[i, 1:1 + n].tolist()
        frames.append(df)

    out = frames[0]
    for f in frames[1:]:
        out = out.merge(f, on="月份", how="outer")
    for c in out.columns:
        if c != "月份":
            out[c] = _to_num(out[c])
    return out, meta


def _load_global() -> pd.DataFrame:
    df = pd.read_excel(_resolve(FILE_MAP["global"]), sheet_name="Sheet1")
    df = df.rename(columns={
        "销售额Top100预估Listing月销量": "Top100月销量",
        "Top100预估月销额": "Top100月销额",
        "前3产品销量垄断系数(%)": "垄断系数",
        "3个月内新品占比(%)": "新品占比",
    })
    df["Top100月销量"] = _to_num(df["Top100月销量"])
    df["Top100月销额"] = _to_num(df["Top100月销额"])
    df["垄断系数"] = _to_num(df["垄断系数"])
    df["新品占比"] = _to_num(df["新品占比"])
    # 无数据站点（如澳洲/沙特）
    df["是否有数据"] = df["Top100月销量"].notna()
    return df


def _load_brand() -> pd.DataFrame:
    df = pd.read_excel(_resolve(FILE_MAP["brand"]), sheet_name="列表视图")
    for c in ("市场份额-产品销量份额占比(%)", "市场份额-产品销售额份额占比(%)", "品牌下新品份额(%)"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    return df


def _load_asin() -> dict:
    path = _resolve(FILE_MAP["asin"])
    detail = pd.read_excel(path, sheet_name="产品详情")
    for c in DETAIL_NUM_COLS:
        if c in detail.columns:
            detail[c] = _to_num(detail[c])
    if "上架时间" in detail.columns:
        detail["上架时间"] = pd.to_datetime(detail["上架时间"], errors="coerce")
    return {
        "detail": detail,
        "summary": _summary_to_dict(path, "产品"),
        "export_time": _extract_export_time(path, "产品"),
        "sales_trend": _melt_trend(path, "销量趋势", "销量"),
        "revenue_trend": _melt_trend(path, "销额趋势", "销额"),
    }


def _load_keyword() -> pd.DataFrame:
    df = pd.read_excel(_resolve(FILE_MAP["keyword"]), sheet_name="产品")
    for c in KEYWORD_NUM_COLS:
        if c in df.columns:
            df[c] = _to_num(df[c])
    return df


def _load_wordcloud() -> pd.DataFrame:
    df = pd.read_excel(_resolve(FILE_MAP["wordcloud"]), sheet_name="Sorftime流量圈词云", skiprows=2)
    for c in ("重复次数", "重复次数占比（%）", "关键词产品月销量", "关键词产品月销量占比（%）"):
        if c in df.columns:
            df[c] = _to_num(df[c])
    return df


def _load_new_release() -> dict:
    path = _resolve(FILE_MAP["new_release"])
    detail = pd.read_excel(path, sheet_name="产品详情")
    for c in DETAIL_NUM_COLS:
        if c in detail.columns:
            detail[c] = _to_num(detail[c])
    if "上架时间" in detail.columns:
        detail["上架时间"] = pd.to_datetime(detail["上架时间"], errors="coerce")

    variants = pd.read_excel(path, sheet_name="子体")
    for c in ("子体销量", "价格($)"):
        if c in variants.columns:
            variants[c] = _to_num(variants[c])

    return {
        "detail": detail,
        "summary": _summary_to_dict(path, "产品"),
        "export_time": _extract_export_time(path, "产品"),
        "variants": variants,
        "sales_trend": _melt_trend(path, "销量趋势", "销量"),
        "revenue_trend": _melt_trend(path, "销额趋势", "销额"),
    }


@st.cache_data(show_spinner="加载数据...")
def load_all() -> dict:
    """读一次 + 清洗一次，返回所有清洗后数据（供所有页面共享）。"""
    market_trend, market_meta = _load_market_trend()
    asin = _load_asin()
    new_release = _load_new_release()
    sales_trend = _load_sales_trend()
    return {
        "sales_trend": sales_trend,
        "market_trend": market_trend,
        "market_meta": market_meta,
        "global": _load_global(),
        "brand": _load_brand(),
        "asin": asin,
        "keyword": _load_keyword(),
        "wordcloud": _load_wordcloud(),
        "new_release": new_release,
        "data_time": {
            "asin_export": asin.get("export_time"),
            "new_release_export": new_release.get("export_time"),
            "sales_latest": str(sales_trend["date"].max().date()) if len(sales_trend) else None,
        },
    }
