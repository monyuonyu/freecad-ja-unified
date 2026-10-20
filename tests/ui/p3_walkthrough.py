# P3「その場の手順」の受け入れ: スケッチを描く間・道具のパネルの間、上に手順の帯（何をしているか・その手順の道具・
# ✓ 終わる・✕ やめる）が出て、道具の列・作った順・検索は同じ位置のまま。✕ で始める前に戻る。
# 手順の途中で道具の列を押すと、手順を終えてからその道具に進む。
# 使い方: guictl start --fresh → guictl py "exec(open('p3_walkthrough.py').read())"（OUT は P3_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P3_OUT", "/tmp/p3-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
mw = Gui.getMainWindow()


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(1200)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def band():
    return mw.findChild(QtWidgets.QToolBar, "UnifiedStepBand")


def layout():
    """Where the tool strip, the tree and the search field are (should not move between states,
    except the strip, which never moves; the band sits below it)"""
    strip = mw.findChild(QtWidgets.QToolBar, "Unified Tools")
    field = mw.findChild(QtWidgets.QLineEdit, "UnifiedSearchField")
    g = lambda w: (w.mapTo(mw, QtCore.QPoint(0, 0)).x(), w.mapTo(mw, QtCore.QPoint(0, 0)).y(), w.width()) if w else None
    return {"strip": g(strip), "search": g(field), "strip_visible": bool(strip and strip.isVisible())}


def check(name, fn):
    try:
        results[name] = fn()
    except Exception:
        results[name] = {"ok": False, "error": traceback.format_exc()[-1500:]}


def click(name):
    b = mw.findChild(QtWidgets.QPushButton, name)
    b.click()
    pump(1200)


doc = App.newDocument("板")
body = doc.addObject("PartDesign::Body", "Body")
sk = body.newObject("Sketcher::SketchObject", "Sketch")
sk.AttachmentSupport = [(body.Origin.OriginFeatures[3], "")]
sk.MapMode = "FlatFace"
doc.recompute()
Gui.activeDocument().activeView().viewIsometric()
before = layout()


def sketch_cancel():
    Gui.activeDocument().setEdit(sk.Name)
    pump(1200)
    during = layout()
    visible = band().isVisible()
    # 描いた（ここでは 4 本の線を足す。利用者が線の道具で描くのと同じく、元に戻すの段になる）
    doc.openTransaction("Draw")
    for a, b in (((0, 0), (80, 0)), ((80, 0), (80, 50)), ((80, 50), (0, 50)), ((0, 50), (0, 0))):
        sk.addGeometry(Part.LineSegment(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0)))
    doc.commitTransaction()
    pump(300)
    shot("p3-01-sketch-band")
    drawn = len(sk.Geometry)
    click("UnifiedStepCancel")
    pump(800)
    return {
        "ok": visible and drawn == 4 and len(sk.Geometry) == 0 and not band().isVisible()
        and during["strip"] == before["strip"] and during["search"] == before["search"],
        "band_visible": visible, "geometry_after_cancel": len(sk.Geometry), "before": before, "during": during,
    }


check("sketch_cancel_goes_back", sketch_cancel)


def sketch_done_then_strip():
    Gui.activeDocument().setEdit(sk.Name)
    pump(1200)
    doc.openTransaction("Draw")
    for a, b in (((0, 0), (80, 0)), ((80, 0), (80, 50)), ((80, 50), (0, 50)), ((0, 50), (0, 0))):
        sk.addGeometry(Part.LineSegment(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0)))
    doc.commitTransaction()
    pump(300)
    # 手順の途中で道具の列の「押し出し」を押す: スケッチを終えてから押し出しに進む
    strip = mw.findChild(QtWidgets.QToolBar, "Unified Tools")
    pad_btn = [b for b in strip.findChildren(QtWidgets.QToolButton) if b.defaultAction() and b.defaultAction().objectName() == "PartDesign_Pad"][0]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, sk.Name)
    QtTest = __import__("PySide6.QtTest", fromlist=["QTest"]).QTest
    QtTest.mouseClick(pad_btn, QtCore.Qt.LeftButton)
    pump(2500)
    in_edit = Gui.activeDocument().getInEdit()
    edited = in_edit.Object.Name if in_edit else None
    title = [w.text() for w in band().findChildren(QtWidgets.QLabel) if w.objectName() == "UnifiedStepTitle"]
    shot("p3-02-pad-band")
    # パネルの OK・キャンセルは帯にだけ（二重にしない）
    import UnifiedChrome

    box, ok, cancel = UnifiedChrome.task_buttons()
    panel_buttons_hidden = box is None or not box.isVisible()
    click("UnifiedStepCancel")
    pads_after_cancel = [o.Name for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    return {
        "ok": len(sk.Geometry) == 4 and edited is not None and edited.startswith("Pad") and panel_buttons_hidden
        and not pads_after_cancel,
        "sketch_kept": len(sk.Geometry), "editing": edited, "band_title": title,
        "panel_buttons_hidden": panel_buttons_hidden, "pads_after_cancel": pads_after_cancel,
    }


check("strip_during_sketch_finishes_it", sketch_done_then_strip)


def pad_done():
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, sk.Name)
    Gui.runCommand("PartDesign_Pad")
    pump(1500)
    click("UnifiedStepDone")
    doc.recompute()
    pads = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    shot("p3-03-padded")
    return {"ok": bool(pads) and pads[0].Shape.Volume > 0 and not band().isVisible(), "pads": [p.Name for p in pads]}


check("pad_done", pad_done)

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
