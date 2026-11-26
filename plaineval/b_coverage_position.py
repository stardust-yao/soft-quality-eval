# -*- coding: utf-8 -*-
"""B1 有没有（覆盖）· B2 在哪（定位）

二者共用同一份配置：cases/<case>/aspects.json
    B1 判「每个诉求有没有落点」
    B2 算「落点在第几个位置」

配置格式（由人编写，可审）：
{
  "aspects": [
    {"id": "aspect_1", "label": "比较两个方案",
     "blocks": [1, 2, 3],          # 该诉求落在哪些 L2 语块（0 = 首个标题之前的开头段）
     "keywords": ["方案A", "方案B"], # 仅用于交叉校验，不用于判定
     "verdict": "有"},              # 有 / 部分 / 无  —— 由人或 LLM 判定后填
    ...
  ]
}

归属：
    B1 = 评估项（漏答是明确的错）
    B2 = 基线（位置早晚本身没有好坏）
"""
from __future__ import annotations

from .units import sections, text_only


def position_table(raw: str, aspects: list[dict]) -> dict:
    """按语块落点算位置百分比（字符口径，分母用清洗后正文）。"""
    body = text_only(raw)
    N = len(body)
    secs = sections(raw)

    def block_pos(b: int) -> int | None:
        if b == 0:
            return 0
        if b - 1 >= len(secs):
            return None
        title = secs[b - 1]["title"]
        j = body.find(title)
        return j if j >= 0 else None

    rows = []
    for a in aspects:
        blocks = a.get("blocks") or []
        if not blocks:
            rows.append({"id": a["id"], "label": a["label"],
                         "position_pct": None, "block": None,
                         "block_title": "漏答", "verdict": a.get("verdict", "无")})
            continue
        first = min(blocks)
        pos = block_pos(first)
        rows.append({
            "id": a["id"], "label": a["label"],
            "position_pct": round(pos / N * 100, 1) if pos is not None else None,
            "block": first,
            "block_title": "开头段" if first == 0 else secs[first - 1]["title"],
            "verdict": a.get("verdict", "有"),
        })
    return {"body_chars": N, "blocks": len(secs), "aspects": rows}


def coverage_summary(rows: list[dict]) -> dict:
    """B1 汇总：落空清单 + 命中率。"""
    missing = [r for r in rows if r["verdict"] == "无" or r["position_pct"] is None]
    partial = [r for r in rows if r["verdict"] == "部分"]
    return {
        "total": len(rows),
        "covered": len(rows) - len(missing) - len(partial),
        "partial": [r["label"] for r in partial],
        "missing": [r["label"] for r in missing],
        "note": "覆盖 100% 不等于没有多余内容；多余内容不在 B1 内计。",
    }


def keyword_crosscheck(raw: str, aspects: list[dict]) -> list[dict]:
    """关键词交叉校验。

    关键词法测的是「这个词第一次出现在哪」，不是「这件事第一次被讲在哪」，
    因此**系统性偏早**——只能用来看「配置里判有、但关键词一次都没出现」这类明显矛盾。
    """
    body = text_only(raw)
    out = []
    for a in aspects:
        kws = a.get("keywords") or []
        hit = [k for k in kws if k in body]
        out.append({"id": a["id"], "label": a["label"],
                    "keywords": kws, "hit": hit,
                    "missing_keywords": [k for k in kws if k not in body]})
    return out
