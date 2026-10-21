# 自動で測る・道具の下見（0.6.x）の受け入れ: 本物のマウスの出来事（xdotool）で 3D 画面の点・辺・面を
# クリック／Ctrl+クリックし、横の候補の左に測った値が出ること・右にくっつける等が並ぶこと、値のコピーと
# 「寸法を残す」、道具の列と候補のボタンに重ねたときの下見（文書を変えない・離すと消える・遅いものは出さない）を
# 確かめて画面を撮る。
# 使い方: KANTAN_GUI_DISPLAY=:193 KANTAN_GUI_STATE=/tmp/kantan-gui-mp guictl start --fresh
#         → guictl py - < measure_preview_check.py（すぐ戻る。結果は OUT/result.json と画像）
import json
import os
import subprocess
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("MP_OUT", "/tmp/measure-preview-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
mw = Gui.getMainWindow()
V = App.Vector


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


def gl_widget():
    return Gui.ActiveDocument.ActiveView.graphicsView().viewport()


def screen_of(point):
    view = Gui.ActiveDocument.ActiveView
    x, y = view.getPointOnViewport(V(*point))
    gl = gl_widget()
    ratio = gl.devicePixelRatioF() if hasattr(gl, "devicePixelRatioF") else 1.0
    g = gl.mapToGlobal(QtCore.QPoint(int(x / ratio), int(gl.height() - y / ratio)))
    return g.x(), g.y()


def click_at(point, ctrl=False):
    sx, sy = screen_of(point)
    xdo("mousemove", sx, sy)
    if ctrl:
        xdo("keydown", "ctrl", "click", "1", "keyup", "ctrl")
    else:
        xdo("click", "1")
    pump(700)


def clear():
    Gui.Selection.clearSelection()
    xdo("mousemove", 5, 500)
    pump(200)


def bar():
    return mw.findChild(QtWidgets.QFrame, "UnifiedContextBar")


def bar_state():
    b = bar()
    if b is None or not b.isVisible():
        return {"visible": False}
    values = [t.text() for t in b.findChildren(QtWidgets.QToolButton, "UnifiedMeasureValue") if t.isVisible()]
    keep = b.findChild(QtWidgets.QToolButton, "UnifiedMeasureKeep")
    actions = [
        (t.text(), t.property("unifiedCommand"), t.mapTo(b, QtCore.QPoint(0, 0)).x())
        for t in b.findChildren(QtWidgets.QToolButton)
        if t.isVisible() and t.property("unifiedCommand")
    ]
    box = b.findChild(QtWidgets.QWidget, "UnifiedMeasure")
    right_of_measure = box is None or all(x > box.geometry().right() for _, _, x in actions)
    return {
        "visible": True,
        "values": values,
        "keep": keep is not None and keep.isVisible(),
        "actions": [a[:2] for a in actions],
        "measure_left_actions_right": right_of_measure,
    }


def button_center(w):
    p = w.mapToGlobal(w.rect().center())
    return p.x(), p.y()


def strip_button(command):
    for tb in mw.findChildren(QtWidgets.QToolBar):
        if tb.objectName() in ("Unified Tools", "Unified Model") and tb.isVisible():
            for b in tb.findChildren(QtWidgets.QToolButton):
                a = b.defaultAction()
                if a is not None and a.objectName() == command and b.isVisible():
                    return b
    return None


def bar_button(command):
    b = bar()
    for t in b.findChildren(QtWidgets.QToolButton) if b else []:
        if t.property("unifiedCommand") == command and t.isVisible():
            return t
    return None


def doc_state(doc):
    return {
        "names": [o.Name for o in doc.Objects],
        "undo": doc.UndoCount,
        "shapes": {o.Name: o.Shape.hashCode() for o in doc.Objects if o.isDerivedFrom("Part::Feature")},
    }


def hover(widget, wait_ms=900):
    import ToolPreviewGui

    x, y = button_center(widget)
    xdo("mousemove", x, y)
    t0 = time.monotonic()
    pump(wait_ms)
    p = ToolPreviewGui.previewer()
    return {"state": p.last_state, "ghost": p.ghost.shown, "ms": int((time.monotonic() - t0) * 1000)}


def leave():
    import ToolPreviewGui

    xdo("mousemove", 800, 700)
    pump(300)
    p = ToolPreviewGui.previewer()
    return {"ghost_after_leave": p.ghost.shown}


def rectangle(sketch, x0, y0, x1, y1):
    pts = [V(x0, y0, 0), V(x1, y0, 0), V(x1, y1, 0), V(x0, y1, 0)]
    for i in range(4):
        sketch.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
    for i in range(4):
        sketch.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))


def make_scene():
    doc = App.newDocument("測る")
    body = doc.addObject("PartDesign::Body", "Body")
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]
    sk.MapMode = "FlatFace"
    rectangle(sk, 0, 0, 80, 50)
    doc.recompute()
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sk
    pad.Length = 5
    sk.Visibility = False
    doc.recompute()
    # A plate with two holes ⌀6, 60 apart
    holes = Part.makeBox(80, 30, 4, V(0, 80, 0))
    for x in (10, 70):
        holes = holes.cut(Part.makeCylinder(3, 4, V(x, 95, 0)))
    plate = doc.addObject("Part::Feature", "Holes")
    plate.Shape = holes
    # A lid in front, 10 further out (its front face is parallel to the plate's)
    lid = doc.addObject("Part::Box", "Lid")
    lid.Length, lid.Width, lid.Height = 30, 20, 10
    lid.Placement.Base = V(90, -10, 0)
    # A sketch to extrude, not used yet
    free = body.newObject("Sketcher::SketchObject", "Free")
    free.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]
    free.MapMode = "FlatFace"
    free.AttachmentOffset = App.Placement(V(0, 0, 0), App.Rotation())
    rectangle(free, 20, 15, 40, 35)
    doc.recompute()
    body.Tip = pad
    doc.recompute()
    Gui.ActiveDocument.ActiveView.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    pump(600)
    return doc


def measure_cases(doc):
    out = {}
    # 1. A corner of the plate and a corner of the lid (Ctrl): distance and ΔX ΔY ΔZ on the
    #    left, "point to point" (0.5.8) on the right
    clear()
    click_at((80, 0, 5))
    click_at((90, -10, 10), ctrl=True)
    out["two_points"] = r = bar_state()
    r["ok"] = r.get("values", [None])[0] == "距離 15 mm" and "Unified_MovePointToPoint" in [a[1] for a in r["actions"]]
    shot("01-two-points")
    # Two corners of the same plate: the same numbers, without the moving tools
    clear()
    click_at((80, 0, 5))
    click_at((0, 0, 5), ctrl=True)
    out["two_points_same_part"] = r = bar_state()
    r["ok"] = r.get("values", [None])[:2] == ["距離 80 mm", "ΔX 80 mm"]
    # 2. The plate's front face and the lid's front face: parallel, 10 apart → gap; snap on the right
    clear()
    # (away from the middle of the faces: the push/pull arrow sits there and takes a click)
    click_at((15, 0, 2.5))
    click_at((96, -10, 7), ctrl=True)
    out["parallel_faces"] = r = bar_state()
    r["ok"] = r.get("values") == ["すき間 10 mm"] and "Unified_SnapFaces" in [a[1] for a in r["actions"]] and r["measure_left_actions_right"]
    shot("02-parallel-faces-gap")
    # 3. The rims of the two holes: center distance 60, ⌀6
    clear()
    click_at((13, 95, 4))
    click_at((73, 95, 4), ctrl=True)
    out["two_holes"] = r = bar_state()
    r["ok"] = r.get("values") == ["中心間 60 mm", "⌀6 mm"]
    shot("03-two-holes-centers")
    # 4. The plate's top and the lid's side: an angle
    clear()
    click_at((20, 10, 5))
    click_at((120, -5, 8), ctrl=True)
    out["angle"] = r = bar_state()
    r["ok"] = (r.get("values") or [""])[0] == "角度 90°"
    shot("04-faces-angle")
    # 5. One edge alone: its length, small
    clear()
    click_at((40, 0, 5))
    out["one_edge"] = r = bar_state()
    r["ok"] = r.get("values") == ["長さ 80 mm"]
    shot("05-one-edge-length")
    # 6. Copy the number: click the first value
    clear()
    click_at((80, 0, 5))
    click_at((0, 0, 5), ctrl=True)
    b = bar()
    first = b.findChildren(QtWidgets.QToolButton, "UnifiedMeasureValue")[0]
    QtWidgets.QApplication.clipboard().clear()
    xdo("mousemove", *button_center(first))
    xdo("click", "1")
    pump(300)
    out["copy"] = {"clipboard": QtWidgets.QApplication.clipboard().text(), "status": mw.statusBar().currentMessage()}
    out["copy"]["ok"] = out["copy"]["clipboard"] == "80"
    # 7. Keep it: a Measure object in the document
    before = len(doc.Objects)
    keep = bar().findChild(QtWidgets.QToolButton, "UnifiedMeasureKeep")
    xdo("mousemove", *button_center(keep))
    xdo("click", "1")
    pump(800)
    measures = [o for o in doc.Objects if o.TypeId.startswith("Measure::")]
    out["keep"] = {
        "new_objects": len(doc.Objects) - before,
        "measures": [(o.TypeId, o.Label, getattr(o, "Distance", None) and o.Distance.Value) for o in measures],
        "undo_steps": doc.UndoCount,
        "button_after": keep.text(),
        "button_enabled_after": keep.isEnabled(),
    }
    out["keep"]["ok"] = len(measures) == 1 and abs(measures[0].Distance.Value - 80) < 1e-6 and not keep.isEnabled() and measures[0].Label.startswith("距離:")
    clear()
    shot("06-kept-dimension")
    return out


def preview_cases(doc):
    import ToolPreview
    import ToolPreviewGui

    out = {}
    body = doc.getObject("Body")
    # 1. An edge picked → the bar's 丸め: hover it, the corner it takes off shows in red
    clear()
    click_at((80, 25, 5))
    state0 = doc_state(doc)
    fil = bar_button("PartDesign_Fillet")
    r = hover(fil)
    r["tooltip_property"] = fil.toolTip()
    shot("10-hover-fillet-on-bar")
    r.update(leave())
    r["document_unchanged"] = doc_state(doc) == state0
    out["bar_fillet"] = r
    # 2. The same edge → 面取り on the strip
    click_at((80, 25, 5))
    b = strip_button("PartDesign_Chamfer")
    r = hover(b, 1600)  # long enough for the tooltip
    r["tooltip"] = QtWidgets.QToolTip.text() if QtWidgets.QToolTip.isVisible() else ""
    shot("11-hover-chamfer-on-strip-tooltip")
    r.update(leave())
    r["document_unchanged"] = doc_state(doc) == state0
    out["strip_chamfer"] = r
    # 3. The unused sketch → 押し出す 10 mm (green)
    clear()
    Gui.Selection.addSelection(doc.Name, "Body", "Free.")
    r = hover(strip_button("PartDesign_Pad"))
    shot("12-hover-extrude-sketch")
    r.update(leave())
    r["document_unchanged"] = doc_state(doc) == state0
    out["strip_pad"] = r
    # 4. A point on the top face → 穴 (red, ⌀6)
    clear()
    click_at((60, 25, 5))
    r = hover(strip_button("Unified_Hole"))
    shot("13-hover-hole")
    r.update(leave())
    r["document_unchanged"] = doc_state(doc) == state0
    out["strip_hole"] = r
    # 5. The pad picked → 鏡に映す / 並べる (copies of the feature)
    clear()
    Gui.Selection.addSelection(doc.Name, "Body", "Pad.")
    pump(200)
    for name, cmd in (("mirror", "PartDesign_Mirrored"), ("linear", "PartDesign_LinearPattern"), ("polar", "PartDesign_PolarPattern")):
        Gui.SendMsgToActiveView("ViewFit")
        r = hover(strip_button(cmd))
        Gui.ActiveDocument.ActiveView.fitAll()
        shot("14-hover-%s" % name)
        r.update(leave())
        r["document_unchanged"] = doc_state(doc) == state0
        out["strip_" + name] = r
    Gui.ActiveDocument.ActiveView.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    # 6. Left before 300 ms: nothing is worked out
    clear()
    click_at((80, 25, 5))
    ToolPreviewGui.previewer().last_state = None
    b = strip_button("PartDesign_Fillet")
    xdo("mousemove", *button_center(b))
    pump(120)
    xdo("mousemove", 800, 700)
    pump(500)
    out["left_early"] = {"state": ToolPreviewGui.previewer().last_state, "ghost": ToolPreviewGui.previewer().ghost.shown}
    # 7. Slow (over a second): no ghost, only the tooltip
    real = ToolPreview.PREPARE["PartDesign_Fillet"]

    def slow(command, picks, value):
        compute = real(command, picks, value)

        def later(check):
            time.sleep(1.5)
            return compute(check)

        return later

    ToolPreview.PREPARE["PartDesign_Fillet"] = slow
    try:
        r = hover(strip_button("PartDesign_Fillet"), 1900)
        r["tooltip"] = QtWidgets.QToolTip.text() if QtWidgets.QToolTip.isVisible() else ""
        shot("15-slow-only-tooltip")
        r.update(leave())
    finally:
        ToolPreview.PREPARE["PartDesign_Fillet"] = real
    out["slow"] = r
    out["document_unchanged_at_end"] = doc_state(doc) == state0
    return out


def all_ok(node):
    """Every case: a measurement case has "ok"; a preview case shows a ghost that goes away and
    leaves the document as it was"""
    bad = []
    for name, r in node.get("measure", {}).items():
        if not r.get("ok"):
            bad.append("measure." + name)
    for name, r in node.get("preview", {}).items():
        if not isinstance(r, dict):
            if r is not True:
                bad.append("preview." + name)
            continue
        if name == "left_early":
            good = r["state"] is None and not r["ghost"]
        elif name == "slow":
            good = r["state"] == "slow" and not r["ghost"] and bool(r["tooltip"])
        else:
            good = r["state"] == "done" and r["ghost"] and not r["ghost_after_leave"] and r["document_unchanged"]
        if not good:
            bad.append("preview." + name)
    return bad


def main():
    try:
        mw.showMaximized()
        pump(800)
        doc = make_scene()
        results["measure"] = measure_cases(doc)
        results["preview"] = preview_cases(doc)
    except Exception:
        results["error"] = traceback.format_exc()
    results["failed"] = all_ok(results) + (["error"] if "error" in results else [])
    results["ok"] = not results["failed"]
    json.dump(results, open(os.path.join(OUT, "result.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)


QtCore.QTimer.singleShot(0, main)
