# 面を動かす（矢印のドラッグ・候補の数値欄）と形の上の寸法の受け入れ: 本物のマウスの出来事（xdotool）で
# 矢印をつかんで動かし、モデル・元に戻す・Esc・面とそろう・寸法の札の編集を確かめて、画面を撮る。
# 使い方: KANTAN_GUI_DISPLAY=:207 KANTAN_GUI_STATE=/tmp/pushpull guictl start --fresh
#         → guictl py - < pushpull_check.py（すぐ戻る。結果は OUT/result.json と画像、done ができたら終わり）
import json
import math
import os
import subprocess
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("PUSHPULL_OUT", os.path.expanduser("~/freecad-ja-unified/docs/ui-redesign/accept/pushpull"))
os.makedirs(OUT, exist_ok=True)
for name in ("result.json", "done"):
    try:
        os.unlink(os.path.join(OUT, name))
    except OSError:
        pass
results = {}
# A crash in the middle: where it was (Python's stack) goes to this file
import faulthandler  # noqa: E402

_fault_log = open(os.path.join(OUT, "crash-stack.txt"), "w")
faulthandler.enable(_fault_log)


def pump(ms=150):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(300)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def xdo(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], check=True)
    pump(40)


def view():
    return Gui.ActiveDocument.ActiveView


def viewport():
    return view().graphicsView().viewport()


def to_screen(coin_xy):
    """Coin's pixel (y up) of the 3D view to the X screen"""
    g = viewport().mapToGlobal(QtCore.QPoint(0, 0))
    h = viewport().height()
    return g.x() + int(round(coin_xy[0])), g.y() + (h - 1 - int(round(coin_xy[1])))


def screen_of(point):
    x, y = view().getPointOnViewport(App.Vector(point))
    return to_screen((x, y))


def pp():
    import PushPullGui

    return PushPullGui.manager()


def new_doc(name):
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument(name)
    pump(300)
    return doc


def plate(doc, length=5.0):
    body = doc.addObject("PartDesign::Body", "Body")
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
    sk.MapMode = "FlatFace"
    pts = [App.Vector(0, 0, 0), App.Vector(40, 0, 0), App.Vector(40, 30, 0), App.Vector(0, 30, 0)]
    for i in range(4):
        sk.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sk.addConstraint(Sketcher.Constraint("Vertical", 1))
    sk.addConstraint(Sketcher.Constraint("Vertical", 3))
    sk.addConstraint(Sketcher.Constraint("Coincident", 0, 1, -1, 1))
    sk.renameConstraint(sk.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 40)), "Width")
    sk.renameConstraint(sk.addConstraint(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, 30)), "Depth")
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sk
    pad.Length = length
    doc.recompute()
    sk.ViewObject.Visibility = False
    return body, sk, pad


def fit():
    Gui.Selection.clearSelection()
    view().setCameraType("Perspective")
    view().viewIsometric()
    view().fitAll()
    pump(500)


def face_named(shape, normal, level=None):
    n = App.Vector(normal)
    for i, f in enumerate(shape.Faces):
        if type(f.Surface).__name__ != "Plane":
            continue
        c = f.CenterOfMass
        u, v = f.Surface.parameter(c)
        if f.normalAt(u, v).dot(n) < 0.999:
            continue
        if level is not None and abs(c.dot(n) - level) > 1e-6:
            continue
        return "Face%d" % (i + 1), f
    raise AssertionError("no face {}".format(normal))


def hover(point, wait=400):
    """Move the cursor over a point of the model (a little wobble so that the view sees a move)"""
    sx, sy = screen_of(point)
    xdo("mousemove", sx + 3, sy + 3)
    xdo("mousemove", sx, sy)
    pump(wait)
    return sx, sy


def arrow_state():
    m = pp()
    a = m.arrow
    if a is None or not a.visible():
        return None
    return {"base": list(a.base), "direction": list(a.direction), "length": a.length}


def arrow_screen(along=0.7):
    """X screen pixel on the arrow's shaft, and the screen direction of the arrow (unit)"""
    a = pp().arrow
    p0 = screen_of(a.base)
    p1 = screen_of(a.base + a.direction * a.length)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1.0
    grab = (int(p0[0] + dx * along), int(p0[1] + dy * along))
    return grab, (dx / n, dy / n), n / max(a.length, 1e-9)


def drag_arrow(pixels, steps=12, shots=None, escape_at=None, shift=False):
    """Take the arrow and drag it pixels along its screen direction; returns the readout texts seen"""
    grab, (ux, uy), _px_per_mm = arrow_screen()
    xdo("mousemove", grab[0], grab[1])
    pump(200)
    seen = []
    xdo("mousedown", 1)
    if shift:
        xdo("keydown", "shift")
    for i in range(1, steps + 1):
        x = int(grab[0] + ux * pixels * i / steps)
        y = int(grab[1] + uy * pixels * i / steps)
        xdo("mousemove", x, y)
        pump(60)
        r = pp().readout
        if r is not None and r.isVisible():
            seen.append(r.text())
        if shots and i in shots:
            shot(shots[i])
        if escape_at == i:
            xdo("key", "Escape")
            pump(200)
    if shift:
        xdo("keyup", "shift")
    xdo("mouseup", 1)
    pump(500)
    return seen


def undo_count(doc):
    return doc.UndoCount


def case_pad_top():
    doc = new_doc("PushPullPad")
    body, sk, pad = plate(doc)
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1), 5)
    c = face.CenterOfMass
    hover(c + App.Vector(6, 4, 0))
    state = arrow_state()
    shot("01-hover-arrow")
    out = {"arrow_shown": state is not None}
    if state is None:
        return out
    out["arrow_on_face_center"] = (App.Vector(state["base"]) - c).Length < 1e-6
    out["arrow_points_up"] = state["direction"][2] > 0.999
    undo0 = undo_count(doc)
    seen = drag_arrow(80, shots={8: "02-drag-top-face"})
    out["readouts"] = seen[-2:]
    out["pad_length_after"] = pad.Length.Value
    out["length_grew"] = pad.Length.Value > 5.5
    out["snapped_to_round_number"] = abs(pad.Length.Value - round(pad.Length.Value)) < 1e-9
    out["no_new_feature"] = len(body.Group) == 2
    out["one_undo_step"] = undo_count(doc) == undo0 + 1
    shot("03-after-drag")
    doc.undo()
    doc.recompute()
    pump(300)
    out["undo_back_to_5"] = abs(pad.Length.Value - 5) < 1e-9
    doc.redo()
    doc.recompute()
    out["redo_again"] = abs(pad.Length.Value - out["pad_length_after"]) < 1e-9
    # push in: inward removes material
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1))
    hover(face.CenterOfMass + App.Vector(6, 4, 0))
    before = pad.Length.Value
    drag_arrow(-25)
    out["pushed_in_length"] = pad.Length.Value
    out["pushed_in_shorter"] = pad.Length.Value < before
    return out


def case_escape():
    doc = new_doc("PushPullEsc")
    body, sk, pad = plate(doc)
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1), 5)
    hover(face.CenterOfMass + App.Vector(6, 4, 0))
    names = [o.Name for o in doc.Objects]
    undo0 = undo_count(doc)
    seen = drag_arrow(70, steps=10, escape_at=6, shots={5: "04-before-escape"})
    shot("05-after-escape")
    return {
        "moved_while_dragging": any("+" in s for s in seen),
        "length_back": abs(pad.Length.Value - 5) < 1e-9,
        "same_objects": [o.Name for o in doc.Objects] == names,
        "no_undo_step": undo_count(doc) == undo0,
    }


def case_side_face():
    doc = new_doc("PushPullSide")
    body, sk, pad = plate(doc)
    fit()
    name, face = face_named(pad.Shape, (1, 0, 0), 40)
    hover(face.CenterOfMass + App.Vector(0, 3, 1))
    shown = arrow_state()
    seen = drag_arrow(60, shots={9: "06-drag-side-face"})
    return {
        "arrow_shown": shown is not None,
        "arrow_points_x": shown is not None and shown["direction"][0] > 0.999,
        "width_after": sk.getDatum("Width").Value,
        "sketch_width_changed": sk.getDatum("Width").Value > 40.5,
        "readout_names_the_sketch_dimension": any("Width" in s for s in seen),
        "no_new_feature": len(body.Group) == 2,
    }


def case_flush():
    doc = new_doc("PushPullFlush")
    body, sk, pad = plate(doc)
    block = doc.addObject("Part::Box", "Block")
    block.Length, block.Width, block.Height = 10, 30, 12
    block.Placement.Base = App.Vector(45, 0, 0)
    doc.recompute()
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1), 5)
    hover(face.CenterOfMass + App.Vector(-6, 4, 0))
    _grab, _dir, px_per_mm = arrow_screen()
    seen = drag_arrow(7 * px_per_mm + 2, steps=10, shots={10: "07-flush-with-block"})
    return {
        "pad_length_after": pad.Length.Value,
        "flush_with_the_block": abs(pad.Length.Value - 12) < 1e-9,
        "readout_says_flush": bool(seen) and ("そろう" in seen[-1] or "flush" in seen[-1]),
    }


def case_plain_solid():
    doc = new_doc("PushPullStep")
    solid = doc.addObject("Part::Feature", "Imported")
    solid.Shape = Part.makeBox(40, 30, 10).cut(Part.makeCylinder(5, 10, App.Vector(20, 15, 0)))
    doc.recompute()
    fit()
    name, face = face_named(solid.Shape, (0, 0, 1), 10)
    hover(App.Vector(8, 8, 10))
    drag_arrow(-30, shots={10: "08-push-into-imported-solid"})
    pushed = [o for o in doc.Objects if o.Name.startswith("PushPull")]
    out = {"pushpull_feature_made": len(pushed) == 1}
    if not pushed:
        return out
    pp_obj = pushed[0]
    out["distance"] = pp_obj.Distance.Value
    out["face_moved_in"] = pp_obj.Distance.Value < 0 and abs(pp_obj.Shape.BoundBox.ZMax - (10 + pp_obj.Distance.Value)) < 1e-6
    out["base_hidden"] = not solid.ViewObject.Visibility
    # the hole: its radius
    fit()
    hole_face = next(f for f in pp_obj.Shape.Faces if type(f.Surface).__name__ == "Cylinder")
    top = pp_obj.Shape.BoundBox.ZMax
    # a point on the far wall of the hole, seen from the iso view
    probe = App.Vector(20 - 5 * 0.7071, 15 + 5 * 0.7071, top - 1)
    hover(probe)
    st = arrow_state()
    out["hole_arrow_shown"] = st is not None
    if st is not None:
        out["hole_arrow_radial"] = abs(st["direction"][2]) < 1e-6
        drag_arrow(-30, shots={10: "09-hole-wider"})
        radii = [f.Surface.Radius for o in doc.Objects if o.Name.startswith("PushPull") for f in o.Shape.Faces if type(f.Surface).__name__ == "Cylinder"]
        out["hole_radii"] = radii
        out["hole_wider"] = bool(radii) and max(radii) > 5.4
    return out


def case_context_bar():
    doc = new_doc("PushPullBar")
    body, sk, pad = plate(doc)
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1), 5)
    sx, sy = screen_of(face.CenterOfMass + App.Vector(-10, -7, 0))
    xdo("mousemove", sx, sy)
    xdo("click", 1)
    pump(600)
    mw = Gui.getMainWindow()
    bar = mw.findChild(QtWidgets.QFrame, "UnifiedContextBar")
    buttons = [b.text() for b in bar.findChildren(QtWidgets.QToolButton) if b.isVisible()] if bar else []
    field = bar.findChild(QtWidgets.QLineEdit, "UnifiedContextField") if bar else None
    shot("10-context-bar-move-face")
    out = {"bar_shown": bool(bar and bar.isVisible()), "buttons": buttons, "field_shown": bool(field and field.isVisible())}
    if field is None:
        return out
    out["field_default"] = field.text()
    c = field.mapToGlobal(QtCore.QPoint(field.width() // 2, field.height() // 2))
    xdo("mousemove", c.x(), c.y())
    xdo("click", 1)
    xdo("key", "ctrl+a")
    xdo("type", "3")
    pump(200)
    out["typed_went_into_field"] = field.text() == "3"
    xdo("key", "Return")
    pump(800)
    out["pad_length_after"] = pad.Length.Value
    out["typed_3_made_it_8"] = abs(pad.Length.Value - 8) < 1e-9
    shot("11-after-typed-3")
    return out


def labels():
    vp = viewport()
    return [w for w in vp.findChildren(QtWidgets.QLabel, "UnifiedDimensionLabel") if w.isVisible()]


def case_dimension_labels():
    doc = new_doc("Dimensions")
    body, sk, pad = plate(doc)
    fit()
    name, face = face_named(pad.Shape, (0, 0, 1), 5)
    sx, sy = screen_of(face.CenterOfMass + App.Vector(-10, -7, 0))
    xdo("mousemove", sx, sy)
    xdo("click", 1)
    pump(700)
    shown = labels()
    texts = sorted(w.text() for w in shown)
    shot("12-dimension-labels")
    out = {"labels": texts, "length_label": "5 mm" in texts, "sketch_labels": "40 mm" in texts and "30 mm" in texts}
    length = next((w for w in shown if w.dim.prop == "Length" and w.dim.obj == pad), None)
    if length is None:
        return out
    # labels sit next to what they drive: the length half way up a side of the plate
    p = length.mapToGlobal(QtCore.QPoint(0, length.height() // 2))
    anchor = screen_of(length.dim.anchor)
    out["length_label_near_its_point_px"] = math.hypot(p.x() - anchor[0], p.y() - anchor[1])
    c = length.mapToGlobal(QtCore.QPoint(length.width() // 2, length.height() // 2))
    xdo("mousemove", c.x(), c.y())
    xdo("click", 1)
    pump(400)
    field = viewport().findChild(QtWidgets.QLineEdit, "UnifiedDimensionField")
    out["field_opened"] = bool(field and field.isVisible())
    shot("13-dimension-edit")
    if field is None:
        return out
    out["field_text"] = field.text()
    xdo("key", "ctrl+a")
    xdo("type", "12")
    xdo("key", "Return")
    pump(800)
    out["pad_length_after"] = pad.Length.Value
    out["edited_to_12"] = abs(pad.Length.Value - 12) < 1e-9
    out["labels_after"] = sorted(w.text() for w in labels())
    shot("14-dimension-after-edit")
    # expressions
    length = next((w for w in labels() if w.dim.prop == "Length"), None)
    if length is not None:
        c = length.mapToGlobal(QtCore.QPoint(length.width() // 2, length.height() // 2))
        xdo("mousemove", c.x(), c.y())
        xdo("click", 1)
        pump(300)
        xdo("key", "ctrl+a")
        xdo("type", "=Sketch.Constraints.Width / 4")
        xdo("key", "Return")
        pump(800)
        out["expression_length"] = pad.Length.Value
        out["expression_works"] = abs(pad.Length.Value - 10) < 1e-9
        out["expression_label"] = sorted(w.text() for w in labels())
        shot("15-dimension-expression")
    # nothing picked: no labels
    Gui.Selection.clearSelection()
    pump(400)
    out["hidden_on_deselect"] = not labels()
    shot("16-deselected")
    return out


def main():
    try:
        mw = Gui.getMainWindow()
        mw.showMaximized()
        pump(800)
        results["pad_top"] = case_pad_top()
        results["escape"] = case_escape()
        results["side_face"] = case_side_face()
        results["flush"] = case_flush()
        results["plain_solid"] = case_plain_solid()
        results["context_bar"] = case_context_bar()
        results["dimension_labels"] = case_dimension_labels()
    except Exception:
        results["error"] = traceback.format_exc()
    checks = {}
    for case, r in results.items():
        if isinstance(r, dict):
            for k, v in r.items():
                if isinstance(v, bool):
                    checks[case + "." + k] = v
    results["failed"] = [k for k, v in checks.items() if not v]
    results["passed"] = sum(1 for v in checks.values() if v)
    json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, ensure_ascii=False, default=str)
    open(os.path.join(OUT, "done"), "w").write("1")


QtCore.QTimer.singleShot(0, main)
