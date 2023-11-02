# Copyright (C) 2022-2023 SHU Geometric Cognitive Reasoning Group
# Author: Xiaokai Zhang
# Contact: xiaokaizhang1999@163.com

"""
'core' responsible for GPL statements executing, which consists of 2 submodules.
'GeometryPredicateLogicExecutor' responsible for GPL statements parsing and relational inference.
'EquationKiller' responsible for symbolic and algebraic computation.
"""

__all__ = [
    "GeometryPredicateLogicExecutor", "EquationKiller"
]

from formalgeo.core.engine import GeometryPredicateLogicExecutor, EquationKiller
