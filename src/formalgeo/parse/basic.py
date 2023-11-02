import sympy
from sympy import sin, cos, tan, sqrt, pi

operation = ["Add", "Sub", "Mul", "Div", "Pow", "Mod", "Sqrt", "Sin", "Cos", "Tan"]


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
        left, l_attrs = parse_equal_to_tree(left, make_vars)
        attrs += l_attrs
    if right[0].isupper():
        right, l_attrs = parse_equal_to_tree(right, make_vars)
        attrs += l_attrs

    return ("Equal", (left, right)), attrs


def parse_equal_to_tree(s, make_vars=False):
    """
    Parse equal's para to a Tree, return the tree and all attr.
    >> parse_equal_to_tree('LengthOfLine(AB)')
    (('LengthOfLine', ('A', 'B')), [('LengthOfLine', ('A', 'B'))])
    >> parse_equal_to_tree('LengthOfLine(AB)', True)
    (('LengthOfLine', ('a', 'b')), [('LengthOfLine', ('a', 'b'))])
    >> parse_equal_to_tree('Add(LengthOfLine(OA),x+1)', True)
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
            if predicate in operation:  # not attribution
                stack.append((predicate, tuple(paras[::-1])))
            else:  # attribution
                paras = tuple("".join(paras[::-1]).lower() if make_vars else "".join(paras[::-1]))
                stack.append((predicate, paras))
                attrs.append((predicate, paras))

        j = j + 1

    return stack.pop(), attrs


def get_equation_from_tree(problem, tree, replaced=False, letters=None):
    """
    Trans expr_tree to symbolic algebraic expression.
    >> get_expr_from_tree(problem, [['LengthOfLine', ['a', 'b']], '2*x-14'], True, {'a': 'Z', 'b': 'X'})
    - 2.0*f_x + ll_zx + 14.0
    >> get_expr_from_tree(problem, [['LengthOfLine', ['Z', 'X']], '2*x-14'])
    - 2.0*f_x + ll_zx + 14.0
    """
    left_expr = get_expr_from_tree(problem, tree[0], replaced, letters)
    if left_expr is None:
        return None
    right_expr = get_expr_from_tree(problem, tree[1], replaced, letters)
    if right_expr is None:
        return None
    return left_expr - right_expr


def get_expr_from_tree(problem, tree, replaced=False, letters=None):
    """
    Recursively trans expr_tree to symbolic algebraic expression.
    :param problem: class <Problem>.
    :param tree: An expression in the form of a list tree.
    :param replaced: Optional. Set True when tree's item is expressed by vars.
    :param letters: Optional. Letters that will replace vars. Dict = {var: letter}.
    >> get_expr_from_tree(problem, ['LengthOfLine', ['T', 'R'[])
    l_tr
    >> get_expr_from_tree(problem, ['Add', [['LengthOfLine', ['Z', 'X']], '2*x-14']])
    2.0*f_x + l_zx - 14.0
    >> get_expr_from_tree(problem, ['Sin', [['MeasureOfAngle', ['a', 'b', 'c']]]],
                          True, {'a': 'X', 'b': 'Y', 'c': 'Z'})
    sin(pi*m_zxy/180)
    """
    if not isinstance(tree, tuple):  # expr
        return parse_expr(problem, tree)
    if tree[0] in problem.parsed_predicate_GDL["Attribution"]:  # attr
        if not replaced:
            return problem.get_sym_of_attr(tree[0], tree[1])
        else:
            replaced_item = [letters[i] for i in tree[1]]
            return problem.get_sym_of_attr(tree[0], tuple(replaced_item))

    if tree[0] in ["Add", "Mul"]:  # operate
        expr_list = []
        for item in tree[1]:
            expr = get_expr_from_tree(problem, item, replaced, letters)
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
        expr_left = get_expr_from_tree(problem, tree[1][0], replaced, letters)
        if expr_left is None:
            return None
        expr_right = get_expr_from_tree(problem, tree[1][1], replaced, letters)
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
        expr = get_expr_from_tree(problem, tree[1][0], replaced, letters)
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


def parse_expr(problem, expr):
    """Parse expression to symbolic form."""
    expr = sympy.parsing.parse_expr(expr)

    for sym in expr.free_symbols:
        if "_" not in str(sym):
            saved_sym = problem.get_sym_of_attr("Free", str(sym))
            if saved_sym is None:
                return None
            expr = expr.subs(sym, saved_sym)
        else:
            sym_str, para = str(sym).split("_", 1)
            para = tuple(para.upper())
            attr_GDL = problem.parsed_predicate_GDL["Attribution"]
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
