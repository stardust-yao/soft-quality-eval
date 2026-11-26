# -*- coding: utf-8 -*-
"""A2 用词熟悉度与解释

A2 是唯一有资格计分的对象，但**计分参数（K 值/封顶/合格线）目前 pending**，
所以本模块只产出**计数**，不产分数。

两件事可自动：
    ① 候选发现：按一份固定概念清单在回答里定位（最长不重叠匹配）
    ② 汇总：读入逐词判定，按「绝对数扣分」的口径算**未解释陌生概念数**

判题（熟悉 / 不熟悉 / 证据不足、是否需要解释、正文是否已解释）必须由人或 LLM
按判定表逐词完成——本模块不代替判题。

## 信息源（判定不靠读者确认，靠内部数据对照）

    E1 问题原文              用户自己的提问里出现过这个词
    E2 成员自然对话（IM 校准） 用户在日常表达里用过        ← 排除测试指令、同词不同义
    E3 项目资料（工具实际返回） 项目语境里已存在这个概念      ← 只认返回正文，不认调用参数
    E4 本轮回答自身           正文里已解释                ← 只有定义/例子算解释
    E5 Agent 自己的输出        ❌ 禁止作为证据（循环论证）

判定顺序：

    E1 命中          → 豁免（问题已给概念）
    E4 命中          → 豁免（正文已有解释）
    E2 或 E3 命中     → 豁免（内部已用）
    全不命中 + 领域术语 → 未解释陌生
    材料缺失/检索不到  → 待查，不扣分

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

# 标准路径：内部数据全不命中 + 正文未解释
# 兼容：早期把「读者确认不熟悉」当判据；现在不要求读者确认，保留为等类别名
FAIL_CLASSES = {"未解释陌生", "内部数据无命中且原文未解释", "读者确认不熟悉，原文未充分解释"}
PASS_CLASSES = {
    "问题已给概念", "项目资料已用", "Teams日常用语", "正文已有解释或线索",
    "正文语境可理解", "项目测试用语，正文也有解释", "已有概念组合，不另计",
    "日历专名，不计陌生",
}
PENDING_CLASSES = {"证据不足", "材料缺失", "待查"}

# 信息源登记（供文档与校验共用）
EVIDENCE_SOURCES = [
    {"id": "E1", "name": "问题原文", "proves": "用户提问里已出现", "boundary": "出现≠会用"},
    {"id": "E2", "name": "成员自然对话", "proves": "用户日常表达用过", "boundary": "排除测试指令；同词不同义不放行"},
    {"id": "E3", "name": "项目资料（工具实际返回）", "proves": "项目语境已存在", "boundary": "只认返回正文，不认调用参数"},
    {"id": "E4", "name": "本轮回答自身", "proves": "正文已解释", "boundary": "只有定义/例子算解释"},
    {"id": "E5", "name": "Agent 自己的输出", "proves": "无", "boundary": "禁止作为证据（循环论证）"},
]

# 不再往包里放领域数据：清单属于 case，放在 cases/<case>/inventory.json
EXAMPLE_INVENTORY = None


def load_inventory(path: str | None = None) -> list[tuple[str, re.Pattern]]:
    """读概念清单：[[概念, 正则], ...]

    清单是**领域相关**的——本仓库带的是 `cases/demo/inventory.json`，只有 3 项，仅作演示。
    换项目必须自己建：把该领域里"内行才懂、外行看到会卡住"的说法列出来。
    """
    if path is None:
        raise FileNotFoundError(
            "没有给概念清单。清单是领域相关的，请在 aspects.json 里用 inventory 字段"
            "指向 cases/<case>/inventory.json，或参考 cases/demo/inventory.json 的格式自建。")
    raw = json.load(open(path, encoding="utf-8"))
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


def check_evidence(j: dict) -> list[str]:
    """证据自洽校验：判为「未解释」的，E1–E4 必须全部未命中。

    这是防自己写错的一道闸——判了扣分但证据里写着「E3 命中」，
    说明标签和证据矛盾，必须人工回看。
    """
    ev = j.get("evidence") or {}
    cls = j.get("classification", "")
    if cls not in FAIL_CLASSES:
        return []
    hits = [k for k in ("E1", "E2", "E3", "E4")
            if str(ev.get(k, "")).startswith(("命中", "有"))]
    if hits:
        return [f"{j['concept']}：判为未解释，但 {','.join(hits)} 显示命中"]
    return []


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
    conflicts = [m for j in judgments for m in check_evidence(j)]
    return {
        "角色": "评估（唯一计分项，但 K 值 pending）",
        "证据矛盾": conflicts,
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
        "信息源": EVIDENCE_SOURCES,
        "判定顺序": "E1 → E4 → E2/E3 任一命中即豁免；全不命中且属领域术语 → 未解释；材料缺失 → 待查不扣分",
        "候选词数": len(cands),
        "候选": [{"概念": c["concept"], "原文形式": c["surface"]} for c in cands],
        "清单来源": inventory_path or "（未提供）",
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
