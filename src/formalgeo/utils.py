import json
import os
from sympy import Float
from graphviz import Digraph, Graph
from formalgeo import InverseParserM2F


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def rough_equal(a, b):
    """Accuracy is controlled at 0.01"""
    return abs(a - b) < 0.01


def show(problem):
    """Show all information about problem-solving."""
    """-----------Conditional Declaration Statement-----------"""
    print("\033[36mproblem_index:\033[0m", end=" ")
    print(problem.problem_CDL["id"])
    print("\033[36mconstruction_cdl:\033[0m")
    for construction_fl in problem.problem_CDL["cdl"]["construction_cdl"]:
        print(construction_fl)
    print("\033[36mtext_cdl:\033[0m")
    for text_fl in problem.problem_CDL["cdl"]["text_cdl"]:
        print(text_fl)
    print("\033[36mimage_cdl:\033[0m")
    for image_fl in problem.problem_CDL["cdl"]["image_cdl"]:
        print(image_fl)
    print("\033[36mgoal_cdl:\033[0m")
    print(problem.problem_CDL["cdl"]["goal_cdl"])
    print()

    """-----------Process of Problem Solving-----------"""
    print("\033[36mreasoning_cdl:\033[0m")
    anti_parsed_cdl = InverseParserM2F.inverse_parse_logic_to_cdl(problem)
    for step in anti_parsed_cdl:
        for cdl in anti_parsed_cdl[step]:
            print("{0:^3}{1:<20}".format(step, cdl))
    print()

    used_id, used_theorem = get_used(problem)

    """-----------Logic Form-----------"""
    print("\033[33mRelations:\033[0m")
    predicates = list(problem.predicate_GDL["Construction"])
    predicates += list(problem.predicate_GDL["BasicEntity"])
    for predicate in predicates:
        items = problem.condition.get_items_by_predicate(predicate)
        if len(items) == 0:
            continue
        print(predicate + ":")

        if len(items) > 20:
            items = items[0:10] + ["..."] + items[len(items) - 10:]

        for item in items:
            if isinstance(item, str):
                print(item)
                continue
            _id = problem.condition.get_id_by_predicate_and_item(predicate, item)
            if len(problem.condition.items[_id][2]) <= 3:
                premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2]]) + ")"
            else:
                premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2][0:3]]) + ",...)"
            theorem = problem.condition.items[_id][3]
            item = ",".join(item)
            if len(item) > 35:
                item = item[0:35] + "..."
            if _id not in used_id:
                print("{0:^6}{1:^50}{2:^25}{3:^6}".format(_id, item, premises, theorem))
            else:
                print("\033[35m{0:^6}{1:^50}{2:^25}{3:^6}\033[0m".format(_id, item, premises, theorem))

    predicates = list(problem.predicate_GDL["Entity"])
    predicates += list(problem.predicate_GDL["Relation"])
    for predicate in predicates:
        items = problem.condition.get_items_by_predicate(predicate)
        if len(items) == 0:
            continue
        print(predicate + ":")

        for item in items:
            _id = problem.condition.get_id_by_predicate_and_item(predicate, item)
            if len(problem.condition.items[_id][2]) <= 3:
                premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2]]) + ")"
            else:
                premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2][0:3]]) + ",...)"
            theorem = problem.condition.items[_id][3]
            item = ",".join(item)
            if len(item) > 35:
                item = item[0:35] + "..."
            if _id not in used_id:
                print("{0:^6}{1:^50}{2:^25}{3:^6}".format(_id, item, premises, theorem))
            else:
                print("\033[35m{0:^6}{1:^50}{2:^25}{3:^6}\033[0m".format(_id, item, premises, theorem))
    print()

    print("\033[33mSymbols and Value:\033[0m")
    for attr in problem.condition.sym_of_attr:
        sym = problem.condition.sym_of_attr[attr]
        if isinstance(problem.condition.value_of_sym[sym], Float):
            print("{0:^70}{1:^15}{2:^20.3f}".format(
                str(("".join(attr[0]), attr[1])), str(sym), problem.condition.value_of_sym[sym]))
        else:
            print("{0:^70}{1:^15}{2:^20}".format(
                str(("".join(attr[0]), attr[1])), str(sym), str(problem.condition.value_of_sym[sym])))

    print("\033[33mEquations:\033[0m")
    items = problem.condition.get_items_by_predicate("Equation")
    for item in items:
        _id = problem.condition.get_id_by_predicate_and_item("Equation", item)
        if len(problem.condition.items[_id][2]) <= 3:
            premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2]]) + ")"
        else:
            premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2][0:3]]) + ",...)"
        theorem = problem.condition.items[_id][3]
        item = str(item).replace(" ", "")
        if len(item) > 40:
            item = item[0:40] + "..."

        if _id not in used_id:
            print("{0:^6}{1:^60}{2:^25}{3:>6}".format(_id, item, premises, theorem))
        else:
            print("\033[35m{0:^6}{1:^60}{2:^25}{3:>6}\033[0m".format(_id, item, premises, theorem))
    print()

    # goal
    print("\033[34mSolving Goal:\033[0m")
    print("type: {}".format(problem.goal.type))
    print("goal: {}".format(str(problem.goal.item).replace(" ", "")))
    print("answer: {}".format(str(problem.goal.answer).replace(" ", "")))
    if problem.goal.solved:
        print("solved: \033[32mTrue\033[0m")
    else:
        print("solved: \033[31mFalse\033[0m")
    if problem.goal.solved_answer is not None:
        print("solved_answer: {}".format(str(problem.goal.solved_answer)))
        if not isinstance(problem.goal.solved_answer, tuple):
            try:
                print("solved_answer(float): {}".format(float(problem.goal.solved_answer)))
            except TypeError:
                print("solved_answer(float): <Cannot convert to float>")
    if problem.goal.premise is not None:
        print("premise: {}".format(str(problem.goal.premise)))
        print("theorem: {}".format(problem.goal.theorem))
    print()

    print("\033[34mTiming:\033[0m")
    time_sum = 0
    for step in problem.timing:
        if problem.timing[step][0] in used_theorem:
            print("\033[35m{:^2} {} {:.6f}s\033[0m".format(step, problem.timing[step][0], problem.timing[step][1]))
        else:
            print("{:^2} {} {:.6f}s".format(step, problem.timing[step][0], problem.timing[step][1]))
        time_sum += problem.timing[step][1]
    print("total: {:.6f}s\n".format(time_sum))


def save_solution_tree(problem, path, save_hyper, save_hyper_pic, save_dag, save_dag_pic):
    if not (save_hyper or save_hyper_pic or save_dag or save_dag_pic):
        return
    """Generate and save solution hyper tree and theorem DAG."""
    st_dot = Digraph(name=str(problem.problem_CDL["id"]))  # Tree
    nodes = []  # list of node(cdl or theorem).
    t_nodes = []  # theorem nodes, used for DAG generating.
    edges = {}  # node(cdl or theorem): [node(cdl or theorem)], used for DAG generating.
    group = {}  # (premise, theorem): [_id], used for building hyper graph.
    cdl = {}  # _id: anti_parsed_cdl, user for getting cdl by id.

    for _id in range(problem.condition.id_count):  # summary information
        predicate, item, premise, theorem, _ = problem.condition.items[_id]
        cdl[_id] = InverseParserM2F.inverse_parse_one(predicate, item, problem)
        if theorem == "prerequisite":  # prerequisite not show in graph
            continue
        if (premise, theorem) not in group:
            group[(premise, theorem)] = [_id]
        else:
            group[(premise, theorem)].append(_id)

    used_id, _ = get_used(problem)  # just keep useful solution msg
    if problem.goal.solved:  # if target solved, add target
        if problem.goal.type == "algebra":
            eq = problem.goal.item - problem.goal.answer
            if eq not in problem.condition.get_items_by_predicate("Equation"):  # target not in condition set
                target_equation = InverseParserM2F.inverse_parse_one("Equation", eq, problem)
                _id = len(cdl)
                cdl[_id] = target_equation
                group[(problem.goal.premise, problem.goal.theorem)] = [_id]
                used_id.append(_id)
            else:
                used_id.append(problem.condition.get_id_by_predicate_and_item("Equation", eq))
        else:
            used_id.append(problem.condition.get_id_by_predicate_and_item(problem.goal.item, problem.goal.answer))
        used_id += list(problem.goal.premise)

    remove_list = []
    for key in group:
        premise = key[0]
        not_used_in_premise = True
        l = 0
        while not_used_in_premise and l < len(premise):
            if premise[l] in used_id:
                not_used_in_premise = False
                break
            l += 1

        conclusion = group[key]
        not_used_in_conclusion = True
        l = 0
        while not_used_in_conclusion and l < len(conclusion):
            if conclusion[l] in used_id:
                not_used_in_conclusion = False
                break
            l += 1

        if not_used_in_premise or not_used_in_conclusion:
            remove_list.append(key)

    for key in remove_list:
        group.pop(key)

    count = 0
    solution_tree = {}
    for key in group:  # generate solution tree
        premise, theorem = key
        conclusion = group[key]

        theorem_node = theorem + "_{}".format(count)  # theorem name in hyper
        t_nodes.append(theorem_node)
        _add_node(st_dot, nodes, theorem_node)

        start_nodes = []
        for _id in premise:
            if _id not in used_id:
                continue
            _add_node(st_dot, nodes, cdl[_id])  # add node to graph
            start_nodes.append(cdl[_id])  # add to json output
            _add_edge(st_dot, nodes, cdl[_id], theorem_node, edges)  # add edge to graph

        end_nodes = []
        for _id in conclusion:
            if _id not in used_id:
                continue
            _add_node(st_dot, nodes, cdl[_id])  # add node to graph
            end_nodes.append(cdl[_id])  # add to json output
            _add_edge(st_dot, nodes, theorem_node, cdl[_id], edges)  # add edge to graph

        solution_tree[count] = {
            "conditions": start_nodes,
            "theorem": theorem,
            "conclusion": end_nodes
        }
        count += 1

    if save_hyper:
        save_json(solution_tree, path + "{}_hyper.json".format(problem.problem_CDL["id"]))  # save solution tree
    if save_hyper_pic:
        st_dot.render(directory=path, view=False, format="png")  # save hyper graph
        os.remove(path + "{}.gv".format(problem.problem_CDL["id"]))
        try:
            os.remove(path + "{}_hyper.png".format(problem.problem_CDL["id"]))
        except NotImplementedError as e:
            pass
        os.rename(path + "{}.gv.png".format(problem.problem_CDL["id"]),
                  path + "{}_hyper.png".format(problem.problem_CDL["id"]))

    if not (save_dag or save_dag_pic):
        return

    dag_dot = Digraph(name=str(problem.problem_CDL["id"]))  # generate theorem DAG
    nodes = []  # list of theorem.
    dag = {}

    for s_node in edges:  # select theorem nodes
        if s_node not in t_nodes:
            continue
        dag[s_node] = []
        for m_node in edges[s_node]:  # middle condition
            if m_node not in edges:
                continue
            for e_node in edges[m_node]:
                dag[s_node].append(e_node)

    update = True
    while update:  # remove tail which contains 'extended' and 'solve_eq'
        update = False
        for head in dag:
            for tail in list(dag[head]):
                if not (tail.startswith("extended") or tail.startswith("solve_eq")):
                    continue
                dag[head].pop(dag[head].index(tail))
                if tail not in dag:
                    continue
                for new_tail in dag[tail]:
                    dag[head].append(new_tail)
                    update = True

    cleaned = {}
    for key in dag:  # remove head which contains 'extended' and 'solve_eq'
        if key.startswith("extended") or key.startswith("solve_eq"):
            continue
        new_key = key.split(")")[0] + ")"  # remove number
        cleaned[new_key] = []
        for tail in dag[key]:
            cleaned[new_key].append(tail.split(")")[0] + ")")
    dag = cleaned

    root_nodes = []
    child_nodes = []
    real_root_nodes = []
    real_child_nodes = []
    for head in dag:  # build DAG graph
        _add_node(dag_dot, nodes, head)
        root_nodes.append(head)
        if len(dag[head]) == 0:
            real_child_nodes.append(head)
            continue
        for tail in set(dag[head]):
            _add_node(dag_dot, nodes, tail)
            _add_edge(dag_dot, nodes, head, tail)
            child_nodes.append(tail)

    _add_node(dag_dot, nodes, "START")  # add START node
    for root in root_nodes:
        if root in child_nodes:
            continue
        real_root_nodes.append(root)
        _add_node(dag_dot, nodes, root)
        _add_edge(dag_dot, nodes, "START", root)
    dag["START"] = real_root_nodes

    for head in list(dag.keys()):  # remove leaf node
        if len(dag[head]) == 0:
            dag.pop(head)

    if save_dag:
        save_json(dag, path + "{}_dag.json".format(problem.problem_CDL["id"]))  # save solution tree
    if save_dag_pic:
        dag_dot.render(directory=path, view=False, format="png")  # save hyper graph
        os.remove(path + "{}.gv".format(problem.problem_CDL["id"]))
        try:
            os.remove(path + "{}_dag.png".format(problem.problem_CDL["id"]))
        except NotImplementedError as e:
            pass
        os.rename(path + "{}.gv.png".format(problem.problem_CDL["id"]),
                  path + "{}_dag.png".format(problem.problem_CDL["id"]))


def _add_node(dot, nodes, node):
    if node in nodes:  # node was already added
        return

    added_node_id = len(nodes)
    nodes.append(node)
    if node[0].isupper():
        dot.node(str(added_node_id), node, shape='box')  # condition node
    else:
        dot.node(str(added_node_id), node)  # theorem node


def _add_edge(dot, nodes, start_node, end_node, edges=None):
    dot.edge(str(nodes.index(start_node)), str(nodes.index(end_node)))
    if edges is not None:
        if start_node not in edges:
            edges[start_node] = [end_node]
        else:
            edges[start_node].append(end_node)


def save_step_msg(problem, path):
    """Save conditions grouped by step in dict."""
    step_msg = {
        "cdl_inverse_parsed": InverseParserM2F.inverse_parse_logic_to_cdl(problem),
        "theorems_applied": {}
    }
    for step in problem.timing:
        if problem.timing[step][0] in ["init_problem", "check_goal"]:
            continue
        step_msg["theorems_applied"][str(step)] = problem.timing[step][0]

    save_json(
        step_msg,
        path + "{}_step.json".format(problem.problem_CDL["id"])
    )


def get_used(problem):
    """Return used condition id and theorem for solving problem."""
    if not problem.goal.solved:
        return [], []

    used_id = list(set(problem.goal.premise))
    used_theorem = []
    while True:
        len_used_id = len(used_id)
        for _id in used_id:
            if _id >= 0:
                used_id += list(problem.condition.items[_id][2])
                used_theorem.append(problem.condition.items[_id][3])
        used_id = list(set(used_id))  # 快速去重
        if len_used_id == len(used_id):
            break

    selected_theorem = []
    for step in problem.timing:  # ensure ordered theorem seqs list
        if problem.timing[step][0] in used_theorem and \
                problem.timing[step][0] not in selected_theorem and \
                problem.timing[step][0] not in ["solve_eq", "extended", "prerequisite"]:
            selected_theorem.append(problem.timing[step][0])
    if problem.goal.theorem not in ["solve_eq", "extended", "prerequisite"] and \
            problem.goal.theorem not in selected_theorem:
        selected_theorem.append(problem.goal.theorem)

    return used_id, selected_theorem
