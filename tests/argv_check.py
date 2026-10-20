# 日本語のパスの受け渡しの試験（tests/windows_argv_smoke.ps1 から使う）:
#   FreeCADCmd argv_check.py -- <開く .jww> <結果の JSON>
# sys.argv をそのまま書き出し、渡された .jww を開いて物の数も書く
import json
import os
import sys

res = {"argv": sys.argv}
path = sys.argv[1]
res["exists"] = os.path.isfile(path)
import importJWW

doc = importJWW.open(path)
res["objects"] = len(doc.Objects) if doc else -1
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False)
print("argv_check done")
