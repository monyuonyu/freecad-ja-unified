# P4「候補の規則を表に・数値欄」の受け入れ: 面・2 つの面・図面の円・STL・DXF の線を選んだときに横の候補が出ること、
# 面を選んで数字を打って Enter で押し出し（パネルを開かずに）ができることを GUI の中で確かめて画面を撮る。
# 使い方: guictl start --fresh → guictl py "exec(open('p4_walkthrough.py').read())"（OUT は P4_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P4_OUT", "/tmp/p4-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
mw = Gui.getMainWindow()
QtTest = __import__("PySide6.QtTest", fromlist=["QTest"]).QTest


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(900)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def bar():
    return mw.findChild(QtWidgets.QFrame, "UnifiedContextBar")


def bar_labels():
    b = bar()
    if b is None or not b.isVisible():
        return []
    return [t.text() for t in b.findChildren(QtWidgets.QToolButton) if t.isVisible()]


def gl_widget():
    sub = mw.findChild(QtWidgets.QMdiArea).activeSubWindow()
    for w in sub.widget().findChildren(QtWidgets.QWidget):
        if "OpenGL" in type(w).__name__ or type(w).__name__.startswith("Quarter") or "GLWidget" in type(w).__name__:
            if w.isVisible():
                return w
    return sub.widget()


def click_at(point, ctrl=False):
    """A real click in the 3D view at the model point (as the user clicks)"""
    view = Gui.ActiveDocument.ActiveView
    x, y = view.getPointOnViewport(App.Vector(*point))
    gl = gl_widget()
    ratio = gl.devicePixelRatioF() if hasattr(gl, "devicePixelRatioF") else 1.0
    pos = QtCore.QPoint(int(x / ratio), int(gl.height() - y / ratio))
    g = gl.mapToGlobal(pos)
    # Through the X server (xdotool), as Coin's view takes the window system's events
    import subprocess

    cmd = ["xdotool", "mousemove", str(g.x()), str(g.y())]
    cmd += ["keydown", "ctrl", "click", "1", "keyup", "ctrl"] if ctrl else ["click", "1"]
    subprocess.run(cmd, check=False)
    pump(900)


def pick(doc, obj, sub, point=(0, 0, 0)):
    Gui.Selection.clearSelection()
    pump(100)
    click_at(point)


def check(name, fn):
    try:
        results[name] = fn()
    except Exception:
        results[name] = {"ok": False, "error": traceback.format_exc()[-1500:]}


# 1. 部品の平らな面 → 先頭が押し出し・数値欄。数字を打って Enter でパネルを開かずに押し出す
def face_number():
    doc = App.newDocument("板")
    body = doc.addObject("PartDesign::Body", "Body")
    box = doc.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length, box.Width, box.Height = 80, 50, 5
    doc.recompute()
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    top = [i for i, f in enumerate(box.Shape.Faces, 1) if abs(f.Surface.Axis.z) > 0.99 and f.CenterOfMass.z > 4][0]
    pick(doc, box, "Face%d" % top, (40, 25, 5))
    labels = bar_labels()
    field = bar().findChild(QtWidgets.QLineEdit, "UnifiedContextField")
    shot("p4-01-face-bar-field")
    field.setFocus()
    field.setText("12")
    QtTest.keyClick(field, QtCore.Qt.Key_Return)
    pump(2500)
    pads = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    panel_open = bool(Gui.Control.activeDialog())
    shot("p4-02-padded-by-number")
    length = pads[0].Length.Value if pads else None
    return {"ok": bool(labels) and field is not None and length == 12.0 and not panel_open,
            "bar": labels, "pad_length": length, "panel_left_open": panel_open}


check("face_number_enter", face_number)


# 2. 別の部品の 2 つの面（Ctrl） → くっつける など
def two_faces():
    doc = App.ActiveDocument
    b1 = doc.addObject("Part::Box", "Base")
    b2 = doc.addObject("Part::Cylinder", "Pin")
    b2.Placement.Base = App.Vector(100, 0, 0)
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.Selection.clearSelection()
    pump(200)
    click_at((100, 0, 10))  # the top of the pin
    click_at((5, 5, 10), ctrl=True)  # the top of the base
    pump(500)
    picked = [(s.ObjectName, s.SubElementNames) for s in Gui.Selection.getSelectionEx()]
    labels = bar_labels()
    shot("p4-03-two-faces")
    return {"ok": len(labels) >= 2, "bar": labels, "picked": picked}


check("two_faces", two_faces)


# 3. 読み込んだ STL（メッシュ） → 調べて直す・立体にする
def mesh():
    import Mesh

    doc = App.newDocument("stl")
    m = doc.addObject("Mesh::Feature", "Bracket")
    m.Mesh = Mesh.createBox(20, 10, 5)
    doc.recompute()
    pump(500)
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    pump(1000)
    # The middle of the view (the mesh fills it after "fit all")
    Gui.Selection.clearSelection()
    gl = gl_widget()
    g = gl.mapToGlobal(QtCore.QPoint(gl.width() // 2, gl.height() // 2))
    import subprocess

    subprocess.run(["xdotool", "mousemove", str(g.x()), str(g.y()), "click", "1"], check=False)
    pump(900)
    labels = bar_labels()
    shot("p4-04-stl-bar")
    return {"ok": len(labels) >= 3, "bar": labels}


check("stl", mesh)


# 4. DXF の線 → 輪郭を押し出す・スケッチにする
def dxf():
    doc = App.newDocument("dxf")
    for i, (a, b) in enumerate((((0, 0), (80, 0)), ((80, 0), (80, 50)), ((80, 50), (0, 50)), ((0, 50), (0, 0)))):
        o = doc.addObject("Part::Feature", "Shape%03d" % i)
        o.Shape = Part.makeLine(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0))
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")
    pick(doc, doc.getObject("Shape000"), "Edge1", (40, 0, 0))
    labels = bar_labels()
    picked = [(s.ObjectName, s.SubElementNames) for s in Gui.Selection.getSelectionEx()]
    shot("p4-05-dxf-line-bar")
    return {"ok": len(labels) >= 3, "bar": labels, "picked": picked}


check("dxf_line", dxf)


# 5. 図面の円 → 直径・半径・中心線
def drawing_circle():
    doc = App.newDocument("図面")
    cyl = doc.addObject("Part::Cylinder", "Shaft")
    cyl.Radius, cyl.Height = 10, 30
    doc.recompute()
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, cyl.Name)
    Gui.runCommand("Unified_NewDrawing")
    pump(2500)
    import UnifiedChrome

    UnifiedChrome.band().finish()
    pump(2500)
    Gui.SendMsgToActiveView("ViewFit")
    views = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawViewPart") and not o.isDerivedFrom("TechDraw::DrawProjGroup")]
    target = None
    for v in views:
        for i in range(60):
            try:
                e = v.getEdgeByIndex(i)
            except Exception:
                break
            if type(e.Curve).__name__ == "Circle":
                target = (v, "Edge%d" % i)
                break
        if target:
            break
    Gui.Selection.clearSelection()
    QtGui.QCursor.setPos(mw.mapToGlobal(QtCore.QPoint(700, 450)))
    Gui.Selection.addSelection(doc.Name, target[0].Name, target[1])
    pump(800)
    labels = bar_labels()
    shot("p4-06-drawing-circle-bar")
    return {"ok": len(labels) >= 3, "bar": labels, "edge": target[1] if target else None}


check("drawing_circle", drawing_circle)

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
