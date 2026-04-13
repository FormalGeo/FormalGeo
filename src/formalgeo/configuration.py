from .tools import entity_letters
from .tools import _parse_expr_to_algebraic_forms, _get_geometric_constraints
from .tools import satisfy_algebraic_map, precision
from .tools import _parse_construction, _parse_theorem, _parse_goal
from .tools import _serialize_fact, _serialize_operation, _serialize_goal
from .tools import _is_negation, _is_conjunction, _is_disjunction
from .tools import _replace_instance, _replace_expr
from .tools import _anti_parse_operation, _anti_parse_fact, _format_ids
from sympy import symbols, nonlinsolve, tan, pi, FiniteSet, EmptySet
from func_timeout import func_timeout, FunctionTimedOut
from graphviz import Graph
import matplotlib.pyplot as plt
import random
import math

plt.rcParams['font.family'] = 'STIXGeneral'  # temporary fix for bug 260413-02
plt.rcParams['mathtext.fontset'] = 'stix'


class GeometricConfiguration:
    def __init__(self, parsed_gdl, sample_max_epoch=500, sample_expansion_rate=1.2, timeout=5):
        """The 'GeometricConfiguration' class stores the construction and reasoning process of a configuration.

        Args:
            parsed_gdl (dict): Parsed Geometry Definition Language (GDL). The function 'formalgeo.tools.parse_gdl'
            demonstrates the detailed parsing process of GDL. You can also use the function 'formalgeo.tools.show_json'
            to view it specific format.

            sample_max_epoch (int): The maximum number of sampling iterations for a single 'constraint_value' during
            construction. This parameter is used only in the function 'self._random_value()'.

            sample_expansion_rate (float): Expansion rate of the sampling range; used together with 'self.sample_range'.
            This parameter is used only in the function 'self._random_value()'.

            timeout (float): Timeout for solving algebraic equations. This parameter applies to all functions involving
            equation solving, including 'self._solve_constraints()', 'self._check_algebraic_premise()', and
            'self._add_algebraic()'.

        Methods:
            self.construct(construction, random_seed=0, added=True): Construct a geometric entity (point, line, circle).
            If successfully construct the entity, return True; otherwise, return False.

            self.apply(theorem): Apply a theorem to add new fact. If applying the theorem adds new facts, return True;
            otherwise, return False.

            self.set_goal(goal): Set the initial goal. If successfully set the initial goal, return True; otherwise,
            return False.

            self.decompose(theorem): Apply a theorem to decompose goal. If applying the theorem decomposes new goals,
            return True; otherwise, return False.

            self.show_gc(): Display the problem-solving process.

            self.get_gc(): Return the serialized problem state.

            self.draw_gc(save_path='./', filename='gc', file_format='pdf', scale=1): Draw geometric figures.

            self.draw_sg(save_path='./', filename='sg', file_format='pdf'): Draw structured graph of problem-solving
            process, including forward hypergraph and backward composite graph.
        """
        self.parsed_gdl = parsed_gdl
        self.sample_max_epoch = sample_max_epoch  # Maximum epoch of sampling attempts
        self.sample_expansion_rate = sample_expansion_rate  # Range expansion ratio during random sampling
        self.sample_range = {'x_max': 1, 'x_min': -1, 'y_max': 1, 'y_min': -1}  # Coordinate range of all points
        self.timeout = timeout  # Maximum tolerance time for solving algebraic equations
        self.letters = set(entity_letters)  # available entity letters

        """Construction.
                
        self.constructions (dict): operation_id -> (used_branch, parsed_construction). Store the construction
        process, i.e., the parsed Geometric Construction Language (GCL). This is for recording purposes only.
        Element is added during the construction but never accessed, meaning it does not affect the construction or
        reasoning processes. It is only accessed in the 'self.show_gc()' and 'self.draw_gc()' functions.
        Specifically:
            1.operation_id (int): The ID corresponding to the current GCL in 'self.operations'.
            2.used_branch (int): After parsing, a GCL may have several branches. We can select a branch for random
            sampling. 'used_branch' stores the selected branch.
            3.parsed_construction (list): Store all parsed construction branches as a list. It is obtained by the
            function 'formalgeo.tools._parse_construction()'. Specifically: [target_entities, dependent_entities,
            added_facts, equations, inequalities, solved_value].
        Examples:
        self.constructions = {
            0: (  # operation_id
                   1,  # used_branch
                   [  # parsed_construction
                       [  # one branch of parsed_construction
                           [('Point', ('M',))],                                 # target_entities
                           [('Circle', ('Ω',))],                                # dependent_entities
                           [('CenterOfCircle', ('M', 'Ω'))],                    # added_facts
                           [M.x - Ω.u, M.y - Ω.v],                              # equations
                           [],                                                  # inequalities
                           ([M.x, M.y],[-0.255516808977684, 1.19236064903496])  # solved_value
                       ]
                   ]
            )
        }
        """
        self.constructions = {}  # operation_id -> (used_branch, parsed_construction)

        """Instance Generation.

        self.relation_instances (dict): relation_predicate -> {relation_instance}. Stores all possible geometric
        relations for the current configuration. These relations are derived through algebraic computation and may
        either already exist in 'self.facts' or require further reasoning to be obtained. For basic entities (Point,
        Line, Circle), instances are generated during the construction phase and added to 'self.relation_instances'.
        During the reasoning phase, other geometric relation instances are generated as needed.
        Examples:
        self.relation_instances = {
            'Point': {('A',), ('B',), ('C',)},
            'Line': {('l',), ('m',)},
            'PointOnLine': {('A','l'), ('B','l'), ('C','m')}
        }

        self.theorem_instances (dict): theorem_name -> {theorem_instance: (premises, conclusion)}. All valid theorem
        parameters. theorem instance is obtained by executing GPL on relation instance. Successfully applied theorem
        instance will be removed from 'self.theorem_instances'.
        Examples:
        self.theorem_instances = {
            'angle_bisector_property_distance_equal': {  # theorem_name
                ('A', 'O', 'x', 'b', 'c'): (  # theorem_instance
                    (('AngleBisector', ('A', 'x', 'b', 'c')), '&', ('PointOnLine', ('O', 'x'))),  # premises
                    ('EqualDistancePointToLine', ('O', 'b', 'O', 'c'))  # conclusion
                ),
                ('B', 'O', 'y', 'c', 'a'): (  # theorem_instance
                    (('AngleBisector', ('B', 'y', 'c', 'a')), '&', ('PointOnLine', ('O', 'y'))),  # premises
                    ('EqualDistancePointToLine', ('O', 'c', 'O', 'a'))  # conclusion
                ),
                ('C', 'O', 'z', 'a', 'b'): (  # theorem_instance
                    (('AngleBisector', ('C', 'z', 'a', 'b')), '&', ('PointOnLine', ('O', 'z'))),  # premises
                    ('EqualDistancePointToLine', ('O', 'a', 'O', 'b'))  # conclusion
                )
            }
        }
        """
        self.relation_instances = {}  # relation_predicate -> {relation_instance}
        for relation in ('Point', 'Line', 'Circle'):
            self.relation_instances[relation] = set()
        self.theorem_instances = {}  # theorem_name -> {theorem_instance: (premises, conclusion)}

        """Forward Solving.
        
        self.facts (list): fact_id -> (predicate, instance, {premise_id}, {entity_id}, operation_id). Store all
        known facts of the current problem. The index of element is its fact_id. Specifically:
            1.predicate (str): The type of fact, such as 'Point', 'Parallel', 'Equation', etc.
            2.instance (tuple): The instance of fact, categorized into geometric relations and algebraic relations,
            such as ('A',), ('l', 'm'), lk.ma - 1, etc.
            3.premise_id (int): The premise of the current fact.
            4.entity_id (int): The dependent entities of the current fact.
            5.operation_id (int): The operation that yielded the current fact.
        Examples:
        self.facts = [
            ('Point', 'A', (,), (,), 0),  # free entity, no premise_id and no entity_id
            ('Line', 'l', (3, 6), (3, 6), 3),  # entity added in construction, premise_id=entity_id
            ('PointOnLine', ('A', 'l'), (3, 6), (3, 6), 3),  # relations added in construction, premise_id=entity_id
            ('Perpendicular', ('l', 'm'), (7, 8, 9), (2, 3), 6),  # inferred geometric relations
            ('Eq', lk.ma - 1, (10, 11), (1, 4), 8)  # inferred algebraic relations
        ]

        self.fact_id (dict): (predicate, instance) -> fact_id. Mapping from fact to fact_id. Each fact has a unique
        ID, corresponding to the index in the 'self.facts' list.
        Examples:
        self.fact_id = {
            ('Point', ('A',)): 0,
            ('PointOnLine', ('A', 'l')): 5,
            ('Eq', lk.ma - 1): 12
        }

        self.predicate_to_fact_ids (dict): predicate -> {fact_id}. The fact_id of facts with the same predicate.
        This is for recording purposes only. Element is added during the construction and reasoning phases but never
        accessed, meaning it does not affect the construction or reasoning processes. It is only accessed in the
        'self.show_gc()' and 'self.draw_gc()' functions.
        Examples:
        self.predicate_to_fact_ids = {
            'Point': {0, 1, 3, 4},
            'PointOnLine': {5, 7}
        }

        self.fact_groups (dict): operation_id -> {fact_id}. Record the fact_ids of all facts added by a specific
        operation. In practice, decompose operation will also add new item to 'self.fact_groups' through function
        'self._add_operation()', but this is only effective for forward process.
        Examples:
        self.fact_groups = {
            0: {0, 1, 2, 3},
            1: {4, 5},
            2: {8, 6, 7},
            10: set(),  # decompose operation
            11: set()  # decompose operation
        }

        self.operations (list): operation_id -> (operation_type, operation_predicate, operation_instance). Record
        all operations, including construction, forward, backward, and automatic ones.
        Examples:
        self.operations = [
            ('construction', 'Point(A)&Point(B)', 'FreePoint(A)&FreePoint(B)'),
            ('auto', 'same_entity_extend', None),
            ('auto', 'set_initial_goal', None),
            ('auto', 'solve_eq', None),
            ('apply', 'equal_distance_point_to_line_property_algebraic', ('O', 'b', 'O', 'a')),
            ('decompose', 'angle_bisector_determination_distance_equal', ('C', 'O', 'z', 'a', 'b'))
        ]
        """
        self.facts = []  # fact_id -> (predicate, instance, {premise_id}, {entity_id}, operation_id)
        self.fact_id = {}  # (predicate, instance) -> fact_id
        self.predicate_to_fact_ids = {}  # predicate -> {fact_id}
        for relation in self.parsed_gdl['Entities'].keys():
            self.predicate_to_fact_ids[relation] = set()
        for relation in self.parsed_gdl['Relations'].keys():
            self.predicate_to_fact_ids[relation] = set()
        for relation in satisfy_algebraic_map.keys():
            self.predicate_to_fact_ids[relation] = set()
        self.fact_groups = {}  # operation_id -> {fact_id}
        self.operations = []  # operation_id -> (operation_type, operation_predicate, operation_instance)

        """Backward Solving.
        
        self.goals (list): goal_id -> (sub_goal_id_tree, operation_id, root_sub_goal_id). The backward process
        utilizes two data structures: goal and sub_goal. Multiple sub_goals are combined via AND, OR, or NOT
        operations to form a tree structure. Each such tree constitutes a goal. 'sub_goal_id_tree' represents the
        tree structure, 'operation_id' is the operation that generated the current goal, and 'root_sub_goal_id' is
        the root node of the current goal. The current goal is derived from the root sub_goal via the operation.
        Example:
        self.goals = [
            (0, 10, None),
            ((1, '&', (2, '&', (3, '&', 4))), 11, 0),
            ((5, '&', (6, '&', (7, '&', (8, '&', 9)))), 12, 4),
            (10, 13, 9)
        ]

        self.status_of_goal (dict): goal_id -> status. The status of the goal. 0 indicates waiting to check; 1
        indicates solved; -1 indicates skip or unsolved.
        Example:
        self.status_of_goal = {
            0: 1, 1: 1, 2: 1, 3: -1, 4: 0
        }

        self.premise_ids_of_goal (dict): goal_id -> {premise_id}. If a goal's status is solved, then
        'self.premise_ids_of_goal' will record the premises required to derive the current goal. Specifically, this
        is the union of the self.premise_ids_of_sub_goal of all its sub_goals.
        Example:
        self.premise_ids_of_goal = {
            0: {38},
            1: {8, 25, 11, 37},
            2: {35, 36, 21, 6, 9},
            3: {37},
            4: set()
        }

        self.sub_goals (list): sub_goal_id -> (predicate, instance, goal_id). sub_goal and fact are essentially the
        same, both consisting of a 'predicate' and 'instance'. 'goal_id' records which goal the current sub_goal
        originates from.
        Example:
        self.sub_goals = [
            ('AngleBisector', ('C', 'z', 'a', 'b'), 0),
            ('PointOnLine', ('C', 'z'), 1),
            ('PointOnLine', ('C', 'a'), 1),
            ('EqualDistancePointToLine', ('O', 'a', 'O', 'b'), 1)
        ]

        self.status_of_sub_goal (dict): sub_goal_id -> status. The status of the sub_goal. 0 indicates waiting to
        check; 1 indicates solved; -1 indicates skip or unsolved.
        Example:
        self.status_of_sub_goal = {
            0: 1, 1: 1, 2: 1, 3: -1, 4: 0
        }

        self.premise_ids_of_sub_goal (dict): sub_goal_id -> {premise_id}. If a sub_goal's status is solved, then
        'self.premise_ids_of_sub_goal' will record the premises required to derive the sub_goal. Specifically, the
        'premise_id' is the fact_id of the fact corresponding to the current sub_goal.
        Example:
        self.premise_ids_of_sub_goal = {
            0: {38}, 1: {25}, 2: {8}, 3: {11}, 4: {37}, 5: {21}, 6: {6}, 7: {21}, 8: {9}, 9: {35, 36}
        }

        self.leaf_goal_ids (dict): sub_goal_id -> {leaf_goal_id}. Record all goals obtained from the decomposition
        of the current sub_goal.
        Example:
        self.leaf_goal_ids = {
            0: {1}, 1: set(), 2: set(), 3: set(), 4: {2}, 5: set(), 6: set(), 7: set(), 8: set(),
            9: {3, 4, 5, 6, 7, 8}, 10: set(), 11: set(), 12: set(), 13: set(), 14: set(), 15: set()
        }

        self.sub_goal_ids (dict): (predicate, instance) -> {sub_goal_id}. The set of sub_goal_ids for all identical
        sub_goals.
        Example:
        self.sub_goal_ids = {
            ('AngleBisector', ('C', 'z', 'a', 'b')): {0},
            ('PointOnLine', ('C', 'z')): {1},
             ('EqualDistancePointToLine', ('O', 'a', 'O', 'b')): {10, 4},
             ('Point', ('O',)): {5, 7}
        }

        self.predicate_to_sub_goal_ids (dict): predicate -> {sub_goal_id}. Record the IDs of all sub_goals of the
        same type. In backward, this data structure is only appended to and never accessed. The original intent was
        the same as in the forward, serving as a display for 'self.show_gc()', but since backward becomes a
        composite graph, recording this data is no longer necessary. This is a legacy issue and can be removed.
        Example:
        self.predicate_to_sub_goal_ids = {
            'Point': {5, 7},
            'Line': {8, 6},
            'Circle': set(),
            'PointOnLine': {1, 2, 3}
        }
        """
        self.goals = []  # goal_id -> (sub_goal_id_tree, operation_id, root_sub_goal_id)
        self.status_of_goal = {}  # goal_id -> int (0: not check, 1: solved, -1: skip or unsolved)
        self.premise_ids_of_goal = {}  # goal_id -> {premise_id}
        self.sub_goals = []  # sub_goal_id -> (predicate, instance, goal_id)
        self.status_of_sub_goal = {}  # sub_goal_id -> int (0: not check, 1: solved, -1: skip or unsolved)
        self.premise_ids_of_sub_goal = {}  # sub_goal_id -> {premise_id}
        self.leaf_goal_ids = {}  # sub_goal_id -> {leaf_goal_id}
        self.sub_goal_ids = {}  # (predicate, instance) -> {sub_goal_id}
        self.predicate_to_sub_goal_ids = {}  # predicate -> {sub_goal_id}
        for relation in self.parsed_gdl['Entities'].keys():
            self.predicate_to_sub_goal_ids[relation] = set()
        for relation in self.parsed_gdl['Relations'].keys():
            self.predicate_to_sub_goal_ids[relation] = set()
        for relation in satisfy_algebraic_map.keys():
            self.predicate_to_sub_goal_ids[relation] = set()

        """Algebraic System.
        
        self.entity_sym_to_value (dict): sym -> value. Mapping from the symbolic representation of entity attributes
        to their values. This includes the coordinates of points (A.x, A.y), the slope and intercept of lines (l.k,
        l.b), and the center coordinates, and radius of circles (O.u, O.v, O.r). After the diagram is constructed,
        'self.entity_sym_to_value' will not change.
        Example:
        self.predicate_to_sub_goal_ids = {
            A.x: 0.826612443660115, A.y: 0.619090567056726,  # Point
            a.k: 0.122226527166831, a.b: -0.555299975696735,  # Line
            Ω.u: 0.162409881908997, Ω.v: 0.152386862349756, Ω.r: 0.811774224168249  # Circle
        }

        self.sym_to_value (dict): sym -> value. Mapping from the symbolic representation of relation attributes to
        their values. Only record solved relation symbols.
        Example:
        self.sym_to_value = {
            AB.dpp: 1,
            lk.ma: 60
        }

        self.sym_to_sym (dict): sym -> sym. Mapping from symbols to their unique representation. Currently, only
        '.dpp' has multiple mappings.
        Example:
        self.sym_to_sym = {
            AB.dpp: AB.dpp,
            BA.dpp: AB.dpp,
            Al.dpl: Al.dpl
        }

        self.sym_to_syms (dict): sym -> {sym}. Mapping from symbols to their multiple representation. Currently,
        only '.dpp' has multiple mappings. 'self.sym_to_syms' is only recorded but never accessed. The only place it
        is accessed is the 'self.show_gc()' function.
        Example:
        self.sym_to_syms = {
            AB.dpp: {AB.dpp, BA.dpp},
            BA.dpp: {AB.dpp, BA.dpp},
            Al.dpl: {Al.dpl}
        }

        self.equations (dict): group_id -> ((simplified_eq), ({premise_id}), {sym}). Store the simplified equations.
        Equations sharing common symbols after simplification will be grouped together and assigned a group_id.
        'premise_id' corresponds one-to-one with 'simplified_eq', indicating the basis for the simplification. 'sym'
        is the common symbols of current group. Each time a new equation is added, it may trigger the merging or
        splitting of groups; see the 'self._add_algebraic()' function.
        Example:
        self.equations = {
            2: (  # group_id
                (Oa.dpl - Ob.dpl, Oa.dpl - Oc.dpl, Ob.dpl - Oc.dpl),  # simplified_eq
                ({39}, {36}, {35}),                                   # premise_id
                {Oc.dpl, Oa.dpl, Ob.dpl}                              # sym
            )
        }

        self.group_count (int): ID of equation group. Generate unique group_id.
        Example:
        self.group_count = 3

        self.simplified_eq_sub_goal (dict): sub_goal_id -> (simplified_eq, {premise_id}, {dependent_sym}, {group_id}).
        Store the simplified algebraic goals. There is a bug: when a goal is added before the group is created, the
        group_id is not recorded. This causes group updates to not affect the goal.
        Example:
        self.simplified_eq_sub_goal = {
            9: (
                Oa.dpl - Ob.dpl,   # simplified_eq
                set(),             # premise_id
                {Ob.dpl, Oa.dpl},  # dependent_sym
                set()              # group_id
            )
        }

        self.solved_target_cache (dict): target_expr -> {premise_id}. Cache the premises of solved target_expr to
        accelerate the solving process. Only successfully solved target_expr are recorded.
        Example:
        self.solved_target_cache = {
            Oa.dpl - Ob.dpl: {35, 36}
        }

        self.attempted_equations_cache (dict): (target_dependent_equation) -> passed. Cache the solving state of all
        dependency equations containing the target_expr to accelerate the solving process. 0 indicates an attempt
        was made, but the status is unknown (e.g., due to a timeout); 1 indicates solved; -1 indicates unsolved.
        Each dependency equation is solved only once, even if the status is 0.
        Example:
        self.attempted_equations_cache = {
            (-Oa.dpl + Ob.dpl + t,): 0,
            (-Oa.dpl + Ob.dpl + t, Oa.dpl - Oc.dpl, Ob.dpl - Oc.dpl): 1
        }
        """
        self.entity_sym_to_value = {}  # entity_related_sym -> value
        self.sym_to_value = {}  # (solved) relation_related_sym -> value
        self.sym_to_sym = {}  # sym_multiple_form -> sym_unified_form
        self.sym_to_syms = {}  # sym_unified_form -> {sym_multiple_form}
        self.equations = {}  # group_id -> ((simplified_eq), ({premise_id}), {sym})
        self.group_count = 0  # generate group_id
        self.simplified_eq_sub_goal = {}  # sub_goal_id -> (simplified_eq, {premise_id}, {dependent_sym}, {group_id})
        self.solved_target_cache = {}  # target_expr -> {premise_id}
        self.attempted_equations_cache = {}  # (target_dependent_equation) -> passed

    def construct(self, construction, random_seed=0, added=True):
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
                in GDL or algebraic constraints. The constraints need to be connected by '&'. Each constraint must
                include the entity currently being constructed, and the remaining entities must all be known entities.
                Furthermore, the temporary forms of entities are also permitted for use here.
                examples: 'Point(A):FreePoint(A)'  # free entity
                          'Line(l):PointOnLine(A,l)&PointOnLine(B,l)'  # constraints defined in GDL
                          'Point(C):Eq(Sub(AC.dpp,CB.dpp))'  # algebraic constraints

        Returns:
            result (bool): If successfully construct the entity, return True; otherwise, return False.
        """
        # (target_entities, dependent_entities, added_facts, equations, inequalities, solved_value)
        parsed_construction = _parse_construction(construction, self.parsed_gdl)
        for branch in range(len(parsed_construction)):
            t_entities, d_entities, added_facts, equations, inequalities, _ = parsed_construction[branch]

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
            values = self._solve_constraints(t_syms, equations, inequalities, random_seed)
            if values is None:  # no solved entity, solve next branch
                continue
            if not added:
                return True

            # add entity to self.operations
            operation_id = self._add_operation(('construction', construction.split(':')[0], construction.split(':')[1]))

            # add target entity to self.facts
            for entity, instance in t_entities:
                self._add_fact(entity, instance, premise_ids, operation_id)

            # set target entity's attribution to solved value
            for i in range(len(t_syms)):
                self.entity_sym_to_value[t_syms[i]] = values[i]
                entity, attr = str(t_syms[i]).split('.')
                if attr == 'x':  # update sample range
                    if values[i] > self.sample_range['x_max']:
                        self.sample_range['x_max'] = values[i]
                    elif values[i] < self.sample_range['x_min']:
                        self.sample_range['x_min'] = values[i]
                elif attr == 'y':
                    if values[i] > self.sample_range['y_max']:
                        self.sample_range['y_max'] = values[i]
                    elif values[i] < self.sample_range['y_min']:
                        self.sample_range['y_min'] = values[i]

            # add relations to self.facts
            for predicate, instance in added_facts:
                self._add_fact(predicate, instance, premise_ids, operation_id)

            # save constructions
            parsed_construction[branch][5] = (t_syms, values)
            self.constructions[operation_id] = (branch + 1, parsed_construction)

            # a certain branch completes construction, return True
            return True

        # no branch completes construction, return False
        return False

    def _solve_constraints(self, t_syms, equations, inequalities, random_seed):
        constraint_values = []  # list of constraint values, contains symbols, such as [[y, y - 1], [x, 0.5]]

        replaced_equations = []  # expr
        for expr in equations:
            expr = expr.subs(self.entity_sym_to_value)
            if len(expr.free_symbols) == 0:
                if not satisfy_algebraic_map['Eq'](expr):
                    return None
                continue
            replaced_equations.append(expr)

        replaced_inequalities = []  # (algebraic_relation, expr)
        for algebraic_relation, expr in inequalities:
            expr = expr.subs(self.entity_sym_to_value)
            if len(expr.free_symbols) == 0:
                if not satisfy_algebraic_map[algebraic_relation](expr):
                    return None
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
                return None

            if equation_solutions is EmptySet:
                e_smg = f'Equations no solution: {equations}'
                raise Exception(e_smg)

            if type(equation_solutions) is not FiniteSet:
                return None

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
                        if not satisfy_algebraic_map[algebraic_relation](expr, sym_to_value):
                            satisfied = False
                            break
                    if satisfied:
                        return [value.evalf(n=precision, chop=False) for value in equation_solution]

        if len(constraint_values) == 0:  # no random sampling required
            return None

        for constraint_value in constraint_values:
            values = self._random_value(t_syms, constraint_value, replaced_inequalities, random_seed)
            if values is not None:
                return values

        return None

    def _random_value(self, syms, constraint_value, replaced_inequalities, random_seed):
        random_number_generator = random.Random(random_seed)
        epoch = 0
        while epoch < self.sample_max_epoch:  # start random sampling, try self.sample_max_epoch times
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
                random_k = tan(random_number_generator.uniform(-89, 89) * pi / 180)
                random_values[sym] = random_k

            for sym in free_symbols:
                if str(sym).split('.')[1] in ['x', 'u']:
                    middle_x = (self.sample_range['x_max'] + self.sample_range['x_min']) / 2
                    range_x = (self.sample_range['x_max'] - self.sample_range['x_min']) / 2 * self.sample_expansion_rate
                    random_x = random_number_generator.uniform(float(middle_x - range_x), float(middle_x + range_x))
                    random_values[sym] = random_x
                elif str(sym).split('.')[1] in ['y', 'v']:
                    middle_y = (self.sample_range['y_max'] + self.sample_range['y_min']) / 2
                    range_y = (self.sample_range['y_max'] - self.sample_range['y_min']) / 2 * self.sample_expansion_rate
                    random_y = random_number_generator.uniform(float(middle_y - range_y), float(middle_y + range_y))
                    random_values[sym] = random_y
                elif str(sym).split('.')[1] == 'r':
                    max_distance = float(((self.sample_range['y_max'] - self.sample_range['y_min']) ** 2 +
                                          (self.sample_range['x_max'] - self.sample_range[
                                              'x_min']) ** 2) ** 0.5) / 2 * self.sample_expansion_rate
                    random_r = random_number_generator.uniform(0, max_distance)
                    random_values[sym] = random_r
                elif str(sym).split('.')[1] == 'b':
                    middle_x = (self.sample_range['x_max'] + self.sample_range['x_min']) / 2
                    range_x = (self.sample_range['x_max'] - self.sample_range['x_min']) / 2 * self.sample_expansion_rate
                    middle_y = (self.sample_range['y_max'] + self.sample_range['y_min']) / 2
                    range_y = (self.sample_range['y_max'] - self.sample_range['y_min']) / 2 * self.sample_expansion_rate

                    k_value = random_values[symbols(str(sym).split('.')[0] + '.k')]
                    b_range = [float(middle_y + range_y - k_value * (middle_x - range_x)),
                               float(middle_y - range_y - k_value * (middle_x - range_x)),
                               float(middle_y + range_y - k_value * (middle_x + range_x)),
                               float(middle_y - range_y - k_value * (middle_x + range_x))]
                    random_b = random_number_generator.uniform(min(b_range), max(b_range))
                    random_values[sym] = random_b

            values = [item.subs(random_values).evalf(n=15, chop=False) for item in constraint_value]

            sym_to_value = dict(zip(syms, values))
            satisfied = True
            for algebraic_relation, expr in replaced_inequalities:
                if not satisfy_algebraic_map[algebraic_relation](expr, sym_to_value):
                    satisfied = False
                    break
            if satisfied:
                return values

        return None

    """↑-----------Construction-----------↑"""

    """↓--------Instance Generation-------↓"""

    def _get_theorem_instances(self, theorem_name):
        if theorem_name not in self.theorem_instances:
            theorem_gdl = self.parsed_gdl['Theorems'][theorem_name]

            if 'determination' in theorem_name:  # generate theorem instances
                generated_paras, generated_instances = self._generate_instances(
                    (theorem_gdl['conclusion'], '&', theorem_gdl['premises'])
                )
            else:  # 'property'
                generated_paras, generated_instances = self._generate_instances(
                    (theorem_gdl['premises'], '&', theorem_gdl['conclusion'])
                )

            if generated_paras != theorem_gdl['paras']:  # ensure consistent paras order
                adjust_ids = tuple([generated_paras.index(p) for p in theorem_gdl['paras']])
                adjusted_generated_instances = set()
                for generated_instance in generated_instances:
                    adjusted_generated_instances.add(tuple([generated_instance[i] for i in adjust_ids]))
                generated_instances = adjusted_generated_instances

            self.theorem_instances[theorem_name] = {}
            for generated_instance in sorted(list(generated_instances), key=str):  # generate premises and conclusion
                replace = dict(zip(theorem_gdl['paras'], generated_instance))
                premises = self._generate_premises(theorem_gdl['premises'], replace)
                conclusion = self._generate_conclusion(theorem_gdl['conclusion'], replace)
                self.theorem_instances[theorem_name][generated_instance] = (premises, conclusion)

        return list(self.theorem_instances[theorem_name].keys())

    def _generate_instances(self, gpl_tree, paras_and_instances=None):
        if _is_negation(gpl_tree):  # negative form
            paras, instances = paras_and_instances
            negation_paras, negation_instances = self._generate_instances(gpl_tree[1])
            for instance in instances.copy():
                if tuple([instance[paras.index(p)] for p in negation_paras]) in negation_instances:
                    instances.remove(instance)
            return paras, instances
        elif _is_conjunction(gpl_tree):  # conjunction
            left_paras_and_instances = self._generate_instances(gpl_tree[0], paras_and_instances)
            right_paras_and_instances = self._generate_instances(gpl_tree[2], left_paras_and_instances)
            return right_paras_and_instances
        elif _is_disjunction(gpl_tree):  # disjunction
            left_paras, left_instances = self._generate_instances(gpl_tree[0], paras_and_instances)
            right_paras, right_instances = self._generate_instances(gpl_tree[2], paras_and_instances)
            if left_paras == right_paras:  # merge left and right
                left_instances.update(right_instances)
            else:
                adjust_ids = tuple([right_paras.index(p) for p in left_paras])
                for right_instance in right_instances:  # left and right must have the same paras structure
                    left_instances.add(tuple([right_instance[i] for i in adjust_ids]))
            return left_paras, left_instances
        else:  # atomic form
            gpl_predicate, gpl_paras = gpl_tree
            if gpl_predicate == 'Eq':
                gpl_paras = _parse_expr_to_algebraic_forms(gpl_paras, self.parsed_gdl)

            paras = []
            instances = {()}
            if paras_and_instances is not None:
                paras = list(paras_and_instances[0])  # list
                instances = paras_and_instances[1]  # set

            if gpl_predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:  # generate instances according algebraic forms
                dependent_entities = _get_geometric_constraints(gpl_predicate, gpl_paras, self.parsed_gdl)

                for entity_predicate, entity_paras in dependent_entities:  # constrained cartesian product
                    if entity_paras[0] in paras:
                        continue
                    paras.append(entity_paras[0])

                    new_instances = set()
                    for instance in instances:
                        for entity_instance in self.relation_instances[entity_predicate]:
                            new_instance = list(instance)
                            new_instance.append(entity_instance[0])
                            new_instances.add(tuple(new_instance))
                    instances = new_instances

                for instance in instances.copy():  # check constraint
                    replace = dict(zip(paras, instance))
                    replaced_expr = _replace_expr(gpl_paras, replace)
                    if not satisfy_algebraic_map[gpl_predicate](replaced_expr, self.entity_sym_to_value):
                        instances.remove(instance)

            else:  # generate instances according relation
                internal_same_ids = []  # [(j_a, j_b)]
                for j_a in range(len(gpl_paras)):
                    for j_b in range(j_a + 1, len(gpl_paras)):
                        if gpl_paras[j_a] == gpl_paras[j_b]:
                            internal_same_ids.append((j_a, j_b))
                mutual_same_ids = []  # [(i, j)]
                for i in range(len(paras)):
                    for j in range(len(gpl_paras)):
                        if paras[i] == gpl_paras[j]:
                            mutual_same_ids.append((i, j))
                added_ids = []  # [j]
                for j in range(len(gpl_paras)):
                    if gpl_paras[j] not in paras:
                        paras.append(gpl_paras[j])
                        added_ids.append(j)

                if gpl_predicate in self.relation_instances:  # dependent relation instances has been generated
                    gpl_instances = self.relation_instances[gpl_predicate]

                else:  # iteratively generate dependent relation instances
                    relation_gpl = self.parsed_gdl['Relations'][gpl_predicate]
                    gpl_paras, gpl_instances = self._generate_instances(relation_gpl['algebraic_forms'])

                    if gpl_paras != relation_gpl['paras']:
                        adjust_ids = tuple([gpl_paras.index(p) for p in relation_gpl['paras']])
                        adjusted_gpl_instances = set()
                        for gpl_instance in gpl_instances:
                            adjusted_gpl_instances.add(tuple([gpl_instance[i] for i in adjust_ids]))
                        gpl_instances = adjusted_gpl_instances

                    self.relation_instances[gpl_predicate] = gpl_instances

                new_instances = []
                for gpl_instance in gpl_instances:  # constrained cartesian product
                    passed = True
                    for j_a, j_b in internal_same_ids:  # check internal constraint
                        if gpl_instance[j_a] != gpl_instance[j_b]:
                            passed = False
                            break
                    if not passed:
                        continue

                    for instance in instances:
                        passed = True
                        for i, j in mutual_same_ids:  # check mutual constraint
                            if instance[i] != gpl_instance[j]:
                                passed = False
                                break
                        if not passed:
                            continue

                        new_instance = list(instance)
                        new_instance.extend([gpl_instance[j] for j in added_ids])
                        new_instances.append(tuple(new_instance))

                instances = new_instances

            return tuple(paras), instances

    def _generate_premises(self, premises_gpl, replace):
        if _is_negation(premises_gpl):  # remove negative form : ('~', ...)
            return None

        elif _is_conjunction(premises_gpl):  # conjunction : (..., '&', ...)
            left_side = self._generate_premises(premises_gpl[0], replace)
            right_side = self._generate_premises(premises_gpl[2], replace)
            if left_side is not None:
                if right_side is not None:
                    return left_side, '&', right_side
                else:
                    return left_side
            else:
                if right_side is not None:
                    return right_side
                else:
                    return None

        elif _is_disjunction(premises_gpl):  # disjunction: (..., '|', ...)
            left_side = self._generate_premises(premises_gpl[0], replace)
            right_side = self._generate_premises(premises_gpl[2], replace)
            if left_side is not None and right_side is not None:
                return left_side, '|', right_side
            else:
                return None

        else:  # atomic node: (predicate, instance)
            predicate, instance = premises_gpl
            if predicate == 'Eq':
                instance = self._adjust_expr(_replace_expr(instance, replace))
            else:
                instance = _replace_instance(instance, replace)

            return predicate, instance

    def _generate_conclusion(self, conclusion_gpl, replace):
        predicate, instance = conclusion_gpl
        if predicate == 'Eq':
            instance = self._adjust_expr(_replace_expr(instance, replace))
        else:
            instance = _replace_instance(instance, replace)

        return predicate, instance

    def _adjust_expr(self, expr):
        """
        1.添加Eq facts时 √
        2.添加Eq goal时 √
        3.生成premises和conclusion时 √
        """
        for sym in list(expr.free_symbols):
            if sym not in self.sym_to_sym:  # new symbols
                entities, attr = str(sym).split('.')
                replace = dict(zip(self.parsed_gdl['Attributions'][attr]['paras'], entities))
                self.sym_to_syms[sym] = set()
                for sym_multiple_form in self.parsed_gdl['Attributions'][attr]['multiple_forms']:
                    sym_multiple_form = symbols(''.join([replace[e] for e in sym_multiple_form]) + '.' + attr)
                    self.sym_to_syms[sym].add(sym_multiple_form)
                    self.sym_to_sym[sym_multiple_form] = sym

            if sym != self.sym_to_sym[sym]:  # replace sym_multiple_form with sym_unified_form
                expr = expr.subs(sym, self.sym_to_sym[sym])

        if str(expr)[0] == '-':  # adjust to a form without a leading negative sign
            expr = -expr

        return expr

    """↑--------Instance Generation-------↑"""

    """↓----------Forward Solving---------↓"""

    def apply(self, theorem):
        """Apply a theorem with parameterized form or parameter-free form.

        Args:
            theorem (str): Theorem to be applied. Two forms: a parameterized form and a parameter-free form.
                examples: 'adjacent_complementary_angle(l,k)'  # parameterized form
                          'adjacent_complementary_angle'  # parameter-free form

        Returns:
            result (bool): If applying the theorem adds new conditions, return True; otherwise, return False.
        """
        theorem_name, theorem_instance = _parse_theorem(theorem, self.parsed_gdl)
        theorem_gdl = self.parsed_gdl["Theorems"][theorem_name]
        applied = []  # (conclusion, premise_ids, theorem_instance)

        if theorem_instance is not None:  # parameterized mode
            if theorem_name in self.theorem_instances:
                if theorem_instance not in self.theorem_instances[theorem_name]:
                    return False

                premises, conclusion = self.theorem_instances[theorem_name][theorem_instance]

                passed, premise_ids = self._check_premises(premises)  # check premises
                if not passed:
                    return False

                # remove applied theorem_instance
                self.theorem_instances[theorem_name].pop(theorem_instance)

                applied.append((conclusion, premise_ids, theorem_instance))
            else:
                replace = dict(zip(theorem_gdl['paras'], theorem_instance))
                premises = self._generate_premises(theorem_gdl['premises'], replace)

                passed, premise_ids = self._check_premises(premises)  # check premises
                if not passed:
                    return False

                if not self._check_algebraic_forms((theorem_gdl['conclusion'], '&', theorem_gdl['premises']), replace):
                    return False

                conclusion = self._generate_conclusion(theorem_gdl['conclusion'], replace)
                applied.append((conclusion, premise_ids, theorem_instance))

        else:  # parameter-free mode
            for theorem_instance in self._get_theorem_instances(theorem_name):
                premises, conclusion = self.theorem_instances[theorem_name][theorem_instance]

                passed, premise_ids = self._check_premises(premises)  # check premises
                if not passed:
                    continue

                # remove applied theorem_instance
                self.theorem_instances[theorem_name].pop(theorem_instance)

                applied.append((conclusion, premise_ids, theorem_instance))

        update = False
        affected_sub_goal_ids = set()
        for conclusion, premise_ids, theorem_instance in applied:
            operation_id = self._add_operation(('apply', theorem_name, theorem_instance))  # add conclusion
            added, sub_goal_ids = self._add_fact(conclusion[0], conclusion[1], premise_ids, operation_id)
            update = added or update
            affected_sub_goal_ids.update(sub_goal_ids)

        # check affected sub goals
        self._check_sub_goals(affected_sub_goal_ids)

        return update

    def _check_premises(self, premises):
        if _is_conjunction(premises):  # conjunction : (..., '&', ...)
            left_passed, left_premise_ids = self._check_premises(premises[0])
            if not left_passed:
                return False, None

            right_passed, right_premise_ids = self._check_premises(premises[2])
            if not right_passed:
                return False, None

            left_premise_ids.update(right_premise_ids)

            return True, left_premise_ids

        elif _is_disjunction(premises):  # disjunction: (..., '|', ...)
            left_passed, left_premise_ids = self._check_premises(premises[0])
            if left_passed:
                return True, left_premise_ids

            right_passed, right_premise_ids = self._check_premises(premises[2])
            if right_passed:
                return True, right_premise_ids

            return False, None

        else:  # atomic node: (predicate, instance)
            predicate, instance = premises
            if predicate == 'Eq':  # algebraic premise
                status, premise_ids = self._check_algebraic_premise(instance)
                # print(predicate, instance, status)
                if status == 1:
                    return True, premise_ids

            else:  # geometric premise
                if premises in self.fact_id:
                    return True, {self.fact_id[premises]}

            return False, None

    def _check_algebraic_premise(self, expr):
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
            if satisfy_algebraic_map['Eq'](expr):
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
        self.attempted_equations_cache[equations_tuple] = 1
        return 1, premise_ids

    def _check_algebraic_forms(self, algebraic_forms, replace=None):
        """
        1.前向求解，参数化运行，退化条件：~的检查
        2.后向 set goal和参数化分解goal时的检查，只有合理的goal才会分解
        """
        if _is_negation(algebraic_forms):  # negative form : ('~', ...)
            return not self._check_algebraic_forms(algebraic_forms[1], replace)

        elif _is_conjunction(algebraic_forms):  # conjunction : (..., '&', ...)
            if not self._check_algebraic_forms(algebraic_forms[0], replace):
                return False
            if not self._check_algebraic_forms(algebraic_forms[2], replace):
                return False
            return True

        elif _is_disjunction(algebraic_forms):  # disjunction: (..., '|', ...)
            if self._check_algebraic_forms(algebraic_forms[0], replace):
                return True
            if self._check_algebraic_forms(algebraic_forms[2], replace):
                return True
            return False

        else:  # atomic node: (predicate, instance)
            predicate, instance = algebraic_forms

            if predicate == 'Eq':
                instance = _parse_expr_to_algebraic_forms(instance, self.parsed_gdl)

            if predicate in {'Eq', 'G', 'Geq', 'L', 'Leq', 'Ueq'}:  # algebraic forms
                if replace is not None:
                    instance = _replace_expr(instance, replace)

                return satisfy_algebraic_map[predicate](instance, self.entity_sym_to_value)

            else:  # geometric forms
                if replace is not None:
                    instance = _replace_instance(instance, replace)

                if predicate in self.relation_instances:
                    return instance in self.relation_instances[predicate]

                relation_gdl = self.parsed_gdl['Relations'][predicate]
                replace = dict(zip(relation_gdl['paras'], instance))

                return self._check_algebraic_forms(relation_gdl['algebraic_forms'], replace)

    def _add_fact(self, predicate, instance, premise_ids, operation_id):
        if predicate in satisfy_algebraic_map.keys():
            return self._add_algebraic(predicate, instance, premise_ids, operation_id)
        elif predicate in {'Point', 'Line', 'Circle'}:
            return self._add_entity(predicate, instance, premise_ids, operation_id)
        elif predicate in {'SamePoint', 'SameLine', 'SameCircle'}:
            return self._add_same(predicate, instance, premise_ids, operation_id)
        else:
            return self._add_relation(predicate, instance, premise_ids, operation_id)

    def _add_entity(self, predicate, instance, premise_ids, operation_id):
        if (predicate, instance) in self.fact_id or instance[0] not in self.letters:
            return False, set()

        fact_id = len(self.facts)
        self.facts.append((predicate, instance, set(premise_ids), set(premise_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.fact_groups[operation_id].add(fact_id)

        self.relation_instances[predicate].add(instance)
        self.letters.remove(instance[0])

        return True, set()

    def _add_relation(self, predicate, instance, premise_ids, operation_id):
        if (predicate, instance) in self.fact_id:
            return False, set()

        fact_id = len(self.facts)
        entity_ids = set()
        for dependent_entity in _get_geometric_constraints(predicate, instance, self.parsed_gdl):
            entity_ids.add(self.fact_id[dependent_entity])
        self.facts.append((predicate, instance, set(premise_ids), entity_ids, operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.fact_groups[operation_id].add(fact_id)

        affected_sub_goal_ids = set()
        if (predicate, instance) in self.sub_goal_ids:
            affected_sub_goal_ids = self.sub_goal_ids[(predicate, instance)]

        return True, affected_sub_goal_ids

    def _add_same(self, predicate, instance, premise_ids, operation_id):
        """Add SamePoint, SameLine, and SameCircle, and remove redundant facts. For two equivalent entities A and B:
        1.Sort entities and take entity comes later in the sorted order (entity B) as removed entity.
        2.Replace B with A in all relations and add new relation to self.facts.
        3.For any symbols in self.sym_to_value, if contain B, add A.sym - self.sym_to_value[B.sym] to self.facts.
        4.For any symbols in self.equations, if contain A or B, add A.sym - B.sym to self.facts.
        """
        if instance[0] == instance[1]:
            return False, set()

        instance = sorted([instance, (instance[1], instance[0])])[0]
        A, B = instance

        if (predicate, instance) in self.fact_id:
            return False, set()

        fact_id = len(self.facts)
        entity_ids = set()
        for dependent_entity in _get_geometric_constraints(predicate, instance, self.parsed_gdl):
            entity_ids.add(self.fact_id[dependent_entity])
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.fact_groups[operation_id].add(fact_id)
        affected_goal_ids = set()

        # Replace B with A in all relations and add new relation to self.facts
        for b_fact_id in range(len(self.facts)):
            predicate, instance, _, _, _ = self.facts[b_fact_id]
            if predicate in {'Equation', 'Point', 'Line', 'Circle', 'SamePoint', 'SameLine', 'SameCircle'}:
                continue
            if B not in instance:
                continue
            instance = tuple([e if e != B else A for e in instance])
            operation_id = self._add_operation(('auto', 'same_entity_extend', None))
            _, sub_goal_ids = self._add_fact(predicate, instance, {fact_id, b_fact_id}, operation_id)
            affected_goal_ids.update(sub_goal_ids)

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
            operation_id = self._add_operation(('auto', 'same_entity_extend', None))
            _, sub_goal_ids = self._add_fact('Eq', instance, {fact_id, b_fact_id}, operation_id)
            affected_goal_ids.update(sub_goal_ids)

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
            operation_id = self._add_operation(('auto', 'same_entity_extend', None))
            _, sub_goal_ids = self._add_fact('Eq', instance, {fact_id}, operation_id)
            affected_goal_ids.update(sub_goal_ids)

        return True, affected_goal_ids

    def _add_algebraic(self, predicate, instance, premise_ids, operation_id):
        instance = self._adjust_expr(instance)
        if len(instance.free_symbols) == 0 or (predicate, instance) in self.fact_id:
            return False, set()

        fact_id = len(self.facts)
        entity_ids = set()
        for dependent_entity in _get_geometric_constraints(predicate, instance, self.parsed_gdl):
            entity_ids.add(self.fact_id[dependent_entity])
        self.facts.append((predicate, instance, set(premise_ids), set(entity_ids), operation_id))
        self.fact_id[(predicate, instance)] = fact_id
        self.predicate_to_fact_ids[predicate].add(fact_id)
        self.fact_groups[operation_id].add(fact_id)

        if predicate != 'Eq' or self.operations[operation_id] == ('auto', 'solve_eq', None):
            return True, set()

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
            return True, set()

        # merge equations group
        deleted_group_ids = set()
        for group_id in self.equations:
            simplified_eqs, premise_ids_list, syms = self.equations[group_id]
            if len(new_syms & syms) > 0:
                deleted_group_ids.add(group_id)
                new_simplified_eqs.extend(simplified_eqs)
                new_premise_ids_list.extend(premise_ids_list)
                new_syms.update(syms)

        for group_id in deleted_group_ids:  # delete old groups
            del self.equations[group_id]

        affected_sub_goal_ids = set()  # influenced sub_goals
        for sub_goal_id in self.simplified_eq_sub_goal:
            if len(new_syms & self.simplified_eq_sub_goal[sub_goal_id][2]) > 0:
                affected_sub_goal_ids.add(sub_goal_id)

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

                    solved_values[new_syms[j]] = solutions[0][j]  # save solved value
        except FunctionTimedOut:
            pass

        # split equations group
        if len(solved_values) == 0:  # no solved value
            self.equations[self.group_count] = (tuple(new_simplified_eqs), tuple(new_premise_ids_list), set(new_syms))
            self.group_count += 1
            return True, affected_sub_goal_ids

        operation_id = self._add_operation(('auto', 'solve_eq', None))  # add the solved values
        premise_ids = set()
        for new_premise_ids in new_premise_ids_list:
            premise_ids.update(new_premise_ids)
        for sym in solved_values:
            instance = sym - solved_values[sym]
            self.sym_to_value[sym] = solved_values[sym]
            self._add_fact('Eq', instance, premise_ids, operation_id)

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

        return True, affected_sub_goal_ids

    def _add_operation(self, operation):
        operation_id = len(self.operations)
        self.operations.append(operation)
        self.fact_groups[operation_id] = set()
        return operation_id

    """↑----------Forward Solving---------↑"""

    """↓---------Backward Solving---------↓"""

    def set_goal(self, goal):
        if len(self.goals) > 0:
            raise Exception("The function 'set_goal' is only used to set the initial goal.")

        goal_tree = _parse_goal(goal)
        # draw_gpl(goal_tree, filename='goal_tree')

        if not self._check_algebraic_forms(goal_tree):
            raise Exception(f"Algebraic forms check not passed when set init goal '{goal}'.")

        operation_id = self._add_operation(('auto', "set_initial_goal", None))
        added, sub_goal_ids = self._add_goal(goal_tree, operation_id, None)

        self._check_sub_goals(sub_goal_ids)  # update influenced sub goals

        return added

    def decompose(self, theorem):
        """decompose according to theorem."""
        theorem_name, theorem_instance = _parse_theorem(theorem, self.parsed_gdl)
        theorem_gdl = self.parsed_gdl["Theorems"][theorem_name]
        decomposed = []  # (premises, root_sub_goal_ids, theorem_instance)

        if theorem_instance is not None:  # parameterized mode
            if theorem_name in self.theorem_instances:
                if theorem_instance not in self.theorem_instances[theorem_name]:
                    return False
                premises, conclusion = self.theorem_instances[theorem_name][theorem_instance]
                root_sub_goal_ids = self._get_decomposed_sub_goal_ids(conclusion)
                if len(root_sub_goal_ids) == 0:
                    return False
                decomposed.append((premises, root_sub_goal_ids, theorem_instance))
            else:
                replace = dict(zip(theorem_gdl['paras'], theorem_instance))
                conclusion = self._generate_conclusion(theorem_gdl['conclusion'], replace)
                root_sub_goal_ids = self._get_decomposed_sub_goal_ids(conclusion)
                if len(root_sub_goal_ids) == 0:
                    return False
                if not self._check_algebraic_forms(theorem_gdl['premises'], replace):
                    return False
                premises = self._generate_premises(theorem_gdl['premises'], replace)
                decomposed.append((premises, root_sub_goal_ids, theorem_instance))

        else:  # parameter-free mode
            for theorem_instance in self._get_theorem_instances(theorem_name):
                premises, conclusion = self.theorem_instances[theorem_name][theorem_instance]
                sub_goal_ids = self._get_decomposed_sub_goal_ids(conclusion)
                if len(sub_goal_ids) == 0:
                    continue
                decomposed.append((premises, sub_goal_ids, theorem_instance))

        update = False
        affected_sub_goal_ids = set()
        for premises, root_sub_goal_ids, theorem_instance in decomposed:
            for sub_goal_id in root_sub_goal_ids:
                operation_id = self._add_operation(('decompose', theorem_name, theorem_instance))
                decomposed, sub_goal_ids = self._add_goal(premises, operation_id, sub_goal_id)
                affected_sub_goal_ids.update(sub_goal_ids)
                update = decomposed or update

        # check affected sub goals
        self._check_sub_goals(affected_sub_goal_ids)

        return update

    def _get_decomposed_sub_goal_ids(self, conclusion):
        root_sub_goal_ids = set()

        if conclusion[0] == 'Eq':  # algebraic goals
            for sub_goal_id in self.simplified_eq_sub_goal:
                if self.status_of_goal[self.sub_goals[sub_goal_id][2]] != 0:
                    continue
                if self.status_of_sub_goal[sub_goal_id] != 0:
                    continue
                if len(self.simplified_eq_sub_goal[sub_goal_id][2] & conclusion[1].free_symbols) == 0:
                    continue
                root_sub_goal_ids.add(sub_goal_id)

        else:  # geometric goals
            if conclusion in self.sub_goal_ids:
                for sub_goal_id in self.sub_goal_ids[conclusion]:
                    if self.status_of_goal[self.sub_goals[sub_goal_id][2]] != 0:
                        continue
                    if self.status_of_sub_goal[sub_goal_id] != 0:
                        continue
                    root_sub_goal_ids.add(sub_goal_id)

        return root_sub_goal_ids

    def _add_goal(self, sub_goal_tree, operation_id, root_sub_goal_id):
        if root_sub_goal_id is not None:
            # root goal has already been solved and does not need to be further decomposed
            if self.status_of_goal[self.sub_goals[root_sub_goal_id][2]] != 0:
                return False, set()

            # check if sibling goals contain the same operation
            for goal_id in self.leaf_goal_ids[root_sub_goal_id]:
                if self.operations[operation_id] == self.operations[self.goals[goal_id][1]]:
                    return False, set()

            # check if root goals contain the same operation
            check_root_sub_goal_id = root_sub_goal_id
            while check_root_sub_goal_id is not None:
                goal_id = self.sub_goals[check_root_sub_goal_id][2]
                if self.operations[operation_id] == self.operations[self.goals[goal_id][1]]:
                    return False, set()
                check_root_sub_goal_id = self.goals[goal_id][2]

        goal_id = len(self.goals)
        sub_goal_id_tree, sub_goal_ids = self._add_sub_goals(sub_goal_tree, goal_id)
        self.goals.append((sub_goal_id_tree, operation_id, root_sub_goal_id))
        self.status_of_goal[goal_id] = 0
        self.premise_ids_of_goal[goal_id] = set()
        if root_sub_goal_id is not None:
            self.leaf_goal_ids[root_sub_goal_id].add(goal_id)

        return True, sub_goal_ids

    def _add_sub_goals(self, sub_goal_tree, goal_id):
        if _is_negation(sub_goal_tree):  # negative form
            sub_goal_id_tree, sub_goal_ids = self._add_sub_goals(sub_goal_tree[1], goal_id)
            self._set_status_of_sub_goal(sub_goal_id_tree, -1)  # negative sub goals do not require solving
            return ('~', sub_goal_id_tree), sub_goal_ids

        elif _is_conjunction(sub_goal_tree) or _is_disjunction(sub_goal_tree):  # conjunction or disjunction
            left_sub_goal_id_tree, left_sub_goal_ids = self._add_sub_goals(sub_goal_tree[0], goal_id)
            right_sub_goal_id_tree, right_sub_goal_ids = self._add_sub_goals(sub_goal_tree[2], goal_id)
            left_sub_goal_ids.update(right_sub_goal_ids)
            return (left_sub_goal_id_tree, sub_goal_tree[1], right_sub_goal_id_tree), left_sub_goal_ids

        else:  # atomic node: (predicate, instance)
            sub_goal_id = len(self.sub_goals)
            predicate, instance = sub_goal_tree
            if predicate == 'Eq':
                instance = self._adjust_expr(instance)
                self.simplified_eq_sub_goal[sub_goal_id] = (instance, set(), set(), set())
            self.sub_goals.append((predicate, instance, goal_id))
            self.status_of_sub_goal[sub_goal_id] = 0
            self.premise_ids_of_sub_goal[sub_goal_id] = set()
            self.leaf_goal_ids[sub_goal_id] = set()
            if (predicate, instance) not in self.sub_goal_ids:
                self.sub_goal_ids[(predicate, instance)] = {sub_goal_id}
            else:
                self.sub_goal_ids[(predicate, instance)].add(sub_goal_id)
            self.predicate_to_sub_goal_ids[predicate].add(sub_goal_id)
            return sub_goal_id, {sub_goal_id}

    def _check_sub_goals(self, sub_goal_ids):
        if len(sub_goal_ids) == 0:
            return

        affected_goal_ids = set()

        for sub_goal_id in sub_goal_ids:
            # skip nodes that do not require checking
            if self.status_of_goal[self.sub_goals[sub_goal_id][2]] != 0:
                continue
            if self.status_of_sub_goal[sub_goal_id] != 0:
                continue

            predicate, instance, goal_id = self.sub_goals[sub_goal_id]

            if predicate == 'Eq':
                instance = self.simplified_eq_sub_goal[sub_goal_id][0]
                status, premise_ids = self._check_algebraic_premise(instance)

                if status in {1, -1}:  # has solution, update status
                    self._set_status_of_sub_goal(sub_goal_id, status)
                    premise_ids.update(self.simplified_eq_sub_goal[sub_goal_id][1])
                    self.premise_ids_of_sub_goal[sub_goal_id] = premise_ids
                    affected_goal_ids.add(goal_id)
                else:  # no solution, simplify expr
                    premise_ids = self.simplified_eq_sub_goal[sub_goal_id][1]
                    for sym in list(instance.free_symbols):
                        if sym in self.sym_to_value:
                            instance = instance.subs(self.sym_to_value)
                            premise_ids.add(self.fact_id[('Eq', sym - self.sym_to_value[sym])])

                    dependent_syms = set(instance.free_symbols)
                    group_ids = set()
                    for group_id in self.equations:
                        if len(dependent_syms & self.equations[group_id][2]) > 0:
                            dependent_syms.update(self.equations[group_id][2])
                            group_ids.add(group_id)

                    self.simplified_eq_sub_goal[sub_goal_id] = (instance, premise_ids, dependent_syms, group_ids)
            else:
                if (predicate, instance) in self.fact_id:
                    self._set_status_of_sub_goal(sub_goal_id, 1)
                    self.premise_ids_of_sub_goal[sub_goal_id] = {self.fact_id[(predicate, instance)]}
                    affected_goal_ids.add(goal_id)
                elif predicate in {'Point', 'Line', 'Circle'}:
                    self._set_status_of_sub_goal(sub_goal_id, -1)
                    affected_goal_ids.add(goal_id)

        self._check_goals(affected_goal_ids)

    def _set_status_of_sub_goal(self, sub_goal_id, status):
        if self.status_of_sub_goal[sub_goal_id] != 0:
            return

        self.status_of_sub_goal[sub_goal_id] = status
        for leaf_goal_id in self.leaf_goal_ids[sub_goal_id]:
            if self.status_of_goal[leaf_goal_id] != 0:
                self._set_status_of_goal(leaf_goal_id, -1)

    def _check_goals(self, goal_ids):
        if len(goal_ids) == 0:
            return

        affected_sub_goal_ids = set()
        for goal_id in goal_ids:
            if self.status_of_goal[goal_id] != 0:  # skip nodes that do not require checking
                continue

            sub_goal_id_tree, operation_id, root_sub_goal_id = self.goals[goal_id]
            status, premise_ids = self._check_goal(sub_goal_id_tree)

            if status == 1:
                self._set_status_of_goal(goal_id, 1)
                if root_sub_goal_id is not None:  # apply theorem
                    _, theorem_name, theorem_instance = self.operations[operation_id]
                    theorem_gpl = self.parsed_gdl['Theorems'][theorem_name]
                    replace = dict(zip(theorem_gpl['paras'], theorem_instance))
                    conclusion = self._generate_conclusion(theorem_gpl['conclusion'], replace)
                    operation_id = self._add_operation(('apply', theorem_name, theorem_instance))
                    added, sub_goal_ids = self._add_fact(conclusion[0], conclusion[1], premise_ids, operation_id)
                    affected_sub_goal_ids.update(sub_goal_ids)
                self.premise_ids_of_goal[goal_id] = premise_ids

            elif status == -1:
                self._set_status_of_goal(goal_id, -1)
                self.premise_ids_of_goal[goal_id] = premise_ids

        self._check_sub_goals(affected_sub_goal_ids)

    def _check_goal(self, sub_goal_id_tree):
        if _is_negation(sub_goal_id_tree):  # negative form
            return 1, set()  # every negative form has passed algebraic form checking and must be true

        elif _is_conjunction(sub_goal_id_tree):
            left_status, left_premise_ids = self._check_goal(sub_goal_id_tree[0])
            if left_status == -1:
                return -1, left_premise_ids

            right_status, right_premise_ids = self._check_goal(sub_goal_id_tree[2])
            if right_status == -1:
                return -1, right_premise_ids

            left_premise_ids.update(right_premise_ids)
            if left_status == 1 and right_status == 1:
                return 1, left_premise_ids

            return 0, set()

        elif _is_disjunction(sub_goal_id_tree):
            left_status, left_premise_ids = self._check_goal(sub_goal_id_tree[0])
            if left_status == 1:
                return 1, left_premise_ids

            right_status, right_premise_ids = self._check_goal(sub_goal_id_tree[2])
            if right_status == 1:
                return 1, right_premise_ids

            if left_status == -1 and right_status == -1:
                left_premise_ids.update(right_premise_ids)
                return 1, left_premise_ids

            return 0, set()
        else:
            if self.status_of_sub_goal[sub_goal_id_tree] in {1, -1}:
                return self.status_of_sub_goal[sub_goal_id_tree], self.premise_ids_of_sub_goal[sub_goal_id_tree].copy()
            return 0, set()

    def _set_status_of_goal(self, goal_id, status):
        if self.status_of_goal[goal_id] != 0:
            return

        self.status_of_goal[goal_id] = status  # set status of goal

        sub_goals = [self.goals[goal_id][0]]  # set status of sub goal
        while len(sub_goals) > 0:
            sub_goal_id_tree = sub_goals.pop()
            if isinstance(sub_goal_id_tree, int):
                self._set_status_of_sub_goal(sub_goal_id_tree, -1)
            elif _is_conjunction(sub_goal_id_tree) or _is_disjunction(sub_goal_id_tree):
                sub_goals.append(sub_goal_id_tree[0])
                sub_goals.append(sub_goal_id_tree[2])

    """↑---------Backward Solving---------↑"""

    """↓-------------Outputs--------------↓"""

    def show_gc(self):
        operation_ids = set()
        goal_related_operation_ids = set()
        if len(self.goals) > 0 and self.status_of_goal[0] == 1:
            goal_related_premise_ids = list(self.premise_ids_of_goal[0])
        else:
            goal_related_premise_ids = []
        for fact_id in goal_related_premise_ids:
            goal_related_operation_ids.add(self.facts[fact_id][4])
            for new_fact_id in self.facts[fact_id][2]:
                if new_fact_id not in goal_related_premise_ids:
                    goal_related_premise_ids.append(new_fact_id)
        goal_related_premise_ids = set(goal_related_premise_ids)

        construction_pf = '{0:<3}{1:<40}'
        construction_pfu = '\033[32m' + construction_pf + '\033[0m'
        parsed_construction_pfu = '\033[37m{}\033[0m'
        print('\033[33m\nConstructions:\033[0m')
        for operation_id in self.constructions:
            construction = self.operations[operation_id][1] + ':' + self.operations[operation_id][2]
            if operation_id in goal_related_operation_ids:
                print(construction_pfu.format(operation_id, construction))
            else:
                print(construction_pf.format(operation_id, construction))

            used_branch, parsed_construction = self.constructions[operation_id]
            for branch in range(len(parsed_construction)):
                t_entities, d_entities, added_facts, equations, inequalities, solved_value = parsed_construction[branch]
                branch_str = '   branch: {}'.format(
                    branch + 1)
                t_entities = '   target_entities: {}'.format(
                    str([_anti_parse_fact(fact) for fact in t_entities]))
                dependent_entities = '   dependent_entities: {}'.format(
                    str([_anti_parse_fact(fact) for fact in d_entities]))
                added_facts = '   added_facts: {}'.format(
                    str([_anti_parse_fact(fact) for fact in added_facts]))
                equations = '   equations: {}'.format(
                    ', '.join([_anti_parse_fact(('Eq', fact)) for fact in equations]))
                inequalities = '   inequalities: {}'.format(
                    ', '.join([_anti_parse_fact(fact) for fact in inequalities]))
                if solved_value is not None:
                    t_syms, values = solved_value
                    solved_value = [f"({', '.join([str(sym) for sym in t_syms])})",
                                    f"({', '.join([str(round(float(value), 4)) for value in values])})"]
                    solved_value = f"[{', '.join(solved_value)}]"
                else:
                    solved_value = 'None'
                solved_value = '   solved_value: {}'.format(solved_value)

                if branch + 1 == used_branch:
                    print(branch_str)
                    print(t_entities)
                    print(dependent_entities)
                    print(added_facts)
                    print(equations)
                    print(inequalities)
                    print(solved_value)
                else:
                    parsed_construction_pfu.format(branch_str)
                    parsed_construction_pfu.format(t_entities)
                    parsed_construction_pfu.format(dependent_entities)
                    parsed_construction_pfu.format(added_facts)
                    parsed_construction_pfu.format(equations)
                    parsed_construction_pfu.format(inequalities)
                    parsed_construction_pfu.format(solved_value)
                print()

        entity_pf = '{0:<12}{1:<15}{2:<31}{3:<25}{4:<25}{5:<15}{6:<100}'
        entity_pfu = '\033[32m' + entity_pf + '\033[0m'
        for entity in ['Point', 'Line', 'Circle']:
            if len(self.predicate_to_fact_ids[entity]) == 0:
                continue
            print(f'\033[36mEntity - {entity}:\033[0m')
            print('\033[36m' + entity_pf.format(
                'fact_id', 'instance', 'values', 'premise_ids', 'entity_ids', 'operation_id', 'operation') + '\033[0m')
            for fact_id in sorted(list(self.predicate_to_fact_ids[entity])):
                predicate, instance, premise_ids, entity_ids, operation_id = self.facts[fact_id]
                operation_ids.add(operation_id)
                operation = _anti_parse_operation(self.operations[operation_id])
                if entity == 'Point':
                    values = str((round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.x')]), 4),
                                  round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.y')]), 4)))
                elif entity == 'Line':
                    values = str((round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.k')]), 4),
                                  round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.b')]), 4)))
                else:
                    values = str((round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.u')]), 4),
                                  round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.v')]), 4),
                                  round(float(self.entity_sym_to_value[symbols(f'{instance[0]}.r')]), 4)))
                instance = f'({instance[0]})'
                premise_ids = _format_ids(premise_ids)
                entity_ids = _format_ids(entity_ids)

                if fact_id in goal_related_premise_ids:
                    print(entity_pfu.format(fact_id, instance, values, premise_ids, entity_ids,
                                            operation_id, operation))
                else:
                    print(entity_pf.format(fact_id, instance, values, premise_ids, entity_ids,
                                           operation_id, operation))
            print()

        relation_pf = '{0:<12}{1:<40}{2:<28}{3:<28}{4:<15}{5:<100}'
        relation_pfu = '\033[32m' + relation_pf + '\033[0m'
        for predicate in self.predicate_to_fact_ids:
            if predicate in {'Point', 'Line', 'Circle'}:
                continue
            if predicate in satisfy_algebraic_map.keys():
                continue
            if len(self.predicate_to_fact_ids[predicate]) == 0:
                continue

            print(f"\033[36m(Geometric) Relation - {predicate}:\033[0m")
            print('\033[36m' + relation_pf.format('fact_id', 'instance', 'premise_ids', 'entity_ids',
                                                  'operation_id', 'operation') + '\033[0m')
            for fact_id in sorted(list(self.predicate_to_fact_ids[predicate])):
                predicate, instance, premise_ids, entity_ids, operation_id = self.facts[fact_id]
                operation_ids.add(operation_id)
                operation = _anti_parse_operation(self.operations[operation_id])
                instance = '(' + ','.join(instance) + ')'
                premise_ids = _format_ids(premise_ids)
                entity_ids = _format_ids(entity_ids)
                if fact_id in goal_related_premise_ids:
                    print(relation_pfu.format(fact_id, instance, premise_ids, entity_ids, operation_id, operation))
                else:
                    print(relation_pf.format(fact_id, instance, premise_ids, entity_ids, operation_id, operation))
            print()

        for predicate in satisfy_algebraic_map.keys():
            if len(self.predicate_to_fact_ids[predicate]) > 0:
                print(f'\033[36m(Algebraic) Relation - {predicate}:\033[0m')
                print('\033[36m' + relation_pf.format(
                    'fact_id', 'instance', 'premise_ids', 'entity_ids', 'operation_id', 'operation') + '\033[0m')
                for fact_id in sorted(list(self.predicate_to_fact_ids[predicate])):
                    predicate, instance, premise_ids, entity_ids, operation_id = self.facts[fact_id]
                    operation_ids.add(operation_id)
                    operation = _anti_parse_operation(self.operations[operation_id])
                    instance = str(instance).replace(' ', '')
                    premise_ids = _format_ids(premise_ids)
                    entity_ids = _format_ids(entity_ids)
                    if fact_id in goal_related_premise_ids:
                        print(relation_pfu.format(fact_id, instance, premise_ids, entity_ids, operation_id, operation))
                    else:
                        print(relation_pf.format(fact_id, instance, premise_ids, entity_ids, operation_id, operation))
                print()

        if len(self.goals) > 0:
            goal_pf = '{0:<11}{1:<55}{2:<6}{3:<10}{4:<26}{5:<15}{6:<100}'
            goal_pfs = '\033[32m' + goal_pf + '\033[0m'
            goal_pfu = '\033[31m' + goal_pf + '\033[0m'
            print("\033[34mGoals:\033[0m")
            print('\033[34m' + goal_pf.format('goal_id', 'sub_goal_id_tree', 'root', 'status',
                                              'premise_ids', 'operation_id', 'operation') + '\033[0m')
            for goal_id in range(len(self.goals)):
                sub_goal_id_tree, operation_id, root_sub_goal_id = self.goals[goal_id]
                sub_goal_id_tree = str(sub_goal_id_tree).replace(' ', '').replace("'", '')
                if len(sub_goal_id_tree) > 53:
                    sub_goal_id_tree = sub_goal_id_tree[:50] + '...'
                operation_ids.add(operation_id)
                operation = _anti_parse_operation(self.operations[operation_id])
                root_sub_goal_id = str(root_sub_goal_id)
                status = self.status_of_goal[goal_id]
                premise_ids = _format_ids(self.premise_ids_of_goal[goal_id])

                if status == 1:
                    print(goal_pfs.format(goal_id, sub_goal_id_tree, root_sub_goal_id, status, premise_ids,
                                          operation_id, operation))
                elif status == -1:
                    print(goal_pfu.format(goal_id, sub_goal_id_tree, root_sub_goal_id, status, premise_ids,
                                          operation_id, operation))
                else:
                    print(goal_pf.format(goal_id, sub_goal_id_tree, root_sub_goal_id, status, premise_ids,
                                         operation_id, operation))
            print()

            sub_goal_pf = '{0:<12}{1:<30}{2:<40}{3:<10}{4:<30}{5:<15}{6:<50}'
            sub_goal_pfs = '\033[32m' + sub_goal_pf + '\033[0m'
            sub_goal_pfu = '\033[31m' + sub_goal_pf + '\033[0m'
            print("\033[34mSub Goals:\033[0m")
            print('\033[34m' + sub_goal_pf.format('sub_goal_id', 'predicate', 'instance', 'goal_id',
                                                  'leaf_goal_ids', 'status', 'premise_ids') + '\033[0m')
            last_goal_id = self.sub_goals[0][2]
            for sub_goal_id in range(len(self.sub_goals)):
                predicate, instance, goal_id = self.sub_goals[sub_goal_id]
                if goal_id != last_goal_id:
                    print()
                    last_goal_id = goal_id
                if predicate == 'Eq':
                    instance = str(instance).replace(' ', '')
                else:
                    instance = '(' + ','.join(instance) + ')'
                leaf_goal_ids = _format_ids(self.leaf_goal_ids[sub_goal_id])
                status = self.status_of_sub_goal[sub_goal_id]
                premise_ids = _format_ids(self.premise_ids_of_sub_goal[sub_goal_id])

                if status == 1:
                    print(sub_goal_pfs.format(sub_goal_id, predicate, instance, goal_id,
                                              leaf_goal_ids, status, premise_ids))
                elif status == -1:
                    print(sub_goal_pfu.format(sub_goal_id, predicate, instance, goal_id,
                                              leaf_goal_ids, status, premise_ids))
                else:
                    print(sub_goal_pf.format(sub_goal_id, predicate, instance, goal_id,
                                             leaf_goal_ids, status, premise_ids))
            print()

        if len(self.predicate_to_fact_ids['Eq']) > 0:
            sym_pf = '{0:<40}{1:<15}{2:<25}{3:<10}{4:<20}'
            sym_pfu = '\033[32m' + sym_pf + '\033[0m'
            print('\033[35mAlgebraic System - Symbols:\033[0m')
            print('\033[35m' + sym_pf.format(
                'attribution', 'sym', 'multiple_forms', 'fact_id', 'value') + '\033[0m')
            for sym in self.sym_to_syms:
                if '.' in str(sym):
                    entities, attr = str(sym).split('.')
                    predicate = self.parsed_gdl['Attributions'][attr]['name']
                    instance = ",".join(list(entities))
                    attr = f'{predicate}({instance})'
                    multiple_forms = '(' + ', '.join([str(item) for item in self.sym_to_syms[sym]]) + ')'
                else:
                    attr = f'Free({str(sym)})'
                    multiple_forms = '(' + str(sym) + ')'

                if sym in self.sym_to_value:
                    fact_id = self.fact_id[('Eq', sym - self.sym_to_value[sym])]
                    value = str(self.sym_to_value[sym])
                else:
                    fact_id = 'None'
                    value = "None"

                if fact_id != 'None' and fact_id in goal_related_premise_ids:
                    print(sym_pfu.format(attr, str(sym), multiple_forms, fact_id, value))
                else:
                    print(sym_pf.format(attr, str(sym), multiple_forms, fact_id, value))
            print()

            eq_groups_pf = '{0:<10}{1:<40}{2:<20}{3:<30}'
            print('\033[35mAlgebraic System - Equation groups:\033[0m')
            print('\033[35m' + eq_groups_pf.format(
                'group_id', 'simplified_eq', 'premise_ids', 'free_symbols') + '\033[0m')
            for group_id in self.equations:
                for i in range(len(self.equations[group_id][0])):
                    simplified_eq = str(self.equations[group_id][0][i]).replace(' ', '')
                    premise_ids = _format_ids(self.equations[group_id][1][i])
                    free_symbols = ', '.join([str(item) for item in self.equations[group_id][0][i].free_symbols])
                    free_symbols = '(' + free_symbols + ')'
                    print(eq_groups_pf.format(group_id, simplified_eq, premise_ids, free_symbols))
                print()

        if len(self.simplified_eq_sub_goal) > 0:
            algebraic_goal_pf = '{0:<10}{1:<40}{2:<20}{3:<45}{4:<20}'
            print('\033[35mAlgebraic System - Algebraic Goals:\033[0m')
            print('\033[35m' + algebraic_goal_pf.format(
                'goal_id', 'simplified_eq', 'premise_ids', 'dependent_syms', 'dependent_group_ids') + '\033[0m')
            for goal_id in self.simplified_eq_sub_goal:
                simplified_eq, premise_ids, dependent_syms, group_ids = self.simplified_eq_sub_goal[goal_id]
                simplified_eq = str(simplified_eq).replace(' ', '')
                premise_ids = _format_ids(premise_ids)
                dependent_syms = ','.join([str(item) for item in sorted(list(dependent_syms), key=str)])
                dependent_syms = '{' + dependent_syms + '}'
                if len(dependent_syms) > 43:
                    dependent_syms = dependent_syms[:40] + '...'
                group_ids = _format_ids(group_ids)
                print(algebraic_goal_pf.format(goal_id, simplified_eq, premise_ids, dependent_syms, group_ids))
            print()

        if len(self.relation_instances) > 0:
            relation_instance_pf = '{0:<45}{1:<100}'
            print('\033[33mRelation instances:\033[0m')
            print('\033[33m' + relation_instance_pf.format('relation_predicate', 'relation_instances') + '\033[0m')
            for relation_predicate in self.relation_instances:
                relation_instances = [f"({','.join(item)})" for item in self.relation_instances[relation_predicate]]
                relation_instances = f"[{', '.join(relation_instances)}]"
                print(relation_instance_pf.format(relation_predicate, relation_instances))
            print()

        if len(self.theorem_instances) > 0:
            theorem_instance_pf = '{0:<45}{1:<100}'
            print('\033[33mTheorem instances:\033[0m')
            print('\033[33m' + theorem_instance_pf.format('theorem_name', 'theorem_instances') + '\033[0m')
            for theorem_name in self.theorem_instances:
                theorem_instances = [f"({','.join(item)})" for item in self.theorem_instances[theorem_name]]
                theorem_instances = f"[{', '.join(theorem_instances)}]"
                print(theorem_instance_pf.format(theorem_name, theorem_instances))
            print()

        operation_pf = '{0:<15}{1:<50}'
        operation_pfu = '\033[32m' + operation_pf + '\033[0m'
        print('\033[33mOperations:\033[0m')
        print('\033[33m' + operation_pf.format('operation_id', 'operation') + '\033[0m')
        for operation_id in range(len(self.operations)):
            if operation_id not in operation_ids:
                continue
            operation = _anti_parse_operation(self.operations[operation_id])
            if operation_id in goal_related_operation_ids:
                print(operation_pfu.format(operation_id, operation))
            else:
                print(operation_pf.format(operation_id, operation))
        print()

    def get_gc(self):
        serialized_graph = ['<init_fact>']

        # forward
        edges = set()
        for fact_id in range(len(self.facts)):
            predicate, instance, premise_ids, entity_ids, operation_id = self.facts[fact_id]
            if len(premise_ids | entity_ids) == 0:
                if serialized_graph[-1] != '<init_fact>':
                    serialized_graph.append('&')
                serialized_graph.extend(_serialize_fact(predicate, instance))
            else:
                if len(premise_ids) > 0:  # temporary fix for bug 260413-01
                    edge = (tuple(sorted(list(premise_ids))), operation_id,
                            tuple(sorted(list(self.fact_groups[operation_id]))))
                else:
                    edge = (tuple(sorted(list(premise_ids | entity_ids))), operation_id,
                            tuple(sorted(list(self.fact_groups[operation_id]))))
                if edge in edges:
                    continue

                serialized_graph.append('<premises>')
                for premise_id in edge[0]:
                    predicate, instance, _, _, _ = self.facts[premise_id]
                    if serialized_graph[-1] != '<premises>':
                        serialized_graph.append('&')
                    serialized_graph.extend(_serialize_fact(predicate, instance))

                serialized_graph.append('<operation>')
                serialized_graph.extend(_serialize_operation(self.operations[operation_id]))

                serialized_graph.append('<conclusion>')
                for conclusion_id in edge[2]:
                    predicate, instance, _, _, _ = self.facts[conclusion_id]
                    if serialized_graph[-1] != '<conclusion>':
                        serialized_graph.append('|')
                    serialized_graph.extend(_serialize_fact(predicate, instance))

                edges.add(edge)

        if len(self.goals) == 0:
            return serialized_graph

        # backward
        serialized_graph.append('<init_goal>')
        serialized_graph.extend(_serialize_goal(self, self.goals[0][0]))

        for goal_id in range(1, len(self.goals)):
            sub_goal_id_tree, operation_id, root_sub_goal_id = self.goals[goal_id]
            serialized_graph.append('<goal>')
            predicate, instance, _ = self.sub_goals[root_sub_goal_id]
            serialized_graph.extend(_serialize_fact(predicate, instance))
            serialized_graph.append('<sub_goals>')
            serialized_graph.extend(_serialize_goal(self, sub_goal_id_tree))

        return serialized_graph

    def draw_gc(self, save_path='./', filename='gc', file_format='pdf', scale=1):
        center_x = float((self.sample_range['x_max'] + self.sample_range['x_min']) / 2)
        center_y = float((self.sample_range['y_max'] + self.sample_range['y_min']) / 2)
        radius = float(max((self.sample_range['x_max'] - self.sample_range['x_min']),
                           (self.sample_range['y_max'] - self.sample_range['y_min']))) / 2
        _, ax = plt.subplots(figsize=(radius * 4 * scale, radius * 4 * scale), dpi=512 / scale)
        ax.axis('equal')  # maintain the circle's aspect ratio
        ax.axis('off')  # hide the axes
        ax.set_xlim(center_x - radius * 1.3, center_x + radius * 1.3)
        ax.set_ylim(center_y - radius * 1.3, center_y + radius * 1.3)

        for fact_id in self.predicate_to_fact_ids['Line']:
            line = self.facts[fact_id][1][0]
            k = float(self.entity_sym_to_value[symbols(f'{line}.k')])
            b = float(self.entity_sym_to_value[symbols(f'{line}.b')])
            ax.axline((0, b), slope=k, color='blue', linewidth=radius * 0.8)

        for fact_id in self.predicate_to_fact_ids['Circle']:
            circle = self.facts[fact_id][1][0]
            u = float(self.entity_sym_to_value[symbols(f'{circle}.u')])
            v = float(self.entity_sym_to_value[symbols(f'{circle}.v')])
            r = float(self.entity_sym_to_value[symbols(f'{circle}.r')])
            ax.add_artist(plt.Circle((u, v), r, color="green", fill=False, linewidth=radius * 0.8))

        for fact_id in self.predicate_to_fact_ids['Point']:
            point = self.facts[fact_id][1][0]
            x = float(self.entity_sym_to_value[symbols(f'{point}.x')])
            y = float(self.entity_sym_to_value[symbols(f'{point}.y')])
            ax.plot(x, y, "o", color='red', markersize=radius * 2.5)
        # ax.plot(center_x, center_y, "o", color='green', markersize=radius * 3.5)

        random_number = random.Random(0)
        random_epoch = 100
        added_text = []  # (x, y)

        def _get_crossed_distance(checked):
            crossed = []
            for added in added_text:
                distance_between_text = math.sqrt((checked[0] - added[0]) ** 2 + (checked[1] - added[1]) ** 2)
                if distance_between_text < radius * 0.16 / scale:
                    crossed.append(distance_between_text)
            if len(crossed) == 0:
                return 0
            return sum(crossed) / len(crossed)

        def _get_text_coordinates(func, args):
            best_x, best_y = func(*args)
            best_crossed_distance = _get_crossed_distance((best_x, best_y))
            if best_crossed_distance != 0:
                for epoch_count in range(random_epoch):
                    random_x, random_y = func(*args)
                    crossed_distance = _get_crossed_distance((random_x, random_y))
                    if crossed_distance == 0:
                        best_x = random_x
                        best_y = random_y
                        break
                    if crossed_distance > best_crossed_distance:
                        best_x = random_x
                        best_y = random_y
                        best_crossed_distance = crossed_distance
            added_text.append((best_x, best_y))
            return best_x, best_y

        def _check_text_coordinates(text_x, text_y):
            if (center_x - radius * 1.2 < text_x < center_x + radius * 1.2 and
                    center_y - radius * 1.2 < text_y < center_y + radius * 1.2):
                return True
            return False

        def _get_point_text_coordinates(point_x, point_y):
            angle_rad = math.radians(random_number.randint(0, 359))
            random_x = point_x + (radius * 0.1 / scale) * math.cos(angle_rad)
            random_y = point_y + (radius * 0.1 / scale) * math.sin(angle_rad)

            if not _check_text_coordinates(random_x, random_y):
                random_x, random_y = _get_point_text_coordinates(point_x, point_y)
            return random_x, random_y

        for fact_id in self.predicate_to_fact_ids['Point']:
            point = self.facts[fact_id][1][0]
            x, y = _get_text_coordinates(
                _get_point_text_coordinates,
                (float(self.entity_sym_to_value[symbols(f'{point}.x')]),
                 float(self.entity_sym_to_value[symbols(f'{point}.y')]))
            )
            ax.text(x, y, point, ha='center', va='center', color='black', fontsize=radius * 10)

        def _get_line_text_coordinates(line_k, line_b):
            if abs(line_k) > 1:  # sample y
                if random_number.randint(0, 1) == 0:
                    random_y = random_number.uniform(center_y - radius * 1.1, center_y - radius)
                else:
                    random_y = random_number.uniform(center_y + radius, center_y + radius * 1.1)
                random_x = (random_y - line_b) / line_k
            else:  # sample x
                if random_number.randint(0, 1) == 0:
                    random_x = random_number.uniform(center_x - radius * 1.1, center_x - radius)
                else:
                    random_x = random_number.uniform(center_x + radius, center_x + radius * 1.1)
                random_y = line_k * random_x + line_b

            # x_step = math.sqrt(((radius * 0.08) ** 2 * (line_k ** 2)) / (line_k ** 2 + 1))
            #
            # if random_number.randint(0, 1) == 0:
            #     random_x = random_x - x_step
            #     x_step = -x_step
            # else:
            #     random_x = random_x + x_step
            #
            # random_y = - 1 / line_k * x_step + random_y

            if not _check_text_coordinates(random_x, random_y):
                random_x, random_y = _get_line_text_coordinates(line_k, line_b)
            return random_x, random_y

        for fact_id in self.predicate_to_fact_ids['Line']:
            line = self.facts[fact_id][1][0]
            x, y = _get_text_coordinates(
                _get_line_text_coordinates,
                (float(self.entity_sym_to_value[symbols(f'{line}.k')]),
                 float(self.entity_sym_to_value[symbols(f'{line}.b')]))
            )
            ax.text(x, y, line, ha='center', va='center', color='black', fontsize=radius * 10)

        def _get_circle_text_coordinates(circle_u, circle_v, circle_r):
            angle_deg = math.degrees(math.atan((center_y - circle_v) / (center_x - circle_u)))
            angle_deg = angle_deg + random_number.randint(-30, 30)
            if center_x < circle_u:
                angle_deg = (angle_deg + 180) % 360
            # random_x = circle_u + (circle_r + radius * 0.08) * math.cos(math.radians(angle_deg))
            # random_y = circle_v + (circle_r + radius * 0.08) * math.sin(math.radians(angle_deg))
            random_x = circle_u + circle_r * math.cos(math.radians(angle_deg))
            random_y = circle_v + circle_r * math.sin(math.radians(angle_deg))

            if not _check_text_coordinates(random_x, random_y):
                random_x, random_y = _get_circle_text_coordinates(circle_u, circle_v, circle_r)
            return random_x, random_y

        for fact_id in self.predicate_to_fact_ids['Circle']:
            circle = self.facts[fact_id][1][0]
            x, y = _get_text_coordinates(
                _get_circle_text_coordinates,
                (float(self.entity_sym_to_value[symbols(f'{circle}.u')]),
                 float(self.entity_sym_to_value[symbols(f'{circle}.v')]),
                 float(self.entity_sym_to_value[symbols(f'{circle}.r')]))
            )
            ax.text(x, y, circle, ha='center', va='center', color='black', fontsize=radius * 10)

        plt.savefig(save_path + filename + '.' + file_format, bbox_inches='tight')

    def draw_sg(self, save_path='./', filename='sg', file_format='pdf'):
        forward_graph = Graph()
        if len(self.status_of_goal) > 0 and self.status_of_goal[0] == 1:
            goal_related_premise_ids = list(self.premise_ids_of_goal[0])
        else:
            goal_related_premise_ids = []
        for fact_id in goal_related_premise_ids:
            for new_fact_id in self.facts[fact_id][2]:
                if new_fact_id not in goal_related_premise_ids:
                    goal_related_premise_ids.append(new_fact_id)
        goal_related_premise_ids = set(goal_related_premise_ids)
        edges = set()
        for fact_id in range(len(self.facts)):
            predicate, instance, premise_ids, entity_ids, operation_id = self.facts[fact_id]
            name = f'fact_{fact_id}'
            label = _anti_parse_fact((predicate, instance))
            if fact_id in goal_related_premise_ids:
                fillcolor = 'lightgreen'
            else:
                fillcolor = 'lightgrey'
            forward_graph.node(name=name, label=label,
                               shape='rectangle', style='filled', color='black', fillcolor=fillcolor)
            if len(premise_ids) > 0:
                edge_name = f'operation_{operation_id}'
                edge_label = _anti_parse_operation(self.operations[operation_id])
                if edge_label.startswith('Construct'):
                    fillcolor = 'lightyellow'
                else:
                    fillcolor = 'lightblue'
                forward_graph.node(name=edge_name, label=edge_label,
                                   style='filled', color='black', fillcolor=fillcolor)
                for premise_id in premise_ids:
                    edges.add((f'fact_{premise_id}', edge_name))
                edges.add((edge_name, name))
        for tail, head in edges:
            forward_graph.edge(tail, head, dir='forward')

        forward_graph.render(save_path + f'{filename}_forward', view=False, cleanup=True, format=file_format)

        backward_graph = Graph()
        backward_graph.attr(compound='true')
        for goal_id in range(len(self.goals)):
            goal = Graph(f'cluster_goal_{goal_id}')
            goal.attr(style='solid', color='black')

            sub_goal_id_tree, operation_id, root_sub_goal_id = self.goals[goal_id]
            sub_goals = [(sub_goal_id_tree, None)]  # [(sub_goal_id_tree, root_name)]
            operator_id_count = 0
            first_sub_goal_name = None
            while len(sub_goals) > 0:
                sub_goal_id_tree, root_name = sub_goals.pop()

                if _is_negation(sub_goal_id_tree):
                    name = f'operator_{goal_id}_{operator_id_count}'
                    operator_id_count += 1
                    goal.node(name=name, label='~', shape='circle', style='filled', color='black')
                    sub_goals.append((sub_goal_id_tree[1], name))

                elif _is_conjunction(sub_goal_id_tree) or _is_disjunction(sub_goal_id_tree):
                    name = f'operator_{goal_id}_{operator_id_count}'
                    operator_id_count += 1
                    goal.node(name=name, label=sub_goal_id_tree[1], shape='circle', color='black')
                    sub_goals.append((sub_goal_id_tree[0], name))
                    sub_goals.append((sub_goal_id_tree[2], name))

                else:
                    name = f'sub_goal_{goal_id}_{sub_goal_id_tree}'
                    predicate, instance, _ = self.sub_goals[sub_goal_id_tree]
                    if self.status_of_sub_goal[sub_goal_id_tree] == 0:
                        fillcolor = 'lightgrey'
                    elif self.status_of_sub_goal[sub_goal_id_tree] == -1:
                        fillcolor = 'lightcoral'
                    else:
                        fillcolor = 'lightgreen'
                    goal.node(name=name, label=_anti_parse_fact((predicate, instance)),
                              shape='rectangle', style='filled', color='black', fillcolor=fillcolor)

                if first_sub_goal_name is None:
                    first_sub_goal_name = name

                if root_name is not None:
                    goal.edge(root_name, name)

            backward_graph.subgraph(goal)
            if root_sub_goal_id is not None:
                _, _, root_goal_id = self.sub_goals[root_sub_goal_id]
                edge_name = f'edge_{root_sub_goal_id}_{goal_id}'
                backward_graph.node(name=edge_name, label=_anti_parse_operation(self.operations[operation_id]),
                                    style='filled', color='black', fillcolor='lightblue')

                root_name = f'sub_goal_{root_goal_id}_{root_sub_goal_id}'
                backward_graph.edge(root_name, edge_name, dir='forward')
                backward_graph.edge(edge_name, first_sub_goal_name, dir='forward')

        backward_graph.render(save_path + f'{filename}_backward', view=False, cleanup=True, format=file_format)

    """↑-------------Outputs--------------↑"""
