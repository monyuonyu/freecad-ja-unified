#!/usr/bin/env python3
"""Write the tool names of the terminology table (src/Mod/Unified/Wording.py) into the Japanese
override translations (src/Mod/Unified/Gui/Resources/translations/UnifiedWording_ja.ts).

  apply_wording.py CMDINFO.json [CommandCatalog.json] [--src ~/freecad-src] [--dry]

CMDINFO.json: the untranslated texts of the commands, dumped inside a running FreeCAD:
  {name: {"ctx": className, "menu": menuText, "tip": toolTip, "status": statusTip}}
(see tests/ui/p11_check.py, which writes it as accept/P11/cmdinfo.json), and/or the tool search's
catalog made by the build. Commands of modules that are in neither take their texts from
Wording.SOURCES.

A Python command's texts are translated in the context of its name. The line breaks of the .ts
file are kept.
"""
import html
import importlib.util
import json
import os
import re
import sys


def load_wording(src):
    path = os.path.join(src, "src/Mod/Unified/Wording.py")
    spec = importlib.util.spec_from_file_location("Wording", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def upsert(text, ctx, src_esc, tr_esc, nl):
    """The translation of (context, source) becomes tr; added when missing. Every copy of a
    source in the context gets it (a .ts may have the same source twice)."""
    m = re.search(r"<context>\s*<name>" + re.escape(ctx) + r"</name>(.*?)</context>", text, re.S)
    if m:
        body = m.group(1)
        pat = re.compile(
            r"(<source>" + re.escape(src_esc) + r"</source>\s*(?:<comment>.*?</comment>\s*)?)<translation[^>]*>.*?</translation>",
            re.S,
        )
        if pat.search(body):
            body = pat.sub(lambda mm: mm.group(1) + "<translation>" + tr_esc + "</translation>", body)
        else:
            body = body.rstrip(" ") + "    <message>" + nl + "        <source>" + src_esc + "</source>" + nl + \
                "        <translation>" + tr_esc + "</translation>" + nl + "    </message>" + nl
        return text[:m.start(1)] + body + text[m.end(1):]
    block = "<context>" + nl + "    <name>" + ctx + "</name>" + nl + "    <message>" + nl + "        <source>" + src_esc + \
        "</source>" + nl + "        <translation>" + tr_esc + "</translation>" + nl + "    </message>" + nl + "</context>" + nl
    i = text.rindex("</TS>")
    return text[:i] + block + text[i:]


def main():
    args = sys.argv[1:]
    dry = "--dry" in args
    src = os.path.expanduser("~/freecad-src")
    if "--src" in args:
        src = os.path.expanduser(args[args.index("--src") + 1])
    info = {}
    for path in [a for a in args if a.endswith(".json")]:
        data = json.load(open(path, encoding="utf-8"))
        if isinstance(data, dict) and "commands" in data:
            # The tool search's catalog (build/release/Mod/Unified/CommandCatalog.json): every
            # command of every module, also those not loaded
            for e in data["commands"]:
                info.setdefault(e["name"], {"ctx": e.get("ctx"), "menu": e.get("en_raw") or e.get("en"),
                                            "tip": e.get("tip_en") or "", "status": e.get("tip_en") or ""})
        else:
            info.update(data)
    W = load_wording(src)
    ts = os.path.join(src, "src/Mod/Unified/Gui/Resources/translations/UnifiedWording_ja.ts")
    text = open(ts, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text[:2000] else "\n"

    def esc(s):
        return html.escape(s, quote=False).replace("\n", nl)

    done, missing = 0, []
    for command, (name, tooltip) in W.TOOLS.items():
        bad = W.problems(name)
        if bad:
            sys.exit("{}: {} — {}".format(command, name, bad))
        if command in W.SOURCES:
            ctx, menu, tip = W.SOURCES[command]
            status = tip
        elif command in info and info[command].get("menu"):
            i = info[command]
            ctx = i["ctx"] if i["ctx"] != "PythonCommand" else command
            menu, tip, status = i["menu"], i.get("tip") or "", i.get("status") or ""
        else:
            missing.append(command)
            continue
        text = upsert(text, ctx, esc(menu), esc(name), nl)
        if tooltip:
            for source in {tip, status} - {""}:
                text = upsert(text, ctx, esc(source), esc(tooltip), nl)
        done += 1
    if missing:
        print("not found (the module was not loaded?):", ", ".join(missing))
    print(done, "tools")
    if not dry:
        open(ts, "w", encoding="utf-8", newline="").write(text)


if __name__ == "__main__":
    main()
