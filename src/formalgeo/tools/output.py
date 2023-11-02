from sympy import Float
from formalgeo.parse import inverse_parse_one, inverse_parse_logic_to_cdl, inverse_parse_one_theorem


def show_solution(problem):
    """Show all information about problem-solving."""
    """-----------Conditional Declaration Statement-----------"""
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
    print("\033[36mreasoning_cdl:\033[0m")
    anti_parsed_cdl = inverse_parse_logic_to_cdl(problem)
    for step in anti_parsed_cdl:
        for cdl in anti_parsed_cdl[step]:
            print("{0:^3}{1:<20}".format(step, cdl))
    print()

    used_pid, used_theorem = get_used_pid_and_theorem(problem)

    """-----------Logic Form-----------"""
    print("\033[33mRelations:\033[0m")
    predicates = list(problem.parsed_predicate_GDL["Preset"]["Construction"])
    predicates += list(problem.parsed_predicate_GDL["Preset"]["BasicEntity"])
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
            if _id not in used_pid:
                print("{0:^6}{1:^50}{2:^25}{3:^6}".format(_id, item, premises, theorem))
            else:
                print("\033[35m{0:^6}{1:^50}{2:^25}{3:^6}\033[0m".format(_id, item, premises, theorem))

    predicates = list(problem.parsed_predicate_GDL["Entity"])
    predicates += list(problem.parsed_predicate_GDL["Relation"])
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


def get_solution_step(problem):
    """Get conditions grouped by step in dict."""
    step_msg = {
        "cdl": inverse_parse_logic_to_cdl(problem),
        "theorems_applied": {}
    }
    for step in problem.timing:
        if problem.timing[step][0] in ["init_problem", "check_goal"]:
            continue
        step_msg["theorems_applied"][str(step)] = problem.timing[step][0]

    return step_msg


def get_solution_tree(problem):
    """Generate and save solution hyper tree and theorem DAG."""
    group = {}  # (premise, theorem): [_id], used for building hyper graph.
    cdl = {}  # _id: anti_parsed_cdl, user for getting cdl by id.

    for _id in range(problem.condition.id_count):  # summary information
        predicate, item, premise, theorem, _ = problem.condition.items[_id]
        theorem = inverse_parse_one_theorem(theorem, problem.parsed_theorem_GDL)
        cdl[_id] = inverse_parse_one(predicate, item, problem)
        if theorem == "prerequisite":  # prerequisite not show in graph
            continue
        if (premise, theorem) not in group:
            group[(premise, theorem)] = [_id]
        else:
            group[(premise, theorem)].append(_id)

    if problem.goal.solved and problem.goal.type == "algebra":  # if target solved, add target
        eq = problem.goal.item - problem.goal.answer
        if eq not in problem.condition.get_items_by_predicate("Equation"):  # target not in condition set
            target_equation = inverse_parse_one("Equation", eq, problem)
            _id = len(cdl)
            cdl[_id] = target_equation
            group[(problem.goal.premise, problem.goal.theorem)] = [_id]

    solution_tree = {}
    for premise, theorem in group:  # generate solution tree
        start_nodes = [cdl[_id] for _id in premise]

        conclusion = group[(premise, theorem)]
        end_nodes = [cdl[_id] for _id in conclusion]

        solution_tree[len(solution_tree)] = {
            "conditions": start_nodes,
            "theorem": theorem,
            "conclusion": end_nodes
        }

    return solution_tree


def get_theorem_dag(problem):
    pass


def get_used_pid_and_theorem(problem):
    """Return used condition id and theorem for solving problem."""
    if not problem.goal.solved:
        return [], []

    used_pid = list(set(problem.goal.premise))
    used_theorem = []
    while True:
        len_used_pid = len(used_pid)
        for _id in used_pid:
            if _id >= 0:
                used_pid += list(problem.condition.items[_id][2])
                used_theorem.append(problem.condition.items[_id][3])
        used_pid = list(set(used_pid))  # 快速去重
        if len_used_pid == len(used_pid):
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

    return used_pid, selected_theorem
