# -*- coding: utf-8 -*-
"""评测主流程：跑一份回答的全部八项 + 句法基线"""
from __future__ import annotations

import json
import os

from . import (b3_dispersion, b4_structure, b5_state, b6_verbosity,
               b7_anaphora, b8_declaration)
from .b_coverage_position import coverage_summary, keyword_crosscheck, position_table
from .syntax import syntax

# 归属表：基线只报数，评估可判错
ROLE = {
    "B1_覆盖": "评估",
    "B2_在哪": "基线",
    "B3_散不散": "基线",
    "B4_层级": "基线",
    "B5_状态vs推理": "评估",
    "B6_废话": "观察（不计分）",
    "B7_指代": "评估",
    "B8_数量自述": "评估（零争议）",
}


def evaluate(raw: str, aspects: list[dict] | None = None,
             qud: list[dict] | None = None) -> dict:
    """跑一份回答。

    raw     : 回答全文（Markdown 或纯文本）
    aspects : [{id, label, blocks, keywords, verdict}]，来自 aspects.json
    qud     : [{id, question}]，来自 aspects.json 的 qud 字段
    """
    pos = position_table(raw, aspects or [])
    return {
        "ROLE": ROLE,
        "句法基线": syntax(raw),
        "B1_覆盖": coverage_summary(pos["aspects"]),
        "B2_在哪": {
            "正文字符数": pos["body_chars"],
            "语块数": pos["blocks"],
            "诉求位置": pos["aspects"],
            "关键词交叉校验": keyword_crosscheck(raw, aspects or []),
            "口径": "位置% = 语块起始处的清洗后正文字符 ÷ 全文清洗后字符；分母剔除 markdown 与链接 URL",
        },
        "B3_散不散": {
            "微观": b3_dispersion.micro(raw),
            "宏观": b3_dispersion.macro(raw),
        },
        "B4_层级": b4_structure.structure(raw),
        "B5_状态vs推理": {**b5_state.screen(raw), "QUD": qud or []},
        "B6_废话": b6_verbosity.screen(raw),
        "B7_指代": b7_anaphora.scan(raw),
        "B8_数量自述": b8_declaration.check(raw),
    }


def evaluate_pair(a_raw: str, b_raw: str,
                  aspects_a: list[dict] | None = None,
                  aspects_b: list[dict] | None = None,
                  qud: list[dict] | None = None) -> dict:
    return {"A": evaluate(a_raw, aspects_a, qud),
            "B": evaluate(b_raw, aspects_b, qud)}


def compare(result: dict) -> list[dict]:
    """把两份结果并成对照表（只放可比的数）"""
    a, b = result["A"], result["B"]
    rows = [
        ("句数", a["句法基线"]["句数"], b["句法基线"]["句数"]),
        ("句长均值", a["句法基线"]["句长均值"], b["句法基线"]["句长均值"]),
        ("T-unit 数", a["句法基线"]["T-unit数"], b["句法基线"]["T-unit数"]),
        ("每 T-unit 从句数", a["句法基线"]["每T-unit从句数"], b["句法基线"]["每T-unit从句数"]),
        ("B3 延续率", a["B3_散不散"]["微观"]["延续率_CONTINUE"], b["B3_散不散"]["微观"]["延续率_CONTINUE"]),
        ("B3 指称距离", a["B3_散不散"]["微观"]["指称距离_平均间隔句"], b["B3_散不散"]["微观"]["指称距离_平均间隔句"]),
        ("B3 平均集中度", a["B3_散不散"]["宏观"]["平均集中度"], b["B3_散不散"]["宏观"]["平均集中度"]),
        ("B4 语块数", a["B4_层级"]["标题块数"], b["B4_层级"]["标题块数"]),
        ("B4 列表项平均字数", a["B4_层级"]["列表项平均字数"], b["B4_层级"]["列表项平均字数"]),
        ("B4 标题层级深度", a["B4_层级"]["标题层级深度"], b["B4_层级"]["标题层级深度"]),
        ("B1 缺口数", len(a["B1_覆盖"]["missing"]), len(b["B1_覆盖"]["missing"])),
        ("B5 候选句数", a["B5_状态vs推理"]["候选数"], b["B5_状态vs推理"]["候选数"]),
        ("B7 回指数", a["B7_指代"]["回指数"], b["B7_指代"]["回指数"]),
        ("B7 需配对数", a["B7_指代"]["需配对数"], b["B7_指代"]["需配对数"]),
        ("B8 声明不一致数", a["B8_数量自述"]["声明不一致数"], b["B8_数量自述"]["声明不一致数"]),
    ]
    return [{"指标": k, "A": x, "B": y} for k, x, y in rows]


def load_case(case_dir: str) -> dict:
    """读一个 case 目录：case.md / a.md / b.md / aspects.json"""
    def rd(name):
        p = os.path.join(case_dir, name)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None

    spec = {}
    p = os.path.join(case_dir, "aspects.json")
    if os.path.exists(p):
        spec = json.load(open(p, encoding="utf-8"))

    return {
        "question": rd("case.md"),
        "a": rd("a.md"),
        "b": rd("b.md"),
        "aspects_a": spec.get("aspects_a", spec.get("aspects")),
        "aspects_b": spec.get("aspects_b", spec.get("aspects")),
        "qud": spec.get("qud"),
        "meta": spec.get("meta", {}),
    }


def run_case(case_dir: str) -> dict:
    c = load_case(case_dir)
    if not c["a"] or not c["b"]:
        raise ValueError(f"{case_dir} 缺少 a.md 或 b.md")
    res = evaluate_pair(c["a"], c["b"], c["aspects_a"], c["aspects_b"], c["qud"])
    res["case"] = c["meta"]
    res["question"] = c["question"]
    res["compare"] = compare(res)
    return res
