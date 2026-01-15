from sympy import sympify, symbols, atan, pi, log
from pprint import pprint
from graphviz import Graph
import json
import re
import time

"""↓-------------Vocabulary------------↓"""

_lu = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
       'W', 'X', 'Y', 'Z')  # latin_upper 26
_lsu = ('𝓐', '𝓑', '𝓒', '𝓓', '𝓔', '𝓕', '𝓖', '𝓗', '𝓘', '𝓙', '𝓚', '𝓛', '𝓜', '𝓝', '𝓞', '𝓟', '𝓠', '𝓡', '𝓢', '𝓣', '𝓤',
        '𝓥', '𝓦', '𝓧', '𝓨', '𝓩')  # latin_script_upper26
_ll = ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v',
       'w', 'x', 'y', 'z')  # latin_lower 26
_lsl = ('𝓪', '𝓫', '𝓬', '𝓭', '𝓮', '𝓯', '𝓰', '𝓱', '𝓲', '𝓳', '𝓴', '𝓵', '𝓶', '𝓷', '𝓸', '𝓹', '𝓺', '𝓻', '𝓼', '𝓽', '𝓾', '𝓿',
        '𝔀', '𝔁', '𝔂', '𝔃')  # latin_script_lower 26
_gu = ('Α', 'Β', 'Γ', 'Δ', 'Ε', 'Ζ', 'Η', 'Θ', 'Ι', 'Κ', 'Λ', 'Μ', 'Ν', 'Ξ', 'Ο', 'Π', 'Ρ', 'Σ', 'Σ', 'Τ', 'Υ', 'Φ',
       'Χ', 'Ψ', 'Ω')  # greek_upper 24
_giu = ('𝜜', '𝜝', '𝜞', '𝜟', '𝜠', '𝜡', '𝜢', '𝜣', '𝜤', '𝜥', '𝜦', '𝜧', '𝜨', '𝜩', '𝜪', '𝜫', '𝜬', '𝜭', '𝜮', '𝜯', '𝜰', '𝜱',
        '𝜲', '𝜳', '𝜴')  # greek_italic_upper 24
_gl = ('α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 'ν', 'ξ', 'ο', 'π', 'ρ', 'ς', 'σ', 'τ', 'υ', 'φ',
       'χ', 'ψ', 'ω')  # greek_lower 24
_gil = ('𝜶', '𝜷', '𝜸', '𝜹', '𝜺', '𝜻', '𝜼', '𝜽', '𝜾', '𝜿', '𝝀', '𝝁', '𝝂', '𝝃', '𝝄', '𝝅', '𝝆', '𝝇', '𝝈', '𝝉', '𝝊', '𝝋',
        '𝝌', '𝝍', '𝝎')  # greek_italic_lower 24

entity_letters = tuple(  # available entity letters
    list(_lu) + list(_lsu) + list(_gu) + list(_giu) + list(_ll) + list(_lsl) + list(_gl) + list(_gil)
)
expr_letters = tuple(  # letter in expr
    ['+', '-', '**', '*', '/', 'sqrt', 'atan', 'Mod', 'nums', 'pi', '(', ')'] +
    ['.dpp', '.dpl', '.dpc', '.ma', '.rc']
)
delimiter_letters = (  # letter distinguish between different part of fact and operation
    '&', '|', '~', ':',
    '<init_fact>',  # initial facts
    '<p>',  # premise
    '<o>',  # operation,
    '<c>',  # conclusion
    '<init_goal>',  # initial goals
    '<g>',  # goal
    '<s>',  # sub goal
)
theorem_letters = (  # preset theorem name
    'multiple_forms', 'auto_extend', 'solve_eq', 'same_entity_extend'
)

"""↑-------------Vocabulary------------↑"""
"""↓---------------Output--------------↓"""


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(dict_data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dict_data, f, ensure_ascii=False, indent=2)


def show_json(dict_data):
    pprint(dict_data, sort_dicts=False)


def draw_gpl(gpl_tree, save_path='./', filename='gpl', file_format='pdf'):
    dot = Graph()
    node_id_count = [0]

    def draw_one_node(tree):
        if len(tree) == 3 and tree[1] in {'&', '|'}:
            node_id = str(node_id_count[0])
            node_id_count[0] += 1
            dot.node(node_id, tree[1])
            left_node_id = draw_one_node(tree[0])
            right_node_id = draw_one_node(tree[2])
            dot.edge(node_id, left_node_id)
            dot.edge(node_id, right_node_id)
        elif len(tree) == 2 and tree[0] == '~':
            node_id = str(node_id_count[0])
            node_id_count[0] += 1
            dot.node(node_id, tree[0])
            child_node_id = draw_one_node(tree[1])
            dot.edge(node_id, child_node_id)
        else:
            node_id = str(node_id_count[0])
            node_id_count[0] += 1
            dot.node(node_id, str(tree))
        return node_id

    draw_one_node(gpl_tree)
    dot.render(save_path + filename, view=False, cleanup=True, format=file_format)


def debug_execute(func, args):
    timing = time.time()
    result = func(*args)
    msg = f"func: {func.__name__}, args: {str(args)}, return: {str(result)}, take: {round(time.time() - timing, 4)}s."
    if isinstance(result, bool):
        if result:
            print(f"\033[32m{msg}\033[0m")
        else:
            print(f"\033[31m{msg}\033[0m")
    else:
        print(msg)


"""↑---------------Output--------------↑"""
"""↓-------------Algebraic-------------↓"""

precision = 15
chop = 1e-10


def _satisfy_eq(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) == 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) == 0


def _satisfy_g(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) > 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) > 0


def _satisfy_geq(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) >= 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) >= 0


def _satisfy_l(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) < 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) < 0


def _satisfy_leq(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) <= 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) <= 0


def _satisfy_ueq(expr, sym_to_value=None):
    if sym_to_value is None:
        return expr.evalf(n=precision, chop=chop) != 0
    return expr.subs(sym_to_value).evalf(n=precision, chop=chop) != 0


_satisfy_algebraic = {'Eq': _satisfy_eq, 'G': _satisfy_g, 'Geq': _satisfy_geq,
                      'L': _satisfy_l, 'Leq': _satisfy_leq, 'Ueq': _satisfy_ueq}

negation_map = {'Eq': 'Ueq', 'G': 'Leq', 'Geq': 'L', 'L': 'Geq', 'Leq': 'G', 'Ueq': 'Eq'}

"""↑-------------Algebraic-------------↑"""
"""↓--------------Parser---------------↓"""


def parse_gdl(gdl):
    """Parse Geometry Definition Language into a usable format for <GeometricConfiguration>."""
    parsed_gdl = {
        'Entities': {
            'Point': {"paras": ("A",)},
            'Line': {"paras": ("l",)},
            'Circle': {"paras": ("O",)}
        },
        'Attributions': {},
        'Relations': {},
        'Theorems': {}
    }

    # parse Attributions
    for attr in gdl['Attributions']:
        try:
            _parse_one_attribution(attr, gdl, parsed_gdl)
        except Exception as e:
            e_msg = f"An error occurred while parsing attribution '{attr}'."
            raise Exception(e_msg) from e

    # parse Relations
    for relation in gdl['Relations']:
        try:
            _parse_one_relation(relation, gdl, parsed_gdl)
        except Exception as e:
            e_msg = f"An error occurred while parsing relation '{relation}'."
            raise Exception(e_msg) from e

    # parse Theorems
    for theorem in gdl['Theorems']:
        try:
            _parse_one_theorem(theorem, gdl, parsed_gdl)
        except Exception as e:
            e_msg = f"An error occurred while parsing theorem '{theorem}'."
            raise Exception(e_msg) from e

    return parsed_gdl


def _parse_one_attribution(attr, gdl, parsed_gdl):
    name, paras = _parse_geometric_fact(attr)

    sym = gdl['Attributions'][attr]['sym']
    if sym in parsed_gdl['Attributions']:
        e_msg = f"Conflicting symbol '{sym}' in '{parsed_gdl['Attributions'][sym]['name']}' and '{name}'."
        raise Exception(e_msg)

    geometric_constraints = _parse_geometric_constraints(gdl['Attributions'][attr]['geometric_constraints'], paras)
    _, algebraic_forms = _parse_algebraic_fact('Af(' + gdl['Attributions'][attr]['algebraic_forms'] + ')')
    multiple_forms = []
    for multiple_form in gdl['Attributions'][attr]['multiple_forms'].split('|'):
        _, multiple_form = _parse_geometric_fact(multiple_form)
        multiple_forms.append(multiple_form)

    parsed_gdl['Attributions'][sym] = {
        'name': name,
        'paras': paras,
        'multiple_forms': tuple(multiple_forms),
        'geometric_constraints': geometric_constraints,
        'algebraic_forms': algebraic_forms
    }


def _parse_one_relation(relation, gdl, parsed_gdl):
    name, paras = _parse_geometric_fact(relation)
    if name in parsed_gdl['Relations']:
        return False

    geometric_constraints = _parse_geometric_constraints(gdl['Relations'][relation]['geometric_constraints'], paras)

    algebraic_forms = _serialize_gpl(gdl['Relations'][relation]['algebraic_forms'])
    for i in range(len(algebraic_forms)):
        if algebraic_forms[i] in {'&', '|', '~', '(', ')'}:
            continue
        elif (algebraic_forms[i].startswith('Eq(') or algebraic_forms[i].startswith('G(') or
              algebraic_forms[i].startswith('Geq(') or algebraic_forms[i].startswith('L(') or
              algebraic_forms[i].startswith('Leq(') or algebraic_forms[i].startswith('Ueq(')):
            algebraic_relation, expr = _parse_algebraic_fact(algebraic_forms[i])
            if not _paras_is_consistent(algebraic_relation, expr, paras):
                raise Exception(f"'{algebraic_forms[i]}' is not consistent with relation para.")
            algebraic_forms[i] = (algebraic_relation, expr)
        else:
            predicate, instance = _parse_geometric_fact(algebraic_forms[i])
            if predicate not in parsed_gdl['Relations']:
                raise Exception(f'Dependent relation {predicate} not defined.')
            if not _paras_is_consistent(predicate, instance, paras):
                raise Exception(f"'{algebraic_forms[i]}' is not consistent with relation para.")
            replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
            for entity, entity_paras in parsed_gdl['Relations'][predicate]['geometric_constraints']:
                if (entity, _replace_instance(entity_paras, replace)) not in geometric_constraints:
                    raise Exception(f'Geometric constraints of dependent relation {predicate} not consistent.')
            algebraic_forms[i] = (predicate, instance)
    algebraic_forms = _negation_inward(_parse_gpl_to_tree(algebraic_forms))

    parsed_gdl['Relations'][name] = {
        'paras': paras,
        'geometric_constraints': geometric_constraints,
        'algebraic_forms': algebraic_forms
    }


def _parse_one_theorem(theorem, gdl, parsed_gdl):
    name, paras = _parse_geometric_fact(theorem)
    if name in parsed_gdl['Theorems']:
        raise Exception(f"Duplicate definition of theorem '{name}'.")

    geometric_constraints = set()
    premises = _serialize_gpl(gdl['Theorems'][theorem]['premises'])
    for i in range(len(premises)):
        if premises[i] in {'&', '|', '~', '(', ')'}:
            continue
        elif premises[i].startswith('Eq('):
            algebraic_relation, expr = _parse_algebraic_fact(premises[i])
            if not _paras_is_consistent(algebraic_relation, expr, paras):
                raise Exception(f"'{premises[i]}' is not consistent with theorem para.")
            premises[i] = (algebraic_relation, expr)
            geometric_constraints.update(_get_geometric_constraints(algebraic_relation, expr, parsed_gdl))
        else:
            predicate, instance = _parse_geometric_fact(premises[i])
            if predicate not in {'Line', 'Point', 'Circle'} and predicate not in parsed_gdl['Relations']:
                raise Exception(f'Dependent relation {predicate} not defined.')
            if not _paras_is_consistent(predicate, instance, paras):
                raise Exception(f"'{premises[i]}' is not consistent with relation para.")
            premises[i] = (predicate, instance)
            geometric_constraints.update(_get_geometric_constraints(predicate, instance, parsed_gdl))
    premises = _negation_inward(_parse_gpl_to_tree(premises))

    if gdl['Theorems'][theorem]['conclusion'].startswith('Eq('):
        conclusion = _parse_algebraic_fact(gdl['Theorems'][theorem]['conclusion'])
    else:
        conclusion = _parse_geometric_fact(gdl['Theorems'][theorem]['conclusion'])
    geometric_constraints.update(_get_geometric_constraints(conclusion[0], conclusion[1], parsed_gdl))

    if len(geometric_constraints) != len(paras) or set([e[1][0] for e in geometric_constraints]) != set(paras):
        raise Exception(f"Geometric constraints of premises and conclusion.")

    parsed_gdl['Theorems'][name] = {
        'paras': paras,
        'premises': premises,
        'conclusion': conclusion
    }


def _paras_is_consistent(predicate, instance, paras):
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        for sym in instance.free_symbols:
            for para in list(str(sym).split('.')[0]):
                if para not in paras:
                    return False
    else:
        for para in instance:
            if para not in paras:
                return False
    return True


def _parse_geometric_constraints(geometric_constraints, paras):
    entities = []
    entity_paras = []
    for entity in geometric_constraints.split('&'):
        entity_name, entity_para = _parse_geometric_fact(entity)
        if entity_name not in {'Point', 'Line', 'Circle'}:
            raise Exception(f"'{entity_name}' is not an valid entity used for EE Check.")
        entities.append((entity_name, entity_para))
        entity_paras.append(entity_para[0])

    if tuple(entity_paras) != paras:
        raise Exception(f"Geometric constraints {entities} does not match with the paras {paras}.")

    return tuple(entities)  # tuple of ('Point', ('A',))


def _get_geometric_constraints(predicate, instance, parsed_gdl):
    dependent_entities = []  # [('Point', ('A',))]
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        for sym in instance.free_symbols:
            entities, attr = str(sym).split('.')
            replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
            for entity, paras in parsed_gdl['Attributions'][attr]['geometric_constraints']:
                dependent_entities.append((entity, _replace_instance(paras, replace)))
    elif predicate in {'Point', 'Line', 'Circle'}:
        dependent_entities.append((predicate, instance))
    else:
        replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
        for entity, paras in parsed_gdl['Relations'][predicate]['geometric_constraints']:
            dependent_entities.append((entity, _replace_instance(paras, replace)))
    return sorted(dependent_entities)


def _parse_geometric_fact(fact):
    """Parse fact to logic form.

    Args:
        fact (str): Entity, relation, measure or theorem. Such as: 'Point(A)', 'D6(a,b,c)', 'PointOnLine(A,l)',
        'DistanceBetweenPointAndPoint(A,B)'.

    Returns:
        parsed_predicate (tuple): Predicate name and instance list. Such as: ('Point', ['A']), ('D6', ['a', 'b', 'c']),
        ('PointOnLine', ['A', 'l']), ('DistanceBetweenPointAndPoint', ['A', 'B']).
    """
    if not bool(re.match(r'^\w+\(\S(?:,\s*\S)*\)$', fact)):
        raise Exception(f"The format of '{fact}' is incorrect.")

    predicate, paras = fact.split('(')
    paras = paras[:-1].split(',')

    return predicate, tuple(paras)


def _parse_algebraic_fact(fact):
    """
    Parse an algebra constraint to logic form.

    Args:
        algebra_constraint (str): Algebra relation and expression. The components include algebra relation types,
        algebraic operations, the symbolic representations of measures and constants. Such as:
        'Eq(Sub(A.y,Add(Mul(l.k,A.x),l.b)))', 'G(Sub(Mul(Sub(C.x,B.x),Sub(A.y,B.y)),Mul(Sub(C.y,B.y),Sub(A.x,B.x))))'.

    Returns:
        parsed_algebra_constraint (tuple): Algebra relation type and instance of sympy expression. Such as:
        ('Eq', -A.x*l.k + A.y - l.b), ('G', -(A.x - B.x)*(-B.y + C.y) + (A.y - B.y)*(-B.x + C.x)).
    """
    if ' ' in fact:
        raise Exception(f"Syntax error in '{fact}': spaces are not allowed in algebra expression.")

    algebraic_relation, expr_str = fact.split("(", 1)
    expr_str = expr_str[:-1]

    if '(' not in expr_str:  # such as 'Eq(lk.ma)'
        return algebraic_relation, symbols(expr_str)

    i = 0
    j = 0
    stack = []
    while j < len(expr_str):
        if expr_str[j] == "(":
            stack.append(expr_str[i:j])
            stack.append(expr_str[j])
            i = j + 1
        elif expr_str[j] == ",":
            if i < j:
                stack.append(expr_str[i: j])
                i = j + 1
            else:
                i = i + 1
        elif expr_str[j] == ")":
            if i < j:
                stack.append(expr_str[i: j])
                i = j + 1
            else:
                i = i + 1

            paras = []
            while True:
                para = stack.pop()
                if para == "(":
                    break
                if type(para) is str:
                    if '.' in para:
                        para = symbols(para)  # symbol representation of measure
                    else:
                        para = sympify(para)  # constant
                paras.append(para)
            paras = paras[::-1]

            operation = stack.pop()

            if operation == 'Add':
                result = 0
                for l in range(len(paras)):
                    result += paras[l]
            elif operation == 'Sub':
                result = paras[0] - paras[1]
            elif operation == 'Mul':
                result = 1
                for l in range(len(paras)):
                    result *= paras[l]
            elif operation == 'Div':
                result = paras[0] / paras[1]
            elif operation == 'Pow':
                result = paras[0] ** paras[1]
            elif operation == 'SquaredNorm':  # SquaredNorm(x1,x2,y1,y2,z1,z2,...)
                result = 0
                for l in range(0, len(paras), 2):
                    result += (paras[l + 1] - paras[l]) ** 2
            elif operation == 'Ma':  # Ma(k1,k2)
                result = ((atan(paras[0]) - atan(paras[1])) * 180 / pi) % 180
            elif operation == 'Pp':  # Pp(x,y,cx,cy,r)
                result = (paras[2] - paras[0]) ** 2 + (paras[3] - paras[1]) ** 2 - paras[4] ** 2
            elif operation == 'Log':  # Log(x)
                result = log(paras[0])
            else:
                raise Exception(f"Unknown operation '{operation}' in algebra constraint '{fact}'.")

            stack.append(result)

        j = j + 1

    if len(stack) > 1:
        raise Exception(f"Syntax error in algebra constraint '{fact}': missing ')' ?")

    return algebraic_relation, stack.pop()


def _replace_instance(instance, replace):
    """Replace instances according to the replacement mapping.

    Args:
        paras (list): List of entity. Such as ['A', 'B', 'C'].
        replace (dict): Keys are the old entity and values are the new entity. Such As {'A': 'B', 'B': 'C', 'C': 'D'}.
    Returns:
        replaced_instances: Replaced instances. Such as ['B', 'C', 'D'].
    """
    return tuple([replace[entity] for entity in instance])


def _replace_expr(expr, replace):
    """Replace instances according to the replacement mapping.

    Args:
        expr (sympy_expr): instance of sympy expression. Such as -A.x*l.k + A.y - l.b.
        replace (dict): Keys are the old entity and values are the new entity. Such As {'A': 'B', 'l': 'k'}.

    Returns:
        replaced_expr: Replaced expr. Such as -B.x*k.k + B.y - k.b.
    """
    replace_old_to_temp = {}
    replace_temp_to_new = {}
    for sym_old in expr.free_symbols:
        entities_old, attr = str(sym_old).split('.')

        sym_temp = symbols("".join([e + "'" for e in entities_old]) + '.' + attr)
        replace_old_to_temp[sym_old] = sym_temp

        sym_new = symbols("".join([replace[e] for e in entities_old]) + '.' + attr)
        replace_temp_to_new[sym_temp] = sym_new

    expr = expr.subs(replace_old_to_temp).subs(replace_temp_to_new)

    return expr


def _serialize_gpl(gpl):
    """

    Args:
    gpl (str): '~(~(~A(a,b))|B(c(d,e))&~C(c))&(D)&(E|~F|G(g))'

    Returns:
    gpl_serialized (list): ['~', '(', '~', '(', '~', 'A(a,b)', ')', '|', 'B(c(d,e))', '&',
                            '~', 'C(c)', ')', '&',
                            '(', 'D', ')', '&',
                            '(', 'E', '|', '~', 'F', '|', 'G(g)', ')']
    """
    gpl_serialized = []
    head = 0
    tail = 0
    count = 0
    while tail < len(gpl):
        if gpl[tail] in {'|', '&', '~'}:
            if head < tail:
                gpl_serialized.append(gpl[head:tail])
            gpl_serialized.append(gpl[tail])
            tail += 1
            head = tail
        elif gpl[tail] == '(':
            if tail == 0 or gpl[tail - 1] in {'|', '&', '~'}:  # priority
                gpl_serialized.append(gpl[tail])
                tail += 1
                head = tail
            else:  # '(' in predicate
                count += 1
                tail += 1
        elif gpl[tail] == ')':
            if count == 1:  # last ')'
                gpl_serialized.append(gpl[head:tail + 1])
                count -= 1
                tail += 1
                head = tail
            elif count == 0:  # priority
                if head < tail:
                    gpl_serialized.append(gpl[head:tail])
                gpl_serialized.append(gpl[tail])
                tail += 1
                head = tail
            else:  # '(' in predicate
                count -= 1
                tail += 1
        else:  # letters or other symbols
            tail += 1
    if head < tail:
        raise Exception(f"Syntax error in GPL '{gpl}': missing ')' ?")

    return gpl_serialized


def _parse_gpl_to_tree(gpl_serialized):
    """

    Args:
    gpl_serialized (list): ['~', '(', '~', '(', '~', 'A(a,b)', ')', '|', 'B(c(d,e))', '&',
                            '~', 'C(c)', ')', '&',
                            '(', 'D', ')', '&',
                            '(', 'E', '|', '~', 'F', '|', 'G(g)', ')']

    Returns:
    gpl_tree (list): [['~', [['~', ['~', 'A(a,b)']], '|', ['B(c(d,e))', '&', ['~', 'C(c)']]]], '&',
                      ['D', '&', ['E', '|', [['~', 'F'], '|', 'G(g)']]]]
    """
    if len(gpl_serialized) == 0:  # empty
        return ()

    priority = 0
    priorities = []
    operator_ids = []  # & and |
    for i in range(len(gpl_serialized)):
        if gpl_serialized[i] == '(':
            priority -= 1
            priorities.append(priority)
        elif gpl_serialized[i] == ')':
            priorities.append(priority)
            priority += 1
        else:
            priorities.append(priority)

        if gpl_serialized[i] in {'&', '|'} and priority == 0:
            operator_ids.append(i)

    if len(operator_ids) > 0:  # conjunctive form (&) or disjunctive form (|)
        operator_id = operator_ids[0]
        for _id in operator_ids:
            if gpl_serialized[_id] == '|':
                operator_id = _id
                break
        # conjunctive form: [..., '&', ...] -> [_parse_gpl_to_tree(...), '&', _parse_gpl_to_tree(...)]
        # disjunctive form: [..., '|', ...] -> [_parse_gpl_to_tree(...), '|', _parse_gpl_to_tree(...)]
        return (_parse_gpl_to_tree(gpl_serialized[:operator_id]), gpl_serialized[operator_id],
                _parse_gpl_to_tree(gpl_serialized[operator_id + 1:]))

    else:  # negative form (~) or atomic form
        if gpl_serialized[0] == '(' and gpl_serialized[-1] == ')' and priorities[0] == priorities[-1]:
            # redundant '(' and ')': ['(', ..., ')'] -> _parse_gpl_to_tree(...)
            return _parse_gpl_to_tree(gpl_serialized[1:-1])
        elif len(gpl_serialized) == 1 and gpl_serialized[0] not in {'&', '|', '~', '(', ')'}:
            # atomic form: [A] -> A
            return gpl_serialized[0]
        elif len(gpl_serialized) > 1 and gpl_serialized[0] == '~':
            # negative form: ['~', ...] -> ['~', _parse_gpl_to_tree(...)]
            return '~', _parse_gpl_to_tree(gpl_serialized[1:])
        else:
            raise Exception(f"Syntax error in serialized GPL '{gpl_serialized}'.")


def _is_negation(gpl_tree):
    if isinstance(gpl_tree, tuple) and len(gpl_tree) == 2 and gpl_tree[0] == '~':
        return True
    return False


def _is_conjunction(gpl_tree):
    if isinstance(gpl_tree, tuple) and len(gpl_tree) == 3 and gpl_tree[1] == '&':
        return True
    return False


def _is_disjunction(gpl_tree):
    if isinstance(gpl_tree, tuple) and len(gpl_tree) == 3 and gpl_tree[1] == '|':
        return True
    return False


def _negation_inward(gpl_tree):
    """

    Args:
    gpl_tree (list): [['~', [['~', ['~', 'A(a,b)']], '|', ['B(c(d,e))', '&', ['~', 'C(c)']]]], '&',
                      ['D', '&', ['E', '|', [['~', 'F'], '|', 'G(g)']]]]

    Returns:
    gpl_tree_no_negation (list): [[('~', 'A(a,b)'), '&', [('~', 'B(c(d,e))'), '|', 'C(c)']], '&',
                                  ['D', '&', ['E', '|', [('~', 'F'), '|', 'G(g)']]]]
    """
    if len(gpl_tree) == 0:  # empty
        return ()

    elif _is_negation(gpl_tree):  # negative form
        if _is_negation(gpl_tree[1]):
            # merge negation: ('~', ('~', ...)) -> _negation_inward(...)
            return _negation_inward(gpl_tree[1][1])
        elif _is_conjunction(gpl_tree[1]):
            # ~ conjunction: (~, (..., '&', ...)) -> (_negation_inward(('~', ...)), '|', _negation_inward(('~', ...]))
            return _negation_inward(('~', gpl_tree[1][0])), '|', _negation_inward(('~', gpl_tree[1][2]))
        elif _is_disjunction(gpl_tree[1]):
            # ~ disjunction: (~, (..., '|', ...)) -> (_negation_inward(('~', ...)), '&', _negation_inward(('~', ...]))
            return _negation_inward(('~', gpl_tree[1][0])), '&', _negation_inward(('~', gpl_tree[1][2]))
        else:
            # negative atomic form: ('~', A) -> ('~', A)
            return gpl_tree

    elif _is_conjunction(gpl_tree):  # conjunction
        # conjunction: (..., '&', ...) -> (_negation_inward(...), '&', _negation_inward(...))
        return _negation_inward(gpl_tree[0]), '&', _negation_inward(gpl_tree[2])

    elif _is_disjunction(gpl_tree):  # disjunction
        # disjunction: (..., '|', ...) -> (_negation_inward(...), '|', _negation_inward(...))
        return _negation_inward(gpl_tree[0]), '|', _negation_inward(gpl_tree[2])

    else:  # atomic form
        # atomic form: A -> A
        return gpl_tree


def _parse_gpl_tree_to_dnf(gpl_tree):
    """

    Args:
    gpl_tree_no_negation (list): [[('~', 'A(a,b)'), '&', [('~', 'B(c(d,e))'), '|', 'C(c)']], '&',
                                  ['D', '&', ['E', '|', [('~', 'F'), '|', 'G(g)']]]]

    Returns:
    gpl_dnf (list): [[('~', 'A(a,b)'), ('~', 'B(c(d,e))'), 'D', 'E'],
                     [('~', 'A(a,b)'), ('~', 'B(c(d,e))'), 'D', ('~', 'F')],
                     [('~', 'A(a,b)'), ('~', 'B(c(d,e))'), 'D', 'G(g)'],
                     [('~', 'A(a,b)'), 'C(c)', 'D', 'E'],
                     [('~', 'A(a,b)'), 'C(c)', 'D', ('~', 'F')],
                     [('~', 'A(a,b)'), 'C(c)', 'D', 'G(g)']]
    """
    if len(gpl_tree) == 0:
        return [[]]

    elif _is_conjunction(gpl_tree):  # conjunction
        norm_form1 = _parse_gpl_tree_to_dnf(gpl_tree[0])
        norm_form2 = _parse_gpl_tree_to_dnf(gpl_tree[2])
        norm_forms = []
        for a in norm_form1:
            for b in norm_form2:
                norm_forms.append(a + b)
        # [left, '&', right] -> _parse_gpl_tree_to_dnf(left) × _parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)&(B1|B2) -> A1&B1|A1&B2|A2&B1|A2&B2
        return norm_forms

    elif _is_disjunction(gpl_tree):  # disjunction
        norm_form1 = _parse_gpl_tree_to_dnf(gpl_tree[0])
        norm_form2 = _parse_gpl_tree_to_dnf(gpl_tree[2])
        # [left, '|', right] -> _parse_gpl_tree_to_dnf(left) + _parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)|(B1|B2) -> A1|A2|B1|B2
        return norm_form1 + norm_form2

    else:  # negative form or atomic form
        # A -> [[A]]
        return [[gpl_tree]]


def _get_algebraic_forms(algebraic_forms, parsed_gdl, replace=None):
    if len(algebraic_forms) == 0:  # syntax error
        return ()

    elif _is_negation(algebraic_forms):  # negative form
        return '~', _get_algebraic_forms(algebraic_forms[1], parsed_gdl, replace)

    elif _is_conjunction(algebraic_forms):  # conjunction
        return (_get_algebraic_forms(algebraic_forms[0], parsed_gdl, replace), '&',
                _get_algebraic_forms(algebraic_forms[2], parsed_gdl, replace))

    elif _is_disjunction(algebraic_forms):  # disjunction
        return (_get_algebraic_forms(algebraic_forms[0], parsed_gdl, replace), '|',
                _get_algebraic_forms(algebraic_forms[2], parsed_gdl, replace))

    else:  # atomic form
        predicate, instance = algebraic_forms
        if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
            if replace is not None:
                instance = _replace_expr(instance, replace)
            return predicate, instance

        else:
            if replace is not None:
                instance = _replace_instance(instance, replace)
            replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
            return _get_algebraic_forms(parsed_gdl['Relations'][predicate]['algebraic_forms'], parsed_gdl, replace)


def _parse_expr_to_algebraic_forms(expr, parsed_gdl):
    attr = str(list(expr.free_symbols)[0]).split('.')[0]
    if attr in {'x', 'y', 'k', 'b', 'u', 'v', 'r'}:
        return expr

    for sym in list(expr.free_symbols):
        entities, attr = str(sym).split('.')
        replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
        sym_replace = _replace_expr(parsed_gdl['Attributions'][attr]['algebraic_forms'], replace)
        expr = expr.subs(sym, sym_replace)
    return expr


def _parse_construction(construction, parsed_gdl):
    """
    Point(C)&Line(m):PointOnLine(C,m)&~(PointOnLine(C,l)|~PointOnLine(C,n))&EqualAngle(m,l,l,n)
    """
    parsed_construction = []  # [[target_entities, dependent_entities, added_facts, equations, inequalities, values]]

    target_entities, constraints = construction.split(':')

    target_entities = target_entities.split('&')
    for i in range(len(target_entities)):
        target_entities[i] = _parse_geometric_fact(target_entities[i])
    target_entities = sorted(list(set(target_entities)))

    constraints = _serialize_gpl(constraints)
    for i in range(len(constraints)):  # parse to logic form
        if constraints[i] in {'&', '|', '~', '(', ')'}:
            continue
        if constraints[i].startswith('Eq('):  # algebraic relation
            constraints[i] = _parse_algebraic_fact(constraints[i])

        else:  # geometric relation
            constraints[i] = _parse_geometric_fact(constraints[i])

    for constraints in _parse_gpl_tree_to_dnf(_negation_inward(_parse_gpl_to_tree(constraints))):
        dependent_entities = set()
        added_facts = []
        algebraic_forms = []
        for constraint in constraints:
            negation = False
            if constraint[0] == '~':  # negation form, such as ('~', ('PointOnLine', ('C', 'a')))
                negation = True
                constraint = constraint[1]

            predicate, instance = constraint

            constraint_dependent_entities = _get_geometric_constraints(predicate, instance, parsed_gdl)

            if len(set(target_entities) & set(constraint_dependent_entities)) == 0:
                raise Exception(f"No target entity in constraints branch '{constraints}'.")
            dependent_entities.update(constraint_dependent_entities)

            if len(algebraic_forms) > 0:
                algebraic_forms.append('&')

            if not negation:
                added_facts.append(constraint)
            else:
                algebraic_forms.append('~')

            if predicate == 'Eq':
                instance = _parse_expr_to_algebraic_forms(instance, parsed_gdl)

            algebraic_forms.append((predicate, instance))

        not_target_entities = set(target_entities) - dependent_entities
        if len(not_target_entities) > 0:
            raise Exception(f"Target entity {not_target_entities} not in constraints branch '{constraints}'.")

        dependent_entities = sorted(list(dependent_entities - set(target_entities)))
        # algebraic_forms = _parse_gpl_to_tree(algebraic_forms)
        # draw_gpl(algebraic_forms, filename='algebraic_forms')
        algebraic_forms = _negation_inward(_get_algebraic_forms(_parse_gpl_to_tree(algebraic_forms), parsed_gdl))
        for algebraic_forms_dnf in _parse_gpl_tree_to_dnf(algebraic_forms):
            equations = set()
            inequalities = set()
            for algebraic_form in algebraic_forms_dnf:
                if algebraic_form[0] == '~':
                    algebraic_relation, expr = algebraic_form[1]
                    algebraic_relation = negation_map[algebraic_relation]
                else:
                    algebraic_relation, expr = algebraic_form
                if algebraic_relation == 'Eq':
                    equations.add(expr.subs(_find_mod(expr)))
                else:
                    inequalities.add((algebraic_relation, expr))
            equations = sorted(list(equations), key=str)
            inequalities = sorted(list(inequalities), key=str)

            parsed_construction.append([target_entities, dependent_entities,
                                        added_facts, equations, inequalities, None])

    return parsed_construction  # [[target_entities, dependent_entities, added_facts, equations, inequalities, values]]


def _find_mod(expr, replace=None):
    if replace is None:
        replace = dict()
    if type(expr).__name__ == 'Mod':
        replace[expr] = expr.args[0]
    else:
        for arg in expr.args:
            _find_mod(arg, replace)
    return replace


def _parse_theorem(theorem, parsed_gdl):
    if '(' not in theorem:
        theorem_name = theorem
        theorem_paras = None
    else:
        theorem_name, theorem_paras = _parse_geometric_fact(theorem)

    if theorem_name not in parsed_gdl['Theorems']:
        raise Exception(f"Theorem '{theorem_name}' not defined in GDL.")
    if theorem_paras is not None and len(theorem_paras) != len(parsed_gdl['Theorems'][theorem_name]['paras']):
        raise Exception(f"Incorrect number of paras in theorem '{theorem}'.")

    return theorem_name, theorem_paras


def _parse_goal(goal):
    goal_serialized = _serialize_gpl(goal)

    for i in range(len(goal_serialized)):
        if goal_serialized[i] in {'&', '|', '~', '(', ')'}:
            continue

        if goal_serialized[i].startswith('Eq('):
            algebraic_relation, expr = _parse_algebraic_fact(goal_serialized[i])
            goal_serialized[i] = (algebraic_relation, expr)
        else:
            goal_serialized[i] = _parse_geometric_fact(goal_serialized[i])

    goal_tree = _negation_inward(_parse_gpl_to_tree(goal_serialized))

    return goal_tree


def _format_ids(ids):
    if len(ids) > 5:
        return '{' + ','.join([str(_id) for _id in sorted(list(ids))[:5]]) + ',...}'
    else:
        return '{' + ','.join([str(_id) for _id in sorted(list(ids))]) + '}'


def _anti_parse_operation(operation):
    operation_type, operation_predicate, operation_instance = operation
    if operation_type == 'construction':
        return 'Construct: ' + operation_predicate + ':' + operation_instance
    elif operation_type == 'auto':
        return 'Auto: ' + operation_predicate
    elif operation_type == 'apply':
        return 'Apply: ' + operation_predicate + '(' + ','.join(operation_instance) + ')'
    elif operation_type == 'decompose':
        return 'Decompose: ' + operation_predicate + '(' + ','.join(operation_instance) + ')'
    else:
        raise Exception(f"Unknown operation type '{operation_type}'.")


def _anti_parse_fact(fact):
    predicate, instance = fact
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        return f"{predicate}({str(instance).replace(' ', '')})"
    else:
        return f"{predicate}({','.join(instance)})"


def _serialize_fact(predicate, instance):
    if predicate == 'Eq':
        serialized_expr = ['Eq']
        expr = str(instance).replace(' ', '')  # remove ' '

        for matched in re.findall(r'\d+\.*\d*', expr):  # replace number with 'nums'
            expr = expr.replace(matched, 'nums', 1)

        i = 0
        while i < len(expr):  # serialize
            added = False
            for matched_part in expr_letters:  # expr letters
                if expr[i:].startswith(matched_part):
                    serialized_expr.append(matched_part)
                    i = i + len(matched_part)
                    added = True
                    break
            if not added:  # entity letters
                serialized_expr.append(expr[i])
                i = i + 1
        return serialized_expr
    else:
        return [predicate] + list(instance)


def _serialize_operation(operation):
    operation_type, operation_predicate, operation_instance = operation
    parsed_operation = []
    if operation_type == 'construction':
        for target_entity in operation_predicate.split('&'):
            if len(parsed_operation) != 0:
                parsed_operation.append('&')
            predicate, instance = _parse_geometric_fact(target_entity)
            parsed_operation.extend(_serialize_fact(predicate, instance))
        parsed_operation.append(':')
        for item in _serialize_gpl(operation_instance):
            if item in {'&', '|', '~', '(', ')'}:
                parsed_operation.append(item)
            else:
                if item.startswith('Eq('):
                    predicate, instance = _parse_algebraic_fact(item)
                else:
                    predicate, instance = _parse_geometric_fact(item)
                parsed_operation.extend(_serialize_fact(predicate, instance))
        return parsed_operation
    elif operation_type == 'auto':
        return [operation_predicate]
    elif operation_type == 'apply':
        return [operation_predicate] + list(operation_instance)
    elif operation_type == 'decompose':
        return [operation_predicate] + list(operation_instance)
    else:
        raise Exception(f"Unknown operation type '{operation_type}'.")


def _serialize_goal(gc, sub_goal_id_tree):
    if _is_negation(sub_goal_id_tree):
        return ['~'] + _serialize_goal(gc, sub_goal_id_tree[1])
    elif _is_conjunction(sub_goal_id_tree):
        left_side = _serialize_goal(gc, sub_goal_id_tree[0])
        right_side = _serialize_goal(gc, sub_goal_id_tree[2])
        return left_side + ['&'] + right_side
    elif _is_disjunction(sub_goal_id_tree):
        left_side = _serialize_goal(gc, sub_goal_id_tree[0])
        right_side = _serialize_goal(gc, sub_goal_id_tree[2])
        return ['('] + left_side + ['|'] + right_side + [')']
    else:
        predicate, instance, _ = gc.sub_goals[sub_goal_id_tree]
        return _serialize_fact(predicate, instance)


"""↑---------------Parser--------------↑"""
