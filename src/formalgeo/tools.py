from sympy import sympify, symbols, atan, pi, log
import json
import matplotlib
import matplotlib.pyplot as plt
import re
from pprint import pprint
from graphviz import Digraph, Graph

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

    update = True
    while update:
        update = False
        for relation in gdl['Relations']:  # parse Relations
            try:
                update = _parse_one_relation(relation, gdl, parsed_gdl) or update
            except Exception as e:
                e_msg = f"An error occurred while parsing relation '{relation}'."
                raise Exception(e_msg) from e

    for theorem in gdl['Theorems']:  # parse Theorems
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
    for multiple_form in gdl['Attributions'][attr]['multiple_forms']:
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

    geometric_constraints = _parse_geometric_constraints(
        gdl['Relations'][relation]['geometric_constraints'], paras)

    algebraic_forms = []
    for algebraic_form in _serialize_gpl(gdl['Relations'][relation]['algebraic_forms']):
        if algebraic_form in {'&', '|', '~', '(', ')'}:
            algebraic_forms.append(algebraic_form)
        elif (algebraic_form.startswith('Eq(') or algebraic_form.startswith('G(') or
              algebraic_form.startswith('Geq(') or algebraic_form.startswith('L(') or
              algebraic_form.startswith('Leq(') or algebraic_form.startswith('Ueq(')):
            algebraic_forms.append(_parse_algebraic_fact(algebraic_form))
        else:
            predicate, instance = _parse_geometric_fact(algebraic_form)
            if predicate not in parsed_gdl['Relations']:
                return False
            replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
            algebraic_forms.append('(')
            for dependent_algebraic_form in parsed_gdl['Relations'][predicate]['algebraic_forms']:
                if dependent_algebraic_form in {'&', '|', '~', '(', ')'}:
                    algebraic_forms.append(dependent_algebraic_form)
                else:
                    algebraic_relation, expr = dependent_algebraic_form
                    expr = _replace_expr(expr, replace)
                    algebraic_forms.append((algebraic_relation, expr))
            algebraic_forms.append(')')

    parsed_gdl['Relations'][name] = {
        'paras': paras,
        'geometric_constraints': geometric_constraints,
        'algebraic_forms': tuple(algebraic_forms)
    }

    return True


def _parse_one_theorem(theorem, gdl, parsed_gdl):
    name, paras = _parse_geometric_fact(theorem)
    if name in parsed_gdl['Theorems']:
        raise Exception(f"Duplicate definition of theorem '{name}'.")

    premises = _serialize_gpl(gdl['Theorems'][theorem]['premises'])
    geometric_constraints = []
    algebraic_forms = []
    for i in range(len(premises)):
        if premises[i] in {'&', '|', '~', '(', ')'}:
            algebraic_forms.append(premises[i])
        else:
            if premises[i].startswith('Eq('):  # algebraic relation
                algebraic_relation, expr = _parse_algebraic_fact(premises[i])
                premises[i] = (algebraic_relation, expr)
                geometric_constraints.extend(_parse_dependent_entities(premises[i][0], premises[i][1], parsed_gdl))
                algebraic_forms.extend(_parse_algebraic_forms(premises[i][0], premises[i][1], parsed_gdl))
            else:  # geometric relation
                premises[i] = _parse_geometric_fact(premises[i])
                geometric_constraints.extend(_parse_dependent_entities(premises[i][0], premises[i][1], parsed_gdl))
                algebraic_forms.extend(_parse_algebraic_forms(premises[i][0], premises[i][1], parsed_gdl))

    if gdl['Theorems'][theorem]['conclusion'].startswith('Eq('):
        conclusion = _parse_algebraic_fact(gdl['Theorems'][theorem]['conclusion'])
    else:
        conclusion = _parse_geometric_fact(gdl['Theorems'][theorem]['conclusion'])

    geometric_constraints.extend(_parse_dependent_entities(conclusion[0], conclusion[1], parsed_gdl))
    geometric_constraints = tuple(sorted(list(set(geometric_constraints)), key=lambda x: paras.index(x[1][0])))
    if len(geometric_constraints) != len(paras):
        e_msg = (f"Theorem '{theorem}' is incorrectly defined."
                 f"geometric_constraints: '{geometric_constraints}', paras: '{paras}'")
        raise Exception(e_msg)

    if len(algebraic_forms) > 0:
        algebraic_forms = ['('] + algebraic_forms + [')', '&']
    algebraic_forms.extend(_parse_algebraic_forms(conclusion[0], conclusion[1], parsed_gdl))

    if len(premises) == 0:
        premises = list(geometric_constraints)
        for i in range(1, len(geometric_constraints))[::-1]:
            premises.insert(i, '&')

    premises = _parse_gpl_to_tree(premises)
    premises = _negation_inward(premises)
    premises = _format_premises(premises)

    algebraic_forms = _parse_gpl_to_tree(algebraic_forms)
    algebraic_forms = _negation_inward(algebraic_forms)
    algebraic_forms = _format_algebraic_forms(algebraic_forms, parsed_gdl, add_dependent=True)

    parsed_gdl['Theorems'][name] = {
        'paras': paras,
        'geometric_constraints': geometric_constraints,
        'algebraic_forms': algebraic_forms,
        'premises': premises,
        'conclusion': conclusion
    }


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

    return tuple(entities)


def _parse_algebraic_forms(predicate, instance, parsed_gdl):
    if predicate == 'Eq':  # algebraic relation
        for sym in list(instance.free_symbols):
            entities, attr = str(sym).split('.')
            replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
            sym_replace = _replace_expr(parsed_gdl['Attributions'][attr]['algebraic_forms'], replace)
            instance = instance.subs(sym, sym_replace)
        return [('Eq', instance)]
    else:  # geometric relation
        replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
        algebraic_forms = list(parsed_gdl['Relations'][predicate]['algebraic_forms'])
        for j in range(len(algebraic_forms)):
            if algebraic_forms[j] in {'&', '|', '~', '(', ')'}:
                continue
            expr = _replace_expr(algebraic_forms[j][1], replace)
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
        return ()

    elif not isinstance(algebraic_forms, list):  # atomic form
        if algebraic_forms[0] == '~':
            algebraic_relation = negation_map[algebraic_forms[1][0]]
            expr = algebraic_forms[1][1]
        else:
            algebraic_relation, expr = algebraic_forms

        if not add_dependent:
            return algebraic_relation, expr
        dependent_entities = {}
        for entity_type, para in _parse_dependent_entities(algebraic_relation, expr, parsed_gdl):
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
    if len(gpl_serialized) == 0:
        return []

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
            # disjunctive form: [..., '|', ...] -> [_parse_gpl_to_tree(...), '|', _parse_gpl_to_tree(...)]
            return [_parse_gpl_to_tree(gpl_serialized[:i]), '|', _parse_gpl_to_tree(gpl_serialized[i + 1:])]
        # conjunctive form: [..., '&', ...] -> [_parse_gpl_to_tree(...), '&', _parse_gpl_to_tree(...)]
        return [_parse_gpl_to_tree(gpl_serialized[:operators[0]]), '&',
                _parse_gpl_to_tree(gpl_serialized[operators[0] + 1:])]

    else:  # negative form (~) or atomic form
        if gpl_serialized[0] == '(' and gpl_serialized[-1] == ')' and priorities[0] == priorities[-1]:
            # redundant '(' and ')': ['(', ..., ')'] -> _parse_gpl_to_tree(...)
            return _parse_gpl_to_tree(gpl_serialized[1:-1])
        elif len(gpl_serialized) == 1 and gpl_serialized[0] not in {'&', '|', '~', '(', ')'}:
            # atomic form: [A] -> A
            return gpl_serialized[0]
        elif (len(gpl_serialized) == 2 and
              gpl_serialized[0] == '~' and gpl_serialized[1] not in {'&', '|', '~', '(', ')'}):
            # negative atomic form: ['~', A] -> ['~', A]
            return gpl_serialized
        elif (gpl_serialized[0] == '~' and
              gpl_serialized[1] == '(' and gpl_serialized[-1] == ')' and priorities[1] == priorities[-1]):
            # negative form: ['~', '(', ..., ')'] -> ['~', _parse_gpl_to_tree(...)]
            return ['~', _parse_gpl_to_tree(gpl_serialized[2:-1])]
        else:
            raise Exception(f"Syntax error in serialized GPL '{gpl_serialized}'.")


def _negation_inward(gpl_tree):
    """

    Args:
    gpl_tree (list): [['~', [['~', ['~', 'A(a,b)']], '|', ['B(c(d,e))', '&', ['~', 'C(c)']]]], '&',
                      ['D', '&', ['E', '|', [['~', 'F'], '|', 'G(g)']]]]

    Returns:
    gpl_tree_no_negation (list): [[('~', 'A(a,b)'), '&', [('~', 'B(c(d,e))'), '|', 'C(c)']], '&',
                                  ['D', '&', ['E', '|', [('~', 'F'), '|', 'G(g)']]]]
    """
    if len(gpl_tree) == 0:  # syntax error
        return []

    elif not isinstance(gpl_tree, list):  # atomic form
        # atomic form: A -> A
        return gpl_tree

    elif len(gpl_tree) == 2:  # negative form
        if not isinstance(gpl_tree[1], list):
            # negative atomic form: ['~', A] -> ('~', A)
            return '~', gpl_tree[1]
        elif len(gpl_tree[1]) == 2:
            # merge negation: ['~', ['~', ...]] -> _negation_inward(...)
            return _negation_inward(gpl_tree[1][1])
        elif len(gpl_tree[1]) == 3 and gpl_tree[1][1] == '&':
            # ~ conjunction: [~, [..., '&', ...]] -> [_negation_inward(['~', ...]), '|', _negation_inward(['~', ...])]
            return [_negation_inward(['~', gpl_tree[1][0]]), '|', _negation_inward(['~', gpl_tree[1][2]])]
        elif len(gpl_tree[1]) == 3 and gpl_tree[1][1] == '|':
            # ~ disjunction: [~, [..., '|', ...]] -> [_negation_inward(['~', ...]), '&', _negation_inward(['~', ...])]
            return [_negation_inward(['~', gpl_tree[1][0]]), '&', _negation_inward(['~', gpl_tree[1][2]])]
        else:
            raise Exception(f"Syntax error in tree GPL '{gpl_tree}'.")

    elif len(gpl_tree) == 3 and gpl_tree[1] == '&':
        # conjunction: [..., '&', ...] -> [_negation_inward(...), '&', _negation_inward(...)]
        return [_negation_inward(gpl_tree[0]), '&', _negation_inward(gpl_tree[2])]

    elif len(gpl_tree) == 3 and gpl_tree[1] == '|':
        # disjunction: [..., '|', ...] -> [_negation_inward(...), '|', _negation_inward(...)]
        return [_negation_inward(gpl_tree[0]), '|', _negation_inward(gpl_tree[2])]

    else:
        raise Exception(f"Syntax error in tree GPL '{gpl_tree}'.")


def _parse_gpl_tree_to_dnf(gpl_tree_no_negation):
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
        return [[]]

    elif len(gpl_tree_no_negation) == 3 and gpl_tree_no_negation[1] == '&':  # conjunction
        norm_form1 = _parse_gpl_tree_to_dnf(gpl_tree_no_negation[0])
        norm_form2 = _parse_gpl_tree_to_dnf(gpl_tree_no_negation[2])
        norm_forms = []
        for a in norm_form1:
            for b in norm_form2:
                norm_forms.append(a + b)
        # [left, '&', right] -> _parse_gpl_tree_to_dnf(left) × _parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)&(B1|B2) -> A1&B1|A1&B2|A2&B1|A2&B2
        return norm_forms

    elif len(gpl_tree_no_negation) == 3 and gpl_tree_no_negation[1] == '|':  # disjunction
        norm_form1 = _parse_gpl_tree_to_dnf(gpl_tree_no_negation[0])
        norm_form2 = _parse_gpl_tree_to_dnf(gpl_tree_no_negation[2])
        # [left, '|', right] -> _parse_gpl_tree_to_dnf(left) + _parse_gpl_tree_to_dnf(right)
        # example: (A1|A2)|(B1|B2) -> A1|A2|B1|B2
        return norm_form1 + norm_form2

    else:  # atomic form
        # A -> [[A]]
        return [[gpl_tree_no_negation]]


def _parse_dependent_entities(predicate, instance, parsed_gdl):
    dependent_entities = []
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        for sym in instance.free_symbols:
            entities, attr = str(sym).split('.')
            replace = dict(zip(parsed_gdl['Attributions'][attr]['paras'], entities))
            for entity, paras in parsed_gdl['Attributions'][attr]['geometric_constraints']:
                dependent_entities.append((entity, _replace_instance(paras, replace)))
    else:
        replace = dict(zip(parsed_gdl['Relations'][predicate]['paras'], instance))
        for entity, paras in parsed_gdl['Relations'][predicate]['geometric_constraints']:
            dependent_entities.append((entity, _replace_instance(paras, replace)))

    return sorted(dependent_entities)


def _parse_construction(construction, parsed_gdl):
    """
    Point(C)&Line(m):PointOnLine(C,m)&~(PointOnLine(C,l)|~PointOnLine(C,n))&EqualAngle(m,l,l,n)
    """
    parsed_construction = []  # (target_entities, dependent_entities, equations, inequalities, added_facts)

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

            if constraint in added_facts:
                continue

            predicate, instance = constraint

            constraint_dependent_entities = _parse_dependent_entities(predicate, instance, parsed_gdl)
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

        dependent_entities = sorted(list(dependent_entities - set(target_entities)))

        algebraic_forms = _format_algebraic_forms(_negation_inward(_parse_gpl_to_tree(algebraic_forms)), parsed_gdl)
        for algebraic_forms_dnf in _parse_gpl_tree_to_dnf(algebraic_forms):
            equations = set()
            inequalities = set()
            for algebraic_relation, expr in algebraic_forms_dnf:
                if algebraic_relation == 'Eq':
                    replace = {}
                    _find_mod(expr, replace)
                    equations.add(expr.subs(replace))
                else:
                    inequalities.add((algebraic_relation, expr))
            equations = list(equations)
            inequalities = list(inequalities)

            parsed_construction.append([target_entities, dependent_entities,
                                        added_facts, equations, inequalities, None])

    return parsed_construction  # [target_entities, dependent_entities, added_facts, equations, inequalities, values]


def _find_mod(expr, replace):
    if type(expr).__name__ == 'Mod':
        replace[expr] = expr.args[0]
    else:
        for arg in expr.args:
            _find_mod(arg, replace)


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


def _anti_parse_operation(operation):
    operation_type, operation_predicate, operation_instance = operation
    if operation_type == 'construction':
        return operation_predicate + ':' + operation_instance
    elif operation_type == 'auto':
        return 'Auto' + ':' + operation_predicate
    elif operation_type == 'apply':
        return 'Apply' + ':' + operation_predicate + '(' + ','.join(operation_instance) + ')'
    elif operation_type == 'decompose':
        return 'Decompose' + ':' + operation_predicate + '(' + ','.join(operation_instance) + ')'
    else:
        raise Exception(f"Unknown operation type '{operation_type}'.")


def _anti_parse_fact(fact):
    predicate, instance = fact
    if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:
        return f"{predicate}({str(instance).replace(' ', '')})"
    else:
        return f"{predicate}({','.join(instance)})"


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

    predicate, paras = _parse_geometric_fact(entity)  # parse target entity
    parsed_construction.append(predicate)
    parsed_construction.extend(paras)
    parsed_construction.append(':')

    for constraint in parse_disjunctive(constraints):
        if parsed_construction[-1] != ':':
            parsed_construction.append('&')

        if (constraint.startswith('Eq(') or constraint.startswith('G(')  # parse algebraic constraint
                or constraint.startswith('Geq(') or constraint.startswith('L(')
                or constraint.startswith('Leq(') or constraint.startswith('Ueq(')):
            algebraic_relation, expr = _parse_algebraic_fact(constraint)
            expr = split_expr(expr, letters)
            parsed_construction.append(algebraic_relation)
            parsed_construction.extend(expr)
        else:  # parse predefined constraint
            predicate, paras = _parse_geometric_fact(constraint)
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
            edge_predicate, edge_instance = _parse_geometric_fact(edge)
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
