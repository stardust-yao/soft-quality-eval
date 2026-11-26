# -*- coding: utf-8 -*-
"""评测主流程：跑一份回答的 11 项（措辞 3 + 信息组织 8）"""
from __future__ import annotations

import json
import os

from . import (a1_diversity, a2_familiarity, b3_dispersion, b4_structure,
               b5_state, b6_verbosity, b7_anaphora, b8_declaration, scoring)
from .b_coverage_position import coverage_summary, keyword_crosscheck, position_table
from .syntax import syntax

# 归属表：基线只报数；评估可判错；观察不计分
ROLE = {
    # 措辞层
    "A1_词汇多样性": "基线（权重 0）",
    "A2_用词熟悉度": "评估（唯一计分项，K 值 pending）",
    "A3_句法": "基线（权重 0）",
    # 信息组织层
    "B1_覆盖": "评估",
    "B2_在哪": "基线",
    "B3_散不散": "基线",
    "B4_层级": "基线",
    "B5_状态vs推理": "评估",
    "B6_废话": "观察（不计分）",
    "B7_指代": "评估",
    "B8_数量自述": "评估（零争议）",
}

LAYER = {
    "措辞层": ["A1_词汇多样性", "A2_用词熟悉度", "A3_句法"],
    "信息组织层": ["B1_覆盖", "B2_在哪", "B3_散不散", "B4_层级",
                   "B5_状态vs推理", "B6_废话", "B7_指代", "B8_数量自述"],
}


def evaluate(raw: str, aspects: list[dict] | None = None,
             qud: list[dict] | None = None,
             inventory: str | None = None,
             judgments: str | None = None) -> dict:
    """跑一份回答。

    raw       : 回答全文（Markdown 或纯文本）
    aspects   : [{id, label, blocks, keywords, verdict}]，来自 aspects.json
    qud       : [{id, question}]，来自 aspects.json 的 qud 字段
    inventory : A2 概念清单路径（不给就用示例清单，仅作演示）
    judgments : A2 逐词判定结果路径
    """
    pos = position_table(raw, aspects or [])
    return {
        "ROLE": ROLE,
        "LAYER": LAYER,
        "A1_词汇多样性": a1_diversity.measure(raw),
        "A2_用词熟悉度": a2_familiarity.run(raw, inventory, judgments),
        "A3_句法": syntax(raw),
        "B1_覆盖": coverage_summary(pos["aspects"]),
        "B2_在哪": {
            "正文字符数": pos["body_chars"],
            "语块数": pos["blocks"],
            "诉求位置": pos["aspects"],
            "关键词交叉校验": keyword_crosscheck(raw, aspects or []),
            "口径": "位置% = 语块起始处的清洗后正文字符 ÷ 全文清洗后字符；分母剔除 markdown 与链接 URL",
        },
        "B3_散不散": {"微观": b3_dispersion.micro(raw),
                      "宏观": b3_dispersion.macro(raw)},
        "B4_层级": b4_structure.structure(raw),
        "B5_状态vs推理": {**b5_state.screen(raw), "QUD": qud or []},
        "B6_废话": b6_verbosity.screen(raw),
        "B7_指代": b7_anaphora.scan(raw),
        "B8_数量自述": b8_declaration.check(raw),
    }


def evaluate_pair(a_raw: str, b_raw: str,
                  aspects_a: list[dict] | None = None,
                  aspects_b: list[dict] | None = None,
                  qud: list[dict] | None = None,
                  inventory: str | None = None,
                  judgments_a: str | None = None,
                  judgments_b: str | None = None) -> dict:
    return {
        "A": evaluate(a_raw, aspects_a, qud, inventory, judgments_a),
        "B": evaluate(b_raw, aspects_b, qud, inventory, judgments_b),
    }


def compare(result: dict) -> list[dict]:
    """对照表：只放两份结果里同口径、可比的数"""
    a, b = result["A"], result["B"]
    rows = [
        # 措辞层
        ("A1 词次 / 词型", f"{a['A1_词汇多样性']['N_词次']} / {a['A1_词汇多样性']['V_词型']}",
         f"{b['A1_词汇多样性']['N_词次']} / {b['A1_词汇多样性']['V_词型']}"),
        ("A1 MSTTR-50", a["A1_词汇多样性"]["MSTTR50"], b["A1_词汇多样性"]["MSTTR50"]),
        ("A1 尾部丢弃词数", a["A1_词汇多样性"]["尾部丢弃词数"], b["A1_词汇多样性"]["尾部丢弃词数"]),
        ("A2 候选词数", a["A2_用词熟悉度"]["候选词数"], b["A2_用词熟悉度"]["候选词数"]),
        ("A2 未解释陌生概念数", a["A2_用词熟悉度"].get("未解释陌生概念数"),
         b["A2_用词熟悉度"].get("未解释陌生概念数")),
        ("A3 句长均值", a["A3_句法"]["句长均值"], b["A3_句法"]["句长均值"]),
        ("A3 句长 P90", a["A3_句法"]["句长P90"], b["A3_句法"]["句长P90"]),
        ("A3 T-unit 数", a["A3_句法"]["T-unit数"], b["A3_句法"]["T-unit数"]),
        ("A3 每 T-unit 从句数", a["A3_句法"]["每T-unit从句数"], b["A3_句法"]["每T-unit从句数"]),
        # 信息组织层
        ("B1 缺口数", len(a["B1_覆盖"]["missing"]), len(b["B1_覆盖"]["missing"])),
        ("B2 拍板位置%", _pos(a, "拍板什么"), _pos(b, "拍板什么")),
        ("B3 延续率", a["B3_散不散"]["微观"]["延续率_CONTINUE"],
         b["B3_散不散"]["微观"]["延续率_CONTINUE"]),
        ("B3 指称距离", a["B3_散不散"]["微观"]["指称距离_平均间隔句"],
         b["B3_散不散"]["微观"]["指称距离_平均间隔句"]),
        ("B3 平均集中度", a["B3_散不散"]["宏观"]["平均集中度"],
         b["B3_散不散"]["宏观"]["平均集中度"]),
        ("B4 语块数", a["B4_层级"]["标题块数"], b["B4_层级"]["标题块数"]),
        ("B4 列表项平均字数", a["B4_层级"]["列表项平均字数"], b["B4_层级"]["列表项平均字数"]),
        ("B4 标题层级深度", a["B4_层级"]["标题层级深度"], b["B4_层级"]["标题层级深度"]),
        ("B5 候选句数", a["B5_状态vs推理"]["候选数"], b["B5_状态vs推理"]["候选数"]),
        ("B7 回指数", a["B7_指代"]["回指数"], b["B7_指代"]["回指数"]),
        ("B7 需配对数", a["B7_指代"]["需配对数"], b["B7_指代"]["需配对数"]),
        ("B8 声明不一致数", a["B8_数量自述"]["声明不一致数"], b["B8_数量自述"]["声明不一致数"]),
    ]
    return [{"指标": k, "A": x, "B": y} for k, x, y in rows]


def _pos(r, label):
    for x in r["B2_在哪"]["诉求位置"]:
        if x["label"] == label:
            return x["position_pct"]
    return None


def load_case(case_dir: str) -> dict:
    def rd(name):
        p = os.path.join(case_dir, name)
        return open(p, encoding="utf-8").read() if os.path.exists(p) else None

    spec, p = {}, os.path.join(case_dir, "aspects.json")
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
        "inventory": spec.get("inventory"),
        "judgments_a": spec.get("judgments_a"),
        "judgments_b": spec.get("judgments_b"),
    }


def score_from_file(case_dir: str, result: dict) -> dict | None:
    """如果 case 目录里有 scoring.json，就按层3/层4 算分"""
    p = os.path.join(case_dir, "scoring.json")
    if not os.path.exists(p):
        return None
    spec = json.load(open(p, encoding="utf-8"))
    sides = {}
    for side in ("A", "B"):
        objs = spec.get(side, {})
        wording_objs = {k: v for k, v in objs.items() if k.startswith("A")}
        info_objs = {k: v for k, v in objs.items() if k.startswith("B")}
        sides[side] = {
            "措辞": scoring.layer_score(wording_objs) if wording_objs else None,
            "信息组织": scoring.layer_score(info_objs) if info_objs else None,
        }
        sides[side]["呈现"] = scoring.overall(sides[side]["措辞"], sides[side]["信息组织"])
    return {
        "刻度": scoring.scales(),
        "A": sides["A"], "B": sides["B"],
        "判定": {
            "措辞": scoring.verdict(sides["A"]["呈现"]["措辞分"], sides["B"]["呈现"]["措辞分"]),
            "信息组织": scoring.verdict(sides["A"]["呈现"]["信息组织分"], sides["B"]["呈现"]["信息组织分"]),
            "总分_短板加权": scoring.verdict(sides["A"]["呈现"].get("总分_短板加权"),
                                        sides["B"]["呈现"].get("总分_短板加权")),
        },
        "提醒": "两个维度方向可能相反。默认不合成总分——措辞与信息组织不是同一量纲。",
    }


def run_case(case_dir: str) -> dict:
    c = load_case(case_dir)
    if not c["a"] or not c["b"]:
        raise ValueError(f"{case_dir} 缺少 a.md 或 b.md")
    res = evaluate_pair(c["a"], c["b"], c["aspects_a"], c["aspects_b"], c["qud"],
                        c["inventory"], c["judgments_a"], c["judgments_b"])
    res["case"] = c["meta"]
    res["question"] = c["question"]
    res["compare"] = compare(res)
    sc = score_from_file(case_dir, res)
    if sc:
        res["scoring"] = sc
    return res
