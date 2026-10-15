#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Run every corpus file through a (sanitizer) FreeCADCmd and keep the raw output per case.

  run_corpus.py --freecadcmd build/bin/FreeCADCmd --list corpus/manifest.txt --out results \
                [--jobs 2] [--timeout 600] [--cli] [--dwg2dxf PATH] [--deadline SECONDS]
                [--tests "TestPartApp TestMeshApp ..."]

Per case: results/cases/<id>/{cmd,stdout,stderr,status.json}. results/results.jsonl has one line per
case. Nothing is summarised here; triage.py reads the case folders.
Cases: "worker" (tools/bughunt/worker.py on the file), "cli" (FreeCADCmd <file> --render ...
--export-svg ... --export-polygons ... --export-pptx ... --interference-report ...) for shape files,
"test:<suite>" (FreeCADCmd -t <suite>).
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import signal
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SHAPE_EXT = {"fcstd", "step", "stp", "iges", "igs", "brep", "brp"}


def sanitizer_env(args, home):
    env = dict(os.environ)
    env.update({
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "HOME": home, "XDG_CONFIG_HOME": os.path.join(home, "config"),
        "XDG_DATA_HOME": os.path.join(home, "data"), "XDG_CACHE_HOME": os.path.join(home, "cache"),
        "QT_QPA_PLATFORM": "offscreen",
        "ASAN_OPTIONS": ":".join([
            "detect_leaks=0", "halt_on_error=0", "abort_on_error=0", "allocator_may_return_null=1",
            "detect_odr_violation=0", "handle_segv=1", "allow_user_segv_handler=0", "handle_abort=1", "symbolize=1",
            "fast_unwind_on_malloc=0", "malloc_context_size=10", "detect_stack_use_after_return=0",
            "alloc_dealloc_mismatch=0", "print_summary=1",
        ] + (["external_symbolizer_path=" + args.symbolizer] if args.symbolizer else [])),
        "UBSAN_OPTIONS": "print_stacktrace=1:halt_on_error=0:report_error_type=1:symbolize=1"
                         + (":external_symbolizer_path=" + args.symbolizer if args.symbolizer else ""),
        "PYTHONFAULTHANDLER": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    if args.sanlib:
        env["LD_LIBRARY_PATH"] = args.sanlib + ":" + env.get("LD_LIBRARY_PATH", "")
    if args.dwg2dxf:
        env["PATH"] = os.path.dirname(args.dwg2dxf) + ":" + env["PATH"]
    return env


def run_case(args, case):
    cdir = os.path.join(args.out, "cases", case["id"])
    os.makedirs(cdir, exist_ok=True)
    work = os.path.join(cdir, "work")
    os.makedirs(work, exist_ok=True)
    home = tempfile.mkdtemp(prefix="bh-home-")
    env = sanitizer_env(args, home)
    if case["kind"] == "worker":
        env.update({"BH_IN": case["file"], "BH_OUT": work})
        if args.dwg2dxf:
            env["BH_DWG2DXF"] = args.dwg2dxf
        cmd = [args.freecadcmd, os.path.join(HERE, "worker.py")]
    elif case["kind"] == "cli":
        o = os.path.join(work, "v")
        cmd = [args.freecadcmd, case["file"], "--render", o + ".png", "--size", "160x120",
               "--export-svg", o + ".svg", "--export-polygons", o + ".json",
               "--export-pptx", o + ".pptx", "--interference-report", o + "-int.json"]
    else:
        cmd = [args.freecadcmd, "-t", case["suite"]]
    t0 = time.time()
    status = {"id": case["id"], "kind": case["kind"], "file": case.get("file"),
              "suite": case.get("suite"), "cmd": cmd}
    with open(os.path.join(cdir, "stdout"), "wb") as so, open(os.path.join(cdir, "stderr"), "wb") as se:
        p = subprocess.Popen(cmd, stdout=so, stderr=se, stdin=subprocess.DEVNULL, env=env,
                             cwd=work, start_new_session=True)
        try:
            rc = p.wait(timeout=case.get("timeout", args.timeout))
            status["timeout"] = False
        except subprocess.TimeoutExpired:
            os.killpg(p.pid, signal.SIGKILL)  # whole process group (dwg2dxf children too)
            rc = p.wait()
            status["timeout"] = True
    status["rc"] = rc
    status["signal"] = -rc if rc < 0 else None
    status["seconds"] = round(time.time() - t0, 1)
    subprocess.run(["rm", "-rf", home])
    # keep outputs small: drop big export files, keep names and sizes
    sizes = {}
    for root, _, files in os.walk(work):
        for f in files:
            fp = os.path.join(root, f)
            sizes[f] = os.path.getsize(fp)
            os.remove(fp)
    status["outputs"] = sizes
    with open(os.path.join(cdir, "status.json"), "w") as f:
        json.dump(status, f)
    return status


def case_id(kind, key):
    h = hashlib.sha1(key.encode()).hexdigest()[:10]
    base = os.path.basename(key)[:40].replace(" ", "_")
    return "%s-%s-%s" % (kind.replace(":", "_"), h, base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freecadcmd", required=True)
    ap.add_argument("--list", help="text file, one corpus file path per line")
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--cli", action="store_true", help="also run the CLI view/export flags on shape files")
    ap.add_argument("--cli-max", type=int, default=80)
    ap.add_argument("--dwg2dxf")
    ap.add_argument("--sanlib", help="directory with libclang_rt.asan*.so")
    ap.add_argument("--symbolizer")
    ap.add_argument("--tests", default="", help="space separated test suites for FreeCADCmd -t")
    ap.add_argument("--test-timeout", type=int, default=2400)
    ap.add_argument("--deadline", type=int, default=0, help="stop starting new cases after N seconds")
    args = ap.parse_args()
    args.freecadcmd = os.path.abspath(args.freecadcmd)
    args.out = os.path.abspath(args.out)
    os.makedirs(args.out, exist_ok=True)

    cases = []
    for suite in args.tests.split():
        cases.append({"id": case_id("test", suite), "kind": "test", "suite": suite,
                      "timeout": args.test_timeout})
    files = []
    if args.list:
        files = [os.path.abspath(l.strip()) for l in open(args.list) if l.strip() and not l.startswith("#")]
    for f in files:
        cases.append({"id": case_id("worker", f), "kind": "worker", "file": f})
    ncli = 0
    for f in files:
        if args.cli and os.path.splitext(f)[1].lower().lstrip(".") in SHAPE_EXT and ncli < args.cli_max:
            ncli += 1
            cases.append({"id": case_id("cli", f), "kind": "cli", "file": f})

    done = {}
    rpath = os.path.join(args.out, "results.jsonl")
    if os.path.exists(rpath):  # resume
        for l in open(rpath):
            s = json.loads(l)
            done[s["id"]] = s
    todo = [c for c in cases if c["id"] not in done]
    print("cases: %d total, %d to run" % (len(cases), len(todo)), flush=True)
    t0 = time.time()
    n = 0
    with open(rpath, "a") as rf, cf.ThreadPoolExecutor(args.jobs) as ex:
        futs = {}
        it = iter(todo)
        stop = False

        def submit_one():
            nonlocal stop
            if stop:
                return
            if args.deadline and time.time() - t0 > args.deadline:
                stop = True
                return
            c = next(it, None)
            if c is not None:
                futs[ex.submit(run_case, args, c)] = c

        for _ in range(args.jobs):
            submit_one()
        while futs:
            fin, _ = cf.wait(list(futs), return_when=cf.FIRST_COMPLETED)
            for fu in fin:
                futs.pop(fu)
                s = fu.result()
                rf.write(json.dumps(s) + "\n")
                rf.flush()
                n += 1
                flag = "TIMEOUT" if s["timeout"] else ("rc=%s" % s["rc"])
                print("[%d/%d] %s %s %.0fs" % (n, len(todo), s["id"], flag, s["seconds"]), flush=True)
                submit_one()
    if stop:
        print("deadline reached; %d cases not started" % (len(todo) - n), flush=True)


if __name__ == "__main__":
    main()
