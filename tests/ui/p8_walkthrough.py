# P8「図面の流れ」の受け入れ: 穴あきの板で「図面を描く」を 1 回押すと、A4 の表題欄付きの用紙に三面図・穴の中心線 4・
# 穴の寸法 1（4×⌀6 キリ）・外形寸法が付き、PDF に書き出せることを確かめて画面を撮る。
# 使い方: guictl start → guictl py "exec(open('p8_walkthrough.py').read())"（OUT は P8_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P8_OUT", "/tmp/p8-accept")
os.makedirs(OUT, exist_ok=True)
results = {}


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(1200)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def run():
    import FirstSteps

    doc = FirstSteps.sample_plate("ベース板")
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.Selection.clearSelection()
    Gui.runCommand("Unified_NewDrawing")
    pump(3000)
    Gui.SendMsgToActiveView("ViewFit")
    shot("p8-01-drawing-made")
    page = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawPage")][0]
    group = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawProjGroup")][0]
    dims = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawViewDimension")]
    holes = [d for d in dims if d.Type == "Diameter"]
    outer = [d for d in dims if d.Type in ("DistanceX", "DistanceY")]
    lines = len(group.Anchor.CosmeticEdges) if hasattr(group.Anchor, "CosmeticEdges") else None
    texts = dict(page.Template.EditableTexts)
    pdf = os.path.join(OUT, "p8-plate-drawing.pdf")
    try:
        import TechDrawGui

        TechDrawGui.exportPageAsPdf(page, pdf)
    except Exception as e:
        App.Console.PrintWarning("pdf: {}\n".format(e))
    return {
        "ok": len(group.Views) == 3 and len(holes) == 1 and len(outer) >= 2 and (lines or 0) >= 8
        and os.path.isfile(pdf) and texts.get("title") == doc.Label,
        "views": [v.Label for v in group.Views], "hole_dimension": holes[0].FormatSpec if holes else None,
        "outer_dimensions": len(outer), "center_line_segments": lines, "title": texts.get("title"),
        "scale": texts.get("scale"), "pdf": os.path.isfile(pdf), "template": os.path.basename(page.Template.Template),
        "modals": [w.windowTitle() for w in QtWidgets.QApplication.topLevelWidgets() if w.isVisible() and isinstance(w, QtWidgets.QDialog)],
    }


try:
    results["plate_drawing"] = run()
except Exception:
    results["plate_drawing"] = {"ok": False, "error": traceback.format_exc()[-1500:]}

with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
