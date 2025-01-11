import matplotlib.pyplot as plt
import numpy as np
import random
import math
from sympy import symbols, solveset, S, Eq, Ne, Lt, Gt, Le, Ge, And
from sympy import Poly
from sympy.solvers.inequalities import solve_univariate_inequality
from sympy import symbols, solveset, S, solve
from sympy.sets import Interval, Intersection
import string

# x, y = symbols('x y')

# [Gt(y - x ** 2, 0), Gt(5 - x - y, 0)]
# solutions = solveset(Gt(y - x ** 2, 0), symbol=x, domain=S.Reals)
# print(solutions)

# inequality = x**2 - 4 > 0
# solutions = solveset(inequality, x, domain=S.Reals)

# ineq1 = x + y > 1
# ineq2 = x - y < 3
# expr = And(x + y > 1, x - y < 3)
# solutions = solveset(expr, (x, y), domain=S.Reals)
# print(solutions)
#
# ineq1 = x + y > 1
# ineq2 = x - y < 2
#
# # 求解每个不等式
# sol1 = solveset(ineq1, x, domain=S.Reals)  # 对x求解第一个不等式
# sol2 = solveset(ineq2, x, domain=S.Reals)  # 对y求解第二个不等式
#
# # 通过交集求解不等式组
# # 注意: 实际情况中需要通过图像分析或数值方法进行进一步处理
# solution = Intersection(sol1, sol2)
#
# print("解集为:", solution)
# exit(0)
"""
'b' : 蓝色 (blue)
'g' : 绿色 (green)
'r' : 红色 (red)
'c' : 青色 (cyan)
'm' : 品红色 (magenta)
'y' : 黄色 (yellow)
'k' : 黑色 (black)
'w' : 白色 (white)
"""
random.seed(0)
point_names = list(string.ascii_uppercase)[::-1]


class Canvas:
    def __init__(self):
        _, self.ax = plt.subplots()
        plt.gca().set_aspect('equal', adjustable='box')  # 保证圆的比例不失真

    def set_range(self, range_x, range_y):
        self.ax.set_xlim(range_x[0], range_x[1])
        self.ax.set_ylim(range_y[0], range_y[1])

    def draw_points(self, point, color):
        self.ax.plot(point.x, point.y, color + "o")  # 'o'表示点

    def draw_line(self, start_point, end_point, color):
        self.ax.plot([start_point.x, end_point.x], [start_point.y, end_point.y], color + "-")  # '-'表示直线

    def draw_circle(self, center, radius, color):
        circle = plt.Circle((center.x, center.y), radius, color=color, fill=False)
        self.ax.add_artist(circle)


class Point:
    def __init__(self, name):
        self.name = name
        self.x, self.y = None, None
        self.sym_x, self.sym_y = symbols(f"x_{name.lower()}"), symbols(f"y_{name.lower()}")
        self.equations = []    # =
        self.inequalities = []    # > < !=

    def set_coordinate(self, coordinate):
        self.x, self.y = coordinate

    def add_equation(self, equation):
        self.equations.append(equation)

    def add_inequality(self, inequality):
        self.inequalities.append(inequality)

    def replace_sym_with_value(self, value_of_sym):
        """替换约束中已知变量为其实际值"""
        for i in range(len(self.equations)):
            self.equations[i] = self.equations[i].subs(value_of_sym)
        for i in range(len(self.inequalities)):
            self.inequalities[i] = self.inequalities[i].subs(value_of_sym)

    def show(self):
        print(f"{self.name}: ({self.x}, {self.y})")
        print(f"equations: {self.equations}")
        print(f"inequalities: {self.inequalities}")
        print()


class Problem:
    def __init__(self):
        self.points = {}
        self.lines = []
        self.circle = []
        self.value_of_sym = {}
        self.canvas = Canvas()

    def add_point(self, point, color="k"):
        if point.x is None:
            raise Exception("No x coordinate!")

        self.points[point.name] = point
        self.value_of_sym[point.sym_x] = point.x
        self.value_of_sym[point.sym_y] = point.y
        self.canvas.draw_points(point, color)

    def add_line(self, start_point, end_point, color="b"):
        self.lines.append([start_point.name, end_point.name])
        self.canvas.draw_line(start_point, end_point, color)

    def show(self):
        print("Points:")
        for point_name in self.points:
            self.points[point_name].show()
        print("Lines:")
        for line in self.lines:
            print(line)
        print()

    def get_max_range(self, r=1):
        """返回包含所有点的矩形区域大小，r是扩张系数"""
        x_min = min([point.x for point in self.points.values()])
        x_max = max([point.x for point in self.points.values()])
        x_middle = (x_max + x_min) / 2
        x_range = (x_max - x_min) / 2
        x_min = x_middle - x_range * r
        x_max = x_middle + x_range * r
        y_min = min([point.y for point in self.points.values()])
        y_max = max([point.y for point in self.points.values()])
        y_middle = (y_max + y_min) / 2
        y_range = (y_max - y_min) / 2
        y_min = y_middle - y_range * r
        y_max = y_middle + y_range * r
        return (x_min, x_max), (y_min, y_max)


def random_points_from_rectangle(n, range_x, range_y):
    """生成n个点，x范围为range_x，y范围为range_y。"""
    points = []
    for _ in range(n):
        # 生成每个点的x和y坐标
        x = random.uniform(range_x[0], range_x[1])  # 在range_x范围内生成随机数
        y = random.uniform(range_y[0], range_y[1])  # 在range_y范围内生成随机数
        points.append((x, y))  # 将生成的点添加到列表中
    return points


def solve_point_coordinate(problem, point, r=4, n=100):
    point.replace_sym_with_value(problem.value_of_sym)  # simplify
    check_points = []
    legal_points = []
    illegal_points = []

    if len(point.equations) > 0:  # solve equations
        solutions = solve(point.equations)
        if isinstance(solutions, dict):
            solutions = [solutions]
        if isinstance(solutions, list):
            for solution in solutions:
                check_points.append((solution[point.sym_x], solution[point.sym_y]))

    else:
        range_x, range_y = problem.get_max_range(r=r)
        check_points = random_points_from_rectangle(n=n, range_x=range_x, range_y=range_x)

    for random_point in check_points:
        legal = True
        value_of_sym = {point.sym_x: random_point[0], point.sym_y: random_point[1]}
        for inequality in point.inequalities:
            if inequality.subs(value_of_sym) <= 0:
                legal = False
                break
        if legal:
            legal_points.append(random_point)
        else:
            illegal_points.append(random_point)

    return legal_points, illegal_points


def random_points_from_circle(n, center, radius):
    """生成n个点，圆心为center，半径为r。"""
    points = []
    for _ in range(n):
        # 随机角度，范围[0, 2*pi)
        theta = random.uniform(0, 2 * math.pi)
        # 随机半径，范围[0, r]
        radius = random.uniform(0, radius)

        # 计算点的x, y坐标
        x = center[0] + radius * math.cos(theta)
        y = center[1] + radius * math.sin(theta)

        points.append((x, y))

    return points


def get_centroid_point(points):
    x = sum([x for x, _ in points]) / len(points)
    y = sum([y for _, y in points]) / len(points)
    min_distance = 1e5
    centroid_point = None
    for point in points:
        if (point[0] - x) ** 2 + (point[1] - y) ** 2 < min_distance:
            min_distance = (point[0] - x) ** 2 + (point[1] - y) ** 2
            centroid_point = point
    return centroid_point


def vector(a, b):
    """return vector ab"""
    return b.sym_x - a.sym_x, b.sym_y - a.sym_y


def cosine(a, c, b):
    """return cosine of 'ac' and 'ab'."""
    ac = vector(a, c)
    ab = vector(a, b)
    return ac[0] * ab[0] + ac[1] * ab[1]


def parallel(a, b, c, d):
    """ab // cd"""
    ab = vector(a, b)
    cd = vector(c, d)
    return ab[0] * cd[1] - cd[0] * ab[1]


def line(a, b, c):
    """Line AB. c is the intersection."""
    A = b.sym_y - a.sym_y
    B = a.sym_x - b.sym_x
    C = b.sym_x * a.sym_y - a.sym_x * b.sym_y
    return A * c.sym_x + B * c.sym_y + C


def cycle(step):
    random.seed(0)
    problem = Problem()
    point_a = Point("A")
    point_b = Point("B")

    coordinate_a, coordinate_b = random_points_from_rectangle(2, (0, 10), (0, 10))  # 随机点 a, b
    point_a.set_coordinate(coordinate_a)
    point_b.set_coordinate(coordinate_b)
    problem.add_point(point_a)
    if step == 1:
        plt.show()
        return
    problem.add_point(point_b)
    if step == 2:
        plt.show()
        return
    problem.add_line(point_a, point_b)
    if step == 3:
        plt.show()
        return

    point_c = Point("C")  # c
    ieq_anticlockwise = (point_b.sym_x - point_a.sym_x) * (point_c.sym_y - point_a.sym_y) - (
            point_b.sym_y - point_a.sym_y) * (point_c.sym_x - point_a.sym_x)
    point_c.add_inequality(ieq_anticlockwise)  # 点a、b的逆时针方向约束
    point_c.add_inequality(cosine(point_a, point_c, point_b))  # 锐角三角形约束
    point_c.add_inequality(cosine(point_b, point_a, point_c))  # 锐角三角形约束
    point_c.add_inequality(cosine(point_c, point_a, point_b))  # 锐角三角形约束
    legal_points, illegal_points = solve_point_coordinate(problem, point_c)  # 求得点坐标
    if step == 4:
        for point in legal_points:
            a_point = Point("Random")
            a_point.set_coordinate(point)
            problem.add_point(a_point, "g")
        for point in illegal_points:
            a_point = Point("Random")
            a_point.set_coordinate(point)
            problem.add_point(a_point, "r")
        plt.show()
        return

    centroid_point = get_centroid_point(legal_points)
    point_c.set_coordinate(centroid_point)
    problem.add_point(point_c)
    if step == 5:
        plt.show()
        return
    problem.add_line(point_b, point_c)
    if step == 6:
        plt.show()
        return

    point_d = Point("D")
    point_d.add_equation(parallel(point_a, point_d, point_b, point_c))
    point_d.add_equation(parallel(point_b, point_a, point_c, point_d))
    legal_points, illegal_points = solve_point_coordinate(problem, point_d)  # 求得点坐标
    centroid_point = get_centroid_point(legal_points)
    point_d.set_coordinate(centroid_point)
    problem.add_point(point_d)
    if step == 7:
        plt.show()
        return
    problem.add_line(point_c, point_d)
    problem.add_line(point_a, point_d)
    if step == 8:
        plt.show()
        return
    problem.add_line(point_a, point_c)
    if step == 9:
        plt.show()
        return
    problem.add_line(point_b, point_d)
    if step == 10:
        plt.show()
        return

    point_e = Point("E")
    point_e.add_equation(line(point_a, point_c, point_e))
    point_e.add_equation(line(point_b, point_d, point_e))
    legal_points, illegal_points = solve_point_coordinate(problem, point_e)
    centroid_point = get_centroid_point(legal_points)
    point_e.set_coordinate(centroid_point)
    problem.add_point(point_e)
    if step == 11:
        plt.show()
        return

    point_f = Point("F")
    point_f.add_equation(cosine(point_f, point_b, point_e))
    point_f.add_equation(parallel(point_b, point_f, point_f, point_c))
    legal_points, illegal_points = solve_point_coordinate(problem, point_f)
    centroid_point = get_centroid_point(legal_points)
    point_f.set_coordinate(centroid_point)
    problem.add_point(point_f)
    if step == 12:
        plt.show()
        return
    problem.add_line(point_e, point_f, "r")
    if step == 13:
        plt.show()
        return

    # centroid_point = get_centroid(points)
    # canvas.draw_points(centroid_point, "r")
    #
    # r = max([((centroid_point[0] - point[0]) ** 2 + (centroid_point[1] - point[1]) ** 2) ** 0.5 for point in points])
    # canvas.draw_circle(centroid_point, r, "y")


def main():
    for step in range(1, 14):
        cycle(step)
        input("continue?")


main()
