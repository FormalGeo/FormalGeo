from sympy import Float
from formalgeo.parse import inverse_parse_one, inverse_parse_logic_to_cdl, inverse_parse_one_theorem


def simple_show(pid, correct_answer, solved, solved_answer, timing):
    """Show simple information about problem-solving."""
    solved = "\033[32m1\033[0m\t" if solved else "\033[31m0\033[0m\t"
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

    used_pid, used_theorem = get_used_pid_and_theorem(problem)

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
        if problem.timing[step][0] in used_theorem:
            theorem = inverse_parse_one_theorem(problem.timing[step][0], problem.parsed_theorem_GDL)
            print("\033[35m{:^2} {} {:.6f}s\033[0m".format(step, theorem, problem.timing[step][1]))
        else:
            print("{:^2} {} {:.6f}s".format(step, problem.timing[step][0], problem.timing[step][1]))
        time_sum += problem.timing[step][1]
    print("total: {:.6f}s".format(time_sum))


def get_solution_step(problem):
    """Get conditions grouped by step in dict."""
    step_msg = {
        "cdl": inverse_parse_logic_to_cdl(problem),
        "theorems_applied": {}
    }
    for step in problem.timing:
        if isinstance(problem.timing[step][0], tuple):
            step_msg["theorems_applied"][str(step)] = inverse_parse_one_theorem(
                problem.timing[step][0], problem.parsed_theorem_GDL)

    return step_msg


def get_solution_hypertree(problem):
    """Generate solution hyper tree and theorem DAG."""
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

    solution_hypertree = {}
    for premise, theorem in group:  # generate solution tree
        start_nodes = [cdl[_id] for _id in premise]

        conclusion = group[(premise, theorem)]
        end_nodes = [cdl[_id] for _id in conclusion]

        solution_hypertree[len(solution_hypertree)] = {
            "conditions": start_nodes,
            "theorem": theorem,
            "conclusion": end_nodes
        }

    return solution_hypertree


def get_theorem_dag(problem):
    """Generate theorem DAG."""
    group = {}  # (premise, theorem): [_id], used for building theorem DAG.
    for _id in range(problem.condition.id_count):  # summary information
        predicate, item, premise, theorem, _ = problem.condition.items[_id]
        if theorem[0] == "prerequisite":  # prerequisite not show in graph
            continue
        if (premise, theorem) not in group:
            group[(premise, theorem)] = [_id]
        else:
            group[(premise, theorem)].append(_id)
    if problem.goal.solved and problem.goal.type == "algebra":  # if target solved, add target
        eq = problem.goal.item - problem.goal.answer
        if eq not in problem.condition.get_items_by_predicate("Equation"):  # target not in condition set
            group[(problem.goal.premise, problem.goal.theorem)] = [problem.condition.id_count]

    adjust_group = {}
    for premise, theorem in group:
        adjust_theorem = (theorem[0], theorem[1], theorem[2], len(adjust_group))
        adjust_group[(premise, adjust_theorem)] = group[(premise, theorem)]

    rough_dag = {}
    for premise, theorem in adjust_group:  # generate theorem dag
        conclusion = adjust_group[(premise, theorem)]
        for _id in conclusion:
            for tail_premise, tail_theorem in adjust_group:
                if _id not in tail_premise:
                    continue
                if theorem not in rough_dag:
                    rough_dag[theorem] = []
                if tail_theorem not in rough_dag[theorem]:
                    rough_dag[theorem].append(tail_theorem)

    update = True
    while update:  # remove tail which contains 'extended' and 'solve_eq'
        update = False
        for head in rough_dag:
            for tail in list(rough_dag[head]):
                if tail[0] not in ["extended", "solve_eq"]:
                    continue
                rough_dag[head].pop(rough_dag[head].index(tail))
                if tail not in rough_dag:
                    continue
                for new_tail in rough_dag[tail]:
                    rough_dag[head].append(new_tail)
                    update = True

    cleaned_dag = {}
    for head in rough_dag:  # remove head which contains 'extended' and 'solve_eq'
        if head[0] in ["extended", "solve_eq"]:
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
            start_nodes.append(inverse_parse_one_theorem(
                (head[0], head[1], head[2]), problem.parsed_theorem_GDL))

    dag = {"START": start_nodes}
    for head in cleaned_dag:
        if len(cleaned_dag[head]) == 0:
            continue
        inverse_adjust_head = inverse_parse_one_theorem(
            (head[0], head[1], head[2]), problem.parsed_theorem_GDL)
        dag[inverse_adjust_head] = [
            inverse_parse_one_theorem((tail[0], tail[1], tail[2]), problem.parsed_theorem_GDL)
            for tail in cleaned_dag[head]
        ]

    return dag


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
                problem.timing[step][0][0] not in ["solve_eq", "extended", "prerequisite"]:
            selected_theorem.append(problem.timing[step][0])
    if problem.goal.theorem[0] not in ["solve_eq", "extended", "prerequisite"] and \
            problem.goal.theorem not in selected_theorem:
        selected_theorem.append(problem.goal.theorem)

    return used_pid, selected_theorem
