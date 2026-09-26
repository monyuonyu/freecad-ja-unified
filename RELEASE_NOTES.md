FreeCAD（main `b48098efa`、26.3.0dev）にこのリポジトリのパッチを当ててビルドしたもの。試しに使ってもらうための先行版。

- **Linux**: `…-Linux-x86_64.AppImage` に実行権限を付けて起動
- **Windows**: `…-Windows-x86_64-installer.exe`（インストーラー）か `.7z`（展開して `bin\FreeCAD.exe`）

署名はしていないので、Windows では SmartScreen の警告が出る（「詳細情報」→「実行」）。
設定フォルダは本家の FreeCAD と共通。

変更点は [README](https://github.com/monyuonyu/freecad-ja-unified#readme) を参照:
作業場の切り替えを無くした一つの画面、選んだものの横に出る操作、1 種類に固定したマウス操作、
プロパティ欄まで含めた日本語化、コマンドライン・スクリプトまわりの修正。

Built from FreeCAD main `b48098efa` with the patches in this repository. Unsigned preview build.
