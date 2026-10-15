#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later
"""Download the corpus described in corpus.tsv.

  fetch_corpus.py --out corpus [--freecad-src FreeCAD] [--only name,name]

Writes corpus/<name>/<file>, corpus/manifest.txt (one absolute path per line, for run_corpus.py)
and corpus/sources.tsv (name, file, URL, bytes). Uses $GH_TOKEN for the GitHub API if set.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def get(url, token=None, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "freecad-ja-bughunt"})
            if token and "api.github.com" in url:
                req.add_header("Authorization", "Bearer " + token)
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def pick(entries, rx, nmax, bmax):
    rx = re.compile(rx)
    c = [(p, s) for p, s in entries if rx.search(p) and s <= bmax and s > 0]
    c.sort(key=lambda e: hashlib.sha1(e[0].encode()).hexdigest())
    return c[:nmax]


def safe(path):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", path)[-120:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--freecad-src")
    ap.add_argument("--spec", default=os.path.join(HERE, "corpus.tsv"))
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    only = set(filter(None, a.only.split(",")))
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    manifest, sources = [], []
    trees = {}
    for line in open(a.spec):
        if not line.strip() or line.startswith("#"):
            continue
        name, repo, commit, rx, nmax, bmax = line.rstrip("\n").split("\t")
        if only and name not in only:
            continue
        nmax, bmax = int(nmax), int(bmax)
        d = os.path.join(out, name)
        os.makedirs(d, exist_ok=True)
        if repo == "freecad":
            if not a.freecad_src:
                print("skip %s (no --freecad-src)" % name)
                continue
            files = subprocess.run(["git", "-C", a.freecad_src, "ls-files"], capture_output=True,
                                   text=True, check=True).stdout.split("\n")
            ent = [(p, os.path.getsize(os.path.join(a.freecad_src, p))) for p in files
                   if p and os.path.isfile(os.path.join(a.freecad_src, p))]
            for p, s in pick(ent, rx, nmax, bmax):
                dst = os.path.join(d, safe(p))
                if not os.path.exists(dst):
                    os.symlink(os.path.join(os.path.abspath(a.freecad_src), p), dst)
                manifest.append(dst)
                sources.append((name, p, "freecad-src:" + p, s))
            continue
        key = (repo, commit)
        if key not in trees:
            t = json.loads(get("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % key, token))
            trees[key] = [(e["path"], e["size"]) for e in t["tree"] if e["type"] == "blob"]
        n = 0
        for p, s in pick(trees[key], rx, nmax, bmax):
            url = "https://raw.githubusercontent.com/%s/%s/%s" % (repo, commit, urllib.request.quote(p))
            dst = os.path.join(d, safe(p))
            if not os.path.exists(dst):
                try:
                    data = get(url)
                except Exception as e:
                    print("  fail %s: %s" % (url, e))
                    continue
                if data.startswith(b"version https://git-lfs"):
                    continue
                with open(dst, "wb") as f:
                    f.write(data)
            manifest.append(dst)
            sources.append((name, p, url, s))
            n += 1
        print("%-20s %3d files" % (name, n), flush=True)
    with open(os.path.join(out, "manifest.txt"), "w") as f:
        f.write("\n".join(manifest) + "\n")
    with open(os.path.join(out, "sources.tsv"), "w") as f:
        for r in sources:
            f.write("\t".join(map(str, r)) + "\n")
    print("total %d files" % len(manifest))


if __name__ == "__main__":
    main()
