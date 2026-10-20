#!/bin/bash
# jww-tools（Jw_cad の図面 .jww/.jws → DXF）の jww2dxf を作る。リリースの手順と手元の両方で使う。
# 使い方: tools/build_jww2dxf.sh <出力先> [linux|win64]
#   linux: この機体用（静的リンク）
#   win64: MinGW-w64 でクロスビルドした Windows 用（静的リンク。DLL 不要）
set -euo pipefail
OUT=$(mkdir -p "$1" && cd "$1" && pwd)
TARGET=${2:-linux}
VERSION=v0.1.0
COMMIT=e89fa7fdb85d8e75323fe533df90344a3cbc958c
URL=https://github.com/monyuonyu/jww-tools.git

WORK=$(mktemp -d)
git -c advice.detachedHead=false clone -q --depth 1 --branch "$VERSION" "$URL" "$WORK/src"
got=$(git -C "$WORK/src" rev-parse HEAD)
[ "$got" = "$COMMIT" ] || { echo "jww-tools $VERSION is $got, expected $COMMIT"; exit 1; }
args=(-DJWW_STATIC=ON -DCMAKE_BUILD_TYPE=Release)
exe=""
if [ "$TARGET" = win64 ]; then
  cat > "$WORK/mingw.cmake" <<'EOF'
set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++-posix)
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)
EOF
  args+=(-DCMAKE_TOOLCHAIN_FILE="$WORK/mingw.cmake")
  exe=".exe"
fi
cmake -S "$WORK/src" -B "$WORK/build" "${args[@]}" > "$WORK/cmake.log" || { tail -30 "$WORK/cmake.log"; exit 1; }
cmake --build "$WORK/build" -j"$(nproc)" > "$WORK/build.log" || { tail -30 "$WORK/build.log"; exit 1; }
cp "$WORK/build/jww2dxf$exe" "$OUT/"
if [ "$TARGET" = win64 ]; then
  x86_64-w64-mingw32-strip "$OUT/jww2dxf.exe"
  # Windows に必ずある DLL だけに頼ること
  bad=$(x86_64-w64-mingw32-objdump -p "$OUT/jww2dxf.exe" | awk '/DLL Name/ {print $3}' | grep -viE '^(kernel32|msvcrt|shell32)\.dll$' || true)
  [ -z "$bad" ] || { echo "jww2dxf.exe needs DLLs: $bad"; exit 1; }
else
  strip "$OUT/jww2dxf"
  (cd "$WORK/build" && ctest --output-on-failure > /dev/null)
  "$OUT/jww2dxf" --version
fi
rm -rf "$WORK"
