**元にした FreeCAD: {BASE_VERSION}（main のコミット [`{BASE_SHORT}`](https://github.com/FreeCAD/FreeCAD/commit/{BASE_SHA})）＋ このリポジトリのパッチ {TAG}**

ファイル名は `FreeCAD_{BASE_VERSION}-{BASE_SHORT}_{TAG}-<OS>…`（元の FreeCAD の版・元にしたコミット・このパッチの版）。
試しに使ってもらうための先行版。

- **Linux**: `…-Linux-x86_64.AppImage` に実行権限を付けて起動
- **Windows**: `…-Windows-x86_64-installer.exe`（インストーラー）か `.7z`（展開して `bin\FreeCAD.exe`）

署名はしていないので、Windows では SmartScreen の警告が出る（「詳細情報」→「実行」）。
設定フォルダは本家の FreeCAD とは別（`FreeCAD-ja-unified`）。0.3.1 以前の設定は引き継がない。
アンインストールでは、画面の「ユーザー設定も削除」を選ぶと設定も消える（選ばなければ残る。本家の設定には触れない）。

変更点は [README](https://github.com/monyuonyu/freecad-ja-unified#readme) を参照:
作業場の切り替えを無くした一つの画面、選んだものの横に出る操作、1 種類に固定したマウス操作、
プロパティ欄と失敗の知らせまで含めた日本語化、設計の検査（DRC のような間違い探しと自動修正）、
AI チャット、今風のナビキューブ、コマンドライン・スクリプトまわりの修正。

AI チャットを使うには、自分の Anthropic の API キーが要る（使った分はキーの持ち主に請求される。
AI が実行するコードは毎回表示され、承認したときだけ動く）。

Built from FreeCAD {BASE_VERSION} (main, commit {BASE_SHORT}) with the patches {TAG} of this repository. Unsigned preview build.
