# P0「行き止まりを無くす」の受け入れ: 2 章で止まった操作を GUI の中でもう一度行い、
# 英語・モーダル・崩れた図が出ないことを確かめて画面を撮る。
# 使い方: guictl start --fresh → guictl py - < p0_walkthrough.py（結果は OUT/result.json と画像）
import json
import os
import traceback

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P0_OUT", "/tmp/p0-accept")
WORK = os.environ.get("P0_WORK", "/tmp/p0-work")
os.makedirs(WORK, exist_ok=True)
results = {}
App.ParamGet("User parameter:BaseApp/Preferences/Dialog").SetBool("DontUseNativeDialog", True)


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(400)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def modal_texts():
    """Visible dialogs and message boxes (should be none after each step)"""
    found = []
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.isVisible() and isinstance(w, (QtWidgets.QDialog, QtWidgets.QMessageBox)):
            found.append((w.windowTitle(), getattr(w, "text", lambda: "")()))
    return found


def close_modals():
    for w in QtWidgets.QApplication.topLevelWidgets():
        if w.isVisible() and isinstance(w, QtWidgets.QDialog):
            w.reject()


def step(name):
    def wrap(fn):
        try:
            results[name] = fn()
        except Exception:
            results[name] = {"ok": False, "error": traceback.format_exc()[-1500:]}
        close_modals()
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
        return fn

    return wrap


def accept_task():
    """作業パネルの OK を押す（利用者と同じ経路）"""
    for box in QtWidgets.QApplication.allWidgets():
        if isinstance(box, QtWidgets.QDialogButtonBox) and box.isVisible():
            ok = box.button(QtWidgets.QDialogButtonBox.Ok)
            if ok and ok.isEnabled():
                ok.click()
                pump(800)
                return True
    return False


def new_doc(name):
    doc = App.newDocument(name)
    App.setActiveDocument(doc.Name)
    Gui.activeDocument().activeView().viewIsometric()
    return doc


def box_body(doc, x=80, y=50, z=5):
    body = doc.addObject("PartDesign::Body", "Body")
    box = doc.addObject("PartDesign::AdditiveBox", "Box")
    body.addObject(box)
    box.Length, box.Width, box.Height = x, y, z
    doc.recompute()
    return body


# ① .stl の書き出しは Mesh へ（FEM の英語エラーにならない）
@step("stl_export")
def _():
    doc = new_doc("plate")
    body = box_body(doc)
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, body.Name)
    target = os.path.join(WORK, "plate.stl")
    if os.path.exists(target):
        os.unlink(target)
    seen = {}

    def fill():
        for w in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(w, QtWidgets.QFileDialog) and w.isVisible():
                seen["filter"] = w.selectedNameFilter()
                # 利用者と同じく、名前の欄に打って Enter
                edit = w.findChild(QtWidgets.QLineEdit, "fileNameEdit")
                edit.setText(target)
                QtTest = __import__("PySide6.QtTest", fromlist=["QTest"])
                QtTest.QTest.keyClick(edit, QtCore.Qt.Key_Return)
                return
        QtCore.QTimer.singleShot(200, fill)

    QtCore.QTimer.singleShot(300, fill)
    Gui.runCommand("Std_Export")
    pump(1500)
    msgs = modal_texts()
    shot("p0-01-stl-exported")
    import Mesh

    ok = os.path.isfile(target)
    facets = Mesh.Mesh(target).CountFacets if ok else 0
    return {"ok": ok and facets > 0 and not msgs, "facets": facets, "dialog_filter": seen.get("filter"), "modals": msgs}


# ② 組立: 保存していない文書に、保存していない STEP の部品を置く（英語のダイアログ無し、最初の部品は動かない）
@step("assembly_insert")
def _():
    src = new_doc("pin_src")
    import Part

    pin = src.addObject("Part::Cylinder", "Pin")
    pin.Radius, pin.Height = 3, 20
    src.recompute()
    step_path = os.path.join(WORK, "pin.step")
    import Import

    Import.export([pin], step_path)
    App.closeDocument(src.Name)
    # STEP を開く（保存していない別の文書になる）
    Import.open(step_path)
    step_doc = App.ActiveDocument
    step_label = [o.Label for o in step_doc.Objects]
    asm_doc = new_doc("組立")
    Gui.runCommand("Assembly_CreateAssembly")
    pump(500)
    asm = [o for o in asm_doc.Objects if o.isDerivedFrom("Assembly::AssemblyObject")][0]
    Gui.runCommand("Assembly_InsertLink")
    pump(800)
    panel = Gui.Control.activeDialog() and getattr(Gui.Control, "activeTaskDialog", lambda: None)()
    # パネルの木から STEP の部品を探してクリックする（利用者のクリックと同じ経路）
    import CommandInsertLink

    task = None
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, QtWidgets.QTreeWidget) and w.isVisible() and w.objectName() == "partList":
            tree = w
            break
    else:
        tree = None
    clicked = None
    if tree is not None:
        it = QtWidgets.QTreeWidgetItemIterator(tree)
        while it.value():
            item = it.value()
            part = item.data(0, QtCore.Qt.UserRole)
            if part is not None and getattr(part, "Document", None) == step_doc and part.TypeId != "App::Part":
                clicked = item.text(0)
                tree.itemClicked.emit(item, 0)
                break
            it += 1
    pump(800)
    msgs = modal_texts()
    shot("p0-02-assembly-inserted")
    Gui.Control.closeDialog() if Gui.Control.activeDialog() else None
    pump(300)
    grounded = [o for o in asm_doc.Objects if hasattr(o, "ObjectToGround")]
    parts = [o.Label for o in asm.Group if o.isDerivedFrom("Part::Feature") or o.isDerivedFrom("App::Link")]
    return {
        "ok": bool(clicked) and not msgs and bool(grounded),
        "step_labels": step_label,
        "clicked": clicked,
        "parts": parts,
        "grounded": [g.Label for g in grounded],
        "assembly_file": asm_doc.FileName,
        "modals": msgs,
    }


# ③④ DXF: 開くときに聞かない。線を選んで押し出すと部品になる（「アクティブな部品が必要」が出ない）
DXF = """0
SECTION
2
ENTITIES
{}0
ENDSEC
0
EOF
"""


def dxf_line(x1, y1, x2, y2):
    return "0\nLINE\n8\n0\n10\n{}\n20\n{}\n30\n0\n11\n{}\n21\n{}\n31\n0\n".format(x1, y1, x2, y2)


@step("dxf_extrude")
def _():
    path = os.path.join(WORK, "plate.dxf")
    with open(path, "w") as f:
        f.write(DXF.format(dxf_line(0, 0, 80, 0) + dxf_line(80, 0, 80, 50) + dxf_line(80, 50, 0, 50) + dxf_line(0, 50, 0, 0)))
    import importDXF

    QtCore.QTimer.singleShot(1500, lambda: results.setdefault("dxf_open_modals", modal_texts()))
    importDXF.open(path)
    pump(500)
    doc = App.ActiveDocument
    Gui.activeDocument().activeView().viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    open_msgs = modal_texts() or results.pop("dxf_open_modals", [])
    lines = [o for o in doc.Objects if o.isDerivedFrom("Part::Feature")]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, lines[0].Name, "Edge1")
    shot("p0-03-dxf-line-selected")
    Gui.runCommand("PartDesign_Pad")
    pump(1500)
    pad_msgs = modal_texts()
    shot("p0-04-dxf-pad-panel")
    accept_task()
    doc.recompute()
    pads = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Pad")]
    vol = pads[0].Shape.Volume if pads else 0
    shot("p0-05-dxf-padded")
    return {"ok": not open_msgs and not pad_msgs and vol > 0, "objects": len(lines), "pad_volume": vol,
            "open_modals": open_msgs, "pad_modals": pad_msgs}


@step("dxf_broken")
def _():
    path = os.path.join(WORK, "broken.dxf")
    with open(path, "w") as f:
        f.write("this is not a drawing\n")
    import importDXF

    seen = []

    class Obs:
        def __init__(self):
            self.text = []

    log = []
    App.Console.PrintLog("")  # 何もしない（通知の欄に出たかは画面で見る）
    importDXF.open(path)
    pump(800)
    shot("p0-06-dxf-broken")
    return {"ok": not modal_texts(), "modals": modal_texts()}


# ⑤ 三面図: 正面が今の 3D の向き（等角）にならず、尺度は自動でページに収まる
@step("three_view")
def _():
    doc = new_doc("ベース板")
    body = box_body(doc)
    Gui.activeDocument().activeView().viewIsometric()
    Gui.runCommand("TechDraw_PageDefault")
    pump(800)
    page = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawPage")][0]
    Gui.Selection.clearSelection()
    Gui.Selection.addSelection(doc.Name, body.Name)
    Gui.runCommand("TechDraw_ProjectionGroup")
    pump(1500)
    shot("p0-07a-three-view-panel")
    accept_task()
    pump(500)
    doc.recompute()
    group = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawProjGroup")][0]
    anchor = group.Anchor
    direction = tuple(round(c, 6) for c in anchor.Direction)
    tpl = page.Template
    width, height = float(tpl.Width), float(tpl.Height)
    inside = True
    for v in group.Views:
        bb = v.getBoundingBox() if hasattr(v, "getBoundingBox") else None
    Gui.SendMsgToActiveView("ViewFit")
    shot("p0-07-three-view")
    return {
        # 正面は板の広い面、尺度は標準の尺度でページに収まる（80×50×5 の板なら A4 横に 2:1）
        "ok": direction == (0.0, 0.0, 1.0) and group.Scale == 2.0 and len(group.Views) == 3,
        "direction": direction,
        "scale_type": group.ScaleType,
        "scale": group.Scale,
        "views": [v.Label for v in group.Views],
        "page": (width, height),
    }


# ⑦ STEP の名前: 製品名の無い STEP（FreeCAD が書いたもの）はファイル名
@step("step_name")
def _():
    src = new_doc("bracket_src")
    b = src.addObject("Part::Box", "Box")
    src.recompute()
    path = os.path.join(WORK, "bracket.step")
    # Written without a product name (as Open CASCADE writes a bare shape): the part is named
    # "Open CASCADE STEP translator 8.0 1" in the file
    b.Shape.exportStep(path)
    App.closeDocument(src.Name)
    import ImportGui

    ImportGui.open(path)
    doc = App.ActiveDocument
    labels = [o.Label for o in doc.Objects]
    return {"ok": not any("Open CASCADE" in l for l in labels) and "bracket" in labels and doc.Label == "bracket",
            "labels": labels, "document": doc.Label}


# ⑨ 言葉: 用語表に合わせた訳
@step("terms")
def _():
    tr = QtCore.QCoreApplication.translate
    got = {
        "Additive Loft": tr("CmdPartDesignAdditiveLoft", "Additive Loft"),
        "Multi-Transform": tr("CmdPartDesignMultiTransform", "Multi-Transform"),
        "Parallel": tr("CmdSketcherConstrainParallel", "Parallel Constraint"),
        "Solve": tr("Assembly_SolveAssembly", "Solve Assembly"),
        "Ground": tr("Assembly_ToggleGrounded", "Toggle Grounded"),
        "Datum Plane": tr("CmdPartDesignPlane", "Datum Plane"),
        "Projection Group": tr("CmdTechDrawProjectionGroup", "Projection Group"),
        "Ask AI": tr("DesignCheck", "Ask AI"),
    }
    bad = [k for k, v in got.items() if any(w in v for w in ("加算", "マルチ変換", "並行", "求解", "接地", "データム", "投影グループ", "相談"))]
    return {"ok": not bad, "got": got, "bad": bad}


with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1, default=str)
{k: v.get("ok") for k, v in results.items() if isinstance(v, dict)}
