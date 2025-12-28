from formalgeo.tools import entity_letters, _parse_dependent_entities
from formalgeo.tools import _parse_algebraic_forms, _parse_gpl_to_tree, _negation_inward, _format_algebraic_forms
from formalgeo.tools import _parse_construction, _parse_theorem, _replace_instance, _replace_expr, _parse_geometric_fact
from formalgeo.tools import _parse_geometric_fact, _parse_algebraic_fact
from formalgeo.tools import _satisfy_algebraic, precision
from sympy import symbols, nonlinsolve, tan, pi, FiniteSet, EmptySet
from func_timeout import func_timeout, FunctionTimedOut
import random
import copy


class GeometricConfiguration:
    def __init__(self, parsed_gdl, random_seed=0, sample_max_number=1, sample_max_epoch=1000, sample_rate=1.2,
                 timeout=2):
        """The <GeometricConfiguration> class stores the construction and reasoning process of a configuration.

        Args:
            parsed_gdl (dict): Parsed Geometry Definition Language (GDL).

        Attributions:
            self.parsed_gdl (dict): Parsed Geometry Definition Language (GDL). You can save it to json to view the specific
            format. The function em.formalgeo.parser.parse_gdl demonstrates the detailed parsing process of GDL.

            self.facts (list): fact_id -> (predicate, instance, premise_ids, entity_ids, operation_id). Store all known
            facts of the current problem. The index of element is its fact_id. Specifically:
                1.predicate (str): The type of fact, such as 'Line', 'Parallel', 'Equation', etc.
                2.instance (tuple): The instance of fact, categorized into geometric relations and algebraic relations,
                such as ('A', 'B', 'C'), 'MeasureOfAngle(lk)-1', etc.
                3.premise_ids (tuple): The premise of the current fact.
                4.entity_ids (tuple): The dependent entities of the current fact.
                5.operation_id (int): The operation that yielded the current fact.
            examples: [('Point', 'A', (,), (,), 0),  # free entity
                       ('Line', 'l', (,), (3, 6), 3),  # constructed entity
                       ('PointOnLine', ('A', 'l'), (3,), (3, 6), 3),  # initial geometric relations
                       ('Perpendicular', ('l', 'm'), (7, 8, 9), (2, 3), 6),  # inferred geometric relations
                       ('Equation', 'lk.ma-1', (10, 11), (1, 4), 8)]  # algebraic relations

            self.id (dict): (predicate, instance) -> fact_id. Mapping from fact to fact_id.
            examples: {('Point', ('A',)): 0, ('PointOnLine', ('A', 'l')): 5, ('Equation', 'MeasureOfAngle(lk)-1'): 12}

            self.groups (list): operation_id -> [fact_id]. A tuple of fact_id that share the same operation_id. The
            index of element is its operation_id.
            examples: [[0, 1, 2], [3, 4], [5, 6, 7, 8]]

            self.ids_of_predicate (dict): predicate -> [fact_id]. The fact_id of facts with the same predicate.
            examples: {'Point': [0, 1, 3, 4], 'PointOnLine': [5, 7]}

            self.instances_of_predicate (dict): predicate -> [instance]. The instance of facts with the same predicate.
            examples: {'Point': ['A', 'B', 'C', 'D'], 'PointOnLine': [('A', l), ('B', l)]}

            self.operations (list): operation_id -> operation. Mapping from operation_id to operation. The index of
            element is its operation_id.
            examples: ['Point(A): PointOnLine(A, l)', 'perpendicular_judgment_angle(l,k)']

            self.constructions (list): operation_id -> (constraints, target_entities, dependent_entities, solved_values).
            Store the constraints obtained from parsing each construction statement. The index of element is its
            operation_id. specifically:
                1.constraints (list): The disjunctive normal form of constraints, where each element is a conjunction
                with the form of {'eq': [], 'l': [], 'leq': [], 'g': [], 'geq': [], 'ueq': []}.
                2.target_entities (dict): Tuple of symbols related to the current entity, which need to be solved.
                3.dependent_entities (dict): Tuple of symbols related to the dependency entities of the current entity,
                which are replaced with values before solving.
                4.solved_values (list): List of solved values, which stores multiple values obtained from solving, where
                the values correspond one-to-one with target_syms.
            examples: [([{'eq': [A.y-l.k*A.x-l.b], 'l': [], 'leq': [], 'g': [], 'geq': [], 'ueq': []}],
                       (l.k, l.b), (A.x, A.y), [(0, 0), (1, 1), ..., (999, 999)]),  # infinite solutions
                       ([{'eq': [A.y-l.k*A.x-l.b, B.y-l.k*B.x-l.b], 'l': [], 'leq': [], 'g': [], 'geq': [], 'ueq': []}],
                       (A.x, A.y, B.x, B.y), (l.k, l.b), [(1, 0)])]  # finite solutions

            self.sym_of_attr (dict): attr -> sym. The mapping from attribute names to attribute symbols.
            examples: {'A.x': A.x, 'l.k': l.k,  # parameter of entity
                       'LengthOfSegment(AB)': LengthOfSegment(AB),  # attribution of entity
                       'LengthOfSegment(BA)': LengthOfSegment(AB)}  # attribution of entity

            self.attr_of_sym (dict): sym -> [attr]. The mapping from attribute symbols to attribute names. An attribute
            symbol may have multiple attribute names.
            examples: {A.x: ['A.x'], l.k: ['l.k'],  # parameter of entity
                       LengthOfSegment(AB): ['LengthOfSegment(AB)', 'LengthOfSegment(BA)']}  # attribution of entity

            self.value_of_sym (dict): sym -> value. The value of a symbol.
            examples: {A.x: 0.25846578, l.k: 0.89568755, LengthOfSegment(AB): 5, MeasureOfAngle(lk): 90}

            self.equations (list): [[simplified_equation, original_equation_fact_id, dependent_equation_fact_id]]. Store
            the simplified equation, along with the fact_id of its original equation and the dependent equations used
            in the simplification process. Taking the equation a + b - c = 0 as an example, if the fact_id of a + b - c = 0
            and c - 2 = 0 are 1 and 2, respectively, then the element (a + b - 2, 1, [2]) would be added to self.equations.
            specifically:
                1.simplified_equation (equation): The simplified equation.
                2.original_equation_fact_id (int): The fact_id of its original equation.
                3.dependent_equation_fact_id (list): The dependent equations used in the simplification process. Note that
                all dependent equations are solved values. Whenever a symbol sym is successfully solved to obtain a value,
                an algebraic relation sym - value = 0 is constructed and added to the self.facts. Simultaneously, For each
                element in self.equations, all sym in the  simplified_equation are replaced with its value, and the fact_id
                of the algebraic relation sym - value = 0 is added to dependent_equation_fact_id. If the simplified_equation
                contains no unsolved symbols, remove current element from self.equations.
            example: [[a + b - 2, 1, [2]], [d + e, 2, []]]

        Methods:
            self.construct(entity): Construct a geometric entity (point, line, circle). If successfully construct the
            entity, return True; otherwise, return False.

            self.apply(theorem): Apply a theorem. If applying the theorem adds new conditions, return True; otherwise,
            return False.
        """
        self.parsed_gdl = parsed_gdl
        self.letters = set(entity_letters)  # available entity letters
        self.random = random.Random(random_seed)  # the random number generator of the current instance
        self.sample_max_number = sample_max_number  # Maximum sampling quantity for symbolic value random sampling
        self.sample_max_epoch = sample_max_epoch  # Maximum epoch of sampling attempts
        self.sample_rate = sample_rate  # Range expansion ratio during random sampling
        self.range = {'x_max': 1, 'x_min': -1, 'y_max': 1, 'y_min': -1}  # Coordinate range of all points
        self.timeout = timeout  # Maximum tolerance time for solving algebraic premises

        # construction
        self.constructions = {}  # operation_id -> (t_entity, d_entities, constraints, solved_values)

        # forward solving
        self.facts = []  # fact_id -> (predicate, instance, {premise_id}, {entity_id}, operation_id)
        self.fact_id = {}  # (predicate, instance) -> fact_id
        self.predicate_to_fact_ids = {}  # predicate -> {fact_id}
        for relation in list(self.parsed_gdl['Entities']) + list(self.parsed_gdl['Relations']) + ['Eq']:
            self.predicate_to_fact_ids[relation] = set()

        # backward solving
        self.goals = []  # goal_id -> (sub_goal_id, operation_id, root_sub_goal_id)
        self.status_of_goal = {}  # goal_id -> int (0: not check, 1: solved, -1: skip or unsolved)
        self.sub_goals = []  # sub_goal_id -> (predicate, instance, goal_id, root_sub_goal_id)
        self.status_of_sub_goal = {}  # sub_goal_id -> int (0: not check, 1: solved, -1: skip or unsolved)
        self.premise_ids_of_sub_goal = {}  # sub_goal_id -> {premise_id}
        self.leaf_sub_goal_ids = {}  # sub_goal_id -> (left_sub_goal_id, right_sub_goal_id) or None
        self.leaf_goal_ids = {}  # sub_goal_id -> {leaf_goal_id}
        self.sub_goal_ids = {}  # (predicate, instance) -> {sub_goal_id}
        self.predicate_to_sub_goal_ids = {}  # predicate -> {sub_goal_id}
        for relation in list(self.parsed_gdl['Entities']) + list(self.parsed_gdl['Relations']) + ['Eq']:
            self.predicate_to_sub_goal_ids[relation] = set()
        self.predicate_to_sub_goal_ids['Operator'] = set()

        # operations
        self.operations = []  # operation_id -> operation
        self.groups = {}  # operation_id -> [fact_id] or [goal_id]

        # theorem instance
        self.theorem_instances = {}  # theorem_name -> {theorem_instance: (premises, conclusion)}

        # algebraic system
        self.entity_sym_to_value = {}  # entity_related_sym -> value
        self.sym_to_value = {}  # (solved) relation_related_sym -> value
        self.sym_to_sym = {}  # sym_multiple_form -> sym_unified_form
        self.sym_to_syms = {}  # sym_unified_form -> {sym_multiple_form}
        self.equations = {}  # group_id -> ((simplified_eq), ({premise_id}), {sym})
        self.group_count = 0  # generate group_id
        self.algebraic_sub_goal = {}  # sub_goal_id -> ({group_id}, {syms})
        self.solved_target_cache = {}  # target_expr -> {premise_id}
        self.attempted_equations_cache = {}  # (target_dependent_equation) -> passed

    def construct(self, construction, added=True):
        """Construct a new point, line, or circle.
        1.Parse the geometric construction statement, extract the target entity, implicit entities, and dependent
        entities, perform entity existence checks, format validity checks, and linear construction checks, and add the
        relations that do not contain implicit entities to the added_facts.

        2.Combine all constraints together, and update the implicit entities during the merging process.

        3.Solve the constraints to obtain the values of all unknown variables. For results involving random variables,
        generate random sampled values. Variables related to implicit entities, although solved for, will be ignored.
        Only the values of the variables related to the target entities are ultimately returned. This aligns with the
        first step of discarding relations that contain implicit entities. If an entity is implicit, we are not
        concerned with the implicit entity itself or its associated relations. The purpose of implicit entities is
        solely to transmit constraint relationships between the target entities and the dependent entities.

        4.Add all content generated by the current geometric construction statement to the database. This includes the
        current action, newly generated entities and their parameter values, and the generated relations, etc. Note that
        we also record the current constraints and their other solved values. This is primarily to serve the rollback
        functionality in future versions and is not used in the current version.

        Args:
            construction (str): Constructed entities and constraints. The constraints can be either constraints defined
            in GDL or algebraic constraints. The constraints need to be connected by '&'. Each constraint must include
            the entity currently being constructed, and the remaining entities must all be known entities. Furthermore,
            the temporary forms of entities are also permitted for use here.
            examples: 'Point(A):FreePoint(A)'  # free entity
                      'Line(l):PointOnLine(A,l)&PointOnLine(B,l)'  # constraints defined in GDL
                      'Point(C):Eq(Sub(AC.dpp,CB.dpp))'  # algebraic constraints

        Returns:
            result (bool): If successfully construct the entity, return True; otherwise, return False.
        """
        if added:
            random_instance = self.random
        else:
            random_instance = copy.copy(self.random)

        # construction
        parsed_construction = _parse_construction(construction, self.parsed_gdl)
        for branch in range(len(parsed_construction)):
            t_entities, d_entities, equations, inequalities, added_facts = parsed_construction[branch]

            # parse entity symbols
            t_syms = []
            for entity, instance in t_entities:
                if entity == 'Point':
                    t_syms.append(symbols(instance[0] + '.x'))
                    t_syms.append(symbols(instance[0] + '.y'))
                elif entity == 'Line':
                    t_syms.append(symbols(instance[0] + '.k'))
                    t_syms.append(symbols(instance[0] + '.b'))
                else:
                    t_syms.append(symbols(instance[0] + '.u'))
                    t_syms.append(symbols(instance[0] + '.v'))
                    t_syms.append(symbols(instance[0] + '.r'))

            # get dependent entity id and check whether dependent entity exits
            premise_ids = set()
            for dependent_entity in d_entities:
                premise_ids.add(self.fact_id[dependent_entity])

            # solve constraint
            solved_values = self._solve_constraints(t_syms, equations, inequalities, random_instance)
            if len(solved_values) == 0:  # no solved entity, solve next branch
                continue

            if not added:
                return True

            # add entity to self.operations
            operation_id = self._add_operation(construction)

            # add target entity to self.facts
            for entity, instance in t_entities:
                self._add_fact(entity, instance, premise_ids, premise_ids, operation_id)

            # set target entity's attribution to solved value
            solved_value = solved_values.pop(0)
            for i in range(len(t_syms)):
                self.entity_sym_to_value[t_syms[i]] = solved_value[i]
                entity, attr = str(t_syms[i]).split('.')
                if attr == 'x':  # update sample range
                    if solved_value[i] > self.range['x_max']:
                        self.range['x_max'] = solved_value[i]
                    elif solved_value[i] < self.range['x_min']:
                        self.range['x_min'] = solved_value[i]
                elif attr == 'y':
                    if solved_value[i] > self.range['y_max']:
                        self.range['y_max'] = solved_value[i]
                    elif solved_value[i] < self.range['y_min']:
                        self.range['y_min'] = solved_value[i]

            # add relations to self.facts
            for predicate, instance in added_facts:
                entity_ids = self._get_entity_ids(predicate, instance)
                self._add_fact(predicate, instance, premise_ids, entity_ids, operation_id)

            # a certain branch completes construction, return True
            return True

        # no branch completes construction, return False
        return False

    def _solve_constraints(self, t_syms, equations, inequalities, random_instance):
        constraint_values = []  # list of constraint values, contains symbols, such as [[y, y - 1], [x, 0.5]]
        solved_values = []  # list of values, such as [[1, 0.5], [1.5, 0.5]]

        replaced_equations = []  # expr
        for expr in equations:
            expr = expr.subs(self.entity_sym_to_value)
            if len(expr.free_symbols) == 0:
                if not _satisfy_algebraic['Eq'](expr):
                    return solved_values
                continue
            replaced_equations.append(expr)
        replaced_inequalities = []  # (algebraic_relation, expr)
        for algebraic_relation, expr in inequalities:
            expr = expr.subs(self.entity_sym_to_value)
            if len(expr.free_symbols) == 0:
                if not _satisfy_algebraic[algebraic_relation](expr):
                    return solved_values
                continue
            replaced_inequalities.append((algebraic_relation, expr))

        if len(replaced_equations) == 0:  # free entity
            constraint_values.append(t_syms)
        else:
            try:
                equation_solutions = func_timeout(
                    timeout=self.timeout,
                    func=nonlinsolve,
                    args=(replaced_equations, t_syms)
                )
            except FunctionTimedOut:
                return solved_values

            if equation_solutions is EmptySet:
                e_smg = f'Equations no solution: {equations}'
                raise Exception(e_smg)

            if type(equation_solutions) is not FiniteSet:
                return solved_values

            for equation_solution in list(equation_solutions):
                has_free_symbol = False
                for value in equation_solution:
                    if len(value.free_symbols) > 0:
                        has_free_symbol = True
                        break
                if has_free_symbol:  # has free symbols
                    constraint_values.append(equation_solution)
                else:  # no free sym
                    sym_to_value = dict(zip(t_syms, equation_solution))
                    satisfied = True
                    for algebraic_relation, expr in replaced_inequalities:
                        if not _satisfy_algebraic[algebraic_relation](expr, sym_to_value):
                            satisfied = False
                            break
                    if satisfied:
                        solved_values.append([value.evalf(n=precision, chop=False) for value in equation_solution])

        if len(constraint_values) == 0:  # no random sampling required
            return solved_values

        epoch = 0  # start random sampling
        while len(solved_values) < self.sample_max_number and epoch < self.sample_max_epoch:
            constraint_value = constraint_values[epoch % len(constraint_values)]  # iterative select constraint value
            random_value = self._random_value(t_syms, constraint_value, random_instance)
            sym_to_value = dict(zip(t_syms, random_value))

            satisfied = True
            for algebraic_relation, expr in replaced_inequalities:
                if not _satisfy_algebraic[algebraic_relation](expr, sym_to_value):
                    satisfied = False
                    break
            if satisfied:
                solved_values.append(random_value)

            epoch += 1

        return solved_values

    def _random_value(self, syms, constraint_value, random_instance):
        random_values = {}
        free_symbols = set()
        for i in range(len(syms)):  # save k for sampling b
            if len(constraint_value[i].free_symbols) == 0:
                random_values[syms[i]] = float(constraint_value[i])
            else:
                free_symbols.update(constraint_value[i].free_symbols)
        free_symbols = sorted(list(free_symbols), key=str)  # sorting ensures reproducibility

        for sym in free_symbols:  # sample k first, because the value of k is used when sampling b
            if str(sym).split('.')[1] != 'k':
                continue
            random_k = tan(random_instance.random.uniform(-89, 89) * pi / 180)
            random_values[sym] = random_k

        for sym in free_symbols:
            if str(sym).split('.')[1] in ['x', 'u']:
                middle_x = (self.range['x_max'] + self.range['x_min']) / 2
                range_x = (self.range['x_max'] - self.range['x_min']) / 2 * self.sample_rate
                random_x = random_instance.random.uniform(float(middle_x - range_x), float(middle_x + range_x))
                random_values[sym] = random_x
            elif str(sym).split('.')[1] in ['y', 'v']:
                middle_y = (self.range['y_max'] + self.range['y_min']) / 2
                range_y = (self.range['y_max'] - self.range['y_min']) / 2 * self.sample_rate
                random_y = random_instance.random.uniform(float(middle_y - range_y), float(middle_y + range_y))
                random_values[sym] = random_y
            elif str(sym).split('.')[1] == 'r':
                max_distance = float(((self.range['y_max'] - self.range['y_min']) ** 2 +
                                      (self.range['x_max'] - self.range['x_min']) ** 2) ** 0.5) / 2 * self.sample_rate
                random_r = random_instance.random.uniform(0, max_distance)
                random_values[sym] = random_r
            elif str(sym).split('.')[1] == 'b':
                middle_x = (self.range['x_max'] + self.range['x_min']) / 2
                range_x = (self.range['x_max'] - self.range['x_min']) / 2 * self.sample_rate
                middle_y = (self.range['y_max'] + self.range['y_min']) / 2
                range_y = (self.range['y_max'] - self.range['y_min']) / 2 * self.sample_rate

                k_value = random_values[symbols(str(sym).split('.')[0] + '.k')]
                b_range = [float(middle_y + range_y - k_value * (middle_x - range_x)),
                           float(middle_y - range_y - k_value * (middle_x - range_x)),
                           float(middle_y + range_y - k_value * (middle_x + range_x)),
                           float(middle_y - range_y - k_value * (middle_x + range_x))]
                random_b = random_instance.random.uniform(min(b_range), max(b_range))
                random_values[sym] = random_b

        solved_value = [item.subs(random_values).evalf(n=15, chop=False) for item in constraint_value]

        return solved_value

    def apply(self, theorem):
        """Apply a theorem with parameterized form or parameter-free form.

        Args:
            theorem (str): Theorem to be applied. Two forms: a parameterized form and a parameter-free form.
            examples: 'adjacent_complementary_angle(l,k)'  # parameterized form
                      'adjacent_complementary_angle'  # parameter-free form

        Returns:
            result (bool): If applying the theorem adds new conditions, return True; otherwise, return False.
        """
        theorem_name, theorem_para = _parse_theorem(theorem, self.parsed_gdl)
        update = False
        all_sub_goal_ids = set()

        if theorem_para is not None:  # parameterized form
            if theorem_name in self.theorem_instances:
                if theorem_para not in self.theorem_instances[theorem_name]:
                    return False
                premises, conclusion = self.theorem_instances[theorem_name][theorem_para]
            else:
                generated = self._generate_premises_and_conclusion(theorem_name, theorem_para)
                if generated is None:
                    return False
                premises, conclusion = generated

            passed, premise_ids = self._recursively_check_premises(premises)
            if not passed:
                return False

            # add conclusion
            operation_id = self._add_operation(theorem_name + '(' + ','.join(theorem_para) + ')')
            entity_ids = self._get_entity_ids(conclusion[0], conclusion[1])
            fact_id, sub_goal_ids = self._add_fact(conclusion[0], conclusion[1], premise_ids, entity_ids, operation_id)

            # record the influenced sub goal nodes
            if fact_id is not None:
                all_sub_goal_ids.update(sub_goal_ids)
                update = True

        else:  # parameter-free form
            self._generate_theorem_instance(theorem_name)

            for theorem_instance in self.theorem_instances[theorem_name]:
                premises, conclusion = self.theorem_instances[theorem_name][theorem_instance]
                passed, premise_ids = self._recursively_check_premises(premises)
                if not passed:
                    continue

                # add conclusion
                operation_id = self._add_operation(theorem_name + '(' + ','.join(theorem_instance) + ')')
                entity_ids = self._get_entity_ids(conclusion[0], conclusion[1])
                fact_id, sub_goal_ids = self._add_fact(
                    conclusion[0], conclusion[1], premise_ids, entity_ids, operation_id)

                # remove applied theorem_instance
                self.theorem_instances[theorem_name].pop(theorem_instance)

                # record the influenced sub goal nodes
                if fact_id is not None:
                    all_sub_goal_ids.update(sub_goal_ids)
                    update = True

        # update influenced sub goal nodes
        self._check_sub_goals(all_sub_goal_ids)
        return update

    def _generate_premises_and_conclusion(self, theorem_name, theorem_para):
        if theorem_name in self.theorem_instances:
            if theorem_para not in self.theorem_instances[theorem_name]:
                return None
            return self.theorem_instances[theorem_name][theorem_para]
        else:
            replace = dict(zip(self.parsed_gdl['Theorems'][theorem_name]['paras'], theorem_para))

            for entity, entity_instance in self.parsed_gdl['Theorems'][theorem_name]['geometric_constraints']:
                entity_instance = _replace_instance(entity_instance, replace)
                if (entity, entity_instance) not in self.fact_id:
                    return None

            passed = self._recursively_check_algebraic_forms(
                self.parsed_gdl['Theorems'][theorem_name]['algebraic_forms'], replace)
            if not passed:
                return None

            premises = self._recursively_generate_premises(
                self.parsed_gdl['Theorems'][theorem_name]['premises'], replace)
            if premises is None:
                return None

            conclusion_predicate, conclusion_instance = self.parsed_gdl['Theorems'][theorem_name]['conclusion']
            if conclusion_predicate == 'Eq':
                conclusion_instance = self._adjust_expr(_replace_expr(conclusion_instance, replace))
                if len(conclusion_instance.free_symbols) == 0 and not _satisfy_algebraic['Eq'](conclusion_instance):
                    return None
            else:
                conclusion_instance = _replace_instance(conclusion_instance, replace)

            return premises, (conclusion_predicate, conclusion_instance)

    def _generate_theorem_instance(self, theorem_name):
        if theorem_name not in self.theorem_instances:
            theorem_gdl = self.parsed_gdl['Theorems'][theorem_name]
            theorem_paras = theorem_gdl['paras']
            algebraic_forms = theorem_gdl['algebraic_forms']
            conclusion_predicate, conclusion_instance = theorem_gdl['conclusion']

            self.theorem_instances[theorem_name] = {}
            if conclusion_predicate == 'Eq':  # algebraic conclusion
                paras, instances = self._recursively_generate_theorem_instance(algebraic_forms, None)
                for instance in instances:
                    replace = dict(zip(paras, instance))
                    conclusion_instance = _replace_expr(conclusion_instance, replace)
                    if (len(conclusion_instance.free_symbols) == 0 or
                            (conclusion_predicate, conclusion_instance) in self.fact_id):
                        continue

                    theorem_premises = self._recursively_generate_premises(theorem_gdl['premises'], replace)
                    if theorem_premises is None:
                        continue

                    theorem_instance = tuple([instance[paras.index(p)] for p in theorem_paras])

                    self.theorem_instances[theorem_name][theorem_instance] = (
                        theorem_premises, (conclusion_predicate, conclusion_instance)
                    )
            else:  # geometric conclusion
                paras, instances = self._recursively_generate_theorem_instance(algebraic_forms, None)
                for instance in instances:
                    replace = dict(zip(paras, instance))
                    conclusion_instance = _replace_instance(conclusion_instance, replace)
                    if (conclusion_predicate, conclusion_instance) in self.fact_id:
                        continue

                    theorem_premises = self._recursively_generate_premises(theorem_gdl['premises'], replace)
                    if theorem_premises is None:
                        continue

                    theorem_instance = tuple([instance[paras.index(p)] for p in theorem_paras])

                    self.theorem_instances[theorem_name][theorem_instance] = (
                        theorem_premises, (conclusion_predicate, conclusion_instance)
                    )

    def _recursively_generate_theorem_instance(self, algebraic_forms, theorem_instances):
        # conjunction: (..., '&', ...)
        if algebraic_forms[1] == '&':
            left_theorem_instances = self._recursively_generate_theorem_instance(
                algebraic_forms[0], theorem_instances)
            right_theorem_instances = self._recursively_generate_theorem_instance(
                algebraic_forms[2], left_theorem_instances)
            return right_theorem_instances
        # disjunction: (..., '|', ...)
        elif algebraic_forms[1] == '|':
            left_paras, left_instances = self._recursively_generate_theorem_instance(
                algebraic_forms[0], theorem_instances)
            right_paras, right_instances = self._recursively_generate_theorem_instance(
                algebraic_forms[2], theorem_instances)

            if left_paras == right_paras:  # merge left and right
                left_instances.update(right_instances)
            else:
                for right_instance in right_instances:  # left and right must have the same paras
                    left_instance = tuple([right_instance[right_paras.index(p)] for p in left_paras])
                    left_instances.add(left_instance)

            return left_paras, left_instances
        # atomic node: (algebraic_relation, expr, dependent_entities)
        else:
            algebraic_relation, expr, dependent_entities = algebraic_forms
            if theorem_instances is not None:
                paras, instances = theorem_instances
                paras = list(paras)
                instances = list(instances)
            else:
                paras = []
                instances = [()]

            for p in dependent_entities:  # Cartesian product
                if p in paras:
                    continue
                paras.append(p)
                new_instances = []
                for instance in instances:
                    for fact_id in self.predicate_to_fact_ids[dependent_entities[p]]:
                        entity_instance = self.facts[fact_id][1]
                        new_instance = list(instance)
                        new_instance.append(entity_instance)
                        new_instances.append(tuple(new_instance))

                instances = new_instances

            for i in range(len(instances))[::-1]:
                replace = dict(zip(paras, instances[i]))
                replaced_expr = expr.subs(replace)
                if not _satisfy_algebraic[algebraic_relation](replaced_expr, self.entity_sym_to_value):
                    instances.pop(i)

            return tuple(paras), set(instances)

    def _recursively_generate_premises(self, premises_gpl, replace):
        # conjunction : (..., '&', ...)
        if premises_gpl[1] == '&':
            left_side = self._recursively_generate_premises(premises_gpl[0], replace)
            right_side = self._recursively_generate_premises(premises_gpl[2], replace)
            if left_side is not None:
                if right_side is not None:
                    return left_side, '&', right_side
            return None

        # disjunction: (..., '|', ...)
        elif premises_gpl[1] == '|':
            left_side = self._recursively_generate_premises(premises_gpl[0], replace)
            right_side = self._recursively_generate_premises(premises_gpl[2], replace)
            if left_side is not None:
                if right_side is not None:
                    return left_side, '|', right_side
                else:
                    return left_side
            else:
                if right_side is not None:
                    return right_side
                else:
                    return None

        # atomic node: (predicate, instance)
        else:
            predicate, instance = premises_gpl
            if predicate == 'Eq':
                instance = self._adjust_expr(_replace_expr(instance, replace))
                if len(instance.free_symbols) == 0 and not _satisfy_algebraic['Eq'](instance):
                    return None
            else:
                instance = _replace_instance(instance, replace)
                if predicate in {'Point', 'Line', 'Circle'} and (predicate, instance) not in self.fact_id:
                    return None
            return predicate, instance

    def _recursively_check_premises(self, premises):
        # conjunction : (..., '&', ...)
        if premises[1] == '&':
            left_passed, left_premise_ids = self._recursively_check_premises(premises[0])
            if not left_passed:
                return False, None

            right_passed, right_premise_ids = self._recursively_check_premises(premises[2])
            if not right_passed:
                return False, None

            return True, left_premise_ids | right_premise_ids

        # disjunction: (..., '|', ...)
        elif premises[1] == '|':
            left_passed, left_premise_ids = self._recursively_check_premises(premises[0])
            if left_passed:
                return True, left_premise_ids

            right_passed, right_premise_ids = self._recursively_check_premises(premises[2])
            if right_passed:
                return True, right_premise_ids

            return False, None

        # atomic node: (predicate, instance)
        else:
            predicate, instance = premises
            if predicate == 'Eq':

                status, premise_ids = self._pass_algebraic_premise(instance)
                if status == 1:
                    return True, premise_ids
                return False, None
            else:
                if premises in self.fact_id:
                    return True, {self.fact_id[premises]}
                return False, None

    def _recursively_check_algebraic_forms(self, algebraic_forms_gdl, replace):
        # conjunction : (..., '&', ...)
        if algebraic_forms_gdl[1] == '&':
            left_passed = self._recursively_check_algebraic_forms(algebraic_forms_gdl[0], replace)
            if not left_passed:
                return False

            right_passed = self._recursively_check_algebraic_forms(algebraic_forms_gdl[2], replace)
            if not right_passed:
                return False

            return True

        # disjunction: (..., '|', ...)
        elif algebraic_forms_gdl[1] == '|':
            left_passed = self._recursively_check_algebraic_forms(algebraic_forms_gdl[0], replace)
            if left_passed:
                return True

            right_passed = self._recursively_check_algebraic_forms(algebraic_forms_gdl[2], replace)
            if right_passed:
                return True

            return False

        # atomic node: (algebraic_relation, expr, dependent_entities)
        else:
            algebraic_relation, expr, _ = algebraic_forms_gdl
            return _satisfy_algebraic[algebraic_relation](_replace_expr(expr, replace))

    def _pass_algebraic_premise(self, expr):
        """return status, premise_ids
        status=1 solved
        status=-1 unsolved
        status=0 no solution
        """
        if ('Eq', expr) in self.fact_id:  # expr in self.facts
            return 1, {self.fact_id[('Eq', expr)]}

        premise_ids = set()
        for sym in list(expr.free_symbols):
            if sym in self.sym_to_value:
                premise_ids.add(self.fact_id[('Eq', sym - self.sym_to_value[sym])])
                expr = expr.subs(sym, self.sym_to_value[sym])

        if len(expr.free_symbols) == 0:
            if _satisfy_algebraic['Eq'](expr):
                return 1, premise_ids
            return -1, None

        if expr in self.solved_target_cache:
            return 1, self.solved_target_cache[expr] | premise_ids

        target_sym = symbols('t')
        equations = [target_sym - expr]
        syms = set(expr.free_symbols)
        for group_id in self.equations:
            if len(self.equations[group_id][2] & expr.free_symbols) > 0:
                equations.extend(self.equations[group_id][0])
                for eq_premise_ids in self.equations[group_id][1]:
                    premise_ids.update(eq_premise_ids)
                syms.update(self.equations[group_id][2])
        syms = [target_sym] + list(syms)

        equations_tuple = tuple(sorted(equations, key=str))
        if equations_tuple in self.attempted_equations_cache:
            return self.attempted_equations_cache[equations_tuple], None
        self.attempted_equations_cache[equations_tuple] = 0

        try:
            equation_solutions = func_timeout(
                timeout=self.timeout,
                func=nonlinsolve,
                args=(equations, syms)
            )
        except FunctionTimedOut:
            return 0, None

        if equation_solutions is EmptySet:
            e_smg = f'Equations no solution: {equations}'
            raise Exception(e_smg)

        if type(equation_solutions) is not FiniteSet:
            return 0, None

        for solved_value in list(equation_solutions):
            if solved_value[0] != 0:  # in every solution, the solved value of target_sym must be 0
                if len(solved_value[0].free_symbols) == 0:
                    self.attempted_equations_cache[equations_tuple] = -1
                    return -1, None
                return 0, None

        self.solved_target_cache[expr] = premise_ids

        return 1, premise_ids

    def _add_fact(self, predicate, instance, premise_ids, entity_ids, operation_id):
        if predicate == 'Eq':
            fact_id, sub_goal_ids = self._add_equation(predicate, instance, premise_ids, entity_ids, operation_id)
        elif predicate in {'Point', 'Line', 'Circle'}:
            fact_id, sub_goal_ids = self._add_entity(predicate, instance, premise_ids, entity_ids, operation_id)
        elif predicate in {'SamePoint', 'SameLine', 'SameCircle'}:
            fact_id, sub_goal_ids = self._add_same(predicate, instance, premise_ids, entity_ids, operation_id)
        else:
            fact_id, sub_goal_ids = self._add_relation(predicate, instance, premise_ids, entity_ids, operation_id)

        return fact_id, sub_goal_ids

    def _add_entity(self, predicate, instance, premise_ids, entity_ids, operation_id):
        if (predicate, instance) in self.fact_id or instance[0] not in self.letters:
            return None, set()

        fact_id = len(self.facts)
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.groups[operation_id].append(fact_id)

        self.letters.remove(instance[0])

        return fact_id, set()

    def _add_relation(self, predicate, instance, premise_ids, entity_ids, operation_id):
        if (predicate, instance) in self.fact_id:
            return None, set()

        fact_id = len(self.facts)
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.groups[operation_id].append(fact_id)

        if (predicate, instance) in self.sub_goal_ids:
            return fact_id, self.sub_goal_ids[(predicate, instance)]
        return fact_id, set()

    def _add_same(self, predicate, instance, premise_ids, entity_ids, operation_id):
        """Add SamePoint, SameLine, and SameCircle, and remove redundant facts. For two equivalent entities A and B:
        1.Sort entities and take entity comes later in the sorted order (entity B) as removed entity.
        2.Replace B with A in all relations and add new relation to self.facts.
        3.For any symbols in self.sym_to_value, if contain B, add A.sym - self.sym_to_value[B.sym] to self.facts.
        4.For any symbols in self.equations, if contain A or B, add A.sym - B.sym to self.facts.
        """
        if instance[0] == instance[1]:
            return None, set()

        instance = sorted([instance, (instance[1], instance[0])])[0]
        A, B = instance

        if (predicate, instance) in self.fact_id:
            return None, set()

        fact_id = len(self.facts)
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.groups[operation_id].append(fact_id)
        sub_goal_ids_total = set()

        # Replace B with A in all relations and add new relation to self.facts
        for b_fact_id in range(len(self.facts)):
            predicate, instance, _, _, _ = self.facts[b_fact_id]
            if predicate in {'Equation', 'Point', 'Line', 'Circle', 'SamePoint', 'SameLine', 'SameCircle'}:
                continue
            if B not in instance:
                continue
            instance = tuple([e if e != B else A for e in instance])
            operation_id = self._add_operation('same_entity_extend')
            entity_ids = self._get_entity_ids(predicate, instance)
            _, sub_goal_ids = self._add_fact(predicate, instance, {fact_id, b_fact_id}, entity_ids, operation_id)
            sub_goal_ids_total.update(sub_goal_ids)

        # For any symbols in self.sym_to_value, if contain B, add A.sym - self.sym_to_value[B.sym] to self.facts
        for b_sym in self.sym_to_value:
            entities, attr = str(b_sym).split('.')
            if B not in entities:
                continue
            a_sym = symbols(entities.replace(B, A) + '.' + attr)
            if a_sym in self.sym_to_value:
                continue
            instance = a_sym - self.sym_to_value[b_sym]
            b_fact_id = self.fact_id[('Eq', instance)]
            operation_id = self._add_operation('same_entity_extend')
            entity_ids = self._get_entity_ids('Eq', instance)
            _, sub_goal_ids = self._add_fact('Eq', instance, {fact_id, b_fact_id}, entity_ids, operation_id)
            sub_goal_ids_total.update(sub_goal_ids)

        # For any symbols in self.equations, if contain A or B, add A.sym - B.sym to self.facts
        added_eqs = set()
        for group_id in self.equations:
            for sym in self.equations[group_id][2]:
                entities, attr = str(sym).split('.')
                if A in entities:
                    added_eqs.add(sym - symbols(entities.replace(A, B) + '.' + attr))
                elif B in entities:
                    added_eqs.add(sym - symbols(entities.replace(B, A) + '.' + attr))
        for instance in added_eqs:
            operation_id = self._add_operation('same_entity_extend')
            entity_ids = self._get_entity_ids('Eq', instance)
            _, sub_goal_ids = self._add_fact('Eq', instance, {fact_id}, entity_ids, operation_id)
            sub_goal_ids_total.update(sub_goal_ids)

        return fact_id, sub_goal_ids_total

    def _add_equation(self, predicate, instance, premise_ids, entity_ids, operation_id):
        instance = self._adjust_expr(instance)
        if len(instance.free_symbols) == 0 or (predicate, instance) in self.fact_id:
            return None, set()

        fact_id = len(self.facts)
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.groups[operation_id].append(fact_id)

        if self.operations[operation_id] == 'solve_eq':
            return fact_id, set()

        new_simplified_eqs = [instance]
        new_premise_ids_list = [{fact_id}]
        new_syms = set()

        # replace solved sym with its value
        for sym in instance.free_symbols:
            if sym in self.sym_to_value:
                new_simplified_eqs[0] = new_simplified_eqs[0].subs(sym, self.sym_to_value[sym])
                new_premise_ids_list[0].add(self.fact_id[('Eq', sym - self.sym_to_value[sym])])
            else:
                new_syms.add(sym)

        if len(new_syms) == 0:  # no unsolved sym
            return fact_id, set()

        # merge equations group
        deleted_group_ids = set()
        for group_id in self.equations:
            simplified_eqs, premise_ids_list, syms = self.equations[group_id]
            if len(new_syms & syms) > 0:
                deleted_group_ids.add(group_id)
                new_simplified_eqs.extend(simplified_eqs)
                new_premise_ids_list.extend(premise_ids_list)
                new_syms.update(syms)

        sub_goal_ids = set()
        for sub_goal_id in self.algebraic_sub_goal:
            if len(deleted_group_ids & self.algebraic_sub_goal[sub_goal_id][0]) > 0:
                sub_goal_ids.add(sub_goal_id)

        # solve equations
        new_syms = list(new_syms)
        solved_values = {}
        try:
            solutions = func_timeout(timeout=self.timeout, func=nonlinsolve, args=(new_simplified_eqs, new_syms))
            if solutions is EmptySet:
                e_smg = f'Equations no solution: {new_simplified_eqs}'
                raise Exception(e_smg)

            if type(solutions) is FiniteSet and len(solutions) > 0:
                solutions = list(solutions)

                for j in range(len(new_syms)):
                    if len(solutions[0][j].free_symbols) != 0:  # no numeric solution
                        continue

                    same = True
                    for i in range(1, len(solutions)):
                        if solutions[i][j] != solutions[0][j]:
                            same = False
                            break
                    if not same:  # numeric solution not same in every solved result
                        continue

                    solved_values[new_syms[j]] = solved_values[0][j]  # save solved value
        except FunctionTimedOut:
            pass

        # split equations group
        if len(solved_values) == 0:  # no solved value
            self.equations[self.group_count] = (tuple(new_simplified_eqs), tuple(new_premise_ids_list), set(new_syms))
            self.group_count += 1
            return fact_id, sub_goal_ids

        operation_id = self._add_operation('solve_eq')  # add the solved values
        premise_ids = set()
        for new_premise_ids in new_premise_ids_list:
            premise_ids.update(new_premise_ids)
        for sym in solved_values:
            instance = sym - solved_values[sym]
            entity_ids = self._get_entity_ids('Eq', instance)
            self.sym_to_value[sym] = solved_values[sym]
            self._add_fact('Eq', instance, premise_ids, entity_ids, operation_id)

        for i in range(len(new_simplified_eqs)):  # replace sym with it's solved value
            for sym in new_simplified_eqs[i].free_symbols:
                if sym in solved_values:
                    new_simplified_eqs[i] = new_simplified_eqs[i].subs(sym, solved_values[sym])
                    new_premise_ids_list[i].add(self.fact_id[('Eq', sym - solved_values[sym])])

        while len(new_simplified_eqs) > 0:
            if len(new_simplified_eqs[0].free_symbols) == 0:  # no unsolved sym, skip
                new_simplified_eqs.pop(0)
                new_premise_ids_list.pop(0)
                continue

            simplified_eqs = [new_simplified_eqs.pop(0)]
            premise_ids_list = [new_premise_ids_list.pop(0)]
            syms = set(simplified_eqs[0].free_symbols)
            update = True
            while update:
                update = False
                for i in range(len(new_simplified_eqs))[::-1]:
                    if len(syms & new_simplified_eqs[i].free_symbols) > 0:
                        simplified_eqs.append(new_simplified_eqs.pop(i))
                        premise_ids_list.append(new_premise_ids_list.pop(i))
                        syms.update(simplified_eqs[-1].free_symbols)
                        update = True
            self.equations[self.group_count] = (tuple(simplified_eqs), tuple(premise_ids_list), set(syms))
            self.group_count += 1

        return fact_id, sub_goal_ids

    def _add_operation(self, operation):
        operation_id = len(self.operations)
        self.operations.append(operation)
        self.groups[operation_id] = set()
        return operation_id

    def _adjust_expr(self, expr):
        for sym in list(expr.free_symbols):
            if sym not in self.sym_to_sym:  # new symbols
                entities, attr = str(sym).split('.')
                replace = dict(zip(self.parsed_gdl['Attribution'][attr]['paras'], entities))
                self.sym_to_syms[sym] = set()
                for sym_multiple_form in self.parsed_gdl['Attribution'][attr]['multiple_forms']:
                    sym_multiple_form = symbols(''.join([replace[e] for e in sym_multiple_form]) + '.' + attr)
                    self.sym_to_syms[sym].add(sym_multiple_form)
                    self.sym_to_sym[sym_multiple_form] = sym

            if sym != self.sym_to_sym[sym]:  # replace sym_multiple_form with sym_unified_form
                expr = expr.subs(sym, self.sym_to_sym[sym])

        if str(expr)[0] == '-':  # adjust to a form without a leading negative sign
            expr = -expr

        return expr

    def _get_entity_ids(self, predicate, instance):
        entity_ids = set()
        for dependent_entity in _parse_dependent_entities(predicate, instance, self.parsed_gdl):
            entity_ids.add(self.fact_id[dependent_entity])
        return entity_ids

    def set_goal(self, goal):
        if len(self.goals) > 0:
            raise Exception("The function 'set_goal' is only used to set the initial goal.")

        if goal.startswith('Eq('):
            predicate, instance = _parse_algebraic_fact(goal)
            instance = self._adjust_expr(instance)
            for dependent_entity in _parse_dependent_entities(predicate, instance, self.parsed_gdl):
                if dependent_entity not in self.fact_id:
                    raise Exception(f"Entity '{dependent_entity}' does not exist.")
            algebraic_forms = _parse_algebraic_forms(predicate, instance, self.parsed_gdl)[0][1]
            if not _satisfy_algebraic['Eq'](algebraic_forms, self.entity_sym_to_value):
                raise Exception(f"Algebraic forms '{algebraic_forms}' not pass check.")
        else:
            predicate, instance = _parse_geometric_fact(goal)
            if predicate not in self.parsed_gdl['Relations']:
                raise Exception(f"Unknown goal predicate '{predicate}'.")
            if len(instance) != len(self.parsed_gdl['Relations'][predicate]['paras']):
                raise Exception(f"Instance {instance} length is incorrect.")
            for dependent_entity in _parse_dependent_entities(predicate, instance, self.parsed_gdl):
                if dependent_entity not in self.fact_id:
                    raise Exception(f"Entity '{dependent_entity}' does not exist.")

            replace = dict(zip(self.parsed_gdl['Relations'][predicate]['paras'], instance))

            algebraic_forms = _parse_gpl_to_tree(self.parsed_gdl['Relations'][predicate]['algebraic_forms'])
            algebraic_forms = _negation_inward(algebraic_forms)
            algebraic_forms = _format_algebraic_forms(algebraic_forms, self.parsed_gdl, add_dependent=True)

            if not self._recursively_check_algebraic_forms(algebraic_forms, replace):
                raise Exception(f"Instance {instance} length is incorrect.")

        operation_id = self._add_operation("set_initial_goal")
        goal_id, sub_goal_ids = self._add_goal(-1, operation_id, (predicate, instance))
        if goal_id is not None:
            self._check_sub_goals(sub_goal_ids)
        return goal_id

    def decompose(self, theorem):
        """decompose according to theorem."""
        theorem_name, theorem_para = _parse_theorem(theorem, self.parsed_gdl)

        generated_goals = []  # (premises, conclusion)
        if theorem_para is not None:  # parameterized form
            if theorem_name in self.theorem_instances:
                if theorem_para not in self.theorem_instances[theorem_name]:
                    return False
                generated_goals.append(self.theorem_instances[theorem_name][theorem_para])
            else:
                generated_goal = self._generate_premises_and_conclusion(theorem_name, theorem_para)
                if generated_goal is None:
                    return False
                generated_goals.append(generated_goal)

        else:  # parameter-free form
            self._generate_theorem_instance(theorem_name)
            generated_goals.extend(self.theorem_instances[theorem_name].values())

        update = False
        all_sub_goal_ids = set()
        for premises, conclusion in generated_goals:
            if conclusion[0] == 'Eq':  # algebraic goals
                for sub_goal_id in self.algebraic_sub_goal:
                    if self.status_of_sub_goal[sub_goal_id] != 0:
                        continue
                    if len(self.algebraic_sub_goal[sub_goal_id][1] & conclusion[1].free_symbols) == 0:
                        continue
                    operation_id = self._add_operation(theorem)
                    goal_id, sub_goal_ids = self._add_goal(sub_goal_id, operation_id, premises)
                    if goal_id is not None:
                        all_sub_goal_ids.update(sub_goal_ids)
                        update = True
            else:  # geometric goals
                for sub_goal_id in self.sub_goal_ids[conclusion]:  # expand goal
                    if self.status_of_sub_goal[sub_goal_id] != 0:
                        continue
                    operation_id = self._add_operation(theorem)
                    goal_id, sub_goal_ids = self._add_goal(sub_goal_id, operation_id, premises)
                    if goal_id is not None:
                        all_sub_goal_ids.update(sub_goal_ids)
                        update = True

        # update influenced sub goal nodes
        self._check_sub_goals(all_sub_goal_ids)
        return update

    def _add_goal(self, root_sub_goal_id, operation_id, sub_goal_tree):
        if root_sub_goal_id != -1:
            # the root goal has already been solved and does not need to be further decomposed
            if self.status_of_goal[self.sub_goals[root_sub_goal_id][2]] != 0:
                return None, set()
            # check if sibling goals contain the same operation
            for goal_id in self.leaf_goal_ids[root_sub_goal_id]:
                if self.operations[operation_id] == self.operations[self.goals[goal_id][1]]:
                    return None, set()
            # check if root goals contain the same operation
            goal_id = self.sub_goals[root_sub_goal_id][2]
            while goal_id != -1:
                if self.operations[operation_id] == self.operations[self.goals[goal_id][1]]:
                    return None, set()
                goal_id = self.sub_goals[self.goals[goal_id][0]][2]

        old_sub_goal_id = len(self.sub_goals)
        goal_id = len(self.goals)
        leaf_sub_goal_id = self._recursively_add_sub_goals(sub_goal_tree, goal_id, -1)
        self.goals.append((root_sub_goal_id, operation_id, leaf_sub_goal_id))
        self.status_of_goal[goal_id] = 0

        sub_goal_ids = list(range(old_sub_goal_id, len(self.sub_goals)))
        return goal_id, sub_goal_ids

    def _recursively_add_sub_goals(self, sub_goal_tree, goal_id, root_sub_goal_id):
        sub_goal_id = len(self.sub_goals)

        if sub_goal_tree[1] in {'&', '|'}:  # conjunction or disjunction: (..., '&' or '|', ...)
            predicate = 'Operator'
            instance = sub_goal_tree[1]
            self.sub_goals.append((predicate, instance, goal_id, root_sub_goal_id))
            left_sub_goal_id = self._recursively_add_sub_goals(sub_goal_tree[0], goal_id, sub_goal_id)
            right_sub_goal_id = self._recursively_add_sub_goals(sub_goal_tree[2], goal_id, sub_goal_id)
            leaf_sub_goal_ids = (left_sub_goal_id, right_sub_goal_id)
        else:  # atomic node: (predicate, instance)
            predicate, instance = sub_goal_tree
            self.sub_goals.append((predicate, instance, goal_id, root_sub_goal_id))
            leaf_sub_goal_ids = None

        self.status_of_sub_goal[sub_goal_id] = 0
        self.leaf_sub_goal_ids[sub_goal_id] = leaf_sub_goal_ids
        self.leaf_goal_ids[sub_goal_id] = set()
        if (predicate, instance) not in self.sub_goal_ids:
            self.sub_goal_ids[(predicate, instance)] = {sub_goal_id}
        else:
            self.sub_goal_ids[(predicate, instance)].add(sub_goal_id)
        self.predicate_to_sub_goal_ids[predicate].add(sub_goal_id)

        return sub_goal_id

    def _check_sub_goals(self, sub_goal_ids):
        goal_ids = set()
        for sub_goal_id in sub_goal_ids:
            # skip nodes that do not require checking
            if self.status_of_goal[self.sub_goals[sub_goal_id][2]] != 0 or self.status_of_sub_goal[sub_goal_id] != 0:
                continue
            # skip operator nodes
            if self.sub_goals[sub_goal_id][0] == 'Operator':
                continue

            predicate, instance, _, _ = self.sub_goals[sub_goal_id]
            if predicate == 'Eq':
                status, premise_ids = self._pass_algebraic_premise(instance)
                if status == 1:  # has solution, update status
                    self.status_of_sub_goal[sub_goal_id] = 1
                    self.premise_ids_of_sub_goal[sub_goal_id] = premise_ids
                    goal_ids.add(self.sub_goals[sub_goal_id][2])
                elif status == -1:  # has solution, update status
                    self.status_of_sub_goal[sub_goal_id] = -1
                    goal_ids.add(self.sub_goals[sub_goal_id][2])
                else:  # no solution, update dependent equations group
                    syms = set()
                    for sym in instance.free_symbols:
                        if sym in self.sym_to_value:
                            continue
                        syms.add(sym)
                    group_ids = set()
                    for group_id in self.equations:
                        if len(self.equations[group_id][2] & syms) > 0:
                            group_ids.add(group_id)
                            syms.update(self.equations[group_id][2])
                    self.algebraic_sub_goal[sub_goal_id] = (group_ids, syms)
            else:
                if (predicate, instance) in self.fact_id[(predicate, instance)]:
                    self.status_of_sub_goal[sub_goal_id] = 1
                    self.premise_ids_of_sub_goal[sub_goal_id] = {self.fact_id[(predicate, instance)]}
                    goal_ids.add(self.sub_goals[sub_goal_id][2])
                    continue

                if predicate in {'Point', 'Line', 'Circle'}:
                    self.status_of_sub_goal[sub_goal_id] = -1
                    goal_ids.add(self.sub_goals[sub_goal_id][2])

        self._check_goals(goal_ids)

    def _check_goals(self, goal_ids):
        added_facts = []  # (predicate, instance, premise_ids, entity_ids, operation_id)

        for goal_id in goal_ids:
            # skip nodes that do not require checking
            if self.status_of_goal[goal_id] != 0:
                continue

            sub_goal_id, goal_operation_id, root_sub_goal_id = self.goals[goal_id]
            status, premise_ids = self._recursively_check_one_goal(sub_goal_id)
            if status == 1:
                self._recursively_set_status_of_goal(goal_id, 1)
                if root_sub_goal_id != -1:  # apply theorem
                    theorem_name, theorem_instance = _parse_geometric_fact(self.operations[goal_operation_id])
                    replace = dict(zip(self.parsed_gdl['Theorems'][theorem_name]['paras'], theorem_instance))
                    predicate, instance = self.parsed_gdl['Theorems'][theorem_name]['conclusion']
                    if predicate == 'Eq':
                        instance = _replace_expr(instance, replace)
                    else:
                        instance = _replace_instance(instance, replace)
                    entity_ids = self._get_entity_ids(predicate, instance)
                    operation_id = self._add_operation(self.operations[goal_operation_id])
                    added_facts.append((predicate, instance, premise_ids, entity_ids, operation_id))
            elif status == -1:
                self._recursively_set_status_of_goal(goal_id, -1)

        all_sub_goal_ids = set()
        for predicate, instance, premise_ids, entity_ids, operation_id in added_facts:
            fact_id, sub_goal_ids = self._add_fact(predicate, instance, premise_ids, entity_ids, operation_id)
            if fact_id is not None:
                all_sub_goal_ids.update(sub_goal_ids)

        self._check_sub_goals(all_sub_goal_ids)

    def _recursively_check_one_goal(self, sub_goal_id):
        if self.status_of_sub_goal[sub_goal_id] == -1:
            return -1, None
        elif self.status_of_sub_goal[sub_goal_id] == 1:
            return 1, self.premise_ids_of_sub_goal[sub_goal_id]

        predicate, instance, _, _ = self.sub_goals[sub_goal_id]

        if predicate != 'Operator':
            return 0, None

        elif instance == '&':
            left_sub_goal_id, right_sub_goal_id = self.leaf_sub_goal_ids[sub_goal_id]

            left_status, left_premise_ids = self._recursively_check_one_goal(left_sub_goal_id)
            if left_status == -1:
                self.status_of_sub_goal[sub_goal_id] = -1
                return -1, None

            right_status, right_premise_ids = self._recursively_check_one_goal(right_sub_goal_id)
            if right_status == -1:
                self.status_of_sub_goal[sub_goal_id] = -1
                return -1, None

            if left_status == 1 and right_status == 1:
                self.status_of_sub_goal[sub_goal_id] = 1
                self.premise_ids_of_sub_goal[sub_goal_id] = left_premise_ids | right_premise_ids
                return 1, self.premise_ids_of_sub_goal[sub_goal_id]

            return 0, None

        else:  # instance == '|'
            left_sub_goal_id, right_sub_goal_id = self.leaf_sub_goal_ids[sub_goal_id]

            left_status, left_premise_ids = self._recursively_check_one_goal(left_sub_goal_id)
            if left_status == 1:
                self.status_of_sub_goal[sub_goal_id] = 1
                self.premise_ids_of_sub_goal[sub_goal_id] = left_premise_ids
                return 1, self.premise_ids_of_sub_goal[sub_goal_id]

            right_status, right_premise_ids = self._recursively_check_one_goal(right_sub_goal_id)
            if right_status == 1:
                self.status_of_sub_goal[sub_goal_id] = 1
                self.premise_ids_of_sub_goal[sub_goal_id] = right_premise_ids
                return 1, self.premise_ids_of_sub_goal[sub_goal_id]

            if left_status == -1 and right_status == -1:
                self.status_of_sub_goal[sub_goal_id] = -1
                return -1, None

            return 0, None

    def _recursively_set_status_of_goal(self, goal_id, status):
        """
        set leaf goals status to -1
        set sibling goals status to -1
        """
        if self.status_of_goal[goal_id] != 0:
            return
        self.status_of_goal[goal_id] = status

        goal_ids = set()

        sub_goal_ids = [self.goals[goal_id][0]]  # leaf goals
        while len(sub_goal_ids) > 0:
            sub_goal_id = sub_goal_ids.pop()
            goal_ids.update(self.leaf_goal_ids[sub_goal_id])
            if self.leaf_sub_goal_ids[sub_goal_id] is not None:
                sub_goal_ids.extend(self.leaf_sub_goal_ids[sub_goal_id])

        if self.goals[goal_id][2] != -1:  # sibling goals
            goal_ids.update(self.leaf_goal_ids[self.goals[goal_id][2]])

        for goal_id in goal_ids:
            self._recursively_set_status_of_goal(goal_id, -1)
