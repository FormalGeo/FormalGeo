# Copyright (C) 2022-2024 FormalGeo Development Team
# Author: Xiaokai Zhang
# Contact: formalgeo@gmail.com

"""
'core' responsible for GPL statements executing, which consists of 2 submodules.
'GeometryPredicateLogicExecutor' responsible for GPL statements parsing and relational inference.
'EquationKiller' responsible for symbolic and algebraic computation.
"""

__all__ = [
    "GeometryPredicateLogicExecutor", "EquationKiller"
]

from formalgeo.core.engine import GeometryPredicateLogicExecutor, EquationKiller
