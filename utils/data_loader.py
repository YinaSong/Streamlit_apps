"""数据加载与清洗模块 —— 唯一 read_excel 入口（多站点）。

原则：
- 所有 Excel 只读一次，用 @st.cache_data 缓存「清洗后的 DataFrame」。
- 页面只调用 load_all(site)，禁止在页面里直接 read_excel。
- data/ 按站点分目录，站点内文件名统一为 {类型}.xlsx。
- 站点间数据表与指标存在真实差异（见设计文档 §2.9），缺表数据域返回 None，页面判空降级。

清洗规则（对应设计文档 §3.3）：
1. 日期 "2023-12()" -> 去 "()" -> datetime；市场趋势 "202608" 保持 "YYYYMM"
2. 千分位字符串 "302,305" -> 302305
3. "--" / "该站点未找到相似类目" -> NaN
4. 市场趋势 3 文件宽表转置为长表（月份 × 指标），按指标名合并
5. 销量/销额趋势宽表转置为长表
6. 词云表跳过前 2 行（标题/制表日期）
7. 产品详情/新品表跳过首行 banner（第 2 行才是表头）
8. 关键词表跳过首行注释，2 行表头展平为旧版单层列名
9. "产品" 汇总表 key-value -> dict
10. 币种列名归一化（CDN$/€/£ -> $），站点币种由 SITE_CURRENCY 提供
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SITES = ["US", "CA", "DE", "FR"]
SITE_CURRENCY = {"US": "$", "CA": "CA$", "DE": "€", "FR": "€"}
SITE_CURRENCY_FMT = {"US": "$%,.2f", "CA": "CA$%,.2f", "DE": "€%,.2f", "FR": "€%,.2f"}

# 站点 × 数据域 文件映射（缺表数据域跳过，返回 None）
TABLE_FILES = {
    "asin":        "产品列表_BSR.xlsx",
    "new_release": "产品列表_NewRelease.xlsx",
    "brand":       "品牌销量.xlsx",
    "keyword":     "相关关键词.xlsx",
    "wordcloud":   "词云详情表.xlsx",
    "sales_trend": "售出件数趋势.xlsx",
    "market_scale": "市场趋势_规模竞争.xlsx",
    "market_price": "市场趋势_价格评价.xlsx",
    "market_concentration": "市场趋势_集中度.xlsx",
}

GLOBAL_FILE = "全球售卖对比.xlsx"

# 关键词表需要数值化的列（展平后的规范名）
KEYWORD_NUM_COLS = [
    "cpc精准竞价($)", "cpc最低竞价($)", "cpc最高竞价($)",
    "周搜索排名", "月搜索量",
    "年搜索量-2026年", "年搜索量-2025年", "年搜索量-2024年",
    "近90日搜索转化率（%）", "近90日点击转化率（%）",
    "90天购买量", "竞品数量", "周搜索排名变化",
    "词搜索量复合增长率-近3个月(%)", "词搜索量复合增长率-近6个月(%)", "词搜索量复合增长率-近12个月(%)",
    "曝光点击垄断性(%)", "曝光转化垄断性(%)",
]

# 产品详情/新品表需要数值化的列（新导出列名已归一化为规范名）
DETAIL_NUM_COLS = [
    "实际价格($)", "预计Listing月销量", "Listing月销售额($)", "Listing年销量",
    "单个产品毛利($)", "单个产品毛利率(%)", "评分星级", "评价数量",
    "上架天数", "FBA费用($)", "大类排名", "平均大类排名", "排名变化", "排名变化率",
    "细分类目排名", "单个产品跟卖数量", "单个产品变体数量",
    "体积(in³)", "重量(g)", "体积重量", "目前销售价($)", "优惠($)",
    "月度同品牌销量占比(市场份额%)", "月度流量圈销量占比(%)",
]

# 产品详情新列名 -> 旧版规范名
_DETAIL_RENAME = {
    "预计Listing月销额($)": "Listing月销售额($)",
    "毛利($)": "单个产品毛利($)",
    "毛利率(%)": "单个产品毛利率(%)",
    "上架时长(天)": "上架天数",
    "排名变化(近7日)": "排名变化",
    "排名变化率(近1个月)": "排名变化率",
    "跟卖数量": "单个产品跟卖数量",
    "变体数量": "单个产品变体数量",
}

_CUR_RE = re.compile(r"\((?:CDN\$|€|£|\$)\)")


def _norm_cur(col: str) -> str:
    """币种归一化：实际价格(CDN$)/(€) -> 实际价格($)。"""
    return _CUR_RE.sub("($)", col)


def _site_file(site: str, key: str) -> Path | None:
    """{site}/{file}，兼容 US 的 产品列表_BSR.xlsx 与 CA/DE/FR 的 产品列表.xlsx。"""
    fname = TABLE_FILES[key]
    if key == "asin" and site != "US":
        fname = "产品列表.xlsx"
    p = DATA_DIR / site / fname
    return p if p.exists() else None


def _to_num(series: pd.Series) -> pd.Series:
    """去千分位逗号、把 '--' 视为缺失，转数值。"""
    s = series.astype(str).str.replace(",", "", regex=False)
    s = s.str.strip().replace({"--": None, "": None, "nan": None})
    return pd.to_numeric(s, errors="coerce")


def _norm_detail_columns(df: pd.DataFrame) -> pd.DataFrame:
    """产品详情列名：币种归一化 + 新列名映射回旧版规范名。"""
    df = df.rename(columns=lambda c: _norm_cur(str(c).strip()))
    return df.rename(columns=_DETAIL_RENAME)


def _clean_detail_nums(df: pd.DataFrame) -> pd.DataFrame:
    for c in DETAIL_NUM_COLS:
        if c in df.columns:
            df[c] = _to_num(df[c])
    if "上架时间" in df.columns:
        df["上架时间"] = pd.to_datetime(df["上架时间"], errors="coerce")
    return df


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


def _flatten_keyword_header(df: pd.DataFrame) -> pd.DataFrame:
    """关键词 2 行表头 -> 旧版单层规范名。

    新导出的「年搜索量 ×3」「词搜索量复合增长率 ×3」「搜索结果首页/前3页表现」
    「曝光点击/转化 ×2」等都是 组名 + 子标签 的两级表头，这里按组名拼接回单层列名。
    """
    new_cols = []
    for g, s in df.columns:
        g = _norm_cur(str(g).strip()) if pd.notna(g) else ""
        s = _norm_cur(str(s).strip()) if pd.notna(s) else ""
        if g == "年搜索量":
            name = f"年搜索量-{s}"
        elif g == "词搜索量复合增长率":
            name = f"词搜索量复合增长率-{s}"
        elif g == "曝光点击/转化":
            name = "曝光点击垄断性(%)" if "点击" in s else "曝光转化垄断性(%)"
        elif g == "点击转化占比TOP3 ASIN":
            name = "点击占比TOP3 ASIN" if s == "点击占比" else "转化占比TOP3 ASIN"
        elif g == "搜索结果首页表现":
            name = f"搜索结果首页-{s}"
        elif g == "搜索结果前3页表现":
            name = f"搜索结果前3页-{s}"
        elif g in ("近90日搜索转化率(%)", "近90日点击转化率(%)"):
            name = g.replace("(%)", "（%）")
        else:
            name = g
        new_cols.append(name)
    df.columns = new_cols
    return df


def _load_sales_trend(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="全部月份")
    df = df.rename(columns=lambda c: _norm_cur(str(c).strip()))
    df["日期"] = df["日期"].astype(str).str.replace("()", "", regex=False).str.strip()
    df["date"] = pd.to_datetime(df["日期"] + "-01", errors="coerce")
    df["售出件数"] = _to_num(df["售出件数"])
    df["净销售额($)"] = _to_num(df["净销售额($)"])
    return df


def _load_market_trend(site: str) -> tuple[pd.DataFrame, dict]:
    """合并站点 3 份市场趋势文件 -> (长表, 类目元信息)。按指标名合并，指标顺序无关。"""
    meta: dict = {}
    frames: list[pd.DataFrame] = []
    for key in ("market_scale", "market_price", "market_concentration"):
        path = _site_file(site, key)
        if path is None:
            continue
        raw = pd.read_excel(path, sheet_name="类目历史数据", header=None)
        if not meta:
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
        raw_months = [
            str(int(float(v))) if pd.notna(v) else ""
            for v in raw.iloc[month_row, 1:].tolist()
        ]
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

    out = frames[0] if frames else pd.DataFrame(columns=["月份"])
    for f in frames[1:]:
        out = out.merge(f, on="月份", how="outer")
    for c in out.columns:
        if c != "月份":
            out[c] = _to_num(out[c])
    return out, meta


def _load_global() -> pd.DataFrame:
    path = DATA_DIR / GLOBAL_FILE
    df = pd.read_excel(path, sheet_name="Sheet1")
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
    df["是否有数据"] = df["Top100月销量"].notna()
    return df


def _load_brand(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="列表视图")
    for c in ("市场份额-产品销量份额占比(%)", "市场份额-产品销售额份额占比(%)", "品牌下新品份额(%)"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").round(2)
    return df


def _load_asin(path: Path) -> dict:
    detail = pd.read_excel(path, sheet_name="产品详情", header=1)
    detail = _norm_detail_columns(detail)
    detail = _clean_detail_nums(detail)
    return {
        "detail": detail,
        "summary": _summary_to_dict(path, "产品"),
        "export_time": _extract_export_time(path, "产品"),
        "sales_trend": _melt_trend(path, "销量趋势", "销量"),
        "revenue_trend": _melt_trend(path, "销额趋势", "销额"),
    }


def _load_keyword(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="产品", skiprows=1, header=[0, 1])
    df = _flatten_keyword_header(df)
    for c in KEYWORD_NUM_COLS:
        if c in df.columns:
            df[c] = _to_num(df[c])
    return df


def _load_wordcloud(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Sorftime流量圈词云", skiprows=2)
    for c in ("重复次数", "重复次数占比（%）", "关键词产品月销量", "关键词产品月销量占比（%）"):
        if c in df.columns:
            df[c] = _to_num(df[c])
    return df


def _load_new_release(path: Path) -> dict:
    detail = pd.read_excel(path, sheet_name="产品详情", header=1)
    detail = _norm_detail_columns(detail)
    detail = _clean_detail_nums(detail)

    xl = pd.ExcelFile(path)
    if "子体" in xl.sheet_names:
        variants = pd.read_excel(path, sheet_name="子体")
        variants = variants.rename(columns=lambda c: _norm_cur(str(c).strip()))
        for c in ("子体销量", "价格($)"):
            if c in variants.columns:
                variants[c] = _to_num(variants[c])
    else:
        variants = pd.DataFrame()  # 新导出已无「子体」表

    return {
        "detail": detail,
        "summary": _summary_to_dict(path, "产品"),
        "export_time": _extract_export_time(path, "产品"),
        "variants": variants,
        "sales_trend": _melt_trend(path, "销量趋势", "销量"),
        "revenue_trend": _melt_trend(path, "销额趋势", "销额"),
    }


@st.cache_data(show_spinner="加载数据...")
def load_all(site: str) -> dict:
    """读一次 → 清洗一次 → 返回指定站点所有清洗后 DataFrame 字典 + data_time。

    缺表数据域返回 None，页面取用前判空。site 来自 ui.site_selector()。
    """
    site = site.upper()
    market_trend, market_meta = _load_market_trend(site)

    asin_path = _site_file(site, "asin")
    asin = _load_asin(asin_path) if asin_path else None

    def _opt(key, loader):
        p = _site_file(site, key)
        return loader(p) if p else None

    sales_trend = _opt("sales_trend", _load_sales_trend)
    new_release = _opt("new_release", _load_new_release)

    return {
        "site": site,
        "currency": SITE_CURRENCY.get(site, "$"),
        "currency_fmt": SITE_CURRENCY_FMT.get(site, "$%,.2f"),
        "market_trend": market_trend,
        "market_meta": market_meta,
        "global": _load_global(),
        "asin": asin,
        "brand": _opt("brand", _load_brand),
        "keyword": _opt("keyword", _load_keyword),
        "wordcloud": _opt("wordcloud", _load_wordcloud),
        "sales_trend": sales_trend,
        "new_release": new_release,
        "data_time": {
            "asin_export": asin.get("export_time") if asin else None,
            "new_release_export": new_release.get("export_time") if new_release else None,
            "sales_latest": (
                str(sales_trend["date"].max().date())
                if (sales_trend is not None and len(sales_trend))
                else None
            ),
        },
    }
