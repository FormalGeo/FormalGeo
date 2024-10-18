from formalgeo.parse.basic import parse_geo_predicate, parse_equal_predicate, parse_equal_to_tree


def parse_problem_cdl(problem_CDL):
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
            parsed_equal, _ = parse_equal_predicate(fl)
            parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append(parsed_equal)
        elif fl.startswith("Equation"):
            fl = fl.replace("Equation(", "")
            fl = fl[0:len(fl) - 1]
            parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append(("Equation", fl))
        else:
            predicate, para, _ = parse_geo_predicate(fl)
            parsed_CDL["parsed_cdl"]["text_and_image_cdl"].append([predicate, para])

    if problem_CDL["goal_cdl"].startswith("Value"):
        parsed_CDL["parsed_cdl"]["goal"]["type"] = "value"
        parsed_goal = problem_CDL["goal_cdl"][6:len(problem_CDL["goal_cdl"]) - 1]
        if parsed_goal[0].isupper():
            parsed_goal, _ = parse_equal_to_tree(parsed_goal)
            parsed_CDL["parsed_cdl"]["goal"]["item"] = ("Value", parsed_goal)
        else:
            parsed_CDL["parsed_cdl"]["goal"]["item"] = ("Value", parsed_goal)
        parsed_CDL["parsed_cdl"]["goal"]["answer"] = problem_CDL["problem_answer"]
    elif problem_CDL["goal_cdl"].startswith("Equal"):
        parsed_CDL["parsed_cdl"]["goal"]["type"] = "equal"
        parsed_goal, _ = parse_equal_predicate(problem_CDL["goal_cdl"])
        parsed_CDL["parsed_cdl"]["goal"]["item"] = parsed_goal
        parsed_CDL["parsed_cdl"]["goal"]["answer"] = "0"
    elif problem_CDL["goal_cdl"].startswith("Relation"):
        parsed_CDL["parsed_cdl"]["goal"]["type"] = "logic"
        predicate, para, _ = parse_geo_predicate(
            problem_CDL["goal_cdl"].split("(", 1)[1])
        parsed_CDL["parsed_cdl"]["goal"]["item"] = predicate
        parsed_CDL["parsed_cdl"]["goal"]["answer"] = para

    return parsed_CDL


def parse_theorem_seqs(theorem_seqs):
    """Parse theorem_seqs to logic form."""
    results = []

    for theorem in theorem_seqs:
        results.append(parse_one_theorem(theorem))

    return results


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
        if "," in t_para:
            t_branch, t_para = t_para.split(",", 1)
            t_para = tuple(t_para.replace(",", ""))
            return t_name, t_branch, t_para
        else:
            return t_name, t_para, None

    t_para = tuple(t_para.replace(",", ""))
    return t_name, None, t_para
