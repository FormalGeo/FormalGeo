from sympy import sympify, symbols, atan, pi, log
import json
import matplotlib
import matplotlib.pyplot as plt
import re
from pprint import pprint
from graphviz import Digraph, Graph

matplotlib.use('TkAgg')  # Resolve backend compatibility issues
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # Use Microsoft YaHei font
plt.rcParams['axes.unicode_minus'] = False  # Fix negative sign display issues

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
expr_letters = (  # letter in expr
    '+', '-', '**', '*', '/', 'sqrt', 'atan', 'Mod',
    'nums', 'pi',
    '(', ')'
)
delimiter_letters = (  # letter distinguish between different part of fact and operation
    '&', '|', '~', ':',
    '<p>',  # premise
    '<cons>',  # construction,
    '<t>',  # theorem
    '<c>',  # conclusion
)
theorem_letters = (  # preset theorem name
    'multiple_forms', 'auto_extend', 'solve_eq', 'same_entity_extend'
)

"""↑-------------Vocabulary------------↑"""
"""↓-------------Algebraic-------------↓"""

precision = 20
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


satisfy_algebraic = {'Eq': _satisfy_eq, 'G': _satisfy_g, 'Geq': _satisfy_geq,
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
        name, paras = parse_geometric_fact(attr)

        sym = gdl['Attributions'][attr]['sym']
        if sym in parsed_gdl['Attributions']:
            e_msg = f"Conflicting symbol '{sym}' in '{parsed_gdl['Attributions'][sym]['name']}' and '{name}'."
            raise Exception(e_msg)

        geometric_constraints = _parse_geometric_constraints(gdl['Attributions'][attr]['geometric_constraints'], paras)
        _, algebraic_forms = parse_algebraic_fact('Af(' + gdl['Attributions'][attr]['algebraic_forms'] + ')')

        parsed_gdl['Attributions'][sym] = {
            'name': name,
            'paras': paras,
            'geometric_constraints': geometric_constraints,
            'algebraic_forms': algebraic_forms
        }

    # parse Relations
    for relation in gdl['Relations']:
        name, paras = parse_geometric_fact(relation)
        if name in parsed_gdl['Relations']:
            raise Exception(f"Duplicate definition of relation '{name}'.")

        geometric_constraints = _parse_geometric_constraints(gdl['Relations'][relation]['geometric_constraints'], paras)
        algebraic_forms = serialize_gpl(gdl['Relations'][relation]['algebraic_forms'])
        for i in range(len(algebraic_forms)):
            if algebraic_forms[i] not in {'&', '|', '~', '(', ')'}:
                algebraic_forms[i] = parse_algebraic_fact(algebraic_forms[i])

        parsed_gdl['Relations'][name] = {
            'paras': paras,
            'geometric_constraints': geometric_constraints,
            'algebraic_forms': tuple(algebraic_forms)
        }

    # parse Theorems
    for theorem in gdl['Theorems']:
        name, paras = parse_geometric_fact(theorem)
        if name in parsed_gdl['Theorems']:
            raise Exception(f"Duplicate definition of theorem '{name}'.")

        premises = serialize_gpl(gdl['Theorems'][theorem]['premises'])
        algebraic_forms = []
        for i in range(len(premises)):
            if premises[i] in {'&', '|', '~', '(', ')'}:
                algebraic_forms.append(premises[i])
            else:
                if premises[i].startswith('Eq('):  # algebraic relation
                    algebraic_relation, expr = parse_algebraic_fact(premises[i])
                    premises[i] = (algebraic_relation, expr)
                else:  # geometric relation
                    premises[i] = parse_geometric_fact(premises[i])
                algebraic_forms.extend(_parse_algebraic_forms(premises[i][0], premises[i][1], parsed_gdl))

        if gdl['Theorems'][theorem]['conclusion'].startswith('Eq('):
            conclusion = parse_algebraic_fact(gdl['Theorems'][theorem]['conclusion'])
        else:
            conclusion = parse_geometric_fact(gdl['Theorems'][theorem]['conclusion'])

        algebraic_forms = ['('] + algebraic_forms + [')', '&']
        algebraic_forms.extend(_parse_algebraic_forms(conclusion[0], conclusion[1], parsed_gdl))

        premises = parse_gpl_to_tree(premises)
        premises = negation_inward(premises)
        premises = _format_premises(premises)

        algebraic_forms = parse_gpl_to_tree(algebraic_forms)
        algebraic_forms = negation_inward(algebraic_forms)
        algebraic_forms = _format_algebraic_forms(algebraic_forms, parsed_gdl, add_dependent=True)

        parsed_gdl['Theorems'][name] = {
            'paras': paras,
            'algebraic_forms': algebraic_forms,
            'premises': premises,
            'conclusion': conclusion
        }

    return parsed_gdl


def _parse_geometric_constraints(geometric_constraints, paras):
    entities = []
    entity_paras = []
    for entity in geometric_constraints.split('&'):
        entity_name, entity_para = parse_geometric_fact(entity)
        if entity_name not in {'Point', 'Line', 'Circle'}:
            raise Exception(f"'{entity_name}' is not an valid entity used for EE Check.")
        entities.append((entity_name, entity_para))
        entity_paras.append(entity_para[0])

    if tuple(entity_paras) != paras:
        raise Exception(f"Geometric constraints {entities} does not match with the paras {paras}.")

    return tuple(entities)


def _parse_algebraic_forms(predicate, instance, parsed_gdl):
    if predicate == 'Eq':  # algebraic relation
        for sym in list(instance.free_symbols):
            entities, attr = str(sym).split('.')
            replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
            sym_replace = replace_expr(parsed_gdl['Attributions'][attr]['algebraic_forms'], replace)
            instance = instance.subs(sym, sym_replace)
        return [('Eq', instance)]
    else:  # geometric relation
        replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
        algebraic_forms = list(parsed_gdl['Relations'][predicate]['algebraic_forms'])
        for j in range(len(algebraic_forms)):
            if algebraic_forms[j] in {'&', '|', '~', '(', ')'}:
                continue
            expr = replace_expr(algebraic_forms[j][1], replace)
            algebraic_forms[j] = (algebraic_forms[j][0], expr)
        if len(algebraic_forms) > 1:
            return ['('] + algebraic_forms + [')']
        return algebraic_forms


def _format_premises(premises):
    """Remove negation nodes, because we determine the negation phase using algebraic forms and assume that negation
    nodes in premises are always true."""
    if len(premises) == 0:  # syntax error
        raise Exception(f"Syntax error in premises '{premises}'.")
    elif not isinstance(premises, list):  # atomic form
        if premises[0] == '~':
            return None
        else:
            return premises
    elif len(premises) == 3 and premises[1] == '&':  # conjunction
        left = _format_premises(premises[0])
        right = _format_premises(premises[2])
        if left is None and right is None:
            return None
        elif left is None and right is not None:
            return right
        elif left is not None and right is None:
            return left
        else:
            return left, '&', right

    elif len(premises) == 3 and premises[1] == '|':  # disjunction
        left = _format_premises(premises[0])
        right = _format_premises(premises[2])
        if left is None or right is None:
            return None
        else:
            return left, '|', right
    else:
        raise Exception(f"Syntax error in premises '{premises}'.")


def _format_algebraic_forms(algebraic_forms, parsed_gdl, add_dependent=False):
    """Substitute algebraic relations (e.g., replace ('~', 'Eq') with 'Ueq') and parse dependent entities."""
    if len(algebraic_forms) == 0:  # syntax error
        raise Exception(f"Syntax error in algebraic_forms '{algebraic_forms}'.")

    elif not isinstance(algebraic_forms, list):  # atomic form
        if algebraic_forms[0] == '~':
            algebraic_relation = negation_map[algebraic_forms[1][0]]
            expr = algebraic_forms[1][1]
        else:
            algebraic_relation, expr = algebraic_forms

        if not add_dependent:
            return algebraic_relation, expr
        dependent_entities = {}
        for entity_type, para in parse_dependent_entities(algebraic_relation, expr, parsed_gdl):
            dependent_entities[para[0]] = entity_type
        return algebraic_relation, expr, dependent_entities

    elif len(algebraic_forms) == 3 and algebraic_forms[1] in {'&', '|'}:  # conjunction or disjunction
        result = [_format_algebraic_forms(algebraic_forms[0], parsed_gdl, add_dependent), algebraic_forms[1],
                  _format_algebraic_forms(algebraic_forms[2], parsed_gdl, add_dependent)]

        if not add_dependent:
            return result
        return tuple(result)

    else:
        raise Exception(f"Syntax error in algebraic_forms '{algebraic_forms}'.")


def parse_geometric_fact(fact):
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


def parse_algebraic_fact(fact):
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
        return algebraic_relation, symbols(expr_str, real=True)

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
                        para = symbols(para, real=True)  # symbol representation of measure
                    else:
                        para = sympify(para)  # constant
                paras.append(para)
            paras = paras[::-1]

            operation = stack.pop()

            if operation == 'Add':
                result = paras[0]
                for p in paras[1:]:
                    result += p
            elif operation == 'Sub':
                result = paras[0] - paras[1]
            elif operation == 'Mul':
                result = paras[0]
                for p in paras[1:]:
                    result *= p
            elif operation == 'Div':
                result = paras[0] / paras[1]
            elif operation == 'Pow':
                result = paras[0] ** paras[1]
            elif operation == 'Norm':  # Norm(x1,y1,x2,y2)
                result = (paras[2] - paras[0]) ** 2 + (paras[3] - paras[1]) ** 2
            elif operation == 'Ma':  # Ma(k1,k2)
                result = (atan(paras[0]) - atan(paras[1])) * 180 / pi
            elif operation == 'Mma':  # Mma(k1,k2)
                result = ((atan(paras[0]) - atan(paras[1])) * 180 / pi + 180) % 180
            elif operation == 'Log':  # Log(x)
                result = log(paras[0])
            else:
                raise Exception(f"Unknown operation '{operation}' in algebra constraint '{fact}'.")

            stack.append(result)

        j = j + 1

    if len(stack) > 1:
        raise Exception(f"Syntax error in algebra constraint '{fact}': missing ')' ?")

    return algebraic_relation, stack.pop()


def replace_instance(instance, replace):
    """Replace instances according to the replacement mapping.

    Args:
        paras (list): List of entity. Such as ['A', 'B', 'C'].
        replace (dict): Keys are the old entity and values are the new entity. Such As {'A': 'B', 'B': 'C', 'C': 'D'}.
    Returns:
        replaced_instances: Replaced instances. Such as ['B', 'C', 'D'].
    """
    return [replace[entity] for entity in instance]


def replace_expr(expr, replace):
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


def serialize_gpl(gpl):
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


def parse_gpl_to_tree(gpl_serialized):
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
    if len(gpl_serialized) == 0:
        raise Exception(f"Syntax error in serialized GPL '{gpl_serialized}'.")

    priority = 0
    priorities = []
    operators = []  # & and |
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
            operators.append(i)

    if len(operators) > 0:  # conjunctive form (&) or disjunctive form (|)
        for i in operators:
            if gpl_serialized[i] != '|':
                continue
            # disjunctive form: [..., '|', ...] -> [parse_gpl_to_tree(...), '|', parse_gpl_to_tree(...)]
            return [parse_gpl_to_tree(gpl_serialized[:i]), '|', parse_gpl_to_tree(gpl_serialized[i + 1:])]
        # conjunctive form: [..., '&', ...] -> [parse_gpl_to_tree(...), '&', parse_gpl_to_tree(...)]
        return [parse_gpl_to_tree(gpl_serialized[:operators[0]]), '&',
                parse_gpl_to_tree(gpl_serialized[operators[0] + 1:])]

    else:  # negative form (~) or atomic form
        if gpl_serialized[0] == '(' and gpl_serialized[-1] == ')' and priorities[0] == priorities[-1]:
            # redundant '(' and ')': ['(', ..., ')'] -> parse_gpl_to_tree(...)
            return parse_gpl_to_tree(gpl_serialized[1:-1])
        elif len(gpl_serialized) == 1 and gpl_serialized[0] not in {'&', '|', '~', '(', ')'}:
            # atomic form: [A] -> A
            return gpl_serialized[0]
        elif (len(gpl_serialized) == 2 and
              gpl_serialized[0] == '~' and gpl_serialized[1] not in {'&', '|', '~', '(', ')'}):
            # negative atomic form: ['~', A] -> ['~', A]
            return gpl_serialized
        elif (gpl_serialized[0] == '~' and
              gpl_serialized[1] == '(' and gpl_serialized[-1] == ')' and priorities[1] == priorities[-1]):
            # negative form: ['~', '(', ..., ')'] -> ['~', parse_gpl_to_tree(...)]
            return ['~', parse_gpl_to_tree(gpl_serialized[2:-1])]
        else:
            raise Exception(f"Syntax error in serialized GPL '{gpl_serialized}'.")


def negation_inward(gpl_tree):
    """

    Args:
    gpl_tree (list): [['~', [['~', ['~', 'A(a,b)']], '|', ['B(c(d,e))', '&', ['~', 'C(c)']]]], '&',
                      ['D', '&', ['E', '|', [['~', 'F'], '|', 'G(g)']]]]

    Returns:
    gpl_tree_no_negation (list): [[('~', 'A(a,b)'), '&', [('~', 'B(c(d,e))'), '|', 'C(c)']], '&',
                                  ['D', '&', ['E', '|', [('~', 'F'), '|', 'G(g)']]]]
    """
    if len(gpl_tree) == 0:  # syntax error
        raise Exception(f"Syntax error in tree GPL '{gpl_tree}'.")

    elif not isinstance(gpl_tree, list):  # atomic form
        # atomic form: A -> A
        return gpl_tree

    elif len(gpl_tree) == 2:  # negative form
        if not isinstance(gpl_tree[1], list):
            # negative atomic form: ['~', A] -> ('~', A)
            return '~', gpl_tree[1]
        elif len(gpl_tree[1]) == 2:
            # merge negation: ['~', ['~', ...]] -> negation_inward(...)
            return negation_inward(gpl_tree[1][1])
        elif len(gpl_tree[1]) == 3 and gpl_tree[1][1] == '&':
            # ~ conjunction: [~, [..., '&', ...]] -> [negation_inward(['~', ...]), '|', negation_inward(['~', ...])]
            return [negation_inward(['~', gpl_tree[1][0]]), '|', negation_inward(['~', gpl_tree[1][2]])]
        elif len(gpl_tree[1]) == 3 and gpl_tree[1][1] == '|':
            # ~ disjunction: [~, [..., '|', ...]] -> [negation_inward(['~', ...]), '&', negation_inward(['~', ...])]
            return [negation_inward(['~', gpl_tree[1][0]]), '&', negation_inward(['~', gpl_tree[1][2]])]
        else:
            raise Exception(f"Syntax error in tree GPL '{gpl_tree}'.")

    elif len(gpl_tree) == 3 and gpl_tree[1] == '&':
        # conjunction: [..., '&', ...] -> [negation_inward(...), '&', negation_inward(...)]
        return [negation_inward(gpl_tree[0]), '&', negation_inward(gpl_tree[2])]

    elif len(gpl_tree) == 3 and gpl_tree[1] == '|':
        # disjunction: [..., '|', ...] -> [negation_inward(...), '|', negation_inward(...)]
        return [negation_inward(gpl_tree[0]), '|', negation_inward(gpl_tree[2])]

    else:
        raise Exception(f"Syntax error in tree GPL '{gpl_tree}'.")


def parse_gpl_tree_to_dnf(gpl_tree_no_negation):
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
    if len(gpl_tree_no_negation) == 0:
        raise Exception(f"Syntax error in tree GPL '{gpl_tree_no_negation}'.")

    elif len(gpl_tree_no_negation) == 3 and gpl_tree_no_negation[1] == '&':  # conjunction
        norm_form1 = parse_gpl_tree_to_dnf(gpl_tree_no_negation[0])
        norm_form2 = parse_gpl_tree_to_dnf(gpl_tree_no_negation[2])
        norm_forms = []
        for a in norm_form1:
            for b in norm_form2:
                norm_forms.append(a + b)
        # [left, '&', right] -> parse_gpl_tree_to_dnf(left) × parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)&(B1|B2) -> A1&B1|A1&B2|A2&B1|A2&B2
        return norm_forms

    elif len(gpl_tree_no_negation) == 3 and gpl_tree_no_negation[1] == '|':  # disjunction
        norm_form1 = parse_gpl_tree_to_dnf(gpl_tree_no_negation[0])
        norm_form2 = parse_gpl_tree_to_dnf(gpl_tree_no_negation[2])
        # [left, '|', right] -> parse_gpl_tree_to_dnf(left) + parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)|(B1|B2) -> A1|A2|B1|B2
        return norm_form1 + norm_form2

    else:  # atomic form
        # A -> [[A]]
        return [[gpl_tree_no_negation]]


def parse_dependent_entities(predicate, instance, parsed_gdl):
    dependent_entities = []
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        for sym in instance.free_symbols:
            entities, attr = str(sym).split('.')
            replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
            for entity, paras in parsed_gdl['Attributions'][attr]['geometric_constraints']:
                dependent_entities.append((entity, tuple(replace_instance(paras, replace))))
    else:
        replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
        for entity, paras in parsed_gdl['Relations'][predicate]['geometric_constraints']:
            dependent_entities.append((entity, tuple(replace_instance(paras, replace))))

    return sorted(dependent_entities)


def parse_construction(construction, parsed_gdl):
    """
    Point(C)&Line(m):PointOnLine(C,m)&~(PointOnLine(C,l)|~PointOnLine(C,n))&EqualAngle(m,l,l,n)
    """
    parsed_construction = []  # (target_entities, dependent_entities, equations, inequalities, added_facts)

    target_entities, constraints = construction.split(':')

    target_entities = target_entities.split('&')
    for i in range(len(target_entities)):
        target_entities[i] = parse_geometric_fact(target_entities[i])
    target_entities = sorted(list(set(target_entities)))

    constraints = serialize_gpl(constraints)
    for i in range(len(constraints)):  # parse to logic form
        if constraints[i] in {'&', '|', '~', '(', ')'}:
            continue

        if constraints[i].startswith('Eq('):  # algebraic relation
            constraints[i] = parse_algebraic_fact(constraints[i])
        else:  # geometric relation
            constraints[i] = parse_geometric_fact(constraints[i])

    for constraints in parse_gpl_tree_to_dnf(negation_inward(parse_gpl_to_tree(constraints))):
        dependent_entities = set()
        added_facts = []

        algebraic_forms = []
        for constraint in constraints:
            negation = False
            if constraint[0] == '~':  # negation form, such as ('~', ('PointOnLine', ('C', 'a')))
                negation = True
                constraint = constraint[1]

            if constraint in added_facts:
                continue

            predicate, instance = constraint

            constraint_dependent_entities = parse_dependent_entities(predicate, instance, parsed_gdl)
            if len(set(target_entities) & set(constraint_dependent_entities)) == 0:
                raise Exception(f"No target entity in constraints branch '{constraints}'.")
            dependent_entities.update(constraint_dependent_entities)

            constraint_algebraic_forms = _parse_algebraic_forms(predicate, instance, parsed_gdl)

            if len(algebraic_forms) > 0 and len(constraint_algebraic_forms) > 0:
                algebraic_forms.append('&')

            if not negation:
                added_facts.append(constraint)
            else:
                algebraic_forms.append('~')
            algebraic_forms.extend(_parse_algebraic_forms(predicate, instance, parsed_gdl))

        dependent_entities = sorted(list(dependent_entities))

        algebraic_forms = _format_algebraic_forms(negation_inward(parse_gpl_to_tree(algebraic_forms)), parsed_gdl)
        for algebraic_forms_dnf in parse_gpl_tree_to_dnf(algebraic_forms):
            equations = set()
            inequalities = set()
            for algebraic_relation, expr in algebraic_forms_dnf:
                if algebraic_relation == 'Eq':
                    equations.add(expr)
                else:
                    inequalities.add((algebraic_relation, expr))
            equations = list(equations)
            inequalities = list(inequalities)

            parsed_construction.append((target_entities, dependent_entities, equations, inequalities, added_facts))

    return parsed_construction


def parse_theorem(theorem, parsed_gdl):
    if '(' not in theorem:
        theorem_name, theorem_paras = parse_geometric_fact(theorem)
    else:
        theorem_name = theorem
        theorem_paras = None

    if theorem_name not in parsed_gdl['Theorems']:
        raise Exception(f"Theorem '{theorem_name}' not defined in GDL.")
    if theorem_paras is not None and len(theorem_paras) != len(parsed_gdl['Theorems'][theorem_name]['paras']):
        raise Exception(f"Incorrect number of paras in theorem '{theorem}'.")

    return theorem_name, theorem_paras


"""↑---------------Parser--------------↑"""
"""↓---------------Output--------------↓"""


def load_json(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(dict_data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(dict_data, f, ensure_ascii=False, indent=2)


def show_json(dict_data):
    pprint(dict_data, sort_dicts=False, compact=True)


def draw_gpl(gpl_tree, filename):
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
        else:
            node_id = str(node_id_count[0])
            node_id_count[0] += 1
            dot.node(node_id, str(tree))
        return node_id

    draw_one_node(gpl_tree)
    dot.render(filename, view=True, cleanup=True)


def show_gc(gc, target=None):
    operation_ids = set()
    used_operation_ids = []
    used_premise_ids = []
    if target is not None:
        if target.startswith('Eq('):
            predicate = 'Equation'
            _, instance = parse_algebraic_fact(target)
            if str(instance)[0] == '-':
                instance = -instance
        else:
            predicate, instance = parse_geometric_fact(target)

        if (predicate, instance) in gc.id:
            used_premise_ids.append(gc.id[(predicate, instance)])

        i = 0
        while i < len(used_premise_ids):
            for fact_id in gc.facts[used_premise_ids[i]][2]:
                if fact_id in used_premise_ids:
                    continue
                used_premise_ids.append(fact_id)
            if gc.facts[used_premise_ids[i]][4] not in used_operation_ids:
                used_operation_ids.append(gc.facts[used_premise_ids[i]][4])
            i += 1

    entity_print_format = '{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}{5:<30}'
    relation_print_format = '{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}'
    equation_print_format = "{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}"
    sym_print_format = '{0:<6}{1:<25}{2:<25}{3:<6}'
    operation_print_format = '{0:<6}{1:<50}'

    entity_print_format_used = '\033[35m{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}{5:<30}\033[0m'
    relation_print_format_used = '\033[35m{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}\033[0m'
    equation_print_format_used = '\033[35m{0:<6}{1:<15}{2:<60}{3:<60}{4:<6}\033[0m'
    operation_print_format_used = '\033[35m{0:<6}{1:<50}\033[0m'

    print("\033[33mConstructions:\033[0m")
    for operation_id in gc.constructions:
        print('{0:<4}{1:<40}'.format(operation_id, gc.operations[operation_id]))
        implicit_entities = [f'{p}({i})' for p, i in gc.constructions[operation_id][0]]
        print(f'    target entities: {implicit_entities}')
        implicit_entities = [f'{p}({i})' for p, i in gc.constructions[operation_id][1]]
        print(f'    implicit entities: {implicit_entities}')
        dependent_entities = [f'{p}({i})' for p, i in gc.constructions[operation_id][2]]
        print(f'    dependent entities: {dependent_entities}')
        print(f"    constraints: {str(gc.constructions[operation_id][3]).replace(' ', '')}")
    print()

    print('\033[33mEntities:\033[0m')
    for entity in ['Point', 'Line', 'Circle']:
        if len(gc.ids_of_predicate[entity]) == 0:
            continue
        print(f'{entity}:')
        for fact_id in gc.ids_of_predicate[entity]:
            operation_ids.add(gc.facts[fact_id][4])
            if entity == 'Point':
                values = [(round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.x')]), 4),
                           round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.y')]), 4))]
            elif entity == 'Line':
                values = [(round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.k')]), 4),
                           round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.b')]), 4))]
            else:
                values = [(round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.cx')]), 4),
                           round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.cy')]), 4),
                           round(float(gc.value_of_para_sym[symbols(f'{gc.facts[fact_id][1][0]}.r')]), 4))]
            if fact_id in used_premise_ids:
                print(entity_print_format_used.format(
                    fact_id,
                    gc.facts[fact_id][1][0],
                    str(gc.facts[fact_id][2]).replace(' ', ''),
                    str(gc.facts[fact_id][3]).replace(' ', ''),
                    gc.facts[fact_id][4],
                    str(values).replace(' ', '')
                ))
            else:
                print(entity_print_format.format(
                    fact_id,
                    gc.facts[fact_id][1][0],
                    str(gc.facts[fact_id][2]).replace(' ', ''),
                    str(gc.facts[fact_id][3]).replace(' ', ''),
                    gc.facts[fact_id][4],
                    str(values).replace(' ', '')
                ))
    print()

    print("\033[33mRelations:\033[0m")
    for predicate in gc.ids_of_predicate:
        if len(gc.ids_of_predicate[predicate]) == 0:
            continue
        if predicate in ['Point', 'Line', 'Circle', 'Equation']:
            continue
        print(f"{predicate}:")
        for fact_id in gc.ids_of_predicate[predicate]:
            operation_ids.add(gc.facts[fact_id][4])
            if fact_id in used_premise_ids:
                print(relation_print_format_used.format(
                    fact_id,
                    ','.join(gc.facts[fact_id][1]),
                    str(gc.facts[fact_id][2]).replace(' ', ''),
                    str(gc.facts[fact_id][3]).replace(' ', ''),
                    gc.facts[fact_id][4]
                ))
            else:
                print(relation_print_format.format(
                    fact_id,
                    ','.join(gc.facts[fact_id][1]),
                    str(gc.facts[fact_id][2]).replace(' ', ''),
                    str(gc.facts[fact_id][3]).replace(' ', ''),
                    gc.facts[fact_id][4]
                ))
    print()

    print("\033[33mEquations:\033[0m")
    for fact_id in gc.ids_of_predicate['Equation']:
        operation_ids.add(gc.facts[fact_id][4])
        if fact_id in used_premise_ids:
            print(equation_print_format_used.format(
                fact_id,
                str(gc.facts[fact_id][1]).replace(' ', ''),
                str(gc.facts[fact_id][2]).replace(' ', ''),
                str(gc.facts[fact_id][3]).replace(' ', ''),
                gc.facts[fact_id][4]
            ))
        else:
            print(equation_print_format.format(
                fact_id,
                str(gc.facts[fact_id][1]).replace(' ', ''),
                str(gc.facts[fact_id][2]).replace(' ', ''),
                str(gc.facts[fact_id][3]).replace(' ', ''),
                gc.facts[fact_id][4]
            ))
    print()

    print("\033[33mSymbols and Values:\033[0m")
    for sym in gc.value_of_attr_sym:
        equation_id = gc.id['Equation', sym - gc.value_of_attr_sym[sym]]
        predicate = gc.parsed_gdl['sym_to_measure'][str(sym).split('.')[1]]
        instance = ",".join(list(str(sym).split('.')[0]))
        print(sym_print_format.format(
            equation_id,
            f"{predicate}({instance})",
            str(sym),
            str(gc.value_of_attr_sym[sym])
        ))
    print()

    print("\033[33mOperations:\033[0m")
    for operation_id in range(len(gc.operations)):
        if operation_id not in operation_ids:
            continue
        if operation_id in used_operation_ids:
            print(operation_print_format_used.format(
                operation_id,
                f'{gc.operations[operation_id]}'
            ))
        else:
            print(operation_print_format.format(
                operation_id,
                f'{gc.operations[operation_id]}'
            ))
    print()


def draw_gc(gc, filename):
    _, ax = plt.subplots()
    ax.axis('equal')  # maintain the circle's aspect ratio
    ax.axis('off')  # hide the axes
    middle_x = (gc.range['x_max'] + gc.range['x_min']) / 2
    range_x = (gc.range['x_max'] - gc.range['x_min']) / 2 * gc.rate
    middle_y = (gc.range['y_max'] + gc.range['y_min']) / 2
    range_y = (gc.range['y_max'] - gc.range['y_min']) / 2 * gc.rate
    ax.set_xlim(float(middle_x - range_x), float(middle_x + range_x))
    ax.set_ylim(float(middle_y - range_y), float(middle_y + range_y))

    for line in gc.instances_of_predicate['Line']:
        k = float(gc.value_of_para_sym[symbols(f'{line[0]}.k')])
        b = float(gc.value_of_para_sym[symbols(f'{line[0]}.b')])
        ax.axline((0, b), slope=k, color='blue')

    for circle in gc.instances_of_predicate['Circle']:
        u = float(gc.value_of_para_sym[symbols(f'{circle[0]}.u')])
        v = float(gc.value_of_para_sym[symbols(f'{circle[0]}.v')])
        r = float(gc.value_of_para_sym[symbols(f'{circle[0]}.r')])
        ax.add_artist(plt.Circle((u, v), r, color="green", fill=False))

    for point in gc.instances_of_predicate['Point']:
        x = float(gc.value_of_para_sym[symbols(f'{point[0]}.x')])
        y = float(gc.value_of_para_sym[symbols(f'{point[0]}.y')])
        ax.plot(x, y, "o", color='red')
        ax.text(x, y, point[0], ha='center', va='bottom')

    plt.savefig(filename)


def split_expr(expr, letters):
    parsed_expr = []

    expr = str(expr).replace(' ', '')  # remove ' '

    for matched in re.findall(r'\d+\.*\d*', expr):  # replace number with 'nums'
        expr = expr.replace(matched, 'nums', 1)

    i = 0
    while i < len(expr):  # tokenize
        added = False
        for matched_part in letters:  # expr letters
            if expr[i:].startswith(matched_part):
                parsed_expr.append(matched_part)
                i = i + len(matched_part)
                added = True
                break
        if not added:  # entity letters
            parsed_expr.append(expr[i])
            i = i + 1

    return parsed_expr


def split_construction(construction, letters):
    parsed_construction = []

    entity, constraints = construction.split(':')

    predicate, paras = parse_geometric_fact(entity)  # parse target entity
    parsed_construction.append(predicate)
    parsed_construction.extend(paras)
    parsed_construction.append(':')

    for constraint in parse_disjunctive(constraints):
        if parsed_construction[-1] != ':':
            parsed_construction.append('&')

        if (constraint.startswith('Eq(') or constraint.startswith('G(')  # parse algebraic constraint
                or constraint.startswith('Geq(') or constraint.startswith('L(')
                or constraint.startswith('Leq(') or constraint.startswith('Ueq(')):
            algebraic_relation, expr = parse_algebraic_fact(constraint)
            expr = split_expr(expr, letters)
            parsed_construction.append(algebraic_relation)
            parsed_construction.extend(expr)
        else:  # parse predefined constraint
            predicate, paras = parse_geometric_fact(constraint)
            parsed_construction.append(predicate)
            parsed_construction.extend(paras)

    return parsed_construction


def get_sg(gc, forward=True, serialize=False):
    """
    Return hypergraph (dict format).
    If serialize=True, return serialize '<premise> <theorem> <conclusion>' (list format).
    """
    hypergraph = {
        'notes': [],  # node i, node_id is same with fact_id
        'dependent_entities': [],  # dependent entities of node i
        'edges': [],  # edge i, edge_id is not same with operation_id
        'hypergraph': []  # ((head_node_ids,), edge_id, (tail_node_ids,))
    }
    syms = ['.' + gc.parsed_gdl['Measures'][measure]['sym'] for measure in gc.parsed_gdl['Measures']]
    letters = tuple(list(expr_letters) + syms)

    added_edges = []
    for fact_id in range(len(gc.facts)):
        predicate, instance, premise_ids, entity_ids, operation_id = gc.facts[fact_id]

        if predicate != 'Equation':
            node = tuple([predicate] + list(instance))
        else:
            node = tuple([predicate] + split_expr(instance, letters))

        hypergraph['notes'].append(node)  # add node
        hypergraph['dependent_entities'].append(entity_ids)  # add dependent_entity

        if operation_id in added_edges:
            continue
        added_edges.append(operation_id)

        edge_id = len(hypergraph['edges'])
        edge = gc.operations[operation_id]
        if ':' in edge:  # construction
            edge = tuple(split_construction(edge, letters))
        elif edge in theorem_letters:  # theorem with no paras
            edge = [edge]
        else:  # theorem with paras
            edge_predicate, edge_instance = parse_geometric_fact(edge)
            edge = tuple([edge_predicate] + edge_instance)

        hypergraph['edges'].append(edge)  # add edge
        hypergraph['hypergraph'].append((premise_ids, edge_id, tuple(sorted(list(set(gc.groups[operation_id]))))))

    if serialize:
        serialized_hypergraph = []
        for head_node_ids, edge_id, tail_node_ids in hypergraph['hypergraph']:
            one_step = ['<p>']

            for head_node_id in head_node_ids:  # add premise
                if one_step[-1] != '<p>':
                    one_step.append('&')
                one_step.extend(hypergraph['notes'][head_node_id])

            if ':' in hypergraph['edges'][edge_id]:  # add operation
                one_step.append('<cons>')
            else:
                one_step.append('<t>')
            one_step.extend(hypergraph['edges'][edge_id])

            one_step.append('<c>')  # add conclusions
            for tail_node_id in tail_node_ids:
                if one_step[-1] != '<c>':
                    one_step.append('|')
                one_step.extend(hypergraph['notes'][tail_node_id])

            serialized_hypergraph.append(one_step)

        return serialized_hypergraph

    return hypergraph


def draw_sg(gc, filename, forward=True):
    """实体依赖关系与reasoning关系用不同颜色的线表示"""
    pass


"""↑---------------Output--------------↑"""

if __name__ == '__main__':
    print()
    # s = '~(~(~A(a,b))|B(c(d,e))&~C(c))&(D)&(E|~F|G(g))'
    # print(s)
    # print()
    #
    # serialized_s = serialize_gpl(s)
    # print(serialized_s)
    # print()
    #
    # parsed_s = parse_gpl_to_tree(serialized_s)
    # print(parsed_s)
    # print()
    #
    # tree_no_negation = negation_inward(parsed_s)
    # print(tree_no_negation)
    # print()
    #
    # for ps in parse_gpl_tree_to_dnf(tree_no_negation):
    #     print(ps)

    parsed_gdl_test = parse_gdl(load_json('gdl.json'))

    show_json(parsed_gdl_test)
    #
    # draw_gpl(parsed_gdl_test['Theorems']['parallel_property']['premises'],
    #          'premises')
    # draw_gpl(parsed_gdl_test['Theorems']['parallel_property']['algebraic_forms'],
    #          'algebraic_forms')

    parse_construction(
        'Point(C)&Line(m):PointOnLine(C,m)&~(PointOnLine(C,a)|PointOnLine(C,b)&~PointOnLine(C,c))&EqualAngle(m,l,l,n)',
        parsed_gdl_test)
