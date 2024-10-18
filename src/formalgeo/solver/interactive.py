from formalgeo.problem import Problem
from formalgeo.core import GeometryPredicateLogicExecutor as GPLExecutor
from formalgeo.core import EquationKiller as EqKiller
from formalgeo.parse import parse_predicate_gdl, parse_theorem_gdl, parse_problem_cdl
from formalgeo.parse import get_equation_from_tree
from formalgeo.tools import rough_equal
import warnings
import time


class Interactor:

    def __init__(self, predicate_GDL, theorem_GDL):
        """
        Initialize Interactor.
        :param predicate_GDL: predicate GDL.
        :param theorem_GDL: theorem GDL.
        """
        self.parsed_predicate_GDL = parse_predicate_gdl(predicate_GDL)
        self.parsed_theorem_GDL = parse_theorem_gdl(theorem_GDL, self.parsed_predicate_GDL)
        self.problem = None

    def load_problem(self, problem_CDL):
        """Load problem through problem_CDL."""
        start_time = time.time()
        self.problem = Problem()
        self.problem.load_problem_by_fl(self.parsed_predicate_GDL,
                                        self.parsed_theorem_GDL,
                                        parse_problem_cdl(problem_CDL))  # load problem
        EqKiller.solve_equations(self.problem)  # Solve the equations after initialization
        self.problem.step(("init_problem", None, None), time.time() - start_time)  # save applied theorem and update step

    def apply_theorem(self, t_name, t_branch=None, t_para=None):
        """
        Apply a theorem and return whether it is successfully applied.
        :param t_name: <str>.
        :param t_branch: <str>.
        :param t_para: tuple of <str>.
        :return update: <bool>, Whether the question condition updated or not.
        """
        if self.problem is None:
            e_msg = "Problem not loaded. Please run <load_problem> before run <apply_theorem>."
            raise Exception(e_msg)
        if t_name not in self.parsed_theorem_GDL:
            e_msg = "Theorem {} not defined in current GDL.".format(t_name)
            raise Exception(e_msg)
        if t_name.endswith("definition"):
            e_msg = "Theorem {} only used for backward reason.".format(t_name)
            raise Exception(e_msg)
        if t_para is not None and len(t_para) != len(self.parsed_theorem_GDL[t_name]["vars"]):
            e_msg = "Theorem <{}> para length error. Expected {} but got {}.".format(
                t_name, len(self.parsed_theorem_GDL[t_name]["vars"]), t_para)
            raise Exception(e_msg)
        if t_branch is not None and t_branch not in self.parsed_theorem_GDL[t_name]["body"]:
            e_msg = "Theorem <{}> branch error. Expected {} but got {}.".format(
                t_name, self.parsed_theorem_GDL[t_name]["body"].keys(), t_branch)
            raise Exception(e_msg)

        if t_para is None and t_branch is None:
            update = self.apply_theorem_by_name(t_name)
        elif t_para is not None and t_branch is None:
            update = self.apply_theorem_by_name_and_para(t_name, t_para)
        elif t_para is None and t_branch is not None:
            update = self.apply_theorem_by_name_and_branch(t_name, t_branch)
        else:
            update = self.apply_theorem_by_name_and_para_and_branch(t_name, t_branch, t_para)

        if not update:
            w_msg = "Theorem <{},{},{}> not applied. Please check your theorem or prerequisite.".format(
                t_name, t_branch, t_para)
            warnings.warn(w_msg)

        return update

    def apply_theorem_by_name(self, t_name):
        """
        Apply a theorem with t_name.
        :param t_name: <str>.
        :return update: <bool>, Whether the problem condition updated or not.
        """
        update = False

        for branch in self.parsed_theorem_GDL[t_name]["body"]:
            timing = time.time()  # timing
            gpl = self.parsed_theorem_GDL[t_name]["body"][branch]

            conclusions = GPLExecutor.run(gpl, self.problem)  # get gpl reasoned result
            if len(conclusions) == 0:
                theorem = (t_name, branch, None)
                self.problem.step(theorem, time.time() - timing)
                continue
            avg_timing = (time.time() - timing) / len(conclusions)
            for letters, premise, conclusion in conclusions:
                t_para = [letters[i] for i in self.parsed_theorem_GDL[t_name]["vars"]]
                theorem = (t_name, branch, tuple(t_para))
                for predicate, item in conclusion:  # add conclusion
                    update = self.problem.add(predicate, item, premise, theorem) or update
                self.problem.step(theorem, avg_timing)

        timing = time.time()  # timing
        EqKiller.solve_equations(self.problem)
        self.problem.step(("solve_equations", None, None), time.time() - timing)

        return update

    def apply_theorem_by_name_and_para(self, t_name, t_para):
        """
        Apply a theorem with t_name and t_para.
        :param t_name: <str>.
        :param t_para: tuple of <str>.
        :return update: <bool>, Whether the problem condition updated or not.
        """
        update = False
        letters = {}  # used for vars-letters replacement
        for i in range(len(self.parsed_theorem_GDL[t_name]["vars"])):
            letters[self.parsed_theorem_GDL[t_name]["vars"][i]] = t_para[i]

        for branch in self.parsed_theorem_GDL[t_name]["body"]:
            timing = time.time()  # timing
            theorem = (t_name, branch, t_para)
            gpl = self.parsed_theorem_GDL[t_name]["body"][branch]
            premises = []
            passed = True

            for predicate, item in gpl["products"] + gpl["logic_constraints"]:
                oppose = False
                if "~" in predicate:
                    oppose = True
                    predicate = predicate.replace("~", "")
                item = tuple(letters[i] for i in item)
                has_item = self.problem.condition.has(predicate, item)
                if has_item:
                    premises.append(self.problem.condition.get_id_by_predicate_and_item(predicate, item))

                if (not oppose and not has_item) or (oppose and has_item):
                    passed = False
                    break

            if not passed:
                self.problem.step(theorem, time.time() - timing)
                continue

            for equal, item in gpl["algebra_constraints"]:
                oppose = False
                if "~" in equal:
                    oppose = True
                eq = get_equation_from_tree(self.problem, item, True, letters)
                solved_eq = False

                result, premise = EqKiller.solve_target(eq, self.problem)
                if result is not None and rough_equal(result, 0):
                    solved_eq = True
                premises += premise

                if (not oppose and not solved_eq) or (oppose and solved_eq):
                    passed = False
                    break

            if not passed:
                self.problem.step(theorem, time.time() - timing)
                continue

            for predicate, item in gpl["conclusions"]:
                if predicate == "Equal":  # algebra conclusion
                    eq = get_equation_from_tree(self.problem, item, True, letters)
                    update = self.problem.add("Equation", eq, premises, theorem) or update
                else:  # logic conclusion
                    item = tuple(letters[i] for i in item)
                    update = self.problem.add(predicate, item, premises, theorem) or update

            self.problem.step(theorem, time.time() - timing)

        timing = time.time()  # timing
        EqKiller.solve_equations(self.problem)
        self.problem.step(("solve_equations", None, None), time.time() - timing)

        return update

    def apply_theorem_by_name_and_branch(self, t_name, t_branch):
        """
        Apply a theorem with t_name and t_branch.
        :param t_name: <str>.
        :param t_branch: <str>.
        :return update: <bool>, Whether the question condition updated or not.
        """
        update = False

        timing = time.time()  # timing
        gpl = self.parsed_theorem_GDL[t_name]["body"][t_branch]

        conclusions = GPLExecutor.run(gpl, self.problem)  # get gpl reasoned result
        if len(conclusions) == 0:
            theorem = (t_name, t_branch, None)
            self.problem.step(theorem, time.time() - timing)
            return False
        avg_timing = (time.time() - timing) / len(conclusions)
        for letters, premise, conclusion in conclusions:
            t_para = [letters[i] for i in self.parsed_theorem_GDL[t_name]["vars"]]
            theorem = (t_name, t_branch, tuple(t_para))

            for predicate, item in conclusion:  # add conclusion
                update = self.problem.add(predicate, item, premise, theorem) or update
            self.problem.step(theorem, avg_timing)

        timing = time.time()  # timing
        EqKiller.solve_equations(self.problem)
        self.problem.step(("solve_equations", None, None), time.time() - timing)

        return update

    def apply_theorem_by_name_and_para_and_branch(self, t_name, t_branch, t_para):
        """
        Apply a theorem with t_name, t_branch and t_para.
        :param t_name: <str>.
        :param t_branch: <str>.
        :param t_para: tuple of <str>.
        :return update: <bool>, Whether the problem condition updated or not.
        """
        update = False
        timing = time.time()  # timing
        theorem = (t_name, t_branch, t_para)

        letters = {}  # used for vars-letters replacement
        for i in range(len(self.parsed_theorem_GDL[t_name]["vars"])):
            letters[self.parsed_theorem_GDL[t_name]["vars"][i]] = t_para[i]

        gpl = self.parsed_theorem_GDL[t_name]["body"][t_branch]
        premises = []

        for predicate, item in gpl["products"] + gpl["logic_constraints"]:
            oppose = False
            if "~" in predicate:
                oppose = True
                predicate = predicate.replace("~", "")
            item = tuple(letters[i] for i in item)
            has_item = self.problem.condition.has(predicate, item)
            if has_item:
                premises.append(self.problem.condition.get_id_by_predicate_and_item(predicate, item))

            if (not oppose and not has_item) or (oppose and has_item):
                self.problem.step(theorem, time.time() - timing)
                return False

        for equal, item in gpl["algebra_constraints"]:
            oppose = False
            if "~" in equal:
                oppose = True
            eq = get_equation_from_tree(self.problem, item, True, letters)
            solved_eq = False

            result, premise = EqKiller.solve_target(eq, self.problem)
            if result is not None and rough_equal(result, 0):
                solved_eq = True
            premises += premise

            if (not oppose and not solved_eq) or (oppose and solved_eq):
                self.problem.step(theorem, time.time() - timing)
                return False

        for predicate, item in gpl["conclusions"]:
            if predicate == "Equal":  # algebra conclusion
                eq = get_equation_from_tree(self.problem, item, True, letters)
                update = self.problem.add("Equation", eq, premises, theorem) or update
            else:  # logic conclusion
                item = tuple(letters[i] for i in item)
                update = self.problem.add(predicate, item, premises, theorem) or update
        self.problem.step(theorem, time.time() - timing)

        timing = time.time()  # timing
        EqKiller.solve_equations(self.problem)
        self.problem.step(("solve_equations", None, None), time.time() - timing)

        return update
