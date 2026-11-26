# -*- coding: utf-8 -*-
"""命令行入口

    # 跑一个 case（目录里要有 case.md / a.md / b.md / aspects.json）
    plaineval cases/demo
    plaineval cases/demo -o out/result.json
    plaineval cases/demo --html out/report.html

    # 只跑一份回答（不需要对照）
    plaineval --single path/to/answer.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from .core import evaluate, run_case


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def print_compare(res: dict) -> None:
    meta = res.get("case", {})
    print("=" * 66)
    if meta:
        print(f"case: {meta.get('case_id', '')}（{meta.get('task_type', '')}）")
        print(f"  A = {meta.get('a_name', 'A')}    B = {meta.get('b_name', 'B')}")
        if meta.get("human_preference"):
            print(f"  人工偏好: {meta['human_preference']}")
    print("=" * 66)
    print(f"{'指标':<24}{'A':>12}{'B':>12}")
    print("-" * 48)
    for row in res["compare"]:
        print(f"{row['指标']:<24}{_fmt(row['A']):>12}{_fmt(row['B']):>12}")

    print("\n【归属】")
    for k, v in res["A"]["ROLE"].items():
        print(f"  {k:<16}{v}")

    a, b = res["A"], res["B"]
    if a["B1_覆盖"]["missing"] or b["B1_覆盖"]["missing"]:
        print("\n【B1 覆盖缺口】")
        if a["B1_覆盖"]["missing"]:
            print(f"  A 缺: {'、'.join(a['B1_覆盖']['missing'])}")
        if b["B1_覆盖"]["missing"]:
            print(f"  B 缺: {'、'.join(b['B1_覆盖']['missing'])}")

    print("\n【B2 诉求位置】")
    for x, y in zip(a["B2_在哪"]["诉求位置"], b["B2_在哪"]["诉求位置"]):
        pa = "漏答" if x["position_pct"] is None else f"{x['position_pct']}%"
        pb = "漏答" if y["position_pct"] is None else f"{y['position_pct']}%"
        print(f"  {x['label']:<20}{pa:>9}{pb:>9}")

    print("\n【B3 共享强度分布】（必须看分布，只看均值会误判）")
    for k in a["B3_散不散"]["微观"]["共享强度分布"]:
        va = a["B3_散不散"]["微观"]["共享强度分布"][k]
        vb = b["B3_散不散"]["微观"]["共享强度分布"][k]
        print(f"  {k:<16}A {va:>3} 个    B {vb:>3} 个")

    # 计分（若 case 里有 scoring.json）
    if res.get("scoring"):
        sc = res["scoring"]
        print("\n【计分】层3 去重+递减+饱和，层4 三档 1:2:4（基数 %d 分）"
              % sc["刻度"]["单次扣分基数"])
        for side, name in (("A", "A"), ("B", "B")):
            o = sc[side]["呈现"]
            print(f"  {name}　措辞 {_fmt(o['措辞分'])}　信息组织 {_fmt(o['信息组织分'])}"
                  f"　短板加权 {_fmt(o.get('总分_短板加权'))}")
        print("\n  判定：")
        for k, v in sc["判定"].items():
            print(f"    {k:<14}{v}")
        for side in ("A", "B"):
            c = sc[side]["呈现"].get("冲突")
            if c:
                print(f"    {side} 维度冲突：{c}（差 {sc[side]['呈现']['差值']} 分）")
        print("\n  " + sc["提醒"])

    print("\n注意：B5/B6 只给候选，判定需人或 LLM 逐句确认；B6 为观察项不计分。")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="plaineval", description="回答的信息组织评测")
    ap.add_argument("case_dir", nargs="?", help="case 目录（含 case.md/a.md/b.md/aspects.json）")
    ap.add_argument("--single", metavar="ANSWER_MD", help="只评一份回答")
    ap.add_argument("-o", "--out", metavar="JSON", help="结果写入 JSON")
    ap.add_argument("--html", metavar="HTML", help="生成 HTML 报告")
    ap.add_argument("--quiet", action="store_true", help="不打印对照表")
    args = ap.parse_args(argv)

    if args.single:
        raw = open(args.single, encoding="utf-8").read()
        res = evaluate(raw)
        if args.out:
            os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
            json.dump(res, open(args.out, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"写入 {args.out}")
        if not args.quiet:
            print(json.dumps({k: v for k, v in res.items() if k != "B2_在哪"},
                             ensure_ascii=False, indent=1)[:4000])
        return 0

    if not args.case_dir:
        ap.print_help()
        return 2

    res = run_case(args.case_dir)
    if not args.quiet:
        print_compare(res)

    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        json.dump(res, open(args.out, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"\n写入 {args.out}")

    if args.html:
        from .report import write_html
        os.makedirs(os.path.dirname(args.html) or ".", exist_ok=True)
        write_html(res, args.html)
        print(f"写入 {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
