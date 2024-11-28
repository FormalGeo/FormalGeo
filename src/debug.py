# Simple implementation of the formalgeo solver for test and debug
# copied from formalgeo7k/debug.py

import os
from formalgeo.solver import Interactor
from formalgeo.tools import load_json, save_json, show_solution, get_used
from formalgeo.parse import parse_theorem_seqs, parse_one_theorem


def run(clean_theorem=False, interactive=False):
    # Init solver with predicate and theorem GDL files in /gdl folder
    solver = Interactor(
        load_json(os.path.join("../gdl/", "predicate_GDL.json")),
        load_json(os.path.join("../gdl/", "theorem_GDL.json")),
    )

    # Looping for input pid and solve the problem
    while True:
        try:
            # Only test 20 for now
            pid = input("pid:")
            filename = "{}.json".format(pid)
            problem_CDL = load_json(os.path.join("../problems/", filename))
        except BaseException as e:
            print(repr(e) + "\n")
            continue

        # Load problem
        solver.load_problem(problem_CDL)

        # Apply theorem seqs
        for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
            solver.apply_theorem(t_name, t_branch, t_para)

        # After applying theorem seqs, check goal and show solving process
        solver.problem.check_goal()  # check goal after applied theorem seqs
        show_solution(solver.problem)  # show solving process
        print()

        if interactive:
            # Interactive mode, input theorem name, branch and parameters
            while not solver.problem.goal.solved:
                try:
                    t_name, t_branch, t_para = parse_one_theorem(
                        input("input theorem:")
                    )
                    solver.apply_theorem(t_name, t_branch, t_para)
                    solver.problem.check_goal()  # check goal after applied theorem seqs
                    show_solution(solver.problem)  # show solving process
                    print()
                except BaseException as e:
                    print(repr(e) + "\n")
                    continue

        if clean_theorem and solver.problem.goal.solved:
            # _, theorem_seqs = get_used_pid_and_theorem(
            #     solver.problem
            # )  # clean theorem seqs
            _, theorem_seqs = get_used(solver.problem)  # clean theorem seqs
            problem_CDL["theorem_seqs"] = theorem_seqs
            save_json(problem_CDL, os.path.join("../problems/", filename))


if __name__ == "__main__":
    run()
