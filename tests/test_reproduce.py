"""回归测试：cases/demo 的 11 项结果必须可复现。

任何人 clone 下来跑 `python tests/test_reproduce.py`，
数值应与下面的锚点一致（jieba 版本差异允许 ≤2% 相对误差）。

`cases/demo` 是**合成样例**——不含任何真实项目信息，
但刻意复现了本方法要处理的格式怪异：一份用 Markdown 标题 + 空行，
另一份无空行、标题是独立短行、且含一张压平表格。

改了切分口径或任何指标定义，这里的数就会变 —— 那是提醒你同步改文档，不是把锚点改掉。
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from plaineval import run_case  # noqa: E402

EXPECTED = {
    "A": {
        "词次": 486,
        "词型": 237,
        "MSTTR50": 0.8356,
        "A2候选": 5,
        "A2判过": 3,
        "A2未解释": 1,
        "句数": 27,
        "句长均值": 28.19,
        "T-unit数": 30,
        "每T-unit从句数": 1.83,
        "延续率": 0.5385,
        "指称距离": 3.65,
        "平均集中度": 0.62,
        "语块数": 9,
        "列表项平均字数": 15.7,
        "标题层级深度": 3,
        "B1缺口数": 1,
        "B7需配对数": 1,
        "B8声明不一致": 1,
    },
    "B": {
        "词次": 480,
        "词型": 203,
        "MSTTR50": 0.7956,
        "A2候选": 5,
        "A2判过": 0,
        "A2未解释": 0,
        "句数": 37,
        "句长均值": 20.38,
        "T-unit数": 36,
        "每T-unit从句数": 2.0,
        "延续率": 0.5833,
        "指称距离": 4.35,
        "平均集中度": 0.53,
        "语块数": 8,
        "列表项平均字数": 10.4,
        "标题层级深度": 1,
        "B1缺口数": 0,
        "B7需配对数": 0,
        "B8声明不一致": 0,
    },
}

EXPECTED_POS = {
    "A": {
          "比较两个方案": 2.6,
          "各自影响": 4.0,
          "给建议": 0.1,
          "拍板什么": 88.8,
          "回滚方案": None,
          "当前情况": 4.0,
    },
    "B": {
          "比较两个方案": 20.9,
          "各自影响": 38.3,
          "给建议": 0.0,
          "拍板什么": 80.3,
          "回滚方案": 46.3,
          "当前情况": 4.7,
    },
}


def extract(r):
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


def main() -> int:
    res = run_case(os.path.join(ROOT, "cases/demo"))
    fails = []

    for side in ("A", "B"):
        got = extract(res[side])
        for k, want in EXPECTED[side].items():
            g = got[k]
            if isinstance(want, float) or isinstance(g, float):
                if g is None or abs(float(g) - float(want)) > max(0.02, abs(want) * 0.02):
                    fails.append(f"{side}.{k}: got {g}, want {want}")
            elif g != want:
                fails.append(f"{side}.{k}: got {g}, want {want}")

        pos = {a["label"]: a["position_pct"] for a in res[side]["B2_在哪"]["诉求位置"]}
        for k, want in EXPECTED_POS[side].items():
            g = pos.get(k)
            if want is None:
                if g is not None:
                    fails.append(f"{side}.B2[{k}]: got {g}, want 漏答")
            elif g is None or abs(float(g) - want) > 0.2:
                fails.append(f"{side}.B2[{k}]: got {g}, want {want}")

    if fails:
        print("❌ 不一致（改了口径？请同步更新文档与本文件的锚点）：")
        for f in fails:
            print("   ", f)
        return 1

    print("✅ demo 全部锚点一致（11 项 + 12 个位置值）")
    print(f"   句数 {EXPECTED['A']['句数']}/{EXPECTED['B']['句数']}　"
          f"A2未解释 {EXPECTED['A']['A2未解释']}/{EXPECTED['B']['A2未解释']}　"
          f"B8不一致 {EXPECTED['A']['B8声明不一致']}/{EXPECTED['B']['B8声明不一致']}")
    return 0


def test_reproduce():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())
