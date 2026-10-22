# 0.7.1 の受け入れ: 使い勝手の試験（docs/ui-redesign/usability-0.6.9/report.md）で起きたことを、本物のマウスとキー（xdotool）で
# もう一度やって、直ったことを確かめる。画像と result.json は accept/U071/。
# 使い方: KANTAN_GUI_DISPLAY=:263 KANTAN_GUI_STATE=/tmp/p11gui guictl start --fresh → guictl py - < u071_check.py
import os
exec(open(os.path.join(os.path.expanduser("~/freecad-ja-unified/tests/ui"), "u071_common.py")).read())

results = {}
CASES = os.environ.get("U071_CASES", "")


def links(doc):
    return [o for o in doc.Objects if o.isDerivedFrom("App::Link")]


def grounded(doc):
    return [o.ObjectToGround.Name for o in doc.Objects if getattr(o, "ObjectToGround", None) is not None]


def press_done():
    b = mw().findChild(QtWidgets.QPushButton, "UnifiedStepDone")
    if b is not None and b.isVisible():
        click_widget(b)
    pump(800)


def bar_button(command):
    bar = mw().findChild(QtWidgets.QFrame, "UnifiedContextBar")
    if bar is None or not bar.isVisible():
        return None
    for b in bar.findChildren(QtWidgets.QToolButton):
        if b.isVisible() and b.property("unifiedCommand") == command:
            return b
    return None


# ------------------------------------------------------------- 1, 2: the assembly


def case_assembly():
    out = {}
    close_all()
    block("柱", 20, 20, 50)
    plate = block("板", 100, 60, 15)
    App.setActiveDocument(plate.Name)
    Gui.ActiveDocument = Gui.getDocument(plate.Name)
    fit()
    Gui.runCommand("Unified_PlacePart")
    pump(1500)
    t = mw().findChild(QtWidgets.QTreeWidget, "partList")
    top = [t.topLevelItem(k) for k in range(t.topLevelItemCount()) if t.topLevelItem(k).text(0) == "柱"][0]
    r = t.visualItemRect(top.child(0))
    c = t.viewport().mapToGlobal(r.center())
    click(c.x(), c.y())
    pump(800)
    press_done()
    body = plate.getObject("Body")
    out["plate_in_assembly_and_held"] = grounded(plate) == ["Body"]
    out["placed_part_free"] = len(links(plate)) == 1 and links(plate)[0].Name not in grounded(plate)
    fit()
    shot("01-assembly-plate-held")
    plate_pl = App.Placement(body.Placement)
    link = links(plate)[0]
    # The plate first, then the pillar (the order that used to turn the plate over)
    lb = link.Shape.BoundBox
    plate_top = pick_pixel([App.Vector(70, 40, 15), App.Vector(60, 30, 15), App.Vector(80, 20, 15)],
                           lambda i: i.get("Component", "").startswith("Face") and "Body" in (i.get("SubName", "") + i.get("Object", "")))
    col_top = pick_pixel([App.Vector(lb.Center.x, lb.Center.y, lb.ZMax)], lambda i: i.get("Component", "").startswith("Face"))
    out["picks_found"] = bool(plate_top and col_top)
    Gui.Selection.clearSelection()
    click(*plate_top)
    click(*col_top, ctrl=True)
    pump(600)
    b = bar_button("Unified_SnapFaces")
    if b is not None:
        click_widget(b)
    else:
        Gui.runCommand("Unified_SnapFaces")
    pump(1500)
    shot("02-snap-plate-first")
    press_done()
    body = plate.getObject("Body")
    out["plate_not_moved"] = body.Placement.isSame(plate_pl, 1e-6)
    out["plate_not_turned_over"] = abs(body.Placement.Rotation.Angle) < 1e-6
    lb = link.Shape.BoundBox
    out["pillar_on_the_plate"] = abs(lb.ZMin - 15) < 1e-4 and 0 - 1e-4 <= lb.XMin and lb.XMax <= 100 + 1e-4
    out["pillar_box"] = [round(v, 2) for v in (lb.XMin, lb.YMin, lb.ZMin, lb.XMax, lb.YMax, lb.ZMax)]
    shot("03-pillar-on-plate")
    # Ctrl+C / Ctrl+V on the pillar
    Gui.Selection.clearSelection()
    px = pick_pixel([App.Vector(lb.Center.x, lb.Center.y, lb.ZMax)], lambda i: i.get("Component", "").startswith("Face"))
    click(*px)
    xdo("key", "ctrl+c")
    xdo("key", "ctrl+v")
    pump(1200)
    out["ctrl_v_puts_another"] = len(links(plate)) == 2
    shot("04-ctrl-v-another")
    plate.undo()
    plate.recompute()
    pump(500)
    out["undo_takes_it_back"] = len(links(plate)) == 1
    # four corners: move the pillar to the corner, then 2 × 2
    link.Placement.Base = link.Placement.Base + App.Vector(-lb.XMin, -lb.YMin, 0)
    plate.recompute()
    Gui.Selection.clearSelection()
    lb = link.Shape.BoundBox
    fit()
    px = pick_pixel([App.Vector(lb.Center.x, lb.Center.y, lb.ZMax)], lambda i: i.get("Component", "").startswith("Face"))
    click(*px)
    pump(500)
    b = bar_button("Unified_GridCopies")
    out["grid_on_the_bar"] = b is not None
    barw = mw().findChild(QtWidgets.QFrame, "UnifiedContextBar")
    out["bar_tools"] = [x.property("unifiedCommand") for x in barw.findChildren(QtWidgets.QToolButton) if x.isVisible()] if barw else None
    import AssemblyCopiesGui
    out["picked_parts"] = [o.Name for o in AssemblyCopiesGui.picked_parts()]
    out["sel"] = [(x.Object.Name, x.SubElementNames) for x in Gui.Selection.getSelectionEx("", 0)]
    if b is not None:
        click_widget(b)
    else:
        Gui.runCommand("Unified_GridCopies")
    pump(1000)
    form = mw().findChild(QtWidgets.QSpinBox, "UnifiedGridColumns")
    if form is not None:
        mw().findChild(QtWidgets.QDoubleSpinBox, "UnifiedGridDX").setValue(80)
        mw().findChild(QtWidgets.QDoubleSpinBox, "UnifiedGridDY").setValue(40)
        shot("05-grid-panel")
        press_done()
    places = sorted((round(o.Shape.BoundBox.XMin), round(o.Shape.BoundBox.YMin)) for o in links(plate))
    out["grid_places"] = places
    out["four_corners"] = places == [(0, 0), (0, 40), (80, 0), (80, 40)]
    fit()
    shot("06-four-corners")
    # a double-click on a part in the tree: picked, not opened in its own file
    import HistoryLineGui as H

    tree = [x for x in H.trees() if x.isVisible()][0]
    found = []

    def walk(idx):
        m = tree.model()
        for k in range(m.rowCount(idx)):
            ch = m.index(k, 0, idx)
            o = H.object_of(ch)
            if o is not None and o.isDerivedFrom("App::Link"):
                found.append(ch)
            walk(ch)

    walk(QtCore.QModelIndex())
    if found:
        r = tree.visualRect(found[-1])
        c = tree.viewport().mapToGlobal(r.center())
        xdo("mousemove", c.x(), c.y())
        xdo("click", "--repeat", 2, "--delay", 80, 1)
        pump(1000)
    out["tree_double_click_stays"] = App.ActiveDocument.Name == plate.Name
    shot("07-tree-double-click")
    return out



def plate_doc(name="板", holes=(), fillet=0.0):
    """A 100 × 60 × 15 plate; holes: [(x, y)] ⌀6 through (pockets of circles); R fillet on the corners"""
    import Sketcher

    close_all()
    doc = block(name, 100, 60, 15, save=False)
    body = doc.getObject("Body")
    tip = body.Tip
    if holes:
        sk = body.newObject("Sketcher::SketchObject", "SketchHoles")
        sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
        sk.MapMode = "FlatFace"
        for x, y in holes:
            sk.addGeometry(Part.Circle(App.Vector(x, y, 0), App.Vector(0, 0, 1), 3))
        pk = body.newObject("PartDesign::Pocket", "Pocket")
        pk.Profile = sk
        pk.Type = 1
        pk.Reversed = True
        doc.recompute()
        sk.ViewObject.Visibility = False
    if fillet:
        tip = body.Tip
        shape = tip.Shape
        vert = ["Edge%d" % (i + 1) for i, e in enumerate(shape.Edges)
                if type(e.Curve).__name__ == "Line" and abs(App.Vector(e.Curve.Direction).z) > 0.999
                and len(shape.ancestorsOfType(e, Part.Face)) == 2]
        f = body.newObject("PartDesign::Fillet", "Fillet")
        f.Base = (tip, vert)
        f.Radius = fillet
        doc.recompute()
    fit()
    return doc, body


def top_face_pixel(doc, points):
    return pick_pixel([App.Vector(*p) for p in points],
                      lambda i: i.get("Component", "").startswith("Face"))


# ------------------------------------------------------------- 4: more holes, positions in numbers


def case_holes():
    out = {}
    doc, body = plate_doc("穴の板")
    px = top_face_pixel(doc, [(10, 10, 15), (12, 12, 15)])
    click(*px)
    pump(500)
    b = bar_button("Unified_Hole")
    if b is not None:
        click_widget(b)
    else:
        Gui.runCommand("Unified_Hole")
    pump(2500)
    for p in ((90, 10, 15), (10, 50, 15), (90, 50, 15)):
        q = top_face_pixel(doc, [p, (p[0] - 2, p[1] - 2, 15)])
        if q:
            click(*q)
            pump(1500)
    import HoleMultiGui

    hm = HoleMultiGui.current()
    out["four_holes_by_clicks"] = hm is not None and len(hm.points()) == 4
    box = mw().findChild(QtWidgets.QGroupBox, "UnifiedHolePositions")
    out["positions_on_panel"] = box is not None and box.isVisible()
    if box is not None:
        fx = box.findChildren(QtWidgets.QLineEdit, "UnifiedHoleX")[0]
        fy = box.findChildren(QtWidgets.QLineEdit, "UnifiedHoleY")[0]
        for f, v in ((fx, "10"), (fy, "10")):
            click_widget(f)
            xdo("key", "ctrl+a")
            xdo("type", v)
        xdo("key", "Return")
        pump(1500)
        shot("10-holes-panel", box.window())
    pts = sorted((round(g.X - hm.origin.x, 2), round(g.Y - hm.origin.y, 2)) for _i, g in hm.points()) if hm else []
    out["typed_position"] = (10.0, 10.0) in pts
    out["points"] = pts
    press_done()
    hole = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Hole")]
    cyl = [f for f in hole[0].Shape.Faces if type(f.Surface).__name__ == "Cylinder"] if hole else []
    out["four_holes_made"] = len(cyl) == 4
    shot("11-four-holes")
    return out


# ------------------------------------------------------------- 6: "3" and Enter after "same direction"


def case_type_radius():
    out = {}
    doc, body = plate_doc("丸めの板", holes=[(20, 20)])
    tip = body.Tip
    edge = pick_pixel([App.Vector(100, 0, 7.5), App.Vector(0, 0, 7.5), App.Vector(100, 60, 7.5)],
                      lambda i: i.get("Component", "").startswith("Edge"))
    Gui.Selection.clearSelection()
    click(*edge)
    pump(600)
    b = bar_button("Unified_SelectParallelEdges")
    out["same_direction_on_bar"] = b is not None
    if b is not None:
        click_widget(b)
    pump(900)
    picks = [s for x in Gui.Selection.getSelectionEx() for s in x.SubElementNames]
    out["four_edges_no_seam"] = len(picks) == 4
    bar = mw().findChild(QtWidgets.QFrame, "UnifiedContextBar")
    out["bar_stays"] = bar is not None and bar.isVisible()
    shot("20-bar-stays")
    rot = view().getCameraOrientation()
    viewport().setFocus()
    xdo("mousemove", *edge)
    xdo("type", "3")
    pump(300)
    out["view_not_turned"] = view().getCameraOrientation().isSame(rot, 1e-9) if hasattr(rot, "isSame") else str(view().getCameraOrientation()) == str(rot)
    xdo("key", "Return")
    pump(2000)
    fil = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Fillet")]
    out["fillet_r3_four_edges"] = bool(fil) and abs(fil[0].Radius.Value - 3) < 1e-9 and len(fil[0].Base[1]) == 4
    shot("21-fillet-r3")
    return out


# ------------------------------------------------------------- 3, 7: the drawing


def case_drawing():
    out = {}
    doc, body = plate_doc("図面の板", holes=[(10, 10), (90, 10), (10, 50), (90, 50)], fillet=5)
    doc.saveAs(os.path.join(WORK, "図面の板.FCStd"))
    Gui.runCommand("Unified_NewDrawing")
    pump(6000)
    dims = [d for d in doc.Objects if d.isDerivedFrom("TechDraw::DrawViewDimension")]
    dia = [d for d in dims if d.Type == "Diameter"]
    out["one_hole_callout"] = len(dia) == 1 and dia[0].FormatSpec.startswith("4×") and abs(dia[0].getRawValue() - 6) < 1e-6
    pos = sorted(round(d.getRawValue(), 2) for d in dims if d.Type in ("DistanceX", "DistanceY")
                 and d.References2D and d.References2D[0][1][0].startswith("Edge"))
    out["hole_positions"] = pos
    out["hole_positions_ok"] = pos == [10.0, 10.0, 50.0, 90.0]
    tpl = [o for o in doc.Objects if o.isDerivedFrom("TechDraw::DrawSVGTemplate")]
    text = open(tpl[0].Template, encoding="utf-8").read() if tpl else ""
    out["title_block_japanese"] = "表題" in text and ">Title:<" not in text
    shot("30-drawing")
    # Ctrl+K "寸法": each row says where it works
    import CommandSearchGui as G

    viewport().setFocus() if False else None
    xdo("key", "ctrl+k")
    pump(600)
    pop = G.popup()
    field = pop.findChild(QtWidgets.QLineEdit) if pop is not None else None
    titles = []
    if field is not None:
        field.setText("寸法")
        pump(800)
        lw = pop.findChild(QtWidgets.QListWidget)
        titles = [lw.item(k).text().split("\n")[0] for k in range(min(8, lw.count()))]
        shot("31-search-dimension", pop, 4)
        xdo("key", "Escape")
    out["search_titles"] = titles
    out["search_rows_differ"] = bool(titles) and len(set(titles)) == len(titles)
    return out


# ------------------------------------------------------------- 5: DXF with a frame


def case_dxf():
    out = {}
    close_all()
    src = "/home/shota/jww-corpus/extract/vector-se350214/Sakura-type_mark1.dxf"
    if not os.path.isfile(src):
        return {"skipped": True}
    warnings = []

    class Obs:
        def __init__(self):
            pass

    import UnifiedFiles
    import importDXF

    importDXF.open(src)
    pump(3000)
    docs = [d for d in App.listDocuments().values() if d.Label.startswith("Sakura")]
    doc = docs[0] if docs else App.ActiveDocument
    band = mw().findChild(QtWidgets.QWidget, "UnifiedOpenedBand")
    btn = None
    if band is not None:
        for b in band.findChildren(QtWidgets.QAbstractButton):
            if b.isVisible() and ("押し出" in b.text()):
                btn = b
    out["band_shown"] = btn is not None
    before = len(doc.Objects)
    if btn is not None:
        click_widget(btn)
        pump(2500)
    bodies = [o for o in doc.Objects if o.isDerivedFrom("PartDesign::Body")]
    out["no_plate_from_the_frame"] = not bodies
    out["no_question_dialog"] = QtWidgets.QApplication.activeModalWidget() is None
    shot("40-dxf-not-extruded")
    m = QtWidgets.QApplication.activeModalWidget()
    if m is not None:
        m.close()
    return out


# ------------------------------------------------------------- 8: screws and drawings follow, last 3D tab


def case_follow():
    out = {}
    import PartsShelf as PS

    doc, body = plate_doc("ねじの板")
    sk = body.newObject("Sketcher::SketchObject", "SketchHole")
    sk.AttachmentSupport = (body.Origin.OriginFeatures[3], [""])
    sk.MapMode = "FlatFace"
    sk.AttachmentOffset = App.Placement(App.Vector(0, 0, 15), App.Rotation())
    sk.addGeometry(Part.Point(App.Vector(10, 10, 0)))
    hole = body.newObject("PartDesign::Hole", "Hole")
    hole.Profile = sk
    hole.Diameter = 6
    hole.DepthType = "ThroughAll"
    doc.recompute()
    Gui.runCommand("Unified_NewDrawing")
    pump(6000)
    Gui.Selection.clearSelection()
    face = [f for f in hole.Shape.Faces if type(f.Surface).__name__ == "Cylinder"][0]
    h = PS.analyze_hole(face, PS.solids_of_document(doc), view_direction=App.Vector(0, 0, -1))
    links = PS.put_plan(doc, PS.plan_for_hole(h, size="M5"))
    doc.recompute()
    out["screw_length_fits"] = PS.plan_for_hole(h, size="M5").length >= 19
    screw = links[0]
    x0 = screw.Shape.BoundBox.Center.x
    views = [v for v in doc.Objects if v.isDerivedFrom("TechDraw::DrawViewPart") and getattr(v, "AutoCenterLines", None)]
    holes_before = list(views[0].AutoCenterHoles) if views else []
    # move the hole by 7 mm
    sk.moveGeometry(0, 1, App.Vector(17, 10, 0))
    doc.recompute()
    pump(5000)
    x1 = screw.Shape.BoundBox.Center.x
    out["screw_follows"] = abs((x1 - x0) - 7) < 1e-3
    out["center_holes"] = [holes_before, list(views[0].AutoCenterHoles) if views else None]
    out["center_lines_follow"] = bool(views) and list(views[0].AutoCenterHoles) != holes_before
    doc.saveAs(os.path.join(WORK, "ねじの板.FCStd"))
    path = doc.FileName
    # back to the 3D tab and close it: the file closes (saved: nothing to ask)
    import FollowGui

    FollowGui.show_3d_first(doc.Name)
    pump(500)
    subs = FollowGui._3d_subwindows(doc.Name)
    out["one_3d_tab"] = len(subs) == 1
    asked = {}

    def answer():
        m = QtWidgets.QApplication.activeModalWidget()
        asked["dialog"] = m is not None
        if m is not None:
            asked["text"] = " ".join(w.text() for w in m.findChildren(QtWidgets.QLabel) if w.text())
            shot("51-asked-to-save")
            for b in m.findChildren(QtWidgets.QAbstractButton):
                if b.text().replace("&", "") in ("変更を破棄", "Discard"):
                    click_widget(b)
                    return
            xdo("key", "Escape")

    doc_name = doc.Name
    out["modified_before_close"] = Gui.getDocument(doc.Name).Modified
    if subs:
        QtCore.QTimer.singleShot(1500, answer)
        subs[0].close()
        for _k in range(60):
            pump(200)
            if doc_name not in App.listDocuments():
                break
    out["asked_if_modified"] = asked.get("dialog", False) or not out["modified_before_close"]
    out["asked"] = asked
    out["closing_last_3d_closes_file"] = doc_name not in App.listDocuments()
    # open it again: the 3D view in front
    App.openDocument(path)
    pump(7000)
    d2 = App.ActiveDocument or App.getDocument(doc_name)
    mdi = mw().findChild(QtWidgets.QMdiArea)
    act = mdi.activeSubWindow()
    out["reopened_on_3d"] = act is not None and act in FollowGui._3d_subwindows(d2.Name)
    pump(1500)
    out["reopened_modified_mark"] = Gui.getDocument(d2.Name).Modified  # not judged: the drawing's views mark it
    shot("50-reopened-3d-first")
    return out


# ------------------------------------------------------------- 9: the first click on a plane


def case_plane_click():
    out = {}
    close_all()
    Gui.runCommand("Unified_NewPart")
    pump(150)
    px = None
    for k in range(40):
        pump(10)
        doc = App.ActiveDocument
        try:
            px = pick_pixel([App.Vector(x, y, 0) for x in (-8, 8, 20, -20) for y in (8, -8, 20, -20)],
                            lambda i: "XY" in i.get("Object", "") or "XY" in i.get("Component", "") or "XY" in str(i))
        except Exception:
            px = None
        if px:
            break
    out["plane_found"] = bool(px)
    if px:
        click(*px)
        pump(1500)
    doc = App.ActiveDocument
    sk = [o for o in doc.Objects if o.isDerivedFrom("Sketcher::SketchObject")]
    out["first_click_takes_the_plane"] = bool(sk) and Gui.ActiveDocument.getInEdit() is not None
    shot("60-first-click-plane")
    if Gui.Control.activeDialog():
        Gui.Control.closeDialog()
    return out


# ------------------------------------------------------------- 10: icons, English


def case_messages():
    out = {}
    close_all()
    App.newDocument("言葉")
    pump(500)
    seen = []

    class Watch:
        def __init__(self):
            pass

    import CommandSearchGui as G
    import CommandSearchCore as C

    # every icon of the catalog, as the search shows it: none that is not there
    pop = G.popup()
    missing = []
    for e in G.entries():
        icon = G.local_icon(e.get("icon", ""))
        if e.get("icon", "").startswith("/") and not icon:
            missing.append(e["name"])
    out["catalog_icons_missing"] = missing[:10]
    xdo("key", "ctrl+k")
    pump(500)
    field = pop.findChild(QtWidgets.QLineEdit)
    hits = []
    for q in ("コピー", "部品の棚", "点から点へ"):
        field.setText(q)
        pump(500)
        lw = pop.findChild(QtWidgets.QListWidget)
        hits.append(lw.item(0).text().split("\n")[0])
    shot("70-search-copy", pop, 4)
    xdo("key", "Escape")
    out["search_first"] = hits
    names = [h["name"] for h in C.search("コピー", G.entries(), limit=5)]
    out["copy_top"] = names
    out["copy_finds_another_part"] = "Unified_AnotherPart" in names[:5]
    area = mw().findChild(QtWidgets.QWidget, "NotificationArea")
    texts = []
    for w in mw().findChildren(QtWidgets.QWidget):
        if w.metaObject().className() == "Gui::NotificationArea" or "Notification" in w.metaObject().className():
            try:
                texts.append(w.toolTip())
            except Exception:
                pass
    out["no_icon_notification"] = not any("Cannot find icon" in t for t in texts)
    from PySide import QtCore as QC

    out["processing_in_japanese"] = QC.QCoreApplication.translate("Gui::SequencerBar", "Processing...") != "Processing..."
    return out


STAGES = [("assembly", case_assembly), ("holes", case_holes), ("type_radius", case_type_radius),
          ("drawing", case_drawing), ("dxf", case_dxf), ("follow", case_follow), ("plane_click", case_plane_click),
          ("messages", case_messages)]
if CASES:
    STAGES = [s for s in STAGES if s[0] in CASES.split(",")]
run_stages(STAGES, results)
