# 部品の棚（Parts shelf）

ねじ・ナット・座金（JIS、M3〜M12）、アルミフレーム、会社の部品を、クリックでモデルに入れる。
道具の列の「部品の棚」、Ctrl+K（「ねじ」「ボルト」「ナット」「座金」「ワッシャ」「六角穴付き」「M6」「アルミフレーム」…）、
穴を選んだときの横の帯の「ねじを入れる」から使う。受け入れの画面は [ui-redesign/accept/parts-shelf](ui-redesign/accept/parts-shelf)。

## ねじを穴に入れる

穴（丸い面か、その縁）をクリックすると、合うねじが入る。

- **太さは穴の径から**: 下穴（M3 ⌀2.5、M4 ⌀3.3、M5 ⌀4.2、M6 ⌀5、M8 ⌀6.8、M10 ⌀8.5、M12 ⌀10.2）、呼び径で描いたねじ穴、
  キリ穴（JIS B 1001 の 1〜3 級。例 M6 は ⌀6.4・6.6・7）、座ぐり、皿もみ
- **長さは締めるものから**: 同じ軸の上にあるほかの部品の穴も見る。キリ穴の板を何枚通り、どのねじ穴にどれだけ入るか。
  ねじ穴に入るときはねじ径の 1.5 倍かみ合う長さを目安に、止まり穴の底に当たらない規格の長さを選ぶ。
  通し穴だけならナットで止める（座金・ナットの厚さとねじ山 2 つ分の余り）。描いていない板を一緒に締めるときは「上に重ねる板」に厚さを入れる
- **置き場所は穴の軸の上**（「くっつける」と同じ計算 SnapMath）。座ぐりがあれば頭はその底、皿もみなら面と同じ高さ。
  通し穴は見ている側から入れる
- パネルで太さ・長さ・種類・座金・ナットを変えると、いま入れたねじがその場で変わる。Ctrl+K の「M6×20」のような言葉もそのまま使える

| 種類 | 規格 | 形を作るもの |
|---|---|---|
| 六角穴付きボルト | JIS B 1176（ISO 4762） | Fasteners |
| 六角ボルト（全ねじ・半ねじ） | JIS B 1180（ISO 4017・4014） | Fasteners |
| 六角穴付き皿ボルト | JIS B 1194（ISO 10642） | Fasteners |
| 六角ナット（1種） | JIS B 1181（ISO 4032） | Fasteners |
| 平座金 | JIS B 1256（ISO 7089） | Fasteners |
| ばね座金 | JIS B 1251（2号相当） | この版（PartsShelf.py） |
| 六角穴付き止めねじ（平先・くぼみ先） | JIS B 1177（ISO 4026・4029） | Fasteners |

ねじ山は描かない（呼び径の円柱）。設計の検査は、棚のねじがねじ穴に入っている重なり（ねじ山と下穴の間の輪の分まで）を干渉にしない。

## 部品表

文書には、種類と大きさごとに見えない「元の形」を 1 つ（「棚の部品（元の形）」の中）、使う所にはそれへのリンクを置く。
元の形の名前が「六角穴付きボルト M6×20」で、組立の部品表（BOM）ではリンクの数が数量になる。
元の形には部品表の列に使えるプロパティがある: `PartName`（名前）・`Standard`（規格）・`Size`（呼び）、会社の部品は `PartNumber`（品番）。
部品表の列名を `.Standard` のように点で始めると、そのプロパティが列になる。
形はそのまま保存されるので、Fasteners の無い FreeCAD でもファイルは開ける。

## アルミフレーム

20・30・40 シリーズ、溝 6・8（20 角溝 6、30 角溝 6、30 角溝 8、40 角溝 8）。始まりと終わりの 2 点をクリックする
（1 点目の後は影がカーソルについてくる。長さを打ち込んで Enter でもよい。長さは 1 mm 単位）。面の上をクリックすると、その面に載せる。

断面は公開されている一般的な寸法から作った汎用の形で、特定のメーカーの図面ではない。
**メーカーのデータ（例えば SUS のもの）は含めていない**: 再配布を禁じている規約があるため。
メーカーの形が要るときは、自社で入手した CAD データを下の「会社の部品」に置く（各社の利用規約の範囲で）。

## 会社の部品

FCStd・STEP のファイルを入れたフォルダーを棚に足すと、その部品が「会社の部品」に並ぶ。面をクリックすると、
部品の原点がその点に、部品の Z が面の外向きになるように置く。

- フォルダーの足し方: 棚の「会社の部品」を選んで「フォルダー…」。設定には `Mod/Unified/PartsShelf` の `CompanyFolders`（`;` 区切り）として残る
- 会社全体で同じフォルダーを使うとき（情報システムの方向け）: 環境変数 `FREECAD_PARTS_SHELF` に共有フォルダーを書く
  （複数は `;`（Windows）・`:`（Linux）区切り）。利用者の設定と合わせて全部並ぶ
- 一覧のファイル（無くてもよい）: フォルダーの直下に `shelf.csv`（`index.csv`・`棚.csv` でも可）。
  無ければ、フォルダーとその下のフォルダーの FCStd・STEP を全部並べる（下のフォルダー名が分類、ファイル名が名前）

`shelf.csv` の書き方（1 行目は列の名前。日本語でも英語でもよい。Excel の「CSV（コンマ区切り）」で保存した Shift_JIS のものもそのまま読める）:

```csv
ファイル,名前,分類,別名,品番,メモ
brackets/L20.step,L 金具 20,金具,アングル;L字,KB-020,ステンレス
pins/pin10.FCStd,位置決めピン ⌀10,ピン,ピン,P-001,h7
```

| 列 | 英語の列名 | 中身 |
|---|---|---|
| ファイル | file | フォルダーからの相対パス（必須） |
| 名前 | name | 棚と部品表に出る名前（無ければファイル名） |
| 分類 | category | 棚の中のまとまり |
| 別名 | keywords | 棚の検索で引っかかる言葉（何でも） |
| 品番 | number | `PartNumber` プロパティになる |
| メモ | note | 棚でカーソルを当てると出る |

FCStd は見えている部品の形（複数ならまとめて 1 つ）を、STEP は形をそのまま取り込む。取り込んだ形は文書に保存されるので、
元のファイルが無い所でも開ける（元のファイルを直したときは、置き直すと新しい形になる）。

## ライセンス

- 同梱の [Fasteners ワークベンチ](https://github.com/shaise/FreeCAD_FastenersWB)（Shai Seger 氏ほか）は **GPL-2.0-or-later**。
  `src/Mod/Fasteners` に、コミット `fddd07af`（0.5.67）の実行に要るファイルを手を加えずに入れている（`BUNDLED_FROM`・`LICENSE`）。
  FreeCAD 本体（LGPL-2.1-or-later）とは別のモジュールとして配る。Ctrl+K と「その他の道具」から Fasteners の全部の道具（223）も使える
- 棚・穴の判定・ばね座金・アルミフレーム・会社の部品の部分（`Mod/Unified/PartsShelf*.py`）は、ほかのパッチと同じ LGPL-2.1-or-later
- 寸法は公開されている規格の値（JIS B 1001 など）と一般的な寸法から取った

---

## Parts shelf (English summary)

Screws, nuts and washers (JIS, M3–M12), generic aluminium extrusion profiles (20/30/40 series, slot 6/8) and the company's
own parts, put into the model with clicks: "Parts Shelf" on the tool strip, Ctrl+K, or "Insert screw" next to a picked hole.
Clicking a hole inserts the screw that fits: the size from the hole diameter (tap drill, thread, JIS B 1001 clearance hole,
counterbore, countersink), the length from what it clamps and the thread it goes into (also of other parts on the same axis),
coaxial with the hole. Each kind and size is one hidden original with BOM properties (`PartName`, `Standard`, `Size`,
`PartNumber`); the placed parts are links to it, so the Assembly BOM counts them.

Company parts: add a folder of FCStd/STEP files ("Folder…" in the shelf, or the environment variable `FREECAD_PARTS_SHELF`).
An optional `shelf.csv` lists them (columns `file,name,category,keywords,number,note`, UTF-8 or Shift_JIS).

The bundled [Fasteners workbench](https://github.com/shaise/FreeCAD_FastenersWB) is GPL-2.0-or-later (unchanged runtime files of
commit `fddd07af` in `src/Mod/Fasteners`). The profiles are generic; no maker's data is included (e.g. SUS forbids redistribution).
