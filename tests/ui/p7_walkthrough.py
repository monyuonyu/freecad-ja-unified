# P7「スタート画面と見本」の受け入れ: 4 つの始め方がどれも 1 回で最初の画面に着くこと、
# 「はじめての人へ」で見本の文書と手順が出て、手順が操作に合わせて進むことを確かめて画面を撮る。
# 使い方: guictl start（初回起動の画面を済ませた状態）→ guictl py "exec(open('p7_walkthrough.py').read())"
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P7_OUT", "/tmp/p7-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
mw = Gui.getMainWindow()
mdi = mw.findChild(QtWidgets.QMdiArea)


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(900)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def start_page():
    if not any(sub.widget().objectName() == "StartView" for sub in mdi.subWindowList()):
        Gui.runCommand("Start_Start")
        pump(800)
    subs = mdi.subWindowList()
    for sub in subs:
        if sub.widget().objectName() == "StartView":
            mdi.setActiveSubWindow(sub)
            pump(300)
    # Looked up again each time: PySide may drop a wrapper reached through a temporary one
    return mw.findChild(QtWidgets.QMainWindow, "StartView")


def card(view, heading):
    for b in view.findChildren(QtWidgets.QPushButton):
        if b.isVisible() and heading in (b.text() + " ".join(l.text() for l in b.findChildren(QtWidgets.QLabel))):
            return b
    return None


def check(name, fn):
    try:
        results[name] = fn()
    except Exception:
        results[name] = {"ok": False, "error": traceback.format_exc()[-1500:]}
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.isVisible() and isinstance(w, QtWidgets.QDialog):
            w.reject()
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()


tr = QtCore.QCoreApplication.translate
view = start_page()
shot("p7-01-start")
results["four_ways"] = {"ok": all(card(view, tr("StartGui::StartView", h)) for h in ("New Part", "New Assembly", "Make a Drawing", "Open File")) and view.findChild(QtWidgets.QLineEdit, "UnifiedStartSearch") is not None}


def new_part():
    card(start_page(), tr("StartGui::StartView", "New Part")).click()
    pump(1500)
    ok = bool(Gui.Control.activeDialog())  # where to draw: click a plane
    shot("p7-02-new-part-first-screen")
    return {"ok": ok}


def new_assembly():
    card(start_page(), tr("StartGui::StartView", "New Assembly")).click()
    pump(1500)
    doc = App.ActiveDocument
    ok = doc is not None and any(o.isDerivedFrom("Assembly::AssemblyObject") for o in doc.Objects)
    return {"ok": ok}


def open_file():
    seen = {}

    def close():
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QFileDialog) and w.isVisible():
                seen["dialog"] = w.windowTitle()
                w.reject()
                return
        QtCore.QTimer.singleShot(200, close)

    QtCore.QTimer.singleShot(400, close)
    card(start_page(), tr("StartGui::StartView", "Open File")).click()
    pump(800)
    return {"ok": "dialog" in seen, "dialog": seen.get("dialog")}


def drawing():
    # With a part open: straight to the three views
    import FirstSteps

    FirstSteps.sample_plate("板")
    card(start_page(), tr("StartGui::StartView", "Make a Drawing")).click()
    pump(2500)
    doc = App.getDocument("板")
    ok = any(o.isDerivedFrom("TechDraw::DrawProjGroup") for o in doc.Objects)
    shot("p7-03-drawing-first-screen")
    return {"ok": ok}


def guide():
    import FirstSteps

    start_page()
    FirstSteps.start("change")
    pump(1500)
    shot("p7-04-guide-change-size")
    panel = mw.findChild(QtWidgets.QDockWidget, "UnifiedFirstSteps")
    text_before = panel.widget().findChildren(QtWidgets.QLabel)[1].text()
    doc = App.ActiveDocument
    sk = [o for o in doc.Objects if o.isDerivedFrom("Sketcher::SketchObject")][0]
    Gui.ActiveDocument.setEdit(sk.Name)
    pump(1500)
    text_after = panel.widget().findChildren(QtWidgets.QLabel)[1].text()
    shot("p7-05-guide-step-done")
    Gui.ActiveDocument.resetEdit()
    return {"ok": panel.isVisible() and text_before != text_after and "✓" in text_after}


check("new_part", new_part)
check("new_assembly", new_assembly)
check("open_file", open_file)
check("drawing", drawing)
check("guide", guide)

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
