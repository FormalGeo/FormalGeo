def inverse_parse_logic_to_cdl(problem):
    """Inverse parse conditions from machine language to formal language."""
    items = problem.condition.items
    steps = problem.condition.ids_of_step

    inverse_parsed_cdl = {}
    for step in sorted(list(steps)):
        if len(steps[step]) == 0:
            continue
        inverse_parsed_cdl[step] = []
        i = 0
        while i < len(steps[step]):
            _id = steps[step][i]
            predicate, item = items[_id][0], items[_id][1]

            if predicate in problem.parsed_predicate_GDL["Preset"]["Construction"] or \
                    predicate in problem.parsed_predicate_GDL["Preset"]["BasicEntity"]:  # skip preset
                i += 1
                continue

            result = inverse_parse_one(predicate, item, problem)
            inverse_parsed_cdl[step].append(result)

            if predicate in problem.parsed_predicate_GDL["Entity"]:  # remove duplicate representation
                i += len(problem.parsed_predicate_GDL["Entity"][predicate]["multi"]) + 1
            elif predicate in problem.parsed_predicate_GDL["Relation"]:
                i += len(problem.parsed_predicate_GDL["Relation"][predicate]["multi"]) + 1
            else:  # Equation
                i += 1

    return inverse_parsed_cdl


def inverse_parse_one(predicate, item, problem, remove_predicate=False):
    """
    Inverse parse one condition.
    Called by <inverse_parse_logic_to_cdl>.
    """
    if predicate == "Equation":
        inverse_parsed = inverse_parse_equation(item, problem)
    elif (predicate in problem.parsed_predicate_GDL["Preset"]["Construction"] or
          predicate in problem.parsed_predicate_GDL["Preset"]["BasicEntity"]):
        inverse_parsed = inverse_parse_preset(predicate, item)
    else:
        inverse_parsed = inverse_parse_logic(predicate, item, problem)

    if remove_predicate:
        inverse_parsed = inverse_parsed.split("(")[1].replace(")", "")

    return inverse_parsed


def inverse_parse_logic(predicate, item, problem):
    """
    Inverse parse logic conditions.
    >> inverse_parse_logic(Parallel, ('A', 'B', 'C', 'D'), problem)
    'Parallel(AB,CD)'
    """
    if predicate in problem.parsed_predicate_GDL["Entity"]:
        return predicate + "(" + "".join(item) + ")"
    else:
        result = []
        i = 0
        for l in problem.parsed_predicate_GDL["Relation"][predicate]["para_len"]:
            result.append("")
            for _ in range(l):
                result[-1] += item[i]
                i += 1
        return predicate + "(" + ",".join(result) + ")"


def inverse_parse_equation(item, problem):
    """
    Inverse parse algebra conditions.
    >> inverse_parse_one(ll_ac - ll_cd, problem)
    'Equal(LengthOfLine(AC),LengthOfLine(CD))'
    >> inverse_parse_one(ll_ac - 1, problem)
    'Value(LengthOfLine(AC))'
    >> inverse_parse_one(ll_ac - ll_cd - ll_ef, problem)
    'Equation(ll_ac-ll_cd-ll_ef)'
    """
    syms = list(item.free_symbols)
    if len(syms) == 1:
        if problem.condition.value_of_sym[syms[0]] is not None and \
                syms[0] - problem.condition.value_of_sym[syms[0]] == item:
            attr, items = problem.condition.attr_of_sym[syms[0]]
            if attr == "Free":
                attr = items[0][0]
            else:
                attr = attr + "(" + "".join(items[0]) + ")"
            return "Value({},{})".format(attr, str(problem.condition.value_of_sym[syms[0]]).replace(" ", ""))
    elif len(syms) == 2 and (item == (syms[0] - syms[1]) or item == (syms[1] - syms[0])):
        attr1, items1 = problem.condition.attr_of_sym[syms[0]]
        if attr1 == "Free":
            attr1 = items1[0][0]
        else:
            attr1 = attr1 + "(" + "".join(items1[0]) + ")"
        attr2, items2 = problem.condition.attr_of_sym[syms[1]]
        if attr2 == "Free":
            attr2 = items2[0][0]
        else:
            attr2 = attr2 + "(" + "".join(items2[0]) + ")"
        if item == (syms[0] - syms[1]):
            return "Equal({},{})".format(attr1, attr2)
        return "Equal({},{})".format(attr2, attr1)

    return "Equation" + "(" + str(item).replace(" ", "") + ")"


def inverse_parse_preset(predicate, item):
    """
    Inverse parse preset conditions.
    >> inverse_parse_logic(Line, ('A', 'B'))
    'Line(AB)'
    >> inverse_parse_logic(Cocircular, ('O', 'A', 'B', 'C'))
    'Cocircular(O,ABC)'
    """
    if predicate == "Cocircular":
        if len(item) == 1:
            return "Cocircular({})".format(item[0])
        else:
            return "Cocircular({},{})".format(item[0], "".join(item[1:]))
    elif predicate == "Shape":
        return "Shape({})".format(",".join(item))
    else:
        return "{}({})".format(predicate, "".join(item))


def inverse_parse_one_theorem(theorem, parsed_theorem_GDL):
    """
    Inverse parse theorem to formal language.
    >> inverse_parse_one_theorem('t_name', 1, ('R', 'S', 'T'), parsed_theorem_GDL)
    't_name(1,RST)'
    >> inverse_parse_one_theorem('t_name', None, ('R', 'S', 'T'), parsed_theorem_GDL)
    't_name(RST)'
    >> inverse_parse_one_theorem('t_name', None, None, parsed_theorem_GDL)
    't_name'
    """
    t_name, t_branch, t_para = theorem
    if t_para is None:
        if t_branch is None:
            return t_name
        return "{}({})".format(t_name, t_branch)
    else:
        result = []
        i = 0
        for l in parsed_theorem_GDL[t_name]["para_len"]:
            result.append("")
            for _ in range(l):
                result[-1] += t_para[i]
                i += 1
        t_para = ",".join(result)

        if t_branch is None:
            return "{}({})".format(t_name, t_para)
        return "{}({},{})".format(t_name, t_branch, t_para)
