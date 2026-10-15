# SPDX-License-Identifier: LGPL-2.1-or-later
# Shape.scale (BRepBuilderAPI_Transform with a gp_Trsf scale) makes the OCC sample bottle invalid
# ("Unorientable shape" on the thread: a cylinder face over two turns, bounded by two BSpline edges; its u range moves from
# 0.1207 to 0.0964). Any factor (0.5, 1.5, 2, 3); transformShape too. Same with OCC 7.8.1.
#   BOTTLE=<occt data>/occ/bottle.brep FreeCADCmd scale_invalidates_bottle.py
import os

import Part

s = Part.read(os.environ["BOTTLE"]).Solids[0]
k = s.copy().scale(2.0)
print("valid before", s.isValid(), "after", k.isValid())
f = s.Faces[5]
print("face 5 u range", f.ParameterRange[:2], "->", f.copy().scale(2.0).ParameterRange[:2])
