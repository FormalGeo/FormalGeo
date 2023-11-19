# Copyright (C) 2022-2023 FormalGeo Development Team
# Author: Xiaokai Zhang
# Contact: formalgeo@gmail.com

"""
'tools' provides some practical tools, such as problem-solving process outputting.
"""

__all__ = [
    "load_json", "save_json", "safe_save_json", "debug_print", "rough_equal", "get_user_input",
    "simple_show", "show_solution", "get_solution_step", "get_solution_hypertree", "get_theorem_dag",
    "get_used_pid_and_theorem"
]

from formalgeo.tools.utils import load_json, save_json, safe_save_json, debug_print, rough_equal, get_user_input
from formalgeo.tools.output import simple_show, show_solution, get_solution_step, get_solution_hypertree, get_theorem_dag
from formalgeo.tools.output import get_used_pid_and_theorem
