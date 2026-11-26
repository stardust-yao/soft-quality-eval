# -*- coding: utf-8 -*-
"""A2 用词熟悉度与解释

A2 是唯一有资格计分的对象，但**计分参数（K 值/封顶/合格线）目前 pending**，
所以本模块只产出**计数**，不产分数。

两件事可自动：
    ① 候选发现：按一份固定概念清单在回答里定位（最长不重叠匹配）
    ② 汇总：读入逐词判定，按「绝对数扣分」的口径算**未解释陌生概念数**

判题（熟悉 / 不熟悉 / 证据不足、是否需要解释、正文是否已解释）必须由人或 LLM
按判定表逐词完成——本模块不代替判题。

## 四条硬标准（判题时必须遵守）

1. **「调用参数 / 下载完成通知」≠「读到内容」**
   只认实际返回的材料文本。工具返回里的标题不算读到正文。

2. **不能把 Agent 自己说过的话当作用户常用的证明**
   否则是循环论证：它先说了这个词，再用自己说过的话证明这个词读者熟悉。

3. **同词不同义不放行**
   如「基线」在统计语境和在项目语境不是一个概念，不能因为一个义项常见就放过另一个。

4. **测试指令不计入自然对话词频**
   「用这个词造个句」里的出现，不代表用户在自然表达里会用。

## 计数口径

绝对数扣分：**按概念去重**，不按出现次数。
长文本天然更容易出现生僻词——接受这个偏差，并在报告里写出来。
"""
from __future__ import annotations

import json
import os
import re

# 【待定】每个「未解释陌生概念」扣多少分。仅为占位，不用于产出分数。
K_PER_TERM = None

FAIL_CLASSES = {"读者确认不熟悉，原文未充分解释", "未解释陌生"}
PASS_CLASSES = {
    "问题已给概念", "项目资料已用", "Teams日常用语", "正文已有解释或线索",
    "正文语境可理解", "项目测试用语，正文也有解释", "已有概念组合，不另计",
    "日历专名，不计陌生",
}
PENDING_CLASSES = {"证据不足"}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
EXAMPLE_INVENTORY = os.path.join(DATA_DIR, "inventory_example.json")


def load_inventory(path: str | None = None) -> list[tuple[str, re.Pattern]]:
    """读概念清单：[[概念, 正则], ...]

    清单是**领域相关**的——本仓库带的是某个 回答 A 项目的例子（60 项）。
    换项目必须自己建：把该领域里"内行才懂、外行看到会卡住"的说法列出来。
    """
    p = path or EXAMPLE_INVENTORY
    raw = json.load(open(p, encoding="utf-8"))
    inv = raw["inventory"] if isinstance(raw, dict) else raw
    return [(term, re.compile(pat, re.IGNORECASE if re.search(r"[A-Za-z]", pat) else 0))
            for term, pat in inv]


def discover(text: str, inventory) -> list[dict]:
    """定位候选词：最长不重叠匹配，同一概念多处出现逐条返回"""
    cands = []
    for term, rx in inventory:
        for m in rx.finditer(text):
            if m.end() > m.start():
                cands.append((m.start(), m.end(), term, m.group(0)))
    cands.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    picked, last_end = [], -1
    for start, end, term, surface in cands:
        if start >= last_end:
            picked.append({"concept": term, "surface": surface,
                           "start": start, "end": end})
            last_end = end
    return picked


def summarize(judgments: list[dict]) -> dict:
    """按概念去重后汇总。judgments: [{concept, classification, eligible}]"""
    seen, fail, pend, ok = set(), [], [], []
    for j in judgments:
        c = j["concept"]
        if c in seen:
            continue
        seen.add(c)
        cls = j.get("classification", "")
        if cls in FAIL_CLASSES:
            fail.append(c)
        elif cls in PENDING_CLASSES:
            pend.append(c)
        elif cls in PASS_CLASSES:
            ok.append(c)
    return {
        "角色": "评估（唯一计分项，但 K 值 pending）",
        "判过概念数": len(seen),
        "豁免数": len(ok),
        "未解释陌生概念数": len(fail),
        "未解释清单": fail,
        "证据不足": pend,
        "本轮处理": "只报计数，不产出分数（K 值未定）",
        "分母内生": "「适用概念数」算不算豁免类没有定论，所以判过/豁免/未解释三个数一起报，不合成比率。",
        "计数口径": "按概念去重，不按出现次数",
    }


def run(text: str, inventory_path: str | None = None,
        judgments_path: str | None = None) -> dict:
    inv = load_inventory(inventory_path)
    cands = discover(text, inv)
    out = {
        "角色": "评估",
        "候选词数": len(cands),
        "候选": [{"概念": c["concept"], "原文形式": c["surface"]} for c in cands],
        "清单来源": inventory_path or "data/inventory_example.json（示例，需替换成本领域的）",
    }
    if judgments_path and os.path.exists(judgments_path):
        js = json.load(open(judgments_path, encoding="utf-8"))
        out.update(summarize(js if isinstance(js, list) else js.get("judgments", [])))
    else:
        out.update({
            "判过概念数": None,
            "未解释陌生概念数": None,
            "本轮处理": "未提供逐词判定（judgments）——候选已列出，请人判后回填",
            "K值": "pending",
        })
    return out
