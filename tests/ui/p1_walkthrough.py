# P1「道具の検索」の受け入れ: Ctrl+K の検索で、決めた言葉の 1 件目が正しい道具か、
# 読み込んでいないモジュールの道具（メッシュの穴埋め）を選んで実行できるかを GUI の中で確かめ、画面を撮る。
# 使い方: guictl start --fresh → guictl py "exec(open('p1_walkthrough.py').read())"（OUT は P1_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P1_OUT", "/tmp/p1-accept")
os.makedirs(OUT, exist_ok=True)
results = {}


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(400)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


import CommandSearchGui as C

doc = App.newDocument("search")
popup = C.popup()

# 決めた言葉の 1 件目
EXPECT = {
    "先端": {"PartDesign_MoveTip"},
    "MoveTip": {"PartDesign_MoveTip"},
    "STL 直す": {"Mesh_Evaluation", "Mesh_FillupHoles"},
    "歯車": {"PartDesign_InvoluteGear"},
    "中心線": {"TechDraw_CenterLineGroup", "TechDraw_FaceCenterLine", "TechDraw_2LineCenterLine", "TechDraw_2PointCenterLine"},
    "Pad": {"PartDesign_Pad"},
    "IFC": {"BIM_IfcExplorer", "Std_Export"},
}
firsts = {}
for query, ok in EXPECT.items():
    Gui.runCommand("Unified_Search")
    popup.edit.setText(query)
    pump(200)
    item = popup.list.item(0)
    firsts[query] = item.data(QtCore.Qt.UserRole) if item else None
    if query in ("歯車", "STL 直す"):
        shot("p1-0%d-search-%s" % (1 if query == "歯車" else 2, "gear" if query == "歯車" else "fix-stl"))
    popup.close_popup()
results["first_hits"] = {"ok": all(firsts[q] in EXPECT[q] for q in EXPECT), "got": firsts}

# 読み込んでいないモジュールの道具を選んで実行: 穴のあいたメッシュを選び「穴埋め」
try:
    import Mesh

    loaded_before = "Mesh_FillupHoles" in Gui.listCommands()
    m = Mesh.createBox(10, 10, 10)
    m.removeFacets([0])
    obj = doc.addObject("Mesh::Feature", "Holed")
    obj.Mesh = m
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")
    before = obj.Mesh.CountFacets
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, obj.Name)

    def fill_dialog():
        # 穴埋めは「何辺までの穴か」を聞く（本家の入力の小窓）。既定のまま OK
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QInputDialog) and w.isVisible():
                w.accept()
                return
        QtCore.QTimer.singleShot(200, fill_dialog)

    Gui.runCommand("Unified_Search")
    popup.edit.setText("穴埋め")
    pump(200)
    shot("p1-03-search-not-loaded")
    QtCore.QTimer.singleShot(1500, fill_dialog)
    popup.activate()
    pump(4000)
    after = obj.Mesh.CountFacets
    results["run_not_loaded"] = {
        "ok": not loaded_before and "Mesh_FillupHoles" in Gui.listCommands() and after > before,
        "loaded_before": loaded_before, "facets": [before, after],
        "workbench": Gui.activeWorkbench().name(),
    }
    shot("p1-04-hole-filled")
except Exception:
    results["run_not_loaded"] = {"ok": False, "error": traceback.format_exc()[-1500:]}

# 見つからないときの「AI に聞く」が最後の行にある
Gui.runCommand("Unified_Search")
popup.edit.setText("ねじ穴を 4 つ等間隔に")
pump(200)
last = popup.list.item(popup.list.count() - 1)
results["ask_ai_row"] = {"ok": last is not None and last.data(QtCore.Qt.UserRole) == popup.ROW_AI, "rows": popup.list.count()}
shot("p1-05-search-ask-ai")
popup.close_popup()

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
