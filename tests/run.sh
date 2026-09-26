#!/bin/bash
# FreeCAD の CLI の挙動の試験。使い方: run.sh <freecadcmd> [<freecad(GUI)>]
# 例: run.sh ~/freecad-src/build/release/bin/FreeCADCmd ~/freecad-src/build/release/bin/FreeCAD
CMD=${1:?freecadcmd のパス}; GUI=$2
T=$(mktemp -d); cd "$T" || exit 1
pass=0; fail=0
ok()  { echo "  OK   $1"; pass=$((pass+1)); }
ng()  { echo "  NG   $1  ($2)"; fail=$((fail+1)); }
# run <名前> <期待する終了コード> <出力に含むべき文字列 or -> <含んではいけない文字列 or -> -- コマンド…
check() {
  local name=$1 want=$2 must=$3 mustnot=$4; shift 5
  out=$(timeout 120 "$@" 2>&1); code=$?
  if [ "$code" != "$want" ]; then ng "$name" "終了コード $code、期待 $want"; return; fi
  if [ "$must" != "-" ] && ! grep -qF -- "$must" <<<"$out"; then ng "$name" "出力に '$must' が無い"; return; fi
  if [ "$mustnot" != "-" ] && grep -qF -- "$mustnot" <<<"$out"; then ng "$name" "出力に '$mustnot' がある"; return; fi
  ok "$name"
}
printf 'print("RAN")\nraise RuntimeError("boom")\n' > fail.py
printf 'import sys\nprint("name=" + __name__)\nprint("argv=" + repr(sys.argv))\nif __name__ == "__main__":\n    print("MAIN")\n' > argv.py
printf 'import sys\nsys.exit()\n' > exit0.py
printf 'import sys\nprint("BEFORE-EXIT")\nsys.exit(3)\n' > exit3.py
printf 'import sys\nsys.exit("bad input")\n' > exitmsg.py
printf 'print("hello")\n' > hello.py

echo "== freecadcmd: $CMD"
check "例外で終了コード 1"                1 "boom" -            -- "$CMD" fail.py
out=$(timeout 60 "$CMD" fail.py 2>&1); n=$(grep -c RAN <<<"$out")
[ "$n" = 1 ] && ok "例外でもスクリプトは 1 回だけ走る" || ng "例外でもスクリプトは 1 回だけ走る" "RAN が $n 回"
check "トレースバックに行番号"            1 'line 2' -          -- "$CMD" fail.py
check "__name__ が __main__"              0 "MAIN" -            -- "$CMD" argv.py
check "sys.argv が [script, 引数…]（--）" 0 "argv.py', 'a', 'b']" - -- "$CMD" argv.py -- a b
check "-- の後ろはファイル扱いしない"      0 "MAIN" "No such file" -- "$CMD" argv.py -- x.step
check "sys.exit() は 0"                   0 - -                 -- "$CMD" exit0.py
check "sys.exit(3) は 3、直前の print も出る" 3 "BEFORE-EXIT" -                 -- "$CMD" exit3.py
check "sys.exit('msg') はメッセージを出す" 1 "bad input" -      -- "$CMD" exitmsg.py
check "無いファイルは終了コード 1"         1 "No such file" -   -- "$CMD" nonexistent.py
check "スクリプト実行でバナーを出さない"   0 "hello" "(C) 20"   -- "$CMD" hello.py
check "-c のコードは従来どおり"           0 "42" -              -- "$CMD" -c "print(6*7)"
out=$(timeout 60 "$CMD" -c 'import Part; Part.makeBox(1,1,1).exportStep("o.step"); print("ONLY")' 2>/dev/null)
[ "$out" = "ONLY" ] && ok "STEP 書き出しで stdout を汚さない" || ng "STEP 書き出しで stdout を汚さない" "stdout: $(head -c 80 <<<"$out" | tr '\n' ' ')"
check "Part.export に Shape を渡せる"      0 "solids=1" -        -- "$CMD" -c 'import Part; Part.export([Part.makeBox(1,2,3)], "e.step"); print("solids=%d" % len(Part.read("e.step").Solids))'
check "Part.export で書くものが無ければエラー" 1 - -            -- "$CMD" -c 'import Part; Part.export([1, "x"], "n.step")'
# パイプで渡したスクリプト: 空行なしの for、プロンプトやバナーが混ざらない、エラーは 1
printf 'for i in range(2):\n    print("loop", i)\nprint("END")\n' > pipe_ok.py
out=$(timeout 60 "$CMD" < pipe_ok.py 2>&1); code=$?
[ "$code" = 0 ] && [ "$out" = "$(printf 'loop 0\nloop 1\nEND')" ] && ok "パイプのスクリプトを 1 本として実行" || ng "パイプのスクリプトを 1 本として実行" "code=$code out=$(tr '\n' '|' <<<"$out" | head -c 120)"
printf 'print("A")\nraise ValueError("pipe-err")\n' > pipe_ng.py
out=$(timeout 60 "$CMD" < pipe_ng.py 2>&1); code=$?
[ "$code" = 1 ] && grep -q "ValueError: pipe-err" <<<"$out" && ok "パイプのスクリプトの例外は 1" || ng "パイプのスクリプトの例外は 1" "code=$code"
"$CMD" -c 'import Part; Part.makeBox(4,5,6).exportStep("in.step")' >/dev/null 2>&1
check "--output で変換できる"             0 - -                 -- "$CMD" in.step -o out.stl
[ -s out.stl ] && ok "--output の出力ファイルがある" || ng "--output の出力ファイルがある" "out.stl が無い"
check "--output の未対応形式は 1"         1 "not supported" -  -- "$CMD" in.step -o out.xyz123
check "--output の書き込み失敗は 1"       1 "not written" -    -- "$CMD" in.step -o /nonexistent/dir/o.stl
check "--help に使い方の例と終了コード"    0 "Exit status" -    -- "$CMD" --help
ASM=$(ls "$(dirname "$CMD")"/../share/examples/AssemblyExample.FCStd "$(dirname "$CMD")"/../data/examples/AssemblyExample.FCStd 2>/dev/null | head -1)
if [ -n "$ASM" ]; then
  out=$(timeout 120 "$CMD" -c "import FreeCAD; FreeCAD.openDocument('$ASM'); print('ONLY')" 2>/dev/null)
  [ "$out" = "ONLY" ] && ok "アセンブリを開いても stdout を汚さない" || ng "アセンブリを開いても stdout を汚さない" "stdout: $(head -c 60 <<<"$out" | tr '\n' ' ')"
fi
check "-c の例外は 1"                     1 - -                 -- "$CMD" -c "raise ValueError('x')"

if [ -n "$GUI" ]; then
  echo "== freecad (GUI, --hidden): $GUI"
  cat > render.py <<'PY'
import FreeCAD as App, FreeCADGui as Gui, Part
print("STDOUT-VISIBLE")
d = App.newDocument("r"); o = d.addObject("Part::Feature", "b"); o.Shape = Part.makeBox(10, 20, 30); d.recompute()
v = Gui.getDocument("r").activeView()
v.viewIsometric(); v.fitAll(); v.saveImage("iso.png", 300, 300, "White")
s = d.addObject("Part::Feature", "s"); s.Shape = Part.makeSphere(5, App.Vector(100, 0, 0)); d.recompute()
o.Visibility = False; v.fitAll(); v.saveImage("nc.png", 300, 300, "White")
print("SAVED")
PY
  check "--hidden: print が端末に出る"      0 "STDOUT-VISIBLE" "Segmentation" -- xvfb-run -a "$GUI" --hidden render.py
  check "--hidden: 例外で終了コード 1"      1 "boom" "Segmentation" -- xvfb-run -a "$GUI" --hidden fail.py
  out=$(timeout 120 xvfb-run -a "$GUI" --hidden fail.py 2>&1); n=$(grep -c RAN <<<"$out")
  [ "$n" = 1 ] && ok "--hidden: スクリプトは 1 回だけ" || ng "--hidden: スクリプトは 1 回だけ" "RAN が $n 回"
  # アニメーションの途中でなく iso で保存されたか: 箱の正面・右・上の 3 面が見える＝色が 3 種類以上
  python3 - <<'PY' && ok "--hidden: 視点切替を待たずに iso で保存される" || ng "--hidden: 視点切替を待たずに iso で保存される" "面の色が 3 種類未満"
from PIL import Image
im = Image.open("iso.png").convert("RGB"); cols = {c for n, c in im.getcolors(1 << 20) if n > 500 and c != (255, 255, 255)}
raise SystemExit(0 if len(cols) >= 3 else 1)
PY
  # 旧版の設定フォルダがあると設定移行のダイアログが出る。--hidden では出さずに走り切ること、GUI の設定を変えないこと
  OLDCFG=$(mktemp -d); mkdir -p "$OLDCFG/FreeCAD/v1-1" "$OLDCFG/data/FreeCAD/v1-1/Macro"
  printf '<?xml version="1.0" encoding="utf-8"?>\n<FCParameters><FCParamGroup Name="Root"><FCParamGroup Name="BaseApp"/></FCParamGroup></FCParameters>\n' > "$OLDCFG/FreeCAD/v1-1/user.cfg"
  cp "$OLDCFG/FreeCAD/v1-1/user.cfg" "$OLDCFG/before.cfg"
  out=$(XDG_CONFIG_HOME=$OLDCFG XDG_DATA_HOME=$OLDCFG/data timeout 60 xvfb-run -a "$GUI" --hidden render.py 2>&1); code=$?
  [ "$code" = 0 ] && ok "--hidden: 設定移行のダイアログで止まらない" || ng "--hidden: 設定移行のダイアログで止まらない" "終了コード $code（124 ならタイムアウト）"
  found=$(find "$OLDCFG/FreeCAD" -name user.cfg | head -1)
  if grep -q "MRU0\|MainWindowState" $(find "$OLDCFG/FreeCAD" -name user.cfg); then ng "--hidden: 最近使ったファイルやウィンドウ配置を書かない" "user.cfg に MRU0/MainWindowState"; else ok "--hidden: 最近使ったファイルやウィンドウ配置を書かない"; fi
  rm -rf "$OLDCFG"
  # 右上（ナビゲーションキューブの位置）が真っ白＝画面用の飾りが写り込んでいない
  python3 - <<'PY' && ok "--hidden: saveImage に NaviCube が写らない" || ng "--hidden: saveImage に NaviCube が写らない" "右上に白以外の画素"
from PIL import Image
im = Image.open("nc.png").convert("RGB"); w, h = im.size
px = [im.getpixel((x, y)) for x in range(int(w * 0.75), w) for y in range(0, int(h * 0.2))]
raise SystemExit(0 if sum(1 for p in px if p != (255, 255, 255)) < 20 else 1)
PY
fi
echo "== 合格 $pass / 不合格 $fail"
rm -rf "$T"
[ "$fail" = 0 ]
