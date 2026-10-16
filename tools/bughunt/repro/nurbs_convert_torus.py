# SPDX-License-Identifier: LGPL-2.1-or-later
# OCC: BRepBuilderAPI_NurbsConvert (Shape.toNurbs) fails with Convert_TorusToBSplineSurface on a
# valid torus face of OCC's own bottle (data/occ/bottle.brep: the fillet at the neck, R 7.5,
# r 0.6, U the full turn, V pi/2..pi). Its U range from the pcurves is 2*pi + 3.6e-15.
# Same with OCC 7.8.1 (FreeCAD 1.1.3) and 8.0.1. A face made from the same torus with
# Part.Toroid().toShape(0, 2*pi + 4e-15, pi/2, pi) converts fine.
#   FreeCADCmd nurbs_convert_torus.py
import math
import os

import Part

f = Part.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bottle_torus_face.brep"))
u0, u1, v0, v1 = f.Faces[0].ParameterRange
print("OCC", Part.OCC_VERSION, "valid", f.isValid(), "U range - 2pi = %.3g" % (u1 - u0 - 2 * math.pi))
try:
    f.toNurbs()
    print("toNurbs ok")
except Exception as e:
    print("toNurbs failed:", e)
