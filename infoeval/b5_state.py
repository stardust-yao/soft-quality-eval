# -*- coding: utf-8 -*-
"""B5 状态 vs 推理 —— 三档判定

依据：Wu, Mangla, Durrett, Li (2023). QUDeval. EMNLP 2023.
      doi:10.18653/v1/2023.emnlp-main.325
      「话语 = 连续提问与回答」；把 QUD 的理论约束做成具体协议。

做法：
  ① 从题目里抽出预设问题（QUD），写进 cases/<case>/aspects.json 的 "qud" 字段
  ② 逐句问：这句回答的是哪个 QUD？
  ③ 检查：如果回答的是「状态」，关键状态给了吗？

三档：
  ① 完整状态     给出了具体对象的具体状态（是/否/未知/数量/时间）→ 通过
  ② 半状态+推理   只有半个状态、关键状态缺失，用「不能推出」代替 → 问题
  ③ 纯元话语     不回答任何 QUD，也不给状态和行动            → 问题（归 B5，不计入 B6）

改写方向：② → ①
  「不能用前一份的成功证明后一份已恢复」
  → 「10月29日那份 PPT 恢复状态无法判定；只读测试不受影响，可继续。」

本模块只做**定位**（把候选句捞出来），分档需人或 LLM 逐句确认后填回 JSON。
"""
from __future__ import annotations

import json
import os

from .units import clean_units

BOUNDARY = ["不能据此", "不能用", "不能证明", "不等于", "不代表", "不能当作",
            "不能当成", "不能默认", "不能算", "不算", "尚未核实", "未核实"]
META = ["以上是建议", "尚未据此", "仅供参考", "我的取舍是", "不必重新讨论"]


def load_qud(path: str | None) -> list[dict]:
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("qud", [])


def screen(raw: str) -> dict:
    """返回候选句清单（定位用，不是判定）。"""
    units, _ = clean_units(raw)
    rows = []
    for i, s in enumerate(units, 1):
        tags = []
        if any(w in s for w in META):
            tags.append("③候选_元话语")
        if any(w in s for w in BOUNDARY):
            tags.append("②候选_推断边界")
        if tags:
            rows.append({"序号": i, "初筛": tags, "句": s})
    return {"候选数": len(rows), "作者句数": len(units), "候选": rows,
            "说明": "初筛召回率高、精度低——候选里大部分是正常句，必须逐句过。"}
