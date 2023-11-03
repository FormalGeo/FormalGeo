import copy
from formalgeo.parse import parse_expr, get_expr_from_tree, get_equation_from_tree


class Condition:
    def __init__(self):
        """All conditions of one problem."""
        self.id_count = 0  # <int>
        self.step_count = 0  # <int>
        self.fix_length_predicates = None  # <list> of <str>
        self.variable_length_predicates = None  # <list> of <str>

        self.items = []  # <list> of <tuple>, [(predicate, item, premise, theorem, step)]
        self.items_group = {}  # <dict>, [predicate: [item]], such as {'Angle':[('A', 'B', 'C')]}

        self.id_of_item = {}  # <dict>, {(predicate, item): id}, such as {('Angle', ('A', 'B', 'C')): 0}
        self.ids_of_predicate = {}  # <dict>, {predicate: [id]}, such as {'Angle': [0, 1, 2]}
        self.ids_of_step = {}  # <dict>, {step: [id]}, such as {0: [0, 1, 2]}

        self.sym_of_attr = {}  # <dict>, {(attr, paras): sym}, such as {('LengthOfLine', ('A', 'B')): l_ab}
        self.attr_of_sym = {}  # <dict>, {sym: (attr, (paras))}, such as {l_ab: ('LengthOfLine', (('A', 'B'),))}
        self.value_of_sym = {}  # <dict>, {sym: value}, such as {l_ab: 3}
        self.simplified_equation = {}  # <dict>, {simplified_equation: premises}, such as {a + b - 2: [1, 2, 3]}
        self.eq_solved = True  # <bool>, record whether the equation is solved

    def init_by_fl(self, fix_length_predicates, variable_length_predicates):
        """
        Initial condition by formal language.
        :param fix_length_predicates: List of predicates that has fix parameter length.
        :param variable_length_predicates: List of predicates that has variable parameter length.
        """
        self.fix_length_predicates = fix_length_predicates
        self.variable_length_predicates = variable_length_predicates
        self.ids_of_step[self.step_count] = []
        for predicate in self.fix_length_predicates + self.variable_length_predicates:
            self.items_group[predicate] = []
            self.ids_of_predicate[predicate] = []

    def init_by_copy(self, condition):
        """
        Initial condition by copy other condition.
        :param condition: <Condition>.
        """
        self.id_count = condition.id_count
        self.step_count = condition.step_count
        self.fix_length_predicates = copy.deepcopy(condition.fix_length_predicates)
        self.variable_length_predicates = copy.deepcopy(condition.variable_length_predicates)
        self.items = copy.deepcopy(condition.items)
        self.items_group = copy.deepcopy(condition.items_group)
        self.id_of_item = copy.deepcopy(condition.id_of_item)
        self.ids_of_predicate = copy.deepcopy(condition.ids_of_predicate)
        self.ids_of_step = copy.deepcopy(condition.ids_of_step)
        self.sym_of_attr = copy.deepcopy(condition.sym_of_attr)
        self.attr_of_sym = copy.deepcopy(condition.attr_of_sym)
        self.value_of_sym = copy.deepcopy(condition.value_of_sym)
        self.simplified_equation = copy.deepcopy(condition.simplified_equation)
        self.eq_solved = condition.eq_solved

    def add(self, predicate, item, premise, theorem):
        """
        Add one condition and guarantee no redundancy.
        :param predicate: <str>, predicate of condition.
        :param item: <tuple> of <str> or <equation>, body of condition, logic relation or equation.
        :param premise: <tuple> of <int>, premise of condition, no redundancy.
        :param theorem: <tuple>, (t_name, t_branch, t_para).
        :return added: <bool>, indicate whether the addition was successful.
        :return _id: <int>, id of condition, if not added, return None.
        """

        if not self.has(predicate, item):
            self.items.append((predicate, item, tuple(sorted(list(set(premise)))), theorem, self.step_count))
            self.items_group[predicate].append(item)
            self.ids_of_predicate[predicate].append(self.id_count)
            self.ids_of_step[self.step_count].append(self.id_count)

            if predicate == "Equation" and theorem[0] != "solve_eq":
                self.simplified_equation[item] = [self.id_count]
                self.eq_solved = False

            if predicate == "Equation":
                item = str(item)
            self.id_of_item[(predicate, item)] = self.id_count
            self.id_count += 1

            return True, self.id_count - 1

        return False, None

    def has(self, predicate, item):
        """
        Check if this condition exists.
        :param predicate: <str>, predicate of condition.
        :param item: <tuple> of <str> or symbols, body of condition, logic relation or equation.
        :return exist: <bool>, indicate whether the addition was successful.
        """
        if predicate == "Equation":
            return item in self.items_group["Equation"] or -item in self.items_group["Equation"]
        else:
            return item in self.items_group[predicate]

    def step(self):
        self.step_count += 1
        self.ids_of_step[self.step_count] = []

    def get_id_by_predicate_and_item(self, predicate, item):
        if predicate == "Equation":
            item = str(item)
        return self.id_of_item[(predicate, item)]

    def get_items_by_predicate(self, predicate):
        return copy.copy(self.items_group[predicate])

    def get_ids_and_items_by_predicate_and_variable(self, predicate, variable=None):
        ids = []
        items = []
        if variable is not None and predicate in self.variable_length_predicates:
            l = len(variable)
            for item in self.items_group[predicate]:
                if len(item) != l:
                    continue
                items.append(item)
                ids.append([self.id_of_item[(predicate, item)]])
        else:
            for item in self.items_group[predicate]:
                items.append(item)
                ids.append([self.id_of_item[(predicate, item)]])
        return ids, items

    def get_premise_by_predicate_and_item(self, predicate, item):
        return self.items[self.get_id_by_predicate_and_item(predicate, item)][2]

    def get_theorem_by_predicate_and_item(self, predicate, item):
        return self.items[self.get_id_by_predicate_and_item(predicate, item)][3]


class Goal:
    def __init__(self):
        """Goal of one problem."""
        self.type = None  # <str>, such as: 'algebra', 'logic'.
        self.item = None  # <equation> or predicate, such as: a - b, 'ParallelBetweenLine'
        self.answer = None  # <number> or <tuple> of <str>, such as: 0, ('A', 'B', 'C', 'D')
        self.solved = False  # <bool>
        self.solved_answer = None  # <number>, only used in 'algebra' and 'equal'
        self.premise = None  # <tuple> of <int>
        self.theorem = None  # <str>

    def init_by_fl(self, problem, goal_CDL):
        """Initial goal by formal language."""
        if goal_CDL["type"] == "value":
            self.type = "algebra"
            self.item = get_expr_from_tree(problem, goal_CDL["item"][1])
            self.answer = parse_expr(problem, goal_CDL["answer"])
        elif goal_CDL["type"] == "equal":
            self.type = "algebra"
            self.item = get_equation_from_tree(problem, goal_CDL["item"][1])
            self.answer = 0
        elif goal_CDL["type"] == "logic":
            self.type = "logic"
            self.item = goal_CDL["item"]
            self.answer = tuple(goal_CDL["answer"])

    def init_by_copy(self, goal):
        """Initial goal by copy."""
        self.type = goal.type
        self.item = goal.item
        self.answer = goal.answer
        self.solved = goal.solved
        self.solved_answer = goal.solved_answer
        self.premise = copy.copy(goal.premise)
        self.theorem = goal.theorem
