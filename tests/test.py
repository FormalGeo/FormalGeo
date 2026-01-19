from formalgeo.configuration import GeometricConfiguration
from formalgeo.tools import load_json, parse_gdl, debug_execute


def test1():
    parsed_gdl = parse_gdl(load_json('gdl.json'))

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)
    debug_execute(gc.construct, ['Point(A)&Point(B):FreePoint(A)&FreePoint(B)'])
    debug_execute(gc.construct, ['Point(C):PointLeftSegment(C,A,B)'])
    debug_execute(gc.construct, ['Line(a):PointOnLine(B,a)&PointOnLine(C,a)'])
    debug_execute(gc.construct, ['Line(b):PointOnLine(A,b)&PointOnLine(C,b)'])
    debug_execute(gc.construct, ['Line(c):PointOnLine(A,c)&PointOnLine(B,c)'])
    debug_execute(gc.construct, ['Line(x):PointOnLine(A,x)&EqualAngle(b,x,x,c)'])
    debug_execute(gc.construct, ['Line(y):PointOnLine(B,y)&EqualAngle(c,y,y,a)'])
    debug_execute(gc.construct, ['Point(O):PointOnLine(O,x)&PointOnLine(O,y)'])
    debug_execute(gc.construct, ['Line(z):PointOnLine(C,z)&PointOnLine(O,z)'])
    debug_execute(gc.construct, ['Circle(Ω):PointOnCircle(A,Ω)&PointOnCircle(B,Ω)&PointOnCircle(C,Ω)'])
    gc.draw_gc()

    debug_execute(gc.set_goal, ['AngleBisector(C,z,a,b)'])

    debug_execute(gc.decompose, ['angle_bisector_determination_distance_equal'])
    debug_execute(gc.decompose, ['equal_distance_point_to_line_determination_algebraic'])
    debug_execute(gc.decompose, ['equal_distance_point_to_line_property_algebraic'])

    debug_execute(gc.apply, ['angle_bisector_determination_angle_equal'])
    debug_execute(gc.apply, ['angle_bisector_property_distance_equal'])

    gc.show_gc()
    gc.draw_sg()
    print(gc.get_gc())


def test2():
    parsed_gdl = parse_gdl(load_json('gdl.json'))

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)

    debug_execute(gc.construct, ['Point(A)&Point(B):FreePoint(A)&FreePoint(B)'])
    debug_execute(gc.construct, ['Point(C):PointLeftSegment(C,A,B)'])
    debug_execute(gc.construct, ['Circle(Ω):PointOnCircle(A,Ω)&PointOnCircle(B,Ω)&PointOnCircle(C,Ω)'])
    debug_execute(gc.construct, ['Line(a):PointOnLine(A,a)&PointOnLine(B,a)'])
    debug_execute(gc.construct, ['Line(b):PointOnLine(B,b)&PointOnLine(C,b)'])
    debug_execute(gc.construct, ['Line(c):PointOnLine(C,c)&ParallelBetweenLine(c,a)'])
    debug_execute(gc.construct, ['Line(d):PointOnLine(A,d)&ParallelBetweenLine(b,d)'])
    debug_execute(gc.construct, ['Point(D):PointOnLine(D,d)&PointOnLine(D,c)'])
    debug_execute(gc.construct, ['Line(l):PointOnLine(A,l)&PointOnLine(C,l)'])
    gc.draw_gc()
    debug_execute(gc.set_goal, ['EqualDistancePointToPoint(A,B,C,D)&EqualDistancePointToPoint(D,A,B,C)'])
    debug_execute(gc.apply, ['parallel_property_multiple_forms'])
    debug_execute(gc.apply, ['parallel_property_angle_equal'])
    debug_execute(gc.apply, ['equal_angle_property_algebraic'])
    debug_execute(gc.apply, ['line_property_adjacent_complementary_angle'])
    debug_execute(gc.apply, ['equal_angle_determination_algebraic'])
    debug_execute(gc.apply, ['triangle_determination'])

    debug_execute(gc.decompose, ['congruent_triangle_property_line_equal'])
    debug_execute(gc.decompose, ['congruent_triangle_property_multiple_forms'])
    debug_execute(gc.decompose, ['congruent_triangle_property_multiple_forms'])
    debug_execute(gc.decompose, ['congruent_triangle_determination_asa'])
    debug_execute(gc.decompose, ['equal_distance_point_to_point_determination_algebraic'])

    gc.show_gc()
    gc.draw_sg()
    print(gc.get_gc())


def test3():
    parsed_gdl = parse_gdl(load_json('gdl.json'))

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl, random_seed=19)
    debug_execute(gc.construct, ['Circle(Γ)&Circle(Ω):IntersectBetweenCircle(Ω,Γ)&G(Sub(Γ.rc,Ω.rc))'])
    debug_execute(gc.construct, ['Point(M):CenterOfCircle(M,Ω)'])
    debug_execute(gc.construct, ['Point(N):CenterOfCircle(N,Γ)'])
    debug_execute(gc.construct, ['Point(A):PointOnCircle(A,Ω)&PointOnCircle(A,Γ)&PointLeftSegment(A,N,M)'])
    debug_execute(gc.construct, ['Point(B):PointOnCircle(B,Ω)&PointOnCircle(B,Γ)&PointLeftSegment(B,M,N)'])
    debug_execute(gc.construct, ['Line(a):PointOnLine(M,a)&PointOnLine(N,a)'])
    debug_execute(gc.construct, ['Point(C):PointOnLine(C,a)&PointOnCircle(C,Ω)&PointLeftSegment(C,A,B)'])
    debug_execute(gc.construct, ['Point(D):PointOnLine(D,a)&PointOnCircle(D,Γ)&PointLeftSegment(D,B,A)'])
    debug_execute(gc.construct, ['Line(c):PointOnLine(A,c)&PointOnLine(D,c)'])
    debug_execute(gc.construct, ['Line(d):PointOnLine(A,d)&PointOnLine(C,d)'])
    debug_execute(gc.construct, ['Point(P):CircumcenterOfTriangle(P,C,d,A,c,D,a)'])
    debug_execute(gc.construct, ['Line(p):PointOnLine(A,p)&PointOnLine(P,p)'])
    debug_execute(gc.construct, ['Point(E):PointOnLine(E,p)&PointOnCircle(E,Ω)&~SamePoint(E,A)'])
    debug_execute(gc.construct, ['Point(F):PointOnLine(F,p)&PointOnCircle(F,Γ)&~SamePoint(F,A)'])
    debug_execute(gc.construct, ['Line(n):PointOnLine(P,n)&PointOnLine(M,n)'])
    debug_execute(gc.construct, ['Line(m):PointOnLine(P,m)&PointOnLine(N,m)'])
    debug_execute(gc.construct, ['Point(H):OrthocenterOfTriangle(H,P,n,M,a,N,m)'])
    debug_execute(gc.construct, ['Line(f):PointOnLine(B,f)&PointOnLine(E,f)'])
    debug_execute(gc.construct, ['Line(e):PointOnLine(B,e)&PointOnLine(F,e)'])
    debug_execute(gc.construct, ['Circle(Φ):CircumcircleOfTriangle(Φ,B,f,E,p,F,e)'])
    debug_execute(gc.construct, ['Line(x):PointOnLine(M,x)&PointOnLine(E,x)'])  # aux
    debug_execute(gc.construct, ['Line(y):PointOnLine(N,y)&PointOnLine(F,y)'])
    debug_execute(gc.construct, ['Point(T):PointOnLine(T,x)&PointOnLine(T,y)'])
    debug_execute(gc.construct, ['Line(t):PointOnLine(H,t)&PointOnLine(T,t)'])
    debug_execute(gc.construct, ['Circle(Δ):CircumcircleOfTriangle(Δ,C,d,A,c,D,a)'])
    debug_execute(gc.construct, ['Line(g):PointOnLine(P,g)&PointOnLine(C,g)'])
    debug_execute(gc.construct, ['Line(h):PointOnLine(P,h)&PointOnLine(D,h)'])
    debug_execute(gc.construct, ['Line(i):PointOnLine(M,i)&PointOnLine(H,i)'])
    debug_execute(gc.construct, ['Line(j):PointOnLine(N,j)&PointOnLine(H,j)'])
    debug_execute(gc.construct, ['Line(k):PointOnLine(A,k)&PointOnLine(M,k)'])
    debug_execute(gc.construct, ['Line(l):PointOnLine(A,l)&PointOnLine(N,l)'])
    debug_execute(gc.construct, ['Line(u):PointOnLine(B,u)&PointOnLine(C,u)'])
    debug_execute(gc.construct, ['Line(v):PointOnLine(A,v)&PointOnLine(B,v)'])
    debug_execute(gc.construct, ['Line(w):PointOnLine(B,w)&PointOnLine(D,w)'])
    debug_execute(gc.construct, ['Point(X):PointOnLine(X,n)&PointOnLine(X,d)'])
    debug_execute(gc.construct, ['Point(Y):PointOnLine(Y,m)&PointOnLine(Y,c)'])
    debug_execute(gc.construct, ['Point(G):CenterOfCircle(G,Φ)'])
    debug_execute(gc.construct, ['Line(b):PointOnLine(T,b)&PointOnLine(G,b)'])

    gc.draw_gc(scale=3)

    debug_execute(gc.set_goal, ['ParallelBetweenLine(p,t)&TangentBetweenLineAndCircle(t,Φ)'])

    gc.show_gc()
    gc.draw_sg()


if __name__ == '__main__':
    test3()
