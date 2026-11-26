# -*- coding: utf-8 -*-
"""实体抽取（供 B3 散不散 使用）

依据：Barzilay & Lapata (2008), Modeling Local Coherence: An Entity-Based
Approach, Computational Linguistics 34(1). doi:10.1162/coli.2008.34.1.1

原文用依存句法分析给每个实体标语法角色（S 主语 / O 宾语 / X 其他 / – 缺席）。
本实现没有句法分析器，改用**位置启发式**近似：

    第一个名词      → S
    动词之后的名词  → O
    其余名词        → X

这是工程近似，不是原文方法。换解析器（LTP / HanLP）可提高准确性。
"""
from __future__ import annotations

import re

CJK = re.compile(r"[\u4e00-\u9fa5]")

# jieba 把英文专名/术语（如 Case、Sheet、PPT 这类）标成 eng 而不是 n。
# 只取 n 会漏掉几乎全部英文实体，实体数会掉到每句 1 个。
NOUN_TAGS = ("n", "eng")

# 停用词：量词 + 极泛名词 + 元话语标记（后者是「关于内容的话」，不是话语实体）
STOP_NOUN = {
    "问题", "情况", "时候", "方面", "内容", "方式", "过程", "部分",
    "条", "个", "项", "类", "种", "层", "次", "天", "点", "边",
    "建议", "结论", "优势", "代价", "方法", "目的", "理由", "实际",
}


def _pseg():
    import jieba
    import jieba.posseg as pseg
    jieba.setLogLevel(60)
    return pseg


def entity_roles(sentence: str) -> dict[str, str]:
    """返回 {实体: 角色}，角色为 S / O / X。无实体的句子返回 {}。"""
    pseg = _pseg()
    pairs = list(pseg.cut(sentence))
    nouns = [w for w, f in pairs
             if f.startswith(NOUN_TAGS) and len(w) >= 2 and w not in STOP_NOUN]
    if not nouns:
        return {}

    has_verb = any(f.startswith("v") for _w, f in pairs)
    if not has_verb:
        return {n: "X" for n in nouns}

    # 找到第一个动词的字符位置
    vpos, cur = None, 0
    for w, f in pairs:
        if f.startswith("v"):
            vpos = cur
            break
        cur += len(w)

    out: dict[str, str] = {}
    first = True
    for n in nouns:
        idx = sentence.find(n)
        if first:
            out[n] = "S"
            first = False
        elif vpos is not None and idx > vpos:
            out.setdefault(n, "O")
        else:
            out.setdefault(n, "X")
    return out


def entity_set(sentence: str) -> set[str]:
    return set(entity_roles(sentence).keys())
