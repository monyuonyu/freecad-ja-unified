# 0.7.2 の受け入れ: エンジンの実地試験（~/engine-demo/FIELD-NOTES.md）の画面の指摘を、本物のマウスとキーで再現して確かめる。
# 使い方: KANTAN_GUI_DISPLAY=:263 KANTAN_GUI_STATE=/tmp/p11gui U071_OUT=…/accept/U072 guictl start --fresh → guictl py - < u072_check.py
import os
os.environ.setdefault("U071_OUT", os.path.expanduser("~/freecad-ja-unified/docs/ui-redesign/accept/U072"))
exec(open(os.path.join(os.path.expanduser("~/freecad-ja-unified/tests/ui"), "u071_common.py")).read())

results = {}


def case_constraint_list():
    """Dimension on a circle, Esc, then a double-click on the list's last row (crashed in 0.6.9)"""
    import Sketcher

    out = {}
    close_all()
    doc = App.newDocument("拘束の一覧")
    body = doc.addObject("PartDesign::Body", "Body")
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
    sk.MapMode = "FlatFace"
    sk.addGeometry(Part.Circle(App.Vector(0, 0, 0), App.Vector(0, 0, 1), 10))
    doc.recompute()
    Gui.ActiveDocument.setEdit(sk.Name)
    pump(2000)
    # the tool first, then a click on the circle, then Esc (the tester's order)
    Gui.runCommand("Sketcher_Dimension")
    pump(800)
    view().viewTop() if hasattr(view(), "viewTop") else None
    pump(500)
    px = pick_pixel([App.Vector(10, 0, 0), App.Vector(0, 10, 0), App.Vector(-10, 0, 0)],
                    lambda i: "Edge" in i.get("Component", ""))
    out["circle_pixel"] = str(px)
    if px:
        click(*px)
        pump(800)
        shot("00-dimension-started")
    xdo("key", "Escape")
    pump(800)
    xdo("key", "Escape")
    pump(800)
    out["constraints_after_escape"] = len(sk.Constraints)
    lw = None
    for w in QtWidgets.QApplication.allWidgets():
        if w.objectName() == "listWidgetConstraints" and w.isVisible():
            lw = w
    out["list_found"] = lw is not None
    if lw is not None:
        out["rows"] = lw.count()
        if lw.count():
            item = lw.item(lw.count() - 1)
            r = lw.visualItemRect(item)
            c = lw.viewport().mapToGlobal(r.center())
            xdo("mousemove", c.x(), c.y())
            xdo("click", "--repeat", 2, "--delay", 80, 1)
            pump(1500)
            m = QtWidgets.QApplication.activeModalWidget() or QtWidgets.QApplication.activePopupWidget()
            if m is not None:
                xdo("key", "Escape")
                pump(500)
    out["still_running"] = True
    shot("01-constraint-list-after-double-click")
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    return out


def case_joint_small_hole():
    """A revolute joint without double-clicking the assembly; a click next to a small hole picks the
    hole, not the face around it (engine field test 0.6.9)"""
    import math

    out = {}
    close_all()
    doc = App.newDocument("小さな穴")
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    jg = asm.newObject("Assembly::JointGroup", "Joints")
    plate = asm.newObject("Part::Feature", "Plate")
    plate.Shape = Part.makeBox(100, 60, 15).cut(Part.makeCylinder(3, 17, App.Vector(20, 20, -1)))
    pin = asm.newObject("Part::Feature", "Pin")
    pin.Shape = Part.makeCylinder(3, 30, App.Vector(60, 30, 15))
    doc.recompute()
    import JointObject

    g = jg.newObject("App::FeaturePython", "Ground")
    JointObject.GroundedJoint(g, plate)
    doc.recompute()
    Gui.ActiveDocument.resetEdit()
    fit()
    out["assembly_not_active_before"] = Gui.ActiveDocument.getInEdit() is None
    Gui.runCommand("Assembly_CreateJointRevolute")
    pump(1500)
    out["joint_panel_opened"] = bool(Gui.Control.activeDialog())
    # 4 px outside the hole's rim, on the top face
    rim = App.Vector(23, 20, 15)
    cx, cy = view().getPointOnViewport(rim)
    away = view().getPointOnViewport(App.Vector(28, 20, 15))
    dx, dy = away[0] - cx, away[1] - cy
    n = math.hypot(dx, dy) or 1
    px = (cx + dx / n * 4, cy + dy / n * 4)
    info = view().getObjectInfo((int(px[0]), int(px[1])))
    out["under_cursor"] = info.get("Component") if info else None
    g0 = viewport().mapToGlobal(QtCore.QPoint(0, 0))
    h = viewport().height()
    click(g0.x() + int(px[0]), g0.y() + (h - 1 - int(px[1])))
    pump(1200)
    task = JointObject.activeTask
    refs = getattr(task, "refs", []) if task else []
    out["picked"] = [str(r) for r in refs]
    picked_round = False
    if refs:
        obj, subs = refs[0][0], refs[0][1]
        sub = subs[0] if subs else ""
        try:
            el = obj.getSubObject(sub)
            picked_round = type(getattr(el, "Surface", None)).__name__ == "Cylinder" or type(getattr(el, "Curve", None)).__name__ == "Circle"
        except Exception:
            pass
    out["small_hole_picked"] = picked_round
    shot("10-joint-small-hole")
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    Gui.Selection.removeSelectionGate()
    return out


def case_click_without_hover():
    """A click without the cursor first resting on the model (pen, touch, remote desktop) picks,
    and does not turn the view (engine field test 0.6.9)"""
    out = {}
    close_all()
    doc = block("ホバーなし", 80, 50, 10, save=False)
    pump(800)
    App.setActiveDocument(doc.Name)
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    pump(300)
    fit()
    pump(500)
    cam = view().getCameraOrientation()
    target = pick_pixel([App.Vector(40, 25, 10)], lambda i: i.get("Component", "").startswith("Face"))
    far = viewport().mapToGlobal(QtCore.QPoint(5, 5))
    xdo("mousemove", far.x(), far.y())
    pump(500)
    Gui.Selection.clearSelection()
    # one xdotool call: move and press at once, no time to hover
    subprocess.run(["xdotool", "mousemove", str(target[0]), str(target[1]), "click", "1"], check=True)
    pump(800)
    out["picked"] = [s for x in Gui.Selection.getSelectionEx() for s in x.SubElementNames]
    out["first_click_picks"] = bool(out["picked"])
    out["view_not_turned"] = view().getCameraOrientation().isSame(cam, 1e-9)
    shot("20-click-without-hover")
    return out


def case_digits_in_sketch():
    """Typing 1 or 3 while a sketch is drawn does not turn the view (engine field test 0.6.9)"""
    out = {}
    close_all()
    doc = App.newDocument("数字")
    pump(500)
    body = doc.addObject("PartDesign::Body", "Body")
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
    sk.MapMode = "FlatFace"
    doc.recompute()
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    Gui.ActiveDocument.setEdit(sk.Name)
    pump(2000)
    cam = view().getCameraOrientation()
    viewport().setFocus()
    c = viewport().mapToGlobal(viewport().rect().center())
    xdo("mousemove", c.x(), c.y())
    for k in ("1", "3"):
        xdo("key", k)
        pump(400)
    out["view_not_turned"] = view().getCameraOrientation().isSame(cam, 1e-9)
    shot("30-digits-in-sketch")
    Gui.ActiveDocument.resetEdit()
    pump(500)
    return out


STAGES = [("constraint_list", case_constraint_list), ("joint_small_hole", case_joint_small_hole), ("click_without_hover", case_click_without_hover), ("digits_in_sketch", case_digits_in_sketch)]
run_stages(STAGES, results)
