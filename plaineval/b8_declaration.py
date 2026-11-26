# -*- coding: utf-8 -*-
"""B8 数量自述对不对

两种检查：
  ① 数量声明 vs 实际列举数（「只需拍板三组决定」→ 后面是不是 3 组）
  ② 序数回指一致性（「第四层」→ 前面列举的层数够不够 4 层）

判定：零争议（数一数就知道）——全部 11 项里唯一「换谁判都一样」的一项。

**白名单是必须的**，否则误报率极高（实测 15 处里 11 处不是真声明）：
    认：N组 / N项 / N件事 / N个偏差 / N类风险 / N条建议 / N条规则 / N步
    不认：「一点工夫」（程度副词）、「两个项目创建失败」（具体对象）、
         「同一组」「第一层」（带上限定的不算）、「第四层」（序数回指，另算）、
         「只能决定一件事，就决定这一项」（不是列举声明）

**只在一个 L2 语块内数列举项**，不能跨块数——否则会把后面小节的列表也算进来。

列举计数分三种（缺一不可）：
    a. 同行：冒号后用 、／； 分隔  → 数分隔符 + 1
    b. 同块内的编号行 1. 2. 3.    → 数编号行
    c. 同块内的列表行 - •         → 数列表行
"""
from __future__ import annotations

import re

from .units import BULLET, NUMLIST, clean_units, sections, strip_decor

CN = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
      "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}

DECL = re.compile(
    r"(?<![同第这那每])"
    r"([一二两三四五六七八九十]|\d{1,2})\s*"
    r"(组|项|件事|个偏差|类风险|条建议|条规则|步)"
)
ORD = re.compile(r"第([一二两三四五六七八九十]|\d{1,2})(层|组|项|步)")


def _num(s: str):
    return int(s) if s.isdigit() else CN.get(s)


def _count_inline(s: str) -> int:
    """同行列举：冒号后按 、／； 数项"""
    m = re.search(r"[：:](.+)$", s)
    if not m:
        return 0
    body = re.sub(r"[*_`]", "", m.group(1))
    return len([p for p in re.split(r"[、；;]", body) if p.strip()])


def _block_of(secs: list[dict], pos: int) -> dict | None:
    """字符位置落在哪个 L2 语块"""
    for i, s in enumerate(secs):
        end = secs[i + 1]["start_char"] if i + 1 < len(secs) else 10 ** 9
        if s["start_char"] <= pos < end:
            return s
    return None


def _count_in_block(block: dict) -> int:
    """数一个语块内的编号行 + 列表行"""
    n = 0
    for ln in block["body"].split("\n"):
        t = ln.strip()
        if NUMLIST.match(t) or BULLET.match(t):
            n += 1
    return n


def check(raw: str) -> dict:
    units, _ = clean_units(raw)
    secs = sections(raw)
    decls, ords = [], []

    for i, s in enumerate(units):
        t = strip_decor(s)          # 去掉 ** 等装饰符，否则「…优先：**」不以冒号结尾
        pos = raw.find(s[:12])
        blk = _block_of(secs, pos) if pos >= 0 else None
        in_block = _count_in_block(blk) if blk else 0

        for m in DECL.finditer(t):
            v = _num(m.group(1))
            if v is None or v > 10:
                continue
            inline = _count_inline(t)
            # 是否列举声明：整句是引导句（以：结尾），或声明后紧跟冒号
            tail = t[m.end():].strip(" *_`")
            at_eol = tail in ("", "：", ":") or t.rstrip().endswith(("：", ":"))

            if inline >= 2:
                actual = inline
            elif at_eol and in_block >= 2:
                actual = in_block
            else:
                continue                      # 不是列举声明，跳过

            decls.append({
                "句序": i + 1, "声明": m.group(0), "声明数": v,
                "同行列举": inline, "同块列举": in_block, "实际": actual,
                "一致": actual == v, "原句": s,
            })

        for m in ORD.finditer(t):
            ords.append({"句序": i + 1, "表达": m.group(0),
                         "序数": _num(m.group(1)), "原句": s})

    # 序数一致性：数声明之前的编号列举块
    blocks_num, cur = [], []
    for i, s in enumerate(units):
        if NUMLIST.match(s):
            cur.append(i)
        elif cur:
            blocks_num.append(cur)
            cur = []
    if cur:
        blocks_num.append(cur)

    for o in ords:
        before = [b for b in blocks_num if b[0] < o["句序"] - 1]
        o["前文列举块数"] = len(before)
        o["前文最长列举项数"] = max((len(b) for b in before), default=0)
        o["一致"] = (o["前文最长列举项数"] >= o["序数"]) if before and o["序数"] else None

    bad = [d for d in decls if not d["一致"]]
    return {
        "作者句数": len(units),
        "数量声明数": len(decls),
        "声明不一致数": len(bad),
        "序数回指数": len(ords),
        "序数不一致数": sum(1 for o in ords if o.get("一致") is False),
        "声明明细": decls,
        "序数明细": ords,
        "状态": "零争议判据；触发频率需多样本验证",
    }
