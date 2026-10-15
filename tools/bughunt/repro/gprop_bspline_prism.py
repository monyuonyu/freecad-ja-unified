# SPDX-License-Identifier: LGPL-2.1-or-later
# OCC GProp gives a wrong volume/area for a prism on a closed periodic BSpline profile
# (EngineBlock example, solid of a Pad). Same with OCC 7.8.1 (FreeCAD 1.1.3) and 8.0.1.
# BRepGProp::VolumeProperties: 58% of the true volume; with eps=1e-6 also wrong;
# VolumePropertiesGK is right. A mesh and a Monte Carlo isInside() agree with GK.
#   FreeCADCmd gprop_bspline_prism.py
import os

import FreeCAD as App
import Part

e = Part.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), "engineblock_profile.brep")).Edges[0]
c = e.Curve
pts = c.discretize(20000)
area = 0.5 * abs(sum(pts[i].x * pts[i - 1].y - pts[i - 1].x * pts[i].y for i in range(len(pts))))
face = Part.Face(Part.Wire(e))
prism = face.extrude(App.Vector(0, 0, 110))
print("OCC", Part.OCC_VERSION)
print("face area  %.1f  (polygon %.1f)" % (face.Area, area))
print("prism vol  %.1f  (expected %.1f)" % (prism.Volume, area * 110))
print("side area  %.1f  (expected %.1f)" % (e.extrude(App.Vector(0, 0, 110)).Area, c.length() * 110))
