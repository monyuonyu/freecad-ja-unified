# freecad-ja-unified

FreeCAD を「迷わない一つの画面」にまとめ、日本語で使えるようにしたもの。
作業場（ワークベンチ）の切り替えを無くし、選んだものに応じてその場で次の操作を出し、
画面の言葉を平易な日本語にそろえた。あわせて、コマンドラインやスクリプトから使うときの不具合も直している。
FreeCAD 本家へのパッチの形で置いている（上流には送っていない）。

FreeCAD with one integrated, Japanese-first working environment: no workbench switching,
actions offered next to what you picked, plain Japanese throughout, plus fixes for using
FreeCAD from the command line and from scripts. Kept as patches on top of FreeCAD; not
submitted upstream.

- 元にした版: FreeCAD main `b48098efa`（2026-09-26、バージョン表記 26.3.0dev）
- 同梱の OndselSolver: `4be80eef`

## ダウンロード

[Releases](https://github.com/monyuonyu/freecad-ja-unified/releases) にビルド済みのものを置いている。

- Linux: `FreeCAD_<版>-Linux-x86_64.AppImage`（実行権限を付けてそのまま起動）
- Windows: `FreeCAD_<版>-Windows-x86_64-installer.exe`（インストーラー）または `.7z`（展開して `bin/FreeCAD.exe`）

署名はしていないので、Windows では SmartScreen の警告が出る（「詳細情報」→「実行」）。
設定フォルダは本家の FreeCAD と共通なので、本家と並べて使うと設定が混ざる。

## 一つの画面

| | 本家 FreeCAD | このパッチ |
|---|---|---|
| 作業場（ワークベンチ） | Part / PartDesign / Sketcher / Draft / TechDraw / Assembly … を切り替える | 切り替え無し。一つの画面にスケッチ・立体・図面・アセンブリ |
| 2D の作図 | Sketcher と Draft の二本立て | Sketcher に一本化（スケッチ中だけスケッチの道具を出す） |
| 図面・アセンブリ | それぞれの作業場 | 「図面」「アセンブリ」メニューに説明付きで収納 |
| 最初の一歩 | スタート画面の選択肢が多い | 「新しい部品」「開く」だけ。新しい部品はすぐスケッチ面の選択へ |
| スケッチ面の選択 | ダイアログで面を選んで OK | 3D 画面の面や基準面を1回クリック |
| 選んだあとの操作 | ツールバーから探す | 選んだものの横に候補を出す（面→スケッチ/押し出し/切り抜き/薄肉化、辺→角丸め/面取り、スケッチ→押し出し/回転/編集、部品→移動/隠す） |
| ツールバー | アイコンだけ。1600 幅でも一部が「»」の奥に隠れる | 主な道具はアイコンの下に名前（押し出し・切り抜き・丸め…）。スケッチの道具も一列に収まる |
| スケッチの吸着 | 既定では切 | グリッドの点の近くで吸着（マウスで描いても切りのいい寸法になる） |
| カーソルの下の表示 | `Preselected: Unnamed.Body.Pad.Face6` | `押し出し の 面 6` |
| 面をダブルクリック | 何も起きない | その面を作った手順（押し出し・丸め…）の編集が開く |
| 面を選んで「穴」 | 「軸が見つかりません」で失敗（先にスケッチに点を描く必要がある） | クリックした位置に穴 |
| 図面の投影図 | 開き直すまでページの左下に出る（本家の不具合）。第一角法が既定 | ページの中央に出る。第三角法（JIS）が既定 |
| 読み込んだ立体（STEP など）に手を加える | 「アクティブな部品が必要です」のダイアログ | そのままスケッチ・丸め・押し出しができる（自動で部品にする） |
| 何も選ばずにエクスポート | 「オブジェクトを選択してください」で止まる | 見えている部品を書き出す |
| メニュー | 「マクロ」や開発者向けの道具が上に並ぶ | 上のメニューを 1 つ減らし、表示・ツールの上級者向けはサブメニューへ |
| 直線配列の最初の間隔 | 常に 100 mm（小さい部品だと複製が画面の外） | 並べる形の大きさの 2 倍 |
| マウス操作 | 7 種類から選ぶ | 1 種類（右ドラッグで回転、中ドラッグで移動、ホイールで拡大縮小）に固定 |
| 作業パネル | 常に場所をとる | 道具を使っている間だけ出る。終わったらモデルが見えるように視点を合わせる |
| 右クリックメニュー | 項目が多い | モデリングに要るものだけ（ほかは上のメニューに残る） |
| 設定画面 | BIM・アドオンなど使わない頁もある | 使う頁だけ |
| アドオン管理 | あり | 無し（作業場を足す仕組みのため） |

機能は消していない。普段使わないものはメニューの中に説明付きで入れてある。

## 日本語

- メニュー・ツールバー・作業パネル・通知・設定画面の未訳を埋め、用語を平易な言葉にそろえた
  （例: Pad → 押し出し、Pocket → 切り抜き、Body → 部品、Constraint → 拘束）
- 左のプロパティ欄（項目名・分類・説明・選択肢の値）を日本語に
- 新しく作ったものの名前も日本語（部品、スケッチ、押し出し …）
- 部品の中の原点（Origin）は木の表示から隠す

日本語以外の言語では本家と同じ表示になる。

## コマンドライン・スクリプト

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
FreeCAD 自身の試験（`FreeCADCmd -t 0`、C++ の Base/App/Part/Gui の試験）もパッチ後にすべて通ることを確かめている。

## リリースの作り方

GitHub Actions の「Build release」（`.github/workflows/release.yml`）をタグ名を入れて手で実行する。
元の版にパッチを当て、本家と同じ `package/bundle` の手順で Linux と Windows を作ってリリースに載せる（数時間かかる）。


## ライセンス

パッチは FreeCAD と同じ LGPL-2.1-or-later（`LICENSE`）。
