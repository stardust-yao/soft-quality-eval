# 文献与自研清单

> **这一页必须跟着任何报告一起走。** 换人接手时，看到这张表就知道哪些能引文献、哪些只是工程适配。
> **把自研部分写成"参照某标准"，是这类工作最容易犯的错。**

---

## 一、有文献依据的

| 结论 | 出处 | 读到什么程度 |
|---|---|---|
| 位置是篇章连贯的一部分；BLEU/ROUGE/BertScore 抓不到；用位置箱 + 篇章角色分布 + KL 散度 | Liu, Su, Shareghi, Collier (2024). *PDD: Positional Discourse Coherence*. NAACL 2024. doi:10.18653/v1/2024.naacl-short.9 | ✅ 全文 |
| 局部连贯 = 实体语法角色（S/O/X/–）的转移序列；CONTINUE（共享实体）优于 SHIFT（切换实体） | Barzilay & Lapata (2008). *Modeling Local Coherence: An Entity-Based Approach*. Computational Linguistics 34(1). doi:10.1162/coli.2008.34.1.1 | ✅ 全文（861 引用） |
| 话语 = 连续提问与回答；已把 QUD 的理论约束做成具体协议 | Wu, Mangla, Durrett, Li (2023). *QUDeval*. EMNLP 2023. doi:10.18653/v1/2023.emnlp-main.325 | ✅ 摘要 |
| 长文本生成可用原子断言与期望 aspects 的对齐来测覆盖；aspects 是外部给定的 | Samarinas et al. (2025). *Beyond Factual Accuracy: Evaluating Coverage of Diverse Factual Information in Long-form Text Generation*. Findings of ACL 2025. doi:10.18653/v1/2025.findings-acl.693 | ✅ 摘要 |
| 中文 Coh-Metrix 不存在（"still underdeveloped and unavailable online"），中文衔接改用 CTAP；指标含 LNO/LAO/GNO/GAO/连词/因果连词/LSA | Zhang, Zhou, Li, Xu (2026). *Writing creativity, cohesion, and formal linguistic competence in LLMs*. PLoS ONE. doi:10.1371/journal.pone.0335185 | ✅ 全文方法段 |
| 指代评测应按语义类别诊断，不报单一总分 | Gatti, Martinelli, Navigli (2026). *Interpretable Coreference Resolution Evaluation Using Explicit Semantics*. ACL 2026. doi:10.18653/v1/2026.acl-long.2126 | ✅ 摘要 |
| 逐句意义保真判定需要 sanity check：相同句=100%、无关句=0% | Beauchemin et al. (2025). *JUDGEBERT*. EMNLP 2025. doi:10.18653/v1/2025.emnlp-main.5 | ✅ 摘要 |
| 冗余在学术写作中至今没有统一定义与分类 | Тихонова et al. (2024). *Text Redundancy in Academic Writing: A Scoping Review*. doi:10.17323/jle.2024.23747 | ✅ 摘要 |
| IAA 应按任务类型选指标，报置信区间，并分析分歧模式；标签不平衡与缺失数据会影响信度估计 | James (2026). *Counting on Consensus: Selecting the Right Inter-Annotator Agreement Metric*. LREC 2026. doi:10.63317/2wuxteb6uvcj | ✅ 摘要 |
| 手工 rubric + 逐题判定 + 离散标签是正规做法；人类评委之间也不完全一致 | Hashemi, Eisner, Rosset, Van Durme (2024). *LLM-Rubric*. ACL 2024. doi:10.18653/v1/2024.acl-long.745 | ✅ 摘要（298 引用） |
| 用标题检测做主题切分 | TSHD (2023). doi:10.1155/2023/6044007 | 📇 仅核元数据 |
| 同主题词跨段落分布可作为连贯性的代理 | *Paragraph boundaries and discourse genre: Applying Lexical Priming*. (2024). doi:10.5209/clac.96954 | 📇 仅核元数据 |
| 倒金字塔（最重要先说）作为新闻写作实践 | *Revisiting the Inverted Pyramid in Online News* (2025) | 📇 仅核元数据 |
| 用 QUD 框架量化话语推进，可检测 LLM 的结构复用 | *QUDsim: Quantifying Discourse Similarities in LLM-Generated Text* (2025). arXiv:2504.09373 | ✅ 摘要 |
| 用蕴含（entailment）判断内容是否已被覆盖 | *OpineSum* (Findings of ACL 2023). doi:10.18653/v1/2023.findings-acl.686 | 📇 仅核元数据 |

**读到程度的标记**：✅ 全文/摘要已读 · 📇 仅核元数据 · ⚪ 通用知识未核原文


---

## 一之二、措辞层（A）的依据

| 结论 | 出处 | 读到什么程度 |
|---|---|---|
| 七个经典可读性公式（Flesch / Dale-Chall / SMOG 等）**全部含"平均句长"**；但同文指出「以这些语言特征预测文本可读性，并没有强而有力的证据」 | ROCLING 2015（中文可读性公式综述） | ✅ 全文表一 |
| 衔接指标可测：LNO/LAO/GNO/GAO/连词/因果连词/LSA；中文侧用 CTAP | Coh-Metrix (2004). *Analysis of text on cohesion and language*. Behavior Research Methods. doi:10.3758/bf03195564（1997 引用） | ✅ 摘要 |
| CTAP 提供平均/最大依存距离、句法树高度等句法复杂度指标 | CTAP (LREC 2022) | 📇 仅核元数据 |
| 中文版 Coh-Metrix 不存在（"still underdeveloped and unavailable online"） | Zhang et al. (2026). PLoS ONE. doi:10.1371/journal.pone.0335185 | ✅ 全文 |
| MSTTR（Mean Segmental TTR）：按固定窗口切段、段内算 TTR 再取均值，用于消除文本长度对 TTR 的影响 | 词汇多样性经典方法（Malvern et al.） | ⚪ 通用知识未核原文 |
| 中文可读性工具有 CRIE 等在线平台 | CRIE（chinesereadability.net），需账号；原 Demo 为 Flash 已不可用 | ✅ 实测访问 |
| LLM 中文文本的"AI 味"特征清单（31 项） | Humanizer-zh 项目（社区实践） | ✅ 代码与规则 |

### 措辞层里明确没有依据的

| 项 | 状态 |
|---|---|
| **A2 的 K 值（每个未解释概念扣几分）** | 🔴 **无原型**。K=10 只是占位值 |
| A2 的封顶 / 合格线 | 🔴 无原型 |
| A2「绝对数扣分」的口径 | 🟡 逻辑上成立（按概念去重），但无文献直接支持 |
| A3 的"只测不判"处理 | 🟡 依据是 ROCLING 2015 自己说表层特征证据不足——**这句是文献说的，处理方式是我们定的** |
| 词频熵 H 与篇幅 ρ≈0.95 | ✅ 本项目实测（Case1 两组） |

---

## 二、自己设计的（不能引文献）

| 部分 | 说明 |
|---|---|
| **位置百分比指标**（核心答案首现位置、各诉求首现位置） | 思想取自 PDD 的「位置箱」，但单篇版本的形式是本项目设计的。PDD 原式需要金标参考答案，评不了单篇 |
| **QUD 三档判定**（完整状态 / 半状态+推理 / 纯元话语） | 依据 QUDeval 的框架，但三档划分是本项目设计的 |
| **Entity Grid 的位置启发式 S/O/X 指派** | 原文用依存句法分析；本实现用「句首第一个名词=S、动词后第一个名词=O」近似 |
| **共指规则**（该X / 它 / 前一份 / 前者 → 绑定先行词） | 无文献出处，覆盖率低（实测成功 4 / 未解析 5） |
| **数量自述检查** | 无文献原型，纯计数 |
| **A2 的 K 值与扣分口径** | 无文献原型；K=10 是占位值，未定 |
| **A3 的近似 T-unit（连词规则）** | 中文无现成 T-unit 库，连词表的选择是本项目定的 |
| **表格区识别规则**（周期形状一致 ≥4 次） | 无文献原型。工程需要，实测有效但换格式可能失效 |
| **「需读者自己配对」这一档**（B7） | 无文献出处，是从实例里归纳的 |

---

## 三、明确没做的

| 没做 | 原因 |
|---|---|
| PDD 原式（KL 散度） | 需要参考文，评不了单篇 |
| Cob-Metrix 原工具 | 中文版不存在（见 PLoS ONE 2026 原文） |
| 中文 T-unit 标准切分 | 没有现成库（LTP/HanLP/stanza 只给依存树），只能用连词规则近似 |
| RST 修辞结构树 | 中文 discourse parser 效果不够，且这一版不需要 |
| 真共指消解 | 需要 coref 模型，成本高；B3 的纯词面版已能分出方向 |
| LSA 原语义空间 | 本地 TF-IDF + SVD 复现不了预训练语义空间 |

---

## 四、几条方法论原则（来自这些文献）

1. **先暴露问题，再定分数刻度。** 阈值要等数据积累，不能先定权重再算分。
2. **进扣分项必须零争议**——换个人看同一处，必须给出相同判定。
3. **报分歧模式，不只报一致率。** 分歧集中在哪类句子，说明定义哪里模糊。
4. **人类评委之间也不完全一致**，所以一致率数据是标配，不是补丁。
5. **均值会掩盖分布。** 同一批文本，连续值指标和二元值指标可以给出相反方向。
