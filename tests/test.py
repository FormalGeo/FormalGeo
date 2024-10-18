from formalgeo.solver import Interactor
from formalgeo.data import DatasetLoader
from formalgeo.parse import parse_theorem_seqs
from formalgeo.tools import show_solution

datasets_path = "../../released"
dataset_names = ["formalgeo7k_v1", "formalgeo7k_v2", "formalgeo-imo_v1", "formalgeo-test_v1"]
dataset_name = dataset_names[3]

dl = DatasetLoader(dataset_name=dataset_name, datasets_path=datasets_path)
solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
problem_CDL = dl.get_problem(pid=2)

solver.load_problem(problem_CDL)
for t_name, t_branch, t_para in parse_theorem_seqs(problem_CDL["theorem_seqs"]):
    solver.apply_theorem(t_name, t_branch, t_para)

solver.problem.check_goal()
show_solution(solver.problem)
