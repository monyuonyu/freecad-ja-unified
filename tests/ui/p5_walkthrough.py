# P5「設定と AI パネル」の受け入れ: ☰ → 設定 が「したいこと」の 6 分類で開き、探す欄で「プロキシ」「JIS」「タッチパッド」が
# 正しい分類に着くこと、変えるとすぐ効くこと（マウスの方式）、AI パネルに「たずねずに実行」が常には出ないことを確かめて撮る。
# 使い方: guictl start → guictl py "exec(open('p5_walkthrough.py').read())"（OUT は P5_OUT）
import json
import os

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui, QtWidgets

OUT = os.environ.get("P5_OUT", "/tmp/p5-accept")
os.makedirs(OUT, exist_ok=True)


def pump(ms=300):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(700)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


import UnifiedSettings

Gui.runCommand("Unified_AIChat")
pump(500)
w = UnifiedSettings.SettingsWindow(Gui.getMainWindow())
w.show()
pump(300)
kinds = [w.list.item(i).text() for i in range(w.list.count())]
found = {}
for word, page in (("プロキシ", 4), ("JIS", 2), ("タッチパッド", 1)):
    w.search.setText(word)
    pump(200)
    found[word] = w.list.currentRow() == page
    if word == "プロキシ":
        shot("p5-01-settings-proxy")
w.search.setText("")
w.list.setCurrentRow(1)
combo = w.stack.currentWidget().widget().findChildren(QtWidgets.QComboBox)[0]
combo.setCurrentIndex(combo.findData("Gui::TouchpadNavigationStyle"))
pump(300)
style = App.ParamGet("User parameter:BaseApp/Preferences/View").GetString("NavigationStyle")
shot("p5-02-settings-mouse")
combo.setCurrentIndex(combo.findData("Gui::TinkerCADNavigationStyle"))
w.accept()
import AIChatGui

auto_visible = AIChatGui.chat.panel.auto_box.isVisible()
shot("p5-03-ai-panel")
results = {"settings": {"ok": len(kinds) == 6 and all(found.values()) and style == "Gui::TouchpadNavigationStyle" and not auto_visible,
                        "kinds": kinds, "search": found, "mouse_style_set_at_once": style, "ai_auto_box_visible": auto_visible}}
with open(os.path.join(OUT, "result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
{k: v["ok"] for k, v in results.items()}
