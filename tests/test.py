from formalgeo.configuration import GeometricConfiguration
from formalgeo.tools import load_json, show_json, parse_gdl, debug_execute


def test1():
    parsed_gdl = parse_gdl(load_json('gdl.json'))
    show_json(parsed_gdl)
    print()

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

    debug_execute(gc.set_goal, ['AngleBisector(C,z,a,b)'])

    debug_execute(gc.decompose, ['angle_bisector_determination_distance_equal'])
    debug_execute(gc.decompose, ['angle_bisector_property_distance_equal'])
    debug_execute(gc.apply, ['equal_angle_property_algebraic'])
    debug_execute(gc.apply, ['angle_bisector_determination_angle_equal'])

    gc.show_gc()
    gc.draw_gc()
    gc.draw_sg()
    print(gc.get_gc())


def test2():
    parsed_gdl = parse_gdl(load_json('gdl.json'))

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)
    gc.construct('Point(A)&Point(B):FreePoint(A)&FreePoint(B)', debug=True)
    gc.construct('Point(C):PointLeftSegment(C,A,B)', debug=True)
    gc.construct('Circle(Ω):PointOnCircle(A,Ω)&PointOnCircle(B,Ω)&PointOnCircle(C,Ω)', debug=True)
    gc.construct('Line(a):PointOnLine(A,a)&PointOnLine(B,a)', debug=True)
    gc.construct('Line(b):PointOnLine(B,b)&PointOnLine(C,b)', debug=True)
    gc.construct('Line(c):PointOnLine(C,c)&ParallelBetweenLine(c,a)', debug=True)
    gc.construct('Line(d):PointOnLine(A,d)&ParallelBetweenLine(b,d)', debug=True)
    gc.construct('Point(D):PointOnLine(D,d)&PointOnLine(D,c)', debug=True)
    gc.construct('Line(l):PointOnLine(A,l)&PointOnLine(C,l)', debug=True)

    gc.set_goal('EqualDistance(A,B,D,C)&EqualDistance(A,D,B,C)', debug=True)

    gc.apply('parallel_property_angle_equal', debug=True)
    gc.apply('adjacent_supplementary_angle', debug=True)
    gc.apply('congruent_triangle_determination_asa', debug=True)
    gc.apply('congruent_triangle_property_multiple_forms', debug=True)
    # gc.apply('congruent_triangle_property_line_equal', debug=True)

    gc.show_gc()
    gc.draw_gc()
    # gc.draw_sg()
    # print(gc.get_gc())


if __name__ == '__main__':
    test1()
