# -*- coding: utf-8 -*-
"""B7 指代清不清 —— 按对象类别诊断

依据：Gatti, Martinelli, Navigli (2026). Interpretable Coreference Resolution
      Evaluation Using Explicit Semantics. ACL 2026. doi:10.18653/v1/2026.acl-long.2126
      批评单一总分「不给诊断信息」，主张按语义类别报。

判据（硬）：
    能列出 ≥2 个合理对象 → 指代不清
    只有一个合理对象     → 清楚

另加一档（可扣分）：
    需读者自己配对 —— 如「前一份 / 后一份」，要回到前文数出两个对象才能对上。
    这不是「不清」，但读者要额外推理，属于表述问题。

类别：人 / 文件 / 时间 / 项目 / 层级·分组 / 决策项

**扫描器必须人工剔误报**：「因此 / 据此 / 此前 / 此外 / 与此同时」里的「此」不是实体回指。
本实现的「此」已用前后向排除，但仍建议人工过一遍。
"""
from __future__ import annotations

import re

from .units import clean_units

ANAPH = [
    ("前/后/这/那一+量词", re.compile(r"(前|后|这|那)一(份|个|条|项|版|批|层|点)")),
    ("该+名词", re.compile(r"该([\u4e00-\u9fa5]{2,6})")),
    ("上述+名词", re.compile(r"上述([\u4e00-\u9fa5]{2,6})")),
    ("此+名词（排除因此/据此/此前等）",
     re.compile(r"(?<![因据从为彼])此(?!前|外|时|举|后|致|类|间|刻)([\u4e00-\u9fa5]{2,6})")),
    ("它/它们", re.compile(r"它们|它(?!们)")),
    ("其+名词（排除其中/其他等）", re.compile(r"其(?![中他余它实次外])")),
    ("前者/后者", re.compile(r"前者|后者")),
    ("泛指回指", re.compile(r"(各层|各项|同一组|整组|这一项)")),
]

CAT = {
    "人": ["Owner", "Member", "执行人", "谁"],
    "文件": ["PPT", "Sheet", "文件", "工作簿", "包", "清单"],
    "时间": ["11月", "10月", "Daily", "窗口", "时间", "日期"],
    "项目": ["项目", "Case", "实例", "任务", "测试项目"],
    "层级/分组": ["层", "组", "能力", "分类", "等级", "批次"],
    "决策项": ["决定", "拍板", "取舍", "决策", "建议", "方案", "规则"],
}

# 需要读者自己配对的形式
PAIRING = re.compile(r"(前|后)一(份|个|条|项)")


def _classify(s: str) -> str:
    sc = {k: sum(s.count(w) for w in ws) for k, ws in CAT.items()}
    best = max(sc.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "未分类"


def scan(raw: str) -> dict:
    units, _ = clean_units(raw)
    hits = []
    seen = set()
    for i, s in enumerate(units, 1):
        for label, rx in ANAPH:
            for m in rx.finditer(s):
                key = (i, m.group(0))
                if key in seen:
                    continue
                seen.add(key)
                hits.append({
                    "句序": i, "类型": label, "表达": m.group(0),
                    "类别": _classify(s),
                    "需配对": bool(PAIRING.search(s)),
                    "原句": s,
                })
    from collections import Counter
    return {
        "作者句数": len(units),
        "回指数": len(hits),
        "每百句": round(len(hits) / max(1, len(units)) * 100, 1),
        "分类计数": dict(Counter(h["类别"] for h in hits)),
        "需配对数": sum(1 for h in hits if h["需配对"]),
        "明细": hits,
        "说明": "「需配对」= 同一句里出现两个指代（如「前一份/后一份」），读者要回前文数对象才能对上。",
    }
