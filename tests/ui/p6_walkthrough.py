# P6（一部）「履歴とパネル」の受け入れ: 木には今の文書だけ、詳しいプロパティは畳んで右クリックで出す、
# 道具のパネルを開いた瞬間にモデル全体が見える。
# 使い方: guictl start --fresh → guictl py "exec(open('p6_walkthrough.py').read())"（OUT は P6_OUT）
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P6_OUT", "/tmp/p6-accept")
os.makedirs(OUT, exist_ok=True)
mw = Gui.getMainWindow()


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(900)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


import FirstSteps
import UnifiedChrome

App.newDocument("別の文書")
doc = FirstSteps.sample_plate("板")
pump(800)
tree = [w for w in mw.findChildren(QtWidgets.QTreeWidget) if w.isVisible() and type(w).__name__.endswith("TreeWidget")][0]
items = []
for i in range(tree.topLevelItemCount()):
    top = tree.topLevelItem(i)
    items += [top.child(j) for j in range(top.childCount())] if top.childCount() and top.text(0) in ("", "アプリケーション", "Application") else [top]
shown_docs = [it.text(0) for it in items if not it.isHidden()]
props_folded = UnifiedChrome._model_splitter().sizes()[1] == 0
shot("p6-01-tree-active-doc-only")
Gui.runCommand("Unified_Properties")
pump(300)
props_shown = UnifiedChrome._model_splitter().sizes()[1] > 50
shot("p6-02-properties-shown")
Gui.runCommand("Unified_Properties")
# 道具のパネルを開くと、モデルはパネルに重ならない所に見える
def model_clear_of_panel():
    Gui.Selection.clearSelection()
    pad = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")][0]
    Gui.ActiveDocument.setEdit(pad.Name)
    pump(2000)
    view = Gui.ActiveDocument.ActiveView
    bb = pad.Shape.BoundBox
    xs = []
    for x in (bb.XMin, bb.XMax):
        for y in (bb.YMin, bb.YMax):
            for z in (bb.ZMin, bb.ZMax):
                xs.append(view.getPointOnViewport(App.Vector(x, y, z))[0])
    sub = mw.findChild(QtWidgets.QMdiArea).activeSubWindow().widget()
    dock = mw.findChild(QtWidgets.QDockWidget, "Tasks")
    panel_left = dock.mapTo(sub, QtCore.QPoint(0, 0)).x() if dock and dock.isVisible() else 10 ** 6
    shot("p6-03-panel-beside-model")
    import UnifiedChrome as U
    U.band().cancel()
    pump(800)
    return max(xs) < panel_left, max(xs), panel_left


clear, right_edge, panel_left = model_clear_of_panel()
results = {"panel": {"ok": clear, "model_right_edge_px": right_edge, "panel_left_px": panel_left}, "left": {"ok": shown_docs == ["板"] and props_folded and props_shown,
                    "tree_documents": shown_docs, "properties_folded": props_folded, "properties_shown_on_request": props_shown}}
with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
{k: v["ok"] for k, v in results.items()}
