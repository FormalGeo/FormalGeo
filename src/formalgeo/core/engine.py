import copy
from sympy import symbols, solve, Float
from func_timeout import func_set_timeout, FunctionTimedOut
from formalgeo.parse import get_equation_from_tree
from formalgeo.tools import rough_equal
import warnings


class EquationKiller:
    solve_eqs = True  # whether to solve the equation in the intermediate process
    sym_simplify = True  # whether to apply symbol substitution simplification
    accurate_mode = False  # whether to use accurate mode
    solve_rank_deficient_eqs = False  # whether to solve rank deficient equations
    use_cache = False  # whether to use cache to store solved target equations
    cache_eqs = None  # <dict>, {tuple(str(eqs),): [(sym_str, value)]}
    cache_target = None  # <dict>, {tuple(str(eqs),): value}

    @staticmethod
    def get_minimum_target_equations(target_expr, eqs):
        """
        Return minimum target equations. Called by function <EquationKiller.solve_target>.
        :param target_expr: Target Expression.
        :param eqs: Existing Equations.
        :return target_sym: Target symbols.
        :return mini_eqs: minimum equations rank by solving difficulty.
        :return n_m: number of equations and syms.
        """
        target_sym = symbols("t_s")
        eqs = [target_sym - target_expr] + eqs

        sym_to_eqs = {}  # dict, sym: [equation]
        for eq in eqs:
            for sym in eq.free_symbols:
                if sym in sym_to_eqs:
                    sym_to_eqs[sym].append(eq)
                else:
                    sym_to_eqs[sym] = [eq]

        mini_eqs = [eqs[0]]  # mini equations
        mini_syms = eqs[0].free_symbols  # sym of mini equations
        n_m = [(len(mini_eqs), len(mini_syms))]  # number of equations and variable

        related_eqs = []  # related eqs waiting to add
        for sym in mini_syms:
            for r_eq in sym_to_eqs[sym]:
                related_eqs.append(r_eq)
        related_eqs = list(set(related_eqs) - set(mini_eqs))

        while len(related_eqs) > 0:
            added_eq_id = 0
            added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
            added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)
            for i in range(1, len(related_eqs)):
                if len(related_eqs[i].free_symbols - mini_syms) < added_eq_n1:
                    added_eq_id = i
                    added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
                    added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)
                elif len(related_eqs[i].free_symbols - mini_syms) == added_eq_n1:
                    if len(related_eqs[i].free_symbols) > added_eq_n2:
                        added_eq_id = i
                        added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
                        added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)

            added_eq = related_eqs[added_eq_id]
            mini_eqs.append(added_eq)
            mini_syms |= added_eq.free_symbols
            n_m.append((len(mini_eqs), len(mini_syms)))

            for sym in added_eq.free_symbols:
                for r_eq in sym_to_eqs[sym]:
                    related_eqs.append(r_eq)
            related_eqs = list(set(related_eqs) - set(mini_eqs))

        return target_sym, mini_eqs, n_m

    @staticmethod
    def get_minimum_group_equations(eqs):
        """
        Return minimum group equations. Called by function <EquationKiller.solve_equations>.
        :param eqs: Equations.
        :return mini_eqs_list: minimum equations lists rank by solving difficulty.
        :return n_m: number of equations and syms.
        """

        sym_to_eqs = {}  # dict, sym: [equation]
        for eq in eqs:
            for sym in eq.free_symbols:
                if sym in sym_to_eqs:
                    sym_to_eqs[sym].append(eq)
                else:
                    sym_to_eqs[sym] = [eq]

        mini_eqs_lists = []  # mini equations
        n_m = []  # number of equations and variable

        added_eqs = set()
        for eq in eqs:
            if eq in added_eqs:
                continue
            added_eqs.add(eq)

            mini_eqs = [eq]  # mini equations
            mini_syms = eq.free_symbols  # sym of mini equations

            related_eqs = []  # related eqs waiting to add
            for sym in mini_syms:
                for r_eq in sym_to_eqs[sym]:
                    related_eqs.append(r_eq)
            related_eqs = list(set(related_eqs) - set(mini_eqs))

            if len(related_eqs) == 0:
                mini_eqs_lists.append(mini_eqs)
                n_m.append((len(mini_eqs), len(mini_syms)))  # add mini equations
                continue

            while True:
                added_eq_id = 0
                added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
                added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)
                for i in range(1, len(related_eqs)):
                    if len(related_eqs[i].free_symbols - mini_syms) < added_eq_n1:
                        added_eq_id = i
                        added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
                        added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)
                    elif len(related_eqs[i].free_symbols - mini_syms) == added_eq_n1:
                        if len(related_eqs[i].free_symbols) > added_eq_n2:
                            added_eq_id = i
                            added_eq_n1 = len(related_eqs[added_eq_id].free_symbols - mini_syms)
                            added_eq_n2 = len(related_eqs[added_eq_id].free_symbols)

                added_eq = related_eqs[added_eq_id]
                mini_eqs.append(added_eq)
                mini_syms |= added_eq.free_symbols
                added_eqs.add(added_eq)

                for sym in added_eq.free_symbols:
                    for r_eq in sym_to_eqs[sym]:
                        related_eqs.append(r_eq)
                related_eqs = list(set(related_eqs) - set(mini_eqs))

                if len(related_eqs) == 0:
                    mini_eqs_lists.append(mini_eqs)
                    n_m.append((len(mini_eqs), len(mini_syms)))  # add mini equations
                    break

        return mini_eqs_lists, n_m

    @staticmethod
    def get_minimum_syms(target_eqs, eqs):
        """
        Return minimum equation's syms. Called by function <Searcher.get_theorem_selection>.
        :param target_eqs: <list>, target Equations.
        :param eqs: <list>, existing Equations.
        :return syms: <set>, set of minimum equation's syms.
        """
        sym_to_eqs = {}  # dict, sym: [equation]
        for eq in target_eqs + eqs:
            for sym in eq.free_symbols:
                if sym in sym_to_eqs:
                    sym_to_eqs[sym].append(eq)
                else:
                    sym_to_eqs[sym] = [eq]

        mini_eqs = set(target_eqs)
        mini_syms = set()
        for eq in mini_eqs:
            mini_syms |= eq.free_symbols

        while True:
            new_sym = set()
            for sym in mini_syms:
                for eq in sym_to_eqs[sym]:
                    mini_eqs.add(eq)
                    new_sym |= eq.free_symbols
            new_sym = new_sym - mini_syms
            if len(new_sym) == 0:
                break
            mini_syms |= new_sym

        return mini_syms

    @staticmethod
    @func_set_timeout(2)
    def simplification_value_replace(problem):
        """
        Simplify equations by replacing sym with known value.
        :param problem: Instance of class <Problem>.
        """
        update = True
        while update:
            update = False
            remove_lists = set()  # equation to be deleted
            add_lists = []  # equation to be added

            for eq in problem.condition.simplified_equation:  # solve eq that only one sym unsolved
                if len(eq.free_symbols) != 1:
                    continue

                target_sym = list(eq.free_symbols)[0]
                try:
                    result = EquationKiller.solve(eq)  # solve equations
                except FunctionTimedOut:
                    msg = "Timeout when solve equation: {}".format(eq)
                    warnings.warn(msg)
                else:
                    if target_sym in result:
                        problem.set_value_of_sym(target_sym, result[target_sym],
                                                 tuple(problem.condition.simplified_equation[eq]))
                        remove_lists |= {eq}

            for eq in problem.condition.simplified_equation:  # value replace
                if eq in remove_lists:
                    continue
                raw_eq = eq
                simplified = False
                added_premise = []
                for sym in eq.free_symbols:
                    if problem.condition.value_of_sym[sym] is None:
                        continue
                    simplified = True  # replace sym with value when the value known
                    eq = eq.subs(sym, problem.condition.value_of_sym[sym])
                    added_premise.append(problem.condition.get_id_by_predicate_and_item(
                        "Equation", sym - problem.condition.value_of_sym[sym]))
                    remove_lists |= {raw_eq}

                if not simplified:
                    continue

                if len(eq.free_symbols) == 0:  # no need to add new simplified equation when it's all sym known
                    continue
                else:  # add new simplified equation
                    update = True
                    premise = problem.condition.simplified_equation[raw_eq] + added_premise
                    add_lists.append((eq, premise))

            for remove_eq in remove_lists:  # remove useless equation
                problem.condition.simplified_equation.pop(remove_eq)
            for add_eq, premise in add_lists:  # remove useless equation
                problem.condition.simplified_equation[add_eq] = premise

    @staticmethod
    @func_set_timeout(2)
    def simplification_sym_replace(equations, target_sym):
        """ High level simplify based on symbol replacement."""
        update = True
        while update:
            update = False
            for i in range(len(equations)):
                eq = equations[i]

                if target_sym in eq.free_symbols or \
                        len(eq.free_symbols) != 2 or \
                        len(eq.atoms()) > 5:  # too many atoms, no need to replace
                    continue

                try:
                    result = EquationKiller.solve(eq, keep_sym=True)  # solve sym
                except FunctionTimedOut:
                    msg = "Timeout when solve equations: {}".format(equations)
                    warnings.warn(msg)
                    continue

                if len(result) == 0:  # no solved result
                    continue

                sym = list(result.keys())[0]
                has_float = False
                for atom in result[sym].atoms():
                    if isinstance(atom, Float):
                        has_float = True
                        break
                if has_float:  # float has precision error
                    continue

                for j in range(len(equations)):  # replace sym with solved sym_expr
                    if sym in equations[j].free_symbols:
                        equations[j] = equations[j].subs(sym, result[sym])
                        update = True

        for i in range(len(equations))[::-1]:  # remove 0
            if len(equations[i].free_symbols) == 0:
                equations.pop(i)

    @staticmethod
    @func_set_timeout(2)
    def solve(equations, target_sym=None, keep_sym=False):
        try:
            if target_sym is not None:
                solved = solve(equations, target_sym, dict=True)
            else:
                solved = solve(equations, dict=True)

            if len(solved) == 0:  # no result solved
                return {}
        except Exception as e:  # exception
            msg = "Exception <{}> occur when solve {}".format(e, equations)
            warnings.warn(msg)
            return {}
        else:  # has result
            if keep_sym:  # keep sym result
                if isinstance(solved, list):
                    return solved[0]
                return solved

            if isinstance(solved, list):
                update = True
                while update and len(solved) > 1:  # choose min but > 0, when has multi result
                    update = False
                    for sym in solved[0]:
                        if sym not in solved[1]:
                            solved.pop(1)
                            update = True
                            break
                        if len(solved[0][sym].free_symbols) != 0 and len(solved[1][sym].free_symbols) == 0:
                            solved.pop(0)
                            update = True
                            break
                        if len(solved[0][sym].free_symbols) == 0 and len(solved[1][sym].free_symbols) != 0:
                            solved.pop(1)
                            update = True
                            break
                        if len(solved[0][sym].free_symbols) != 0:
                            continue
                        if solved[0][sym] == solved[1][sym]:
                            continue
                        if float(solved[0][sym]) < 0 < float(solved[1][sym]):
                            solved.pop(0)
                            update = True
                            break
                        if float(solved[0][sym]) > 0 > float(solved[1][sym]):
                            solved.pop(1)
                            update = True
                            break

                    if update:
                        continue

                    for sym in solved[0]:
                        if len(solved[0][sym].free_symbols) != 0:
                            continue
                        if solved[0][sym] == solved[1][sym]:
                            continue
                        if abs(float(solved[0][sym])) > abs(float(solved[1][sym])):
                            solved.pop(0)
                            update = True
                        else:
                            solved.pop(1)
                            update = True
                        break

                solved = solved[0]

            real_results = {}  # real_number
            for sym in solved:  # filter out real number solution
                if len(solved[sym].free_symbols) == 0:
                    # real_results[sym] = number_round(solved[sym])
                    real_results[sym] = solved[sym]
            return real_results

    @staticmethod
    def solve_equations(problem):
        """
        Solve equations in problem.condition.equations.
        :param problem: Instance of class <Problem>.
        """
        if not EquationKiller.solve_eqs or problem.condition.eq_solved:
            return

        try:
            EquationKiller.simplification_value_replace(problem)  # simplify equations before solving
        except FunctionTimedOut:
            msg = "Timeout when simplify equations by value replace."
            warnings.warn(msg)

        mini_eqs_lists, n_m = EquationKiller.get_minimum_group_equations(  # get mini equations
            list(problem.condition.simplified_equation)
        )

        for i in range(len(mini_eqs_lists)):
            if not EquationKiller.solve_rank_deficient_eqs and n_m[i][0] < n_m[i][1]:
                continue

            eqs_for_cache = None
            if EquationKiller.use_cache:
                eqs_for_cache = []
                premise = []
                str_to_sym = {}
                for eq in mini_eqs_lists[i]:
                    eqs_for_cache.append(str(eq))
                    premise += problem.condition.simplified_equation[eq]
                    for sym in eq.free_symbols:
                        str_to_sym[str(sym)] = sym
                eqs_for_cache = tuple(sorted(eqs_for_cache))

                if eqs_for_cache in EquationKiller.cache_eqs:
                    for sym_str, value in EquationKiller.cache_eqs[eqs_for_cache]:
                        problem.set_value_of_sym(str_to_sym[sym_str], value, premise)
                    continue
                EquationKiller.cache_eqs[eqs_for_cache] = []

            solved = False
            solved_results = None
            mini_eqs = None

            try:
                results = EquationKiller.solve(mini_eqs_lists[i])  # solve equations
            except FunctionTimedOut:
                msg = "Timeout when solve equations: {}".format(mini_eqs_lists[i])
                warnings.warn(msg)
            else:
                for sym in results:
                    if problem.condition.value_of_sym[sym] is None:
                        solved = True
                        solved_results = results
                        mini_eqs = mini_eqs_lists[i]
                        break

            if not solved:
                continue

            if EquationKiller.accurate_mode:
                for sym in solved_results:
                    if problem.condition.value_of_sym[sym] is not None:
                        continue
                    sym_mini_eqs = copy.copy(mini_eqs)
                    for removed_eq in copy.copy(sym_mini_eqs):
                        try_eqs = copy.copy(sym_mini_eqs)
                        try_eqs.remove(removed_eq)
                        try:
                            results = EquationKiller.solve(try_eqs, sym)  # solve equations
                        except FunctionTimedOut:
                            msg = "Timeout when solve equations: {}".format(try_eqs)
                            warnings.warn(msg)
                        else:
                            if sym in results:
                                sym_mini_eqs.remove(removed_eq)

                    premise = []
                    for eq in sym_mini_eqs:
                        premise += problem.condition.simplified_equation[eq]
                    problem.set_value_of_sym(sym, solved_results[sym], premise)

                    if EquationKiller.use_cache:
                        EquationKiller.cache_eqs[eqs_for_cache].append((str(sym), solved_results[sym]))

            else:
                premise = []
                for eq in mini_eqs:
                    premise += problem.condition.simplified_equation[eq]

                for sym in solved_results:
                    problem.set_value_of_sym(sym, solved_results[sym], premise)

                if EquationKiller.use_cache:
                    for sym in solved_results:
                        EquationKiller.cache_eqs[eqs_for_cache].append((str(sym), solved_results[sym]))

    @staticmethod
    def solve_target(target_expr, problem):
        """
        Solve target_expr in the constraint of problem's equation.
        :param problem: Instance of class <Problem>.
        :param target_expr: symbol expression.
        """
        if target_expr is None:
            return None, []

        if target_expr in problem.condition.get_items_by_predicate("Equation"):  # no need to solve
            return 0, [problem.condition.get_id_by_predicate_and_item("Equation", target_expr)]
        if -target_expr in problem.condition.get_items_by_predicate("Equation"):
            return 0, [problem.condition.get_id_by_predicate_and_item("Equation", -target_expr)]

        try:
            EquationKiller.simplification_value_replace(problem)  # simplify equations before solving
        except FunctionTimedOut:
            msg = "Timeout when simplify equations by value replace."
            warnings.warn(msg)

        premise = []
        for sym in target_expr.free_symbols:  # solve only using value replacement
            if problem.condition.value_of_sym[sym] is not None:
                target_expr = target_expr.subs(sym, problem.condition.value_of_sym[sym])
                premise.append(problem.condition.get_id_by_predicate_and_item(
                    "Equation", sym - problem.condition.value_of_sym[sym]))
        if len(target_expr.free_symbols) == 0:
            return target_expr, premise

        target_sym, mini_eqs, n_m = EquationKiller.get_minimum_target_equations(  # get mini equations
            target_expr,
            list(problem.condition.simplified_equation)
        )

        if len(mini_eqs) == 0:  # no mini equations, can't solve
            return None, []

        eqs_for_cache = None
        if EquationKiller.use_cache:
            eqs_for_cache = [str(mini_eqs[0])]
            for eq in mini_eqs[1:]:
                eqs_for_cache.append(str(eq))
                premise += problem.condition.simplified_equation[eq]
            eqs_for_cache = tuple(sorted(eqs_for_cache))

            if eqs_for_cache in EquationKiller.cache_target:
                value = EquationKiller.cache_target[eqs_for_cache]
                if value is None:
                    return None, []
                return value, premise
            EquationKiller.cache_target[eqs_for_cache] = None

        head = 0  # can't solve
        tail = len(mini_eqs)  # can solve
        solved_mini_eqs = None
        solved_target_value = None
        while tail - head > 1:
            solved = False
            p = int((head + tail) / 2)
            try_mini_eqs = copy.copy(mini_eqs[0:p + 1])

            if EquationKiller.sym_simplify:
                try:
                    EquationKiller.simplification_sym_replace(try_mini_eqs, target_sym)
                except FunctionTimedOut:
                    msg = "Timeout when simplify equations by sym replace."
                    warnings.warn(msg)

            try:
                results = EquationKiller.solve(try_mini_eqs)  # solve equations
            except FunctionTimedOut:
                msg = "Timeout when solve equations: {}".format(try_mini_eqs)
                warnings.warn(msg)
            else:
                if target_sym in results:
                    solved = True
                    solved_mini_eqs = copy.copy(mini_eqs[0:p + 1])
                    solved_target_value = results[target_sym]

            if solved:
                tail = p
                if not EquationKiller.accurate_mode:
                    break
            else:
                head = p

        if solved_target_value is None:  # no solved result
            return None, []

        if EquationKiller.accurate_mode:
            for removed_eq in copy.copy(solved_mini_eqs[1:]):
                try_mini_eqs = copy.copy(solved_mini_eqs)
                try_mini_eqs.remove(removed_eq)

                if EquationKiller.sym_simplify:
                    try:
                        EquationKiller.simplification_sym_replace(try_mini_eqs, target_sym)
                    except FunctionTimedOut:
                        msg = "Timeout when simplify equations by sym replace."
                        warnings.warn(msg)

                try:
                    results = EquationKiller.solve(try_mini_eqs, target_sym)  # solve equations
                except FunctionTimedOut:
                    msg = "Timeout when solve equations: {}".format(try_mini_eqs)
                    warnings.warn(msg)
                else:
                    if target_sym in results:
                        solved_mini_eqs.remove(removed_eq)

        for eq in solved_mini_eqs[1:]:
            premise += problem.condition.simplified_equation[eq]

        eq = target_expr - solved_target_value
        value_added = False
        if len(eq.free_symbols) == 1:
            try:
                results = EquationKiller.solve(eq, list(eq.free_symbols)[0])  # solve equations
            except FunctionTimedOut:
                msg = "Timeout when solve equations: {}".format(target_expr - solved_target_value)
                warnings.warn(msg)
            else:
                for sym in results:
                    problem.set_value_of_sym(sym, results[sym], premise)
                    value_added = True
        if not value_added:
            problem.condition.add("Equation", target_expr - solved_target_value, premise, ("solve_eq", None, None))

        if EquationKiller.use_cache:
            EquationKiller.cache_target[eqs_for_cache] = solved_target_value
        return solved_target_value, premise


class GeometryPredicateLogicExecutor:

    @staticmethod
    def run(gpl, problem, letters=None):
        """
        Run reason step by step.
        :param gpl: <dict>, (products, logic_constraints, algebra_constraints, conclusions), geometric predicate logic.
        :param problem: instance of class <Problem>.
        :param letters: preset letters for para selection.
        :return results: <list> of <tuple>, [(letters, premises, conclusions)].
        """
        r = GeometryPredicateLogicExecutor.run_logic(gpl, problem, letters)
        r = GeometryPredicateLogicExecutor.run_algebra(r, gpl, problem)
        return GeometryPredicateLogicExecutor.make_conclusion(r, gpl, problem)

    @staticmethod
    def run_logic(gpl, problem, letters=None):
        """
        Run 'products', 'logic_constraints' of GPL.
        :param gpl: <dict>, (products, logic_constraints, algebra_constraints, conclusions), geometric predicate logic.
        :param problem: instance of class <Problem>.
        :param letters: preset letters for para selection.
        :return r: triplet, (r_ids, r_items, r_vars).
        """
        products = gpl["products"]
        logic_constraints = gpl["logic_constraints"]

        r_ids, r_items = problem.condition.get_ids_and_items_by_predicate_and_variable(products[0][0], products[0][1])
        r_vars = products[0][1]
        for i in range(len(r_items)):  # delete duplicated vars and corresponding item
            r_items[i] = list(r_items[i])
        r_vars = list(r_vars)
        deleted_vars_index = []  # deleted vars index
        for i in range(len(r_vars)):
            if r_vars[i] in r_vars[0:i]:
                deleted_vars_index.append(i)
        for index in deleted_vars_index[::-1]:  # delete
            r_vars.pop(index)
            for i in range(len(r_items)):
                r_items[i].pop(index)

        for i in range(1, len(products)):
            r_ids, r_items, r_vars = GeometryPredicateLogicExecutor.product(
                (r_ids, r_items, r_vars), products[i], problem)

        if letters is not None:  # select result according to letters
            for i in range(len(r_ids))[::-1]:
                selected = True
                for v in letters:
                    if r_items[i][r_vars.index(v)] != letters[v]:
                        selected = False
                        break
                if not selected:
                    r_items.pop(i)
                    r_ids.pop(i)

        for i in range(len(logic_constraints)):
            r_ids, r_items, r_vars = GeometryPredicateLogicExecutor.constraint_logic(
                (r_ids, r_items, r_vars), logic_constraints[i], problem)

        if letters is not None:  # select result according to letters
            for i in range(len(r_ids))[::-1]:
                selected = True
                for v in letters:
                    if r_items[i][r_vars.index(v)] != letters[v]:
                        selected = False
                        break
                if not selected:
                    r_items.pop(i)
                    r_ids.pop(i)

        return r_ids, r_items, r_vars

    @staticmethod
    def run_algebra(r, gpl, problem):
        """
        Run 'algebra_constraints' of GPL.
        :param r: triplet, (r_ids, r_items, r_vars).
        :param gpl: <dict>, (products, logic_constraints, algebra_constraints, conclusions), geometric predicate logic.
        :param problem: instance of class <Problem>.
        :return results: <list> of <tuple>, [(letters, premises, conclusions)].
        """
        algebra_constraints = gpl["algebra_constraints"]
        r_ids, r_items, r_vars = r
        if len(r_ids) == 0:
            return [], [], r_vars

        for i in range(len(algebra_constraints)):
            r_ids, r_items, r_vars = GeometryPredicateLogicExecutor.constraint_algebra(
                (r_ids, r_items, r_vars), algebra_constraints[i], problem)

        return r_ids, r_items, r_vars

    @staticmethod
    def make_conclusion(r, gpl, problem):
        """
        Make conclusion according given reasoned points sets 'r' and GDL 'conclusions'.
        :param r: triplet, (r_ids, r_items, r_vars).
        :param gpl: <dict>, (products, logic_constraints, algebra_constraints, conclusions), geometric predicate logic.
        :param problem: instance of class <Problem>.
        :return results: <list> of <tuple>, [(letters, premises, conclusions)].
        """
        if len(r[0]) == 0:
            return []
        conclusions = gpl["conclusions"]
        results = []
        r_ids, r_items, r_vars = r
        for i in range(len(r_ids)):
            letters = {}
            for j in range(len(r_vars)):
                letters[r_vars[j]] = r_items[i][j]
            conclusion = []

            for predicate, item in conclusions:
                if predicate == "Equal":  # algebra conclusion
                    eq = get_equation_from_tree(problem, item, True, letters)
                    conclusion.append(("Equation", eq))
                else:  # logic conclusion
                    item = tuple(letters[i] for i in item)
                    conclusion.append((predicate, item))
            results.append((letters, r_ids[i], conclusion))

        return results

    @staticmethod
    def product(r1, r2_logic, problem):
        """
        Constrained Cartesian product.
        :param r1: triplet, (r1_ids, r1_items, r1_vars).
        :param r2_logic: geo predicate logic, such as ['Collinear', ['a', 'b', 'c']].
        :param problem: instance of class <Problem>.
        :return r: triplet, (r_ids, r_items, r_vars), reasoning result.
        >> product(([(1,), (2,)], [('A', 'B'), ('C', 'D')], ['a', 'b']),
                   ['Line', ['b', 'c']],
                   problem)
        ([(1, 3), (2, 4)], [('A', 'B', 'C'), ('C', 'D', 'E')], ['a', 'b', 'c'])
        """
        r1_ids, r1_items, r1_vars = r1
        if len(r1_ids) == 0:
            return [], [], r1_vars
        r2_ids, r2_items = problem.condition.get_ids_and_items_by_predicate_and_variable(r2_logic[0], r2_logic[1])
        r2_vars = r2_logic[1]

        inter = list(set(r1_vars) & set(r2_vars))  # intersection
        for i in range(len(inter)):
            inter[i] = (r1_vars.index(inter[i]), r2_vars.index(inter[i]))  # change to index

        difference = list(set(r2_vars) - set(r1_vars))  # difference
        for i in range(len(difference)):
            difference[i] = r2_vars.index(difference[i])  # change to index

        r_ids = []  # result
        r_items = []
        r_vars = list(r1_vars)
        for dif in difference:  # add r2 vars
            r_vars.append(r2_vars[dif])
        r_vars = tuple(r_vars)

        for i in range(len(r1_items)):
            r1_data = r1_items[i]
            for j in range(len(r2_items)):
                r2_data = r2_items[j]
                passed = True
                for r1_i, r2_i in inter:
                    if r1_data[r1_i] != r2_data[r2_i]:  # the corresponding points are inconsistent.
                        passed = False
                        break
                if passed:
                    item = list(r1_data)
                    for dif in difference:
                        item.append(r2_data[dif])
                    r_items.append(tuple(item))
                    r_ids.append(tuple(set(list(r1_ids[i]) + list(r2_ids[j]))))
        return r_ids, r_items, r_vars

    @staticmethod
    def constraint_logic(r1, r2_logic, problem):
        """
        Logic constraint.
        :param r1: triplet, (r1_ids, r1_items, r1_vars).
        :param r2_logic: geo predicate logic, such as ['Collinear', ['a', 'b', 'c']].
        :param problem: instance of class <Problem>.
        :return r: triplet, (r_ids, r_items, r_vars), reasoning result.
        >> problem.conditions['Line'].get_item_by_id  # supposed
        {3: ('B', 'C')}
        >> constraint_logic(([(1,), (2,)], [('A', 'B', 'C'), ('C', 'D', 'E')], ['a', 'b', 'c']),
                            ['Line', ['b', 'c']],
                            problem)
        ([(1, 3)], [('A', 'B', 'C')], ['a', 'b', 'c'])
        >> constraint_logic(([(1,), (2,)], [('A', 'B', 'C'), ('C', 'D', 'E')], ['a', 'b', 'c']),
                            ['~Line', ['b', 'c']],
                            problem)
        ([(2,)], [('C', 'D', 'E')], ['a', 'b', 'c'])
        """
        r1_ids, r1_items, r1_vars = r1
        if len(r1_ids) == 0:
            return [], [], r1_vars
        oppose = False  # indicate '&' or '&~'
        if "~" in r2_logic[0]:
            r2_logic = list(r2_logic)
            r2_logic[0] = r2_logic[0].replace("~", "")
            r2_logic = tuple(r2_logic)
            oppose = True
        index = [r1_vars.index(v) for v in r2_logic[1]]
        r_ids = []
        r_items = []

        if not oppose:  # &
            for i in range(len(r1_items)):
                r2_item = tuple(r1_items[i][j] for j in index)
                if r2_item in problem.condition.get_items_by_predicate(r2_logic[0]):
                    r2_id = problem.condition.get_id_by_predicate_and_item(r2_logic[0], r2_item)
                    r_ids.append(tuple(set(list(r1_ids[i]) + [r2_id])))
                    r_items.append(r1_items[i])
        else:  # &~
            for i in range(len(r1_items)):
                r2_item = tuple(r1_items[i][j] for j in index)
                if r2_item not in problem.condition.get_items_by_predicate(r2_logic[0]):
                    r_ids.append(r1_ids[i])
                    r_items.append(r1_items[i])
        return r_ids, r_items, r1_vars

    @staticmethod
    def constraint_algebra(r1, r2_algebra, problem):
        """
        Algebra constraint.
        :param r1: triplet, (r1_ids, r1_items, r1_vars).
        :param r2_algebra: geo predicate logic, such as ['Equal', [['Length', ['a', 'b']], 5]].
        :param problem: instance of class <Problem>.
        :return r: triplet, (r_ids, r_items, r_vars), reasoning result.
        >> problem.conditions['Equation'].get_value_of_sym  # supposed
        {ll_ab: 1}
        >> problem.conditions['Equation'].get_item_by_id  # supposed
        {3: ll_ab - 1}
        >> constraint_algebra(([(1,), (2,)], [('A', 'B', 'C'), ('C', 'D', 'E')], ['a', 'b', 'c']),
                              ['Equal', [['Length', ['a', 'b']], 1]],
                              problem)
        ([(1, 3)], [('A', 'B', 'C')], ['a', 'b', 'c'])
        >> constraint_algebra(([(1,), (2,)], [('A', 'B', 'C'), ('C', 'D', 'E')], ['a', 'b', 'c']),
                              ['~Equal', [['Length', ['a', 'b']], 1]],
                              problem)
        ([(2,)], [('C', 'D', 'E')], ['a', 'b', 'c'])
        """
        r1_ids, r1_items, r1_vars = r1
        if len(r1_ids) == 0:
            return [], [], r1_vars
        oppose = False  # indicate '&' or '&~'
        if "~" in r2_algebra[0]:
            r2_algebra = list(r2_algebra)
            r2_algebra[0] = r2_algebra[0].replace("~", "")
            r2_algebra = tuple(r2_algebra)
            oppose = True
        r_ids = []
        r_items = []

        if not oppose:  # &
            for i in range(len(r1_items)):
                letters = {}
                for j in range(len(r1_vars)):
                    letters[r1_vars[j]] = r1_items[i][j]
                eq = get_equation_from_tree(problem, r2_algebra[1], True, letters)
                try:
                    result, premise = EquationKiller.solve_target(eq, problem)
                except FunctionTimedOut:
                    msg = "Timeout when solve target: {}".format(str(eq))
                    warnings.warn(msg)
                else:
                    if result is not None and rough_equal(result, 0):  # meet constraints
                        r_id = tuple(set(premise + list(r1_ids[i])))
                        r_ids.append(r_id)
                        r_items.append(r1_items[i])

        else:  # &~
            for i in range(len(r1_items)):
                letters = {}
                for j in range(len(r1_vars)):
                    letters[r1_vars[j]] = r1_items[i][j]
                eq = get_equation_from_tree(problem, r2_algebra[1], True, letters)
                try:
                    result, premise = EquationKiller.solve_target(eq, problem)
                except FunctionTimedOut:
                    msg = "Timeout when solve target: {}".format(str(eq))
                    warnings.warn(msg)
                else:
                    if result is None or not rough_equal(result, 0):  # meet constraints
                        r_id = tuple(set(premise + list(r1_ids[i])))
                        r_ids.append(r_id)
                        r_items.append(r1_items[i])

        return r_ids, r_items, r1_vars
