日本語で迷わず使える一つの画面にした FreeCAD の改良版。DWG（AutoCAD の図面）を R2018 まで読み書きできる LibreDWG と、Jw_cad の図面（JWW）を開ける jww2dxf を同梱。**元にした FreeCAD: {BASE_VERSION}（main のコミット [`{BASE_SHORT}`](https://github.com/FreeCAD/FreeCAD/commit/{BASE_SHA})）＋ このリポジトリのパッチ {TAG}**

**ダウンロード**

| OS | ファイル | 使い方 |
|---|---|---|
| Windows（x64） | `FreeCAD_{BASE_VERSION}-{BASE_SHORT}_{TAG}-Windows-x86_64-installer.exe` | インストーラー |
| | `FreeCAD_{BASE_VERSION}-{BASE_SHORT}_{TAG}-Windows-x86_64.7z` | 展開して `bin\FreeCAD.exe`（署名なし。SmartScreen は「詳細情報」→「実行」） |
| Linux（x86_64） | `FreeCAD_{BASE_VERSION}-{BASE_SHORT}_{TAG}-Linux-x86_64.AppImage` | 実行権限を付けて起動。WSL など FUSE の無い所では `--appimage-extract` で展開して `squashfs-root/AppRun` |

チェックサム: 各ファイルの `-SHA256.txt`。設定フォルダは本家とは別（`FreeCAD-ja-unified`）。アンインストールで「ユーザー設定も削除」を選ぶと設定も消える。

**変更点**: [README の各版の変更](https://github.com/monyuonyu/freecad-ja-unified/blob/main/README.ja.md)。機能の一覧も README にある。
AI チャットは自分の Anthropic の API キーで使う（AI が実行するコードは毎回表示され、承認したときだけ動く）。

---
FreeCAD {BASE_VERSION} (main, {BASE_SHORT}) + patches {TAG}: one Japanese-first working screen, DWG read/write up to R2018 via the bundled LibreDWG, Jw_cad (JWW) drawings via the bundled jww2dxf, headless rendering/interference/2D export. Windows (installer/7z) and Linux (AppImage); unsigned preview builds. See the [README](https://github.com/monyuonyu/freecad-ja-unified#readme).
