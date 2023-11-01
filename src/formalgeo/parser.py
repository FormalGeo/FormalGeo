from sympy import sin, cos, tan, sqrt, pi
from sympy.parsing import parse_expr


class Parser:
    """Parse formal language to machine language"""
    operator_predicate = ["Add", "Sub", "Mul", "Div", "Pow", "Mod", "Sqrt", "Sin", "Cos", "Tan"]

    @staticmethod
    def parse_geo_predicate(s, make_vars=False):
        """
        Parse s to get predicate_name, para, and para structural msg.
        >> parse_geo_predicate('Predicate(ABC)')
        ('Predicate', ['A', 'B', 'C'], [3])
        >> parse_geo_predicate('Predicate(ABC, DE)', True)
        ('Predicate', ['a', 'b', 'c', 'd', 'e'], [3, 2])
        """
        predicate_name, para = s.split("(")
        para = para.replace(")", "")
        if make_vars:
            para = para.lower()

        if "," not in para:
            return predicate_name, list(para), [len(para)]
        para_len = []
        para = para.split(",")
        for item in para:
            para_len.append(len(item))
        return predicate_name, list("".join(para)), para_len

    @staticmethod
    def parse_equal_predicate(s, make_vars=False):
        """
        Parse s to a Tree, return the tree and all attr.
        >> parse_equal_predicate('Equal(LengthOfLine(AB),LengthOfLine(CD))')
        (('Equal', (('LengthOfLine', ('A', 'B')), ('LengthOfLine', ('C', 'D')))),
         [('LengthOfLine', ('A', 'B')), ('LengthOfLine', ('C', 'D'))])
        >> parse_equal_predicate('Equal(LengthOfLine(OA),LengthOfLine(OB))', True)
        (('Equal', (('LengthOfLine', ('o', 'a')), ('LengthOfLine', ('o', 'b')))),
         [('LengthOfLine', ('o', 'a')), ('LengthOfLine', ('o', 'b'))])
        >> parse_equal_predicate('Equal(Add(LengthOfLine(OA),x+1),y+2)', True)
        (('Equal', (('Add', (('LengthOfLine', ('o', 'a')), 'x+1')), 'y+2')),
         [('LengthOfLine', ('o', 'a'))])
        """
        s = s[6:len(s) - 1]
        count = 0
        m = 0
        for i in range(len(s)):
            if s[i] == "(":
                count += 1
            elif s[i] == ")":
                count -= 1

            if count == 0 and s[i] == ",":
                m = i

        if count != 0:
            e_msg = "Sym stack not empty. Miss ')' in {}?.".format(s)
            raise Exception(e_msg)

        left = s[0:m]
        right = s[m + 1:len(s)]
        attrs = []
        if left[0].isupper():
            left, l_attrs = Parser.parse_to_tree(left, make_vars)
            attrs += l_attrs
        if right[0].isupper():
            right, l_attrs = Parser.parse_to_tree(right, make_vars)
            attrs += l_attrs

        return ("Equal", (left, right)), attrs

    @staticmethod
    def parse_to_tree(s, make_vars=False):
        """
        Parse equal's para to a Tree, return the tree and all attr.
        >> parse_to_tree('LengthOfLine(AB)')
        (('LengthOfLine', ('A', 'B')), [('LengthOfLine', ('A', 'B'))])
        >> parse_to_tree('LengthOfLine(AB)', True)
        (('LengthOfLine', ('a', 'b')), [('LengthOfLine', ('a', 'b'))])
        >> parse_to_tree('Add(LengthOfLine(OA),x+1)', True)
        (('Add', (('LengthOfLine', ('o', 'a')), 'x+1')), [('LengthOfLine', ('o', 'a'))])
        """
        attrs = []
        i = 0
        j = 0
        stack = []
        while j < len(s):
            if s[j] == "(":
                stack.append(s[i:j])
                stack.append(s[j])
                i = j + 1

            elif s[j] == ",":
                if i < j:
                    stack.append(s[i: j])
                    i = j + 1
                else:
                    i = i + 1

            elif s[j] == ")":
                if i < j:
                    stack.append(s[i: j])
                    i = j + 1
                else:
                    i = i + 1

                paras = []
                while stack[-1] != "(":
                    paras.append(stack.pop())
                stack.pop()  # pop '('
                predicate = stack.pop()
                if predicate in Parser.operator_predicate:  # not attribution
                    stack.append((predicate, tuple(paras[::-1])))
                else:  # attribution
                    paras = tuple("".join(paras[::-1]).lower() if make_vars else "".join(paras[::-1]))
                    stack.append((predicate, paras))
                    attrs.append((predicate, paras))

            j = j + 1

        return stack.pop(), attrs


class GDLParser(Parser):
    """Parse formal language to machine language"""

    @staticmethod
    def parse_predicate_gdl(predicate_GDL):
        """parse predicate_GDL to logic form."""
        parsed_GDL = {  # preset Construction
            "FixLength": tuple(predicate_GDL["Preset"]["FixLength"]),
            "VariableLength": tuple(predicate_GDL["Preset"]["VariableLength"]),
            "Construction": tuple(predicate_GDL["Preset"]["Construction"]),
            "BasicEntity": tuple(predicate_GDL["Preset"]["BasicEntity"]),
            "Entity": {},
            "Relation": {},
            "Attribution": {}
        }
        entities = predicate_GDL["Entity"]  # parse entity
        for item in entities:
            name, para, para_len = GDLParser.parse_geo_predicate(item, True)
            parsed_GDL["Entity"][name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "ee_check": tuple(GDLParser.parse_ee_check(entities[item]["ee_check"])),
                "multi": tuple(GDLParser.parse_multi(entities[item]["multi"])),
                "extend": tuple(GDLParser.parse_extend(entities[item]["extend"]))
            }

        relations = predicate_GDL["Relation"]  # parse relation
        for item in relations:
            name, para, para_len = GDLParser.parse_geo_predicate(item, True)
            if "fv_check" in relations[item]:
                parsed_GDL["Relation"][name] = {
                    "vars": tuple(para),
                    "para_len": tuple(para_len),
                    "ee_check": tuple(GDLParser.parse_ee_check(relations[item]["ee_check"])),
                    "fv_check": tuple(GDLParser.parse_fv_check(relations[item]["fv_check"])),
                    "multi": tuple(GDLParser.parse_multi(relations[item]["multi"])),
                    "extend": tuple(GDLParser.parse_extend(relations[item]["extend"]))
                }
            else:
                parsed_GDL["Relation"][name] = {
                    "vars": tuple(para),
                    "para_len": tuple(para_len),
                    "ee_check": tuple(GDLParser.parse_ee_check(relations[item]["ee_check"])),
                    "multi": tuple(GDLParser.parse_multi(relations[item]["multi"])),
                    "extend": tuple(GDLParser.parse_extend(relations[item]["extend"]))
                }

        attributions = predicate_GDL["Attribution"]  # parse attribution
        for item in attributions:
            name, para, para_len = GDLParser.parse_geo_predicate(item, True)
            if "fv_check" in attributions[item]:
                parsed_GDL["Attribution"][name] = {
                    "vars": tuple(para),
                    "para_len": tuple(para_len),
                    "ee_check": tuple(GDLParser.parse_ee_check(attributions[item]["ee_check"])),
                    "fv_check": tuple(GDLParser.parse_fv_check(attributions[item]["fv_check"])),
                    "sym": attributions[item]["sym"],
                    "multi": tuple(GDLParser.parse_multi(attributions[item]["multi"]))
                }
            else:
                parsed_GDL["Attribution"][name] = {
                    "vars": tuple(para),
                    "para_len": tuple(para_len),
                    "ee_check": tuple(GDLParser.parse_ee_check(attributions[item]["ee_check"])),
                    "sym": attributions[item]["sym"],
                    "multi": tuple(GDLParser.parse_multi(attributions[item]["multi"]))
                }

        return parsed_GDL

    @staticmethod
    def parse_ee_check(ee_check):
        """
        parse ee_check to logic form.
        >> parse_ee_check(['Triangle(ABC)'])
        [('Triangle', ('a', 'b', 'c'))]
        >> parse_ee_check(['Line(AO)', 'Line(CO)'])
        [('Line', ('a', 'o')), ('Line', ('c', 'o'))]
        """
        results = []
        for item in ee_check:
            name, item_para, _ = GDLParser.parse_geo_predicate(item, True)
            results.append((name, tuple(item_para)))
        return results

    @staticmethod
    def parse_fv_check(fv_check):
        """
        parse fv_check to logic form.
        >> parse_fv_check(['O,AB,CD'])
        ['01234']
        >> parse_fv_check(['AD,ABC', 'AB,ABC', 'AC,ABC'])
        ['01023', '01012', '01021']
        """
        results = []
        for item in fv_check:
            checked = []
            result = []
            for i in item.replace(",", ""):
                if i not in checked:
                    checked.append(i)
                result.append(str(checked.index(i)))
            results.append("".join(result))
        return results

    @staticmethod
    def parse_multi(multi):
        """
        parse multi to logic form.
        >> _parse_multi(['BCA', 'CAB'])
        [('b', 'c', 'a'), ('c', 'a', 'b')]
        >> _parse_multi(['M,BA'])
        [('m', 'b', 'a')]
        """
        return [tuple(parsed_multi.replace(",", "").lower()) for parsed_multi in multi]

    @staticmethod
    def parse_extend(extend_items):
        """
        parse extend to logic form.
        >> parse_extend(['Equal(MeasureOfAngle(AOC),90)'])
        [('Equal', (('MeasureOfAngle', ('a', 'o', 'c')), '90'))]
        >> parse_extend(['Perpendicular(AB,CB)', 'IsAltitude(AB,ABC)'])
        [('Perpendicular', ('a', 'b', 'c', 'b')), ('IsAltitude', ('a', 'b', 'a', 'b', 'c'))]
        """
        results = []
        for extend in extend_items:
            if extend.startswith("Equal"):
                parsed_equal, _ = GDLParser.parse_equal_predicate(extend, True)
                results.append(parsed_equal)
            else:
                extend_name, extend_para, _ = GDLParser.parse_geo_predicate(extend, True)
                results.append((extend_name, tuple(extend_para)))
        return results

    @staticmethod
    def parse_theorem_gdl(theorem_GDL, parsed_predicate_GDL):
        """Parse theorem_GDL to logic form."""
        parsed_GDL = {}

        for theorem_name in theorem_GDL:
            name, para, para_len = GDLParser.parse_geo_predicate(theorem_name, True)
            p1 = set(para)

            body = {}
            branch_count = 1
            for branch in theorem_GDL[theorem_name]:
                raw_premise_GDL = [theorem_GDL[theorem_name][branch]["premise"]]
                parsed_premise, paras_list = GDLParser.parse_premise(raw_premise_GDL)
                raw_theorem_GDL = theorem_GDL[theorem_name][branch]["conclusion"]
                parsed_conclusion, paras = GDLParser.parse_conclusion(raw_theorem_GDL)

                p2 = set(paras)    # theorem_GDL format check
                if len(p2 - p1) > 0:
                    e_msg = "Theorem GDL definition error in <{}>.".format(theorem_name)
                    raise Exception(e_msg)

                for i in range(len(parsed_premise)):
                    p2 = set(paras_list[i])
                    if len(p2 - p1) > 0 or len(p1 - p2) > 0:
                        e_msg = "Theorem GDL definition error in <{}>.".format(theorem_name)
                        raise Exception(e_msg)
                    body[str(branch_count)] = parsed_premise[i]    # add parsed premise
                    body[str(branch_count)].update(parsed_conclusion)    # add parsed conclusion
                    branch_count += 1

            parsed_GDL[name] = {
                "vars": tuple(para),
                "para_len": tuple(para_len),
                "body": body
            }

        # Auto generate theorem definition for backward solving
        for predicate in parsed_predicate_GDL["Entity"]:
            conclusions = list(parsed_predicate_GDL["Entity"][predicate]["extend"])    # add extend
            for multi in parsed_predicate_GDL["Entity"][predicate]["multi"]:    # add multi
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
                attr_in_conclusions += GDLParser.find_attrs_in_tree(conclusion)

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
                attr_in_conclusions += GDLParser.find_attrs_in_tree(conclusion)

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

    @staticmethod
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
                    premise_GDL[i][j], eq_attrs = GDLParser.parse_equal_predicate(premise_GDL[i][j], True)
                    attrs += eq_attrs
                    for attr, para in eq_attrs:
                        paras += list(para)
                else:
                    predicate, para, _ = GDLParser.parse_geo_predicate(premise_GDL[i][j], True)
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

    @staticmethod
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
        for i in range(len(conclusion_GDL)):
            if "Equal" in conclusion_GDL[i]:
                conclusion_GDL[i], eq_attrs = GDLParser.parse_equal_predicate(conclusion_GDL[i], True)
                attrs += eq_attrs
                for attr, para in eq_attrs:
                    paras += list(para)
            else:
                predicate, para, _ = GDLParser.parse_geo_predicate(conclusion_GDL[i], True)
                conclusion_GDL[i] = (predicate, tuple(para))
                paras += para

        parsed_conclusion_GDL = {
            "conclusions": tuple(conclusion_GDL),
            "attr_in_conclusions": sorted(tuple([(attr, tuple(para)) for attr, para in set(attrs)]))
        }
        return parsed_conclusion_GDL, paras

    @staticmethod
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
            if item[0] in GDLParser.operator_predicate:
                for item in item[1]:
                    stack.append(item)
                continue
            if item not in attrs:
                attrs.append(item)
        return attrs


class CDLParser(Parser):
    """Parse formal language to machine language"""

    @staticmethod
    def parse_problem(problem_CDL):
        """parse problem_CDL to logic form."""
        parsed_CDL = {
            "id": problem_CDL["problem_id"],
            "cdl": {
                "construction_cdl": problem_CDL["construction_cdl"],
                "text_cdl": problem_CDL["text_cdl"],
                "image_cdl": problem_CDL["image_cdl"],
                "goal_cdl": problem_CDL["goal_cdl"]
            },
            "parsed_cdl": {
                "construction_cdl": [],
                "text_and_image_cdl": [],
                "goal": {},
            }
        }
        for fl in problem_CDL["construction_cdl"]:
            predicate, para = fl.split("(")
            para = para.replace(")", "")
            if predicate == "Shape":
                parsed_CDL["parsed_cdl"]["construction_cdl"].append([predicate, para.split(",")])
            elif predicate == "Collinear":
                parsed_CDL["parsed_cdl"]["construction_cdl"].append([predicate, list(para)])
            elif predicate == "Cocircular":
                parsed_CDL["parsed_cdl"]["construction_cdl"].append([predicate, list(para.replace(",", ""))])
            else:
                e_msg = "The predicate <{}> should not appear in construction_cdl.".format(predicate)
                raise Exception(e_msg)

        for fl in problem_CDL["text_cdl"] + problem_CDL["image_cdl"]:
            if fl.startswith("Equal"):
                parsed_equal, _ = CDLParser.parse_equal_predicate(fl)
                parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append(parsed_equal)
            elif fl.startswith("Equation"):
                fl = fl.replace("Equation(", "")
                fl = fl[0:len(fl) - 1]
                parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append(("Equation", fl))
            else:
                predicate, para, _ = CDLParser.parse_geo_predicate(fl)
                parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append([predicate, para])

        if problem_CDL["goal_cdl"].startswith("Value"):
            parsed_CDL["parsed_cdl"]["goal"]["type"] = "value"
            parsed_goal = problem_CDL["goal_cdl"][6:len(problem_CDL["goal_cdl"]) - 1]
            if parsed_goal[0].isupper():
                parsed_goal, _ = CDLParser.parse_to_tree(parsed_goal)
                parsed_CDL["parsed_cdl"]["goal"]["item"] = ("Value", parsed_goal)
            else:
                parsed_CDL["parsed_cdl"]["goal"]["item"] = ("Value", parsed_goal)
            parsed_CDL["parsed_cdl"]["goal"]["answer"] = problem_CDL["problem_answer"]
        elif problem_CDL["goal_cdl"].startswith("Equal"):
            parsed_CDL["parsed_cdl"]["goal"]["type"] = "equal"
            parsed_goal, _ = CDLParser.parse_equal_predicate(problem_CDL["goal_cdl"])
            parsed_CDL["parsed_cdl"]["goal"]["item"] = parsed_goal
            parsed_CDL["parsed_cdl"]["goal"]["answer"] = "0"
        elif problem_CDL["goal_cdl"].startswith("Relation"):
            parsed_CDL["parsed_cdl"]["goal"]["type"] = "logic"
            predicate, para, _ = CDLParser.parse_geo_predicate(
                problem_CDL["goal_cdl"].split("(", 1)[1])
            parsed_CDL["parsed_cdl"]["goal"]["item"] = predicate
            parsed_CDL["parsed_cdl"]["goal"]["answer"] = para

        return parsed_CDL

    @staticmethod
    def parse_theorem_seqs(theorem_seqs):
        """Parse theorem_seqs to logic form."""
        results = []

        for theorem in theorem_seqs:
            results.append(CDLParser.parse_one_theorem(theorem))

        return results

    @staticmethod
    def parse_one_theorem(theorem):
        """
        Parse one theorem to logic form.
        >> parse_one_theorem('congruent_triangle_property_angle_equal(1,RST,XYZ)')
        ('congruent_triangle_property_angle_equal', 1, ('R', 'S', 'T', 'X', 'Y', 'Z'))
        >> parse_one_theorem('congruent_triangle_property_angle_equal(RST,XYZ)')
        ('congruent_triangle_property_angle_equal', None, ('R', 'S', 'T', 'X', 'Y', 'Z'))
        >> parse_one_theorem('congruent_triangle_property_angle_equal')
        ('congruent_triangle_property_angle_equal', None, None)
        """
        if "(" not in theorem:
            return theorem, None, None

        t_name, t_para = theorem.split("(", 1)
        t_para = t_para.replace(")", "")
        if t_para[0].isnumeric():
            t_branch, t_para = t_para.split(",", 1)
            t_para = tuple(t_para.replace(",", ""))
            return t_name, t_branch, t_para

        t_para = tuple(t_para.replace(",", ""))
        return t_name, None, t_para

    @staticmethod
    def get_equation_from_tree(problem, tree, replaced=False, letters=None):
        """
        Trans expr_tree to symbolic algebraic expression.
        >> get_expr_from_tree(problem, [['LengthOfLine', ['a', 'b']], '2*x-14'], True, {'a': 'Z', 'b': 'X'})
        - 2.0*f_x + ll_zx + 14.0
        >> get_expr_from_tree(problem, [['LengthOfLine', ['Z', 'X']], '2*x-14'])
        - 2.0*f_x + ll_zx + 14.0
        """
        left_expr = CDLParser.get_expr_from_tree(problem, tree[0], replaced, letters)
        if left_expr is None:
            return None
        right_expr = CDLParser.get_expr_from_tree(problem, tree[1], replaced, letters)
        if right_expr is None:
            return None
        return left_expr - right_expr

    @staticmethod
    def get_expr_from_tree(problem, tree, replaced=False, letters=None):
        """
        Recursively trans expr_tree to symbolic algebraic expression.
        :param problem: class <Problem>.
        :param tree: An expression in the form of a list tree.
        :param replaced: Optional. Set True when tree's item is expressed by vars.
        :param letters: Optional. Letters that will replace vars. Dict = {var: letter}.
        >> get_expr_from_tree(problem, ['LengthOfLine', ['T', 'R']])
        l_tr
        >> get_expr_from_tree(problem, ['Add', [['LengthOfLine', ['Z', 'X']], '2*x-14']])
        2.0*f_x + l_zx - 14.0
        >> get_expr_from_tree(problem, ['Sin', [['MeasureOfAngle', ['a', 'b', 'c']]]],
                              True, {'a': 'X', 'b': 'Y', 'c': 'Z'})
        sin(pi*m_zxy/180)
        """
        if not isinstance(tree, tuple):  # expr
            return CDLParser.parse_expr(problem, tree)
        if tree[0] in problem.predicate_GDL["Attribution"]:  # attr
            if not replaced:
                return problem.get_sym_of_attr(tree[0], tree[1])
            else:
                replaced_item = [letters[i] for i in tree[1]]
                return problem.get_sym_of_attr(tree[0], tuple(replaced_item))

        if tree[0] in ["Add", "Mul"]:  # operate
            expr_list = []
            for item in tree[1]:
                expr = CDLParser.get_expr_from_tree(problem, item, replaced, letters)
                if expr is None:
                    return None
                expr_list.append(expr)
            if tree[0] == "Add":
                result = 0
                for expr in expr_list:
                    result += expr
            else:
                result = 1
                for expr in expr_list:
                    result *= expr
            return result
        elif tree[0] in ["Sub", "Div", "Pow", "Mod"]:
            expr_left = CDLParser.get_expr_from_tree(problem, tree[1][0], replaced, letters)
            if expr_left is None:
                return None
            expr_right = CDLParser.get_expr_from_tree(problem, tree[1][1], replaced, letters)
            if expr_right is None:
                return None
            if tree[0] == "Sub":
                return expr_left - expr_right
            elif tree[0] == "Div":
                return expr_left / expr_right
            elif tree[0] == "Pow":
                return expr_left ** expr_right
            else:
                return expr_left % expr_right
        elif tree[0] in ["Sin", "Cos", "Tan", "Sqrt"]:
            expr = CDLParser.get_expr_from_tree(problem, tree[1][0], replaced, letters)
            if expr is None:
                return None
            if tree[0] == "Sin":
                return sin(expr * pi / 180)
            elif tree[0] == "Cos":
                return cos(expr * pi / 180)
            elif tree[0] == "Tan":
                return tan(expr * pi / 180)
            else:
                return sqrt(expr)
        else:
            e_msg = "Operator {} not defined, please check your expression.".format(tree[0])
            raise Exception(e_msg)

    @staticmethod
    def parse_expr(problem, expr):
        """Parse expression to symbolic form."""
        expr = parse_expr(expr)

        for sym in expr.free_symbols:
            if "_" not in str(sym):
                saved_sym = problem.get_sym_of_attr("Free", str(sym))
                if saved_sym is None:
                    return None
                expr = expr.subs(sym, saved_sym)
            else:
                sym_str, para = str(sym).split("_", 1)
                para = tuple(para.upper())
                attr_GDL = problem.predicate_GDL["Attribution"]
                in_GDL = False
                for attr_name in attr_GDL:
                    if attr_GDL[attr_name]["sym"] == sym_str:
                        in_GDL = True
                        saved_sym = problem.get_sym_of_attr(attr_name, para)
                        if saved_sym is None:
                            return None
                        expr = expr.subs(sym, saved_sym)
                if not in_GDL:
                    return None

        return expr


class InverseParserM2F:
    """Inverse parse machine language to formal language."""

    @staticmethod
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

                if predicate in problem.predicate_GDL["Construction"] or \
                        predicate in problem.predicate_GDL["BasicEntity"]:  # skip preset
                    i += 1
                    continue

                result = InverseParserM2F.inverse_parse_one(predicate, item, problem)
                inverse_parsed_cdl[step].append(result)

                if predicate in problem.predicate_GDL["Entity"]:  # remove duplicate representation
                    i += len(problem.predicate_GDL["Entity"][predicate]["multi"]) + 1
                elif predicate in problem.predicate_GDL["Relation"]:
                    i += len(problem.predicate_GDL["Relation"][predicate]["multi"]) + 1
                else:  # Equation
                    i += 1

        return inverse_parsed_cdl

    @staticmethod
    def inverse_parse_one(predicate, item, problem):
        """
        Inverse parse one condition.
        Called by <inverse_parse_logic_to_cdl>.
        """
        if predicate == "Equation":
            return InverseParserM2F.inverse_parse_equation(item, problem)
        elif predicate in problem.predicate_GDL["Construction"] or predicate in problem.predicate_GDL["BasicEntity"]:
            return InverseParserM2F.inverse_parse_preset(predicate, item)
        else:
            return InverseParserM2F.inverse_parse_logic(predicate, item, problem)

    @staticmethod
    def inverse_parse_logic(predicate, item, problem):
        """
        Inverse parse logic conditions.
        >> inverse_parse_logic(Parallel, ('A', 'B', 'C', 'D'), problem)
        'Parallel(AB,CD)'
        """
        if predicate in problem.predicate_GDL["Entity"]:
            return predicate + "(" + "".join(item) + ")"
        else:
            result = []
            i = 0
            for l in problem.predicate_GDL["Relation"][predicate]["para_len"]:
                result.append("")
                for _ in range(l):
                    result[-1] += item[i]
                    i += 1
            return predicate + "(" + ",".join(result) + ")"

    @staticmethod
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
            if problem.condition.value_of_sym[syms[0]] is not None and\
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

    @staticmethod
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

    @staticmethod
    def inverse_parse_one_theorem(t_name, t_branch, t_para, theorem_GDL):
        """
        Inverse parse theorem to formal language.
        >> inverse_parse_one_theorem('t_name', 1, ('R', 'S', 'T'), theorem_GDL)
        't_name(1,RST)'
        >> inverse_parse_one_theorem('t_name', None, ('R', 'S', 'T'), theorem_GDL)
        't_name(RST)'
        >> inverse_parse_one_theorem('t_name', None, None, theorem_GDL)
        't_name'
        """
        if t_para is None:
            if t_branch is None:
                return t_name
            return "{}({})".format(t_name, t_branch)
        else:
            result = []
            i = 0
            for l in theorem_GDL[t_name]["para_len"]:
                result.append("")
                for _ in range(l):
                    result[-1] += t_para[i]
                    i += 1
            t_para = ",".join(result)

            if t_branch is None:
                return "{}({})".format(t_name, t_para)
            return "{}({},{})".format(t_name, t_branch, t_para)


class InverseParserF2N:
    """Inverse parse formal language to natural language."""
    pass
