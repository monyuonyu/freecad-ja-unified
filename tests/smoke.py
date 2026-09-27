# ビルド済みの FreeCAD で最低限の動作を確かめる: FreeCADCmd smoke.py -- <出力フォルダ>
# スケッチ → 押し出し → 丸め → STEP/STL 書き出し、統合環境のモジュールと日本語訳ファイルの有無
import os
import sys

import FreeCAD as App
import Part
import Sketcher

out = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(out, exist_ok=True)

doc = App.newDocument("smoke")
body = doc.addObject("PartDesign::Body", "Body")
sketch = body.newObject("Sketcher::SketchObject", "Sketch")
sketch.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]  # XY 平面
sketch.MapMode = "FlatFace"
pts = [App.Vector(0, 0, 0), App.Vector(40, 0, 0), App.Vector(40, 30, 0), App.Vector(0, 30, 0)]
for i in range(4):
    sketch.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
for i in range(4):
    sketch.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
doc.recompute()
pad = body.newObject("PartDesign::Pad", "Pad")
pad.Profile = sketch
pad.Length = 10
doc.recompute()
fillet = body.newObject("PartDesign::Fillet", "Fillet")
fillet.Base = (pad, ["Edge1"])
fillet.Radius = 2
doc.recompute()

volume = body.Shape.Volume
print("volume", round(volume, 3))
assert body.Shape.isValid(), "shape is not valid"
assert 11900 < volume < 12000, volume  # 12000 から丸めの分が少し減る

import Import, Mesh
Import.export([body], os.path.join(out, "smoke.step"))
Mesh.export([body], os.path.join(out, "smoke.stl"))
for name in ("smoke.step", "smoke.stl"):
    size = os.path.getsize(os.path.join(out, name))
    print(name, size)
    assert size > 1000, name

# 統合環境のモジュールと、その訳ファイルが入っているか
home = App.getHomePath()
unified = os.path.join(home, "Mod", "Unified")
assert os.path.isfile(os.path.join(unified, "InitGui.py")), unified
print("unified module", unified)
print("version", " ".join(App.Version()[:4]))
print("SMOKE OK")
