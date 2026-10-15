#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Summarise a run_corpus.py result folder: dedupe sanitizer reports, list crashes and hangs.

  triage.py results [--freecad-src FreeCAD --base <sha>] [--md report.md] [--json findings.json]

Sanitizer reports are deduplicated by (type, top 3 frames inside FreeCAD/OCC/Coin/...).
With --freecad-src/--base, the FreeCAD frames are blamed: "ours" when a line comes from a commit
after the base (our patches), "upstream" otherwise.
"""
import argparse
import collections
import json
import os
import re
import subprocess

ASAN_HEAD = re.compile(r"^==\d+==ERROR: (AddressSanitizer|LeakSanitizer|MemorySanitizer): ([\w-]+)(.*)")
UBSAN = re.compile(r"^(.+?):(\d+):(\d+): runtime error: (.*)")
FRAME = re.compile(r"^\s*#(\d+) 0x[0-9a-f]+ in (.+?) (/\S+?)(?::(\d+))?(?::\d+)?$")
FRAME_MOD = re.compile(r"^\s*#(\d+) 0x[0-9a-f]+ (?:in (.+?) )?\((\S+?)\+0x[0-9a-f]+\)")
PYEXC = re.compile(r"^(?:<class '([\w.]+)'>|([\w.]*(?:Error|Exception|Failure)))[:>]?\s*(.*)$")
CPP_HINT = re.compile(r"Standard_|OCC|Unknown C\+\+|C\+\+ exception|std::|Base\.|FreeCADError|"
                      r"SystemError|bad_alloc|Segmentation|access violation", re.I)


def component(path, func=""):
    p = path or ""
    if "/3rdParty/coin" in p or "libCoin" in p:
        return "Coin"
    if "/3rdParty/" in p:
        return "3rdParty"
    if "/src/" in p and ("freecad" in p.lower() or "FreeCAD" in p) and "/opencascade/" not in p:
        return "FreeCAD"
    if "opencascade" in p or re.search(r"libTK\w+\.so", p):
        return "OCC"
    if "libQt" in p or "/qt" in p.lower():
        return "Qt"
    if "python" in p.lower():
        return "Python"
    if re.search(r"/lib/(Part|Mesh|Import|Sketcher|PartDesign|TechDraw|Surface|Points|MeshPart|"
                 r"Fem|Measure|Spreadsheet|Assembly|Materials|Path|Inspection|ReverseEngineering|"
                 r"Draft)\w*\.so|libFreeCAD|FreeCADCmd|/Mod/", p):
        return "FreeCAD"
    return "other"


def parse_frames(lines, i):
    frames = []
    while i < len(lines):
        l = lines[i]
        m = FRAME.match(l)
        if m:
            frames.append({"n": int(m.group(1)), "func": m.group(2), "file": m.group(3),
                           "line": int(m.group(4)) if m.group(4) else None})
        else:
            m = FRAME_MOD.match(l)
            if m:
                frames.append({"n": int(m.group(1)), "func": m.group(2) or "?", "file": m.group(3),
                               "line": None})
            elif frames and not l.strip():
                break
            elif frames and not l.lstrip().startswith("#"):
                break
        i += 1
    return frames, i


def short_func(f):
    f = re.sub(r"\(.*", "", f)  # drop argument lists
    f = re.sub(r"<[^<>]*>", "<>", f)
    return f[-90:]


def key_frames(frames):
    out = []
    for f in frames:
        if f["n"] is not None and f.get("_stop"):
            break
        c = component(f["file"], f["func"])
        if c in ("other", "Python") or "sanitizer" in f["file"] or "libclang_rt" in f["file"]:
            continue
        out.append(f)
        if len(out) == 3:
            break
    return out


def parse_stderr(text):
    """Return a list of sanitizer reports in this output."""
    lines = text.splitlines()
    reps = []
    i = 0
    while i < len(lines):
        l = lines[i]
        m = ASAN_HEAD.match(l)
        if m:
            kind = m.group(2)
            extra = m.group(3)
            if kind == "SEGV" or "signal" in extra or kind in ("BUS", "FPE", "ILL", "ABRT"):
                kind = "SEGV" if kind == "SEGV" else kind
            frames, i = parse_frames(lines, i + 1)
            reps.append({"tool": m.group(1), "type": kind, "msg": (m.group(2) + m.group(3))[:200],
                         "frames": frames})
            continue
        m = UBSAN.match(l)
        if m and "runtime error" in l:
            msg = m.group(4)
            frames, j = parse_frames(lines, i + 1)
            cat = re.sub(r"0x[0-9a-f]+|-?\d+(\.\d+)?(e[+-]?\d+)?|'[^']*'", "N", msg)[:120]
            reps.append({"tool": "UBSan", "type": "ub: " + cat, "msg": msg[:200],
                         "loc": "%s:%s" % (m.group(1), m.group(2)), "frames": frames})
            i = max(j, i + 1)
            continue
        i += 1
    return reps


_blame_cache = {}


def blame(src, base, path, line):
    """'ours' when path:line was last changed after base, else 'upstream' (None if unknown)."""
    if not src or not line:
        return None
    k = (path, line)
    if k in _blame_cache:
        return _blame_cache[k]
    rel = None
    m = re.search(r"(src/.*)$", path)
    if m and os.path.exists(os.path.join(src, m.group(1))):
        rel = m.group(1)
    r = None
    if rel:
        b = subprocess.run(["git", "-C", src, "blame", "--porcelain", "-L", "%d,%d" % (line, line),
                            "HEAD", "--", rel], capture_output=True, text=True)
        if b.returncode == 0 and b.stdout:
            sha = b.stdout.split()[0]
            anc = subprocess.run(["git", "-C", src, "merge-base", "--is-ancestor", sha, base])
            r = "upstream" if anc.returncode == 0 else "ours:" + sha[:9]
    _blame_cache[k] = r
    return r


def stages(stdout):
    out = {}
    for l in stdout.splitlines():
        if l.startswith("BH "):
            p = l.split(" ", 3)
            if len(p) >= 3:
                out[p[1]] = (p[2], p[3] if len(p) > 3 else "")
    return out


def tracebacks(stderr):
    """Last line of each Python traceback that hints at a C++ error."""
    res = []
    for l in stderr.splitlines():
        l = l.strip()
        m = PYEXC.match(l)
        if m and CPP_HINT.search(l):
            res.append(l[:200])
    return res


def repro(st):
    if st["kind"] == "worker":
        return "BH_IN=%s BH_OUT=/tmp/bh FreeCADCmd tools/bughunt/worker.py" % st["file"]
    return " ".join(os.path.basename(c) if i == 0 else c for i, c in enumerate(st["cmd"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--freecad-src")
    ap.add_argument("--base", default="b48098efaa2560d0aa989d7f6e61cdb7f831877f")
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()

    statuses = [json.loads(l) for l in open(os.path.join(a.results, "results.jsonl"))]
    issues = collections.OrderedDict()
    hangs, crashes, stage_fail, pyexc, test_fail = [], [], collections.Counter(), {}, []
    stage_examples = {}
    mism = collections.OrderedDict()  # (check, kind, ext) -> [count, files, example detail, status]
    for st in statuses:
        cdir = os.path.join(a.results, "cases", st["id"])
        so = open(os.path.join(cdir, "stdout"), errors="replace").read()
        se = open(os.path.join(cdir, "stderr"), errors="replace").read()
        reps = parse_stderr(se + "\n" + so)
        for r in reps:
            kf = key_frames(r["frames"])
            key = (r["type"], r.get("loc") if r["tool"] == "UBSan" else None,
                   tuple(short_func(f["func"]) for f in kf))
            if key not in issues:
                top = kf[0] if kf else (r["frames"][0] if r["frames"] else {"file": r.get("loc", "?"), "func": "?", "line": None})
                comp = component(top["file"], top["func"]) if kf or r["frames"] else component(r.get("loc", ""))
                owner = None
                for f in kf:
                    if component(f["file"]) == "FreeCAD":
                        owner = blame(a.freecad_src, a.base, f["file"], f["line"])
                        if owner and owner.startswith("ours"):
                            break
                if r["tool"] == "UBSan" and owner is None and r.get("loc"):
                    p, ln = r["loc"].rsplit(":", 1)
                    if component(p) == "FreeCAD":
                        owner = blame(a.freecad_src, a.base, p, int(ln))
                issues[key] = {"type": r["type"], "tool": r["tool"], "msg": r["msg"], "loc": r.get("loc"),
                               "component": comp, "owner": owner,
                               "frames": ["%s %s:%s" % (short_func(f["func"]), f["file"].split("/src/")[-1].split("/opencascade/")[-1], f["line"])
                                          for f in (kf or r["frames"][:3])],
                               "count": 0, "cases": [], "repro": repro(st), "example": st["id"]}
            issues[key]["count"] += 1
            if st["id"] not in issues[key]["cases"]:
                issues[key]["cases"].append(st["id"])
        if st["timeout"]:
            hangs.append(st)
        elif st["rc"] not in (0, 1) and not reps:
            crashes.append((st, se.strip().splitlines()[-3:] if se.strip() else []))
        sg = stages(so)
        for name, (status, detail) in sg.items():
            if status == "fail":
                k = (name, re.sub(r"\d+", "N", detail)[:100])
                stage_fail[k] += 1
                stage_examples.setdefault(k, st)
        if (st["kind"] == "worker" and sg and "done" not in sg and not st["timeout"] and not reps
                and sg.get("load", ("",))[0] != "fail"):
            last = list(sg)[-1]
            crashes.append((st, ["stopped after stage %s (rc=%s)" % (last, st["rc"])]))
        ext = os.path.splitext(st.get("file") or "")[1].lower().lstrip(".")
        for l in so.splitlines():
            p = l.split(" ", 3)
            if l.startswith("BH-MM ") and len(p) >= 3:
                k = (p[1], p[2], ext)
            elif l.startswith("BH-CK ") and len(p) >= 3 and p[2] == "error":
                det = p[3] if len(p) > 3 else ""
                k = (p[1], "check raised: " + re.sub(r"\d+", "N", det.split(":")[0])[:60], ext)
            else:
                continue
            e = mism.setdefault(k, [0, [], (p[3] if len(p) > 3 else ""), st])
            e[0] += 1
            if st["id"] not in e[1]:
                e[1].append(st["id"])
        for t in tracebacks(se):
            k = re.sub(r"\d+", "N", t)[:120]
            pyexc.setdefault(k, []).append(st["id"])
        if st["kind"] == "test":
            m = re.findall(r"^(FAILED \(.*\)|OK.*|Ran \d+ tests.*)$", se + "\n" + so, re.M)
            test_fail.append((st["suite"], st["rc"], st["timeout"], " / ".join(m[-2:]), st["seconds"]))

    kinds = collections.Counter(s["kind"] for s in statuses)
    md = ["# bughunt report", "",
          "cases: %d (%s); timeouts: %d; crashes without a full worker run: %d; unique sanitizer issues: %d"
          % (len(statuses), ", ".join("%s %d" % kv for kv in kinds.items()), len(hangs), len(crashes), len(issues)),
          "", "## Unique sanitizer issues", "",
          "| # | type | component | owner | top frames | hits | reproducer |", "|---|---|---|---|---|---|---|"]
    for n, (k, v) in enumerate(issues.items(), 1):
        md.append("| %d | %s | %s | %s | %s | %d | `%s` |" % (
            n, v["type"].replace("|", "/"), v["component"], v["owner"] or "?",
            "<br>".join(x.replace("|", "/") for x in v["frames"]) or v.get("loc") or "?",
            v["count"], v["repro"]))
    md += ["", "## Silent mismatches (grouped by check, kind, file type)", "",
           "| # | check | kind | ext | files | hits | example detail | reproducer |", "|---|---|---|---|---|---|---|---|"]
    for n, ((chk, kind, ext), (cnt, ids, det, st)) in enumerate(
            sorted(mism.items(), key=lambda kv: -len(kv[1][1])), 1):
        md.append("| %d | %s | %s | %s | %d | %d | %s | `%s` |" % (
            n, chk, kind, ext, len(ids), cnt, det.replace("|", "/")[:120], repro(st)))
    md += ["", "## Hangs (timeout)", ""]
    md += ["- %s `%s` (%ss)" % (s["kind"], s.get("file") or s.get("suite"), s["seconds"]) for s in hangs] or ["none"]
    md += ["", "## Crashes / abnormal exits without sanitizer report", ""]
    md += ["- rc=%s signal=%s %s `%s` — %s" % (s["rc"], s["signal"], s["kind"], s.get("file") or s.get("suite"),
                                               " | ".join(x[:150] for x in tail)) for s, tail in crashes] or ["none"]
    md += ["", "## Test suites", "", "| suite | rc | timeout | result | s |", "|---|---|---|---|---|"]
    md += ["| %s | %s | %s | %s | %s |" % t for t in test_fail]
    md += ["", "## Stage failures (Python-level, grouped)", "", "| stage | detail | n | example |", "|---|---|---|---|"]
    for (name, det), n in stage_fail.most_common(60):
        md.append("| %s | %s | %d | %s |" % (name, det.replace("|", "/"), n,
                                              os.path.basename(stage_examples[(name, det)].get("file") or "")))
    md += ["", "## Python exceptions that look like C++ errors (grouped)", ""]
    for k, ids in sorted(pyexc.items(), key=lambda kv: -len(kv[1]))[:40]:
        md.append("- %d× `%s` (e.g. %s)" % (len(ids), k, ids[0]))
    text = "\n".join(md) + "\n"
    if a.md:
        open(a.md, "w").write(text)
    else:
        print(text)
    if a.json:
        json.dump({"mismatches": [{"check": k[0], "kind": k[1], "ext": k[2], "files": len(v[1]),
                                   "hits": v[0], "detail": v[2], "example": v[3]["id"],
                                   "repro": repro(v[3])} for k, v in mism.items()],
                   "issues": list(issues.values()), "hangs": [s["id"] for s in hangs],
                   "crashes": [(s["id"], t) for s, t in crashes]}, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
