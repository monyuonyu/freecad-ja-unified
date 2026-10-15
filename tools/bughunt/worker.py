# SPDX-License-Identifier: LGPL-2.1-or-later
# One corpus file through FreeCADCmd: open/import -> recompute -> check -> export -> re-import.
# Run as:  FreeCADCmd worker.py  with env BH_IN=<file> BH_OUT=<dir> [BH_DWG2DXF=<dwg2dxf>]
# Prints one "BH <stage> ok|fail|skip <detail>" line per stage; tracebacks go to stderr.
# The caller (run_corpus.py) adds sanitizer output, exit status and timeouts.
import os
import sys
import traceback

import faulthandler

import FreeCAD as App

# hangs: dump the Python stack every BH_HANG_DUMP seconds (triage.py reads the last one)
faulthandler.dump_traceback_later(int(os.environ.get("BH_HANG_DUMP", "240")), repeat=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks  # noqa: E402

SRC = os.environ["BH_IN"]
OUT = os.environ["BH_OUT"]
os.makedirs(OUT, exist_ok=True)
EXT = os.path.splitext(SRC)[1].lower().lstrip(".")


def say(stage, status, detail=""):
    detail = " ".join(str(detail).split())[:300]
    sys.stdout.write("BH %s %s %s\n" % (stage, status, detail))
    sys.stdout.flush()


def stage(name):
    def wrap(fn):
        def run(*a):
            try:
                r = fn(*a)
                say(name, "ok", "" if r is None else r)
                return r
            except Exception as e:
                traceback.print_exc()
                say(name, "fail", "%s: %s" % (type(e).__name__, e))
                return None
        return run
    return wrap


if EXT == "dwg" and os.environ.get("BH_DWG2DXF"):
    g = App.ParamGet("User parameter:BaseApp/Preferences/Mod/Draft")
    g.SetString("TeighaFileConverter", os.environ["BH_DWG2DXF"])
    g.SetInt("DWGConversion", 1)


@stage("load")
def load():
    if EXT == "fcstd":
        doc = App.openDocument(SRC)
        return doc
    mods = App.getImportType(EXT)
    if isinstance(mods, str):
        mods = [mods]
    if not mods:
        raise RuntimeError("no importer for ." + EXT)
    doc = App.newDocument("bh")
    for name in mods:  # e.g. ifc: nativeifc has no insert(), importIFC has
        mod = __import__(name)
        if hasattr(mod, "insert"):
            mod.insert(SRC, doc.Name)
            return doc
    raise RuntimeError("no importer with insert() for ." + EXT)


doc = load()
if doc is None:
    sys.exit(0)
say("objects", "ok", len(doc.Objects))
stored = checks.object_snapshot(doc) if EXT == "fcstd" else None


@stage("recompute")
def recompute():
    doc.recompute()
    bad = [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]
    return "invalid=%d" % len(bad)


recompute()


CONTAINERS = ("App::Part", "App::DocumentObjectGroup", "App::DocumentObjectGroupPython")


def shape_objects():
    out = []
    for o in doc.Objects:
        sh = getattr(o, "Shape", None)
        if sh is None or not hasattr(sh, "isNull") or sh.isNull():
            continue
        if o.TypeId in ("App::Line", "App::Plane", "App::Point", "App::Origin") or \
                not sh.BoundBox.isValid() or sh.BoundBox.DiagonalLength > 1e10:
            continue  # infinite datum geometry (Shape.check(True) on App::Line crashes; reported)
        if o.TypeId in CONTAINERS:
            continue  # their children are taken one by one
        if o.InList and any(p.TypeId not in CONTAINERS and hasattr(p, "Shape") for p in o.InList):
            continue  # only roots (children are inside their parent's shape)
        out.append(o)
    return out


@stage("check")
def check():
    objs = shape_objects()
    bad = 0
    for o in objs:
        if not o.Shape.isValid():
            bad += 1
    return "shapes=%d invalid=%d" % (len(objs), bad)


def compound():
    import Part
    return Part.makeCompound([o.Shape.copy() for o in objs])


check()
objs = shape_objects()
if objs:
    # before any export: exportStl leaves a 0.01 mm mesh on the shapes, which made
    # projectVisible take minutes (fixed in 28fc51f32 on unified-ui, not yet in the patches)
    checks.projection_and_render(compound(), OUT)
meshes = [o for o in doc.Objects if o.TypeId.startswith("Mesh::")]


if objs:
    import Part

    comp = compound()
    for ext, fn in (("step", comp.exportStep), ("iges", comp.exportIges),
                    ("brep", comp.exportBrep)):
        p = os.path.join(OUT, "out." + ext)
        stage("export_" + ext)(fn)(p)
        if os.path.exists(p):
            stage("reimport_" + ext)(lambda p=p: "valid=%s" % Part.read(p).isValid())()

    @stage("export_step_doc")
    def export_step_doc():
        import Import
        Import.export(objs, os.path.join(OUT, "doc.step"))

    export_step_doc()

    @stage("reimport_step_doc")
    def reimport_step_doc():
        import Import
        d = App.newDocument("bhre")
        Import.insert(os.path.join(OUT, "doc.step"), d.Name)
        return "objects=%d" % len(d.Objects)

    if os.path.exists(os.path.join(OUT, "doc.step")):
        reimport_step_doc()

    @stage("mesh_from_shape")
    def mesh_from_shape():
        import MeshPart
        m = MeshPart.meshFromShape(Shape=comp, LinearDeflection=1.0, AngularDeflection=0.5)
        return "facets=%d" % m.CountFacets

    mesh_from_shape()

    @stage("export_dxf")
    def export_dxf():
        import importDXF
        importDXF.export(objs, os.path.join(OUT, "out.dxf"))

    export_dxf()

    @stage("reimport_dxf")
    def reimport_dxf():
        import importDXF
        d = App.newDocument("bhdxf")
        importDXF.insert(os.path.join(OUT, "out.dxf"), d.Name)
        return "objects=%d" % len(d.Objects)

    if os.path.exists(os.path.join(OUT, "out.dxf")):
        reimport_dxf()
else:
    say("export_shapes", "skip", "no shapes")

if objs or meshes:
    import Mesh

    for ext in ("stl", "obj", "off", "ply", "3mf"):
        p = os.path.join(OUT, "mesh." + ext)
        stage("export_" + ext)(Mesh.export)(objs + meshes, p)
        if os.path.exists(p):
            stage("reimport_" + ext)(lambda p=p: "facets=%d" % Mesh.Mesh(p).CountFacets)()

    @stage("mesh_check")
    def mesh_check():
        r = []
        for o in meshes:
            m = o.Mesh
            r.append("%d/%d/%d" % (m.CountFacets, m.hasNonManifolds(), m.hasSelfIntersections()))
            m2 = m.copy()
            m2.harmonizeNormals()
            m2.removeDuplicatedPoints()
            m2.fixIndices()
        return " ".join(r[:5])

    if meshes:
        mesh_check()

# silent-bug checks (BH-MM lines)
if objs:
    import Part
    comp = compound()
    solids = checks.usable_solids(comp)
    checks.roundtrip_cad(comp, OUT)
    checks.roundtrip_mesh(comp, OUT)
    checks.export_twice(comp, OUT)
    checks.valid_vs_check([o.Shape for o in objs][:20])
    checks.mesh_volume(solids)
    checks.booleans(solids)
    checks.interference_vs_bruteforce(solids)
    checks.metamorphic(solids)
    checks.reorder_invariance([o.Shape for o in objs if o.Shape.Solids][:30])
    if EXT in ("dxf", "dwg"):
        checks.drawing_roundtrip(doc, objs, OUT, EXT)
checks.recompute_idempotent(doc, stored)
if EXT == "fcstd":
    checks.fcstd_roundtrip(doc, OUT)

say("done", "ok")
App.closeDocument(doc.Name)
