# 統合版で届かなくなった操作（本家 FreeCAD との比較）

調査日 2026-10-20 / 対象 `~/freecad-src` ブランチ `unified-ui`（基点 b48098e）/ 未コミットの下書き

## 調べ方

- ビルド済みの FreeCAD を xvfb で起動し（`FREECAD_USER_HOME` を別にして）、`Gui.listCommands()` と、メニューバー・全ツールバー（グループコマンドの中身を含む）の QAction をたどって「統合版で届くコマンド」を出した。そのあと全作業場の Initialize() を走らせてコマンドを全部登録させ、本家の各作業場の Workbench.cpp / InitGui.py / init_tools.py に並ぶコマンド名と突き合わせた。
- 右クリックメニューと、選んだものの横に出る候補（ContextBar.cpp）はソースで確認した。
- 数: 本家でどこかのメニュー・ツールバーに並ぶコマンド 997 個のうち、統合版のメニュー・ツールバーから届くのは 320 個。差の 677 個から、置き換え済み（穴・複製・一致拘束など）、意図的に外したもの（作業場の切り替え・アドオン管理）、試験用を除くと **約 636 個が届かない**。
  - 作業場ごと見えなくなったもの（BIM 126・FEM 78・CAM 55・Robot 15・リバースエンジニアリング 12・OpenSCAD 14・点群 6・サーフェス 6・検査 2）: **約 314 個**
  - 統合版の守備範囲（モデリング・スケッチ・図面・アセンブリ・ファイル）に近いもの（TechDraw 106・Draft 78・Part 57・Mesh 37・スプレッドシート 15・アセンブリ 10・PartDesign 7・スケッチ 4・材料 3・共通 4）: **約 322 個**
- **コマンド検索は無い**。本家にも標準では無く（アドオンの SearchBar 頼み）、統合版ではアドオン管理も無いので入れられない。
- 抜け道の現状:
  - 「ツール → カスタマイズ」でツールバーに任意のコマンドを足せる。ただし一覧に出るのは**読み込まれたモジュールのコマンドだけ**。統合版が起動時に読むのは Part・Sketcher・PartDesign・TechDraw・Assembly・Spreadsheet（と共通）で、Draft・Mesh・BIM・FEM・CAM・Surface などは一覧にも出ない。
  - Python コンソールで `Gui.activateWorkbench("MeshWorkbench")` などとすると、画面は統合版のままコマンドだけ登録される（e3111a52d）。そのあとカスタマイズで足せる。一般の利用者が見つけられる道ではない。
  - キーボードの近道: メニュー・ツールバーに無いコマンドに近道が効くかは**未確認**。

頻度の目安: 高＝この版の利用者（部品を作る人・図面を出す人）の多くが月に何度も要る / 中＝ときどき、または一部の人が毎回要る / 低＝まれ・専門。
戻し方: メ＝既存メニューに足す / 候＝選んだものの横の候補 / そ＝新しい「その他の道具」メニュー / 検＝コマンド検索で届けば十分 / 右＝右クリック

## 1. モデリング（Part・PartDesign）

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `PartDesign_MoveTip`（先端を設定） | 履歴の途中を「今の先端」にして、その位置に手順を差し込む | 高（手順を途中に足すのはよくある。本家は右クリックで出る） | 右（ツリーの右クリック） |
| `PartDesign_MoveFeatureInTree`（手順の後ろへ移動） | 手順の順番を入れ替える | 中 | 右 |
| `PartDesign_MoveFeature`（別の部品へ移動） | 手順を別のボディへ移す | 低 | 右 |
| `Part_Fuse` / `Part_Cut` / `Part_Common`（和・差・積） | ボディや読み込んだ立体どうしをまとめて足す・引く・重なりを取る（PartDesign の「ブーリアン」はボディの中だけ） | 高（読み込んだ STEP の加工、型の作成） | メ（モデル）＋候（2つ以上選んだとき） |
| `Part_Mirror`（鏡像） | ボディや立体を丸ごと鏡に映した複製を作る（PartDesign の「ミラー」は手順単位） | 高（左右対称の部品の対） | メ |
| `Part_Scale`（拡大縮小） | 立体を倍率で大きく・小さくする（読み込んだ STL/STEP の単位違い直しにも） | 高 | メ＋候 |
| `Part_ShapeFromMesh` / `Part_MakeSolid`（メッシュから形状・ソリッド化） | STL などのメッシュを立体に変える（統合版の solidFromMesh は Python からだけ） | 中〜高（3D プリンタの人は既存 STL の加工が多い） | メ（ファイル or モデル） |
| `Part_RefineShape`（形状を整理） | 余計な継ぎ目の面・辺を消す（読み込んだ形の掃除） | 中 | そ |
| `Part_SimpleCopy`（単純コピー） | 履歴を持たない固まった複製を作る | 中 | そ |
| `Part_ColorPerFace`（面ごとの外観） | 面ごとに色を付ける | 中（色分けした絵を出す人） | 右 |
| `Part_EditAttachment`（アタッチメント） | 部品や基準を他の面・点に付けて一緒に動かす（スケッチは「スケッチを貼る」で可） | 中 | メ（編集） |
| `Part_Primitives`（プリミティブ） | ねじ用のらせん・渦巻・正多角形・くさび などを寸法で作る | 中（らせんはねじ・ばねに要る。PartDesign の付加らせんで一部代替） | そ |
| `Part_Box` / `Part_Cylinder` / `Part_Sphere` / `Part_Cone` / `Part_Torus` / `Part_Tube` | ボディの外に箱・円柱などの立体を置く（ボディ内の付加プリミティブはある） | 中（治具・仮置き） | そ |
| `Part_Extrude` / `Part_Revolve` / `Part_Loft` / `Part_Sweep` | ボディの外で押し出し・回転・ロフト・スイープ（面でなく殻も作れる） | 中 | そ |
| `Part_Section` / `Part_CrossSections` / `Part_SectionCut` | 立体の断面線を取り出す・等間隔の輪切り・持続的な断面表示 | 中（断面の確認・レーザー加工の輪切り） | そ |
| `Part_Offset` / `Part_Offset2D` / `Part_Thickness` | 立体や輪郭を一定量太らせる・殻にする（ボディの外） | 中 | そ |
| `Part_MakeFace`（ワイヤから面） | 線から面を作る（DXF 読み込み後など） | 中 | そ |
| `Part_Compound` / `Part_ExplodeCompound` / `Part_CompoundFilter` | 立体をまとめる・ばらす | 中（STEP の中の部品を個別に扱う） | そ |
| `Part_BooleanFragments` / `Part_Slice` / `Part_SliceApart` / `Part_XOR` / 結合（Connect・Embed・Cutout） | 立体を互いの境で分割する・接続する | 低 | そ |
| `Part_Chamfer` / `Part_Fillet`（Part 版） | ボディの外の立体の面取り・丸め（統合版は読み込んだ立体を自動で部品にするので大半は代替できる） | 低 | 検 |
| `Part_Builder` / `Part_RuledSurface` / `Part_ProjectionOnSurface` / `Part_ElementCopy` / `Part_TransformedCopy` / `Part_ReverseShape` / `Part_ToleranceSet` / `Part_Defeaturing`（Part 版） / `Part_PointsFromMesh` | 形を要素から組む・線織面・面への投影 ほか | 低 | 検 |
| `Part_LinkArrays`（リンク配列：直線・円・極・パス・点） | ボディや部品を（リンクで軽く）並べる。PartDesign の配列はボディ内の手順だけ | 中〜高（同じ部品を並べる：ボルト・板） | メ（モデル→並べる） |
| `PartDesign_InvoluteGear` / `PartDesign_Sprocket` | 歯車・スプロケットの輪郭を寸法から作る | 中（ホビー用途で人気） | そ |
| `PartDesign_WizardShaft` | 軸の設計ウィザード | 低 | 検 |
| `Materials_InspectAppearance` / `Materials_InspectMaterial` / `Material_Edit` | 外観・材料の中身を見る / 材料を自作・編集する（材料の割り当て自体は右クリックに残る） | 低〜中（質量計算の密度を自作したいとき） | そ |
| `Std_ToggleFreeze`（凍結の切替） | 再計算しないよう固める | 低〜中（重い読み込み形状） | 右（戻すのが早い） |

## 2. スケッチ

ほぼ全部届く（スケッチ メニュー＋編集中のツールバー）。抜けは次だけ。

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Sketcher_NewSketch`（ボディの外のスケッチ） | どのボディにも属さないスケッチ（Part の押し出し・Draft 用） | 低 | 検 |
| `Sketcher_CancelSketch`（編集を取り消す） | スケッチの変更を捨てて抜ける（作業パネルの閉じる/取消で代わる場合あり） | 低 | 検 |
| `Sketcher_ProfilesHexagon1`（六角形プロファイル） | 六角ナット形の輪郭を一発で（多角形で代替可） | 低 | 検 |
| `Sketcher_StopOperation` | 実行中の道具をやめる（Esc で代わる） | 低 | 不要 |

## 3. 2D 作図・配置（Draft）—— 作業場ごと読み込まれない（78）

統合版の方針で Sketcher に一本化。ただし「配置・複製・文字」の多くは Sketcher で代わりがない。

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Draft_Move`（点から点へ移動） | 立体を点を拾ってきっちり動かす | 高 | **別のエージェントが「点から点へ動かす」「くっつける」として追加中** |
| `Draft_Rotate` | 点を中心に角度を決めて回す | 高（「変形」ハンドルは目分量になりやすい） | 「点から点へ」と同じ形で足す |
| `Draft_Clone` / `Draft_OrthoArray` / `Draft_PolarArray` / `Draft_PathArray` / `Draft_PointArray`（Draft_ArrayTools） | 立体の複製・格子・円形・パスに沿った配列 | 中〜高 | Part_LinkArrays と合わせて「並べる」に |
| `Draft_ShapeString`（文字から形状） | 文字を輪郭にして押し出し・彫り込みに使う（Sketcher の「テキスト（試験的）」は一部代替） | 中〜高（銘板・刻印） | メ（スケッチ or モデル） |
| `Draft_Draft2Sketch`（Draft → スケッチ） | 読み込んだ DXF の線をスケッチにして押し出せるようにする | 中〜高（DXF から立体を作る人） | メ（ファイルの読み込み直後の候補でも） |
| `Draft_Upgrade` / `Draft_Downgrade` | 線をつないで面に・面を線に分解 | 中（DXF の後処理） | そ |
| `Draft_Shape2DView` | 立体の 2D 投影を作る（レーザー加工の DXF 書き出し） | 中 | そ（図面 → DXF で代替できる場合あり） |
| `Draft_Scale` / `Draft_Mirror` / `Draft_Offset` / `Draft_Trimex` / `Draft_Stretch` / `Draft_Join` / `Draft_Split` / `Draft_Fillet` | 2D/3D の編集一式 | 低〜中 | 検 |
| `Draft_Line` / `Draft_Wire` / `Draft_Circle` / `Draft_Rectangle` / `Draft_Polygon` / `Draft_BSpline` / `Draft_Point` ほか作図 | 3D 空間に直接線を引く | 低（スケッチで足りる。方針どおり） | 検 |
| `Draft_Dimension` / `Draft_Text` / `Draft_Label` / `Draft_Hatch` | 3D 画面の中の寸法・文字・引出し線 | 低〜中（図面を作らずに画面へ寸法を出したい） | 検 |
| `Draft_SelectPlane` / スナップ 17 種 / `Draft_ToggleGrid` / `Draft_Layer` / `Draft_LayerManager` / グループ操作 / スタイル | Draft の作業平面・スナップ・レイヤー | 低（Draft を使わないなら不要。DXF のレイヤーを扱う人は中） | 検 |

## 4. アセンブリ

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Assembly_CreateJointScrew` / `Assembly_CreateJointRackPinion` / `Assembly_CreateJointGearBelt`（歯車・ベルト） | ねじ・ラック＆ピニオン・歯車/ベルトの連動ジョイント | 中 | メ（ジョイントの下に「連動」） |
| `Assembly_CreateJointRigidGroup`（剛体グループ） | 複数部品を一体として固める | 中 | メ |
| `Assembly_CreateSimulation`（シミュレーション） | ジョイントを動かすアニメーション | 中 | メ |
| `Assembly_CreateSnapshot` / `Assembly_ExportASMT` | 状態の保存 / ASMT 書き出し | 低 | 検 |
| `Assembly_ActivateAssembly` | アセンブリをアクティブにする（ダブルクリックで代替） | 低 | 検 |
| `Assembly_SelectJointsOfComponent`（部品のジョイントを選ぶ） | 本家は右クリックに出る | 低〜中 | 右 |
| `Part_LinkArrays` | アセンブリ内で部品を並べる | 中 | 1 章と同じ |

## 5. 図面（TechDraw）—— 106 個が届かない

「図面」メニューには基本（ページ・投影・断面・詳細・6 種の寸法・注記・バルーン・SVG/DXF 書き出し）だけ。JIS の図面を最後まで仕上げるには次が要る。

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| 中心線（`TechDraw_FaceCenterLine` / `2LineCenterLine` / `2PointCenterLine` / `ExtensionCircleCenterLines` / `ExtensionHoleCircle`） | 穴・軸の中心線、ボルト円の中心線 | 高（JIS 図面の必須要素） | メ（図面 → 線と記号） |
| `TechDraw_Dimension`（スマート寸法） / `TechDraw_3PtAngleDimension` / `TechDraw_ExtensionCreateLengthArc`（弧長） | 選んだ物に合う寸法を自動で / 3 点角度 / 弧の長さ | 中〜高 | メ（寸法の下） |
| 直列・累進・面取り寸法（`ExtensionCreate*ChainDimension` / `*CoordDimension` / `*ChamferDimension`）、`Extent` 寸法 | 並び寸法・座標寸法・C 面取り寸法・全幅寸法 | 中 | メ（寸法の下） |
| 寸法の接頭字（`ExtensionInsertDiameter` ⌀ / `InsertSquare` □ / `InsertRepetition` n× / `RemovePrefixChar`）・小数桁の増減 | 寸法文字の体裁 | 中 | 右（寸法を右クリック） |
| `TechDraw_HoleShaftFit`（はめあい） | H7/g6 などの公差記号を寸法に | 中 | メ |
| `TechDraw_SurfaceFinishSymbols`（表面性状） / `TechDraw_WeldSymbol`（溶接記号） / `TechDraw_LeaderLine`（引出し線） / `TechDraw_RichTextAnnotation` | 記号と注記 | 中 | メ（図面 → 記号） |
| ハッチング（`TechDraw_Hatch` / `TechDraw_GeometricHatch`） | 断面のハッチを変える・面に塗る（断面図の標準ハッチは自動で付く） | 中 | 右 |
| 化粧線・化粧点（`CosmeticVertex` / `Midpoints` / `Quadrants` / `CosmeticCircle` / `2PointCosmeticLine` / 平行・垂直線 / ねじ表示 4 種 / `CosmeticEraser` / `DecorateLine` / `ShowAll`） | 図面上だけの線・点・ねじの慣用表示・線種変更・隠れ線の表示切替 | 中（ねじの慣用表示は JIS で頻出） | そ（図面 → 作図補助） |
| `TechDraw_ComplexSection` / `TechDraw_BrokenView` | 階段断面・破断図 | 中 | メ |
| `TechDraw_ExportPagePDF` | 図面ページを PDF に（ファイル → PDF 書き出し・印刷で代替可） | 中 | メ |
| `TechDraw_FillTemplateFields` / `TechDraw_RedrawPage` / `TechDraw_ToggleFrame` / `TechDraw_ActiveView` / `TechDraw_Image` / `TechDraw_Symbol`（SVG 挿入） / `TechDraw_SpreadsheetView`（部品表を図面に） / `TechDraw_ClipGroup` / `TechDraw_ShareView` / 重ね順 / 位置合わせ / ビューのロック ほか | 表題欄の自動記入・再描画・枠の表示・3D 画面の取り込み・画像/記号・表 | 低〜中（表題欄と部品表は中） | そ |
| `TechDraw_DraftView` / `TechDraw_ArchView` / `TechDraw_ProjectShape` | Draft/BIM の図・単純投影 | 低 | 検 |

## 6. メッシュ（Mesh・MeshPart）—— 作業場ごと読み込まれない（37）

STL の読み込み・書き出しはファイル メニューで今も可能。届かないのは「直す・変える」側。

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Mesh_FromPartShape` / `MeshPart_Mesher` | 細かさを指定して立体をメッシュにする（書き出しの既定の粗さでは足りないとき） | 中（3D プリンタ・CG の人） | メ（ファイル → 書き出しの選択肢） |
| `Mesh_Evaluation` / `Mesh_FillupHoles` / `Mesh_HarmonizeNormals` / `Mesh_FlipNormals` / `Mesh_RemoveComponents` | 壊れた STL の検査と修理 | 中 | そ |
| `Mesh_Decimating` / `Mesh_Smoothing` / `Mesh_RemeshGmsh` / `Mesh_Scale` | 間引き・平滑化・再分割・倍率 | 低〜中 | そ |
| `Mesh_Union` / `Difference` / `Intersection` / `PolyCut` / `TrimByPlane` / `SectionByPlane` / `CrossSections` / `Segmentation` / `BuildRegularSolid` / 曲率表示 ほか | メッシュの演算・切断・分析 | 低 | 検 |
| `MeshPart_CreateFlatMesh` / `CreateFlatFace`（展開） | 面・メッシュを平面に展開（型紙・板金の目安） | 低〜中 | そ |

## 7. スプレッドシート（読み込まれているがメニューに無い）

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Spreadsheet_CreateSheet`（新しい表） | 寸法をまとめて表で管理（式で参照） | 中（パラメトリック設計。「変数セット」は 編集 → 作成 にあり一部代替） | メ（編集 → 作成） |
| `Spreadsheet_Import` / `Spreadsheet_Export` | CSV の読み込み・書き出し | 低〜中 | 表の右クリック |
| 書式（太字・揃え・セル結合/分割・別名） | 表の中の右クリックとセルの「プロパティ」に同じ操作がある | — | 不要 |

## 8. 共通（ファイル・表示・選択・道具）

| コマンド | 何をするか | 頻度 | 戻し方 |
|---|---|---|---|
| `Std_TreeSelectAllInstances`（全インスタンスを選択） | 同じ物のリンクを全部選ぶ（右クリックから外し、メニューに無い） | 低 | 右 or 表示→その他 |
| `Std_LinkMakeGroup`（リンクグループ） | リンク操作の右クリックから外した。編集 → 作成 → リンク操作 には入っていない | 低 | 編集 → 作成 → リンク操作 に足す |
| `Std_ToggleFreeze` | 1 章を参照（右クリックから外して、ほかに無い） | 低〜中 | 右 |
| `Std_AddonMgr` / `Std_AddonMgrPip` | アドオン管理（意図的に削除）。作業場だけでなく**マクロ・テーマ・設定パック**の入手口も消えている | 中（マクロを入れたい人） | 判断事項（マクロだけ入れられる口を残すか） |

右クリックから外したうち、選択可否の切替・ツリーで選択・窓のドッキング・Python へ送る は他のメニューに残っている（問題なし）。`Std_ToggleSuppress`（抑制の切替）と `Std_ToggleToolBarLock` は右クリックに残る。

## 9. 作業場ごと見えなくなったもの（約 314）

| 作業場 | 数 | 何ができなくなったか | 頻度 | 戻し方 |
|---|---|---|---|---|
| CAM | 55 | CNC 加工の工具経路（G コード）作成 | 中（CNC を持つ人には必須、ほかの人には不要） | 「その他の道具」から作業場を一時的に開く口 |
| FEM | 78 | 強度・熱の解析 | 低〜中 | 同上 |
| BIM（Arch・IFC 含む） | 126 | 建築の壁・窓・IFC | 低（この版の対象外。ただし IFC の読み込み設定ページも隠れた） | 同上 |
| Surface | 6 | 曲面の張り（境界から面を作る・面の延長・ブレンド曲線） | 低〜中（外装の曲面） | そ |
| OpenSCAD | 14 | 凸包（Hull）・ミンコフスキー和・.scad 要素 | 低 | 検 |
| Robot / Reverse Engineering / Points / Inspection | 35 | ロボット、点群からの面再構成、点群、形状の差の色分け | 低 | 検 |

**README.ja.md の「機能は消していない」は、この章と 3・6 章を見る限り正確ではない**（メニューにも検索にも無く、カスタマイズの一覧にも出ない）。

## 10. コマンド以外で変わった振る舞い

| 変更 | 失われた能力 | まだ道があるか |
|---|---|---|
| マウス操作の方式を 1 種類に固定（設定画面・スタート画面の選択欄を隠す、ステータスバーの切替表示 NavigationIndicator も読み込まない） | タッチパッド向け（Gesture・Touchpad）や他 CAD 風（SolidWorks・Inventor・Blender 等）の操作に変えられない。ノート PC のタッチパッドだけの人は回転できない恐れ | 開発者向け → パラメータの編集 で `BaseApp/Preferences/View/NavigationStyle` を書き換えれば可。一般には無い。**戻す価値が高い**（少なくとも「タッチパッド」） |
| 設定画面から BIM・IFC・DAE・SH3D・WebGL・アドオンの頁を除外 | IFC/DAE/SH3D の読み込み・WebGL 書き出しの設定を変えられない（読み込み自体はファイル メニューに出る） | パラメータの編集だけ |
| 作業場の設定頁と 表示 → 作業場 を削除 | なし（意図どおり） | — |
| アドオン管理を削除 | 作業場に加え、マクロ・テーマ・設定パックの入手口 | マクロはフォルダに手で置けば使える |
| 右クリックの短縮・PartDesign/Assembly 独自の右クリックが出ない（統合版の setupContextMenu が StdWorkbench だけを呼ぶ） | 先端の設定・手順の移動・凍結・全インスタンス選択・部品のジョイント選択 | 無し（1・4・8 章） |
| 原点（基準面・軸）をツリーに出さない（ShowInTree=false） | ツリーから基準面を選ぶ・表示を切り替える | ツリーの右クリック「隠した項目を表示」で出せる（気づきにくい） |
| スタート画面: 「新しい部品」「開く」だけ、作例を出さない | 作例ファイルを開く・空の文書/アセンブリ/2D から始める | 空の文書は ファイル → 新規、アセンブリはメニュー。作例はファイル→開くで本体のフォルダを探す必要 |
| 道具を使っていないときは作業パネルを隠す | PartDesign の「次にできること」の案内（タスクウォッチャー） | 選んだものの横の候補が代わる。問題小 |
| ツールチップから内部コマンド名を消し、カーソル下の表示も表示名に | マクロを書く人がコマンド名・内部名を知る手段 | Python へ送る・プロパティ欄・レポート欄で可。問題小 |
| スケッチを Esc で抜けない（既定）、グリッドに吸着（既定） | なし | 設定で戻せる |

## 11. 推奨

1. **コマンド検索を入れる**（Ctrl+K など、メニューの先頭にも「コマンドを探す」）。登録済みコマンドだけでなく、未読み込みの作業場のコマンドも名前・日本語名・ツールチップで引けるようにし、選んだときにその作業場を裏で読み込んでから実行する。これで 9 章を含む全部に「道がある」状態になり、README の「機能は消していない」が本当になる。
2. **短い一覧をメニュー・候補に戻す**（下の 15 個を中心に）。特に ツリーの右クリックに「先端を設定」「手順を移動」（PartDesign の右クリックを統合版の setupContextMenu から呼ぶだけで戻る）、モデル メニューに Part のブーリアン・鏡像・拡大縮小・リンク配列、図面 メニューに中心線とねじの慣用表示。
3. **「その他の道具」メニュー**を一つ作り、Part の残り・メッシュの修理・Draft の文字/配列/DXF→スケッチ・スプレッドシート・歯車 をまとめる。
4. **マウス操作の選択を戻す**（少なくとも設定画面で選べるように。既定は今のまま）。
5. README の「機能は消していない」を「CAM・FEM・BIM などは外した（必要ならコマンド検索から）」と正直に書き直す。

## 付録: 届かないコマンドの全一覧（作業場ごと、英語のメニュー名）

置き換え済み（`PartDesign_Hole`→穴、`Std_DuplicateSelection`→PartDesign 版、一致拘束系）、意図的な削除（`Std_Workbench`）、試験用は除いた。

### BIM（126）

`Arch_Add`（Add Component）, `Arch_Axis`（Axis）, `Arch_AxisSystem`（Axis System）, `Arch_Building`（Building）, `Arch_Check`（Check）, `Arch_CloseHoles`（Close Holes）, `Arch_Component`（Component）, `Arch_CurtainWall`（Curtain Wall）, `Arch_CutPlane`（Cut With Plane）, `Arch_Equipment`（Equipment）, `Arch_Fence`（Fence）, `Arch_Frame`（Frame）, `Arch_Grid`（Grid）, `Arch_IfcSpreadsheet`（New IFC Spreadsheet）, `Arch_Level`（Level）, `Arch_MergeWalls`（Merge Walls）, `Arch_MeshToShape`（Mesh to Shape）, `Arch_Panel`（Panel）, `Arch_PanelTools`（Panel Tools）, `Arch_Pipe`（Pipe）, `Arch_PipeConnector`（Connector）, `Arch_Profile`（Profile）, `Arch_Rebar`（Custom Rebar）, `Arch_Reference`（External Reference）, `Arch_Remove`（Remove Component）, `Arch_RemoveShape`（Remove Shape From BIM）, `Arch_Roof`（Roof）, `Arch_Schedule`（Schedule）, `Arch_SectionPlane`（Section Plane）, `Arch_SelectNonSolidMeshes`（Select Non-Manifold Meshes）, `Arch_Site`（Site）, `Arch_Space`（Space）, `Arch_SplitMesh`（Split Mesh）, `Arch_Stairs`（Stairs）, `Arch_StructureTools`（Structure Tools）, `Arch_Survey`（Survey）, `Arch_ToggleIfcBrepFlag`（Toggle IFC B-Rep Flag）, `Arch_ToggleSubs`（Toggle Subcomponents）, `Arch_Truss`（Truss）, `Arch_Wall`（Wall）, `Arch_Window`（Window）, `BIM_ArcTools`（Arc Tools）, `BIM_ArrayTools`（Array Tools）, `BIM_AxisTools`（Axis Tools）, `BIM_Beam`（Beam）, `BIM_BooleanTools`（Boolean Tools）, `BIM_Box`（Box）, `BIM_Builder`（Shape Builder）, `BIM_Classification`（Manage Classification）, `BIM_Clone`（Clone）, `BIM_CloneTools`（Cloning Tools）, `BIM_Column`（Column）, `BIM_Common`（Intersection）, `BIM_Compound`（Compound）, `BIM_Copy`（Copy）, `BIM_Covering`（Covering）, `BIM_Create2DViews`（Create 2D Views）, `BIM_Cut`（Difference）, `BIM_Diff`（IFC Shape Diff）, `BIM_DimensionAligned`（Aligned Dimension）, `BIM_DimensionHorizontal`（Horizontal Dimension）, `BIM_DimensionVertical`（Vertical Dimension）, `BIM_Door`（Door）, `BIM_DrawingView`（2D Drawing）, `BIM_EmptyTrash`（Empty Trash）, `BIM_Examples`（BIM Examples）, `BIM_Extrude`（Extrude）, `BIM_ExtrudeFace`（Extrude Face）, `BIM_Fuse`（Union）, `BIM_GenericTools`（Generic 3D Tools）, `BIM_Glue`（Glue）, `BIM_Help`（BIM Help）, `BIM_IfcElements`（Manage IFC Elements）, `BIM_IfcExplorer`（IFC Explorer）, `BIM_IfcManageTools`（IFC Management）, `BIM_IfcProperties`（Manage IFC Properties）, `BIM_IfcQuantities`（Manage IFC Quantities）, `BIM_ImagePlane`（Image Plane）, `BIM_Layers`（Manage Layers）, `BIM_Leader`（Leader）, `BIM_Library`（Objects Library）, `BIM_LinkMake`（Make Link）, `BIM_Material`（Material）, `BIM_MoveView`（Move View）, `BIM_Nudge_Down`（Nudge Down）, `BIM_Nudge_Extend`（Nudge Extend）, `BIM_Nudge_Left`（Nudge Left）, `BIM_Nudge_Right`（Nudge Right）, `BIM_Nudge_RotateLeft`（Nudge Rotate Left）, `BIM_Nudge_RotateRight`（Nudge Rotate Right）, `BIM_Nudge_Shrink`（Nudge Shrink）, `BIM_Nudge_Switch`（Nudge Switch）, `BIM_Nudge_Up`（Nudge Up）, `BIM_Offset2D`（2D Offset）, `BIM_OffsetTools`（Offset Tools）, `BIM_Preflight`（Preflight Checks）, `BIM_Project`（IFC Project）, `BIM_ProjectManager`（Setup Project）, `BIM_Reextrude`（Re-Extrude）, `BIM_Reorder`（Reorder Children）, `BIM_Report`（Report）, `BIM_ReportTools`（Report Tools）, `BIM_ResetCloneColors`（Reset Colors）, `BIM_Rewire`（Rewire）, `BIM_SetWPFront`（Working Plane Front）, `BIM_SetWPSide`（Working Plane Side）, `BIM_SetWPTop`（Working Plane Top）, `BIM_Setup`（BIM Setup）, `BIM_Shape2DCut`（Section Cut）, `BIM_Shape2DView`（Section View）, `BIM_SimpleCopy`（Simple Copy）, `BIM_Sketch`（New Sketch）, `BIM_Slab`（Slab）, `BIM_SplineTools`（Spline Tools）, `BIM_TDPage`（New Page）, `BIM_TDView`（New View）, `BIM_Text`（Text）, `BIM_Trash`（Move to Trash）, `BIM_Trimex`（Trimex）, `BIM_Tutorial`（BIM Tutorial）, `BIM_Unclone`（Unclone）, `BIM_Ungroup`（Remove From Group）, `BIM_Views`（Views Manager）, `BIM_WPView`（Working Plane View）, `BIM_Welcome`（BIM Welcome Screen）, `BIM_Windows`（Manage Doors and Windows）

### TechDraw（106）

`TechDraw_2LineCenterLine`（Centerline Between 2 Lines）, `TechDraw_2PointCenterLine`（Centerline Between 2 Points）, `TechDraw_2PointCosmeticLine`（Cosmetic Line Through 2 Points）, `TechDraw_3PtAngleDimension`（Angle Dimension From 3 Points）, `TechDraw_ActiveView`（Active View）, `TechDraw_AlignVertexesHorizontally`（Align Vertices/Edge Horizontally）, `TechDraw_AlignVertexesVertically`（Align Vertices/Edge Vertically）, `TechDraw_ArchView`（BIM View）, `TechDraw_AreaDimension`（Area Annotation）, `TechDraw_AxoLengthDimension`（Axonometric Length Dimension）, `TechDraw_BrokenView`（Broken View）, `TechDraw_CenterLineGroup`（Centerline）, `TechDraw_ClipGroup`（Clip Group）, `TechDraw_CommandAddOffsetVertex`（Offset Vertex）, `TechDraw_CommandVertexCreationGroup`（Cosmetic Intersection Vertices）, `TechDraw_CompDimensionTools`（Dimension）, `TechDraw_ComplexSection`（Complex Section View）, `TechDraw_CosmeticCircle`（Cosmetic 1 Point Circle）, `TechDraw_CosmeticEraser`（Remove Cosmetic Object）, `TechDraw_CosmeticVertex`（Cosmetic Vertex）, `TechDraw_CosmeticVertexGroup`（Cosmetic Vertex）, `TechDraw_DecorateLine`（Edit Line Appearance）, `TechDraw_Dimension`（Dimension）, `TechDraw_DimensionRepair`（Repair Dimension References）, `TechDraw_DraftView`（Draft View）, `TechDraw_ExportPagePDF`（Export Page as PDF）, `TechDraw_ExtensionArcLengthAnnotation`（Arc Length Annotation）, `TechDraw_ExtensionAreaAnnotation`（Area Annotation）, `TechDraw_ExtensionCascadeHorizDimension`（Cascade Horizontal Dimensions）, `TechDraw_ExtensionCascadeObliqueDimension`（Cascade Oblique Dimensions）, `TechDraw_ExtensionCascadeVertDimension`（Cascade Vertical Dimensions）, `TechDraw_ExtensionChamferDimensionGroup`（Horizontal Chamfer Dimension）, `TechDraw_ExtensionChangeLineAttributes`（Change Line Attributes）, `TechDraw_ExtensionCircleCenterLines`（Circle Centerlines）, `TechDraw_ExtensionCircleCenterLinesGroup`（Circle Centerlines）, `TechDraw_ExtensionCreateChainDimensionGroup`（Horizontal Chain Dimension）, `TechDraw_ExtensionCreateCoordDimensionGroup`（Horizontal Coordinate Dimension）, `TechDraw_ExtensionCreateHorizChainDimension`（Horizontal Chain Dimension）, `TechDraw_ExtensionCreateHorizChamferDimension`（Horizontal Chamfer Dimension）, `TechDraw_ExtensionCreateHorizCoordDimension`（Horizontal Coordinate Dimension）, `TechDraw_ExtensionCreateLengthArc`（Arc Length Dimension）, `TechDraw_ExtensionCreateObliqueChainDimension`（Oblique Chain Dimension）, `TechDraw_ExtensionCreateObliqueCoordDimension`（Oblique Coordinate Dimension）, `TechDraw_ExtensionCreateVertChainDimension`（Vertical Chain Dimension）, `TechDraw_ExtensionCreateVertChamferDimension`（Vertical Chamfer Dimension）, `TechDraw_ExtensionCreateVertCoordDimension`（Vertical Coordinate Dimension）, `TechDraw_ExtensionCustomizeFormat`（Customize Format Label）, `TechDraw_ExtensionDecreaseDecimal`（Decrease Decimal Places）, `TechDraw_ExtensionDrawCirclesGroup`（Cosmetic 1 Point Circle）, `TechDraw_ExtensionDrawCosmArc`（Cosmetic Arc）, `TechDraw_ExtensionDrawCosmCircle`（Cosmetic 2 Point Circle）, `TechDraw_ExtensionDrawCosmCircle3Points`（Cosmetic 3 Point Circle）, `TechDraw_ExtensionExtendLine`（Extend Line）, `TechDraw_ExtensionExtendShortenLineGroup`（Extend Line）, `TechDraw_ExtensionHoleCircle`（Bolt Circle Centerlines）, `TechDraw_ExtensionIncreaseDecimal`（Increase Decimal Places）, `TechDraw_ExtensionIncreaseDecreaseGroup`（Increase Decimal Places）, `TechDraw_ExtensionInsertDiameter`（Insert '⌀' Prefix）, `TechDraw_ExtensionInsertPrefixGroup`（Insert '⌀' Prefix）, `TechDraw_ExtensionInsertRepetition`（Insert 'n×' Prefix）, `TechDraw_ExtensionInsertSquare`（Insert '□' Prefix）, `TechDraw_ExtensionLinePPGroup`（Cosmetic Parallel Line）, `TechDraw_ExtensionLineParallel`（Cosmetic Parallel Line）, `TechDraw_ExtensionLinePerpendicular`（Cosmetic Perpendicular Line）, `TechDraw_ExtensionLockUnlockView`（Toggle View Lock）, `TechDraw_ExtensionPosHorizChainDimension`（Align Horizontal Chain Dimensions）, `TechDraw_ExtensionPosObliqueChainDimension`（Align Oblique Chain Dimensions）, `TechDraw_ExtensionPosVertChainDimension`（Align Vertical Chain Dimensions）, `TechDraw_ExtensionPositionSectionView`（Position Section View）, `TechDraw_ExtensionRemovePrefixChar`（Remove Prefix）, `TechDraw_ExtensionSelectLineAttributes`（Select Line Attributes, Cascade Spacing and Delta Distance）, `TechDraw_ExtensionShortenLine`（Shorten Line）, `TechDraw_ExtensionThreadBoltBottom`（Cosmetic Thread Bolt Bottom View）, `TechDraw_ExtensionThreadBoltSide`（Cosmetic Thread Bolt Side View）, `TechDraw_ExtensionThreadHoleBottom`（Cosmetic Thread Hole Bottom View）, `TechDraw_ExtensionThreadHoleSide`（Cosmetic Thread Hole Side View）, `TechDraw_ExtensionThreadsGroup`（Cosmetic Thread Hole Side View）, `TechDraw_ExtensionVertexAtIntersection`（Cosmetic Intersection Vertices）, `TechDraw_ExtentGroup`（Extent Dimension）, `TechDraw_FaceCenterLine`（Centerline on Face）, `TechDraw_FillTemplateFields`（Update Template Fields）, `TechDraw_GeometricHatch`（Geometric Hatch）, `TechDraw_Hatch`（Image Hatch）, `TechDraw_HoleShaftFit`（Hole/Shaft Fit）, `TechDraw_HorizontalExtentDimension`（Horizontal Extent Dimension）, `TechDraw_Image`（Bitmap Image）, `TechDraw_LeaderLine`（Leader Line）, `TechDraw_Midpoints`（Midpoint Vertices）, `TechDraw_ProjectShape`（Project Shape）, `TechDraw_Quadrants`（Quadrant Vertices）, `TechDraw_RedrawPage`（Redraw Page）, `TechDraw_RichTextAnnotation`（Rich Text Annotation）, `TechDraw_SectionGroup`（Section View (Simple or Complex)）, `TechDraw_ShareView`（Share View）, `TechDraw_ShowAll`（Toggle Edge Visibility）, `TechDraw_SpreadsheetView`（Spreadsheet View）, `TechDraw_StackBottom`（Stack Bottom）, `TechDraw_StackDown`（Stack Down）, `TechDraw_StackGroup`（View Stacking Order）, `TechDraw_StackTop`（Stack Top）, `TechDraw_StackUp`（Stack Up）, `TechDraw_SurfaceFinishSymbols`（Surface Finish Symbol）, `TechDraw_Symbol`（Insert SVG）, `TechDraw_ToggleFrame`（Toggle View Frames）, `TechDraw_VerticalExtentDimension`（Vertical Extent Dimension）, `TechDraw_WeldSymbol`（Weld Symbol）

### Draft（78）

`Draft_AddConstruction`（Add to Construction Group）, `Draft_AddNamedGroup`（New Named Group）, `Draft_AddToGroup`（Add to Group）, `Draft_AddToLayer`（Add to Layer）, `Draft_AnnotationStyleEditor`（Annotation Styles）, `Draft_ApplyStyle`（Apply Current Style）, `Draft_Arc`（Arc）, `Draft_ArcTools`（Arc Tools）, `Draft_Arc_3Points`（Arc From 3 Points）, `Draft_ArrayTools`（Array Tools）, `Draft_BSpline`（B-Spline）, `Draft_BezCurve`（Bézier Curve）, `Draft_BezierTools`（Bézier Tools）, `Draft_Circle`（Circle）, `Draft_Clone`（Clone）, `Draft_CubicBezCurve`（Cubic Bézier Curve）, `Draft_Dimension`（Dimension）, `Draft_Downgrade`（Downgrade）, `Draft_Draft2Sketch`（Draft to Sketch）, `Draft_Edit`（Edit）, `Draft_Ellipse`（Ellipse）, `Draft_Facebinder`（Facebinder）, `Draft_Fillet`（Fillet）, `Draft_FlipDimension`（Flip Dimension）, `Draft_Hatch`（Hatch）, `Draft_Heal`（Heal）, `Draft_Join`（Join）, `Draft_Label`（Label）, `Draft_Layer`（New Layer）, `Draft_LayerManager`（Manage Layers）, `Draft_Line`（Line）, `Draft_Mirror`（Mirror）, `Draft_Move`（Move）, `Draft_Offset`（Offset）, `Draft_OrthoArray`（Array）, `Draft_PathLinkArray`（Path Link Array）, `Draft_Point`（Point）, `Draft_PointLinkArray`（Point Link Array）, `Draft_PolarArray`（Polar Array）, `Draft_Polygon`（Polygon）, `Draft_Rectangle`（Rectangle）, `Draft_Rotate`（Rotate）, `Draft_Scale`（Scale）, `Draft_SelectGroup`（Select Group）, `Draft_SelectPlane`（Working Plane）, `Draft_SetStyle`（Set Style）, `Draft_Shape2DView`（Shape 2D View）, `Draft_ShapeString`（Shape From Text）, `Draft_ShowSnapBar`（Show Snap Toolbar）, `Draft_Slope`（Set Slope）, `Draft_Snap_Angle`（Snap Angle）, `Draft_Snap_Center`（Snap Center）, `Draft_Snap_Dimensions`（Snap Dimensions）, `Draft_Snap_Endpoint`（Snap Endpoint）, `Draft_Snap_Extension`（Snap Extension）, `Draft_Snap_Grid`（Snap Grid）, `Draft_Snap_Intersection`（Snap Intersection）, `Draft_Snap_Lock`（Snap Lock）, `Draft_Snap_Midpoint`（Snap Midpoint）, `Draft_Snap_Near`（Snap Near）, `Draft_Snap_Ortho`（Snap Ortho）, `Draft_Snap_Parallel`（Snap Parallel）, `Draft_Snap_Perpendicular`（Snap Perpendicular）, `Draft_Snap_Special`（Snap Special）, `Draft_Snap_WorkingPlane`（Snap Working Plane）, `Draft_Split`（Split）, `Draft_Stretch`（Stretch）, `Draft_SubelementHighlight`（Highlight Subelements）, `Draft_Text`（Text）, `Draft_ToggleConstructionMode`（Toggle Construction Mode）, `Draft_ToggleDisplayMode`（Toggle Wireframe）, `Draft_ToggleGrid`（Toggle Grid）, `Draft_Trimex`（Trimex）, `Draft_UpdateShape2DView`（Force 2D View Update）, `Draft_Upgrade`（Upgrade）, `Draft_Wire`（Polyline）, `Draft_WireToBSpline`（Convert Wire/B-Spline）, `Draft_WorkingPlaneProxy`（Working Plane Proxy）

### FEM（78）

`FEM_Analysis`（New Analysis）, `FEM_ClippingPlaneAdd`（Clipping Plane on Face）, `FEM_ClippingPlaneRemoveAll`（Remove All Clipping Planes）, `FEM_CompEmConstraints`（Electromagnetic Boundary Conditions）, `FEM_CompEmEquations`（Electromagnetic Equations）, `FEM_CompMechEquations`（Mechanical Equations）, `FEM_CompSolvers`（Solvers）, `FEM_ConstantVacuumPermittivity`（Constant Vacuum Permittivity）, `FEM_ConstraintBearing`（Bearing Constraint）, `FEM_ConstraintBodyHeatSource`（Body Heat Source）, `FEM_ConstraintCentrif`（Centrifugal Load）, `FEM_ConstraintContact`（Contact Constraint）, `FEM_ConstraintCurrentDensity`（Current Density Boundary Condition）, `FEM_ConstraintDisplacement`（Displacement Boundary Condition）, `FEM_ConstraintElectricChargeDensity`（Electric Charge Density）, `FEM_ConstraintElectromagnetic`（Electromagnetic Boundary Condition）, `FEM_ConstraintFixed`（Fixed Boundary Condition）, `FEM_ConstraintFlowVelocity`（Flow Velocity Boundary Condition）, `FEM_ConstraintFluidBoundary`（Fluid Boundary Condition）, `FEM_ConstraintForce`（Force Load）, `FEM_ConstraintGear`（Gear Constraint）, `FEM_ConstraintHeatflux`（Heat Flux Load）, `FEM_ConstraintInitialFlowVelocity`（Initial Flow Velocity Condition）, `FEM_ConstraintInitialPressure`（Initial Pressure Condition）, `FEM_ConstraintInitialTemperature`（Initial Temperature）, `FEM_ConstraintMagnetization`（Magnetization Boundary Condition）, `FEM_ConstraintPlaneRotation`（Plane Multi-Point Constraint）, `FEM_ConstraintPressure`（Pressure Load）, `FEM_ConstraintPulley`（Pulley Constraint）, `FEM_ConstraintRigidBody`（Rigid Body Constraint）, `FEM_ConstraintSectionPrint`（Section Print Feature）, `FEM_ConstraintSelfWeight`（Gravity Load）, `FEM_ConstraintSpring`（Spring Boundary Condition）, `FEM_ConstraintTemperature`（Temperature Boundary Condition）, `FEM_ConstraintTie`（Tie Constraint）, `FEM_ConstraintTransform`（Local Coordinate System）, `FEM_CreateElementsSet`（Erase Elements）, `FEM_CreateNodesSet`（Nodes Set）, `FEM_ElementFluid1D`（Fluid Section for 1D Flow）, `FEM_ElementGeometry1D`（Beam Cross Section）, `FEM_ElementGeometry2D`（Shell Plate Thickness）, `FEM_ElementRotation1D`（Beam Rotation）, `FEM_EquationFlow`（Flow Equation）, `FEM_EquationFlux`（Flux Equation）, `FEM_EquationHeat`（Heat Equation）, `FEM_Examples`（FEM Examples）, `FEM_FEMMesh2Mesh`（FEM Mesh to Mesh）, `FEM_MaterialEditor`（Material Editor）, `FEM_MaterialFluid`（Fluid Material）, `FEM_MaterialMechanicalNonlinear`（Non-Linear Mechanical Material）, `FEM_MaterialReinforced`（Reinforced Material (Concrete)）, `FEM_MaterialSolid`（Solid Material）, `FEM_MeshClear`（Clear FEM Mesh）, `FEM_MeshClearGroups`（Clear Mesh Groups）, `FEM_MeshDisplayInfo`（Display Mesh Info）, `FEM_MeshGMSHRefinement`（GMSH Refinements）, `FEM_MeshGmshFromShape`（Mesh From Shape by Gmsh）, `FEM_MeshGroup`（Mesh Group）, `FEM_MeshNetgenFromShape`（Mesh From Shape by Netgen）, `FEM_MeshRegion`（Mesh Refinement）, `FEM_PostApplyChanges`（Apply Changes to Pipeline）, `FEM_PostBranchFilter`（Pipeline Branch）, `FEM_PostCreateFunctions`（Filter Functions）, `FEM_PostFilterCalculator`（Calculator Filter）, `FEM_PostFilterClipRegion`（Region Clip Filter）, `FEM_PostFilterClipScalar`（Scalar Clip Filter）, `FEM_PostFilterContours`（Contours Filter）, `FEM_PostFilterCutFunction`（Function Cut Filter）, `FEM_PostFilterDataAlongLine`（Line Clip Filter）, `FEM_PostFilterDataAtPoint`（Data at Point Clip Filter）, `FEM_PostFilterGlyph`（Glyph Filter）, `FEM_PostFilterLinearizedStresses`（Stress Linearization Plot）, `FEM_PostFilterWarp`（Warp Filter）, `FEM_PostPipelineFromResult`（Post Pipeline From Result）, `FEM_ResultShow`（Show Result）, `FEM_ResultsPurge`（Purge Results）, `FEM_SolverControl`（Solver Job Control）, `FEM_SolverRun`（Run Solver）

### Part（57）

`Part_Boolean`（Boolean Operation）, `Part_BooleanFragments`（Boolean Fragments）, `Part_Box`（Cube）, `Part_BoxSelection`（Box Selection）, `Part_Builder`（Shape Builder）, `Part_Chamfer`（Chamfer）, `Part_ColorPerFace`（Appearance per Face）, `Part_Common`（Intersection）, `Part_CompCompoundTools`（Compound Tools）, `Part_CompJoinFeatures`（Join Shapes）, `Part_CompOffset`（Offset）, `Part_CompSplitFeatures`（Split Shapes）, `Part_Compound`（Compound）, `Part_CompoundFilter`（Compound Filter）, `Part_Cone`（Cone）, `Part_CrossSections`（Cross-Sections）, `Part_Cut`（Cut）, `Part_Cylinder`（Cylinder）, `Part_Defeaturing`（Defeaturing）, `Part_EditAttachment`（Attachment）, `Part_ElementCopy`（Shape Element Copy）, `Part_ExplodeCompound`（Explode Compound）, `Part_Extrude`（Extrude）, `Part_Fillet`（Fillet）, `Part_Fuse`（Union）, `Part_JoinConnect`（Connect Shapes）, `Part_JoinCutout`（Cutout Shape）, `Part_JoinEmbed`（Embed Shapes）, `Part_LinkArrays`（Link Arrays）, `Part_Loft`（Loft）, `Part_MakeFace`（Face From Wires）, `Part_MakeSolid`（Convert to Solid）, `Part_Mirror`（Mirror）, `Part_Offset`（3D Offset）, `Part_Offset2D`（2D Offset）, `Part_PointsFromMesh`（Points From Shape）, `Part_Primitives`（Primitive）, `Part_ProjectionOnSurface`（Project on Surface）, `Part_RefineShape`（Refine Shape）, `Part_ReverseShape`（Reverse Shapes）, `Part_Revolve`（Revolve）, `Part_RuledSurface`（Ruled Surface）, `Part_Scale`（Scale）, `Part_Section`（Section）, `Part_SectionCut`（Persistent Section Cut）, `Part_ShapeFromMesh`（Shape From Mesh）, `Part_SimpleCopy`（Simple Copy）, `Part_Slice`（Slice to Compound）, `Part_SliceApart`（Slice Apart）, `Part_Sphere`（Sphere）, `Part_Sweep`（Sweep）, `Part_Thickness`（Thickness）, `Part_ToleranceSet`（Set Tolerance）, `Part_Torus`（Torus）, `Part_TransformedCopy`（Transformed Copy）, `Part_Tube`（Tube）, `Part_XOR`（Boolean XOR）

### CAM（55）

`CAM_Adaptive`（Adaptive）, `CAM_Area`（Area）, `CAM_Area_Workplane`（Area Workplane）, `CAM_Array`（Array）, `CAM_Comment`（Comment）, `CAM_Custom`（Custom）, `CAM_Deburr`（Deburr）, `CAM_DressupArray`（Array）, `CAM_DressupAxisMap`（Axis Map）, `CAM_DressupDogbone`（Dogbone）, `CAM_DressupDragKnife`（Drag Knife）, `CAM_DressupLeadInOut`（Lead In/Out）, `CAM_DressupMirror`（Mirror）, `CAM_DressupPathBoundary`（Boundary）, `CAM_DressupPlungeMilling`（Plunge Milling）, `CAM_DressupRampEntry`（Ramp Entry）, `CAM_DressupTag`（Tag）, `CAM_DressupTools`（Dressup Operations）, `CAM_DressupZCorrect`（Z Depth Correction）, `CAM_Drilling`（Drilling）, `CAM_DrillingTools`（Drilling Operations）, `CAM_Engrave`（Engrave）, `CAM_EngraveTools`（Engraving Operations）, `CAM_ExportTemplate`（Export Template）, `CAM_Flute`（Flute）, `CAM_Helix`（Helix）, `CAM_Inspect`（Inspect Toolpath）, `CAM_Job`（New Job）, `CAM_MillFacing`（Mill Facing）, `CAM_OpActiveToggle`（Toggle Operation）, `CAM_OperationCopy`（Copy Operation）, `CAM_PathShape`（Path from Shape）, `CAM_Pocket3D`（3D Pocket）, `CAM_Pocket_Shape`（Pocket Shape）, `CAM_Post`（Post Process）, `CAM_PostSelected`（Post Process Selected）, `CAM_PostTools`（Post process Operations）, `CAM_Probe`（Probe）, `CAM_Profile`（Profile）, `CAM_PropertyBag`（Property Bag）, `CAM_Sanity`（Sanity Check）, `CAM_SelectLoop`（Finish Selecting Loop）, `CAM_SetStartPoint`（Start Point Selection）, `CAM_SimTools`（Simulators）, `CAM_SimpleCopy`（Simple Copy）, `CAM_Simulator`（Legacy CAM Simulator）, `CAM_SimulatorGL`（CAM Simulator）, `CAM_Slot`（Slot）, `CAM_Stop`（Stop）, `CAM_ThreadMilling`（Thread Milling）, `CAM_ToolBitDock`（Add Toolbit…）, `CAM_ToolBitSave`（Save Tool）, `CAM_ToolBitSaveAs`（Save Tool As…）, `CAM_Vcarve`（Vcarve）, `CAM_Workplane`（Work Plane）

### Mesh（37）

`MeshPart_CreateFlatFace`（Unwrap Face）, `MeshPart_CreateFlatMesh`（Unwrap Mesh）, `MeshPart_Mesher`（Mesh From Shape）, `Mesh_AddFacet`（Add Triangle）, `Mesh_BoundingBox`（Bounding Box Info）, `Mesh_BuildRegularSolid`（Regular Solid）, `Mesh_CrossSections`（Cross-Sections）, `Mesh_CurvatureInfo`（Curvature Info）, `Mesh_Decimating`（Decimate）, `Mesh_Difference`（Difference）, `Mesh_EvaluateFacet`（Face Info）, `Mesh_EvaluateSolid`（Evaluate Solid）, `Mesh_Evaluation`（Evaluate and Repair）, `Mesh_Export`（Export Mesh…）, `Mesh_FillInteractiveHole`（Close Hole）, `Mesh_FillupHoles`（Fill Holes）, `Mesh_FlipNormals`（Flip Normals）, `Mesh_FromPartShape`（Mesh From Shape）, `Mesh_HarmonizeNormals`（Harmonize Normals）, `Mesh_Import`（Import Mesh…）, `Mesh_Intersection`（Intersection）, `Mesh_Merge`（Merge）, `Mesh_PolyCut`（Cut）, `Mesh_PolySegm`（Segment）, `Mesh_PolyTrim`（Trim）, `Mesh_RemeshGmsh`（Refinement）, `Mesh_RemoveCompByHand`（Remove Components Manually）, `Mesh_RemoveComponents`（Remove Components）, `Mesh_Scale`（Scale）, `Mesh_SectionByPlane`（Section From Plane）, `Mesh_Segmentation`（Segmentation）, `Mesh_SegmentationBestFit`（Segmentation From Best-Fit Surfaces）, `Mesh_Smoothing`（Smooth）, `Mesh_SplitComponents`（Split by Components）, `Mesh_TrimByPlane`（Trim With Plane）, `Mesh_Union`（Union）, `Mesh_VertexCurvature`（Curvature Plot）

### Std（5）

`Std_LinkMakeGroup`（Link Group）, `Std_OnlineHelp`（Help）, `Std_ToggleFreeze`（Toggle Freeze）, `Std_ToggleSuppress`（Toggle Suppressed）, `Std_TreeSelectAllInstances`（Select All Instances）

### Robot（15）

`Robot_AddToolShape`（Tool）, `Robot_Create`（Place Robot）, `Robot_CreateTrajectory`（Trajectory）, `Robot_Edge2Trac`（Edge to Trajectory）, `Robot_ExportKukaCompact`（Kuka Compact Subroutine）, `Robot_ExportKukaFull`（Kuka Full Subroutine）, `Robot_InsertWaypoint`（Insert in Trajectory）, `Robot_InsertWaypointPreselect`（Insert in Trajectory）, `Robot_RestoreHomePos`（Move to Home）, `Robot_SetDefaultOrientation`（Set Default Orientation）, `Robot_SetDefaultValues`（Set Default Values）, `Robot_SetHomePos`（Set Home Position）, `Robot_Simulate`（Simulate Trajectory）, `Robot_TrajectoryCompound`（Trajectory Compound）, `Robot_TrajectoryDressUp`（Dress-Up Trajectory）

### Spreadsheet（15）

`Spreadsheet_AlignBottom`（Align Bottom）, `Spreadsheet_AlignCenter`（Align Horizontal Center）, `Spreadsheet_AlignLeft`（Align Left）, `Spreadsheet_AlignRight`（Align Right）, `Spreadsheet_AlignTop`（Align Top）, `Spreadsheet_AlignVCenter`（Align Vertical Center）, `Spreadsheet_CreateSheet`（New Spreadsheet）, `Spreadsheet_Export`（Export Spreadsheet）, `Spreadsheet_Import`（Import Spreadsheet）, `Spreadsheet_MergeCells`（Merge Cells）, `Spreadsheet_SetAlias`（Set Alias）, `Spreadsheet_SplitCell`（Split Cell）, `Spreadsheet_StyleBold`（Bold Text）, `Spreadsheet_StyleItalic`（Italic Text）, `Spreadsheet_StyleUnderline`（Underline Text）

### OpenSCAD（14）

`OpenSCAD_AddOpenSCADElement`（Add OpenSCAD Element）, `OpenSCAD_Edgestofaces`（Convert Edges to Faces）, `OpenSCAD_ExpandPlacements`（Expand Placements）, `OpenSCAD_ExplodeGroup`（Explode Group）, `OpenSCAD_Hull`（Hull）, `OpenSCAD_IncreaseToleranceFeature`（Increase Tolerance Feature）, `OpenSCAD_MeshBoolean`（Mesh Boolean）, `OpenSCAD_Minkowski`（Minkowski Sum）, `OpenSCAD_MirrorMeshFeature`（Mirror Mesh Feature）, `OpenSCAD_RefineShapeFeature`（Refine Shape Feature）, `OpenSCAD_RemoveSubtree`（Remove Objects and Children）, `OpenSCAD_ReplaceObject`（Replace Object）, `OpenSCAD_ResizeMeshFeature`（Resize Mesh Feature）, `OpenSCAD_ScaleMeshFeature`（Scale Mesh Feature）

### ReverseEngineering（12）

`Reen_ApproxCurve`（Approximate B-Spline Curve…）, `Reen_ApproxCylinder`（Cylinder）, `Reen_ApproxPlane`（Plane）, `Reen_ApproxPolynomial`（Polynomial Surface）, `Reen_ApproxSphere`（Sphere）, `Reen_ApproxSurface`（Approximate B-Spline Surface…）, `Reen_MeshBoundary`（Wire From Mesh Boundary…）, `Reen_PoissonReconstruction`（Poisson…）, `Reen_Segmentation`（Mesh Segmentation…）, `Reen_SegmentationFromComponents`（From Components）, `Reen_SegmentationManual`（Manual Segmentation…）, `Reen_ViewTriangulation`（Structured Point Clouds）

### Test（0）



### Assembly（10）

`Assembly_ActivateAssembly`（Activate Assembly）, `Assembly_CreateJointGearBelt`（Gears/Belt Joint）, `Assembly_CreateJointRackPinion`（Rack and Pinion Joint）, `Assembly_CreateJointRigidGroup`（Create Rigid Group）, `Assembly_CreateJointScrew`（Screw Joint）, `Assembly_CreateSimulation`（Simulation）, `Assembly_CreateSnapshot`（Snapshot）, `Assembly_ExportASMT`（Export ASMT File）, `Assembly_LinkSelectLinked`（Go to Linked Assembly）, `Assembly_SelectJointsOfComponent`（Select Component Joints）

### Sketcher（4）

`Sketcher_CancelSketch`（Cancel Editing）, `Sketcher_NewSketch`（New Sketch）, `Sketcher_ProfilesHexagon1`（Creates a hexagonal profile）, `Sketcher_StopOperation`（Stop Operation）

### PartDesign（7）

`PartDesign_CompSketches`（Create Datum）, `PartDesign_InvoluteGear`（Involute Gear）, `PartDesign_MoveFeature`（Move Object To…）, `PartDesign_MoveFeatureInTree`（Move Feature After…）, `PartDesign_MoveTip`（Set Tip）, `PartDesign_Sprocket`（Sprocket）, `PartDesign_WizardShaft`（Shaft Design Wizard）

### Points（6）

`Points_Convert`（Convert to Points）, `Points_Export`（Export Points…）, `Points_Import`（Import Points…）, `Points_Merge`（Merge Point Clouds）, `Points_PolyCut`（Cut Point Cloud）, `Points_Structure`（Structured Point Cloud）

### Surface（6）

`Surface_BlendCurve`（Blend Curve）, `Surface_CurveOnMesh`（Curve on Mesh）, `Surface_ExtendFace`（Extend Face）, `Surface_Filling`（Filling）, `Surface_GeomFillSurface`（Fill Boundary Curves）, `Surface_Sections`（Sections）

### Material（3）

`Material_Edit`（Edit）, `Materials_InspectAppearance`（Inspect Appearance）, `Materials_InspectMaterial`（Inspect Material）

### Inspection（2）

`Inspection_InspectElement`（Inspection…）, `Inspection_VisualInspection`（Visual Inspection）
