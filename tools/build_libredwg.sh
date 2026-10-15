#!/bin/bash
# LibreDWG（本家の版＋patches/libredwg）から dwg2dxf / dxf2dwg を作る。リリースの手順と手元の両方で使う。
# 使い方: tools/build_libredwg.sh <出力先> [linux|win64]
#   linux: この機体用（libredwg は静的、libc は動的）
#   win64: MinGW-w64 でクロスビルドした Windows 用（-static。DLL 不要）
set -euo pipefail
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
TARGET=${2:-linux}
VERSION=0.14.8601
SHA256=f1140a219d6edb291e55fad740be6c5e49c046fee558860575aeef110caa4ef9
URL=https://github.com/LibreDWG/libredwg/releases/download/$VERSION/libredwg-$VERSION.tar.xz

WORK=$(mktemp -d)
cd "$WORK"
if [ -n "${LIBREDWG_TARBALL:-}" ]; then
  cp "$LIBREDWG_TARBALL" libredwg.tar.xz
else
  curl -fsSL -o libredwg.tar.xz "$URL"
fi
echo "$SHA256  libredwg.tar.xz" | sha256sum -c -
mkdir src && tar xf libredwg.tar.xz -C src --strip-components=1
cd src
# パッチは git の形式なので git am で当てる（名前の無い環境でも当たるように仮の名前で）
git init -q && git add -A && git -c user.name=build -c user.email=build@localhost commit -qm base
git -c user.name=build -c user.email=build@localhost am -q "$HERE"/patches/libredwg/*.patch
# 当てた後の時刻のずれで autotools・gperf・makeinfo を呼ばないように、生成物を新しくする
touch aclocal.m4
sleep 1
touch configure src/config.h.in
sleep 1
find . -name Makefile.in -exec touch {} +
touch src/objects.c
host=()
cflags="-O2 -g0"
ldflags=""
exe=""
if [ "$TARGET" = win64 ]; then
  host=(--host=x86_64-w64-mingw32)
  ldflags="-static"
  exe=".exe"
fi
./configure "${host[@]}" --disable-shared --enable-static --disable-bindings --disable-python \
  CFLAGS="$cflags" LDFLAGS="$ldflags" > configure.log 2>&1 || { tail -30 configure.log; exit 1; }
make -j"$(nproc)" -C src MAKEINFO=true > build.log 2>&1 || { tail -30 build.log; exit 1; }
# Windows: libtool の -static は libtool のライブラリだけ。configure が MinGW に付ける -lssp も
# 静的に入れるため、実行ファイルは -all-static でつなぐ
linkflags=""
[ "$TARGET" = win64 ] && linkflags="-all-static"
# PROGRAMS: 作る道具（既定は FreeCAD が使う 2 つ。libredwg-fixes のリリースでは dwgread なども）
programs=(${PROGRAMS:-dwg2dxf dxf2dwg})
make -C programs MAKEINFO=true LDFLAGS="$ldflags $linkflags" "${programs[@]/%/$exe}" >> build.log 2>&1 \
  || { tail -30 build.log; exit 1; }
for p in "${programs[@]}"; do
  cp "programs/$p$exe" "$OUT/"
  [ "$TARGET" = win64 ] || strip "$OUT/$p$exe"
done
[ "$TARGET" = win64 ] && x86_64-w64-mingw32-strip "$OUT"/*.exe
# Windows 用は Windows に必ずある DLL だけに頼ること
if [ "$TARGET" = win64 ]; then
  dlls=$(x86_64-w64-mingw32-objdump -p "$OUT/dwg2dxf.exe" | awk '/DLL Name/ {print $3}' | tr 'A-Z' 'a-z' | sort -u | tr '\n' ' ')
  echo "DLLs: $dlls"
  for d in $dlls; do
    case "$d" in kernel32.dll|msvcrt.dll|user32.dll|advapi32.dll|shell32.dll|ws2_32.dll) ;;
      *) echo "dwg2dxf.exe needs $d"; exit 1 ;; esac
  done
fi
echo "LibreDWG $VERSION + $(ls "$HERE"/patches/libredwg/*.patch | wc -l) patches ($TARGET) -> $OUT"
ls -l "$OUT"
rm -rf "$WORK"
