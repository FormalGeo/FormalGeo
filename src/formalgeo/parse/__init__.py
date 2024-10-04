# Copyright (C) 2022-2024 FormalGeo Development Team
# Author: Xiaokai Zhang
# Contact: formalgeo@gmail.com

"""
'parse' responsible for statements parsing and inverse parsing, building a bridge
between natural language, formal language, and machine language.
"""

__all__ = [
    "parse_expr", "get_expr_from_tree", "get_equation_from_tree",
    "parse_predicate_gdl", "parse_theorem_gdl", "parse_problem_cdl", "parse_theorem_seqs", "parse_one_theorem",
    "inverse_parse_one", "inverse_parse_logic_to_cdl", "inverse_parse_one_theorem",
    "inverse_parse_solution"
]

from formalgeo.parse.basic import parse_expr, get_expr_from_tree, get_equation_from_tree
from formalgeo.parse.parse_tgdl import parse_theorem_gdl
from formalgeo.parse.parse_pgdl import parse_predicate_gdl
from formalgeo.parse.parse_cdl import parse_problem_cdl, parse_theorem_seqs, parse_one_theorem
from formalgeo.parse.inverse_parse_m2f import inverse_parse_one, inverse_parse_logic_to_cdl, inverse_parse_one_theorem
from formalgeo.parse.inverse_parse_s2n import inverse_parse_solution
