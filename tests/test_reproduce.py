"""校验：case01 的结果必须可复现。

任何人 clone 下来跑 `pytest` 或直接 `python tests/test_reproduce.py`，
数值应当与 EXPECTED 完全一致（jieba 版本差异允许 ±0.02 的相对误差）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from plaineval import run_case  # noqa: E402

# 锚点：这些数变了说明切分口径被改了，必须同步更新文档
EXPECTED = {
    "A": {
        "词次": 854,
        "词型": 389,
        "MSTTR50": 0.8835,
        "A2候选": 7,
        "A2判过": 5,
        "A2未解释": 0,
        "句数": 47,
        "句长均值": 27.79,
        "T-unit数": 53,
        "每T-unit从句数": 2.23,
        "延续率": 0.2391,
        "指称距离": 11.07,
        "平均集中度": 0.76,
        "语块数": 7,
        "列表项平均字数": 45.5,
        "标题层级深度": 2,
        "B1缺口数": 1,
        "B7需配对数": 2,
        "B8声明不一致": 0,
    },
    "B": {
        "词次": 897,
        "词型": 397,
        "MSTTR50": 0.8847,
        "A2候选": 28,
        "A2判过": 16,
        "A2未解释": 2,
        "句数": 47,
        "句长均值": 23.55,
        "T-unit数": 51,
        "每T-unit从句数": 2.06,
        "延续率": 0.5217,
        "指称距离": 7.2,
        "平均集中度": 0.65,
        "语块数": 13,
        "列表项平均字数": 18.9,
        "标题层级深度": 1,
        "B1缺口数": 0,
        "B7需配对数": 0,
        "B8声明不一致": 0,
    },
}

# B2 诉求位置（字符口径）
EXPECTED_POS_A = {"比较两个方案": 10.3, "各自影响": 10.3, "给建议": 0.0,
                  "拍板什么": 79.3, "已确认安排": 0.0, "四个风险": 38.1}
EXPECTED_POS_B = {"比较两个方案": 15.4, "各自影响": 29.6, "给建议": 0.0,
                  "拍板什么": 68.0, "已确认安排": 0.2, "四个风险": 39.9}


def extract(res, side):
    r = res[side]
    return {
        "词次": r["A1_词汇多样性"]["N_词次"],
        "词型": r["A1_词汇多样性"]["V_词型"],
        "MSTTR50": r["A1_词汇多样性"]["MSTTR50"],
        "A2候选": r["A2_用词熟悉度"]["候选词数"],
        "A2判过": r["A2_用词熟悉度"].get("判过概念数"),
        "A2未解释": r["A2_用词熟悉度"].get("未解释陌生概念数"),
        "句数": r["A3_句法"]["句数"],
        "句长均值": r["A3_句法"]["句长均值"],
        "T-unit数": r["A3_句法"]["T-unit数"],
        "每T-unit从句数": r["A3_句法"]["每T-unit从句数"],
        "延续率": r["B3_散不散"]["微观"]["延续率_CONTINUE"],
        "指称距离": r["B3_散不散"]["微观"]["指称距离_平均间隔句"],
        "平均集中度": r["B3_散不散"]["宏观"]["平均集中度"],
        "语块数": r["B4_层级"]["标题块数"],
        "列表项平均字数": r["B4_层级"]["列表项平均字数"],
        "标题层级深度": r["B4_层级"]["标题层级深度"],
        "B1缺口数": len(r["B1_覆盖"]["missing"]),
        "B7需配对数": r["B7_指代"]["需配对数"],
        "B8声明不一致": r["B8_数量自述"]["声明不一致数"],
    }


def pos_map(res, side):
    return {x["label"]: x["position_pct"] for x in res[side]["B2_在哪"]["诉求位置"]}


def main() -> int:
    res = run_case(os.path.join(ROOT, "cases/case01"))
    fails = []

    for side in ("A", "B"):
        got = extract(res, side)
        for k, want in EXPECTED[side].items():
            g = got[k]
            if isinstance(want, float) or isinstance(g, float):
                if g is None or abs(float(g) - float(want)) > max(0.02, abs(want) * 0.02):
                    fails.append(f"{side}.{k}: got {g}, want {want}")
            elif g != want:
                fails.append(f"{side}.{k}: got {g}, want {want}")

    for side, want in (("A", EXPECTED_POS_A), ("B", EXPECTED_POS_B)):
        got = pos_map(res, side)
        for k, v in want.items():
            g = got.get(k)
            if g is None or abs(float(g) - v) > 0.2:
                fails.append(f"{side}.B2[{k}]: got {g}, want {v}")

    if fails:
        print("❌ 不一致：")
        for f in fails:
            print("   ", f)
        return 1

    print("✅ case01 全部锚点一致（11 项）")
    print(f"   词次 {EXPECTED['A']['词次']}/{EXPECTED['B']['词次']}　"
          f"A2未解释 {EXPECTED['A']['A2未解释']}/{EXPECTED['B']['A2未解释']}　"
          f"句数 {EXPECTED['A']['句数']}/{EXPECTED['B']['句数']}　"
          f"延续率 {EXPECTED['A']['延续率']}/{EXPECTED['B']['延续率']}　"
          f"语块 {EXPECTED['A']['语块数']}/{EXPECTED['B']['语块数']}")
    return 0


def test_reproduce():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
