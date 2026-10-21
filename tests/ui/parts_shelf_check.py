# 部品の棚（0.6.6）の受け入れ: 本物のクリック（xdotool）で穴を選び、横の帯の「ねじを入れる」→ パネルの「入れる」、
# パネルを開いたまま別の穴をクリック、アルミフレームを 2 点で、会社の部品を面に、Ctrl+K の「ナット」。画面も撮る。
# 使い方: KANTAN_GUI_DISPLAY=:197 KANTAN_GUI_STATE=/tmp/ps-gui guictl start --fresh
#         → guictl py - < parts_shelf_check.py（60 秒を超えるので中で QTimer から走らせる。結果は OUT/result.json）
import json
import os
import shutil
import subprocess
import tempfile
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("SHELF_OUT", os.path.expanduser("~/freecad-ja-unified/docs/ui-redesign/accept/parts-shelf"))
os.makedirs(OUT, exist_ok=True)
results = {}


def pump(ms=150):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(400)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def xdo(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], check=True)
    pump(60)


def view():
    return Gui.ActiveDocument.ActiveView


def to_screen(coin_xy):
    w = view().graphicsView()
    g = w.viewport().mapToGlobal(QtCore.QPoint(0, 0))
    _w, h = view().getSize()
    return g.x() + int(coin_xy[0]), g.y() + (h - 1 - int(coin_xy[1]))


def click_screen(x, y):
    xdo("mousemove", x, y)
    pump(150)
    xdo("click", 1)
    pump(400)


def find_pixel(near, test, radius=40):
    """A pixel of the 3D view near the point `near` where getObjectInfo passes test(info)"""
    cx, cy = view().getPointOnViewport(near)
    for r in range(0, radius, 2):
        for dx in range(-r, r + 1, 2):
            for dy in (-r, r) if abs(dx) != r else range(-r, r + 1, 2):
                info = view().getObjectInfo((int(cx + dx), int(cy + dy)))
                if info and test(info):
                    return (int(cx + dx), int(cy + dy)), info
    return None, None


def element_of(info):
    root = info.get("ParentObject")
    sub = info.get("SubName")
    if root is None or not sub:
        root = App.ActiveDocument.getObject(info["Object"])
        sub = info.get("Component")
    try:
        return root.getSubObject(sub) if root is not None and sub else None
    except Exception:
        return None


def is_cylinder(diameter):
    def test(info):
        f = element_of(info)
        return (f is not None and f.ShapeType == "Face" and isinstance(f.Surface, Part.Cylinder)
                and abs(2 * f.Surface.Radius - diameter) < 1e-6)
    return test


def is_object(name):
    return lambda info: info.get("Object") == name or getattr(info.get("ParentObject"), "Name", None) == name


def button(parent_name, text):
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, QtWidgets.QAbstractButton) and w.isVisible() and w.text().replace("&", "") == text:
            p = w
            while p is not None and p.objectName() != parent_name:
                p = p.parentWidget()
            if p is not None or parent_name is None:
                return w
    return None


def click_widget(w):
    g = w.mapToGlobal(w.rect().center())
    click_screen(g.x(), g.y())


def panel():
    for w in QtWidgets.QApplication.allWidgets():
        if w.objectName() == "PartsShelfPanel" and w.isVisible():
            return w
    return None


def links(doc):
    return [o for o in doc.Objects if o.isDerivedFrom("App::Link")]


def make_scene():
    doc = App.newDocument("Shelf")
    block = Part.makeBox(80, 50, 30)
    block = block.cut(Part.makeCylinder(2.5, 15, App.Vector(20, 25, 15)))  # M6 の下穴 ⌀5、深さ 15
    b = doc.addObject("Part::Feature", "Block")
    b.Shape = block
    b.Label = "ベース"
    plate = Part.makeBox(40, 50, 10, App.Vector(0, 0, 30)).cut(Part.makeCylinder(3.3, 12, App.Vector(20, 25, 29)))
    p = doc.addObject("Part::Feature", "Plate")
    p.Shape = plate  # M6 のキリ穴 ⌀6.6、2 級
    p.Label = "押さえ板"
    # 部品（Body）の中の穴: ⌀9 の通し穴（M8 のキリ穴）
    body = doc.addObject("PartDesign::Body", "Body")
    base = doc.addObject("Part::Feature", "BracketShape")
    base.Shape = Part.makeBox(30, 30, 12, App.Vector(100, 0, 0)).cut(Part.makeCylinder(4.5, 14, App.Vector(115, 15, -1)))
    body.BaseFeature = base
    base.Visibility = False
    body.Label = "ブラケット"
    doc.recompute()
    Gui.SendMsgToActiveView("ViewFit")
    Gui.ActiveDocument.ActiveView.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")
    pump(500)
    return doc


def step():
    doc = App.ActiveDocument
    mw = Gui.getMainWindow()

    # 1. 道具の列の「部品の棚」
    strip = button(None, "部品の棚")
    results["strip_button"] = strip is not None
    shot("01-tool-strip")

    # 2. 穴を本物のクリックで選ぶ → 横の帯に「ねじを入れる」
    px, info = find_pixel(App.Vector(20, 25, 36), is_cylinder(6.6))
    results["hole_pixel"] = px
    sx, sy = to_screen(px)
    click_screen(sx, sy)
    sel = Gui.Selection.getSelectionEx("", 0)
    results["picked"] = [(s.Object.Name, list(s.SubElementNames)) for s in sel]
    bar_button = button("UnifiedContextBar", "ねじを入れる")
    results["context_bar_offers_insert_screw"] = bar_button is not None
    shot("02-hole-picked-context-bar")

    # 3. 「ねじを入れる」→ パネル（穴の説明と入るもの）→「入れる」
    click_widget(bar_button)
    pump(800)
    p = panel()
    results["panel_open"] = p is not None
    hole_label = [w for w in QtWidgets.QApplication.allWidgets() if w.objectName() == "PartsShelfHole"][0]
    results["panel_hole_text"] = hole_label.text()
    shot("03-panel-suggestion")
    click_widget(button(None, "入れる"))
    pump(800)
    ls = links(doc)
    results["after_insert"] = [(l.Label, l.LinkedObject.Label, l.LinkedObject.Standard) for l in ls]
    screw = [l for l in ls if "六角穴付きボルト" in l.LinkedObject.Label]
    if screw:
        pl = screw[0].Placement
        axis = pl.Rotation.multVec(App.Vector(0, 0, -1))
        results["screw_axis"] = [round(axis.x, 9), round(axis.y, 9), round(axis.z, 9)]
        results["screw_origin"] = [round(v, 6) for v in pl.Base]
        bb = screw[0].Shape.BoundBox
        results["screw_bottom_z"] = round(bb.ZMin, 6)
    Gui.Selection.clearSelection()
    shot("04-screw-inserted")

    # 4. パネルを開いたまま: 座金にチェック → 今のねじが変わる
    washers = button(None, "頭の下に座金（平座金とばね座金）")
    click_widget(washers)
    pump(800)
    results["after_washers"] = sorted(l.LinkedObject.Label for l in links(doc))
    shot("05-with-washers")

    # 5. 部品（Body）の中の ⌀9 の通し穴をクリック → M8 とナット
    px, info = find_pixel(App.Vector(115, 15, 6), is_cylinder(9.0))
    results["body_hole_pixel"] = px
    sx, sy = to_screen(px)
    click_screen(sx, sy)
    pump(800)
    results["after_body_hole"] = sorted(l.LinkedObject.Label for l in links(doc))
    results["message"] = [w for w in QtWidgets.QApplication.allWidgets() if w.objectName() == "PartsShelfMessage"][0].text()
    shot("06-body-hole-with-nut")

    # 6. アルミフレーム: 棚で選び、ベースの上面の 2 点をクリック（1 点目の後は影がカーソルについてくる）
    tree = [w for w in QtWidgets.QApplication.allWidgets() if w.objectName() == "PartsShelfList"][0]
    it = QtWidgets.QTreeWidgetItemIterator(tree)
    while it.value():
        if it.value().data(0, QtCore.Qt.UserRole) == "profile":
            tree.setCurrentItem(it.value())
            break
        it += 1
    pump(300)
    a, b = App.Vector(55, 8, 30), App.Vector(55, 45, 30)
    pa, _ = find_pixel(a, is_object("Block"))
    pb, _ = find_pixel(b, is_object("Block"))
    sa, sb = to_screen(pa), to_screen(pb)
    click_screen(*sa)
    xdo("mousemove", (sa[0] + sb[0]) // 2, (sa[1] + sb[1]) // 2)
    pump(500)
    shot("07-profile-ghost")
    click_screen(*sb)
    pump(800)
    prof = [l for l in links(doc) if l.LinkedObject.ShelfKind == "profile"]
    if prof:
        bb = prof[0].Shape.BoundBox
        results["profile"] = {"label": prof[0].LinkedObject.Label, "zmin": round(bb.ZMin, 3), "zmax": round(bb.ZMax, 3),
                              "length": round(max(bb.XLength, bb.YLength, bb.ZLength), 3), "valid": prof[0].Shape.isValid()}
    shot("08-profile-placed")

    # 7. 会社の部品: フォルダー（STEP と shelf.csv）を設定して棚を開き直し、ブラケットの上面に置く
    folder = tempfile.mkdtemp(prefix="company-shelf-")
    lpart = Part.makeBox(20, 4, 15).fuse(Part.makeBox(20, 15, 4))
    lpart.exportStep(os.path.join(folder, "angle.step"))
    with open(os.path.join(folder, "shelf.csv"), "w", encoding="utf-8") as f:
        f.write("ファイル,名前,分類,別名,品番\nangle.step,L 金具 20,金具,アングル,KB-020\n")
    App.ParamGet("User parameter:BaseApp/Preferences/Mod/Unified/PartsShelf").SetString("CompanyFolders", folder)
    Gui.Control.closeDialog()
    for _ in range(50):
        pump(100)
        if not Gui.Control.activeDialog():
            break
    Gui.runCommand("Unified_PartsShelf")
    pump(800)
    tree = [w for w in QtWidgets.QApplication.allWidgets() if w.objectName() == "PartsShelfList"][0]
    it = QtWidgets.QTreeWidgetItemIterator(tree)
    while it.value():
        if it.value().data(0, QtCore.Qt.UserRole) == "company":
            tree.setCurrentItem(it.value())
            break
        it += 1
    pump(300)
    pc, _ = find_pixel(App.Vector(105, 5, 12), lambda i: "Body" in str(i.get("Object")) or "Bracket" in str(i.get("Object"))
                       or getattr(i.get("ParentObject"), "Name", "") == "Body")
    results["company_pixel"] = pc
    if pc:
        click_screen(*to_screen(pc))
        pump(800)
    comp = [l for l in links(doc) if l.LinkedObject.ShelfKind == "company"]
    results["company"] = [(l.LinkedObject.Label, l.LinkedObject.PartNumber, round(l.Shape.BoundBox.ZMin, 3)) for l in comp]
    shot("09-company-part")
    Gui.Control.closeDialog()
    shutil.rmtree(folder, ignore_errors=True)

    # 8. Ctrl+K で「ナット」→ 部品の棚が見つかる → Enter でナットを選んだ棚
    Gui.Selection.clearSelection()
    mw.activateWindow()
    view().graphicsView().setFocus()
    pump(200)
    xdo("key", "ctrl+k")
    pump(500)
    focus = QtWidgets.QApplication.focusWidget()
    results["search_focus"] = type(focus).__name__
    if isinstance(focus, QtWidgets.QLineEdit):
        focus.setText("ナット")
        pump(600)
    shot("10-search-nut")
    lists = [w for w in QtWidgets.QApplication.allWidgets() if isinstance(w, QtWidgets.QListWidget) and w.isVisible()]
    results["search_rows"] = [lists[0].item(i).text() for i in range(min(5, lists[0].count()))] if lists else []
    xdo("key", "Return")
    pump(1200)
    tree = [w for w in QtWidgets.QApplication.allWidgets() if w.objectName() == "PartsShelfList" and w.isVisible()]
    results["shelf_from_search"] = tree[0].currentItem().text(0) if tree and tree[0].currentItem() else None
    shot("11-shelf-from-search")
    Gui.Control.closeDialog()

    # 9. 部品表に載る名前（元の形の一覧）
    import PartsShelf

    results["originals"] = sorted((o.Label, o.Standard, o.Size) for o in PartsShelf.originals(doc))
    results["link_count"] = len(links(doc))


def main():
    try:
        mw = Gui.getMainWindow()
        mw.showMaximized()
        pump(500)
        # 初回の画面（言語・単位）は閉じる
        start = button(None, "始める")
        if start is not None:
            click_widget(start)
            pump(500)
        make_scene()
        step()
    except Exception:
        results["error"] = traceback.format_exc()
    json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, ensure_ascii=False, default=str)


QtCore.QTimer.singleShot(0, main)
print("started; results in", OUT)
