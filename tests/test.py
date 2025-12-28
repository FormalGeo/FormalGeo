from formalgeo.configuration import GeometricConfiguration
from formalgeo.tools import load_json, show_json, parse_gdl


def forward_solving():
    parsed_gdl = parse_gdl(load_json('gdl.json'))
    show_json(parsed_gdl)

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)
    gc.construct('Point(A):FreePoint(A)')
    gc.construct('Point(B):FreePoint(B)')
    gc.construct('Point(C):PointLeftSegment(C,A,B)')
    gc.construct('Line(a):PointOnLine(B,a)&PointOnLine(C,a)')
    gc.construct('Line(b):PointOnLine(A,b)&PointOnLine(C,b)')
    gc.construct('Line(c):PointOnLine(A,c)&PointOnLine(B,c)')
    gc.construct('Line(x):PointOnLine(A,x)&EqualAngle(b,x,x,c)')
    gc.construct('Line(y):PointOnLine(B,y)&EqualAngle(c,y,y,a)')
    gc.construct('Point(O):PointOnLine(O,x)&PointOnLine(O,y)')
    gc.construct('Line(z):PointOnLine(C,z)&PointOnLine(O,z)')

    gc.set_goal('AngleBisector(C,z,a,b)')

    gc.apply()


def backward_solving():
    parsed_gdl = parse_gdl(load_json('gdl.json'))
    show_json(parsed_gdl)

    gc = GeometricConfiguration(parsed_gdl=parsed_gdl)
    gc.construct('Point(A):FreePoint(A)')
    gc.construct('Point(B):FreePoint(B)')
    gc.construct('Point(C):PointLeftSegment(C,A,B)')
    gc.construct('Line(a):PointOnLine(B,a)&PointOnLine(C,a)')
    gc.construct('Line(b):PointOnLine(A,b)&PointOnLine(C,b)')
    gc.construct('Line(c):PointOnLine(A,c)&PointOnLine(B,c)')
    gc.construct('Line(x):PointOnLine(A,x)&EqualAngle(b,x,x,c)')
    gc.construct('Line(y):PointOnLine(B,y)&EqualAngle(c,y,y,a)')
    gc.construct('Point(O):PointOnLine(O,x)&PointOnLine(O,y)')
    gc.construct('Line(z):PointOnLine(C,z)&PointOnLine(O,z)')

    gc.set_goal('AngleBisector(C,z,a,b)')

    gc.decompose()


if __name__ == '__main__':
    forward_solving()
    # backward_solving()
