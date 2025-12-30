from formalgeo.configuration import GeometricConfiguration
from formalgeo.tools import load_json, show_json, parse_gdl


def solving():
    parsed_gdl = parse_gdl(load_json('gdl.json'))
    # show_json(parsed_gdl)

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)
    gc.construct('Point(A)&Point(B):FreePoint(A)&FreePoint(B)', debug=True)
    gc.construct('Point(C):PointLeftSegment(C,A,B)', debug=True)
    gc.construct('Line(a):PointOnLine(B,a)&PointOnLine(C,a)', debug=True)
    gc.construct('Line(b):PointOnLine(A,b)&PointOnLine(C,b)', debug=True)
    gc.construct('Line(c):PointOnLine(A,c)&PointOnLine(B,c)', debug=True)
    gc.construct('Line(x):PointOnLine(A,x)&EqualAngle(b,x,x,c)', debug=True)
    gc.construct('Line(y):PointOnLine(B,y)&EqualAngle(c,y,y,a)', debug=True)
    gc.construct('Point(O):PointOnLine(O,x)&PointOnLine(O,y)', debug=True)
    gc.construct('Line(z):PointOnLine(C,z)&PointOnLine(O,z)', debug=True)
    gc.construct('Circle(Ω):PointOnCircle(A,Ω)&PointOnCircle(B,Ω)&PointOnCircle(C,Ω)', debug=True)

    gc.set_goal('AngleBisector(C,z,a,b)', debug=True)

    gc.decompose('angle_bisector_determination_distance_equal', debug=True)

    gc.apply('equal_angle_property_algebraic', debug=True)
    gc.apply('angle_bisector_determination_angle_equal', debug=True)
    gc.apply('angle_bisector_property_distance_equal', debug=True)

    print()

    gc.show_gc()
    gc.draw_gc()


if __name__ == '__main__':
    solving()
