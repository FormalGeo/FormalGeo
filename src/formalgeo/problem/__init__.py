# Copyright (C) 2022-2023 SHU Geometric Cognitive Reasoning Group
# Author: Xiaokai Zhang
# Contact: xiaokaizhang1999@163.com

"""
'Problem' preserves all details of the problem-solving process, ensures the correctness and
consistency of the problem input conditions, and implements automatic diagram construction,
condition auto-expansion, and validity checks.
"""

__all__ = [
    "Problem"
]

from formalgeo.problem.problem import Problem