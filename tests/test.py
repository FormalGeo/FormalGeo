from formalgeo.solver import Interactor
from formalgeo.tools import load_json, save_json
from formalgeo.tools import show_solution
from formalgeo.parse import parse_theorem_seqs
from formalgeo.tools import get_solution_step, get_solution_tree


def test_interactor():
    solver = Interactor(load_json("predicate_GDL.json"),  # init method
                        load_json("theorem_GDL.json"))
    while True:
        try:
            pid = input("pid:")
            filename = "{}.json".format(pid)
            problem_CDL = load_json(filename)
        except BaseException as e:
            print(repr(e) + "\n")
            continue

        solver.load_problem(problem_CDL)

        for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
            solver.apply_theorem(t_name, t_branch, t_para)

        solver.problem.check_goal()  # check goal after applied theorem seqs

        save_json(get_solution_step(solver.problem), "{}_step.json".format(pid))
        save_json(get_solution_tree(solver.problem)[0], "{}_tree.json".format(pid))
        save_json(get_solution_tree(solver.problem)[1], "{}_dag.json".format(pid))

        show_solution(solver.problem)  # show solving process


def test_forward_searcher():
    pass


def test_backward_searcher():
    pass
