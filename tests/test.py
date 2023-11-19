from formalgeo.solver import Interactor, ForwardSearcher, BackwardSearcher
from formalgeo.tools import load_json, save_json
from formalgeo.tools import show_solution
from formalgeo.parse import parse_theorem_seqs, inverse_parse_one_theorem
from formalgeo.tools import get_solution_step, get_solution_hypertree, get_theorem_dag, get_used_pid_and_theorem
from formalgeo.data import show_available_datasets, DatasetLoader
import random
import warnings


def test_interactor():
    solver = Interactor(load_json("gdl/predicate_GDL.json"),  # init method
                        load_json("gdl/theorem_GDL.json"))
    pid = 1
    problem_CDL = load_json("datasets/{}.json".format(pid))

    solver.load_problem(problem_CDL)

    for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
        solver.apply_theorem(t_name, t_branch, t_para)

    solver.problem.check_goal()  # check goal after applied theorem seqs

    show_solution(solver.problem)  # show solving process

    save_json(solver.parsed_predicate_GDL, "outputs/parsed_predicate_gdl.json")
    save_json(solver.parsed_theorem_GDL, "outputs/parsed_theorem_gdl.json")
    save_json(solver.problem.parsed_problem_CDL, "outputs/{}_parsed_problem_cdl.json".format(pid))
    save_json(get_solution_step(solver.problem), "outputs/{}_step.json".format(pid))
    save_json(get_solution_hypertree(solver.problem), "outputs/{}_hypertree.json".format(pid))
    save_json(get_theorem_dag(solver.problem), "outputs/{}_dag.json".format(pid))


def test_forward_searcher():
    random.seed(619)
    warnings.filterwarnings("ignore")
    searcher = ForwardSearcher(
        load_json("gdl/predicate_GDL.json"), load_json("gdl/theorem_GDL.json"),
        method="bfs", max_depth=15, beam_size=20,
        t_info=load_json("t_info.json"), debug=True
    )
    pid = 1
    searcher.init_search(load_json("datasets/{}.json".format(pid)))
    result = searcher.search()
    print("pid: {}, solved: {}, seqs:{}, step_count: {}.\n".format(pid, result[0], result[1], searcher.step_size))


def test_backward_searcher():
    random.seed(619)
    warnings.filterwarnings("ignore")
    searcher = BackwardSearcher(
        load_json("gdl/predicate_GDL.json"), load_json("gdl/theorem_GDL.json"),
        method="bfs", max_depth=15, beam_size=20,
        t_info=load_json("t_info.json"), debug=True
    )
    pid = 1
    searcher.init_search(load_json("datasets/{}.json".format(pid)))
    solved_result = searcher.search()
    print("pid: {}, solved: {}, seqs:{}, step_count: {}.\n".format(
        pid, solved_result[0], solved_result[1], searcher.step_size))


if __name__ == '__main__':
    # test_interactor()
    # test_forward_searcher()
    # test_backward_searcher()

    test_datasets_path = "F:/Datasets/released"
    # show_available_datasets(test_datasets_path)

    dl = DatasetLoader("formalgeo7k_v1", test_datasets_path)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)

    problem_CDL = dl.get_problem(94077)
    solver.load_problem(problem_CDL)
    for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
        solver.apply_theorem(t_name, t_branch, t_para)
    solver.problem.check_goal()  # check goal after applied theorem seqs

    _, theorem_seqs = get_used_pid_and_theorem(solver.problem)
    theorem_seqs = [inverse_parse_one_theorem(t, solver.parsed_theorem_GDL) for t in theorem_seqs]
    theorem_seqs_dag = get_theorem_dag(solver.problem)
    print(theorem_seqs)
    print(theorem_seqs_dag)
    # show_solution(solver.problem)  # show solving process
