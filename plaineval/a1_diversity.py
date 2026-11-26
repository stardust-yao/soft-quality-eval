# -*- coding: utf-8 -*-
"""A1 词汇多样性（基线，权重 0）

指标
    N 词次      分词后的总词数
    V 词型      去重后的词种数
    H nats      词频熵 = −Σ p·ln p
    MSTTR-50    按顺序切不重叠的 50 词段，段内 V/50 取均值
    词段TTR方差  各段 TTR 的方差
    尾部丢弃词数 不足 50 词的尾段（必须披露，否则不同长度的文本不可比）

**为什么权重 0**
    · 词频熵与篇幅的 Spearman ρ 高达 0.95 —— 它本质上是"篇幅的替身"
    · MSTTR 归一化后与人工偏好只有 4/7 一致
    · 在可读性语境里，"词汇丰富"通常是减分项（生僻词多 = 难读）

所以这一项只作描述和回归特征，不判好坏。
"""
from __future__ import annotations

import math
from collections import Counter

WINDOW = 50          # MSTTR 段长（写死，不随 case 改）
MIN_TOKEN = 1


def _normalize(text: str) -> str:
    import re
    t = re.sub(r"\[([^\]]*)\]\(<?[^)]*>?\)", r"\1", text)   # 链接留文字
    return re.sub(r"[#*`>|_]+", " ", t)                      # 去装饰符


def tokenize(text: str) -> list[str]:
    import re
    import jieba
    jieba.setLogLevel(60)
    t = _normalize(text)
    return [w.strip() for w in jieba.cut(t)
            if w.strip() and not re.fullmatch(r"[\s\W_]+", w) and len(w) >= MIN_TOKEN]


def entropy(tokens) -> float:
    n = len(tokens)
    if n <= 1:
        return 0.0
    c = Counter(tokens)
    return -sum((v / n) * math.log(v / n) for v in c.values())


def msttr(tokens, L: int = WINDOW):
    """按原顺序切不重叠的完整段；尾部不足 L 的丢弃"""
    segs = [tokens[i:i + L] for i in range(0, len(tokens) - L + 1, L)]
    if not segs:
        return None, 0, []
    ttrs = [len(set(s)) / L for s in segs]
    return sum(ttrs) / len(ttrs), len(segs), ttrs


def measure(text: str) -> dict:
    ts = tokenize(text)
    mu, nseg, ttrs = msttr(ts)
    var = (sum((x - mu) ** 2 for x in ttrs) / (len(ttrs) - 1)
           if (mu is not None and len(ttrs) > 1) else None)
    return {
        "角色": "基线（权重 0）",
        "N_词次": len(ts),
        "V_词型": len(set(ts)),
        "H_nats": round(entropy(ts), 4) if ts else 0.0,
        "MSTTR50": round(mu, 4) if mu is not None else None,
        "完整词段数": nseg,
        "尾部丢弃词数": len(ts) - nseg * WINDOW,
        "词段TTR方差": round(var, 6) if var is not None else None,
        "可靠": "否（词数<100）" if len(ts) < 100 else "是",
        "说明": "H 与篇幅 ρ≈0.95，本质是篇幅替身；MSTTR 与人工偏好仅 4/7 一致。故权重 0。",
    }
