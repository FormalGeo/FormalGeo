from sympy import symbols


x, y, z = symbols('x y z')

eq = x * 3

expr = y + z

print(eq)
print(eq.subs(x, expr))