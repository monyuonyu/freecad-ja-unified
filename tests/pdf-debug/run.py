# Windows の図面 PDF の子プロセスが落ちる件の調べ: TestDrawingPdf と同じ文書を作り、子を何回も走らせて
# 落ちた回の出力を全部出す。  freecadcmd run.py <回数> [section|nosection]
import json, os, subprocess, sys, tempfile
import FreeCAD as App
import DrawingPdf

args = [a for a in sys.argv if a.isdigit() or a in ("section", "nosection")]
n = int(args[0]) if args else 5
with_section = "nosection" not in args
tmp = tempfile.mkdtemp()
doc = App.newDocument("drawpdf")
box = doc.addObject("Part::Box", "Box")
template = os.path.join(App.getResourceDir(), "Mod", "TechDraw", "Templates", "Default_Template_A4_Landscape.svg")
for label in ("P1", "Second"):
    page = doc.addObject("TechDraw::DrawPage", "Page")
    page.Label = label
    tpl = doc.addObject("TechDraw::DrawSVGTemplate", "Template")
    tpl.Template = template
    page.Template = tpl
    view = doc.addObject("TechDraw::DrawViewPart", "View")
    page.addView(view)
    view.Source = [box]
if with_section:
    section = doc.addObject("TechDraw::DrawViewSection", "Section")
    page.addView(section)
    section.BaseView = view
    section.Source = [box]
    section.SectionSymbol = "A"
    section.SectionOrigin = App.Vector(5, 5, 5)
    section.SectionDirection = "Right"
    section.Caption = "SECTION <REF> - <REF>"
doc.recompute()
path = os.path.join(tmp, "m.FCStd")
doc.saveAs(path)
App.closeDocument(doc.Name)

bad = 0
for i in range(n):
    result = os.path.join(tmp, "result%d.json" % i)
    job = {"path": path, "out": os.path.join(tmp, "out.pdf"), "pages": None, "seconds": 60, "result": result}
    env = dict(os.environ)
    env[DrawingPdf.JOB_ENV] = json.dumps(job)
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONFAULTHANDLER"] = "1"
    proc = subprocess.run([DrawingPdf._freecadcmd(), "-c", "import DrawingPdf\nDrawingPdf._child()\n"],
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    ok = os.path.isfile(result)
    out = proc.stdout.decode("utf-8", "replace")
    print("run %d: exit %s, result %s, emitted without the GIL %d" % (i, proc.returncode, ok, out.count("without the GIL")), flush=True)
    if not ok:
        bad += 1
        print(out, flush=True)
print("FAILED %d of %d (section=%s)" % (bad, n, with_section), flush=True)
