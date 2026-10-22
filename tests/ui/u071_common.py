# 0.7.1（使い勝手の試験 usability-0.6.9 の指摘を直す）の受け入れの共通部品。u071_check.py が読む
import json
import os
import subprocess
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("U071_OUT", os.path.expanduser("~/freecad-ja-unified/docs/ui-redesign/accept/U071"))
WORK = "/tmp/u071"
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)


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
    sb = mw().statusBar()
    label = sb.findChild(QtWidgets.QLabel, "actionLabel")
    return sb.currentMessage() or (label.text() if label is not None else "")


def view():
    return Gui.ActiveDocument.ActiveView


def viewport():
    return view().graphicsView().viewport()


def screen_of(point):
    x, y = view().getPointOnViewport(App.Vector(point))
    g = viewport().mapToGlobal(QtCore.QPoint(0, 0))
    h = viewport().height()
    return (g.x() + int(round(x)), g.y() + (h - 1 - int(round(y)))), (x, y)


def pick_pixel(points, test):
    for p in points:
        (sx, sy), coin = screen_of(p)
        info = view().getObjectInfo((int(coin[0]), int(coin[1])))
        if info and test(info):
            return sx, sy
    return None


def click(sx, sy, ctrl=False, button=1):
    xdo("mousemove", sx + 2, sy + 2)
    xdo("mousemove", sx, sy)
    pump(200)
    if ctrl:
        xdo("keydown", "ctrl")
    xdo("click", button)
    if ctrl:
        xdo("keyup", "ctrl")
    pump(500)


def click_widget(w):
    c = w.mapToGlobal(w.rect().center())
    click(c.x(), c.y())


def close_all():
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    pump(300)


def block(name, w, d, h, save=True):
    import Sketcher

    doc = App.newDocument(name)
    body = doc.addObject("PartDesign::Body", "Body")
    sk = body.newObject("Sketcher::SketchObject", "Sketch")
    sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
    sk.MapMode = "FlatFace"
    p = [App.Vector(0, 0, 0), App.Vector(w, 0, 0), App.Vector(w, d, 0), App.Vector(0, d, 0)]
    for i in range(4):
        sk.addGeometry(Part.LineSegment(p[i], p[(i + 1) % 4]))
    for i in range(4):
        sk.addConstraint(Sketcher.Constraint("Coincident", i, 2, (i + 1) % 4, 1))
    pad = body.newObject("PartDesign::Pad", "Pad")
    pad.Profile = sk
    pad.Length = h
    doc.recompute()
    sk.ViewObject.Visibility = False
    if save:
        doc.saveAs(os.path.join(WORK, name + ".FCStd"))
    return doc


def fit():
    Gui.Selection.clearSelection()
    view().viewIsometric()
    view().fitAll()
    pump(600)


def run_stages(stages, results):
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
        results["failed"] = [k for k, v in checks.items() if not v] + [
            k for k, v in results.items() if isinstance(v, dict) and "error" in v]
        results["passed"] = sum(1 for v in checks.values() if v)
        json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, ensure_ascii=False, default=str)
        open(os.path.join(OUT, "done"), "w").write("1")

    def stage(i):
        if i >= len(stages):
            finish()
            return
        name, fn = stages[i]
        try:
            if i == 0:
                mw().showMaximized()
                pump(800)
            results[name] = fn()
        except Exception:
            results[name] = {"error": traceback.format_exc()}
        try:
            if Gui.Control.activeDialog():
                Gui.Control.closeDialog()
        except Exception:
            pass
        json.dump(results, open(os.path.join(OUT, "partial.json"), "w"), indent=1, ensure_ascii=False, default=str)
        QtCore.QTimer.singleShot(300, lambda: stage(i + 1))

    for name in ("result.json", "done", "partial.json"):
        try:
            os.unlink(os.path.join(OUT, name))
        except OSError:
            pass
    QtCore.QTimer.singleShot(0, lambda: stage(0))
