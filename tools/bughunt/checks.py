# SPDX-License-Identifier: LGPL-2.1-or-later
# Silent-bug checks for worker.py: round trips, idempotence, self-consistency, metamorphic
# invariants. Every disagreement is printed as
#   BH-MM <check> <kind> <detail>
# (check = what was compared, kind = which quantity disagreed). triage.py groups them by
# (check, kind, file type). Each check is cheap and capped; a failing check never stops the run.
import math
import os
import sys
import time
import traceback

import FreeCAD as App

MAX_FACES = 400        # skip expensive checks on bigger solids
MAX_SOLIDS = 4         # solids per file for boolean/metamorphic checks
DEADLINE = time.time() + float(os.environ.get("BH_CHECK_SECONDS", "240"))


def mm(check, kind, detail=""):
    detail = " ".join(str(detail).split())[:240]
    sys.stdout.write("BH-MM %s %s %s\n" % (check, kind, detail))
    sys.stdout.flush()


def note(check, status, detail=""):
    sys.stdout.write("BH-CK %s %s %s\n" % (check, status, " ".join(str(detail).split())[:200]))
    sys.stdout.flush()


def guarded(fn):
    def run(*a, **k):
        if time.time() > DEADLINE:
            note(fn.__name__, "skip", "check time budget used")
            return None
        try:
            return fn(*a, **k)
        except Exception as e:
            traceback.print_exc()
            note(fn.__name__, "error", "%s: %s" % (type(e).__name__, e))
            return None
    return run


def props(s):
    # optimal box (no triangulation, no tolerances): Shape.BoundBox depends on the mesh cache
    try:
        bb = s.optimalBoundingBox(False, False)
    except Exception:
        bb = s.BoundBox
    return {
        "volume": s.Volume if s.Solids else 0.0,
        "area": s.Area,
        "bbox": (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax) if bb.isValid() else None,
        "diag": bb.DiagonalLength if bb.isValid() else 0.0,
        "solids": len(s.Solids), "shells": len(s.Shells), "faces": len(s.Faces),
        "edges": len(s.Edges), "vertexes": len(s.Vertexes), "valid": s.isValid(),
    }


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)


def compare(check, p, q, rtol, counts=("solids", "faces", "edges"), what=""):
    """Compare two props dicts; print one BH-MM per differing quantity. Returns number of diffs."""
    n = 0
    tag = (" " + what) if what else ""
    for k in ("volume", "area"):
        if max(abs(p[k]), abs(q[k])) > 1e-9 and rel(p[k], q[k]) > rtol:
            mm(check, k, "%.6g vs %.6g%s" % (p[k], q[k], tag)); n += 1
    if p["bbox"] and q["bbox"]:
        d = max(abs(x - y) for x, y in zip(p["bbox"], q["bbox"]))
        if d > max(rtol * max(p["diag"], 1e-9), 1e-7):
            mm(check, "bbox", "off by %.3g (diag %.3g)%s" % (d, p["diag"], tag)); n += 1
    elif bool(p["bbox"]) != bool(q["bbox"]):
        mm(check, "bbox", "one side empty" + tag); n += 1
    for k in counts:
        if p[k] != q[k]:
            mm(check, k, "%d vs %d%s" % (p[k], q[k], tag)); n += 1
    if p["valid"] and not q["valid"]:
        mm(check, "valid", "valid before, invalid after" + tag); n += 1
    return n


# --- 1. round trips --------------------------------------------------------------------------

@guarded
def roundtrip_cad(comp, out):
    import Part
    p = props(comp)
    rules = {  # format: (relative tolerance, counts that must survive)
        "brep": (1e-9, ("solids", "shells", "faces", "edges", "vertexes")),
        "step": (1e-4, ("solids", "faces")),
        "iges": (1e-3, ()),  # IGES has no solids by default; compare area and bbox only
    }
    for ext, (rtol, counts) in rules.items():
        path = os.path.join(out, "out." + ext)
        if not os.path.exists(path):
            continue
        q = props(Part.read(path))
        if ext == "iges":
            q["volume"] = p["volume"]
        compare("roundtrip_" + ext, p, q, rtol, counts)
    note("roundtrip_cad", "ok")


@guarded
def roundtrip_mesh(comp, out):
    import Mesh
    import MeshPart
    p = props(comp)
    closed = p["solids"] > 0 and all(s.isClosed() for s in comp.Solids) if p["solids"] else False
    for ext in ("stl", "obj", "off", "ply", "3mf"):
        path = os.path.join(out, "mesh." + ext)
        if not os.path.exists(path):
            continue
        m = Mesh.Mesh(path)
        if not comp.Faces:
            continue  # wires only: nothing to mesh
        if m.CountFacets == 0:
            mm("roundtrip_mesh_" + ext, "empty", "%d faces exported, no facets read back" % len(comp.Faces))
            continue
        if p["bbox"]:
            bb = m.BoundBox
            d = max(abs(x - y) for x, y in zip(p["bbox"], (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax)))
            if d > 0.02 * max(p["diag"], 1e-9):
                mm("roundtrip_mesh_" + ext, "bbox", "off by %.3g (diag %.3g)" % (d, p["diag"]))
    note("roundtrip_mesh", "ok")


@guarded
def mesh_volume(solids):
    import MeshPart
    for i, s in enumerate(solids):
        if len(s.Faces) > MAX_FACES or not s.isValid() or not s.isClosed() or s.Volume <= 0:
            continue
        diag = s.BoundBox.DiagonalLength
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=diag * 2e-4, AngularDeflection=0.1,
                                   Relative=False)
        if not m.isSolid():
            mm("tessellation", "not_closed", "solid %d: %d facets, open mesh" % (i, m.CountFacets))
            continue
        if rel(abs(m.Volume), s.Volume) > 0.02:
            mm("tessellation", "volume", "solid %d: mesh %.6g vs brep %.6g" % (i, m.Volume, s.Volume))
        if m.Volume < 0:
            mm("tessellation", "orientation", "solid %d: negative mesh volume" % i)
    note("mesh_volume", "ok")


def _value(v):
    """Comparable form: numbers rounded to 9 significant digits (placements, vectors, floats)."""
    def r(x):
        return float("%.9g" % x) if isinstance(x, float) else x
    if isinstance(v, App.Placement):
        q = v.Rotation.Q
        if q[3] < 0:
            q = tuple(-c for c in q)
        return ("P",) + tuple(r(c) for c in tuple(v.Base) + tuple(q))
    if isinstance(v, App.Vector):
        return ("V",) + tuple(r(c) for c in v)
    if hasattr(v, "Value") and hasattr(v, "Unit"):
        return r(float(v.Value))
    return r(v) if isinstance(v, float) else v


def _same(a, b):
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= 1e-7 * max(1.0, abs(a), abs(b))
    return a == b


def object_snapshot(doc):
    snap = {}
    for o in doc.Objects:
        vals = {}
        for name in o.PropertiesList:
            if name.startswith("_"):
                continue  # internal bookkeeping (_ElementMapVersion ...)
            try:
                t = o.getTypeIdOfProperty(name)
                if t in ("App::PropertyFloat", "App::PropertyInteger", "App::PropertyString",
                         "App::PropertyBool", "App::PropertyLength", "App::PropertyDistance",
                         "App::PropertyAngle", "App::PropertyPlacement", "App::PropertyEnumeration",
                         "App::PropertyVector", "App::PropertyIntegerConstraint",
                         "App::PropertyFloatConstraint", "App::PropertyQuantity"):
                    vals[name] = _value(getattr(o, name))
                elif t == "App::PropertyLink":
                    v = getattr(o, name)
                    vals[name] = v.Name if v else None
                elif t == "App::PropertyLinkList":
                    vals[name] = [x.Name for x in getattr(o, name)]
            except Exception:
                pass
        sh = getattr(o, "Shape", None)
        shp = None
        if sh is not None and hasattr(sh, "isNull") and not sh.isNull():
            shp = props(sh)
        snap[o.Name] = (o.TypeId, vals, shp)
    return snap


def compare_snapshots(check, a, b):
    if set(a) != set(b):
        mm(check, "objects", "%d vs %d objects; missing %s"
           % (len(a), len(b), sorted(set(a) ^ set(b))[:5]))
    for name in sorted(set(a) & set(b)):
        ta, va, sa = a[name]
        tb, vb, sb = b[name]
        if ta != tb:
            mm(check, "type", "%s %s vs %s" % (name, ta, tb))
            continue
        for k in sorted(set(va) | set(vb)):
            if not _same(va.get(k), vb.get(k)):
                mm(check, "property", "%s %s.%s: %s vs %s" % (ta, name, k, str(va.get(k))[:60], str(vb.get(k))[:60]))
        if sa and sb:
            compare(check, sa, sb, 1e-6, ("solids", "faces", "edges"), "%s %s" % (ta, name))
        elif bool(sa) != bool(sb):
            mm(check, "shape", "%s %s: shape %s" % (ta, name, "lost" if sa else "appeared"))


@guarded
def fcstd_roundtrip(doc, out):
    before = object_snapshot(doc)
    path = os.path.join(out, "resaved.FCStd")
    doc.saveCopy(path)
    d2 = App.openDocument(path)
    try:
        compare_snapshots("fcstd_reopen", before, object_snapshot(d2))
        for o in d2.Objects:
            o.touch()
        d2.recompute()
        compare_snapshots("fcstd_reopen_recompute", before, object_snapshot(d2))
    finally:
        App.closeDocument(d2.Name)
    note("fcstd_roundtrip", "ok")


# --- 2. idempotence --------------------------------------------------------------------------

@guarded
def recompute_idempotent(doc, stored):
    """stored: snapshot right after loading (shapes as saved). Touch everything and recompute twice."""
    for o in doc.Objects:
        o.touch()
    doc.recompute()
    first = object_snapshot(doc)
    if stored is not None:
        compare_snapshots("stored_vs_recomputed", stored, first)
    for o in doc.Objects:
        o.touch()
    doc.recompute()
    compare_snapshots("recompute_twice", first, object_snapshot(doc))
    note("recompute_idempotent", "ok")


def _strip_step(data):
    # the HEADER section has the time stamp (FILE_NAME may span lines)
    # and OCCT numbers its product names per write ("Open CASCADE STEP translator 8.0 2")
    import re
    i = data.find(b"ENDSEC;")
    return re.sub(rb"STEP translator [0-9.]+ [0-9]+", b"STEP translator", data[i:] if i >= 0 else data)


@guarded
def export_twice(comp, out):
    for ext, fn, strip in (("brep", comp.exportBrep, None), ("step", comp.exportStep, _strip_step),
                           ("stl", comp.exportStl, None)):
        a, b = os.path.join(out, "twice1." + ext), os.path.join(out, "twice2." + ext)
        fn(a)
        fn(b)
        da, db = open(a, "rb").read(), open(b, "rb").read()
        if strip:
            da, db = strip(da), strip(db)
        if da != db:
            mm("export_twice", ext, "%d vs %d bytes" % (len(da), len(db)))
        os.remove(a)
        os.remove(b)
    note("export_twice", "ok")


# --- 3. self-consistency ---------------------------------------------------------------------

@guarded
def valid_vs_check(shapes):
    for i, s in enumerate(shapes):
        if len(s.Faces) > MAX_FACES:
            continue
        v = s.isValid()
        try:
            s.check(True)
            c = True
        except Exception:
            c = False
        if v and not c:
            mm("valid_vs_check", "check_fails", "shape %d: isValid() True but check(True) raises" % i)
        if c and not v:
            mm("valid_vs_check", "isvalid_fails", "shape %d: check(True) passes but isValid() False" % i)
    note("valid_vs_check", "ok")


def usable_solids(comp):
    out = []
    for s in comp.Solids:
        if len(s.Faces) <= MAX_FACES and s.isValid() and s.isClosed() and s.Volume > 1e-9:
            out.append(s)
        if len(out) == MAX_SOLIDS:
            break
    return out


def bool_identities(a, b, tag):
    va, vb = a.Volume, b.Volume
    vi = a.common(b).Volume
    vu = a.fuse(b).Volume
    vc = a.cut(b).Volume
    scale = max(va, vb)
    tol = 1e-4 * scale
    if abs(vu - (va + vb - vi)) > tol:
        mm("boolean", "fuse_identity", "%s: vol(A+B)=%.6g, vA+vB-vAB=%.6g" % (tag, vu, va + vb - vi))
    if abs(vc - (va - vi)) > tol:
        mm("boolean", "cut_identity", "%s: vol(A-B)=%.6g, vA-vAB=%.6g" % (tag, vc, va - vi))
    if vi > min(va, vb) + tol or vi < -tol:
        mm("boolean", "common_range", "%s: vol(AB)=%.6g outside [0, %.6g]" % (tag, vi, min(va, vb)))
    return vi


@guarded
def booleans(solids):
    for i, a in enumerate(solids):
        # A with itself moved by a third of its size: always overlaps, never coplanar
        b = a.copy()
        bb = a.BoundBox
        b.translate(App.Vector(bb.XLength / 3.1, bb.YLength / 2.9, bb.ZLength / 3.3))
        bool_identities(a, b, "solid %d vs shifted copy" % i)
        for j in range(i + 1, len(solids)):
            if a.BoundBox.intersect(solids[j].BoundBox):
                bool_identities(a, solids[j], "solids %d,%d" % (i, j))
    note("booleans", "ok")


@guarded
def interference_vs_bruteforce(solids):
    import Part
    if len(solids) < 2:
        return
    shapes = list(solids)
    b = solids[0].copy()  # make sure there is at least one overlap
    bb = b.BoundBox
    b.translate(App.Vector(bb.XLength / 3.1, bb.YLength / 2.9, bb.ZLength / 3.3))
    shapes.append(b)
    got = {(min(i, j), max(i, j)): v for i, j, v in Part.findInterferences(shapes)}
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            v = shapes[i].common(shapes[j]).Volume
            g = got.get((i, j))
            if v > 1e-6 and g is None:
                mm("interference", "missed_pair", "pair %d,%d common volume %.6g not reported" % (i, j, v))
            elif g is not None and g >= 0 and rel(g, v) > 1e-4 and abs(g - v) > 1e-6:
                mm("interference", "volume", "pair %d,%d reported %.6g, common %.6g" % (i, j, g, v))
            elif g is not None and v <= 1e-9 and g > 1e-6:
                mm("interference", "false_pair", "pair %d,%d reported %.6g, common 0" % (i, j, g))
    note("interference", "ok")


def _poly_area(pts):
    return 0.5 * abs(sum(pts[k][0] * pts[k - 1][1] - pts[k - 1][0] * pts[k][1] for k in range(len(pts))))


@guarded
def projection_and_render(comp, out):
    import Part
    if comp.isNull() or not comp.Faces or len(comp.Faces) > 3000:
        return
    for view in ("iso", "top", "front"):
        r = Part.projectVisible(comp, view=view, edges=False)
        area = 0.0
        for f in r["faces"]:
            for poly in f["polygons"]:
                area += _poly_area(poly["outer"]) - sum(_poly_area(h) for h in poly["holes"])
        bnd = r.get("bounds")
        if bnd:
            bx = (bnd[2] - bnd[0]) * (bnd[3] - bnd[1]) if len(bnd) == 4 else None
            if bx is not None and area > bx * (1 + 1e-6) + 1e-9:
                mm("project_visible", "area_gt_bounds", "%s: visible %.6g > bounds %.6g" % (view, area, bx))
        if area < -1e-9:
            mm("project_visible", "negative_area", view)
        if comp.Solids and not r["faces"]:
            mm("project_visible", "empty", "%s: solids but no visible faces" % view)
    png = os.path.join(out, "r.png")
    Part.renderImage(comp, png, width=64, height=48, supersample=1)
    if not os.path.exists(png) or os.path.getsize(png) < 100:
        mm("render", "no_image", "png missing or tiny")
    else:
        import zlib
        data = open(png, "rb").read()
        # decode the IDAT stream and check that not all pixels equal the background
        idat = b""
        p = 8
        while p < len(data):
            n = int.from_bytes(data[p:p + 4], "big")
            if data[p + 4:p + 8] == b"IDAT":
                idat += data[p + 8:p + 8 + n]
            p += 12 + n
        raw = zlib.decompress(idat)
        if len(set(raw)) <= 2:
            mm("render", "blank", "image has a single colour")
    note("projection_and_render", "ok")


# --- 4. metamorphic --------------------------------------------------------------------------

@guarded
def metamorphic(solids):
    for i, s in enumerate(solids):
        p = props(s)
        t = s.copy()
        t.translate(App.Vector(123.4, -56.7, 89.1))
        q = props(t)
        compare("translate", p, dict(q, bbox=tuple(x - d for x, d in zip(q["bbox"], (123.4, -56.7, 89.1) * 2))),
                1e-7, ("solids", "faces", "edges"), "solid %d" % i)
        r = s.copy()
        r.rotate(App.Vector(1, 2, 3), App.Vector(0.3, -0.5, 0.8), 37.0)
        q = props(r)
        q["bbox"] = p["bbox"]  # bbox changes under rotation
        compare("rotate", p, q, 1e-6, ("solids", "faces", "edges"), "solid %d" % i)
        if not r.isValid() and p["valid"]:
            mm("rotate", "valid", "solid %d" % i)
        k = s.copy().scale(2.0) if hasattr(s, "scale") else None
        if k is not None:
            if rel(k.Volume, 8 * s.Volume) > 1e-6:
                mm("scale2", "volume", "solid %d: %.6g vs 8x %.6g" % (i, k.Volume, 8 * s.Volume))
            if rel(k.Area, 4 * s.Area) > 1e-6:
                mm("scale2", "area", "solid %d: %.6g vs 4x %.6g" % (i, k.Area, 4 * s.Area))
            if p["valid"] and not k.isValid():
                mm("scale2", "valid", "solid %d" % i)
        m = s.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
        if rel(abs(m.Volume), s.Volume) > 1e-6:
            mm("mirror", "volume", "solid %d: %.6g vs %.6g" % (i, m.Volume, s.Volume))
        g = s.transformGeometry(App.Matrix(2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1))
        if rel(g.Volume, 8 * s.Volume) > 2e-2:  # NURBS conversion is approximate
            mm("transformGeometry2", "volume", "solid %d: %.6g vs 8x %.6g" % (i, g.Volume, 8 * s.Volume))
    note("metamorphic", "ok")


@guarded
def reorder_invariance(shapes):
    """Order of the inputs must not change compound properties or interference results."""
    import Part
    if len(shapes) < 2:
        return
    a = Part.makeCompound(shapes)
    b = Part.makeCompound(list(reversed(shapes)))
    compare("reorder_compound", props(a), props(b), 1e-7, ("solids", "faces", "edges"))
    if len(shapes) <= 30:
        n = len(shapes)
        f = {(min(i, j), max(i, j)): v for i, j, v in Part.findInterferences(shapes)}
        g = {(min(n - 1 - i, n - 1 - j), max(n - 1 - i, n - 1 - j)): v
             for i, j, v in Part.findInterferences(list(reversed(shapes)))}
        for k in sorted(set(f) | set(g)):
            a_, b_ = f.get(k), g.get(k)
            if a_ is None or b_ is None or (a_ >= 0) != (b_ >= 0) or (a_ >= 0 and rel(a_, b_) > 1e-6):
                mm("reorder_interference", "pairs", "pair %s: %s vs %s (OCC common(A,B) != common(B,A) "
                   "when an argument is a self-overlapping compound)" % (k, a_, b_))
                break
    note("reorder_invariance", "ok")


# --- 5. DXF / DWG ----------------------------------------------------------------------------

def drawing_counts(doc):
    n_obj = len([o for o in doc.Objects if hasattr(o, "Shape")])
    edges = 0
    length = 0.0
    def has_shape(x):
        sh = getattr(x, "Shape", None)
        return sh is not None and hasattr(sh, "isNull") and not sh.isNull()

    for o in doc.Objects:
        # roots of the geometry: no parent with a shape of its own (layers and groups have none;
        # a Part::Compound has, and its children are already in it)
        if has_shape(o) and not any(has_shape(p) for p in o.InList):
            edges += len(o.Shape.Edges)
            length += sum(e.Length for e in o.Shape.Edges)
    return {"objects": n_obj, "edges": edges, "length": length}


@guarded
def drawing_roundtrip(doc, objs, out, ext):
    """DXF (and DWG through LibreDWG): import -> export -> import keeps edges and total length."""
    import importDXF
    a = drawing_counts(doc)
    targets = [("dxf", importDXF)]
    if ext == "dwg":
        import importDWG
        targets.append(("dwg", importDWG))
    for fmt, mod in targets:
        path = os.path.join(out, "rt." + fmt)
        mod.export(objs, path)
        if not os.path.exists(path):
            mm("drawing_roundtrip_" + fmt, "no_file", "export wrote nothing")
            continue
        d = App.newDocument("bhrt" + fmt)
        try:
            mod.insert(path, d.Name)
            d.recompute()
            b = drawing_counts(d)
            if a["edges"] and b["edges"] != a["edges"]:
                mm("drawing_roundtrip_" + fmt, "edges", "%d vs %d" % (a["edges"], b["edges"]))
            if a["length"] > 0 and rel(a["length"], b["length"]) > 1e-3:
                mm("drawing_roundtrip_" + fmt, "length", "%.6g vs %.6g" % (a["length"], b["length"]))
        finally:
            App.closeDocument(d.Name)
    note("drawing_roundtrip", "ok")
