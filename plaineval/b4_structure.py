# -*- coding: utf-8 -*-
"""B4 层级（结构形态）

指标：
    标题块数        L2 语块个数
    块字数中位数    各块正文字符数的中位数
    列表项数 / 列表项平均字数 / 列表项占比
    标题层级深度    Markdown 标题用了几种级别（无标题 = 1，即平铺）
    Markdown标题数

**列表项平均字数是最稳定的一项**——它不依赖块识别，换格式也不会变。
例：45 字/条 = 一条里塞两三句话（段落伪装成列表）；19 字/条 = 一条一件事。

**不要报「失衡度（最长块÷最短块）」**：最短块常常是「需要确定：」这种引导句，
这个数测的是引导句有多短，不是结构好坏。

归属：基线（形态），只报数不计分。
"""
from __future__ import annotations

from .units import BULLET, NUMLIST, cjk_len, sections, text_only


def structure(raw: str) -> dict:
    body = text_only(raw)
    secs = sections(raw)

    sizes = []
    for i, s in enumerate(secs):
        end = secs[i + 1]["start_char"] if i + 1 < len(secs) else len(raw)
        sizes.append(cjk_len(body[0:0]) or cjk_len(text_only(raw[s["start_char"]:end])))

    items = []
    for ln in raw.split("\n"):
        t = ln.strip()
        if BULLET.match(t) or NUMLIST.match(t):
            items.append(t)

    import re
    md = re.findall(r"(?m)^(#{1,6})\s+", raw)
    depth = len(set(md)) if md else 1

    sizes_sorted = sorted(sizes)
    n = len(sizes_sorted)
    med = (sizes_sorted[n // 2] if n % 2 else
           (sizes_sorted[n // 2 - 1] + sizes_sorted[n // 2]) / 2) if n else None

    return {
        "标题块数": len(secs),
        "块字数中位数": med,
        "块字数最长": max(sizes) if sizes else None,
        "块字数最短": min(sizes) if sizes else None,
        "Markdown标题数": len(md),
        "标题层级深度": depth,
        "列表项数": len(items),
        "列表项平均字数": round(sum(cjk_len(x) for x in items) / len(items), 1) if items else None,
        "列表项占比": round(len(items) / max(1, sum(1 for l in raw.split("\n") if l.strip())), 2),
        "口径": "块=按标题切出的 L2 语块（已排除压平表格的行）；字数为清洗后正文字符",
    }
