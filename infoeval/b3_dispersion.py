# -*- coding: utf-8 -*-
"""B3 散不散（集中）

两个层次：

  微观（句与句）Entity Grid
      延续率   = 相邻句对中「至少共享一个实体」的比例   ← Centering Theory 的 CONTINUE 型
      切换率   = 1 − 延续率
      指称距离 = 同一实体相邻两次提及之间隔几句（均值）
      共享强度分布 = 相邻句对的交集 ÷ min(两边实体数)，分四档

  宏观（块与块）主题词分布
      跨块数    = 该词出现在几个 L2 语块
      跨度      = (末次出现 − 首次出现) ÷ 正文长度
      集中度    = 1 − (跨块数−1) ÷ (总块数−1)      1 = 只在一块，0 = 每块都有

**必须报分布，不能只报均值。** 同一批文本里，
词面重叠（LNO）和实体延续率可以给出相反方向，因为一个数连续值、一个数二元值，
均值会把「两极分化」和「均匀型」抹成同一个数。

归属：基线（形态），只报数不计分。
"""
from __future__ import annotations

from collections import Counter, defaultdict

from .entities import entity_set
from .units import clean_units, sections, text_only

STOP_TOPIC = {
    "问题", "情况", "时候", "方面", "内容", "方式", "过程", "部分",
    "条", "个", "项", "类", "种", "层", "次", "天", "点", "边",
    "建议", "结论", "优势", "代价", "方法", "目的", "理由", "实际",
}
BUCKETS = ("0 完全零共享", "轻微 0~0.3", "中度 0.3~0.6", "高度 >0.6")


def micro(raw: str) -> dict:
    units, _ = clean_units(raw)
    sets = [entity_set(s) for s in units]
    pairs = list(zip(sets, sets[1:]))

    shared = [1 if (a and b and a & b) else 0 for a, b in pairs]
    ratios = [len(a & b) / min(len(a), len(b)) if (a and b) else 0.0 for a, b in pairs]

    buckets = Counter()
    for r in ratios:
        buckets["0 完全零共享" if r == 0 else
                "轻微 0~0.3" if r < 0.3 else
                "中度 0.3~0.6" if r < 0.6 else "高度 >0.6"] += 1

    appear = defaultdict(list)
    for i, s in enumerate(sets):
        for e in s:
            appear[e].append(i)
    dists = [y - x for v in appear.values() for x, y in zip(v, v[1:])]

    def longest_run(v):
        best = run = 1
        for a, b in zip(v, v[1:]):
            run = run + 1 if b == a + 1 else 1
            best = max(best, run)
        return best

    n_pairs = len(pairs) or 1
    cont = sum(shared) / n_pairs
    return {
        "句数": len(units),
        "实体数": len(appear),
        "延续率_CONTINUE": round(cont, 4),
        "切换率_SHIFT": round(1 - cont, 4),
        "指称距离_平均间隔句": round(sum(dists) / len(dists), 2) if dists else None,
        "实体平均出现句数": round(sum(len(v) for v in appear.values()) / len(appear), 2) if appear else None,
        "最长连续出现句数": max((longest_run(v) for v in appear.values()), default=0),
        "共享强度分布": {k: buckets[k] for k in BUCKETS},
        "共享强度占比pct": {k: round(buckets[k] / n_pairs * 100, 1) for k in BUCKETS},
        "空实体句数": sum(1 for s in sets if not s),
        "口径": "作者句（清洗后）；空实体句按「不共享」计入，不剔除",
    }


def macro(raw: str, topk: int = 12) -> dict:
    body = text_only(raw)
    secs = sections(raw)
    nblk = len(secs)
    spans = []
    for i, s in enumerate(secs):
        end = secs[i + 1]["start_char"] if i + 1 < nblk else len(raw)
        spans.append((s["start_char"], end))

    import jieba
    import jieba.posseg as pseg
    jieba.setLogLevel(60)
    words = Counter()
    for w, f in pseg.cut(raw):
        if f.startswith(("n", "eng")) and len(w) >= 2 and w not in STOP_TOPIC:
            words[w] += 1

    rows = []
    for w, c in words.most_common(topk):
        occ = [m for m in range(len(raw)) if raw.startswith(w, m)]
        hit = {i + 1 for o in occ for i, (s, e) in enumerate(spans) if s <= o < e}
        span = (occ[-1] - occ[0]) / len(raw) * 100 if len(occ) > 1 else 0.0
        conc = 1 - (len(hit) - 1) / (nblk - 1) if nblk > 1 else 1.0
        rows.append({"主题词": w, "出现次数": len(occ), "跨块数": len(hit),
                     "跨度pct": round(span, 1), "集中度": round(conc, 2)})

    return {
        "块数": nblk,
        "平均集中度": round(sum(r["集中度"] for r in rows) / len(rows), 2) if rows else None,
        "平均跨度pct": round(sum(r["跨度pct"] for r in rows) / len(rows), 1) if rows else None,
        "跨一半以上块的主题词数": sum(1 for r in rows if r["跨块数"] > nblk / 2),
        "警告": "「跨一半以上块的主题词数」是绝对计数，块数不同的两份文本不可直接比；看趋势用「平均集中度」和「平均跨度」。",
        "明细": sorted(rows, key=lambda r: -r["跨块数"]),
    }
