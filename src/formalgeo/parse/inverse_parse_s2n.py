"""Inverse parse solution hypertree to natural language."""
import copy
from formalgeo.tools import load_json
from formalgeo.parse.basic import parse_geo_predicate
import string
import re


def inverse_parse_gdl(p_vars, s):
    i = 0
    while i < len(s) - 2:
        if s[i] == "{" and s[i + 1] in string.ascii_uppercase and s[i + 2] == "}":
            s = s.replace(s[i:i + 3], "{" + str(p_vars.index(s[i + 1])) + "}")
            i += 3
        else:
            i += 1
    return s


def parse_predicate_gdl_source(gdl_source):
    gdl = {}
    for p_class in ["Entity", "Relation", "Attribution"]:
        for predicate in gdl_source["Predicates"][p_class]:
            p_name, p_para, _ = parse_geo_predicate(predicate)
            gdl[p_name] = {
                "cn": [inverse_parse_gdl(p_para, s)
                       for s in gdl_source["Predicates"][p_class][predicate]["anti_parse_to_nl_cn"]],
                "en": [inverse_parse_gdl(p_para, s)
                       for s in gdl_source["Predicates"][p_class][predicate]["anti_parse_to_nl_en"]]
            }
    return gdl


def parse_theorem_gdl_source(gdl_source):
    gdl = {}
    for theorem in gdl_source["Theorems"]:
        gdl[theorem.split("(")[0]] = {
            "cn": gdl_source["Theorems"][theorem]["name_cn"],
            "en": gdl_source["Theorems"][theorem]["name_en"]
        }
    return gdl


def parse_item(item, gdl_source, sym_to_attr_map):
    if "_" in item:
        sym, para = item.split('_')
        return gdl_source[sym_to_attr_map[sym]]["cn"][0].format(*para.upper())
    return item


def parse_equation(one_part, gdl_source, sym_to_attr_map):
    i = 0
    j = 0
    parsed_s = ""
    while j < len(one_part):
        if one_part[j] in ["+", "-", "*", "/", "(", ")"]:
            parsed_s += parse_item(one_part[i:j], gdl_source, sym_to_attr_map)
            parsed_s += one_part[j]
            i = j + 1
        j += 1
    parsed_s += parse_item(one_part[i:j], gdl_source, sym_to_attr_map)
    parsed_s = parsed_s.replace("**2", "²")
    parsed_s = parsed_s.replace("*", "×")
    for tri_func in re.findall(r"[a-z]{3}\(pi×∠[A-Z]{3}/180\)", parsed_s):
        parsed_s = parsed_s.replace(tri_func, f"{tri_func[0:3]}({tri_func[7:11]})")

    return parsed_s


def split_equation(s):
    """
    Split equation to two parts:
    ll_pn-2*y-5 ==> (ll_pn, 2*y+5)
    """
    s = s[9:-1]
    left_part = ""
    right_part = ""

    parse_left_part = True
    reverse_symbol = {"+": "-", "-": "+"}
    if s[0] == "-":
        reverse_symbol["+"] = "+"
        reverse_symbol["-"] = "-"
        s = s[1:]

    for item in s:
        if item in ["+", "-"]:
            parse_left_part = False
            right_part += reverse_symbol[item]
            continue

        if parse_left_part:
            left_part += item
        else:
            right_part += item

    if len(right_part) > 0 and right_part[0] == "+":
        right_part = right_part[1:]
    if len(right_part) == 0:
        right_part = "0"

    return left_part, right_part


def inverse_parse_fl(s, language, gdl_source, sym_to_attr_map):
    if not s.startswith("Equation"):
        p_name, p_para, _ = parse_geo_predicate(s)
        parsed_s = gdl_source[p_name][language][0].format(*p_para)
    else:
        left_part, right_part = split_equation(s)
        left_part = parse_equation(left_part, gdl_source, sym_to_attr_map)
        right_part = parse_equation(right_part, gdl_source, sym_to_attr_map)
        parsed_s = f"{left_part}={right_part}"

    return parsed_s


def inverse_parse_solution(hypertree, pgdl_source_file, tgdl_source_file, language):
    predicate_gdl_source = load_json(pgdl_source_file)
    theorem_gdl_source = load_json(tgdl_source_file)

    skip_predicates = copy.copy(predicate_gdl_source["Predicates"]["Preset"]["Construction"])
    skip_predicates += predicate_gdl_source["Predicates"]["Preset"]["BasicEntity"]
    sym_to_attr_map = {}
    attr = predicate_gdl_source["Predicates"]["Attribution"]
    for attr_name in attr:
        sym_to_attr_map[attr[attr_name]["body"]["sym"]] = attr_name.split("(")[0]

    predicate_gdl_source = parse_predicate_gdl_source(predicate_gdl_source)
    theorem_gdl_source = parse_theorem_gdl_source(theorem_gdl_source)

    hypertree_inverse = {}
    for tree_id in hypertree["tree"]:
        for node in hypertree["tree"][tree_id]["conclusions"]:
            hypertree_inverse[node] = {"theorem": hypertree["tree"][tree_id]["theorem"],
                                       "conditions": hypertree["tree"][tree_id]["conditions"]}
    start_nodes = []
    for node in hypertree["nodes"]:
        if node not in hypertree_inverse and node.split("(")[0] not in skip_predicates:
            start_nodes.append(node)

    print_stack = []
    target_node = hypertree["target_node"]
    while target_node in hypertree_inverse and hypertree_inverse[target_node]["theorem"] == "extended":
        target_node = hypertree_inverse[target_node]["conditions"][0]
    traceback_stack = [target_node]
    start_nodes_used = []

    while len(traceback_stack) > 0:
        node = traceback_stack.pop()
        if node in start_nodes and node not in start_nodes_used:
            start_nodes_used.append(node)
        if node not in hypertree_inverse:
            continue

        head_nodes = []
        for head_node in hypertree_inverse[node]["conditions"]:
            while head_node in hypertree_inverse and hypertree_inverse[head_node]["theorem"] == "extended":
                head_node = hypertree_inverse[head_node]["conditions"][0]
            if head_node.split("(")[0] not in skip_predicates:
                head_nodes.append(head_node)

        traceback_stack.extend(head_nodes)
        print_stack.append([head_nodes, hypertree_inverse[node]["theorem"], node])

    start_nodes_used = start_nodes_used[::-1]
    node_map = {}  # {node_fl: [node_id, node_nl]}
    for node in start_nodes_used:
        node_map[node] = [len(node_map) + 1, inverse_parse_fl(node, language, predicate_gdl_source, sym_to_attr_map)]

    if language == "cn":
        print_text = "由题意得"
        for node in start_nodes_used:
            print_text += "，{}（{}）".format(node_map[node][1], node_map[node][0])
        print_text += "；\n"
        while len(print_stack) > 0:
            premises, theorem, conclusion = print_stack.pop()
            if conclusion in node_map:
                continue
            node_map[conclusion] = [len(node_map) + 1,
                                    inverse_parse_fl(conclusion, language, predicate_gdl_source, sym_to_attr_map)]

            theorem = theorem.split("(")[0]
            if len(premises) > 0:
                print_text += "已知条件"
                for premise in premises:
                    if premise not in node_map:
                        node_map[premise] = [len(node_map) + 1,
                                             inverse_parse_fl(premise, language, predicate_gdl_source, sym_to_attr_map)]
                    print_text += "（{}）".format(node_map[premise][0])
                print_text += "，"

            if theorem == "solve_eq":
                print_text += "计算可得"
            else:
                print_text += "由{}可得".format(theorem_gdl_source[theorem][language])
            print_text += "，{}（{}）；\n".format(node_map[conclusion][1], node_map[conclusion][0])
        print_text += "完成解题。"
    else:
        print_text = "From the conditions of the problem, we have "
        print_text += "{} ({})".format(node_map[start_nodes_used[0]][1], node_map[start_nodes_used[0]][0])
        for node in start_nodes_used[1:]:
            print_text += ", {} ({})".format(node_map[node][1], node_map[node][0])
        print_text += ";\n"

        while len(print_stack) > 0:
            premises, theorem, conclusion = print_stack.pop()
            if conclusion in node_map:
                continue
            node_map[conclusion] = [len(node_map) + 1,
                                    inverse_parse_fl(conclusion, language, predicate_gdl_source, sym_to_attr_map)]

            lines = ""
            if len(premises) > 0:
                lines += "given conditions "
                for premise in premises:
                    if premise not in node_map:
                        node_map[premise] = [len(node_map) + 1,
                                             inverse_parse_fl(premise, language, predicate_gdl_source, sym_to_attr_map)]
                    lines += "({}) ".format(node_map[premise][0])
                lines += ", "

            theorem = theorem.split("(")[0]
            if theorem == "solve_eq":
                lines += "by calculation, we have "
            else:
                lines += "by the {}, we have ".format(theorem_gdl_source[theorem][language])
            lines += "{} ({});\n".format(node_map[conclusion][1], node_map[conclusion][0])
            print_text += lines[0].upper() + lines[1:]
        print_text += "Proof completed."

    return print_text
