import time
import copy
import warnings
from itertools import combinations
from sympy.parsing import parse_expr
from sympy import symbols
from formalgeo import CDLParser
from formalgeo import rough_equal
from formalgeo import EquationKiller as EqKiller


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
        :param theorem: <str>, theorem of condition.
        :return added: <bool>, indicate whether the addition was successful.
        :return _id: <int>, id of condition, if not added, return None.
        """

        if not self.has(predicate, item):
            self.items.append((predicate, item, tuple(sorted(list(set(premise)))), theorem, self.step_count))
            self.items_group[predicate].append(item)
            self.ids_of_predicate[predicate].append(self.id_count)
            self.ids_of_step[self.step_count].append(self.id_count)

            if predicate == "Equation" and theorem != "solve_eq":
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
            self.item = CDLParser.get_expr_from_tree(problem, goal_CDL["item"][1])
            self.answer = parse_expr(goal_CDL["answer"])
        elif goal_CDL["type"] == "equal":
            self.type = "algebra"
            self.item = CDLParser.get_equation_from_tree(problem, goal_CDL["item"][1])
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


class Problem:
    def __init__(self):
        """Problem conditions, goal, and solving message."""
        self.predicate_GDL = None
        self.problem_CDL = None
        self.condition = None  # <Condition>, all conditions of current problem.
        self.goal = None  # <Goal>, problem goal.
        self.timing = {}  # <dict>, {step: (theorem, timing)}, such as {0: ('init_problem', 0.00325)}.

    def load_problem_by_fl(self, predicate_GDL, problem_CDL):
        """Load problem through problem CDL."""
        self.predicate_GDL = predicate_GDL  # gdl
        self.problem_CDL = problem_CDL  # cdl
        fix_length_predicates = list(self.predicate_GDL["FixLength"])
        fix_length_predicates += list(self.predicate_GDL["Entity"])
        fix_length_predicates += list(self.predicate_GDL["Relation"])
        variable_length_predicates = list(self.predicate_GDL["VariableLength"])
        self.condition = Condition()
        self.condition.init_by_fl(fix_length_predicates, variable_length_predicates)

        self._construction_init()  # start construction

        for predicate, item in problem_CDL["parsed_cdl"]["text_and_image_cdl"]:  # conditions of text_and_image
            if predicate == "Equal":
                self.add("Equation", CDLParser.get_equation_from_tree(self, item), (-1,), "prerequisite")
            elif predicate == "Equation":
                self.add("Equation", CDLParser.parse_expr(self, item), (-1,), "prerequisite")
            else:
                self.add(predicate, tuple(item), (-1,), "prerequisite")

        self.goal = Goal()  # set goal
        self.goal.init_by_fl(self, problem_CDL["parsed_cdl"]["goal"])

    def load_problem_by_copy(self, problem):
        """Load problem through copying existing problem."""
        self.predicate_GDL = problem.predicate_GDL  # gdl
        self.problem_CDL = problem.problem_CDL  # cdl
        self.condition = Condition()  # copy all msg of problem
        self.condition.init_by_copy(problem.condition)
        self.timing = copy.deepcopy(problem.timing)
        self.goal = Goal()  # set goal
        self.goal.init_by_copy(problem.goal)

    def _construction_init(self):
        """
        Constructive process.
        1.Collinear expand.
        2.Cocircular expand.
        3.Shape expand. Shape(s1,s2,s3), Shape(s3,s2,s4) ==> Shape(s1,s4).
        4.Angle expand (combination).
        5.Angle expand (collinear).
        6.Angle expand (vertical angle).
        """
        # 1.Collinear expand.
        for predicate, item in self.problem_CDL["parsed_cdl"]["construction_cdl"]:  # Collinear
            if predicate != "Collinear":
                continue
            if not self.fv_check("Collinear", item):  # FV check
                w_msg = "FV check not passed: [{}, {}]".format(predicate, item)
                warnings.warn(w_msg)
                continue

            added, _id = self.condition.add(predicate, tuple(item), (-1,), "prerequisite")
            if not added:
                continue

            self.condition.add(predicate, tuple(item[::-1]), (_id,), "extended")
            self.add("Line", (item[0], item[-1]), (_id,), "extended")
            for extended_item in combinations(item, 3):  # l=3 is enough
                self.condition.add("Collinear", extended_item, (_id,), "extended")
                self.condition.add("Collinear", extended_item[::-1], (_id,), "extended")
                self.add("Angle", extended_item, (_id,), "extended")
                self.add("Angle", extended_item[::-1], (_id,), "extended")

        # 2.Cocircular expand.
        for predicate, item in self.problem_CDL["parsed_cdl"]["construction_cdl"]:  # Cocircular
            if predicate != "Cocircular":
                continue
            if not self.fv_check("Cocircular", item):  # FV check
                w_msg = "FV check not passed: [{}, {}]".format(predicate, item)
                warnings.warn(w_msg)
                continue

            added, _id = self.condition.add(predicate, tuple(item), (-1,), "prerequisite")
            if not added:
                continue

            circle = item[0]
            self.add("Circle", (circle,), (_id,), "extended")
            if len(item) == 1:
                continue

            item = item[1:]
            for com in range(1, len(item) + 1):  # extend cocircular
                for extended_item in combinations(item, com):
                    if com == 2:
                        self.condition.add("Arc", (circle, extended_item[0], extended_item[-1]), (_id,), "extended")
                        self.condition.add("Arc", (circle, extended_item[-1], extended_item[0]), (_id,), "extended")
                    cocircular = list(extended_item)
                    l = len(cocircular)
                    for bias in range(l):
                        extended_item = tuple([circle] + [cocircular[(i + bias) % l] for i in range(l)])
                        self.condition.add("Cocircular", extended_item, (_id,), "extended")

        # 3.Shape expand.
        jigsaw_unit = {}  # shape's jigsaw
        shape_unit = []  # mini shape unit
        for predicate, item in self.problem_CDL["parsed_cdl"]["construction_cdl"]:  # Shape
            if predicate != "Shape":
                continue
            if not self.fv_check("Shape", item):  # FV check
                w_msg = "FV check not passed: [{}, {}]".format(predicate, item)
                warnings.warn(w_msg)
                continue

            if len(item) == 1:  # point or line
                if len(item[0]) == 1:
                    self.add("Point", tuple(item[0]), (-1,), "prerequisite")
                else:
                    self.add("Line", tuple(item[0]), (-1,), "prerequisite")
                continue
            elif len(item) == 2 and len(item[0]) == 2 and len(item[1]) == 2:  # angle
                self.add("Angle", tuple(item[0] + item[1][1]), (-1,), "prerequisite")
                continue

            added, all_forms = self._add_shape(tuple(item), (-1,), "prerequisite")  # shape
            if not added:
                continue

            for shape in all_forms:
                jigsaw_unit[shape] = all_forms
                shape_unit.append(shape)

        shape_comb = shape_unit
        jigsaw_comb = jigsaw_unit
        while len(shape_comb):
            shape_comb_new = []
            jigsaw_comb_new = {}
            for unit in shape_unit:
                for comb in shape_comb:

                    if len(unit[-1]) != len(comb[0]):  # has same sides?
                        continue
                    elif len(unit[-1]) == 3:  # is arc and same?
                        if unit[-1] != comb[0]:
                            continue
                    else:
                        if unit[-1] != comb[0][::-1]:  # is line and same?
                            continue

                    if unit in jigsaw_comb[comb]:  # comb is combined from unit
                        continue

                    same_length = 1  # number of same sides
                    mini_length = len(unit) if len(unit) < len(comb) else len(comb)  # mini length
                    while same_length < mini_length:
                        if len(unit[- same_length - 1]) != len(comb[same_length]):  # all arcs or all lines
                            break
                        elif len(unit[- same_length - 1]) == 3:  # arc
                            if unit[- same_length - 1] != comb[same_length]:
                                break
                        else:  # line
                            if unit[- same_length - 1] != comb[same_length][::-1]:
                                break

                        same_length += 1

                    new_shape = list(unit[0:len(unit) - same_length])  # diff sides in polygon1
                    new_shape += list(comb[same_length:len(comb)])  # diff sides in polygon2

                    if not len(new_shape) == len(set(new_shape)):  # ensure no ring
                        continue

                    new_shape = tuple(new_shape)
                    if self.condition.has("Shape", new_shape):
                        continue

                    all_sides = ""
                    for item in new_shape:  # remove circle center point
                        if len(item) == 3:
                            item = item[1:]
                        all_sides += item
                    checked = True
                    for point in all_sides:
                        if all_sides.count(point) > 2:
                            checked = False
                            break
                    if not checked:  # ensure no holes
                        continue

                    premise = (self.condition.get_id_by_predicate_and_item("Shape", unit),
                               self.condition.get_id_by_predicate_and_item("Shape", comb))

                    added, all_forms = self._add_shape(new_shape, premise, "extended")  # add shape
                    if not added:  # ensure added
                        continue

                    new_shape_jigsaw = jigsaw_unit[unit] | jigsaw_comb[comb]
                    for shape in all_forms:
                        jigsaw_comb_new[shape] = new_shape_jigsaw
                        shape_comb_new.append(shape)

            shape_comb = shape_comb_new
            jigsaw_comb = jigsaw_comb_new

        # 4.Angle expand (combination).
        angle_unit = self.condition.get_items_by_predicate("Angle")
        jigsaw_unit = {}
        for angle in angle_unit:
            jigsaw_unit[angle] = {angle}

        angle_comb = angle_unit  # combination angle
        jigsaw_comb = jigsaw_unit  # angle's jigsaw
        while len(angle_comb):
            angle_comb_new = []
            jigsaw_comb_new = {}
            for unit in angle_unit:
                for comb in angle_comb:

                    if unit in jigsaw_comb[comb]:  # comb is combined from unit
                        continue

                    if not (unit[1] == comb[1] and unit[2] == comb[0] and unit[0] != comb[2]):  # ensure adjacent
                        continue

                    angles = self.condition.get_items_by_predicate("Angle")
                    if (unit[0], unit[1], comb[2]) in angles or \
                            (unit[0], comb[2], unit[1]) in angles or \
                            (comb[2], unit[0], unit[1]) in angles:
                        continue

                    new_angle = (unit[0], unit[1], comb[2])

                    if not len(new_angle) == len(set(new_angle)):  # ensure same points
                        continue

                    premise = (self.condition.get_id_by_predicate_and_item("Angle", unit),
                               self.condition.get_id_by_predicate_and_item("Angle", comb))
                    added, _ = self.condition.add("Angle", new_angle, premise, "extended")  # need to expand line
                    if not added:
                        continue

                    new_angle_jigsaw = jigsaw_unit[unit] | jigsaw_comb[comb]
                    jigsaw_comb_new[new_angle] = new_angle_jigsaw
                    angle_comb_new.append(new_angle)

            angle_comb = angle_comb_new
            jigsaw_comb = jigsaw_comb_new

        # 5.Angle collinear expand.
        for angle in self.condition.get_items_by_predicate("Angle"):
            a, v, b = angle
            a_collinear = None
            b_collinear = None
            for predicate, item in self.problem_CDL["parsed_cdl"]["construction_cdl"]:
                if predicate == "Collinear" and v in item:
                    if a in item:
                        a_collinear = item
                    if b in item:
                        b_collinear = item

            a_points = []  # Points collinear with a and on the same side with a
            b_points = []
            if a_collinear is not None:
                if a_collinear.index(v) < a_collinear.index(a):  # .....V...P..
                    i = a_collinear.index(v) + 1
                    while i < len(a_collinear):
                        a_points.append(a_collinear[i])
                        i += 1
                else:  # ...P.....V...
                    i = 0
                    while i < a_collinear.index(v):
                        a_points.append(a_collinear[i])
                        i += 1
            else:
                a_points.append(a)

            if b_collinear is not None:
                if b_collinear.index(v) < b_collinear.index(b):  # .....V...P..
                    i = b_collinear.index(v) + 1
                    while i < len(b_collinear):
                        b_points.append(b_collinear[i])
                        i += 1
                else:  # ...P.....V...
                    i = 0
                    while i < b_collinear.index(v):
                        b_points.append(b_collinear[i])
                        i += 1
            else:
                b_points.append(b)

            for a_point in a_points:
                for b_point in b_points:
                    premise = (self.condition.get_id_by_predicate_and_item("Angle", angle),)
                    self.add("Angle", (a_point, v, b_point), premise, "extended")

        # 6.Angle expand (vertical angle).
        for angle in self.condition.get_items_by_predicate("Angle"):
            premise = (self.condition.get_id_by_predicate_and_item("Angle", angle),)
            self.add("Angle", (angle[2], angle[1], angle[0]), premise, "extended")

    def _add_shape(self, shape, premise, theorem):
        """pass"""
        added, _id = self.condition.add("Shape", shape, premise, theorem)
        if not added:
            return False, None

        all_forms = [shape]
        l = len(shape)
        for bias in range(1, l):  # all forms
            new_item = tuple([shape[(i + bias) % l] for i in range(l)])
            self.condition.add("Shape", new_item, (_id,), "extended")
            all_forms.append(new_item)

        shape = list(shape)
        _, col = self.condition.get_ids_and_items_by_predicate_and_variable("Collinear", ["a", "b", "c"])
        i = 0
        has_arc = False
        while i < len(shape):
            if len(shape[i]) == 2:
                self.add("Line", (shape[i][0], shape[i][1]), (-1,), "prerequisite")
            else:
                has_arc = True
                i += 1
                continue

            j = (i + 1) % len(shape)
            if len(shape[j]) == 2:
                self.add("Angle", (shape[i][0], shape[i][1], shape[j][1]), (-1,), "prerequisite")  # extend angle
                if (shape[i][0], shape[i][1], shape[j][1]) in col:
                    shape[i] = shape[i][0] + shape[j][1]
                    shape.pop(j)
                    continue
            i += 1

        if not has_arc and len(shape) > 2:  # extend polygon
            valid = True
            i = 0
            l = len(shape)
            while valid and i < l:
                if shape[i][1] != shape[(i + 1) % l][0]:
                    valid = False
                i += 1
            if valid:
                self.add("Polygon", tuple([item[0] for item in shape]), (-1,), "prerequisite")

        return True, set(all_forms)

    def _align_angle_sym(self, angle):
        """
        Make the symbols of angles the same.
        Measure(Angle(ABC)), Measure(Angle(ABD))  ==>  m_abc,  if Collinear(BCD)
        """
        sym = symbols("ma_" + "".join(angle).lower(), positive=True)  # init sym
        self.condition.value_of_sym[sym] = None  # init symbol's value

        a, v, b = angle
        a_collinear = None
        b_collinear = None
        for predicate, item in self.problem_CDL["parsed_cdl"]["construction_cdl"]:
            if predicate == "Collinear" and v in item:
                if a in item:
                    a_collinear = item
                if b in item:
                    b_collinear = item

        a_points = []  # Points collinear with a and on the same side with a
        b_points = []
        if a_collinear is not None:
            if a_collinear.index(v) < a_collinear.index(a):  # .....V...P..
                i = a_collinear.index(v) + 1
                while i < len(a_collinear):
                    a_points.append(a_collinear[i])
                    i += 1
            else:  # ...P.....V...
                i = 0
                while i < a_collinear.index(v):
                    a_points.append(a_collinear[i])
                    i += 1
        else:
            a_points.append(a)

        if b_collinear is not None:
            if b_collinear.index(v) < b_collinear.index(b):  # .....V...P..
                i = b_collinear.index(v) + 1
                while i < len(b_collinear):
                    b_points.append(b_collinear[i])
                    i += 1
            else:  # ...P.....V...
                i = 0
                while i < b_collinear.index(v):
                    b_points.append(b_collinear[i])
                    i += 1
        else:
            b_points.append(b)

        same_angles = []  # Same angle get by collinear
        for a_point in a_points:
            for b_point in b_points:
                same_angles.append((a_point, v, b_point))

        for same_angle in same_angles:
            self.condition.sym_of_attr[("MeasureOfAngle", same_angle)] = sym
        self.condition.attr_of_sym[sym] = ("MeasureOfAngle", tuple(same_angles))

        return sym

    def add(self, predicate, item, premise, theorem, skip_check=False):
        """
        Add item to condition of specific predicate category.
        Also consider condition expansion and equation construction.
        :param predicate: Construction, Entity, Relation or Equation.
        :param item: <tuple> or equation.
        :param premise: tuple of <int>, premise of item.
        :param theorem: <str>, theorem of item.
        :param skip_check: <bool>, set to True when you are confident that the format of item must be legal.
        :return: True or False.
        """
        if not skip_check and not self.check(predicate, item, premise, theorem):
            return False

        added, _id = self.condition.add(predicate, item, premise, theorem)
        if added:
            if predicate == "Equation":  # preset Equation
                return True

            if predicate in self.predicate_GDL["BasicEntity"]:  # preset BasicEntity
                if predicate == "Line":
                    self.condition.add("Line", item[::-1], (_id,), "extended")
                    self.condition.add("Point", (item[0],), (_id,), "extended")
                    self.condition.add("Point", (item[1],), (_id,), "extended")
                elif predicate == "Arc":
                    self.condition.add("Point", (item[1],), (_id,), "extended")
                    self.condition.add("Point", (item[2],), (_id,), "extended")
                elif predicate == "Angle":
                    self.add("Line", (item[0], item[1]), (_id,), "extended", skip_check=True)
                    self.add("Line", (item[1], item[2]), (_id,), "extended", skip_check=True)
                elif predicate == "Polygon":
                    l = len(item)
                    for bias in range(1, l):  # all forms
                        new_item = tuple([item[(i + bias) % l] for i in range(l)])
                        self.condition.add("Polygon", new_item, (_id,), "extended")
                return True  # Point and Circle no need to extend

            if predicate in self.predicate_GDL["Entity"]:  # user defined Entity
                item_GDL = self.predicate_GDL["Entity"][predicate]
            else:  # user defined Relation
                item_GDL = self.predicate_GDL["Relation"][predicate]

            predicate_vars = item_GDL["vars"]
            letters = {}  # used for vars-letters replacement
            for i in range(len(predicate_vars)):
                letters[predicate_vars[i]] = item[i]

            for para_list in item_GDL["multi"]:  # multi
                self.condition.add(predicate, tuple(letters[i] for i in para_list), (_id,), "extended")

            for extended_predicate, para in item_GDL["extend"]:  # extended
                if extended_predicate == "Equal":
                    self.add("Equation", CDLParser.get_equation_from_tree(self, para, True, letters),
                             (_id,), "extended")
                else:
                    self.add(extended_predicate, tuple(letters[i] for i in para), (_id,), "extended")

            return True

        return False

    def check(self, predicate, item, premise=None, theorem=None):
        """
        EE check and FV check.
        :param predicate: Construction, Entity, Relation or Equation.
        :param item: <tuple> or equation.
        :param premise: tuple of <int>, premise of item.
        :param theorem: <str>, theorem of item.
        :return: True or False.
        """
        if predicate not in self.condition.items_group:  # predicate must be defined
            e_msg = "Predicate '{}' not defined in current predicate GDL.".format(predicate)
            raise Exception(e_msg)
        if not self.ee_check(predicate, item):  # ee check
            w_msg = "EE check not passed: [{}, {}, {}, {}]".format(predicate, item, premise, theorem)
            warnings.warn(w_msg)
            return False
        if not self.fv_check(predicate, item):  # fv check
            w_msg = "FV check not passed: [{}, {}, {}, {}]".format(predicate, item, premise, theorem)
            warnings.warn(w_msg)
            return False

        return True

    def ee_check(self, predicate, item):
        """Entity Existence check."""

        if predicate == "Equation" or predicate in self.predicate_GDL["BasicEntity"] \
                or predicate in self.predicate_GDL["Construction"]:
            return True
        elif predicate in self.predicate_GDL["Entity"]:
            item_GDL = self.predicate_GDL["Entity"][predicate]
        elif predicate in self.predicate_GDL["Relation"]:
            item_GDL = self.predicate_GDL["Relation"][predicate]
        elif predicate == "Free":
            return True
        else:
            item_GDL = self.predicate_GDL["Attribution"][predicate]

        letters = {}  # used for vars-letters replacement
        for i in range(len(item_GDL["vars"])):
            letters[item_GDL["vars"][i]] = item[i]

        for name, para in item_GDL["ee_check"]:
            if tuple(letters[i] for i in para) not in self.condition.get_items_by_predicate(name):
                return False
        return True

    def fv_check(self, predicate, item):
        """Format Validity check."""

        if predicate == "Equation":
            if item is None or item == 0:
                return False
            return True
        elif predicate in self.predicate_GDL["Construction"]:
            if predicate == "Shape":
                if len(item) != len(set(item)):  # default check 1: mutex points
                    return False
                if len(item) == 1:
                    if len(item[0]) not in [1, 2]:
                        return False
                    return True
                for shape in item:
                    if not 2 <= len(shape) <= 3 or len(shape) != len(set(shape)):
                        return False
                return True
            else:
                return len(item) == len(set(item))  # default check 1: mutex points
        elif predicate in self.predicate_GDL["BasicEntity"]:
            if len(item) != len(set(item)):  # default check 1: mutex points
                return False
            if predicate == "Point" and len(item) != 1:
                return False
            elif predicate == "Line" and len(item) != 2:
                return False
            elif predicate == "Arc" and len(item) != 3:
                return False
            elif predicate == "Angle" and len(item) != 3:
                return False
            elif predicate == "Polygon" and len(item) < 3:
                return False
            elif predicate == "Circle" and len(item) != 1:
                return False
            return True
        elif predicate in self.predicate_GDL["Entity"]:
            if len(item) != len(set(item)):  # default check 1: mutex points
                return False
            item_GDL = self.predicate_GDL["Entity"][predicate]
        elif predicate in self.predicate_GDL["Relation"]:
            item_GDL = self.predicate_GDL["Relation"][predicate]
        elif predicate == "Free":
            return True
        else:
            item_GDL = self.predicate_GDL["Attribution"][predicate]

        if len(item) != len(item_GDL["vars"]):  # default check 2: correct para len
            return False

        if "fv_check" in item_GDL:  # fv check, more stringent than default check 3
            checked = []
            result = []
            for i in item:
                if i not in checked:
                    checked.append(i)
                result.append(str(checked.index(i)))
            if "".join(result) in item_GDL["fv_check"]:
                return True
            return False

        if len(item_GDL["ee_check"]) > 1:  # default check 3: para of the same type need to be different
            predicate_to_vars = {}
            for predicate, p_var in item_GDL["ee_check"]:
                if predicate not in self.predicate_GDL["Construction"]:  # check only BasicEntity
                    if predicate not in predicate_to_vars:
                        predicate_to_vars[predicate] = [p_var]
                    else:
                        predicate_to_vars[predicate].append(p_var)

            letters = {}  # used for vars-letters replacement
            for i in range(len(item_GDL["vars"])):
                letters[item_GDL["vars"][i]] = item[i]

            for predicate in predicate_to_vars:
                if len(predicate_to_vars[predicate]) == 1:
                    continue

                mutex_sets = []  # mutex_item
                for p_var in predicate_to_vars[predicate]:
                    mutex_sets.append([letters[i] for i in p_var])

                mutex_sets_multi = []  # mutex_item multi representation
                for mutex_item in mutex_sets:
                    if predicate == "Line":
                        mutex_sets_multi.append(tuple(mutex_item))
                        mutex_sets_multi.append(tuple(mutex_item[::-1]))
                    elif predicate == "Polygon":
                        l = len(mutex_item)
                        for bias in range(0, l):
                            mutex_sets_multi.append(tuple([mutex_item[(i + bias) % l] for i in range(l)]))
                    else:  # Point Arc Angle Circle
                        mutex_sets_multi.append(tuple(mutex_item))

                if len(mutex_sets_multi) != len(set(mutex_sets_multi)):
                    return False

        return True

    def get_sym_of_attr(self, attr, item):
        """
        Get symbolic representation of item's attribution.
        :param attr: attr's name, such as LengthOfLine
        :param item: tuple, such as ('A', 'B')
        :return: sym
        """

        if attr != "Free" and attr not in self.predicate_GDL["Attribution"]:  # attr must define
            e_msg = "Attribution '{}' not defined in current predicate GDL.".format(attr)
            raise Exception(e_msg)
        if not self.ee_check(attr, item):  # ee check
            msg = "EE check not passed: [{}, {}]".format(attr, item)
            warnings.warn(msg)
            return None
        if not self.fv_check(attr, item):  # fv check
            msg = "FV check not passed: [{}, {}]".format(attr, item)
            warnings.warn(msg)
            return None

        if (attr, item) in self.condition.sym_of_attr:  # already has sym
            return self.condition.sym_of_attr[(attr, item)]

        if attr == "Free":
            sym = symbols("".join(item))
            self.condition.sym_of_attr[(attr, item)] = sym  # add sym
            self.condition.value_of_sym[sym] = None  # init symbol's value
            self.condition.attr_of_sym[sym] = (attr, (item,))  # add attr
            return sym

        if attr == "MeasureOfAngle":  # align angle's sym
            return self._align_angle_sym(item)

        attr_GDL = self.predicate_GDL["Attribution"][attr]
        if (attr, item) not in self.condition.sym_of_attr:  # No symbolic representation, initialize one.
            sym = symbols(attr_GDL["sym"] + "_" + "".join(item).lower(), positive=True)
            self.condition.sym_of_attr[(attr, item)] = sym  # add sym
            self.condition.value_of_sym[sym] = None  # init symbol's value

            extend_items = [item]

            letters = {}  # used for vars-letters replacement
            for i in range(len(attr_GDL["vars"])):
                letters[attr_GDL["vars"][i]] = item[i]

            for multi in attr_GDL["multi"]:
                extended_item = [letters[i] for i in multi]  # extend item
                self.condition.sym_of_attr[(attr, tuple(extended_item))] = sym  # multi representation
                extend_items.append(tuple(extended_item))

            self.condition.attr_of_sym[sym] = (attr, tuple(extend_items))  # add attr
            return sym

    def set_value_of_sym(self, sym, value, premise, theorem):
        """
        Set value of sym.
        Add equation to record the premise and theorem of solving the symbol's value at the same time.
        :param sym: <symbol>
        :param value: <float>
        :param premise: tuple of <int>, premise of getting value.
        :param theorem: <str>, theorem of getting value. such as 'solve_eq'.
        """

        if self.condition.value_of_sym[sym] is None:
            self.condition.value_of_sym[sym] = value
            added, _id = self.condition.add("Equation", sym - value, premise, theorem)
            return added
        return False

    def step(self, item, timing):
        """
        Execute when theorem successful applied. Save theorem and update step.
        :param item: <str>, theorem_name, 'init_problem' and 'check_goal'.
        :param timing: <float>.
        """
        self.timing[self.condition.step_count] = (item, timing)
        self.condition.step()

    def check_goal(self):
        """Check whether the solution is completed."""
        s_start_time = time.time()  # timing
        if self.goal.type == "algebra":  # algebra relation
            try:
                result, premise = EqKiller.solve_target(self.goal.item, self)
            except BaseException as e:
                msg = "Exception occur when solve target: {}".format(repr(e))
                warnings.warn(msg)
            else:
                if result is not None:
                    if rough_equal(result, self.goal.answer):
                        self.goal.solved = True
                    self.goal.solved_answer = result

                    eq = self.goal.item - result
                    if eq in self.condition.get_items_by_predicate("Equation"):
                        self.goal.premise = self.condition.get_premise_by_predicate_and_item("Equation", eq)
                        self.goal.theorem = self.condition.get_theorem_by_predicate_and_item("Equation", eq)
                    else:
                        self.goal.premise = tuple(premise)
                        self.goal.theorem = "solve_eq"
        elif self.goal.type == "logic":  # logic relation
            if self.goal.answer in self.condition.get_items_by_predicate(self.goal.item):
                self.goal.solved = True
                self.goal.solved_answer = self.goal.answer
                self.goal.premise = self.condition.get_premise_by_predicate_and_item(self.goal.item, self.goal.answer)
                self.goal.theorem = self.condition.get_theorem_by_predicate_and_item(self.goal.item, self.goal.answer)

        self.step("check_goal", time.time() - s_start_time)
