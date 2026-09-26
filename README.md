# freecad-cli-patches

FreeCAD をコマンドラインやスクリプトから使いやすくするためのパッチ集。
スクリプトの実行（`FreeCADCmd`）、画面を出さない GUI での実行（`FreeCAD --hidden`）、
出力の汚れまわりの不具合を直している。上流（FreeCAD 本家）には送っていない。

Patches that make FreeCAD usable from the command line and from scripts: correct exit
codes, Python-like script execution, clean stdout, and a `--hidden` mode that works for
headless rendering. Not submitted upstream.

- 元にした版: FreeCAD main `b48098efa`（2026-09-26、バージョン表記 26.3.0dev）
- 同梱の OndselSolver: `4be80eef`

## 何が変わるか

| | 素の FreeCAD | パッチ後 |
|---|---|---|
| スクリプトが例外で落ちる | 終了コード **0**、しかも**2回実行**される、エラーは1行だけ | 1回だけ実行、終了コード 1、トレースバックを表示 |
| `if __name__ == "__main__":` | 実行されない（モジュールとして import される） | 実行される |
| `sys.argv` | FreeCAD の引数そのまま | `FreeCADCmd a.py -- x y` → `['a.py', 'x', 'y']` |
| `sys.exit()` / `sys.exit("msg")` | 1 / メッセージが出ない | 0 / メッセージを標準エラーに |
| 例外や `sys.exit()` の直前の `print` | 消えることがある | 出る |
| 存在しないファイル | 終了コード 0 | `No such file`、終了コード 1 |
| `FreeCADCmd < a.py` | 対話モードで1行ずつ処理（`>>>` が混ざり、エラーでも 0） | 1本のスクリプトとして実行 |
| スクリプト実行時のバナー | 出る | 出ない（対話モードでは出る） |
| STEP の書き出し | OCC の統計が標準出力に2重に出る | 出ない（ログに回す） |
| アセンブリを開く | 拘束ソルバーのメッセージが標準出力に出る | 出ない |
| `Part.export([shape], "a.step")` | **空の STEP を黙って書く** | Shape を受け付ける／何も無ければ `ValueError` |
| `--output` での変換失敗 | 終了コード 0 | 終了コード 1 |
| `--help` | 名前が常に「FreeCAD」、使い方の説明なし | 実行ファイル名・例・終了コード。`--output`（`-o`）と `--hidden` を表示 |
| 設定ファイル | 何もしない実行でも毎回書き直す。並列に走らせると設定が消える | 値が変わったときだけ書く |
| `FreeCAD --hidden a.py` が失敗 | 終了コード 0 | 終了コード 1 |
| `--hidden` で視点を変えて保存 | アニメーションの途中が保存される | アニメーションしない |
| `--hidden` で旧版の設定がある | 設定移行のダイアログが見えない画面に出て**永久に止まる** | ダイアログを出さない |
| `--hidden` の実行 | 最近使ったファイル・ウィンドウ配置を書き換える | 書き換えない |
| Python の `saveImage()` | ナビゲーションキューブが写り込む | 写らない（「画像を保存」メニューと同じ） |

## 当て方とビルド

```sh
git clone https://github.com/FreeCAD/FreeCAD.git
cd FreeCAD && git checkout b48098efa && cd ..
./apply.sh FreeCAD

# ビルド（Linux、pixi を使う公式の手順）。FEM/CAM/Robot は時間短縮のため外している
cd FreeCAD
pixi install
pixi run cmake --preset conda-linux-release -DBUILD_FEM=OFF -DBUILD_CAM=OFF -DBUILD_ROBOT=OFF
pixi run cmake --build build/release -j4      # 2 コア 4 スレッドのノートで約 2 時間
pixi run cmake --install build/release        # .pixi/envs/default/bin に FreeCADCmd と FreeCAD
```

## 試験

```sh
XDG_CONFIG_HOME=$(mktemp -d) XDG_DATA_HOME=$(mktemp -d) \
  tests/run.sh <FreeCADCmd のパス> <FreeCAD のパス>
```

設定フォルダは必ず一時フォルダに向けること（本物の設定を汚さないため）。GUI の項目には `xvfb-run` が要る。
素の FreeCAD 1.1.3 では 4/17、パッチ後は全項目（31）合格。

## ライセンス

パッチは FreeCAD と同じ LGPL-2.1-or-later（`LICENSE`）。
