# Copyright (C) 2022-2023 SHU Geometric Cognitive Reasoning Group
# Author: Xiaokai Zhang
# Contact: xiaokaizhang1999@163.com

"""
'solver' invokes other modules to enable interactive problem-solving and automated problem-solving.
The automated problem-solving implements both forward search and backward search, allowing for the
configuration of various search strategies (breadth-first, depth-first, random, beam).
"""

__all__ = [
    "Interactor", "ForwardSearcher", "BackwardSearcher"
]

from formalgeo.solver.interactive import Interactor
from formalgeo.solver.forward_search import ForwardSearcher
from formalgeo.solver.backward_search import BackwardSearcher