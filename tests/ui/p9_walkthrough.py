# P9「組立の流れ」の受け入れ: 新しい組立 → STEP の部品を 2 つ置く（英語・モーダル無し、最初は動かない）→
# ピンの丸い面と穴の面を選ぶと横に「差し込む」→ つながり → ✓。すき間ばめのピンが設計の検査で「浮き」にならない。
# 使い方: guictl start → guictl py "exec(open('p9_walkthrough.py').read())"（OUT は P9_OUT）
import json
import os
import subprocess
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P9_OUT", "/tmp/p9-accept")
os.makedirs(OUT, exist_ok=True)
mw = Gui.getMainWindow()
results = {}
steps = 0  # the user's actions (clicks, keys)


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(900)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def modals():
    return [w.windowTitle() for w in QtWidgets.QApplication.topLevelWidgets()
            if w.isVisible() and isinstance(w, (QtWidgets.QDialog, QtWidgets.QMessageBox))]


def gl_widget():
    sub = mw.findChild(QtWidgets.QMdiArea).activeSubWindow()
    for w in sub.widget().findChildren(QtWidgets.QWidget):
        if ("OpenGL" in type(w).__name__ or "GLWidget" in type(w).__name__) and w.isVisible():
            return w
    return sub.widget()


def click_at(point, ctrl=False):
    global steps
    view = Gui.ActiveDocument.ActiveView
    x, y = view.getPointOnViewport(App.Vector(*point))
    gl = gl_widget()
    g = gl.mapToGlobal(QtCore.QPoint(int(x), int(gl.height() - y)))
    cmd = ["xdotool", "mousemove", str(g.x()), str(g.y())]
    cmd += ["keydown", "ctrl", "click", "1", "keyup", "ctrl"] if ctrl else ["click", "1"]
    subprocess.run(cmd, check=False)
    steps += 1
    pump(900)


def run():
    global steps
    import FirstSteps

    base_path, pin_path = FirstSteps.sample_step_files()
    import ImportGui

    for path in (base_path, pin_path):
        d = App.newDocument("Unnamed", os.path.splitext(os.path.basename(path))[0])
        ImportGui.insert(path, d.Name)
    # 1. 新しい組立
    Gui.runCommand("Unified_NewAssembly")
    steps += 1
    pump(800)
    asm_doc = App.ActiveDocument
    # 2. 部品を置く: base, pin
    Gui.runCommand("Unified_PlacePart")
    steps += 1
    pump(1200)
    tree = [w for w in QtWidgets.QApplication.allWidgets() if isinstance(w, QtWidgets.QTreeWidget) and w.isVisible() and w.objectName() == "partList"][0]
    for name in ("base", "pin"):
        it = QtWidgets.QTreeWidgetItemIterator(tree)
        while it.value():
            item = it.value()
            part = item.data(0, QtCore.Qt.UserRole)
            if part is not None and part.Document.Label == name and not part.isDerivedFrom("App::Part"):
                tree.itemClicked.emit(item, 0)
                steps += 1
                break
            it += 1
        pump(900)
    insert_modals = modals()
    shot("p9-01-parts-put")
    import UnifiedChrome

    UnifiedChrome.band().finish()
    steps += 1
    pump(1200)
    asm = [o for o in asm_doc.Objects if o.isDerivedFrom("Assembly::AssemblyObject")][0]
    parts = [o for o in asm.Group if o.isDerivedFrom("Part::Feature") or o.isDerivedFrom("App::Link")]
    base = [p for p in parts if p.Label.startswith("base")][0]
    pin = [p for p in parts if p.Label.startswith("pin")][0]
    # Move the pin beside the base so that its round face and the hole can both be clicked
    pin.Placement.Base = App.Vector(90, 20, 0)
    asm_doc.recompute()
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    pump(800)
    # 3. ピンの丸い面、Ctrl で穴の面
    Gui.Selection.clearSelection()
    click_at((90 + 5.9 * 0.70, 20 - 5.9 * 0.70, 15))  # the pin's side, facing the viewer
    click_at((30 - 6 * 0.70, 20 + 6 * 0.70, 7), ctrl=True)  # the far side of the hole, inside it
    picked = [(s.Object.Label, s.SubElementNames) for s in Gui.Selection.getSelectionEx()]
    bar = mw.findChild(QtWidgets.QFrame, "UnifiedContextBar")
    labels = [b.text() for b in bar.findChildren(QtWidgets.QToolButton) if b.isVisible()] if bar and bar.isVisible() else []
    shot("p9-02-two-round-faces")
    insert = [b for b in bar.findChildren(QtWidgets.QToolButton) if b.isVisible() and "差し込む" in b.text()] if labels else []
    joints = []
    if insert:
        insert[0].click()
        steps += 1
        pump(2000)
        shot("p9-03-joint-step")
        UnifiedChrome.band().finish()
        steps += 1
        pump(1500)
        joints = [o for o in asm_doc.Objects if hasattr(o, "JointType") and o.JointType != "Grounded"]
    asm_doc.recompute()
    import DesignCheck

    issues = DesignCheck.run(asm_doc) if hasattr(DesignCheck, "run") else []
    floating = [i.message for i in issues if getattr(i, "rule", "") == "floating"]
    shot("p9-04-assembled")
    grounded = [o for o in asm_doc.Objects if hasattr(o, "ObjectToGround")]
    return {
        "ok": not insert_modals and len(parts) == 2 and bool(grounded) and bool(insert) and bool(joints) and not floating,
        "parts": [p.Label for p in parts], "grounded": len(grounded), "picked": picked, "bar": labels,
        "joints": [j.JointType for j in joints], "floating": floating, "modals": insert_modals, "user_actions": steps,
    }


try:
    results["assembly"] = run()
except Exception:
    results["assembly"] = {"ok": False, "error": traceback.format_exc()[-1500:]}
with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
