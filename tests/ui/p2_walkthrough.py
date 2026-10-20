# P2「本家の画面を外す」の受け入れ: メニューバーは ☰ 1 つ、道具の列はスケッチ中・図面のページ・組立でも同じ、
# 1 文字の近道は文字の欄では効かない、その他の道具・右クリックの追加を GUI の中で確かめて画面を撮る。
# 使い方: guictl start --fresh → guictl py "exec(open('p2_walkthrough.py').read())"（OUT は P2_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P2_OUT", "/tmp/p2-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
mw = Gui.getMainWindow()


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(500)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def strip():
    bars = [b for b in mw.findChildren(QtWidgets.QToolBar) if b.isVisible()]
    tools = [b for b in bars if b.objectName() == "Unified Tools"]
    names = [a.objectName() for a in tools[0].actions() if a.objectName()] if tools else []
    return names, sorted(b.objectName() for b in bars)


def check(name, fn):
    try:
        results[name] = fn()
    except Exception:
        results[name] = {"ok": False, "error": traceback.format_exc()[-1500:]}


def top():
    menus = [a.text() for a in mw.menuBar().actions() if a.isVisible()]
    return {"ok": len(menus) == 1, "menus": menus}


check("menubar_is_one_menu", top)
doc = App.newDocument("板")
Gui.activeDocument().activeView().viewIsometric()
base_strip, base_bars = strip()
shot("p2-01-main")

# ☰ を開く
menu = mw.menuBar().actions()[0].menu()
QtCore.QTimer.singleShot(600, lambda: (shot("p2-02-main-menu"), menu.close()))
menu.popup(mw.menuBar().mapToGlobal(QtCore.QPoint(0, mw.menuBar().height())))
pump(1500)
results["main_menu"] = {"ok": menu.actions() != [], "items": [a.text() for a in menu.actions() if a.text()]}

# スケッチを描く間: 道具の列は同じ（スケッチの道具は足されるだけ）
body = doc.addObject("PartDesign::Body", "Body")
sk = body.newObject("Sketcher::SketchObject", "Sketch")
sk.AttachmentSupport = [(doc.getObject("XY_Plane") or body.Origin.OriginFeatures[3], "")]
sk.MapMode = "FlatFace"
import Part

for a, b in (((0, 0), (80, 0)), ((80, 0), (80, 50)), ((80, 50), (0, 50)), ((0, 50), (0, 0))):
    sk.addGeometry(Part.LineSegment(App.Vector(a[0], a[1], 0), App.Vector(b[0], b[1], 0)))
doc.recompute()
Gui.activeDocument().setEdit(sk.Name)
pump(1200)
sketch_strip, sketch_bars = strip()
shot("p2-03-sketch-editing")
Gui.activeDocument().resetEdit()
pump(800)
doc.recompute()

# 1 文字の近道: 3D 画面なら効く、文字の欄では効かない
def keys():
    view = mw.findChild(QtWidgets.QMdiArea).activeSubWindow().widget()
    gl = [w for w in view.findChildren(QtWidgets.QWidget) if w.isVisible() and "GL" in type(w).__name__ or "Quarter" in type(w).__name__]
    target = gl[0] if gl else view
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, sk.Name)
    target.setFocus()
    pump(200)
    QtTest = __import__("PySide6.QtTest", fromlist=["QTest"]).QTest
    # 文字の欄（検索）に e を打っても押し出しは始まらない
    import CommandSearchGui as C

    field = mw.findChild(QtWidgets.QLineEdit, "UnifiedSearchField")
    probe = QtWidgets.QLineEdit(mw)
    probe.show()
    probe.setFocus()
    pump(200)
    QtTest.keyClick(probe, QtCore.Qt.Key_E)
    pump(800)
    typed = probe.text()
    dialog_after_text = bool(Gui.Control.activeDialog())
    probe.hide()
    probe.deleteLater()
    # 3D 画面で E → 押し出しのパネル
    target.setFocus()
    pump(200)
    QtTest.keyClick(target, QtCore.Qt.Key_E)
    pump(1500)
    dialog_after_view = bool(Gui.Control.activeDialog())
    shot("p2-04-key-e-pad")
    if Gui.Control.activeDialog():
        for box in QtWidgets.QApplication.allWidgets():
            if isinstance(box, QtWidgets.QDialogButtonBox) and box.isVisible():
                ok = box.button(QtWidgets.QDialogButtonBox.Ok)
                if ok:
                    ok.click()
                    break
        pump(1000)
    return {"ok": typed == "e" and not dialog_after_text and dialog_after_view,
            "typed_in_field": typed, "panel_after_text": dialog_after_text, "panel_after_view_key": dialog_after_view}


check("one_key", keys)
doc.recompute()

# 右クリック: 押し出しを選ぶと「元のスケッチを編集」「ここに差し込む」
def context():
    pads = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, pads[0].Name)
    tree = [w for w in mw.findChildren(QtWidgets.QTreeWidget) if w.isVisible() and type(w).__name__.endswith("TreeWidget")]
    texts = []

    def grab():
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QMenu) and w.isVisible():
                texts.extend(a.text() for a in w.actions() if a.text())
                shot("p2-05-right-click-step")
                w.close()

    QtCore.QTimer.singleShot(800, grab)
    t = tree[0]
    item = t.currentItem() or t.topLevelItem(0)
    rect = t.visualItemRect(t.currentItem()) if t.currentItem() else QtCore.QRect(10, 10, 10, 10)
    ev = QtGui.QContextMenuEvent(QtGui.QContextMenuEvent.Mouse, rect.center(), t.viewport().mapToGlobal(rect.center()))
    QtWidgets.QApplication.sendEvent(t.viewport(), ev)
    pump(1200)
    tr = QtCore.QCoreApplication.translate
    want = [tr("Unified_EditSourceSketch", "Edit Its Sketch"), tr("CmdPartDesignMoveTip", "Set Tip")]
    return {"ok": all(any(w in x for x in texts) for w in want), "menu": texts[:12], "want": want}


check("context_menu", context)

# 図面のページを開いても道具の列は同じ
Gui.Selection.clearSelection()
Gui.runCommand("Unified_NewDrawing")
pump(2500)
for box in QtWidgets.QApplication.allWidgets():
    if isinstance(box, QtWidgets.QDialogButtonBox) and box.isVisible():
        ok = box.button(QtWidgets.QDialogButtonBox.Ok)
        if ok:
            ok.click()
            break
pump(1500)
Gui.SendMsgToActiveView("ViewFit")
page_strip, page_bars = strip()
shot("p2-06-drawing-page")

# 組立を開いても同じ
adoc = App.newDocument("組立")
Gui.runCommand("Assembly_CreateAssembly")
pump(1200)
asm_strip, asm_bars = strip()
shot("p2-07-assembly")
results["same_strip"] = {
    "ok": base_strip == sketch_strip == page_strip == asm_strip and len(base_strip) > 10,
    "strip": base_strip, "sketch_extra_bars": sorted(set(sketch_bars) - set(base_bars)),
}

# その他の道具
import UnifiedChrome

ot = UnifiedChrome.other_tools()
ot.show_window()
pump(500)
for i in range(ot.kinds.count()):
    if ot.kinds.item(i).data(QtCore.Qt.UserRole) == "MeshWorkbench":
        ot.kinds.setCurrentRow(i)
pump(500)
shot("p2-08-other-tools-mesh")
kinds = [ot.kinds.item(i).text() for i in range(ot.kinds.count())]
ot.hide()
results["other_tools"] = {"ok": len(kinds) >= 15, "kinds": kinds}

# 統合版で届かなくなっていた操作（missing-operations.md の付録）が、検索とその他の道具で全部届く
def reach():
    import re

    import CommandSearchCore as core
    import CommandSearchGui as C

    md = os.environ.get("MISSING_OPS", os.path.join(os.path.dirname(OUT.rstrip("/")), "..", "..", "missing-operations.md"))
    if not os.path.isfile(md):
        md = os.path.expanduser("~/freecad-ja-unified/docs/missing-operations.md")
    text = open(md, encoding="utf-8").read()
    names = set(re.findall(r"([A-Z][A-Za-z]+_[A-Za-z0-9_]+)", text[text.index("## 付録"):]))
    found = {e["name"] for e in C.entries() if not core.hidden(e)}
    # 作業場の切り替えは意図して無くした（統合版には作業場が無い）
    missing = sorted(names - found - {"Std_Workbench"})
    return {"ok": not missing, "commands": len(names), "not_reachable": missing}


check("missing_operations_reachable", reach)

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
