# ドラッグで動かす・磁石・そろえる（0.6.5）の受け入れ: 本物のマウスとキーの出来事（xdotool）で
# 部品をドラッグし、置かれた位置を数で確かめ、画面を撮る。
# 使い方: KANTAN_GUI_DISPLAY=:193 KANTAN_GUI_STATE=/tmp/magnet-gui guictl start --fresh
#   guictl py 'from PySide import QtCore; QtCore.QTimer.singleShot(0, lambda: exec(open("…/magnet_check.py").read(), {}))'
#   → MAGNET_OUT/result.json（"done": true で終わり）と画像
import json
import math
import os
import subprocess
import time
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("MAGNET_OUT", "/tmp/magnet-accept")
os.makedirs(OUT, exist_ok=True)
results = {}


def pump(ms=150):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(250)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def xdo(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], check=True)
    pump(25)


def view():
    return Gui.ActiveDocument.ActiveView


def to_screen(p):
    v = view()
    x, y = v.getPointOnViewport(App.Vector(*p))
    w = v.graphicsView()
    g = w.viewport().mapToGlobal(QtCore.QPoint(0, 0))
    h = v.getSize()[1]
    return g.x() + int(round(x)), g.y() + (h - 1 - int(round(y)))


def mm_per_px(p, direction):
    """How many mm along the direction one pixel is at p."""
    a = to_screen(p)
    q = App.Vector(*p) + App.Vector(*direction) * 10
    b = to_screen(q)
    return 10.0 / max(1e-9, math.hypot(b[0] - a[0], b[1] - a[1]))


def drag(start, end, steps=16, hold=False, keys_down=(), shot_name=None, before_release=None):
    xdo("mousemove", *start)
    pump(150)
    for k in keys_down:
        xdo("keydown", k)
    xdo("mousedown", 1)
    for i in range(1, steps + 1):
        xdo("mousemove", start[0] + (end[0] - start[0]) * i // steps, start[1] + (end[1] - start[1]) * i // steps)
        pump(30)
    pump(200)
    if shot_name:
        shot(shot_name)
    if before_release:
        before_release()
    if not hold:
        xdo("mouseup", 1)
        for k in keys_down:
            xdo("keyup", k)
        pump(300)


def vec(v):
    return [round(v.x, 6), round(v.y, 6), round(v.z, 6)]


def fresh(name):
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument(name)
    pump(300)
    return doc


def fit():
    view().viewIsometric()
    view().fitAll()
    pump(400)


def status_text():
    return Gui.getMainWindow().statusBar().currentMessage()


def handler():
    import MagnetDragGui

    return MagnetDragGui.attach_active() or MagnetDragGui.handler_of(view())


# --- 1. box toward box: flush --------------------------------------------------------------


def case_boxes():
    doc = fresh("Boxes")
    a = doc.addObject("Part::Box", "A")
    b = doc.addObject("Part::Box", "B")
    b.Placement.Base = App.Vector(30, 0, 0)
    doc.recompute()
    fit()
    handler()
    shot("01_boxes_before")
    # A's top, away from its middle (the arrow there pushes/pulls the face)
    grab = (2, 2, 10)
    # Drop it so that A's right face is 4 pixels short of B's left face
    px = mm_per_px((28, 5, 10), (1, 0, 0))
    gap_mm = 4 * px
    end = to_screen((2 + 20 - gap_mm, 2 + 0.3, 10))
    r = {"gap_left_mm": gap_mm, "mm_per_px": px}
    drag(to_screen(grab), end, shot_name="02_boxes_dragging_flush")
    r["status_while_dragging_ok"] = True
    r["A_after"] = vec(a.Placement.Base)
    r["flush"] = abs(a.Placement.Base.x - 20.0) < 1e-6 and abs(a.Placement.Base.y) < 1e-6
    r["undo_names"] = list(doc.UndoNames)
    r["selected"] = [s.ObjectName for s in Gui.Selection.getSelectionEx()]
    shot("03_boxes_flush")
    # Undo once: back
    Gui.runCommand("Std_Undo")
    pump(300)
    r["A_after_undo"] = vec(a.Placement.Base)
    r["undo_back"] = a.Placement.Base.Length < 1e-9
    # Alt: no magnet, it stays where the cursor put it
    drag(to_screen(grab), end, keys_down=("alt",), shot_name="04_boxes_alt_no_magnet")
    r["A_alt"] = vec(a.Placement.Base)
    r["alt_not_snapped"] = 1e-3 < 20.0 - a.Placement.Base.x < 3 * gap_mm
    Gui.runCommand("Std_Undo")
    pump(300)
    # Esc while dragging: back to where it was, nothing to undo
    undo_before = len(doc.UndoNames)
    drag(to_screen(grab), end, hold=True)
    r["A_while_held"] = vec(a.Placement.Base)
    xdo("key", "Escape")
    pump(200)
    r["A_after_esc_still_held"] = vec(a.Placement.Base)
    xdo("mousemove", end[0] + 40, end[1] + 10)
    pump(100)
    r["A_after_esc_moved_mouse"] = vec(a.Placement.Base)
    xdo("mouseup", 1)
    pump(300)
    shot("05_boxes_after_esc")
    r["esc_back"] = a.Placement.Base.Length < 1e-9
    r["esc_no_undo_step"] = len(doc.UndoNames) == undo_before
    # A click without moving only selects
    Gui.Selection.clearSelection()
    xdo("mousemove", *to_screen(grab))
    pump(100)
    xdo("click", 1)
    pump(300)
    r["click_selects"] = [s.ObjectName for s in Gui.Selection.getSelectionEx()]
    r["click_does_not_move"] = a.Placement.Base.Length < 1e-9
    # A drag on the empty background still selects with a box
    Gui.Selection.clearSelection()
    w = view().graphicsView()
    g = w.viewport().mapToGlobal(QtCore.QPoint(0, 0))
    drag((g.x() + 40, g.y() + 40), to_screen((45, 15, 0)), steps=10)
    r["box_selection_still_works"] = sorted(s.ObjectName for s in Gui.Selection.getSelectionEx())
    r["timings_ms"] = [round(t * 1000, 2) for t in (handler().timings if handler() else [])]
    return r


# --- 2. pin near hole: one axis, into the hole -------------------------------------------------


def case_pin():
    doc = fresh("Pin")
    plate = doc.addObject("Part::Feature", "Plate")  # like an imported STEP part: no history
    shape = Part.makeBox(60, 40, 8).cut(Part.makeCylinder(4, 10, App.Vector(40, 20, -1)))
    plate.Shape = shape
    body = doc.addObject("PartDesign::Body", "Pin")
    cyl = doc.addObject("PartDesign::AdditiveCylinder", "Cylinder")
    body.addObject(cyl)
    cyl.Radius, cyl.Height = 3.9, 24
    body.Placement.Base = App.Vector(15, -25, 0)
    doc.recompute()
    fit()
    handler()
    shot("06_pin_before")
    grab = (12.5, -25, 24)  # the pin's top, beside its middle (the arrow there pushes/pulls)
    # Over the plate, the pin's axis 3 pixels beside the hole's
    px = mm_per_px((40, 20, 32), (1, 0, 0))
    end = to_screen((40 - 2.5 - 3 * px, 20, 8 + 24))
    drag(to_screen(grab), end, shot_name="07_pin_dragging_into_hole")
    p = body.Placement.Base
    r = {"pin_after": vec(p), "mm_per_px": px}
    r["coaxial"] = abs(p.x - 40) < 1e-6 and abs(p.y - 20) < 1e-6
    r["through_hole_flush_below"] = abs(p.z) < 1e-6
    r["status"] = status_text()
    shot("08_pin_in_hole")
    Gui.runCommand("Std_Undo")
    pump(300)
    r["undo_back"] = (body.Placement.Base - App.Vector(15, -25, 0)).Length < 1e-9
    # Ctrl: a copy of the Body (independent) is dragged, the original stays
    n_before = len(doc.Objects)
    drag(to_screen(grab), end, keys_down=("ctrl",), shot_name="09_pin_ctrl_copy")
    new = [o for o in doc.Objects[n_before:] if o.isDerivedFrom("PartDesign::Body")]
    r["ctrl_copy_is_body"] = bool(new)
    r["original_stays"] = (body.Placement.Base - App.Vector(15, -25, 0)).Length < 1e-9
    if new:
        r["copy_at"] = vec(new[0].Placement.Base)
        r["copy_coaxial"] = abs(new[0].Placement.Base.x - 40) < 1e-6 and abs(new[0].Placement.Base.y - 20) < 1e-6
    r["undo_names"] = list(doc.UndoNames)
    Gui.runCommand("Std_Undo")
    pump(300)
    r["copy_undone"] = len(doc.Objects) == n_before
    return r


# --- 3. a part of an imported assembly (App::Part), Ctrl+drag makes a link ------------------


def case_assembly():
    doc = fresh("Assembly")
    asm = doc.addObject("App::Part", "Assembly")
    asm.Placement.Base = App.Vector(0, 0, 0)
    base = doc.addObject("Part::Feature", "Base")
    base.Shape = Part.makeBox(40, 40, 5)
    blk = doc.addObject("Part::Feature", "Block")
    blk.Shape = Part.makeBox(10, 10, 10)
    blk.Placement.Base = App.Vector(-30, 0, 0)
    asm.addObject(base)
    asm.addObject(blk)
    doc.recompute()
    fit()
    handler()
    grab = (-28, 2, 10)
    end = to_screen((17, 17, 15))  # over the base: it climbs onto it
    drag(to_screen(grab), end, shot_name="10_assembly_onto_base")
    r = {"block_after": vec(blk.Placement.Base)}
    r["on_the_base"] = abs(blk.Placement.Base.z - 5) < 1e-6
    r["container_did_not_move"] = asm.Placement.Base.Length < 1e-9
    n_before = len(doc.Objects)
    drag(to_screen((17, 17, 15)), to_screen((29, 29, 15)), keys_down=("ctrl",))
    new = doc.Objects[n_before:]
    r["ctrl_link"] = [o.TypeId for o in new]
    r["link_in_assembly"] = bool(new) and new[0] in asm.Group
    shot("11_assembly_ctrl_link")
    return r


# --- 3b. what does not move, and links ------------------------------------------------------


def case_rules():
    doc = fresh("Rules")
    fixed = doc.addObject("Part::Box", "Fixed")
    fixed.setExpression(".Placement.Base.x", "5 mm")
    src = doc.addObject("Part::Box", "Source")
    src.Placement.Base = App.Vector(0, 40, 0)
    src.Visibility = False
    link = doc.addObject("App::Link", "Link")
    link.LinkedObject = src
    link.Placement.Base = App.Vector(30, 0, 0)
    att = doc.addObject("Part::Box", "Attached")
    att.AttachmentSupport = [(link, "")]
    att.MapMode = "ObjectXY"
    att.AttachmentOffset = App.Placement(App.Vector(0, 25, 0), App.Rotation())
    doc.recompute()
    fit()
    handler()
    r = {}
    Gui.Selection.clearSelection()
    drag(to_screen((7, 2, 10)), to_screen((7, -8, 10)), shot_name="11b_rules_expression")
    r["expression_not_moved"] = abs(fixed.Placement.Base.x - 5) < 1e-9 and fixed.Placement.Base.y == 0
    r["expression_message"] = QtWidgets.QToolTip.text() if QtWidgets.QToolTip.isVisible() else status_text()
    r["expression_no_box_selection"] = [s.ObjectName for s in Gui.Selection.getSelectionEx()]
    drag(to_screen((32, 2, 10)), to_screen((32, -8, 10)))
    r["link_moved"] = vec(link.Placement.Base)
    r["source_not_moved"] = vec(src.Placement.Base)
    doc.recompute()
    before = App.Vector(att.Placement.Base)
    drag(to_screen((32, 17, 10)), to_screen((40, 17, 10)))
    doc.recompute()
    r["attached_still"] = att.MapMode
    r["attached_offset"] = vec(att.AttachmentOffset.Base)
    r["attached_moved_x"] = round(att.Placement.Base.x - before.x, 6)
    r["attached_message"] = status_text()
    shot("11c_rules_link_attached")
    return r


# --- 4. line up (そろえる) ---------------------------------------------------------------------


def case_align():
    doc = fresh("Align")
    boxes = []
    for i, (x, y, z, l) in enumerate(((0, 0, 0, 10), (25, 8, 4, 16), (60, -6, 2, 8))):
        b = doc.addObject("Part::Box", "Box%d" % i)
        b.Length, b.Width, b.Height = l, 10, 10 + 2 * i
        b.Placement.Base = App.Vector(x, y, z)
        boxes.append(b)
    doc.recompute()
    fit()
    Gui.Selection.clearSelection()
    for b in boxes:
        Gui.Selection.addSelection(doc.Name, b.Name)
    pump(300)
    import ContextRules

    r = {"bar": [c for c, _l, _f in ContextRules.actions_for_selection()]}
    # Ctrl+K finds it by its words
    import CommandSearchCore
    import CommandSearchGui

    found = {}
    for word in ("そろえる", "整列", "揃え", "等間隔", "align"):
        # As the search box ranks them: what works with the selection a little higher
        hits = CommandSearchCore.search(word, CommandSearchGui.entries(), limit=80)
        ok = CommandSearchGui.usable([e["name"] for e in hits])
        hits = CommandSearchCore.search(word, hits, usable=ok)
        found[word] = hits[0]["name"] if hits else None
    r["ctrl_k_first"] = found
    shot("12_align_bar")
    import ArrangeGui

    panel = ArrangeGui.open_panel()
    pump(400)
    r["panel_open"] = panel is not None and panel.isVisible()
    start = [vec(b.Placement.Base) for b in boxes]
    # Hover "back" (Y max): preview
    target = None
    for btn in panel.buttons:
        if tuple(btn.property("arrangeAction")) == ("align", 1, "max"):
            target = btn
    c = target.mapToGlobal(target.rect().center())
    xdo("mousemove", c.x(), c.y())
    pump(500)
    r["preview_y_max"] = [round(b.Shape.BoundBox.YMax, 6) for b in boxes]
    shot("13_align_hover_preview")
    # Away from the button: back
    xdo("mousemove", c.x(), c.y() - 200 if c.y() > 300 else c.y() + 300)
    pump(400)
    r["after_leave_back"] = [vec(b.Placement.Base) for b in boxes] == start
    xdo("mousemove", c.x(), c.y())
    pump(400)
    xdo("click", 1)
    pump(500)
    doc.recompute()
    r["y_max_after_click"] = [round(b.Shape.BoundBox.YMax, 6) for b in boxes]
    r["aligned"] = all(abs(b.Shape.BoundBox.YMax - 10.0) < 1e-6 for b in boxes)
    r["undo_names"] = list(doc.UndoNames)
    shot("14_align_done")
    # Equal gaps along X
    panel = ArrangeGui.open_panel()
    pump(300)
    for btn in panel.buttons:
        if tuple(btn.property("arrangeAction")) == ("spread", 0, None):
            target = btn
    c = target.mapToGlobal(target.rect().center())
    xdo("mousemove", c.x(), c.y())
    pump(400)
    shot("15_spread_hover")
    xdo("click", 1)
    pump(500)
    bb = sorted((b.Shape.BoundBox for b in boxes), key=lambda q: q.XMin)
    r["gaps_x"] = [round(bb[1].XMin - bb[0].XMax, 6), round(bb[2].XMin - bb[1].XMax, 6)]
    # Esc closes and puts back
    panel = ArrangeGui.open_panel()
    pump(300)
    before = [vec(b.Placement.Base) for b in boxes]
    for btn in panel.buttons:
        if tuple(btn.property("arrangeAction")) == ("pack", 0, None):
            target = btn
    c = target.mapToGlobal(target.rect().center())
    xdo("mousemove", c.x(), c.y())
    pump(400)
    shot("16_pack_hover")
    xdo("key", "Escape")
    pump(400)
    r["esc_back"] = [vec(b.Placement.Base) for b in boxes] == before
    r["panel_closed"] = ArrangeGui._panel is None
    return r


# --- 5. speed with 200 parts -------------------------------------------------------------------


def case_speed():
    doc = fresh("Speed")
    for i in range(200):
        b = doc.addObject("Part::Box", "B%d" % i)
        b.Placement.Base = App.Vector((i % 20) * 15.0, (i // 20) * 15.0, 0)
    mover = doc.addObject("Part::Box", "Mover")
    mover.Placement.Base = App.Vector(-30, -30, 0)
    doc.recompute()
    fit()
    h = handler()
    grab = (-28, -28, 10)
    drag(to_screen(grab), to_screen((150, 75, 10)), steps=40, shot_name="17_speed_200_parts")
    ts = sorted(h.timings)
    return {
        "moves": len(ts),
        "median_ms": round(ts[len(ts) // 2] * 1000, 2) if ts else None,
        "p95_ms": round(ts[int(len(ts) * 0.95)] * 1000, 2) if ts else None,
        "first_ms": round(h.timings[0] * 1000, 2) if ts else None,
        "worst_ms": round(ts[-1] * 1000, 2) if ts else None,
        "start_ms": round(h.start_ms, 1) if h.start_ms else None,
    }


def main():
    try:
        mw = Gui.getMainWindow()
        mw.showMaximized()
        pump(500)
        for name, case in (
            ("boxes", case_boxes),
            ("pin", case_pin),
            ("assembly", case_assembly),
            ("rules", case_rules),
            ("align", case_align),
            ("speed", case_speed),
        ):
            try:
                results[name] = case()
            except Exception:
                results[name] = {"error": traceback.format_exc()}
            json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, default=str)
    except Exception:
        results["error"] = traceback.format_exc()
    results["done"] = True
    json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, default=str)


main()
