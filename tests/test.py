from formalgeo.data import DatasetLoader
from formalgeo.tools import load_json, save_json, get_used
from formalgeo.tools import draw_solution_hypertree, draw_theorem_dag
from formalgeo.tools import get_solution_hypertree, get_theorem_dag, show_solution
from formalgeo.solver import Interactor
from formalgeo.parse import parse_theorem_seqs, inverse_parse_solution, parse_one_theorem


def clean_theorem(problem_id):
    dl = DatasetLoader(dataset_name=dataset_name, datasets_path=datasets_path)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
    problem_cdl = dl.get_problem(pid=problem_id)

    solver.load_problem(problem_cdl)
    for t_name, t_branch, t_para in parse_theorem_seqs(problem_cdl["theorem_seqs"]):
        solver.apply_theorem(t_name, t_branch, t_para)

    solver.problem.check_goal()
    if solver.problem.goal.solved:
        _, _, theorem_seqs = get_used(solver.problem)
        theorem_seqs_dag = get_theorem_dag(solver.problem)
        problem_cdl["theorem_seqs"] = theorem_seqs
        problem_cdl["theorem_seqs_dag"] = theorem_seqs_dag
        save_json(problem_cdl, f"{data_path}/{problem_cdl['problem_id']}_cleaned.json")

        draw_solution_hypertree(solver.problem, data_path)

    show_solution(solver.problem)


def solve(problem_id):
    dl = DatasetLoader(dataset_name=dataset_name, datasets_path=datasets_path)
    solver = Interactor(dl.predicate_GDL, dl.theorem_GDL)
    problem_cdl = dl.get_problem(pid=problem_id)

    solver.load_problem(problem_cdl)
    for t_name, t_branch, t_para in parse_theorem_seqs(problem_cdl["theorem_seqs"]):
        solver.apply_theorem(t_name, t_branch, t_para)

    solver.problem.check_goal()
    if solver.problem.goal.solved:
        draw_solution_hypertree(solver.problem, f"{data_path}/{problem_id}_hypergraph.png")
        draw_theorem_dag(solver.problem, f"{data_path}/{problem_id}_dag.png")
        hypergraph_json = get_solution_hypertree(solver.problem)
        save_json(hypergraph_json, f"{data_path}/{problem_id}_hypergraph.json")
        theorem_dag_json = get_theorem_dag(solver.problem)
        save_json(theorem_dag_json, f"{data_path}/{problem_id}_dag.json")
        human_like_solution_cn = inverse_parse_solution(
            hypergraph_json,
            f"{datasets_path}/{dataset_name}/files/predicate_GDL-source.json",
            f"{datasets_path}/{dataset_name}/files/theorem_GDL-source.json",
            "cn"
        )
        with open(f"{data_path}/{problem_id}_human_like_solution_cn.txt", "w", encoding="utf-8") as f:
            f.write(human_like_solution_cn)
        human_like_solution_en = inverse_parse_solution(
            hypergraph_json,
            f"{datasets_path}/{dataset_name}/files/predicate_GDL-source.json",
            f"{datasets_path}/{dataset_name}/files/theorem_GDL-source.json",
            "en"
        )
        with open(f"{data_path}/{problem_id}_human_like_solution_en.txt", "w", encoding="utf-8") as f:
            f.write(human_like_solution_en)

    show_solution(solver.problem)


def get_solving_rate(hypertree, hypertree_gt):
    """
    hypertree: 未求解成功的问题的超树
    hypertree_gt: 我们标注的超树
    """
    sub_goals = [hypertree_gt.get_goal_node()]  # 需要得到的子目标，初始内容为目标节点
    theorem_needed = []  # 求解问题还需要的定理

    while len(sub_goals) > 0:
        child_goal_node = sub_goals.pop()  # 从栈里弹出一个需要求解的子目标

        # 基于标注的超树，获得求解当前子目标需要的子子目标和定理
        theorem, father_goal_nodes = hypertree_gt.get_father(child_goal_node)
        theorem.append(theorem_needed)

        for father_goal_node in father_goal_nodes:  # 遍历所有子子目标
            if father_goal_node not in hypertree:  # 如果当前子子目标未求解，加到sub_goals
                sub_goals.append(father_goal_node)

    # 最后计算 len(theorem_needed) / len(theorem_seqs)


datasets_path = "../../released"
data_path = "../outputs"
dataset_names = ["formalgeo7k_v1", "formalgeo7k_v2", "formalgeo-imo_v1", "formalgeo-test_v1"]
dataset_name = dataset_names[1]

if __name__ == '__main__':
    solve(6999)
