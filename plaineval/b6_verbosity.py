# -*- coding: utf-8 -*-
"""B6 有没有废话 —— 删句测试（观察项，不计分）

问法（对齐 JUDGEBERT 的 meaning preservation 范式）：
    删掉这句，读者会少知道哪一件具体的事？
        写不出来     → 无效
        只丢半件     → 部分无效
        丢事实/规则/状态 → 保留

**为什么不计分：**
    ① 三种实现（参考人工 / 本轮人工 / 规则版）逐句一致率只有 24/45
    ② 存在构造性矛盾：排版用的引导句（「建议同时确认：」「需要确定：」）
       在删句测试下必然判无效，但它实际上帮助读者扫读
    ③ 同一批文本，引导句算不算无效会导致方向反转

状态：观察项。用足够多 case 重跑后若仍无稳定方向，则去掉。

本模块只做定位。
"""
from __future__ import annotations

from .units import clean_units

LEAD_IN_HINT = ("：", ":")          # 以冒号结尾的引导句是 B6 的主要争议来源
META = ["以上是建议", "尚未据此", "仅供参考"]


def screen(raw: str) -> dict:
    units, _ = clean_units(raw)
    rows = []
    for i, s in enumerate(units, 1):
        kind = []
        if s.rstrip().endswith(LEAD_IN_HINT):
            kind.append("引导句（争议）")
        if any(w in s for w in META):
            kind.append("元话语（已在 B5 计，此处不重复）")
        if any(w in s for w in ("因此，", "综上", "这样最快", "总的来说")):
            kind.append("总结重申")
        if kind:
            rows.append({"序号": i, "可疑类型": kind, "句": s})
    return {"作者句数": len(units), "候选数": len(rows), "候选": rows,
            "状态": "观察项 · 不计分 · 不参与「有区分/无区分」判定"}
