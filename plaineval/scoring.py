# -*- coding: utf-8 -*-
"""计分机制（层3 + 层4）

四层，各管一件事，不要混着调：

    层1 维度      措辞 / 信息组织      → 两个独立分数，不合成
    层2 对象      11 项里 5 项进分     → 权重 pending
    层3 问题项    计什么、计几次        → 去重单位 + 递减 + 饱和   ← 本模块
    层4 严重程度  每次扣多少            → 三档 + 几何系数           ← 本模块

## 层4：三档 + 1:2:4

判据按**读者行为**定，不按"我觉得严重"：

    轻 ×1  注意到了，但不影响理解
    中 ×2  要停下、回看、自己补一步推理
    重 ×4  会得出错误结论，或漏掉一个决策

为什么几何不用等差：读者感受是"要不要重读"，不是线性量。
1:2:4 的意思是——一个让人读错结论的错，等于四个让人略过的小毛病。

## 层3：三个机制

1. **去重单位 = 一个可指认的阅读障碍点**
   不是"命中次数"。同一句里的「前一份/后一份」是**一处**问题，不是两处。

2. **递减** 同类第 1 个 ×1.0、第 2 个 ×0.7、第 3 个 ×0.5、第 4 个起不计
   读者的痛感是边际递减的。不减的话，啰嗦的长回答会被同一个毛病打穿到 0。

3. **不除分母**（不除以句数/篇幅）
   除以篇幅会让长文本占便宜，而且分母怎么定没有依据。改用递减 + 饱和控制。

## 层1：为什么不合成一个总分

措辞 85 分的意思是"有 2 个词读者不认识"；
信息组织 89.5 分的意思是"有几个地方要读者多走一步"。
**加起来没有意义。** 默认报两个数 + 一个冲突提示。

"冲突"本身是最有信息量的输出：这份回答是"词说清楚了但结构乱"，
还是"结构清楚但有行话"。
"""
from __future__ import annotations

UNIT = 5                              # 单次扣分基数
SEV = {"轻": 1, "中": 2, "重": 4}      # 严重度系数（几何级差）
DECAY = (1.0, 0.7, 0.5)               # 同类问题第 1/2/3 个的递减
CAP = len(DECAY)                      # 同类饱和：第 4 个起不计

# 进分的 5 个核心对象；其余为基线/观察，不进分
SCORED = ["A2_用词熟悉度", "B1_覆盖", "B5_状态vs推理", "B7_指代", "B8_数量自述"]
W_OBJECT = None                       # None = 等权（pending：等多样本后再定）
W_LAYER = None                        # None = 不合成总分（默认只报两个维度）
FLAT_THRESHOLD = 5                    # 差距小于 5 分视为持平（单评者噪声量级）


def group_cost(severity: str, count: int) -> float:
    """一类问题扣多少：基数 × 严重度 × 递减，饱和到 CAP 个"""
    sev = SEV.get(severity)
    if sev is None:
        raise ValueError(f"未知严重度 {severity!r}，只接受 {list(SEV)}")
    return sum(UNIT * sev * DECAY[i] for i in range(min(count, CAP)))


def object_score(groups: list[dict]) -> dict:
    """一个对象的分数。

    groups: [{"类型": "未解释陌生概念", "严重度": "中", "个数": 2}, ...]
            **同一类型**计在一组里，不同组之间不共享递减额度。
    """
    rows, total = [], 0.0
    for g in groups:
        c = group_cost(g["严重度"], g["个数"])
        total += c
        rows.append({"类型": g["类型"], "严重度": g["严重度"],
                     "个数": g["个数"], "计入个数": min(g["个数"], CAP),
                     "扣分": round(c, 1)})
    return {"对象": None, "明细": rows, "总扣分": round(total, 1),
            "分数": round(max(0.0, 100 - total), 1)}


def layer_score(objects: dict[str, list[dict]]) -> dict:
    """一个维度（措辞 / 信息组织）的分数：对象等权平均。

    objects: {"B1_覆盖": [groups...], "B5_状态vs推理": [...], ...}
    """
    parts, detail = [], {}
    for name, groups in objects.items():
        s = object_score(groups)
        s["对象"] = name
        detail[name] = s
        parts.append(s["分数"])
    return {
        "对象明细": detail,
        "均分": round(sum(parts) / len(parts), 1) if parts else None,
        "最低分": min(parts) if parts else None,
        "权重": "等权（pending）" if W_OBJECT is None else W_OBJECT,
        "进分对象": list(objects),
    }


def overall(wording: dict | None, info: dict | None) -> dict:
    """两个维度怎么呈现。

    默认**不合成一个总分**——措辞和信息组织不是同一量纲。
    只给两个数 + 一个冲突提示。若确实要一个数，用短板加权（0.6 最低 + 0.4 平均）。
    """
    w = wording["均分"] if wording else None
    i = info["均分"] if info else None
    out = {"措辞分": w, "信息组织分": i, "总分": None,
           "说明": "两个维度不相加：措辞分说的是'有几个词不认识'，信息组织分说的是'有几处要多走一步'，量纲不同。",
           "权重状态": "对象等权、维度不合成（均 pending，需多样本后按方向一致率定）"}

    if w is not None and i is not None:
        d = round(w - i, 1)
        if abs(d) < 1:
            out["冲突"] = None
            out["提示"] = "两个维度基本一致"
        else:
            out["冲突"] = "措辞更好" if d > 0 else "信息组织更好"
            out["差值"] = round(abs(d), 1)
            out["提示"] = (f"两个维度方向相反：{'措辞' if d > 0 else '信息组织'}更好，差 {abs(d)} 分。"
                           "这比单一总分有信息量——它说明这份回答是「词说清楚了但结构乱」"
                           "还是「结构清楚但有行话」。")
        # 若明确要求一个总分：短板加权
        out["总分_短板加权"] = round(0.6 * min(w, i) + 0.4 * (w + i) / 2, 1)
        out["总分_说明"] = "短板加权 = 0.6 × 较低维度 + 0.4 × 平均。读者体验是短板主导的。此权重 pending。"
    return out


def verdict(a_score: float | None, b_score: float | None,
            flat: float = FLAT_THRESHOLD) -> str:
    """两份差多少才算真差"""
    if a_score is None or b_score is None:
        return "无法比较（有维度未评分）"
    d = abs(a_score - b_score)
    if d < flat:
        return f"持平（差 {round(d,1)} 分 < {flat} 分阈值，小数点在决定胜负）"
    return f"{'A' if a_score > b_score else 'B'} 更好（差 {round(d,1)} 分）"


def scales() -> dict:
    """把刻度写死，便于文档与脚本同源"""
    return {
        "单次扣分基数": UNIT,
        "严重度系数": SEV,
        "递减": DECAY,
        "同类饱和": CAP,
        "进分对象": SCORED,
        "持平阈值": FLAT_THRESHOLD,
        "三档判据": {
            "轻": "注意到了，但不影响理解",
            "中": "要停下、回看、自己补一步推理",
            "重": "会得出错误结论，或漏掉一个决策",
        },
        "状态": "层3/层4 已定；层2 权重、层1 合成都 pending",
    }
