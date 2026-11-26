# -*- coding: utf-8 -*-
"""plain-language-eval —— 回答的信息组织评测

十一项（措辞 3 + 信息组织 8）：
    B1 有没有（覆盖）        评估
    B2 在哪（定位）          基线
    B3 散不散（集中）        基线
    B4 层级（结构形态）      基线
    B5 状态 vs 推理          评估
    B6 有没有废话            观察（不计分）
    B7 指代清不清            评估
    B8 数量自述对不对        评估（零争议）

用法：
    from plaineval import run_case
    result = run_case("cases/demo")
"""
from .core import LAYER, ROLE, compare, evaluate, evaluate_pair, load_case, run_case

__version__ = "0.1.0"
__all__ = ["evaluate", "evaluate_pair", "compare", "load_case", "run_case", "ROLE", "LAYER"]
