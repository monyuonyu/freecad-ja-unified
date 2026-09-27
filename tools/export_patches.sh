#!/bin/bash
# FreeCAD の clone（unified-ui ブランチ）から patches/ を作り直す。使い方: tools/export_patches.sh [FreeCAD の clone]
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
SRC=${1:-$HOME/freecad-src}
BASE=b48098efaa2560d0aa989d7f6e61cdb7f831877f
ONDSEL_BASE=4be80eef02a3486cda0d78f3ccbb308d207a9639
rm -f "$HERE"/patches/freecad/*.patch "$HERE"/patches/ondselsolver/*.patch
git -C "$SRC" format-patch -q "$BASE"..unified-ui -o "$HERE/patches/freecad"
# サブモジュール（OndselSolver）の参照だけを動かすコミットは除く（中身は patches/ondselsolver にある）
for p in "$HERE"/patches/freecad/*.patch; do
  files=$(grep '^diff --git ' "$p" | awk '{print $3}' | sort -u)
  if [ "$files" = "a/src/3rdParty/OndselSolver" ]; then rm "$p"; fi
done
git -C "$SRC/src/3rdParty/OndselSolver" format-patch -q "$ONDSEL_BASE"..HEAD -o "$HERE/patches/ondselsolver"
echo "freecad: $(ls "$HERE"/patches/freecad | wc -l)  ondselsolver: $(ls "$HERE"/patches/ondselsolver | wc -l)"
