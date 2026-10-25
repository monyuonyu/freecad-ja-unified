# SPDX-License-Identifier: LGPL-2.1-or-later
"""More of the same part in an assembly, in the GUI (AssemblyCopies.py):

- Ctrl+C / Ctrl+V on parts of an assembly: another of each, beside it (picked, to move or snap)
- "Copies in a Grid": rows × columns at a spacing (the four corners of a plate: 2 × 2)
- a double-click on a part of an assembly in the tree picks it instead of opening its own file
"""

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtWidgets

import AssemblyCopies as AC

translate = App.Qt.translate


def QT_TRANSLATE_NOOP(context, text):
    return text


def picked_parts():
    out = []
    for s in Gui.Selection.getSelectionEx("", 0):
        obj = s.Object
        subs = s.SubElementNames or ("",)
        for sub in subs:
            # A pick inside the assembly: its first level below the assembly is the part
            leaf = obj
            if obj.isDerivedFrom("Assembly::AssemblyObject") and sub:
                name = sub.split(".")[0]
                leaf = obj.Document.getObject(name) or obj
            elif sub and "." in sub:
                first = obj.Document.getObject(sub.split(".")[0])
                if first is not None and AC.is_assembly_part(first):
                    leaf = first
            if AC.is_assembly_part(leaf) and leaf not in out:
                out.append(leaf)
    return out


_clipboard = []


def copy():
    global _clipboard
    _clipboard = [(o.Document.Name, o.Name) for o in picked_parts()]
    if _clipboard:
        Gui.getMainWindow().statusBar().showMessage(
            translate("Unified", "Copied {} part(s): Ctrl+V puts another of each").format(len(_clipboard)), 4000
        )
    return bool(_clipboard)


def paste():
    objs = []
    for d, n in _clipboard:
        try:
            o = App.getDocument(d).getObject(n)
        except Exception:
            o = None
        if o is not None:
            objs.append(o)
    if not objs:
        return False
    new = AC.duplicate(objs)
    Gui.Selection.clearSelection()
    for o in new:
        asm = AC.assembly_of(o)
        if asm is not None:
            Gui.Selection.addSelection(o.Document.Name, asm.Name, o.Name + ".")
        else:
            Gui.Selection.addSelection(o)
    Gui.getMainWindow().statusBar().showMessage(
        translate("Unified", "Put {} more: drag it or use “Snap” to place it").format(len(new)), 5000
    )
    return True


def handle_key(event):
    """Ctrl+C / Ctrl+V on parts of an assembly (else the usual copy and paste)"""
    mods = event.modifiers() & ~QtCore.Qt.KeypadModifier
    if mods != QtCore.Qt.ControlModifier or event.key() not in (QtCore.Qt.Key_C, QtCore.Qt.Key_V):
        return False
    import UnifiedChrome

    app = QtWidgets.QApplication.instance()
    if UnifiedChrome.typing_text(app.focusWidget()) or app.activePopupWidget() or app.activeModalWidget():
        return False
    if Gui.Control.activeDialog():
        return False
    if event.key() == QtCore.Qt.Key_C:
        return bool(picked_parts())  # copied when the key press comes (below)
    return bool(_clipboard)


class GridPanel:
    def __init__(self, part):
        self.part = part
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle(translate("Unified_GridCopies", "Copies in a Grid"))
        lay = QtWidgets.QFormLayout(self.form)
        size = AC._size(part)
        self.columns = QtWidgets.QSpinBox()
        self.columns.setRange(1, 50)
        self.columns.setValue(2)
        self.rows = QtWidgets.QSpinBox()
        self.rows.setRange(1, 50)
        self.rows.setValue(2)
        self.dx = QtWidgets.QDoubleSpinBox()
        self.dy = QtWidgets.QDoubleSpinBox()
        for f, v in ((self.dx, size.x * 2), (self.dy, size.y * 2)):
            f.setRange(-10000, 10000)
            f.setDecimals(2)
            f.setSuffix(" mm")
            f.setValue(v)
        self.columns.setObjectName("UnifiedGridColumns")
        self.rows.setObjectName("UnifiedGridRows")
        self.dx.setObjectName("UnifiedGridDX")
        self.dy.setObjectName("UnifiedGridDY")
        lay.addRow(QtWidgets.QLabel(translate("Unified_GridCopies", "“{}” and its copies").format(part.Label)))
        lay.addRow(translate("Unified_GridCopies", "Across (X)"), self.columns)
        lay.addRow(translate("Unified_GridCopies", "Spacing across"), self.dx)
        lay.addRow(translate("Unified_GridCopies", "Back (Y)"), self.rows)
        lay.addRow(translate("Unified_GridCopies", "Spacing back"), self.dy)
        hint = QtWidgets.QLabel(
            translate("Unified_GridCopies", "From the part's place: e.g. a pillar at one corner of a 100 × 60 plate, "
                      "2 × 2 at 80 and 40 mm puts one at each corner.")
        )
        hint.setWordWrap(True)
        lay.addRow(hint)

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel

    def accept(self):
        AC.grid(self.part, self.columns.value(), self.rows.value(), self.dx.value(), self.dy.value())
        Gui.Control.closeDialog()
        return True

    def reject(self):
        Gui.Control.closeDialog()
        return True


class GridCopiesCommand:
    def GetResources(self):
        return {
            "Pixmap": "Draft_Array",
            "MenuText": QT_TRANSLATE_NOOP("Unified_GridCopies", "Copies in a Grid"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Unified_GridCopies",
                "More of the picked part of the assembly in rows and columns at a spacing (one at each corner: 2 × 2)",
            ),
        }

    def IsActive(self):
        return len(picked_parts()) == 1 and not Gui.Control.activeDialog()

    def Activated(self):
        parts = picked_parts()
        if parts:
            Gui.Control.showDialog(GridPanel(parts[0]))


class DuplicateCommand:
    def GetResources(self):
        return {
            "Pixmap": "Std_DuplicateSelection",
            "MenuText": QT_TRANSLATE_NOOP("Unified_AnotherPart", "Another of This Part"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Unified_AnotherPart", "Put one more of the picked part beside it (as Ctrl+C, Ctrl+V)"
            ),
        }

    def IsActive(self):
        return bool(picked_parts())

    def Activated(self):
        copy()
        paste()


class KeyAndTreeFilter(QtCore.QObject):
    def eventFilter(self, obj, event):
        t = event.type()
        if t == QtCore.QEvent.ShortcutOverride and isinstance(obj, QtWidgets.QWidget):
            if handle_key(event):
                event.accept()
                return True
        elif t == QtCore.QEvent.KeyPress and isinstance(obj, QtWidgets.QWidget):
            if handle_key(event):
                if event.key() == QtCore.Qt.Key_C:
                    copy()
                else:
                    QtCore.QTimer.singleShot(0, paste)
                return True
        elif t == QtCore.QEvent.MouseButtonDblClick and isinstance(obj, QtWidgets.QWidget):
            tree = obj.parentWidget()
            if tree is not None and tree.metaObject().className() == "Gui::TreeWidget":
                import HistoryLineGui as H

                index = tree.indexAt(event.position().toPoint() if hasattr(event, "position") else event.pos())
                o = H.object_of(index)
                if o is not None and o.isDerivedFrom("App::Link") and AC.assembly_of(o) is not None:
                    # A part of the assembly: picked, not opened in its own file
                    return True
        return False


_filter = None


def make_parts_selectable(doc):
    """The parts of the file's assemblies can be picked again. The joint panel's isolation makes
    the other parts unselectable for a while; saved meanwhile (the recovery data every two
    minutes, a crash) they stayed unselectable in the file, 13 parts that no click could pick
    (engine field test 0.7.8)."""
    for asm in doc.Objects:
        if not asm.isDerivedFrom("Assembly::AssemblyObject"):
            continue
        for part in asm.OutListRecursive:
            vo = getattr(part, "ViewObject", None)
            if vo is not None and hasattr(vo, "Selectable") and not vo.Selectable:
                vo.Selectable = True


class _OpenObserver:
    # (no "restored" slot for Python observers: from the document's creation, wait for the end)
    def slotCreatedDocument(self, doc):
        QtCore.QTimer.singleShot(100, lambda: _fix_after_open(doc.Name, 100))


def _fix_after_open(name, tries):
    # the view's properties are read after the document's: wait until the opening is over
    if (App.isRestoring() or Gui.getDocument(name) is None) and tries > 0:
        QtCore.QTimer.singleShot(100, lambda: _fix_after_open(name, tries - 1))
        return
    doc = App.listDocuments().get(name)
    if doc is not None:
        try:
            make_parts_selectable(doc)
        except Exception as e:
            App.Console.PrintLog("Unified: selectable parts: {}\n".format(e))


_observer = None


def install():
    global _filter, _observer
    if _filter is None:
        import UnifiedChrome

        _filter = KeyAndTreeFilter()
        UnifiedChrome.EXTRA_FILTERS.append(_filter)
    if _observer is None:
        _observer = _OpenObserver()
        App.addDocumentObserver(_observer)


class HingeToGroundCommand:
    """One round face (or circle) of a part of an assembly: the part turns about it, in place"""

    def GetResources(self):
        return {
            "Pixmap": "Assembly_CreateJointRevolute",
            "MenuText": QT_TRANSLATE_NOOP("Unified_HingeToGround", "Turns in Place"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Unified_HingeToGround",
                "The part turns about the picked round face, where it is now (held by the ground: "
                "no other part is needed). Then “Turn to an angle” in the joint turns it.",
            ),
        }

    def picked(self):
        sel = Gui.Selection.getSelectionEx("", 0)
        if len(sel) != 1 or len(sel[0].SubElementNames) != 1:
            return None
        obj, sub = sel[0].Object, sel[0].SubElementNames[0]
        names = sub.split(".")
        if obj.isDerivedFrom("Assembly::AssemblyObject"):
            assembly = obj
        else:
            assembly = next((obj.Document.getObject(n) for n in names
                             if obj.Document.getObject(n) is not None
                             and obj.Document.getObject(n).isDerivedFrom("Assembly::AssemblyObject")), None)  # fmt: skip
        if assembly is None:
            return None
        import UtilsAssembly

        part, rel = UtilsAssembly.getComponentReference(assembly, obj, sub)
        if part is None or not rel:
            return None
        element = rel.split(".")[-1]
        if not (element.startswith("Face") or element.startswith("Edge")):
            return None
        return assembly, part, rel

    def IsActive(self):
        return not Gui.Control.activeDialog() and self.picked() is not None

    def make(self, assembly, part, sub):
        return AC.hinge_to_ground(assembly, part, sub)

    def Activated(self):
        found = self.picked()
        if found is None:
            return
        assembly, part, sub = found
        doc = assembly.Document
        doc.openTransaction(translate("Unified", "Joint to the ground"))
        try:
            joint = self.make(assembly, part, sub)
        finally:
            doc.commitTransaction()
        Gui.Selection.clearSelection()
        Gui.Selection.addSelection(joint)


class SlideOnGroundCommand(HingeToGroundCommand):
    """One round face (its axis) or flat face of a part of an assembly: the part slides along
    it, in place (a piston in its cylinder, without the cylinder part)"""

    def GetResources(self):
        return {
            "Pixmap": "Assembly_CreateJointSlider",
            "MenuText": QT_TRANSLATE_NOOP("Unified_SlideOnGround", "Slides in Place"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Unified_SlideOnGround",
                "The part slides along the picked round face's axis, where it is now (held by the "
                "ground: no other part is needed).",
            ),
        }

    def make(self, assembly, part, sub):
        return AC.slide_on_ground(assembly, part, sub)


Gui.addCommand("Unified_GridCopies", GridCopiesCommand())
Gui.addCommand("Unified_AnotherPart", DuplicateCommand())
Gui.addCommand("Unified_HingeToGround", HingeToGroundCommand())
Gui.addCommand("Unified_SlideOnGround", SlideOnGroundCommand())
