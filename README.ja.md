[English](README.md) | **日本語** | [简体中文](README.zh-CN.md)

# freecad-ja-unified

FreeCAD を「迷わない一つの画面」にまとめ、日本語で使えるようにしたもの。
作業場（ワークベンチ）の切り替えを無くし、選んだものに応じてその場で次の操作を出し、
画面の言葉を平易な日本語にそろえた。間違いを見つける「設計の検査」と、モデルを見て直す AI チャットも入れた。
コマンドラインやスクリプトから使うときの不具合も直している。FreeCAD 本家へのパッチの形で置いている（上流には送っていない）。

FreeCAD with one integrated, Japanese-first working environment: no workbench switching,
actions offered next to what you picked, plain Japanese throughout, a design check that finds
and fixes mistakes, an AI chat that works on the model, and fixes for using FreeCAD from the
command line and from scripts. Kept as patches on top of FreeCAD; not submitted upstream.

![面をクリックすると、その横に次の操作が出る](docs/images/08_face_actions.png)

- 元にした版: FreeCAD main `b48098efa`（2026-09-26、バージョン表記 26.3.0dev）
- 同梱の OndselSolver: `4be80eef`

## ダウンロード

[Releases](https://github.com/monyuonyu/freecad-ja-unified/releases) にビルド済みのものを置いている。

- Linux: `FreeCAD_<版>-Linux-x86_64.AppImage`（実行権限を付けてそのまま起動）
- Windows: `FreeCAD_<版>-Windows-x86_64-installer.exe`（インストーラー）または `.7z`（展開して `bin/FreeCAD.exe`）

署名はしていないので、Windows では SmartScreen の警告が出る（「詳細情報」→「実行」）。

設定・マクロ・ウィンドウの配置は本家の FreeCAD と別の場所（`FreeCAD-ja-unified`）に置く。Windows のインストーラーも
本家と別の場所（`FreeCAD-ja-unified 26.3`）に入る。0.3.1 までは本家と共通だった（本家と並べて使うと設定が混ざる）。

アンインストールすると、プログラム・ショートカット・ファイルの関連付け・登録はすべて消える（Windows で確かめた）。
自分の設定は、本家と同じく既定では残る（入れ直したときに引き継ぐため）。消すときはアンインストーラーの画面で
「ユーザー設定も削除」を選ぶ。消えるのはこの版の設定だけで、本家の FreeCAD の設定には触れない。

## 画面で見る

### 最初の起動

言語・単位・見た目（ライト／ダーク）を選ぶだけ。あとから「編集 → 設定」で変えられる。

![最初の起動の画面](docs/images/01_first_start.png)

### 新しい部品 → 描く場所をクリック

スタート画面は「新しい部品」「ファイルを開く」だけ。新しい部品を押すと、そのまま描く場所を聞いてくる。
本家のように面を選んでダイアログで OK を押す必要はなく、3D 画面の平面か部品の平らな面を 1 回クリックする。

![スタート画面](docs/images/02_start.png)

![描く場所を 3D 画面でクリック](docs/images/03_pick_plane.png)

### スケッチ中はスケッチの道具だけ

スケッチを描いている間は、ツールバーがスケッチの道具に切り替わり、終われば元に戻る。
グリッドの点に吸い付くので、マウスで描いても切りのいい寸法になる。決まっていない所の数は日本語で出る。

![スケッチの編集](docs/images/04_sketch.png)

### 描いたら、次の一手が横に出る

スケッチを閉じると、その横に「押し出す・回転・編集・AI に頼む」が出る。ツールバーから探さなくてよい。
ツールバーも主な道具はアイコンの下に名前（押し出し・切り抜き・丸め…）が付いている。

![スケッチを閉じた後の候補](docs/images/05_after_sketch.png)

作業パネルは道具を使っている間だけ出て、終わったら消える（モデルが画面に収まるように視点も合わせる）。

![押し出しの設定](docs/images/06_pad_panel.png)

### 面をクリックすると、その面でできること

面ならスケッチ・押し出し・切り抜き・穴・厚み、辺なら丸め・面取りが出る（一番上の画像）。
「穴」は、クリックした位置にそのまま開く（本家は先にスケッチに点を描く必要がある）。
カーソルの下の物は `Preselected: Unnamed.Body.Pad.Face6` ではなく、名前と場所で出る。
面をダブルクリックすると、その面を作った手順（押し出し・丸め…）の編集が開く。

![カーソルの下の表示](docs/images/08b_hover.png)

### 設計の検査と「直す」

基板 CAD の DRC のように、モデル全体の間違いを一覧にする。失敗した手順・部品どうしの干渉・スケッチの拘束の矛盾・
浮いた部品・形を見失った図面の寸法など。行を選ぶと部品に寄って、場所に赤い印が出る。
ステータスバーには常に結果（「検査: エラー 2・警告 2」）が出る。

![設計の検査](docs/images/09_design_check.png)

直し方がはっきりしているもの（重複・矛盾した拘束、浮いた部品、重なった部品、空の投影図）は「直す」で直る。
下は「直せるものを全部直す」を押した後。「元に戻す」1 回で全部戻る。

![直した後](docs/images/10_design_fixed.png)

### AI に頼む

右の「AI」パネルで頼むと、AI（Claude）がモデルを見て、直して、設計の検査と画面で確かめて報告する。
面や辺を選んで「AI に頼む」を押せば、選んだ物も一緒に伝わる。AI が実行するコードは毎回表示され、
「実行する」を押したときだけ動く。1 回ごとに「元に戻す」の 1 段になる。

![AI のコードを承認する](docs/images/11_ai_approve.png)

![AI が丸めを付けて確かめた](docs/images/12_ai_done.png)

### 失敗の知らせも日本語で

本家では英語のままの失敗の文（`BRep_API: command not done` など）も、何が悪いか・どうすればよいかを日本語で出す。
拘束の番号や辺の番号が入る文も訳す。

![失敗の知らせ](docs/images/13_error_ja.png)

### ナビキューブ

右上の向きを変える立方体は、ふだんは立方体だけ。マウスを乗せると矢印などが現れ、
面の縁や隅に近い所を押せばその辺・角の向きになる（押しやすい）。何が起きるかはツールチップで出る。

![ナビキューブの前後](docs/images/14_navicube.png)

## 本家との違い（一覧）

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
| 間違い探し | 「形状を確認」は選んだ 1 つの形が壊れていないかだけ | 「設計の検査」（基板 CAD の DRC に近い）: 失敗した手順・分かれた部品・部品どうしの干渉・スケッチの拘束の矛盾・極端に短い辺・浮いた部品・形を見失った図面の寸法を一覧に。行を選ぶと部品を選んで寄せ、場所に赤い印。「わざと」は無視として文書に記録。直せるもの（重複・矛盾した拘束、浮いた部品、重なった部品、空の投影図）は「直す」ボタンで直す（元に戻す 1 回で戻る）。ステータスバーに常に結果（エラー・警告の数）。コマンドラインでも `FreeCADCmd -c "import DesignCheck; DesignCheck.main('a.FCStd')"` |
| AI に頼む | 無し | 右の「AI」パネルで、AI（Claude）がモデルを見て・直して・検査と画面で確かめる。面や辺を選んだときの候補と、設計の検査の一覧に「AI に頼む」。AI が実行するコードは既定では毎回見せて、承認してから実行（1 回ごとに元に戻す 1 段。確認を省く切り替えもある）。使うには自分の Anthropic API キーが要る（下記） |
| メニュー | 「マクロ」や開発者向けの道具が上に並ぶ | 上のメニューを 1 つ減らし、表示・ツールの上級者向けはサブメニューへ |
| 直線配列の最初の間隔 | 常に 100 mm（小さい部品だと複製が画面の外） | 並べる形の大きさの 2 倍 |
| マウス操作 | 7 種類から選ぶ | 既定は 1 種類（右ドラッグで回転、中ドラッグで移動、ホイールで拡大縮小）。選ぶ画面は出さない |
| 作業パネル | 常に場所をとる | 道具を使っている間だけ出る。終わったらモデルが見えるように視点を合わせる |
| 右クリックメニュー | 項目が多い | モデリングに要るものだけ（ほかは上のメニューに残る） |
| 設定画面 | BIM・アドオンなど使わない頁もある | 使う頁だけ |
| アドオン管理 | あり | 無し（作業場を足す仕組みのため） |

機能は消していない。普段使わないものはメニューの中に説明付きで入れてある。

## AI チャットを使うには

1. 配布物（0.3.5 から）には、AI チャットに要る部品（claude-agent-sdk・keyring・Claude Code）が最初から入っている。準備は要らない。
   自分でビルドした場合は、右の「AI」パネルの「AI の準備をする」を押す（Python の仮想環境に入れる。ネットワークが要る）
2. [console.anthropic.com](https://console.anthropic.com/) で API キーを作り、「API キー…」で入れる。
   キーは OS の鍵保管庫（Windows の資格情報マネージャー・macOS のキーチェーン・Linux の Secret Service）にしまう。
   鍵保管庫の無い環境では、本人だけが読めるファイル（FreeCAD のユーザーデータの `ai/ai-api-key`）
3. 使った分は API キーの持ち主のアカウントに請求される。このパッチにキーやログインは含まれない

AI はモデル（既定は Opus）に、文書の中身・画面の画像・設計の検査の結果を送る。
AI が実行しようとするコードは、既定では毎回表示され、「実行する」を押したときだけ動く（FreeCAD の外のことも書けるので、読んでから）。
パネルの下の「たずねずに実行する」を入れると確認を省ける（FreeCAD を閉じるまで。実行したコードはチャットと ai/ai-runs.log に残る）。

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
| 画像を出す | 画面（xvfb）と GUI が要る | `FreeCADCmd a.FCStd --render a.png --view iso`（画面も OpenGL も不要。`--render-style shaded\|hidden-lines\|lines`、`--size 1600x1200`、Python は `Part.renderImage`） |
| 干渉チェック | 部品の組を総当たり（300 部品で 106 秒） | `FreeCADCmd a.FCStd --interference`／`Part.findInterferences`（外形で絞って並列、1.2 秒） |
| 隠れ線を消した 2D 図 | TechDraw のページが要る | `--export-svg`、`--export-polygons`（面ごとの多角形 JSON）、`--export-pptx`（編集できる図形の PowerPoint）／`Part.projectVisible` |
| 視点・拡大・断面（0.5.4） | — | `--view` に名前（`iso-bottom` など下からの等角も）か向き `dx,dy,dz`、`--up x,y,z`（画面の上）、`--focus 名前,…` か `--region x0,y0,z0,x1,y1,z1`（その範囲に拡大）、`--section z=10`（z>10 を取り去る。`-x=5` は x<5、`px,py,pz,nx,ny,nz` は法線の側）で切り口を塗ってハッチング。値が `-` で始まるときは `--section=-x=5`。Python は `Part.renderImage`/`projectVisible`/`exportSvg`/`exportPptx` の `up=`・`focus=`・`region=`・`section=(点, 法線)` |
| 大きな組立の隠れ線（0.5.4） | 1200 部品で 15 分以上終わらないことがあった | 深さバッファで隠す側の候補を絞り、全コアで並列。1200 部品 3.9 秒、STL 由来 1200 部品 5.4 秒（0.5.3 は 72 秒）。`--progress`（標準エラーに進み具合）、`--max-seconds 60`（時間切れなら手前から済んだ分を書いて警告）、`--deflection`（粗くして速く） |
| 点の内外判定・光線（0.5.4） | `Shape.isInside` を 1 点ずつ（10 万点で約 52 秒） | `Part.pointsInside(shape, 点の列)`（10 万点 0.16 秒、結果は isInside と同じ）、`Part.rayCast(shapes, 原点, 向き, all=False)`（距離・何番目の形・面・点・法線） |
| STL から作った立体（0.5.4） | `makeShapeFromMesh`＋`makeSolid` は三角形だらけで、閉じていない・裏返り・重複があるとブール演算が不安定 | `Part.solidFromMesh(mesh, 0.01, report=True)`（直して縫い、同じ平面の三角形を 1 つの面に。直したこと・残った問題を返す）。ブール演算は許容差つきで `a.common(b, 0.01)`。角の丸めは `Part.filletMeshSolid(mesh, 1.0)`（平らな面どうしの角だけ。曲面部分は丸めない） |
| Jw_cad の図面（0.5.6） | 開けない | 「開く」「インポート」で `.jww`（Jw_cad の図面）と `.jws`（図形登録）を開く。同梱の [jww2dxf](https://github.com/monyuonyu/jww-tools) で DXF にしてから読む（データの版 220〜700、Jw_cad 2.x〜10.x）。Jw_cad 自身の DXF 出力と 307 図面で図形ごとに突き合わせて全部一致。単体でも `jww2dxf 図面.jww` で DXF を作れる |
| DWG/DXF の 3D ソリッド（0.5.4） | 3DSOLID・REGION・BODY は読み捨て | Part の形として読み込む（平面・円柱・円錐・球・トーラス・B スプライン。試験図面 81 個中 80 個が閉じた立体）。ブロックの中のソリッドと、AutoCAD 2013 以降が書いた DXF（ACDSDATA に入っている）はまだ読めない |
| スクリプトに引数を渡す | — | `FreeCADCmd a.py -- x y`（`--` の後ろが `sys.argv`）。`FreeCADCmd a.py x` で `x` がファイルでないときは「`script.py -- x` で渡す」と案内する |
| `Mesh.addFacets(shape.tessellate(d))` | 接した箱どうしの面を**黙って捨てる**（52 個の箱で 624 → 12 面） | 全部入れる（`check=True` のときだけ捨て、数を警告） |

## 本家から取り込んだ修正（PR 一覧）

本家 FreeCAD に出されていて、まだ本家に入っていない PR のうち、精査して取り込んだもの（作者の名前はコミットにそのまま残している）。
開いている 541 件から、この画面が使う部分の落ちる・不具合・退行を中心に絞り、中身を読み、パッチに当たることと試験を確かめた。

**落ちる（クラッシュ）**

- [#32804](https://github.com/FreeCAD/FreeCAD/pull/32804) スケッチの編集に入るとき・マウスを動かしたときに落ちる（@alfrix）
- [#32975](https://github.com/FreeCAD/FreeCAD/pull/32975) スケッチの事前選択で範囲外を読んで落ちる（@alexdremov）
- [#32989](https://github.com/FreeCAD/FreeCAD/pull/32989) スケッチの反転で落ちる（@alfrix）
- [#32970](https://github.com/FreeCAD/FreeCAD/pull/32970) 作業パネルを閉じるときに、解放済みのメモリを触って落ちる（@alexdremov）
- [#32007](https://github.com/FreeCAD/FreeCAD/pull/32007) プロパティ欄で編集中に 3D 画面をクリックするなどして落ちる（6 種類。作業パネルの 1 か所は #32970 と重なるので除いた）（@oursland）
- [#32684](https://github.com/FreeCAD/FreeCAD/pull/32684) 外部参照のファイルを開くと落ちる（@chennes）
- [#31263](https://github.com/FreeCAD/FreeCAD/pull/31263) 起動直後の SpaceMouse の操作で落ちる（@Maik-0000FF）

**形・スケッチ**

- [#32430](https://github.com/FreeCAD/FreeCAD/pull/32430) ポリラインを角丸めすると最後の点が消える（@alfrix）
- [#32759](https://github.com/FreeCAD/FreeCAD/pull/32759) 曲線どうしの点で角丸めできないとき、その理由を出す（@VishalRamKN）
- [#28238](https://github.com/FreeCAD/FreeCAD/pull/28238) 丸め・面取りが失敗したとき、原因（半径が大きすぎる・面がねじれる…）と直し方を出す（@paragforwork）

**図面**

- [#32552](https://github.com/FreeCAD/FreeCAD/pull/32552) 位置をロックしたビューが、読み込むと原点に飛ぶ（@WandererFan）
- [#32151](https://github.com/FreeCAD/FreeCAD/pull/32151) 寸法の参照の修復が、壊れた参照で失敗する（@WandererFan）

**組立**

- [#31998](https://github.com/FreeCAD/FreeCAD/pull/31998) 部品に固定ジョイントを付けるとエラー（@ryneeverett）
- [#32924](https://github.com/FreeCAD/FreeCAD/pull/32924) 親を失ったジョイントのグループを消せない（@PaddleStroke）
- [#32922](https://github.com/FreeCAD/FreeCAD/pull/32922) ラックとピニオンの誤動作（@PaddleStroke）

**表示・画面**

- [#32658](https://github.com/FreeCAD/FreeCAD/pull/32658) ライト／ダークのテーマで、結合した形の色が崩れる（@chennes）
- [#32813](https://github.com/FreeCAD/FreeCAD/pull/32813) 選択の表示の奥行きの退行（@Connor9220）
- [#32841](https://github.com/FreeCAD/FreeCAD/pull/32841) プロパティ欄の選択肢で日本語などが化ける（@maxwxyz）
- [#32996](https://github.com/FreeCAD/FreeCAD/pull/32996) キーボードでツリーを選んだときにステータスバーを更新する（@007stevendigar-lgtm）

**ファイル**

- [#32934](https://github.com/FreeCAD/FreeCAD/pull/32934) ASCII の STL（長い名前・末尾の改行なし）が読めない（@maxwxyz）

**0.3.3 で追加**

- [#32614](https://github.com/FreeCAD/FreeCAD/pull/32614) スケッチの点を少しだけ動かすと元に戻る（@Reqrefusion）
- [#30997](https://github.com/FreeCAD/FreeCAD/pull/30997) 計測を開いたまま文書を閉じると落ちる（@Amine0x0）。そのまま当てると、この版では別の見張りを上書きして後で落ちるので、合わせて直した
- [#32879](https://github.com/FreeCAD/FreeCAD/pull/32879) 厚みの結果が不正な形でも黙っている（@007stevendigar-lgtm）。厚みが大きすぎて形が変わらない場合も知らせるよう足した

### 本家に報告されていて、まだ直っていない不具合を直したもの

再現手順が付いていて、手元で再現または原因まで確かめたもの。

- [#32968](https://github.com/FreeCAD/FreeCAD/issues/32968) スケッチの寸法を式エディタで入れると、ツールを抜けたときに寸法が消える（今月の退行）
- [#32732](https://github.com/FreeCAD/FreeCAD/issues/32732) 「変数セットに保存」で単位が合わずに失敗する（macOS では落ちる）
- [#32877](https://github.com/FreeCAD/FreeCAD/issues/32877) 見えない文書を開くと、作業中の文書が奪われる（macOS では落ちる）
- [#25050](https://github.com/FreeCAD/FreeCAD/issues/25050) 部品より厚い厚みが、黙って何もしない
- 途中の手順（切り抜きなど）を消すと、後の配列が消した穴を持ったまま「正常」と表示される
- STEP で日本語などの名前が化ける（書き出しを規格どおりの書き方にし、読み込みの既定を UTF-8 にした。他の CAD の STEP も読める）
- 長さ 0 の視点の動きで、画面が固まる

メモリの誤った使い方を見張るビルド（AddressSanitizer）で本家の試験を走らせて見つけたもの（0.3.4）:

- 再計算の最中に部品を消すと、後の処理が消えた部品のメモリを読む（CAM の工具で起きる）
- マクロの編集画面が、消えたファイルについて「読み直しますか」と聞いて止まる
- Draft の選択枠の表示が、渡した点より多くの点を読む

あわせて、組立のソルバー（OndselSolver）で、Linux・macOS では組立の書き出し（ASMT）の関節の種類名が壊れる不具合を直した
（型の名前を Windows の形を前提に切り出していた。本家の試験 #32922 が Linux で落ちて分かった）。

## 0.5.6 の変更

- **Jw_cad の図面（`.jww`・`.jws`）を開けるようにした**。「開く」「インポート」で選ぶだけ。新しく作った変換器 [jww-tools](https://github.com/monyuonyu/jww-tools) の `jww2dxf` を同梱し、DXF にしてから読み込む
  - 線・円・円弧・楕円・点・文字・寸法・ソリッド・ブロック・画像、レイヤグループとレイヤ（名前付きの画層に）、線種・線色・線幅
  - Jw_cad 10.03.7 自身の DXF 出力（`JWW2DXFConv.dll`）と 307 図面（データの版 220〜700）で図形ごとに突き合わせ、線 152,625・円弧 10,001・点 2,313・文字 22,116・ソリッド 1,085・画像 16 がすべて一致
  - 座標は Jw_cad の DXF 出力と同じ（用紙の左下が原点、書込レイヤグループの縮尺で実寸）
  - DOS 版の `.jwc` はまだ読めない

## 0.5.5 の変更

- DWG/DXF の 3D ソリッド: 1 枚の閉じた面だけでできた立体（ドーナツ形・球）が、立体でなく面として取り込まれていたのを直した。試験図面の 3D ソリッド 81 個がすべて閉じた立体になる

## 0.5.4 の変更

社外の実機の組立（機密のため合成データで再現）を 1 日 FreeCADCmd で使った同僚の要望から:
- 隠れ線の 2D 書き出し（`--export-svg` など・`Part.projectVisible`）が大きな組立で終わらない: 面ごとに、外形が重なる全部の面と切り抜きをしていた。
  深さバッファで「その面の上に見えている面」だけを相手にし、面・辺・三角形分割を全コアで並列に。結果は 0.5.3 と同じ（見える面積の差 0.001 % 以下）で、
  合成の 1200 部品が 17.7 → 3.9 秒、STL から作った 1200 部品が 72 → 5.4 秒。三角形だけの形（STL 由来）はメッシュとして扱い、同じ平面の三角形は 1 つの面に、
  三角形の間の線は描かない。`--progress`・`--max-seconds`（`maxSeconds=`、時間切れは手前の面から済んだ分と警告）・`--deflection`
- 画像・2D 書き出しの視点: 向きをベクトルで、画面の上の向き（`up`）、下からの等角（`iso-bottom` ほか 7 つ）、範囲や部品に拡大（`region`・`focus`）、
  断面（`section`。切り口を色で塗りハッチング。SVG はパターン、PowerPoint は柄の塗り）。重なった部品の同じ面が画像で黒く潰れていたのも直した
- `Part.pointsInside`・`Part.rayCast`（たくさんの点の内外判定と光線の当たり。上の表）
- `Part.solidFromMesh`・`Part.filletMeshSolid`（STL から作った立体をブール演算・断面・丸めに使える形に。上の表）
- DWG/DXF の 3DSOLID・REGION・BODY を読み込む（ACIS の SAT を自前で読む `AcisSat`。上の表）
- `FreeCADCmd a.py 値` で値がファイルでないときに `--` の使い方を案内する

## 0.5.3 の変更

- スケッチのソルバーが、同じスケッチでも解けたり解けなかったりする（未知数をメモリ上の番地の順に並べていた。
  矛盾した拘束を持つスケッチで、解ける・失敗・「冗長」の結果が回ごとに変わり、文書を 2 回再計算すると形が変わった。CAM の試験ファイル Drilling_1 で見つけた）

## 0.5.2 の変更

FreeCAD 全体のバグ探し（372 個のファイルを、メモリ破壊の検査つきのビルドと、往復・2 回目・体積の恒等式などの「静かな間違い」の確かめに通した）で見つかった 14 件を直した:
- 落ちる・固まる: `Shape.check(True)` が端点の無い辺で落ちる、OFF 形式のメッシュを読むと止まらない
- 静かに変わる: FCStd に保存すると小さな数値が 0 になる、3MF で小さな座標が消える・座標が丸まる、メッシュの体積が単精度で誤差が大きい、
  IGES の書き出しで面の境界の情報が抜けて面積が変わる、DXF の書き出しで App::Link が書かれない、交差した 4 隅の DXF SOLID が壊れた面になる、
  R14 の DXF の単位、TechDraw の Draft・Arch のビューが選んでいない文書で別の文書の物を読み書きする
- 0.5.0 で足した機能: 隠れ線の 2D 書き出しで重なった面が両方消える、画像・2D 書き出しが元の形のメッシュを書き換える

## 0.5.1 の変更

会社の実図面（R2018）と 2,113 部品のモデルで 0.5.0 を試してもらった結果を受けて:
- 2D 書き出し: PowerPoint・SVG・JSON で部品の階層ごとにグループにする（組立の木、`Group` プロパティ、`"a/b/c"` の指定）。
  `Part.exportPptx`／`Part.exportSvg` を追加（形・色・グループを渡せる）。辺は `--export-edges none|outline|all`（PowerPoint は既定で面の輪郭だけ）。
  画面なしでも FCStd に保存された色を使う
- DWG: AutoCAD が省いた全ゼロのページがあると 3D ソリッドの中身が空になっていた、64KB を超える 3D ソリッドを DXF 経由で R2000 に書くと消えていた、
  日本語の配置名・図面情報・パスが DXF 経由で化けて警告が出ていた、R2018 から R2000 に書くとヘッダの文字列が 1 文字になっていたのを直した

## 0.5.0 の変更

- DWG: **R2004・R2010・R2013・R2018 の DWG を書けるようにした**（これまでは R2000 まで）。
  試験用の 149 図面を各版に書いて ACadSharp で読み直し、読めない図面 0・消えた図形 0・種類が変わった図形 0（DXF 経由でも同じ）。
  AutoCAD が同じ版で保存したものとも図形ごとに突き合わせた
  - 3D ソリッド（ACIS）: R2013 以降の置き場所（AcDs）を読み書きし、古い図面や DXF から R2013 以降に書いても形が消えない
  - DXF → DWG（dxf2dwg）で R2010 以降に書くと図形の 2 割近くが消えていたのを直した
  - FreeCAD の DWG 書き出しは従来どおり R2000（どの AutoCAD でも開ける）。新しい版は同梱の `dxf2dwg --as r2018` で
- コマンドライン: 画像を 1 行で出す（`--render`、画面も OpenGL も不要）、速い干渉チェック（`--interference`）、
  隠れ線を消した 2D 図の書き出し（SVG・面ごとの多角形・PowerPoint）。「コマンドライン・スクリプト」の表を参照
- Mesh: `addFacets` が接した部品の面を黙って捨て、STL に穴が開いていたのを直した

## 0.4.1 の変更

- DWG: 同じ図面を AutoCAD 自身が版を変えて保存したものと突き合わせ、R2000 に書くときの変換を AutoCAD に合わせた。
  example_2004〜2018 は R2000 に書いた全図形が AutoCAD の R2000 保存と一致（DXF 経由でも同じ）
  - 色: ByBlock の図形が ByLayer になっていた、RGB の色の代わりの色番号を AutoCAD と同じにした、色の表を今の AutoCAD の値に
  - R14 の図面: 図形の線種（CONTINUOUS など）が ByLayer になっていた、線の太さが 0.00mm になっていた、標準の名前を AutoCAD と同じに
  - グラデーションのハッチングは最初の色の塗りつぶしに、MTEXT の改行は \P で（DXF でも）
- DWG: 表（TABLE）を読み書きできるようにした（DXF 経由でも消えない）。R2010 以降の表スタイルを全部読む
- DWG: 中身を解読できない独自アプリの図形（建築アドオンなど）を、古い版や DXF に書くとき AutoCAD と同じプロキシ図形として元のデータごと残す
- DWG: DXF 経由で表スタイル名・寸法スタイル名・ハッチングの名前が変わっていた、R14 の DXF で新しい種類の図形が落ちていたのを直した

## 0.4.0 の変更

- DWG の読み書き: LibreDWG（`dwg2dxf` / `dxf2dwg`）を同梱し、ファイル → 開く／取り込み／書き出しで DWG を扱えるようにした。
  読みは R13〜R2018（AutoCAD 2018〜2025 の AC1032 を含む）、書きは開いた図面の版（R2000 以前）で書く。
  LibreDWG 0.14.8601 に、独立した実装（ACadSharp）と 149 図面で突き合わせて見つけた読み書きの不具合の修正を当てている
  （`patches/libredwg`。表・複数行属性・文字コード・R2000 への書き出しなど）。自分で変換器を設定している場合はそちらを使う
- AI チャット: やり取りの回数の上限（80 回）で止まった時は、黙らずに「続けて」で続けられると知らせる
- AI チャット: 120 秒で終わらないコードは止めて、その回の変更を取り消す（FreeCAD が固まらないように）。最後の式の値を表示できなくても、済んだ変更は取り消さない

## 0.3.6 の変更

- Windows のインストーラーで入れた時に、AI チャットの部品（ai-runtime）が入っていなかったのを直した（0.3.5 の 7z には入っている）
- AI チャット: 「たずねずに実行する」の切り替え（既定は切。入れる時に注意が出る。保存しないので、FreeCAD を閉じると毎回たずねる形に戻る。
  実行したコードはチャットに残る）。承認の窓に「実行して、以後はたずねない」
- AI チャット: AI のコードの sys.exit で FreeCAD が落ちて固まったのを直した（ほかの誤りと同じく、その回の変更を取り消して知らせる）
- AI チャット: AI が実行したコードと結果を、ユーザーデータの ai/ai-runs.log に残す
- AI の道具の不具合（AI 自身の試験で見つかったもの）: エラーの時にほかの文書の変更も取り消し、開いていた文書に戻す。
  何も変えなかった回は「元に戻す」の段を作らない。増えた物・消えた物を名前でなく出来事で数える。
  Python で作ったパターンが部品の最後にある時は Tip を進める。get_document の種類の欄が手順の設定（Length など）で上書きされていた
- 設計の検査: 形に使われていない手順（Tip より後）、形の無い部品、調べていない見えない部品を知らせる。
  拘束がぶつかっている間は「決まっていない所」を出さない。拘束の番号が 1 から数えたものだと書く
- 日本語: 原点の中の点を「原点の点」に（入れ物の原点と、どちらも「原点」だった）

## 0.3.5 の変更

- AI チャットに要る部品を配布物に同梱した。インストールしてすぐ、ネットワークからの準備なしで AI パネルが使える（AI との会話そのものにはネットワークが要る）
- AI チャットで失敗したとき（キーが無効など）の説明を分かりやすくした

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

## LibreDWG（DWG の変換器）

`tools/build_libredwg.sh <出力先> [linux|win64]` で、本家の LibreDWG 0.14.8601 に `patches/libredwg` を当てて
`dwg2dxf` / `dxf2dwg` を作る（Windows 用は MinGW-w64 のクロスビルド、DLL 不要）。リリースの手順もこれを使う。

## jww-tools（Jw_cad の変換器）

`tools/build_jww2dxf.sh <出力先> [linux|win64]` で、[jww-tools](https://github.com/monyuonyu/jww-tools) の決まった版（タグとコミットを確かめる）から
`jww2dxf` を作る（静的リンク。Windows 用は MinGW-w64 のクロスビルド、DLL 不要）。リリースの手順もこれを使い、LibreDWG と同じ所に置いて同梱する。

## リリースの作り方

パッチの書き出しは `tools/export_patches.sh`（FreeCAD の clone の unified-ui から patches/ を作り直す）。


GitHub Actions の「Build release」（`.github/workflows/release.yml`）をタグ名を入れて手で実行する。
元の版にパッチを当て、本家と同じ `package/bundle` の手順で Linux と Windows を作ってリリースに載せる（数時間かかる）。


## ライセンス

パッチは FreeCAD と同じ LGPL-2.1-or-later（`LICENSE`）。
