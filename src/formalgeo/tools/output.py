from sympy import Float
from formalgeo.parse import inverse_parse_one, inverse_parse_logic_to_cdl, inverse_parse_one_theorem
from graphviz import Digraph
import os
import random


def simple_show(problem, timing):
    """Show simple information about problem-solving."""
    pid = problem.parsed_problem_CDL["id"]
    correct_answer = str(problem.goal.answer).replace(" ", "")
    solved = problem.goal.solved
    solved_answer = problem.goal.solved_answer

    solved = "\033[32msolved\033[0m\t" if solved else "\033[31munsolved\033[0m\t"
    timing = "{:.6f}".format(timing) if timing < 2 else "\033[31m{:.6f}\033[0m".format(timing)
    print("{}\t{}\t{}\t{}\t{}".format(pid, str(correct_answer), solved, solved_answer, timing))


def show_solution(problem):
    """-----------Condition Declaration Statements-----------"""
    print("\033[36mproblem_index:\033[0m", end=" ")
    print(problem.parsed_problem_CDL["id"])
    print("\033[36mconstruction_cdl:\033[0m")
    for construction_fl in problem.parsed_problem_CDL["cdl"]["construction_cdl"]:
        print(construction_fl)
    print("\033[36mtext_cdl:\033[0m")
    for text_fl in problem.parsed_problem_CDL["cdl"]["text_cdl"]:
        print(text_fl)
    print("\033[36mimage_cdl:\033[0m")
    for image_fl in problem.parsed_problem_CDL["cdl"]["image_cdl"]:
        print(image_fl)
    print("\033[36mgoal_cdl:\033[0m")
    print(problem.parsed_problem_CDL["cdl"]["goal_cdl"])
    print()

    """-----------Process of Problem Solving-----------"""
    print("\033[36mreasoning:\033[0m")
    anti_parsed_cdl = inverse_parse_logic_to_cdl(problem)
    for step in anti_parsed_cdl:
        for cdl in anti_parsed_cdl[step]:
            print("{0:^3}{1:<20}".format(step, cdl))
    print()

    used_pid, used_step, _ = get_used(problem)

    """-----------Logic Form-----------"""
    print("\033[33mRelations:\033[0m")
    basic_predicates = list(problem.parsed_predicate_GDL["Preset"]["Construction"])
    basic_predicates += list(problem.parsed_predicate_GDL["Preset"]["BasicEntity"])
    predicates = list(problem.parsed_predicate_GDL["Entity"])
    predicates += list(problem.parsed_predicate_GDL["Relation"])
    for predicate in basic_predicates + predicates:
        items = problem.condition.get_items_by_predicate(predicate)
        if len(items) == 0:
            continue
        print(predicate + ":")

        if predicate in basic_predicates and len(items) > 20:
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
            theorem = inverse_parse_one_theorem(problem.condition.items[_id][3], problem.parsed_theorem_GDL)
            item = inverse_parse_one(predicate, item, problem, True)
            if len(item) > 35:
                item = item[0:35] + "..."
            if _id not in used_pid:
                print("{0:^6}{1:^50}{2:^25}{3:^6}".format(_id, item, premises, theorem))
            else:
                print("\033[35m{0:^6}{1:^50}{2:^25}{3:^6}\033[0m".format(_id, item, premises, theorem))
    print()

    print("\033[33mSymbols and Value:\033[0m")
    for attr in problem.condition.sym_of_attr:
        sym = problem.condition.sym_of_attr[attr]
        if isinstance(problem.condition.value_of_sym[sym], Float):
            print("{0:^70}{1:^15}{2:^20.3f}".format(
                "{}({})".format(attr[0], "".join(attr[1])), str(sym), problem.condition.value_of_sym[sym]))
        else:
            print("{0:^70}{1:^15}{2:^20}".format(
                "{}({})".format(attr[0], "".join(attr[1])), str(sym), str(problem.condition.value_of_sym[sym])))

    print("\033[33mEquations:\033[0m")
    items = problem.condition.get_items_by_predicate("Equation")
    for item in items:
        _id = problem.condition.get_id_by_predicate_and_item("Equation", item)
        if len(problem.condition.items[_id][2]) <= 3:
            premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2]]) + ")"
        else:
            premises = "(" + ",".join([str(i) for i in problem.condition.items[_id][2][0:3]]) + ",...)"
        theorem = inverse_parse_one_theorem(problem.condition.items[_id][3], problem.parsed_theorem_GDL)
        item = str(item).replace(" ", "")
        if len(item) > 40:
            item = item[0:40] + "..."
        if _id not in used_pid:
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
        print("theorem: {}".format(inverse_parse_one_theorem(problem.goal.theorem, problem.parsed_theorem_GDL)))
    print()

    print("\033[34mTiming:\033[0m")
    time_sum = 0
    for step in problem.timing:
        theorem = inverse_parse_one_theorem(problem.timing[step][0], problem.parsed_theorem_GDL)
        if step in used_step:
            print("\033[35m{:^2} {} {:.6f}s\033[0m".format(step, theorem, problem.timing[step][1]))
        else:
            print("{:^2} {} {:.6f}s".format(step, theorem, problem.timing[step][1]))
        time_sum += problem.timing[step][1]
    print("total: {:.6f}s".format(time_sum))


def get_used(problem):
    """Return used condition id, step and theorem for solved problem."""
    if not problem.goal.solved:
        return [], [], []

    skip_theorems = {("solve_eq", None, None), ("extended", None, None), ("prerequisite", None, None)}
    used_pid = set(problem.goal.premise)
    last_used_pid = set(problem.goal.premise)
    used_step = set()
    while True:
        for _id in last_used_pid:
            if _id >= 0:
                used_pid |= set(problem.condition.items[_id][2])
                if problem.condition.items[_id][3] not in skip_theorems:
                    used_step.add(problem.condition.items[_id][4])
        if last_used_pid == used_pid:
            break
        last_used_pid |= used_pid

    if problem.goal.type == "algebra":
        eq = problem.goal.item - problem.goal.answer
        if eq in problem.condition.get_items_by_predicate("Equation"):  # target in condition set
            _id = problem.condition.get_id_by_predicate_and_item("Equation", eq)
            if problem.condition.items[_id][3] not in skip_theorems:
                used_step |= {problem.condition.items[_id][4]}
    else:
        _id = problem.condition.get_id_by_predicate_and_item(problem.goal.item, problem.goal.answer)
        if problem.condition.items[_id][3] not in skip_theorems:
            used_step |= {problem.condition.items[_id][4]}

    used_theorems = []
    for step in problem.timing:
        theorem = inverse_parse_one_theorem(problem.timing[step][0], problem.parsed_theorem_GDL)
        if step in used_step:
            used_theorems.append(theorem)

    return used_pid, used_step, used_theorems


def get_meta_hypertree(problem):
    """
    Generate meta hypertree message for downstream task.
    :return nodes: all nodes, {node_id: node_name}, such as {1: "Equation(ll_ab-1)"}
    :return edges: all edges, {edge_id: edge_name}, such as {1: "extended"}
    :return free_nodes: nodes not in hypertree but in prerequisite, [node_id], such as [1, 2, 3]
    :return target_node_id: target node id, such as 1
    :return hypertree: {((tail_node_ids), edge_id): (tail_node_ids))}, such as {((1, 2, 3), 1): (4, 5))}
    """
    group = {}  # (premise, theorem): [_id], used for building hyper graph.
    cdl = {}  # _id: anti_parsed_cdl, user for getting cdl by id.
    init_nodes = []  # [_id], id of prerequisite.
    tree_nodes = []  # [_id], id of tree nodes.
    target_node_id = None

    for node_id in range(problem.condition.id_count):  # group conditions
        predicate, item, premise, theorem, _ = problem.condition.items[node_id]
        theorem = inverse_parse_one_theorem(theorem, problem.parsed_theorem_GDL)

        if (predicate in problem.parsed_predicate_GDL["Preset"]["Construction"] or
            predicate in problem.parsed_predicate_GDL["Preset"]["BasicEntity"]) and \
                theorem == "extended":
            continue  # skip construction cdl extending process

        cdl[node_id] = inverse_parse_one(predicate, item, problem)

        if theorem == "prerequisite":  # prerequisite not show in graph
            init_nodes.append(node_id)
            continue
        if (premise, theorem) not in group:
            group[(premise, theorem)] = [node_id]
        else:
            group[(premise, theorem)].append(node_id)

    if problem.goal.solved:
        if problem.goal.type == "algebra":
            eq = problem.goal.item - problem.goal.answer
            if eq not in problem.condition.get_items_by_predicate("Equation"):  # target not in condition set
                node_id = problem.condition.id_count
                cdl[node_id] = "Equation" + "(" + str(eq).replace(" ", "") + ")"
                theorem = inverse_parse_one_theorem(problem.goal.theorem, problem.parsed_theorem_GDL)
                group[(problem.goal.premise, theorem)] = [node_id]
                target_node_id = node_id
            else:
                target_node_id = problem.condition.get_id_by_predicate_and_item("Equation", eq)

        else:
            target_node_id = problem.condition.get_id_by_predicate_and_item(problem.goal.item, problem.goal.answer)

    edges = {-2: "none", -1: "self"}
    tree = {}
    for premise, theorem in group:  # make construction premise to prerequisite
        conclusion = group[(premise, theorem)]
        edge_id = len(edges)
        edges[edge_id] = theorem
        new_premise = []
        for node_id in premise:
            predicate, _, premise, theorem, _ = problem.condition.items[node_id]
            if (predicate in problem.parsed_predicate_GDL["Preset"]["Construction"] or
                    predicate in problem.parsed_predicate_GDL["Preset"]["BasicEntity"]):
                while theorem[0] != "prerequisite":
                    node_id = premise[0]
                    _, _, premise, theorem, _ = problem.condition.items[node_id]
            new_premise.append(node_id)
        tree_nodes += new_premise
        tree_nodes += conclusion
        tree[(tuple(set(new_premise)), edge_id)] = conclusion

    nodes = {}
    for node_id in sorted(list(set(tree_nodes + init_nodes))):
        nodes[node_id] = cdl[node_id]

    free_nodes = sorted(list(set(init_nodes) - set(tree_nodes)))

    return nodes, edges, free_nodes, target_node_id, tree


def get_solution_hypertree(problem):
    """Generate solution hyper tree."""
    nodes, edges, free_nodes, target_node_id, tree = get_meta_hypertree(problem)
    parsed_tree = {}
    for premise, theorem in tree:
        conditions = [nodes[node_id] for node_id in premise]
        conclusions = [nodes[node_id] for node_id in tree[(premise, theorem)]]
        theorem = edges[theorem]
        parsed_tree[len(parsed_tree) + 1] = {
            "conditions": conditions,
            "theorem": theorem,
            "conclusions": conclusions
        }

    hypertree = {
        "nodes": list(nodes.values()),
        "free_nodes": [nodes[node_id] for node_id in free_nodes],
        "target_node": nodes[target_node_id] if target_node_id is not None else "None",
        "tree": parsed_tree
    }
    return hypertree


def draw_solution_hypertree(problem, file_path_and_name):
    """Draw solution hyper tree and save as .png."""
    hypertree = get_solution_hypertree(problem)
    path, filename = os.path.split(file_path_and_name)
    filename = filename.split(".")[0]
    dot = Digraph(name=filename)

    for node in hypertree["nodes"]:
        dot.node(node, node)

    edges_count = 1
    for tree_id in hypertree["tree"]:
        dot.node(str(edges_count), hypertree["tree"][tree_id]["theorem"])
        for condition in hypertree["tree"][tree_id]["conditions"]:
            dot.edge(condition, str(edges_count))
        for conclusion in hypertree["tree"][tree_id]["conclusions"]:
            dot.edge(str(edges_count), conclusion)
        edges_count += 1

    dot.render(directory=path, view=False, format="png")  # save hyper graph
    if f"{filename}.png" in os.listdir(path):
        os.remove(f"{path}/{filename}.png")
    os.rename(f"{path}/{filename}.gv.png", f"{path}/{filename}.png")


def get_theorem_dag(problem):
    """Generate theorem DAG."""
    nodes, edges, free_nodes, target_node_id, tree = get_meta_hypertree(problem)

    rough_dag = {}
    for premise, theorem in tree:  # generate theorem dag
        if theorem not in rough_dag:
            rough_dag[theorem] = []

        for _id in tree[(premise, theorem)]:
            for tail_premise, tail_theorem in tree:
                if _id in tail_premise and tail_theorem not in rough_dag[theorem]:
                    rough_dag[theorem].append(tail_theorem)

    update = True
    while update:  # remove tail which contains 'extended' and 'solve_eq'
        update = False
        for head in rough_dag:
            for tail in list(rough_dag[head]):
                if edges[tail] not in ["extended", "solve_eq"]:
                    continue
                rough_dag[head].pop(rough_dag[head].index(tail))
                if tail not in rough_dag:
                    continue
                for new_tail in rough_dag[tail]:
                    rough_dag[head].append(new_tail)
                    update = True

    cleaned_dag = {}
    for head in rough_dag:  # remove head which contains 'extended' and 'solve_eq'
        if edges[head] in ["extended", "solve_eq"]:
            continue
        cleaned_dag[head] = []
        for tail in rough_dag[head]:
            cleaned_dag[head].append(tail)

    start_nodes = []
    for head in cleaned_dag:  # get START nodes
        is_start_node = True
        for check_head in cleaned_dag:
            if head in cleaned_dag[check_head]:
                is_start_node = False
                break
        if is_start_node:
            start_nodes.append(edges[head])

    dag = {"START": start_nodes}
    for head in cleaned_dag:
        if len(cleaned_dag[head]) == 0:
            continue
        inverse_adjust_head = edges[head]
        dag[inverse_adjust_head] = [edges[tail] for tail in cleaned_dag[head]]

    return dag


def draw_theorem_dag(problem, file_path_and_name):
    """Draw theorem DAG."""
    dag = get_theorem_dag(problem)
    path, filename = os.path.split(file_path_and_name)
    filename = filename.split(".")[0]
    dot = Digraph(name=filename)
    nodes = []  # list of theorem.

    for head in dag:
        if head not in nodes:
            nodes.append(head)
            dot.node(str(nodes.index(head)), head, shape='box')

        for tail in dag[head]:
            if tail not in nodes:
                nodes.append(tail)
                dot.node(str(nodes.index(tail)), tail, shape='box')

            dot.edge(str(nodes.index(head)), str(nodes.index(tail)))

    dot.render(directory=path, view=False, format="png")  # save theorem DAG
    if f"{filename}.png" in os.listdir(path):
        os.remove(f"{path}/{filename}.png")
    os.rename(f"{path}/{filename}.gv.png", f"{path}/{filename}.png")


def topological_sort(theorem_dag, random_seed=0):
    """Generate a theorem sequences according to the theorem DAG."""
    random.seed(random_seed)
    in_degree = {}
    for theorems in theorem_dag.values():
        for theorem in theorems:
            if theorem not in in_degree:
                in_degree[theorem] = 1
            else:
                in_degree[theorem] += 1

    for theorem in theorem_dag.keys():
        if theorem not in in_degree:
            in_degree[theorem] = 0

    theorem_seqs = []
    zero_in_degree = [theorem for theorem, degree in in_degree.items() if degree == 0]
    while len(zero_in_degree) > 0:
        theorem = random.choice(zero_in_degree)  # apply theorem and update state
        theorem_seqs.append(theorem)
        zero_in_degree.remove(theorem)

        if theorem in theorem_dag:
            for tail in theorem_dag[theorem]:
                in_degree[tail] -= 1
                if in_degree[tail] == 0:
                    zero_in_degree.append(tail)

    return theorem_seqs[1:]
