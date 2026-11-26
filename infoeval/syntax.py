# -*- coding: utf-8 -*-
"""共享句法基线：句长 / T-unit

这两个指标措辞层（A3）和信息组织层（B）都用，所以放在公共位置。

句长
    均值 / P90 / 最长，单位=汉字个数
    **方向不定，只做基线**：长句不等于难读，短句也不等于清楚。

T-unit
    一个主句 + 它带的从句 = 一个 T-unit。
    中文没有现成的 T-unit 库（LTP / HanLP / stanza 只给依存树），
    本实现用连词规则近似：并列连词切开、从属连词不切。
    这是**近似**，不是标准 T-unit；报告里必须标注。

    每 T-unit 从句数   = 从属复杂度
    每句 T-unit 数     = 并列密度
    句长 ≈ T-unit 均长 × 每句 T-unit 数（三者只能留两个，否则重复计）
"""
from __future__ import annotations

import re

from .units import cjk_len, clean_units, stats

# 并列连词（切开 → 新 T-unit）
# 注：表里含「因此/所以/于是/然后」等连接副词，它们严格说是从属/承接关系，
#     不产生新的主句。这里按并列处理是对齐既有口径的近似，报告须标注。
COORD = ["并且", "而且", "同时", "另外", "此外", "但是", "然而", "不过",
         "因此", "所以", "于是", "然后", "接着", "随后", "以及", "或者"]
SUBORD = ["因为", "由于", "如果", "假如", "若", "虽然", "尽管", "即使", "只要",
          "除非", "以便", "从而", "因此", "所以", "以致"]

COORD_RX = re.compile("(" + "|".join(sorted(COORD, key=len, reverse=True)) + ")")
FRAG_SPLIT = re.compile(r"[，、,：:]")      # 片段切分（不含分号/句号）
FRAG_MIN_CJK = 2


def has_predicate(frag: str) -> bool:
    """片段是否含谓语（粗略：含动词/形容词/能愿词词性）"""
    try:
        import jieba
        import jieba.posseg as pseg
        jieba.setLogLevel(60)
        return any(f.startswith(("v",)) for _w, f in pseg.cut(frag))
    except ImportError:
        return True


def split_tunits(sent: str) -> list[str]:
    """按并列连词切 T-unit；从属连词不切（从句属于主句）"""
    parts = COORD_RX.split(sent)
    out, buf = [], ""
    for p in parts:
        if COORD_RX.fullmatch(p or ""):
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        else:
            buf += p or ""
    if buf.strip():
        out.append(buf.strip())
    return out or [sent]


def syntax(raw: str) -> dict:
    units, _ = clean_units(raw)
    lens = [cjk_len(s) for s in units]
    st = stats(lens)

    tunits, clauses, dropped = [], 0, 0
    for s in units:
        for t in split_tunits(s):
            frs = [f.strip() for f in FRAG_SPLIT.split(t) if cjk_len(f) >= FRAG_MIN_CJK]
            pred = [f for f in frs if has_predicate(f)]
            if not pred:
                dropped += 1
                continue
            tunits.append({"tunit": t, "clauses": len(pred), "cjk": cjk_len(t)})
            clauses += len(pred)

    n = len(tunits)
    return {
        "句数": st["n"],
        "句长均值": st["mean"],
        "句长P90": st["p90"],
        "最长句": st["max"],
        "T-unit数": n,
        "从句总数": clauses,
        "每T-unit从句数": round(clauses / n, 2) if n else None,
        "每句T-unit数": round(n / st["n"], 2) if st["n"] else None,
        "T-unit均长": round(sum(t["cjk"] for t in tunits) / n, 2) if n else None,
        "丢弃非T-unit片段": dropped,
        "口径": "作者句（清洗后）；T-unit 为连词规则近似，非标准 T-unit",
    }
