# 怎么给自己建一套 case

> 三步：写题 → 写两份回答 → 填 aspects.json。然后一条命令。

---

## 第一步：准备文件

```
cases/你的case名/
├── case.md              # 题目原文（一个问题）
├── a.md                 # 回答 A
├── b.md                 # 回答 B
├── aspects.json         # 诉求清单 + QUD + 清单路径（下面详说）
├── judgments_a.json     # A2 逐词判定（可选，见第五节）
├── judgments_b.json
└── inventory.json       # A2 的概念清单（可选，不给就用仓库里的示例）
```

`a.md` / `b.md` 直接粘贴原始输出即可，**不用清洗**。Markdown、纯文本、带链接都行——`plaineval/units.py` 会处理格式。

---

## 第二步：写 aspects.json

这是唯一需要动脑的地方，分三块。

### ① meta

```json
"meta": {
  "case_id": "L0-BRF-006-C001",
  "task_type": "决策分析",
  "a_name": "回答 A",
  "b_name": "回答 B",
  "human_preference": "B",
  "n_raters": 1
}
```

`human_preference` 填你的盲评结果。**它的用途只有一个：事后看自动指标的方向和人工偏好对不对得上。** 没有盲评就留空。

### ② qud（B5 的预设问题）

从 `case.md` 里逐句抠出用户在问什么。**只抠明确问到的，不要脑补。**

```json
"qud": [
  {"id": "Q1", "question": "两个方案各自怎样、有什么影响？"},
  {"id": "Q2", "question": "应该选哪个方案？"},
  {"id": "Q3", "question": "现在需要拍板什么？"}
]
```

判 B5 时用：**这句话回答的是哪个 QUD？如果答的是"状态"，关键状态给了吗？**

### ③ aspects_a / aspects_b（B1 + B2 的输入）

```json
"aspects_a": [
  {"id": "aspect_1", "label": "比较两个方案", "blocks": [1],
   "keywords": ["方案A", "方案B"], "verdict": "有"},
  {"id": "aspect_7", "label": "Daily Meeting 消失", "blocks": [],
   "keywords": ["Daily", "Meeting"], "verdict": "无"}
]
```

| 字段 | 含义 |
|---|---|
| `label` | 诉求，从题目里抽 |
| `blocks` | 落在第几个语块（**0 = 第一个标题之前的开头段**）；漏答填 `[]` |
| `keywords` | 只用于交叉校验，**不参与判定** |
| `verdict` | `有` / `部分` / `无` —— **人判** |

**注意**：A 和 B 的 `blocks` 一般不一样——同一诉求在两份回答里落点位置不同，这正是 B2 要测的。

---

## 第三步：怎么填 blocks

### 先跑一遍看语块清单

```bash
python -m plaineval.cli cases/你的case名 -o out/r.json
python -c "
import json; r=json.load(open('out/r.json'))
for k in ('A','B'):
    print(k, r[k]['B4_层级']['标题块数'], '块')"
```

或者直接看：

```python
from plaineval.units import sections
for s in sections(open("cases/你的case名/a.md", encoding="utf-8").read()):
    print(s["index"], s["title"])
```

### 然后对照语块填 blocks

**判定标准只有一条**：这个诉求是在哪个语块里**被真正回答**的？

反例（曾经踩过）：

| 想法 | 为什么错 |
|---|---|
| 「第一句就出现了"方案A""方案B"，所以比较在 0.2%」 | 那是**提到**，不是**比较**。真正的比较在第 1 块（10.3%） |
| 「"环境"这个词在 19% 出现过，所以在 19%」 | 那是顺带一提，讲风险要到 34% |
| 「一个诉求只能有一个落点」 | 允许多个（`blocks: [4,5,6]`），B2 取最小的那个 |

### 落点判定的模糊地带

**一个诉求可能散在多个语块里，取"第一个明确服务它"的块。**

实例：回答 B 的「各自影响」——
- 六维对比表里（第 4 块起）已经讲了影响
- 但它有独立的「方案A的影响」「方案B的影响」小节（第 5、6 块）

填 `[5, 6]`（取独立小节）还是 `[4,5,6]`（含对比表）？**取决于你定的规则，但同一批 case 必须一致。**

建议规则：
```
落点 = 以该诉求为主旨的语块
若只是"顺带提到"，不算落点
```

---

## 第三点五步：A2 的概念清单要自己建

A2 的候选词是从一份**领域相关**的清单里定位出来的。仓库带的
`plaineval/data/inventory_example.json` 是某个 回答 A 项目的 60 项例子，**不能直接用**。

```
做法：把该领域里「内行才懂、外行看到会卡住」的说法列出来
格式：[["概念名", "匹配正则"], ...]
      第二列可以写同义写法，例如 "风险和副作用分层|副作用分层"
```

判断标准：**一个不了解这个项目的人看到这个词，会不会卡住？**

---

## 第四步：跑

```bash
# 控制台对照表
python -m plaineval.cli cases/你的case名

# 加 JSON + HTML
python -m plaineval.cli cases/你的case名 -o out/r.json --html out/report.html
```

---

## 第五步：B5 / B6 / B7 要人工判

这三项脚本只给**候选**，不给结论。流程：

```
① 跑一遍，拿到候选句清单（在 result.json 里）
② 逐句判档，把结论填回一个 judgments.json（格式见下）
③ 下一轮复用，不用重判
```

```json
{
  "case_id": "…",
  "b5": [
    {"side": "A", "sentence_index": 4, "tier": "②",
     "missing_state": "分工到底现在定不定",
     "rewrite": "逐条分工未定（不按各15条推进），须在拍板时确认。"}
  ],
  "b7": [
    {"side": "A", "sentence_index": 21, "expression": "前一份/后一份",
     "needs_pairing": true}
  ]
}
```

**为什么不做成自动**：判定需要读内容。做成自动等于把一个不可复核的判断藏进脚本里。

---

## 多人评的时候

如果两个人各判一遍：

```
① 报一致率 + 置信区间（按任务类型选指标：分类用 κ/α，连续用 ICC）
② 报分歧清单（附每人的判定和理由）
③ 把分歧归类：
     · 定义模糊 → 补判定规则
     · 尺度不同 → 加锚点例子（每档 2 正例 2 反例）
```

**不要只报一个一致率数字，要报分歧模式。** 依据：James (2026), LREC 2026, doi:10.63317/2wuxteb6uvcj。

---

## 常见错误

| 错误 | 后果 |
|---|---|
| aspects 抽漏了一条 | B1 会报"没缺口"，但实际漏答了 |
| `blocks` 填了"提到"的位置而不是"回答"的位置 | B2 位置系统性偏早 |
| 同一批 case 用了两套落点规则 | 跨 case 不可比 |
| 用关键词命中当"覆盖"的证明 | 词出现 ≠ 诉求被回答 |
| A/B 用同一份 aspects | 两份回答的落点是不同的，必须分开填 |
