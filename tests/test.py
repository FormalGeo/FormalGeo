from formalgeo.solver import Interactor, ForwardSearcher, BackwardSearcher
from formalgeo.tools import load_json, save_json
from formalgeo.tools import show_solution, draw_solution_tree_and_theorem_dag
from formalgeo.parse import parse_theorem_seqs, inverse_parse_one_theorem
from formalgeo.tools import get_solution_step, get_solution_hypertree, get_theorem_dag, get_used_pid_and_theorem
from formalgeo.data import DatasetLoader
import random
import warnings

if __name__ == '__main__':

    test_datasets_path = "F:/Datasets/released"
    # show_available_datasets(test_datasets_path)

    dl = DatasetLoader("formalgeo-imo_v1", test_datasets_path)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)

    problem_CDL = dl.get_problem(7)
    solver.load_problem(problem_CDL)
    for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
        solver.apply_theorem(t_name, t_branch, t_para)
    solver.problem.check_goal()  # check goal after applied theorem seqs

    save_json(get_solution_hypertree(solver.problem), "7_hypertree.json")
    save_json(get_theorem_dag(solver.problem), "7_dag.json")
    draw_solution_tree_and_theorem_dag(solver.problem, "./")
