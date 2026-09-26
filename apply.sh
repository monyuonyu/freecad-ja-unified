#!/bin/bash
# FreeCAD の clone にパッチを当てる。使い方: ./apply.sh <FreeCAD の clone>
# 元にした版は BASE（下記）。新しい main に当てる場合は、当たらないパッチを直す必要があるかもしれない。
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
SRC=${1:?FreeCAD の clone のパス}
BASE=b48098efaa2560d0aa989d7f6e61cdb7f831877f
ONDSEL_BASE=4be80eef02a3486cda0d78f3ccbb308d207a9639
cd "$SRC"
if ! git merge-base --is-ancestor "$BASE" HEAD 2>/dev/null; then
  echo "注意: HEAD は元にした版 $BASE を含んでいない（当たらない可能性がある）" >&2
fi
git submodule update --init src/3rdParty/OndselSolver
# FreeCAD のソースは CRLF のファイルが多いので --keep-cr が要る
git am --keep-cr "$HERE"/patches/freecad/*.patch
git -C src/3rdParty/OndselSolver am --keep-cr "$HERE"/patches/ondselsolver/*.patch
echo "当てた。ビルド手順は README を参照"
