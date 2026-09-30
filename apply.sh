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
# 同梱のサブモジュール（OndselSolver・Coin・Pivy・GSL・AddonManager）を全部取る。Coin と Pivy が無いと cmake で止まる
git submodule update --init --recursive
# FreeCAD のソースは CRLF のファイルが多いので --keep-cr が要る
# git am は当てた人の名前を記録する。そのリポジトリで git に名前が無ければ仮の名前で当てる
am() {
  local repo=$1; shift
  if git -C "$repo" config user.email >/dev/null 2>&1; then
    git -C "$repo" am --keep-cr "$@"
  else
    GIT_COMMITTER_NAME="freecad-ja-unified apply.sh" GIT_COMMITTER_EMAIL="apply@localhost" \
      git -C "$repo" am --keep-cr "$@"
  fi
}
am . "$HERE"/patches/freecad/*.patch
am src/3rdParty/OndselSolver "$HERE"/patches/ondselsolver/*.patch
echo "当てた。ビルド手順は README を参照"
