# P11（作り直しの残り）の受け入れ: 本物のマウスとキーの出来事（xdotool）で
#   1. 作った順の木の「ここまで有効」線（ドラッグで戻す・途中に足す・一番下へ戻す・元に戻す・右クリック「ここに差し込む」）
#   2. 道具のパネルは大事な項目だけ＋「詳しく ▸」（開いたことを道具ごとに覚える）、スケッチの寸法の欄も
#   3. 選んだ物を場所の言葉で（ステータスバー・候補の題・パネルの一覧）
#   4. 道具の名前が用語表どおり（道具の列・スケッチの帯・候補・Ctrl+K の上位）
# を確かめて画面を撮る。
# 使い方: KANTAN_GUI_DISPLAY=:263 KANTAN_GUI_STATE=/tmp/p11gui guictl start --fresh
#         → guictl py - < p11_check.py（すぐ戻る。結果は OUT/result.json と画像、done ができたら終わり）
import json
import os
import subprocess
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Sketcher
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P11_OUT", os.path.expanduser("~/freecad-ja-unified/docs/ui-redesign/accept/P11"))
os.makedirs(OUT, exist_ok=True)
for name in ("result.json", "done"):
    try:
        os.unlink(os.path.join(OUT, name))
    except OSError:
        pass
results = {}
import faulthandler  # noqa: E402

_fault_log = open(os.path.join(OUT, "crash-stack.txt"), "w")
faulthandler.enable(_fault_log)


def pump(ms=150):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name, widget=None, margin=0):
    pump(300)
    img = QtGui.QGuiApplication.primaryScreen().grabWindow(0)
    if widget is not None:
        g = widget.mapToGlobal(QtCore.QPoint(0, 0))
        img = img.copy(g.x() - margin, g.y() - margin, widget.width() + 2 * margin, widget.height() + 2 * margin)
    img.save(os.path.join(OUT, name + ".png"))


def xdo(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], check=True)
    pump(40)


def mw():
    return Gui.getMainWindow()


def status():
    """What the status bar says: its place for the element under the cursor and the picks
    (MainWindow's "actionLabel"), or a passing message over it"""
    sb = mw().statusBar()
    label = sb.findChild(QtWidgets.QLabel, "actionLabel")
    return sb.currentMessage() or (label.text() if label is not None else "")


def view():
    return Gui.ActiveDocument.ActiveView


def viewport():
    return view().graphicsView().viewport()


def to_screen(coin_xy):
    g = viewport().mapToGlobal(QtCore.QPoint(0, 0))
    h = viewport().height()
    return g.x() + int(round(coin_xy[0])), g.y() + (h - 1 - int(round(coin_xy[1])))


def screen_of(point):
    x, y = view().getPointOnViewport(App.Vector(point))
    return to_screen((x, y)), (x, y)


def new_doc(name):
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument(name)
    pump(300)
    return doc


def rectangle(sk, x0, y0, x1, y1):
    pts = [App.Vector(x0, y0, 0), App.Vector(x1, y0, 0), App.Vector(x1, y1, 0), App.Vector(x0, y1, 0)]
    first = len(sk.Geometry)
    for i in range(4):
        sk.addGeometry(Part.LineSegment(pts[i], pts[(i + 1) % 4]))
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", first + i, 2, first + (i + 1) % 4, 1))


def sketch_on(body, support, offset_z=0.0):
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = support
    sk.MapMode = "FlatFace"
    if offset_z:
        sk.AttachmentOffset = App.Placement(App.Vector(0, 0, offset_z), App.Rotation())
    return sk


def plate_with_hole(doc):
    """穴あき板: 80×50×5 の押し出し、⌀6 の穴（PartDesign の穴）"""
    body = doc.addObject("PartDesign::Body", "Body")
    sk = sketch_on(body, (body.Origin.OriginFeatures[3], [""]))
    rectangle(sk, 0, 0, 80, 50)
    sk.addConstraint(Sketcher.Constraint("Coincident", 0, 1, -1, 1))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 0))
    sk.addConstraint(Sketcher.Constraint("Horizontal", 2))
    sk.addConstraint(Sketcher.Constraint("Vertical", 1))
    sk.addConstraint(Sketcher.Constraint("Vertical", 3))
    sk.renameConstraint(sk.addConstraint(Sketcher.Constraint("DistanceX", 0, 1, 0, 2, 80)), "Width")
    sk.renameConstraint(sk.addConstraint(Sketcher.Constraint("DistanceY", 1, 1, 1, 2, 50)), "Depth")
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sk
    pad.Length = 5
    doc.recompute()
    skh = sketch_on(body, (body.Origin.OriginFeatures[3], [""]), 5)
    skh.addGeometry(Part.Circle(App.Vector(20, 20, 0), App.Vector(0, 0, 1), 2))
    hole = body.newObject("PartDesign::Hole", "Hole")
    hole.Profile = skh
    hole.Diameter = 6
    hole.DepthType = "ThroughAll"
    doc.recompute()
    for o in (sk, skh):
        o.ViewObject.Visibility = False
    return body, sk, pad, hole


def fit():
    Gui.Selection.clearSelection()
    view().viewIsometric()
    view().fitAll()
    pump(600)


def tree():
    import HistoryLineGui as H

    return [t for t in H.trees() if t.isVisible()][0]


def row_of(obj):
    import HistoryLineGui as H

    t = tree()
    for row, body in H.body_items(t, closed=True):
        idx = QtCore.QModelIndex(row)
        if body == obj:
            return idx
        for child in H.children(t, idx):
            if H.object_of(child) == obj:
                return child
    return None


def line_of(body):
    import HistoryLineGui as H

    m = H.manager()
    m.layout_lines()
    for (tid, doc, name), line in m.lines.items():
        if doc == body.Document.Name and name == body.Name:
            return line
    return None


def slot_y(body, places):
    """X screen y of the line's place after `places` steps"""
    import HistoryLineGui as H

    t = tree()
    for row, b in H.body_items(t):
        if b == body:
            for y, n in H.slots(t, row, b):
                if n == places:
                    return t.viewport().mapToGlobal(QtCore.QPoint(0, y)).y()
    return None


def drag_line(body, places):
    line = line_of(body)
    c = line.mapToGlobal(QtCore.QPoint(line.width() // 3, line.height() // 2))
    y1 = slot_y(body, places)
    xdo("mousemove", c.x(), c.y())
    pump(200)
    xdo("mousedown", 1)
    steps = 8
    for i in range(1, steps + 1):
        xdo("mousemove", c.x(), int(c.y() + (y1 - c.y()) * i / steps))
        pump(60)
    xdo("mouseup", 1)
    pump(900)


def visible_texts(widget):
    out = []
    for w in widget.findChildren(QtWidgets.QWidget):
        if not w.isVisible():
            continue
        for attr in ("text", "title", "toolTip"):
            f = getattr(w, attr, None)
            if callable(f):
                try:
                    out.append(f())
                except Exception:
                    pass
    return [t for t in out if t]


# ---------------------------------------------------------------- 1. the line


def case_history_line():
    import HistoryLine as HL

    out = {}
    doc = new_doc("HistoryLine")
    doc.UndoMode = 1
    body, sk, pad, hole = plate_with_hole(doc)
    fit()
    pump(800)
    line = line_of(body)
    out["line_shown"] = line is not None and line.isVisible()
    out["line_under_last_step"] = HL.position(body) == 2 and abs(
        line.mapToGlobal(QtCore.QPoint(0, line.height() // 2)).y() - slot_y(body, 2)
    ) <= 1
    shot("01-line-under-last-step")
    undo0 = doc.UndoCount
    drag_line(body, 1)
    out["dragged_up_tip_is_pad"] = body.Tip == pad
    out["hole_not_in_effect"] = HL.after_line(hole)
    out["shape_without_hole"] = abs(body.Shape.Volume - 80 * 50 * 5) < 1e-6
    idx = row_of(hole)
    fg = idx.data(QtCore.Qt.ForegroundRole)
    font = idx.data(QtCore.Qt.FontRole)
    tip = idx.data(QtCore.Qt.ToolTipRole) or ""
    out["hole_row_grey"] = fg is not None and QtGui.QBrush(fg).color().lightness() >= 150
    out["hole_row_italic"] = font is not None and QtGui.QFont(font).italic()
    out["hole_row_says_not_in_effect"] = "未反映" in tip
    out["one_undo_step"] = doc.UndoCount == undo0 + 1
    out["undo_name"] = doc.UndoNames[0] if doc.UndoNames else ""
    out["undo_named_in_words"] = "ここまで有効" in out["undo_name"]
    shot("02-line-dragged-up")
    # a new step goes in at the line
    top = [i for i, f in enumerate(pad.Shape.Faces) if f.Surface.__class__.__name__ == "Plane"
           and f.normalAt(0, 0).z > 0.99]
    sk2 = sketch_on(body, (pad, ["Face%d" % (top[0] + 1)]))
    rectangle(sk2, 50, 10, 70, 30)
    boss = body.newObject("PartDesign::Pad", "Pad001")
    boss.Profile = sk2
    boss.Length = 4
    doc.recompute()
    sk2.ViewObject.Visibility = False
    pump(600)
    out["new_step_at_the_line"] = HL.steps(body) == [pad, boss, hole]
    out["line_under_new_step"] = HL.position(body) == 2 and HL.after_line(hole)
    shot("03-new-step-at-the-line")
    drag_line(body, 3)
    out["back_at_bottom_all_in_effect"] = body.Tip == hole and HL.at_end(body) and not HL.not_in_effect(body)
    out["hole_and_boss_both_there"] = body.Shape.isValid() and body.Shape.Volume > 80 * 50 * 5 + 20 * 20 * 4 - 200
    shot("04-line-back-at-the-bottom")
    # Ctrl+Z / Ctrl+Y with the keyboard
    mw().activateWindow()
    viewport().setFocus()
    xdo("key", "ctrl+z")
    pump(800)
    out["ctrl_z_puts_the_line_back"] = body.Tip == boss
    xdo("key", "ctrl+shift+z")
    pump(800)
    out["ctrl_y_again"] = body.Tip == hole
    # right-click a step → 「ここに差し込む」
    seen = {}

    def pick_in_menu():
        menu = QtWidgets.QApplication.activePopupWidget()
        if not isinstance(menu, QtWidgets.QMenu):
            seen["menu"] = None
            return
        texts = [a.text().replace("&", "") for a in menu.actions()]
        seen["menu"] = texts
        shot("05-right-click-insert-here")
        for a in menu.actions():
            if a.text().replace("&", "") == "ここに差し込む":
                r = menu.actionGeometry(a)
                c = menu.mapToGlobal(r.center())
                xdo("mousemove", c.x(), c.y())
                pump(200)
                xdo("click", 1)
                return
        xdo("key", "Escape")

    t = tree()
    r = t.visualRect(row_of(pad))
    c = t.viewport().mapToGlobal(QtCore.QPoint(r.left() + 40, r.center().y()))
    xdo("mousemove", c.x(), c.y())
    xdo("click", 1)
    pump(300)
    QtCore.QTimer.singleShot(700, pick_in_menu)
    xdo("click", 3)
    pump(1200)
    out["menu_has_insert_here"] = "ここに差し込む" in (seen.get("menu") or [])
    out["menu_has_all_back"] = "全部の手順を有効に戻す" in (seen.get("menu") or [])
    out["insert_here_moves_the_line"] = body.Tip == pad
    out["menu"] = seen.get("menu")
    pump(500)
    shot("06-after-insert-here")
    # double-click the line: all back
    line = line_of(body)
    c = line.mapToGlobal(QtCore.QPoint(line.width() // 3, line.height() // 2))
    xdo("mousemove", c.x(), c.y())
    pump(200)
    xdo("click", "--repeat", 2, "--delay", 80, 1)
    pump(900)
    out["double_click_all_back"] = HL.at_end(body)
    words = visible_texts(t) + (seen.get("menu") or []) + [line.toolTip()]
    out["no_word_tip_shown"] = not any(("先端" in w or "Tip" in w) for w in words)
    return out


# ---------------------------------------------------------------- 2. short panels

FIELD_TYPES = (QtWidgets.QAbstractSpinBox, QtWidgets.QComboBox, QtWidgets.QCheckBox, QtWidgets.QRadioButton)


def fields_shown(box):
    out = []
    for w in box.findChildren(QtWidgets.QWidget):
        if not w.isVisible() or not isinstance(w, FIELD_TYPES):
            continue
        out.append(w.objectName())
    return out


def details_button(box):
    for b in box.findChildren(QtWidgets.QToolButton, "UnifiedDetails"):
        if b.isVisible():
            return b
    return None


def open_edit(obj, wait=1600):
    close_edit()
    Gui.ActiveDocument.setEdit(obj.Name)
    pump(wait)


def close_edit():
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    try:
        if Gui.ActiveDocument is not None:
            Gui.ActiveDocument.resetEdit()
    except Exception:
        pass
    pump(300)


def panel_box():
    import TaskPanelsGui as T

    folds = [f for f in T.install().folds if T._alive(f.box) and f.box.isVisible()]
    return folds[-1] if folds else None


def tools_doc():
    doc = new_doc("Panels")
    made = {}
    body, sk, pad, hole = plate_with_hole(doc)
    made["Pad"], made["Hole"] = pad, hole
    shape = hole.Shape
    vertical = ["Edge%d" % (i + 1) for i, e in enumerate(shape.Edges)
                if type(e.Curve).__name__ == "Line" and abs(App.Vector(e.Curve.Direction).z) > 0.999
                and len(shape.ancestorsOfType(e, Part.Face)) == 2]
    fil = body.newObject("PartDesign::Fillet", "Fillet")
    fil.Base = (hole, vertical)
    fil.Radius = 3
    doc.recompute()
    made["Fillet"] = fil
    sk3 = sketch_on(body, (body.Origin.OriginFeatures[3], [""]), 5)
    sk3.addGeometry(Part.Circle(App.Vector(60, 25, 0), App.Vector(0, 0, 1), 4))
    pocket = body.newObject("PartDesign::Pocket", "Pocket")
    pocket.Profile = sk3
    pocket.Length = 2
    doc.recompute()
    made["Pocket"] = pocket
    for kind, name, setup in (
        ("PartDesign::Mirrored", "Mirrored", lambda o: setattr(o, "MirrorPlane", (sk, ["V_Axis"]))),
        ("PartDesign::LinearPattern", "LinearPattern", lambda o: (setattr(o, "Direction", (sk, ["H_Axis"])),
                                                                   setattr(o, "Length", 10), setattr(o, "Occurrences", 2))),
        ("PartDesign::PolarPattern", "PolarPattern", lambda o: (setattr(o, "Axis", (sk, ["N_Axis"])),
                                                                setattr(o, "Occurrences", 3))),
    ):
        o = body.newObject(kind, name)
        o.Originals = [pocket]
        setup(o)
        doc.recompute()
        made[name] = o
    # chamfer and shell on a block of their own, a revolve on a third
    b2 = doc.addObject("PartDesign::Body", "Body001")
    s2 = sketch_on(b2, (b2.Origin.OriginFeatures[3], [""]))
    rectangle(s2, 100, 0, 130, 30)
    p2 = b2.newObject("PartDesign::Pad", "Pad002")
    p2.Profile = s2
    p2.Length = 10
    doc.recompute()
    edges = ["Edge%d" % (i + 1) for i, e in enumerate(p2.Shape.Edges) if abs(App.Vector(e.Curve.Direction).z) > 0.999]
    ch = b2.newObject("PartDesign::Chamfer", "Chamfer")
    ch.Base = (p2, edges[:1])
    ch.Size = 1
    doc.recompute()
    made["Chamfer"] = ch
    top = ["Face%d" % (i + 1) for i, f in enumerate(ch.Shape.Faces) if f.Surface.__class__.__name__ == "Plane"
           and abs(f.CenterOfMass.z - 10) < 1e-6]
    th = b2.newObject("PartDesign::Thickness", "Thickness")
    th.Base = (ch, top)
    th.Value = 1
    doc.recompute()
    made["Thickness"] = th
    b3 = doc.addObject("PartDesign::Body", "Body002")
    s3 = sketch_on(b3, (b3.Origin.OriginFeatures[4], [""]))
    s3.addGeometry(Part.Circle(App.Vector(150, 10, 0), App.Vector(0, 0, 1), 3))
    rv = b3.newObject("PartDesign::Revolution", "Revolution")
    rv.Profile = s3
    rv.ReferenceAxis = (s3, ["V_Axis"])
    rv.Angle = 90
    doc.recompute()
    made["Revolution"] = rv
    for o in doc.Objects:
        if o.isDerivedFrom("Sketcher::SketchObject"):
            o.ViewObject.Visibility = False
    fit()
    return doc, made, sk


def case_panels():
    import TaskPanels as TP

    App.ParamGet(TP.PARAM_PATH).Clear()
    out = {}
    doc, made, sk = tools_doc()
    shots = []
    for name in ("Pad", "Pocket", "Revolution", "Hole", "Fillet", "Chamfer", "Thickness", "Mirrored",
                 "LinearPattern", "PolarPattern"):
        obj = made[name]
        open_edit(obj, 2500 if name == "Hole" else 1600)
        fold = panel_box()
        r = {"folded": fold is not None}
        if fold is not None:
            proxy = fold.proxy()
            shown = fields_shown(proxy)
            r["fields"] = shown
            r["at_most_three"] = len(shown) <= 3
            b = details_button(proxy)
            r["details_button"] = b is not None and b.text() == "詳しく ▸"
            fname = "1%d-panel-%s" % (len(shots), name.lower())
            shot(fname, fold.box, 4)
            shots.append(fname)
        out[name] = r
        close_edit()
    # 「詳しく」 opened with the mouse, remembered for the tool (and only for it)
    open_edit(made["Pad"])
    fold = panel_box()
    proxy = fold.proxy()
    before = len(fields_shown(proxy))
    b = details_button(proxy)
    c = b.mapToGlobal(b.rect().center())
    xdo("mousemove", c.x(), c.y())
    xdo("click", 1)
    pump(500)
    after = fields_shown(proxy)
    out["details_opens_more"] = len(after) > before
    out["details_text_open"] = b.text() == "詳しく ▾"
    out["recompute_switch_only_in_details"] = "checkBoxUpdateView" in after
    shot("20-panel-pad-details-open", fold.box, 4)
    close_edit()
    open_edit(made["Pad"])
    fold = panel_box()
    out["details_remembered_for_pad"] = details_button(fold.proxy()).isChecked() and len(fields_shown(fold.proxy())) > before
    close_edit()
    open_edit(made["Pocket"])
    fold = panel_box()
    out["other_tool_still_short"] = not details_button(fold.proxy()).isChecked()
    close_edit()
    # fold the pad again (the user's choice)
    open_edit(made["Pad"])
    fold = panel_box()
    b = details_button(fold.proxy())
    c = b.mapToGlobal(b.rect().center())
    xdo("mousemove", c.x(), c.y())
    xdo("click", 1)
    pump(400)
    out["details_closes_again"] = len(fields_shown(fold.proxy())) == before
    close_edit()
    # the fillet's list reads in words
    open_edit(made["Fillet"])
    lw = None
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, QtWidgets.QListWidget) and w.objectName() == "listWidgetReferences" and w.isVisible():
            lw = w
    texts = [lw.item(i).text() for i in range(lw.count())] if lw else []
    out["fillet_list_in_words"] = texts
    out["fillet_list_words_ok"] = bool(texts) and all(t == "押し出しの縦の辺" for t in texts)
    fold = panel_box()
    if fold is not None:
        shot("21-panel-fillet-words", fold.box, 4)
    close_edit()
    # the sketch's size: the number, and the name and "reference" under 「詳しく」
    out["sketch_dimension"] = sketch_dimension(doc, sk)
    out["hole_fields_three"] = out["Hole"].get("fields") is not None and len(out["Hole"]["fields"]) <= 3
    return out


def sketch_dimension(doc, sk):
    r = {}
    Gui.ActiveDocument.setEdit(sk.Name)
    pump(1500)
    width = [i for i, c in enumerate(sk.Constraints) if c.Name == "Width"][0]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, sk.Name, "Constraint%d" % (width + 1))

    def inspect():
        dlg = QtWidgets.QApplication.activePopupWidget() or QtWidgets.QApplication.activeModalWidget()
        if dlg is None:
            for w in QtWidgets.QApplication.topLevelWidgets():
                if isinstance(w, QtWidgets.QDialog) and w.isVisible():
                    dlg = w
        if dlg is None:
            r["dialog"] = False
            return
        r["dialog"] = True
        name = dlg.findChild(QtWidgets.QLineEdit, "name")
        b = dlg.findChild(QtWidgets.QToolButton, "UnifiedDetails")
        r["name_hidden_first"] = name is not None and not name.isVisible()
        r["details_button"] = b is not None and b.isVisible() and b.text() == "詳しく ▸"
        shot("22-sketch-dimension", dlg, 6)
        if b is not None:
            c = b.mapToGlobal(b.rect().center())
            xdo("mousemove", c.x(), c.y())
            xdo("click", 1)
            pump(400)
            r["details_show_name"] = name.isVisible()
            shot("23-sketch-dimension-details", dlg, 6)
            xdo("click", 1)
            pump(300)
        xdo("key", "Escape")

    QtCore.QTimer.singleShot(1200, inspect)
    try:
        Gui.runCommand("Sketcher_ChangeDimensionConstraint")
    except Exception as e:
        r["error"] = str(e)
    pump(800)
    close_edit()
    return r


# ---------------------------------------------------------------- 3. words


def find_pixel(points, test):
    """The first screen point (of the model points) whose pick passes the test"""
    for p in points:
        (sx, sy), coin = screen_of(p)
        info = view().getObjectInfo((int(coin[0]), int(coin[1])))
        if info and test(info):
            return sx, sy
    return None


def hover(sx, sy, wait=600):
    xdo("mousemove", sx + 3, sy + 3)
    xdo("mousemove", sx, sy)
    pump(wait)


def case_words():
    import math

    out = {}
    doc = new_doc("Words")
    body, sk, pad, hole = plate_with_hole(doc)
    fit()
    shape = hole.Shape
    # the top face
    top = find_pixel([App.Vector(60, 35, 5), App.Vector(55, 30, 5)],
                     lambda i: i.get("Component", "").startswith("Face"))
    hover(*top)
    out["hover_top"] = status()
    out["hover_top_in_words"] = "押し出しの上面" in out["hover_top"]
    shot("30-hover-top-face")
    # the wall of the hole, seen through it
    wall = None
    for k in range(24):
        t = 2 * math.pi * k / 24
        p = App.Vector(20 + 3 * math.cos(t), 20 + 3 * math.sin(t), 3.5)
        wall = find_pixel([p], lambda i: i.get("Component", "").startswith("Face") and
                          shape.getElement(i["Component"]).Surface.__class__.__name__ == "Cylinder")
        if wall:
            break
    if wall:
        hover(*wall)
        out["hover_hole"] = status()
        out["hover_hole_in_words"] = "穴 ⌀6 の内側の面" in out["hover_hole"]
        shot("31-hover-hole-wall")
    else:
        out["hover_hole_in_words"] = False
    # three vertical edges clicked with Ctrl, then "also the edges in the same direction"
    corners = [App.Vector(x, y, 2.5) for x, y in ((0, 0), (80, 0), (80, 50), (0, 50))]
    picked = []
    for c in corners:
        px = find_pixel([c], lambda i: i.get("Component", "").startswith("Edge"))
        if px:
            picked.append(px)
    out["edges_seen"] = len(picked)
    Gui.Selection.clearSelection()
    for n, (sx, sy) in enumerate(picked[:3]):
        hover(sx, sy, 300)
        if n:
            xdo("keydown", "ctrl")
        xdo("click", 1)
        if n:
            xdo("keyup", "ctrl")
        pump(500)
    pump(800)
    bar = mw().findChild(QtWidgets.QFrame, "UnifiedContextBar")
    title = bar.findChild(QtWidgets.QLabel, "UnifiedPickWords") if bar is not None and bar.isVisible() else None
    out["bar_title"] = title.text() if title else None
    out["bar_title_in_words"] = bool(title) and title.text() == "押し出しの縦の辺 ×%d" % min(3, len(picked))
    out["status_after_picks"] = status()
    shot("32-context-bar-title")
    # one edge, then "also the edges in the same direction" on the bar
    Gui.Selection.clearSelection()
    pump(300)
    hover(*picked[0], 300)
    xdo("click", 1)
    pump(900)
    bar = mw().findChild(QtWidgets.QFrame, "UnifiedContextBar")
    same = None
    if bar is not None:
        for b in bar.findChildren(QtWidgets.QToolButton):
            if b.isVisible() and b.property("unifiedCommand") == "Unified_SelectParallelEdges":
                same = b
    if same is not None:
        c = same.mapToGlobal(same.rect().center())
        xdo("mousemove", c.x(), c.y())
        pump(300)
        xdo("click", 1)
        pump(800)
    out["status_after_same_direction"] = status()
    out["four_edges_in_words"] = "押し出しの縦の辺 ×4" in out["status_after_same_direction"]
    shot("33-four-vertical-edges")
    return out


# ---------------------------------------------------------------- 4. terms

QUERIES = ["円", "長方形", "線", "押し出し", "回転", "鏡", "配列", "並べる", "穴", "丸め", "面取り", "寸法", "拘束",
           "先端", "測る", "動かす", "書き出し", "読み込み", "ブーリアン", "メッシュ"]
COMMON = ("PartDesign_", "Sketcher_", "Part_", "Std_", "TechDraw_", "Mesh_", "Assembly_", "Unified_")


def case_terms():
    import CommandSearchCore as C
    import CommandSearchGui as G
    import ContextRules
    import UnifiedChrome
    import Wording as W

    out = {}
    names = {c: n for c, (n, _t) in W.TOOLS.items()}

    def shown(command):
        try:
            a = Gui.Command.get(command).getAction()
            return a[0].text().replace("&", "") if a else None
        except Exception:
            return None

    # the tool strip
    strip = []
    for tb in mw().findChildren(QtWidgets.QToolBar):
        if not tb.isVisible():
            continue
        for b in tb.findChildren(QtWidgets.QToolButton):
            if b.isVisible() and b.text() and b.defaultAction() is not None:
                strip.append(b.text())
    out["strip"] = strip
    out["strip_problems"] = [n for n in strip if W.problems(n)]
    expect = ["押し出す", "切り抜く", "回す", "鏡に映す", "まっすぐ並べる", "円に並べる", "動かす", "測る"]
    out["strip_has_table_words"] = all(e in strip for e in expect)
    bars = [tb for tb in mw().findChildren(QtWidgets.QToolBar) if tb.isVisible() and tb.y() > 20 and tb.y() < 120]
    if bars:
        shot("40-tool-strip", max(bars, key=lambda t: t.width()))
    # the sketch's step band
    doc = new_doc("Terms")
    body, sk, pad, hole = plate_with_hole(doc)
    fit()
    Gui.ActiveDocument.setEdit(sk.Name)
    pump(1800)
    band = [c for c, _ in UnifiedChrome.SKETCH_TOOLS if c]
    band_names = {c: shown(c) for c in band}
    out["band"] = band_names
    out["band_as_table"] = all(band_names[c] == names.get(c) for c in band if band_names[c] is not None and c in names)
    out["band_mismatch"] = {c: (band_names[c], names.get(c)) for c in band if band_names[c] != names.get(c)}
    more = [shown(n) for n in sorted(Gui.listCommands()) if n.startswith("Sketcher_") and not n.startswith("Sketcher_Comp")]
    out["band_more_problems"] = [n for n in more if n and W.problems(n)]
    sb = UnifiedChrome.band()
    if sb is not None and sb.isVisible():
        shot("41-sketch-band", sb)
    close_edit()
    # the bar next to the picks: its words, and the tooltips of its tools
    bar_names = []
    for kind, rows in ContextRules.RULES.items():
        for a in rows:
            bar_names.append(App.Qt.translate("ContextRules", a["label"]))
    out["bar_problems"] = [n for n in bar_names if W.problems(n)]
    # the tool search: the first hits
    ents = G.entries()
    hits = {}
    bad = []
    for q in QUERIES:
        row = []
        for h in C.search(q, ents, limit=5):
            live = G.live_entry(h["name"]) or h
            row.append((h["name"], live.get("ja")))
            if h["name"].startswith(COMMON) and live.get("ja") and W.problems(live["ja"]):
                bad.append((q, h["name"], live["ja"]))
        hits[q] = row
    out["search_top"] = hits
    out["search_problems"] = bad
    out["search_clean"] = not bad
    out["search_tip_first"] = hits["先端"][0][0] in ("Unified_InsertHere", "PartDesign_MoveTip")
    # Ctrl+K with "円": the list as shown
    mw().activateWindow()
    viewport().setFocus()
    xdo("key", "ctrl+k")
    pump(500)
    pop = G.popup()
    field = pop.findChild(QtWidgets.QLineEdit) if pop is not None else None
    if field is not None:
        field.setText("円")
        pump(600)
        shot("42-search-circle", pop, 4)
        xdo("key", "Escape")
        pump(300)
    # the untranslated texts of every command (input of tools/apply_wording.py)
    info = {}
    for n in Gui.listCommands():
        try:
            i = Gui.Command.get(n).getInfo()
        except Exception:
            continue
        info[n] = {"ctx": i.get("className"), "menu": i.get("menuText"), "tip": i.get("toolTip"), "status": i.get("statusTip")}
    json.dump(info, open(os.path.join(OUT, "cmdinfo.json"), "w"), ensure_ascii=False, indent=0)
    return out


STAGES = [("history_line", "case_history_line"), ("panels", "case_panels"),
          ("words", "case_words"), ("terms", "case_terms")]


def finish():
    checks = {}

    def collect(prefix, r):
        if isinstance(r, dict):
            for k, v in r.items():
                if isinstance(v, bool):
                    checks[prefix + k] = v
                elif isinstance(v, dict):
                    collect(prefix + k + ".", v)

    collect("", results)
    results["failed"] = [k for k, v in checks.items() if not v] + [k for k, v in results.items()
                                                                    if isinstance(v, dict) and "error" in v]
    results["passed"] = sum(1 for v in checks.values() if v)
    json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, ensure_ascii=False, default=str)
    open(os.path.join(OUT, "done"), "w").write("1")


def stage(i):
    """Each case from the main event loop: the panels closed by one case are deleted (Qt deletes
    them only back in the loop) before the next case closes its documents"""
    if i >= len(STAGES):
        finish()
        return
    name, fn = STAGES[i]
    try:
        if i == 0:
            mw().showMaximized()
            pump(800)
        results[name] = globals()[fn]()
    except Exception:
        results[name] = {"error": traceback.format_exc()}
    try:
        close_edit()
    except Exception:
        pass
    json.dump(results, open(os.path.join(OUT, "partial.json"), "w"), indent=1, ensure_ascii=False, default=str)
    QtCore.QTimer.singleShot(300, lambda: stage(i + 1))


QtCore.QTimer.singleShot(0, lambda: stage(0))
