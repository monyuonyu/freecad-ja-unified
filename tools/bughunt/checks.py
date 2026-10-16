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
    # volume of the solids only: Volume of a compound also integrates loose faces and shells.
    # Flat (zero volume) solids are not counted: STEP export drops them.
    solids = [x for x in s.Solids if abs(x.Volume) > 1e-9]
    return {
        "volume": sum(x.Volume for x in solids),
        "area": s.Area,
        "bbox": (bb.XMin, bb.YMin, bb.ZMin, bb.XMax, bb.YMax, bb.ZMax) if bb.isValid() else None,
        "diag": bb.DiagonalLength if bb.isValid() else 0.0,
        "solids": len(solids), "shells": len(s.Shells), "faces": len(s.Faces),
        "edges": len(s.Edges), "vertexes": len(s.Vertexes), "valid": s.isValid(),
    }


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-9)


def mesh_vol(s, k=3e-4):
    """Volume of a fine tessellation: a second opinion for GProp, which is wrong on some BSpline
    prisms and a few 1e-4 off on others (OCC). Meshed about the origin: Mesh.Volume sums in
    single precision."""
    import MeshPart
    if s.isNull() or not s.Faces:
        return 0.0
    t = s.copy()
    t.translate(-s.BoundBox.Center)
    m = MeshPart.meshFromShape(Shape=t, LinearDeflection=s.BoundBox.DiagonalLength * k,
                               AngularDeflection=0.5, Relative=False)
    return m.Volume


def fine_bbox(s):
    """Box of a fine tessellation (faces) and discretised edges. optimalBoundingBox works on the
    UV box of a face and overshoots on trimmed surfaces of revolution (IGES reimport)."""
    xs = []
    # 1e-3: BRepMesh takes minutes at 1e-4 on the broken faces of OCC's linkrods.step
    d = max(s.BoundBox.DiagonalLength, 1e-9) * 1e-3
    t = s.copy()
    if t.Faces:
        xs += t.tessellate(d)[0]
    for e in t.Edges:
        xs += e.discretize(Deflection=d)
    if not xs:
        return None
    return (min(x.x for x in xs), min(x.y for x in xs), min(x.z for x in xs),
            max(x.x for x in xs), max(x.y for x in xs), max(x.z for x in xs))


def compare(check, p, q, rtol, counts=("solids", "faces", "edges"), what="", shapes=None):
    """Compare two props dicts; print one BH-MM per differing quantity. Returns number of diffs.
    shapes=(a, b): a box difference is confirmed on fine tessellations before it is reported."""
    n = 0
    tag = (" " + what) if what else ""
    for k in ("volume", "area"):
        if max(abs(p[k]), abs(q[k])) > 1e-9 and rel(p[k], q[k]) > rtol:
            mm(check, k, "%.6g vs %.6g%s" % (p[k], q[k], tag)); n += 1
    if p["bbox"] and q["bbox"]:
        d = max(abs(x - y) for x, y in zip(p["bbox"], q["bbox"]))
        lim = max(rtol * max(p["diag"], 1e-9), 1e-7)
        if d > lim and shapes is not None:
            fa, fb = fine_bbox(shapes[0]), fine_bbox(shapes[1])
            if fa and fb:  # tessellation is within 1e-3 of the diagonal: use that as the floor
                d = max(abs(x - y) for x, y in zip(fa, fb))
                lim = max(lim, 2e-3 * max(p["diag"], 1e-9))
        if d > lim:
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
        rs = Part.read(path)
        q = props(rs)
        if ext == "step" and any(abs(x.Volume) <= 1e-9 for x in comp.Solids):
            counts = ("solids",)  # STEP drops flat solids, and their faces with them
        if ext == "iges":
            q["volume"] = p["volume"]
        compare("roundtrip_" + ext, p, q, rtol, counts, shapes=(comp, rs))
    note("roundtrip_cad", "ok")


@guarded
def roundtrip_mesh(comp, out, has_meshes=False):
    import Mesh
    import MeshPart
    import Part
    p = props(comp)
    if comp.Faces:
        # only faces become facets: wires, edges and points of the drawing are not in the mesh
        fp = props(Part.makeCompound(comp.Faces))  # optimal box, not the loose BoundBox
        p["bbox"], p["diag"] = fp["bbox"], fp["diag"]
    if has_meshes:
        p["bbox"] = None  # mesh objects of the document are exported too
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
    import Part
    for i, s in enumerate(solids):
        if len(s.Faces) > MAX_FACES or not s.isValid() or not s.isClosed() or s.Volume <= 0:
            continue
        diag = s.BoundBox.DiagonalLength
        m = MeshPart.meshFromShape(Shape=s, LinearDeflection=diag * 2e-4, AngularDeflection=0.1,
                                   Relative=False)
        if not m.isSolid():
            if any(len(s.ancestorsOfType(e, Part.Face)) > 2 for e in s.Edges):
                note("tessellation", "skip", "solid %d: an edge has more than two faces" % i)
                continue  # non-manifold input (BRepCheck accepts it): the mesh is right to be open
            mm("tessellation", "not_closed", "solid %d: %d facets, open mesh" % (i, m.CountFacets))
            continue
        # Mesh.Volume sums in single precision about the origin: far from it the result is
        # quantised (68.5, 71.625 ...). Sum in double about the centre of the box instead.
        c = s.BoundBox.Center
        pts, facets = m.Topology
        pts = [p - c for p in pts]
        vol = sum(pts[a].dot(pts[b].cross(pts[d])) for a, b, d in facets) / 6.0
        if rel(abs(vol), s.Volume) > 0.02:
            mm("tessellation", "volume", "solid %d: mesh %.6g vs brep %.6g" % (i, vol, s.Volume))
        if vol < 0:
            mm("tessellation", "orientation", "solid %d: negative mesh volume" % i)
    note("mesh_volume", "ok")


def _value(v):
    """Comparable form: numbers rounded to 9 significant digits (placements, vectors, floats)."""
    def r(x):
        return float("%.9g" % x) if isinstance(x, float) else x
    if isinstance(v, App.Placement):
        # q and -q are the same rotation; make the sign unique by the first clearly non-zero
        # component (only w for half turns gives 4e-19 vs 0 with all other signs flipped)
        q = v.Rotation.Q
        lead = next((c for c in (q[3], q[0], q[1], q[2]) if abs(c) > 1e-12), 1.0)
        if lead < 0:
            q = tuple(-c for c in q)
        return ("P",) + tuple(r(c) for c in tuple(v.Base) + tuple(q))
    if isinstance(v, App.Vector):
        return ("V",) + tuple(r(c) for c in v)
    if hasattr(v, "Value") and hasattr(v, "Unit"):
        return r(float(v.Value))
    return r(v) if isinstance(v, float) else v


def _svg_paths(t):
    import re
    num = re.compile(r"-?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?")
    return {num.sub(lambda m: "%.10g" % (round(float(m.group()), 6) + 0.0), d)
            for d in re.findall(r' d="([^"]*)"', t)}


def _same(a, b):
    if isinstance(a, tuple) and isinstance(b, tuple) and len(a) == len(b):
        return all(_same(x, y) for x, y in zip(a, b))
    if isinstance(a, float) and isinstance(b, float):
        return abs(a - b) <= 1e-7 * max(1.0, abs(a), abs(b))
    if isinstance(a, str) and isinstance(b, str) and a != b and "<svg" in a[:200] and "<svg" in b[:200]:
        # SVG generated from shapes: BRep text keeps 15 significant digits for vertices, so after
        # save/reopen -13499.999999999998 may come back as -13500, and two edges that were 1e-12
        # apart become the same edge and are drawn once. Compare the set of paths, rounded.
        pa, pb = _svg_paths(a), _svg_paths(b)
        if pa == pb:
            return True
        # half circles: the large-arc flag of a 180 degree arc flips with the last bit of the angle
        import re
        arc = re.compile(r"(A \S+ \S+ \S+) [01] ")
        return {arc.sub(r"\1 * ", x) for x in pa} == {arc.sub(r"\1 * ", x) for x in pb}
    if isinstance(a, str) and isinstance(b, str) and a != b:
        # strings with numbers computed from shapes (CAM PathParams heights): the shape's last
        # digits move after save/reopen (BRep text), 2.999999999999993 vs 2.9999999999999005
        import re
        num = re.compile(r"-?\d+\.\d+(?:[eE][-+]?\d+)?")
        if num.sub("#", a) != num.sub("#", b):
            return False
        return all(abs(float(x) - float(y)) <= 1e-9 * max(1.0, abs(float(x)))
                   for x, y in zip(num.findall(a), num.findall(b)))
    return a == b


# FeaturePython objects whose Shape is only drawn in the 3D view and rebuilt by the GUI
DISPLAY_PROXIES = ("WorkingPlaneProxy", "_SectionPlane")


def display_only(o):
    return getattr(getattr(o, "Proxy", None), "__class__", type(None)).__name__ in DISPLAY_PROXIES


def output_property(o, name):
    """Values the object computes itself (read-only/output, or a direction that follows the sketch):
    an older file may have saved them stale or before the property existed."""
    try:
        st = o.getPropertyStatus(name)
        mode = o.getEditorMode(name)
    except Exception:
        return False
    if "ReadOnly" in st or "ReadOnly" in mode or 24 in st or 26 in st or "Output" in st:
        return name != "Placement"  # a derived Placement still has to come out the same
    if name == "Direction" and getattr(o, "UseCustomVector", True) is False:
        return True
    return False


def object_snapshot(doc):
    snap = {}
    for o in doc.Objects:
        vals = {}
        outs = set()
        for name in o.PropertiesList:
            if name.startswith("_"):
                continue  # internal bookkeeping (_ElementMapVersion ...)
            if output_property(o, name):
                outs.add(name)
                continue
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
        if sh is not None and hasattr(sh, "isNull") and not sh.isNull() and not display_only(o):
            shp = props(sh)
        snap[o.Name] = (o.TypeId, vals, shp, outs)
    return snap


def compare_snapshots(check, a, b):
    if set(a) != set(b):
        mm(check, "objects", "%d vs %d objects; missing %s"
           % (len(a), len(b), sorted(set(a) ^ set(b))[:5]))
    for name in sorted(set(a) & set(b)):
        ta, va, sa, oa = a[name]
        tb, vb, sb, ob = b[name]
        if ta != tb:
            mm(check, "type", "%s %s vs %s" % (name, ta, tb))
            continue
        for k in sorted((set(va) | set(vb)) - oa - ob):
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
        # files saved before 1.0 (old topological naming, refine and attachment code) are expected
        # to come out different: keep them apart from regressions on current files
        import re
        m = re.match(r"(\d+)\.(\d+)", getattr(doc, "getProgramVersion", lambda: "")() or "")
        saved = (int(m.group(1)), int(m.group(2))) if m else None
        legacy = saved is not None and saved < (1, 0)
        # saved by an older release: other OCC (edges split differently by HLR, offsets, refine)
        # and fixes since (BIM areas, window hinges) are expected; kept apart from same-version files
        here = tuple(int(x) for x in App.Version()[:2])
        older = saved is not None and not legacy and saved < here
        compare_snapshots("stored_vs_recomputed" + ("_pre1.0" if legacy else "_older" if older else ""),
                          stored, first)
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

# BOP-check findings that are not defects of a single shape: members of a compound may overlap,
# BOP needs C1 curves, and infinite/open edges cannot be checked at all
# BOPAlgo findings BRepCheck does not look for, on input data (same with FreeCAD 1.1.3/OCC 7.8.1):
# InvalidCurveOnSurface = 3D curve and pcurve further apart than the edge tolerance (STEP files);
# SelfIntersect = drawings whose wires cross themselves (DXF), faces of OCC's broken test shells.
_BOP_EXPECTED = ("GeomAbs_C0", "no end vertex", "InvalidCurveOnSurface", "SelfIntersect")


@guarded
def valid_vs_check(shapes):
    import re
    for i, s in enumerate(shapes):
        if len(s.Faces) > MAX_FACES or s.ShapeType in ("Compound", "CompSolid"):
            continue
        if s.ShapeType == "Solid" and abs(s.Volume) < 1e-9:
            continue  # flat "solid" in the input: BRepCheck accepts it, BOP sees the faces touch
        v = s.isValid()
        try:
            s.check(True)
            err = None
        except Exception as e:
            err = " ".join(str(e).split())
        if v and err and not any(x in err for x in _BOP_EXPECTED):
            kinds = sorted(set(re.findall(r"BOPAlgo[ _](\w+)", err))) or ["other"]
            mm("valid_vs_check", "check_fails_" + "+".join(kinds),
               "shape %d (%s): isValid() True but check(True) raises" % (i, s.ShapeType))
        if not err and not v:
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
    I, U, C = a.common(b), a.fuse(b), a.cut(b)
    vi, vu, vc = I.Volume, U.Volume, C.Volume
    scale = max(va, vb)
    tol = 1e-4 * scale
    if abs(vu - (va + vb - vi)) > tol or abs(vc - (va - vi)) > tol:
        # GProp is off on some BSpline surfaces (OCC): check the identities on fine meshes too
        ma, mb, mi, mu, mc = (mesh_vol(x) for x in (a, b, I, U, C))
        mtol = 2e-3 * max(ma, mb)
        if abs(mu - (ma + mb - mi)) <= mtol and abs(mc - (ma - mi)) <= mtol:
            note("booleans", "gprop", "%s: identities hold on meshes, not with GProp" % tag)
            return vi
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
        try:
            a.check(True)
        except Exception as e:
            if "SelfIntersect" in str(e):
                note("booleans", "skip", "solid %d: BOP check finds self-intersecting faces" % i)
                continue  # Boolean results on self-intersecting input are undefined
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
        bb = comp.BoundBox
        dims = sorted((bb.XLength, bb.YLength, bb.ZLength))
        # at 64x48 a 10x10x900 beam or the lines of a drawing are below one pixel: only a solid
        # that should cover a few pixels counts
        visible = comp.Solids and dims[2] > 0 and dims[1] / dims[2] * 48 >= 3
        if visible and len(set(raw)) <= 2:
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
            # GProp integrates with a fixed number of Gauss points: a few 1e-5 apart after scaling
            if rel(k.Volume, 8 * s.Volume) > 1e-4:
                mm("scale2", "volume", "solid %d: %.6g vs 8x %.6g" % (i, k.Volume, 8 * s.Volume))
            if rel(k.Area, 4 * s.Area) > 1e-4:
                mm("scale2", "area", "solid %d: %.6g vs 4x %.6g" % (i, k.Area, 4 * s.Area))
            if p["valid"] and not k.isValid():
                mm("scale2", "valid", "solid %d" % i)
        m = s.mirror(App.Vector(0, 0, 0), App.Vector(1, 0, 0))
        if rel(abs(m.Volume), s.Volume) > 1e-6:
            mm("mirror", "volume", "solid %d: %.6g vs %.6g" % (i, m.Volume, s.Volume))
        g = s.transformGeometry(App.Matrix(2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1))
        if rel(g.Volume, 8 * s.Volume) > 2e-2 and rel(mesh_vol(g), 8 * mesh_vol(s)) > 2e-3:  # NURBS conversion is approximate; GProp too
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
