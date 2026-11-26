# -*- coding: utf-8 -*-
"""切分层：语块（section）与作者句（author unit）

这是整个评测的地基。所有指标都建立在它上面，切错则全错。

三个层次：
    L1 位置段   开头 / 主体 / 结尾       —— 互斥、覆盖全文
    L2 语块     按标题切出的块            —— 互斥、同级
    L3 分支     语块内部的内容分支        —— 包含关系、可嵌套

本模块提供 L2 的语块切分，以及「作者句」——用于句级指标。

三个必须处理的格式陷阱（都在这份代码里）：
    1. 有的回答全文无空行 —— 不能靠空行分段
    2. 有的回答标题是「独立短行」而不是 Markdown `#` —— 要能认出来
    3. 表格被压平成纯文本后，每个单元格都是短行 —— 不能当成标题
       （否则一份 20 块里有 7 块是表格行）
"""
from __future__ import annotations

import re
from typing import Iterable

CJK = re.compile(r"[\u4e00-\u9fa5]")
LINK = re.compile(r"\[([^\]]*)\]\(<?[^)]*>?\)")          # [文字](<url>) → 文字
MD_DECOR = re.compile(r"[#*`>|_]+")                       # Markdown 装饰符
NOISE = re.compile(r"^(Export to CSV|￼|\s*)$")
BULLET = re.compile(r"^\s*[-•*·]\s+")
NUMLIST = re.compile(r"^\s*\d+[.、]\s+")
MD_HEAD = re.compile(r"^#{1,6}\s+")

SENT_SPLIT = re.compile(r"[。！？]")                       # 句末标点（**不含分号**）
SENT_MIN_CJK = 4                                          # 成句最小汉字数


# ───────────────────────── 基础工具 ─────────────────────────

def cjk_len(s: str) -> int:
    """汉字个数"""
    return len(CJK.findall(s))


def strip_decor(s: str) -> str:
    """去掉链接语法与 Markdown 装饰符，保留文字"""
    return MD_DECOR.sub("", LINK.sub(r"\1", s)).strip()


def text_only(raw: str) -> str:
    """清洗正文：去链接 URL、去 Markdown 装饰符。用于计算字符位置百分比。"""
    t = LINK.sub(r"\1", raw)
    t = MD_DECOR.sub("", t)
    return re.sub(r"[ \t]+", " ", t)


# ───────────────────────── L2 语块 ─────────────────────────

def table_zone(lines: list[str]) -> set[int]:
    """识别「被压平的表格区」，返回区内行下标集合。

    表格压平成文本后长这样（一行表格 = 1 个短标签 + 固定数量的长内容）：

        维度 | 方案A：按一级能力分组 | 方案B：按风险和副作用分层
        覆盖可见性 | 好，能快速看到每项能力测了多少 | 单阶段能力分布不完整

    判据：连续 ≥4 个「形状一致」（标签后跟同样数量的长行）的周期。
    列表项会打断周期，所以「标题 + 列表」的普通小节不会被误判。
    """
    def is_short(s: str) -> bool:
        t = strip_decor(s)
        n = cjk_len(t)
        return 0 < n <= 12 and not t.endswith(("。", "！", "？", "，", "、", "；"))

    def is_plain(s: str) -> bool:
        return bool(s) and not NOISE.match(s) and not BULLET.match(s) and not NUMLIST.match(s)

    # 只保留「普通正文行」的连续段
    runs, cur = [], []
    for i, ln in enumerate(lines):
        if is_plain(ln.strip()):
            cur.append(i)
        else:
            if cur:
                runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)

    zones: set[int] = set()
    for run in runs:
        cycles: list[tuple[int, list[int]]] = []
        i = 0
        while i < len(run):
            if is_short(lines[run[i]].strip()):
                longs, j = [], i + 1
                while j < len(run) and len(longs) < 2 and not is_short(lines[run[j]].strip()):
                    longs.append(run[j])
                    j += 1
                if longs:
                    cycles.append((run[i], longs))
                    i = j
                    continue
            i += 1

        k = 0
        while k < len(cycles):
            m = k
            while (m + 1 < len(cycles)
                   and cycles[m + 1][0] > cycles[m][1][-1]
                   and len(cycles[m + 1][1]) == len(cycles[k][1])):
                m += 1
            if m - k + 1 >= 4:
                for idx in range(k, m + 1):
                    zones.add(cycles[idx][0])
                    zones.update(cycles[idx][1])
                # 表头：紧邻表格区之前的连续短行
                pos = run.index(cycles[k][0])
                h = pos - 1
                while h >= 0 and is_short(lines[run[h]].strip()):
                    zones.add(run[h])
                    h -= 1
            k = m + 1
    return zones


def is_heading(line: str, next_line: str = "", in_table: bool = False) -> bool:
    """判断某行是不是标题（L2 语块的边界）。

    规则（按优先级）：
        0. 在表格区内 → 不是
        1. 以 `#` 开头 → 是
        2. 列表项 / 噪声行 → 不是
        3. 汉字数为 0 或 >16 → 不是
        4. 以 。！？，、； 结尾 → 不是
        5. 下一行是列表项 → 是（强信号）
        6. 汉字数 ≤10 且不含逗号 → 是（弱信号）
    """
    s = line.strip()
    if in_table:
        return False
    if MD_HEAD.match(s):
        return True
    if BULLET.match(s) or NUMLIST.match(s) or NOISE.match(s):
        return False
    t = strip_decor(s).strip(" *#`>|_")
    n = cjk_len(t)
    if n == 0 or n > 16:
        return False
    if t.endswith(("。", "！", "？", "，", "、", "；")):
        return False
    if next_line and (BULLET.match(next_line) or NUMLIST.match(next_line)):
        return True
    return n <= 10 and "，" not in t


def sections(raw: str) -> list[dict]:
    """切成 L2 语块。

    返回 [{index, title, body, start_char, level}]，index 从 1 开始。
    若全文无标题，返回一个 («开头段», 全文, 0) 的块。
    """
    lines = raw.split("\n")
    starts, cur = [], 0
    for ln in lines:
        starts.append(cur)
        cur += len(ln) + 1

    tz = table_zone(lines)
    heads: list[int] = []
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or NOISE.match(s):
            continue
        nxt = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
        if is_heading(ln, nxt, in_table=(i in tz)):
            heads.append(i)

    out = []
    for k, i in enumerate(heads):
        end = heads[k + 1] if k + 1 < len(heads) else len(lines)
        title = strip_decor(lines[i]).strip(" *#`>|_")
        lvl_m = MD_HEAD.match(lines[i].strip())
        out.append({
            "index": k + 1,
            "title": title,
            "body": "\n".join(lines[i:end]),
            "start_char": starts[i],
            "level": len(lvl_m.group(0).strip()) if lvl_m else 1,
        })
    if not out:
        out = [{"index": 0, "title": "(无标题)", "body": raw,
                "start_char": 0, "level": 1}]
    return out


def heading_depth(raw: str) -> int:
    """标题层级深度 = 用了几种不同级别的 Markdown 标题。无 Markdown 标题则为 1（平铺）。"""
    levels = re.findall(r"(?m)^(#{1,6})\s+", raw)
    return len(set(levels)) if levels else 1


# ───────────────────────── 作者句 ─────────────────────────

def raw_units(raw: str) -> list[str]:
    """作者句（未清洗）：跳 `#` 标题、URL 来源行、Export to CSV，按 。！？ 切，汉字≥4。

    注意：这只排除了 Markdown 标题和 URL 行，
    **没有**排除「独立短行标题」「表格单元格」「来源标签」——见 clean_units()。
    """
    out = []
    for ln in raw.split("\n"):
        line = ln.strip()
        if not line or line.startswith("#") or LINK.match(line) or NOISE.match(line):
            continue
        if re.match(r"^\[[^\]]*\]\(<?https?://", line):
            continue
        line = LINK.sub(r"\1", line)
        line = re.sub(r"^[\s\-•*]+", "", line)
        for part in SENT_SPLIT.split(line):
            part = part.strip()
            if cjk_len(part) >= SENT_MIN_CJK:
                out.append(part)
    return out


def _has_verb(s: str) -> bool:
    try:
        import jieba
        import jieba.posseg as pseg
        jieba.setLogLevel(60)
        return any(f.startswith("v") for _w, f in pseg.cut(s))
    except ImportError:
        return False


def clean_units(raw: str) -> tuple[list[str], list[dict]]:
    """作者句（清洗后）——所有句级指标都应该用这个。

    在 raw_units 基础上再排除三类「不是句子」的东西：
        · 独立短行标题（如「建议结论」「推荐执行顺序」）
        · 压平表格的单元格（如「覆盖可见性」「好，能快速看到每项能力测了多少」）
        · 来源标签（如「已确认安排」「发包通知」，≤6 字且不以句末标点结尾）

    但**保留引导句**：以「：」结尾且含动词的（如「建议直接拍板：」「需要确定：」）。
    它们是作者句——也正是 B6（废话）要判的对象。

    返回 (保留的句子, 被排除的 [{text, reason}])
    """
    lines = raw.split("\n")
    tz = table_zone(lines)
    heads, cells = set(), set()
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or NOISE.match(s):
            continue
        if i in tz:
            cells.add(strip_decor(s))
            continue
        nxt = next((l.strip() for l in lines[i + 1:] if l.strip()), "")
        if is_heading(ln, nxt):
            heads.add(strip_decor(s))

    keep, drop = [], []
    for u in raw_units(raw):
        t = strip_decor(u)
        if t.endswith(("：", ":")) and _has_verb(t):
            keep.append(u)                     # 引导句：保留
        elif t in heads:
            drop.append({"text": u, "reason": "标题"})
        elif t in cells:
            drop.append({"text": u, "reason": "表格单元格"})
        elif len(t) <= 6 and not t.endswith(("。", "！", "？")):
            drop.append({"text": u, "reason": "短标签/来源标记"})
        else:
            keep.append(u)
    return keep, drop


def stats(xs: Iterable[float]) -> dict:
    """均值 / P90 / 最大 / 个数"""
    xs = sorted(xs)
    n = len(xs)
    if not n:
        return {"n": 0, "mean": None, "p90": None, "max": None}
    return {"n": n,
            "mean": round(sum(xs) / n, 2),
            "p90": round(xs[int(0.9 * (n - 1))], 1),
            "max": max(xs)}
