# P10「読み込み後の案内と 3D プリント」の受け入れ: DXF を開くと「この図形でできること」の帯が出て、「押し出して立体にする」で
# 部品になる。穴のあいた STL を開くと「このメッシュでできること」。3D プリント用の書き出しは、調べた結果を出し、直してから書き出せる。
# 使い方: guictl start → guictl py "exec(open('p10_walkthrough.py').read())"（OUT は P10_OUT）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P10_OUT", "/tmp/p10-accept")
WORK = os.environ.get("P10_WORK", "/tmp/p10-work")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)
mw = Gui.getMainWindow()
results = {}


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(900)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def band_actions():
    bar = mw.findChild(QtWidgets.QToolBar, "UnifiedOpenedBand")
    if bar is None or not bar.isVisible():
        return bar, []
    return bar, [a for a in bar.actions() if a.text() and a.text() != "✕"]


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


def dxf():
    path = os.path.join(WORK, "outline.dxf")
    lines = ""
    for a, b in (((0, 0), (80, 0)), ((80, 0), (80, 50)), ((80, 50), (0, 50)), ((0, 50), (0, 0))):
        lines += "0\nLINE\n8\n0\n10\n{}\n20\n{}\n30\n0\n11\n{}\n21\n{}\n31\n0\n".format(a[0], a[1], b[0], b[1])
    with open(path, "w") as f:
        f.write("0\nSECTION\n2\nENTITIES\n" + lines + "0\nENDSEC\n0\nEOF\n")
    import importDXF

    importDXF.open(path)
    pump(1500)
    doc = App.ActiveDocument
    bar, acts = band_actions()
    texts = [a.text() for a in acts]
    shot("p10-01-dxf-opened-band")
    acts[0].trigger()  # 押し出して立体にする
    pump(1500)
    import UnifiedChrome

    UnifiedChrome.band().finish()
    pump(1500)
    doc.recompute()
    pads = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    Gui.SendMsgToActiveView("ViewFit")
    shot("p10-02-dxf-extruded")
    return {"ok": len(texts) >= 2 and bool(pads) and pads[0].Shape.Volume > 0, "band": texts,
            "volume": pads[0].Shape.Volume if pads else 0}


def stl():
    import Mesh

    m = Mesh.createBox(20, 10, 5)
    m.removeFacets([0, 1])
    path = os.path.join(WORK, "broken.stl")
    m.write(path)
    Mesh.open(path)
    pump(1500)
    doc = App.ActiveDocument
    bar, acts = band_actions()
    texts = [a.text() for a in acts]
    Gui.SendMsgToActiveView("ViewFit")
    shot("p10-03-stl-opened-band")
    # 3D プリント用: 調べた結果と「直してから書き出す」
    import UnifiedFiles

    dlg = UnifiedFiles.PrintDialog([o for o in doc.Objects if o.isDerivedFrom("Mesh::Feature")])
    dlg.dialog.show()
    pump(500)
    report = dict(dlg.report)
    shot("p10-04-print-check")
    target = os.path.join(WORK, "fixed.3mf")
    if os.path.exists(target):
        os.unlink(target)
    QtWidgets.QFileDialog.getSaveFileName = staticmethod(lambda *a, **k: (target, "3MF (*.3mf)"))
    dlg.export(fix=True)
    written = Mesh.Mesh(target) if os.path.isfile(target) else None
    return {"ok": len(texts) >= 2 and report["holes"] and written is not None and written.isSolid(),
            "band": texts, "report": report, "written_solid": bool(written and written.isSolid())}


check("dxf", dxf)
check("stl", stl)
with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items()}
