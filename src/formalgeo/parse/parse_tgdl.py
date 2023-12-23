from formalgeo.parse.basic import parse_geo_predicate, parse_equal_predicate, operation


def parse_theorem_gdl(theorem_GDL, parsed_predicate_GDL):
    """Parse theorem_GDL to logic form."""
    parsed_GDL = {}

    for theorem_name in theorem_GDL:
        name, para, para_len = parse_geo_predicate(theorem_name, True)
        p1 = set(para)

        body = {}
        branch_count = 1
        for branch in theorem_GDL[theorem_name]:
            raw_premise_GDL = [theorem_GDL[theorem_name][branch]["premise"]]
            parsed_premise, paras_list = parse_premise(raw_premise_GDL)
            raw_theorem_GDL = theorem_GDL[theorem_name][branch]["conclusion"]
            parsed_conclusion, paras = parse_conclusion(raw_theorem_GDL)

            p2 = set(paras)  # theorem_GDL format check
            if len(p2 - p1) > 0:
                e_msg = "Theorem GDL definition error in <{}>.".format(theorem_name)
                raise Exception(e_msg)

            for i in range(len(parsed_premise)):
                p2 = set(paras_list[i])
                if len(p2 - p1) > 0 or len(p1 - p2) > 0:
                    e_msg = "Theorem GDL definition error in <{}>.".format(theorem_name)
                    raise Exception(e_msg)
                body[str(branch_count)] = parsed_premise[i]  # add parsed premise
                body[str(branch_count)].update(parsed_conclusion)  # add parsed conclusion
                branch_count += 1

        parsed_GDL[name] = {
            "vars": tuple(para),
            "para_len": tuple(para_len),
            "body": body
        }

    # Auto generate theorem definition for backward solving
    for predicate in parsed_predicate_GDL["Entity"]:
        conclusions = list(parsed_predicate_GDL["Entity"][predicate]["extend"])  # add extend
        for multi in parsed_predicate_GDL["Entity"][predicate]["multi"]:  # add multi
            conclusions.append((predicate, multi))
        if len(conclusions) == 0:
            continue

        name = predicate[0].lower()
        for i in range(1, len(predicate)):
            if predicate[i].isupper():
                name += "_{}".format(predicate[i].lower())
            else:
                name += predicate[i]
        name += "_definition"

        attr_in_conclusions = []
        for conclusion in conclusions:
            if conclusion[0] != "Equal":
                continue
            attr_in_conclusions += find_attrs_in_tree(conclusion)

        parsed_GDL[name] = {
            "vars": parsed_predicate_GDL["Entity"][predicate]["vars"],
            "para_len": parsed_predicate_GDL["Entity"][predicate]["para_len"],
            "body": {
                "1": {
                    "products": ((predicate, parsed_predicate_GDL["Entity"][predicate]["vars"]),),
                    "logic_constraints": (),
                    "algebra_constraints": (),
                    "attr_in_algebra_constraints": (),
                    "conclusions": tuple(conclusions),
                    "attr_in_conclusions": sorted(tuple(set(attr_in_conclusions)))
                }
            }
        }

    for predicate in parsed_predicate_GDL["Relation"]:
        conclusions = list(parsed_predicate_GDL["Relation"][predicate]["extend"])
        for multi in parsed_predicate_GDL["Relation"][predicate]["multi"]:
            conclusions.append((predicate, multi))
        if len(conclusions) == 0:
            continue

        name = predicate[0].lower()
        for i in range(1, len(predicate)):
            if predicate[i].isupper():
                name += "_{}".format(predicate[i].lower())
            else:
                name += predicate[i]
        name += "_definition"

        attr_in_conclusions = []
        for conclusion in conclusions:
            if conclusion[0] != "Equal":
                continue
            attr_in_conclusions += find_attrs_in_tree(conclusion)

        parsed_GDL[name] = {
            "vars": parsed_predicate_GDL["Relation"][predicate]["vars"],
            "para_len": parsed_predicate_GDL["Relation"][predicate]["para_len"],
            "body": {
                "1": {
                    "products": ((predicate, parsed_predicate_GDL["Relation"][predicate]["vars"]),),
                    "logic_constraints": (),
                    "algebra_constraints": (),
                    "attr_in_algebra_constraints": (),
                    "conclusions": tuple(conclusions),
                    "attr_in_conclusions": sorted(tuple(set(attr_in_conclusions)))
                }
            }
        }

    return parsed_GDL


def parse_premise(premise_GDL):
    """
    Parse premise and convert geometric logic statements into disjunctive normal forms.
    'A&(B|C)' ==> 'A&B|A&C' ==> [['A', 'B'], ['A', 'C']]
    >> parse_premise(['Perpendicular(AO,CO)&(Collinear(OBC)|Collinear(OCB))'])
    ([{'products': (('Perpendicular', ('a', 'o', 'c', 'o')), ('Collinear', ('o', 'b', 'c'))),
       'logic_constraints': (),
       'algebra_constraints': (),
       'attr_in_algebra_constraints': ()},
      {'products': (('Perpendicular', ('a', 'o', 'c', 'o')), ('Collinear', ('o', 'c', 'b'))),
       'logic_constraints': (),
       'algebra_constraints': (),
       'attr_in_algebra_constraints': ()}],
     [['a', 'o', 'c', 'o', 'o', 'b', 'c'],
      ['a', 'o', 'c', 'o', 'o', 'c', 'b']])
    """
    update = True
    while update:
        expanded = []
        update = False
        for item in premise_GDL:
            if "|" not in item:
                expanded.append(item)
            else:
                update = True
                left_index = 0
                or_index = item.index("|")
                right_index = -1

                count = 0
                for i in range(1, len(item)):
                    if item[or_index - i] == ")":
                        count -= 1
                    elif item[or_index - i] == "(":
                        count += 1
                    if count == 1:
                        left_index = or_index - i
                        break
                if left_index == 0:
                    head = ""
                else:
                    head = item[0:left_index]

                count = 0
                for i in range(1, len(item)):
                    if item[or_index + i] == "(":
                        count -= 1
                    elif item[or_index + i] == ")":
                        count += 1
                    if count == 1:
                        right_index = or_index + i
                        break
                if right_index == len(item) - 1:
                    tail = ""
                else:
                    tail = item[right_index + 1:len(item)]

                bodies = item[left_index + 1:right_index]
                if "&(" not in bodies:
                    bodies = bodies.split("|")
                else:
                    bodies = bodies.split("|", num=1)
                for body in bodies:
                    expanded.append(head + body + tail)
        premise_GDL = expanded

    paras_list = []
    for i in range(len(premise_GDL)):  # listing
        premise_GDL[i] = premise_GDL[i].split("&")
        attrs = []
        paras = []
        for j in range(len(premise_GDL[i])):
            if "Equal" in premise_GDL[i][j]:
                premise_GDL[i][j], eq_attrs = parse_equal_predicate(premise_GDL[i][j], True)
                attrs += eq_attrs
                for attr, para in eq_attrs:
                    paras += list(para)
            else:
                predicate, para, _ = parse_geo_predicate(premise_GDL[i][j], True)
                premise_GDL[i][j] = (predicate, tuple(para))
                paras += para

        product = []
        logic_constraint = []
        algebra_constraint = []
        existing_paras = set()
        for j in range(len(premise_GDL[i])):
            if premise_GDL[i][j][0][0] == "~":
                continue

            if premise_GDL[i][j][0] == "Equal":
                algebra_constraint.append(premise_GDL[i][j])
            elif len(set(premise_GDL[i][j][1]) - existing_paras) == 0:
                logic_constraint.append(premise_GDL[i][j])
            else:
                existing_paras = existing_paras | set(premise_GDL[i][j][1])
                product.append(premise_GDL[i][j])

        premise_GDL[i] = {
            "products": tuple(product),
            "logic_constraints": tuple(logic_constraint),
            "algebra_constraints": tuple(algebra_constraint),
            "attr_in_algebra_constraints": sorted(tuple([(attr, tuple(para)) for attr, para in set(attrs)]))
        }
        paras_list.append(paras)

    return premise_GDL, paras_list


def parse_conclusion(conclusion_GDL):
    """
    Parse conclusion to logic form, return logic form and para (for format check).
    >> parse_conclusion(['Similar(ABC,ADE)', 'Equal(LengthOfLine(AB),LengthOfLine(CD))'])
    ({'conclusions': (('Similar', ('a', 'b', 'c', 'a', 'd', 'e')),
                     ('Equal', (('LengthOfLine', ('a', 'b')), ('LengthOfLine', ('c', 'd'))))),
      'attr_in_conclusions': (('LengthOfLine', ('c', 'd')),
                             ('LengthOfLine', ('a', 'b')))},
     ['a', 'b', 'c', 'a', 'd', 'e', 'a', 'b', 'c', 'd'])
    """
    paras = []
    attrs = []
    parsed_conclusion_GDL = []
    for i in range(len(conclusion_GDL)):
        if "Equal" in conclusion_GDL[i]:
            parsed_GDL, eq_attrs = parse_equal_predicate(conclusion_GDL[i], True)
            parsed_conclusion_GDL.append(parsed_GDL)
            attrs += eq_attrs
            for attr, para in eq_attrs:
                paras += list(para)
        else:
            predicate, para, _ = parse_geo_predicate(conclusion_GDL[i], True)
            parsed_conclusion_GDL.append((predicate, tuple(para)))
            paras += para

    parsed_conclusion_GDL = {
        "conclusions": tuple(parsed_conclusion_GDL),
        "attr_in_conclusions": sorted(tuple([(attr, tuple(para)) for attr, para in set(attrs)]))
    }
    return parsed_conclusion_GDL, paras


def find_attrs_in_tree(tree):
    """
    Return attrs in parsed equal tree.
    >> find_attrs_in_tree((('Equal', (('Add', (('LengthOfLine', ('o', 'a')), 'x+1')), 'y+2'))))
    [('LengthOfLine', ('o', 'a')]
    """
    attrs = []
    stack = [tree[1][0], tree[1][1]]
    while len(stack) > 0:
        item = stack.pop()
        if not isinstance(item, tuple):
            continue
        if item[0] in operation:
            for item in item[1]:
                stack.append(item)
            continue
        if item not in attrs:
            attrs.append(item)
    return attrs
