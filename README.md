**English** | [日本語](README.ja.md) | [简体中文](README.zh-CN.md)

> Translated from [README.ja.md](README.ja.md) (the Japanese version is the original) at commit `513d863`.

# freecad-ja-unified

FreeCAD turned into a single screen where you don't get lost, and made usable in Japanese.
Workbench switching is gone, the next actions appear right where you picked something,
and the UI wording is plain Japanese throughout. It also adds a "design check" that finds mistakes and an AI chat that looks at the model and fixes it.
Bugs that show up when using FreeCAD from the command line or from scripts are fixed as well. Everything is kept as patches on top of upstream FreeCAD (not submitted upstream).

The application's UI is in Japanese. In this page, Japanese labels you need to find on screen are given in quotes next to their English meaning.

![Click a face and the next actions appear next to it](docs/images/08_face_actions.png)

- Based on: FreeCAD main `b48098efa` (2026-09-26, version string 26.3.0dev)
- Bundled OndselSolver: `4be80eef`

## Download

Prebuilt packages are on [Releases](https://github.com/monyuonyu/freecad-ja-unified/releases).

- Linux: `FreeCAD_<version>-Linux-x86_64.AppImage` (make it executable and run it)
- Windows: `FreeCAD_<version>-Windows-x86_64-installer.exe` (installer) or `.7z` (extract and run `bin/FreeCAD.exe`)

The builds are not signed, so Windows shows a SmartScreen warning ("More info" → "Run anyway").

Settings, macros and window layout are stored in a separate place from upstream FreeCAD (`FreeCAD-ja-unified`). The Windows installer also
installs to a separate location (`FreeCAD-ja-unified 26.3`). Up to 0.3.1 they were shared with upstream (running both side by side mixed up the settings).

Uninstalling removes the program, shortcuts, file associations and registry entries (verified on Windows).
Your own settings are kept by default, as with upstream (so they carry over if you reinstall). To remove them, choose
"ユーザー設定も削除" (also delete user settings) in the uninstaller. Only this build's settings are removed; upstream FreeCAD's settings are not touched.

## A tour in screenshots

### First start

Just pick the language, units and look (light/dark). You can change them later under "編集 → 設定" (Edit → Preferences).

![The first-start screen](docs/images/01_first_start.png)

### New part → click where to draw

The start screen only has "新しい部品" (New part) and "ファイルを開く" (Open file). Pressing New part immediately asks where to draw.
Unlike upstream, there is no dialog where you select a face and press OK: you click a plane in the 3D view, or a flat face of a part, once.

![The start screen](docs/images/02_start.png)

![Click where to draw in the 3D view](docs/images/03_pick_plane.png)

### Only sketch tools while sketching

While you are drawing a sketch, the toolbar switches to the sketch tools and switches back when you finish.
Points snap to the grid, so even freehand mouse drawing gives round dimensions. The number of degrees of freedom left is shown in Japanese.

![Editing a sketch](docs/images/04_sketch.png)

### After drawing, the next step appears alongside

When you close a sketch, "押し出す・回転・編集・AI に頼む" (Extrude, Revolve, Edit, Ask AI) appear next to it. No need to hunt through the toolbar.
The main toolbar tools also have names under their icons (押し出し "Pad", 切り抜き "Pocket", 丸め "Fillet", …).

![Suggestions after closing a sketch](docs/images/05_after_sketch.png)

The task panel only appears while a tool is in use and disappears when you are done (the view is also adjusted so the model fits on screen).

![Pad settings](docs/images/06_pad_panel.png)

### Click a face to see what you can do with it

For a face you get Sketch, Pad, Pocket, Hole and Thickness; for an edge, Fillet and Chamfer (top image).
"穴" (Hole) is made right at the point you clicked (upstream requires drawing a point in a sketch first).
The object under the cursor is shown by name and location instead of `Preselected: Unnamed.Body.Pad.Face6`.
Double-clicking a face opens the editor of the feature that created it (Pad, Fillet, …).

![What is shown under the cursor](docs/images/08b_hover.png)

### Snap parts together, move point to point

Putting parts flush against each other no longer needs the Placement dialog, attachment or
assembly joints. Click a face of the part to move, Ctrl+click a face of the other part, and
"くっつける" (Snap together) appears next to it: the faces end up touching, facing each other.
**The first pick moves** (the panel says which moves where; "入れ替え" swaps them).

![Two faces picked: "Snap together" appears](docs/images/15_snap_pick.png)

The part moves as soon as you press it. Flip (same direction instead of facing), gap, turn
(90° steps or any angle) and what lines up (the clicked points, the centers, or keep the
position along the face) apply right away. OK keeps it (one undo step), Cancel or Esc puts it back.

![The panel after snapping](docs/images/16_snap_panel.png)

Two round faces offer "軸をそろえる" (line up the axes, e.g. a shaft into a hole), a point and a
face "点を面に合わせる" (point onto a face), two points "点から点へ" (point to point).

![A shaft lined up with a hole](docs/images/18_shaft_in_hole.png)

"点から点へ動かす" (Move point to point) moves without turning: click the base point, then the
destination. The cursor snaps to vertices, middles of edges, centers of circles and faces, with
a marker and its name; a see-through copy follows the cursor; Ctrl makes a copy.

![Move point to point](docs/images/17_point_to_point.png)

The tools also start from the Model menu, the toolbar, `J` (snap) and `Shift+M` (point to point).
What moves is the part the picked element belongs to (a Body, a shape, an imported STEP, a link),
or a container around it chosen in the panel; nested and rotated containers are handled in global
coordinates. An attached part keeps its attachment with a new offset, or is detached, as you choose.

### Design check and "直す" (Fix)

Like DRC in PCB CAD, it lists the mistakes in the whole model: failed features, interference between parts, conflicting sketch constraints,
floating parts, drawing dimensions that have lost their geometry, and so on. Selecting a row zooms to the part and puts a red marker at the spot.
The status bar always shows the result ("検査: エラー 2・警告 2", i.e. "Check: 2 errors, 2 warnings").

![Design check](docs/images/09_design_check.png)

Issues with an obvious fix (redundant or conflicting constraints, floating parts, overlapping parts, empty projection views) are fixed with "直す" (Fix).
Below is the result after pressing "直せるものを全部直す" (Fix everything that can be fixed). A single Undo reverts all of it.

![After fixing](docs/images/10_design_fixed.png)

### Ask AI

Ask in the "AI" panel on the right, and the AI (Claude) looks at the model, makes the change, verifies it with the design check and the view, and reports back.
If you select faces or edges and press "AI に頼む" (Ask AI), the selection is passed along too. The code the AI wants to run is shown every time,
and it only runs when you press "実行する" (Run). Each run becomes one Undo step.

![Approving the AI's code](docs/images/11_ai_approve.png)

![The AI added a fillet and checked it](docs/images/12_ai_done.png)

### Error messages in Japanese too

Failure messages that stay in English upstream (such as `BRep_API: command not done`) are shown in Japanese, explaining what went wrong and what to do.
Messages containing constraint numbers or edge numbers are translated as well.

![An error message](docs/images/13_error_ja.png)

### NaviCube

The orientation cube at the top right normally shows just the cube. Hovering the mouse over it reveals the arrows and other controls,
and clicking near an edge or corner of a face turns the view to that edge or corner (easier to hit). Tooltips tell you what will happen.

![NaviCube before and after](docs/images/14_navicube.png)

## Differences from upstream (summary)

| | Upstream FreeCAD | This patch set |
|---|---|---|
| Workbenches | Switch between Part / PartDesign / Sketcher / Draft / TechDraw / Assembly … | No switching. Sketch, solids, drawings and assemblies on one screen |
| 2D drafting | Two systems: Sketcher and Draft | Sketcher only (sketch tools shown only while sketching) |
| Drawings and assemblies | Each in its own workbench | Under the "図面" (Drawing) and "アセンブリ" (Assembly) menus, with descriptions |
| First step | Many choices on the start screen | Only "New part" and "Open". New part goes straight to choosing the sketch plane |
| Choosing the sketch plane | Select a face in a dialog and press OK | Click a face or datum plane in the 3D view once |
| Actions after selecting | Hunt for them in the toolbar | Suggestions next to the selection (face → Sketch/Pad/Pocket/Thickness, edge → Fillet/Chamfer, sketch → Pad/Revolve/Edit, part → Move/Hide) |
| Toolbar | Icons only. Even at 1600 px wide some are hidden behind "»" | Main tools have names under their icons (Pad, Pocket, Fillet, …). The sketch tools fit in one row too |
| Sketch snapping | Off by default | Snaps near grid points (round dimensions even when drawing with the mouse) |
| What is shown under the cursor | `Preselected: Unnamed.Body.Pad.Face6` | `押し出し の 面 6` ("Face 6 of Pad") |
| Double-click a face | Nothing happens | Opens the editor of the feature that created it (Pad, Fillet, …) |
| Put parts face to face, move point to point | Type numbers into the Placement dialog, set up attachment, make assembly joints, or use Draft Move (needs a workbench switch) | Pick two faces → "Snap together" (facing / same direction, gap, 90° turns, centers). Round faces → "Line up the axes", point + face → "Point onto a face", two points → "Point to point" (snaps to vertices, edge middles, circle and face centers; Ctrl copies). Live preview, OK keeps, Esc reverts |
| Select a face and press "Hole" | Fails with "no axis found" (you must draw a point in a sketch first) | A hole at the point you clicked |
| Drawing projection views | Appear at the bottom-left of the page until the file is reopened (an upstream bug). First-angle projection by default | Appear at the center of the page. Third-angle projection (JIS) by default |
| Modifying an imported solid (STEP etc.) | A dialog saying an active body is required | Sketch, fillet and pad work directly (it is turned into a part automatically) |
| Export with nothing selected | Stops with "Please select an object" | Exports the visible parts |
| Finding mistakes | "Check geometry" only checks whether the one selected shape is broken | "設計の検査" (Design check, similar to DRC in PCB CAD): lists failed features, split parts, interference between parts, conflicting sketch constraints, extremely short edges, floating parts and drawing dimensions that lost their geometry. Selecting a row selects and zooms to the part, with a red marker at the spot. Things done "on purpose" are recorded in the document as ignored. Fixable issues (redundant or conflicting constraints, floating parts, overlapping parts, empty projection views) are fixed with the "Fix" button (one Undo reverts it). The status bar always shows the result (number of errors and warnings). Also from the command line: `FreeCADCmd -c "import DesignCheck; DesignCheck.main('a.FCStd')"` |
| Ask AI | None | In the "AI" panel on the right, the AI (Claude) looks at the model, changes it, and verifies with the check and the view. "Ask AI" is offered among the suggestions when you select a face or edge, and in the design check list. By default the code the AI runs is shown every time and runs only after you approve it (each run is one Undo step; there is also a switch to skip confirmation). Requires your own Anthropic API key (see below) |
| Menus | "Macro" and developer tools sit in the top menus | One fewer top-level menu; advanced items of View and Tools moved to submenus |
| Initial spacing of a linear pattern | Always 100 mm (with small parts the copies end up off-screen) | Twice the size of the shape being patterned |
| Mouse navigation | Choose from 7 styles | One style by default (right-drag to rotate, middle-drag to pan, wheel to zoom). No screen to choose a style |
| Task panel | Always takes up space | Only shown while a tool is in use. When done, the view is adjusted so the model is visible |
| Context menu | Many items | Only what modeling needs (the rest stays in the top menus) |
| Preferences | Includes pages you don't use, such as BIM and Addons | Only the pages you use |
| Addon manager | Present | Removed (it is a mechanism for adding workbenches) |

No features have been removed. Things you rarely use are in the menus, with descriptions.

## Using the AI chat

1. Release packages (from 0.3.5) already include what the AI chat needs (claude-agent-sdk, keyring, Claude Code). No setup required.
   If you built it yourself, press "AI の準備をする" (Set up AI) in the "AI" panel on the right (installs into a Python virtual environment; needs network access)
2. Create an API key at [console.anthropic.com](https://console.anthropic.com/) and enter it with "API キーを入れる…" (Enter the API key…), shown when you first send a message.
   To change or remove it later: 編集 → 設定 → 標準 → AI チャット (Edit → Preferences → General → AI chat; from 0.5.7).
   The key is stored in the OS keystore (Windows Credential Manager, macOS Keychain, Linux Secret Service).
   On systems without a keystore, it goes into a file readable only by you (`ai/ai-api-key` in FreeCAD's user data)
3. Usage is billed to the account that owns the API key. This patch set contains no keys or logins
4. On a company network, set the proxy (system settings by default) and, if the network inspects TLS, the company certificate (PEM) in Edit → Preferences → General → Network (from 0.5.7)

The AI sends the document contents, images of the view and the design check results to the model (Opus by default).
By default the code the AI wants to run is shown every time and only runs when you press "実行する" (Run) (it can do things outside FreeCAD too, so read it first).
Turning on "たずねずに実行する" (Run without asking) at the bottom of the panel skips confirmation (until FreeCAD is closed; executed code is kept in the chat and in ai/ai-runs.log).

## Japanese

- Filled in untranslated text in menus, toolbars, task panels, notifications and preferences, and made the terms plain
  (e.g. Pad → 押し出し, Pocket → 切り抜き, Body → 部品, Constraint → 拘束)
- The property editor on the left (property names, groups, descriptions and enum values) is in Japanese
- Newly created objects get Japanese names (部品, スケッチ, 押し出し …)
- The Origin inside a part is hidden from the tree

In languages other than Japanese, the UI looks the same as upstream.

## Command line and scripts

| | Plain FreeCAD | With the patches |
|---|---|---|
| Script dies with an exception | Exit code **0**, the script **runs twice**, and the error is a single line | Runs once, exit code 1, full traceback |
| `if __name__ == "__main__":` | Not executed (the script is imported as a module) | Executed |
| `sys.argv` | FreeCAD's own arguments as-is | `FreeCADCmd a.py -- x y` → `['a.py', 'x', 'y']` |
| `sys.exit()` / `sys.exit("msg")` | 1 / message not printed | 0 / message printed to stderr |
| `print` right before an exception or `sys.exit()` | Can get lost | Printed |
| Nonexistent file | Exit code 0 | `No such file`, exit code 1 |
| `FreeCADCmd < a.py` | Processed line by line in interactive mode (`>>>` mixed into output, 0 even on errors) | Runs as a single script |
| Banner when running a script | Printed | Not printed (still printed in interactive mode) |
| STEP export | OCC statistics printed twice to stdout | Not printed (sent to the log) |
| Opening an assembly | Constraint solver messages printed to stdout | Not printed |
| `Part.export([shape], "a.step")` | **Silently writes an empty STEP** | Accepts Shapes / `ValueError` if there is nothing to write |
| Conversion failure with `--output` | Exit code 0 | Exit code 1 |
| `--help` | Name is always "FreeCAD", no usage explanation | Executable name, examples, exit codes. Shows `--output` (`-o`) and `--hidden` |
| Settings file | Rewritten on every run, even one that does nothing. Running in parallel can wipe settings | Written only when a value changes |
| `FreeCAD --hidden a.py` fails | Exit code 0 | Exit code 1 |
| Changing the view and saving with `--hidden` | Saves a frame from the middle of the animation | No animation |
| `--hidden` with settings from an older version | The settings migration dialog opens on an invisible screen and **hangs forever** | The dialog is not shown |
| Running with `--hidden` | Rewrites recent files and window layout | Leaves them alone |
| Python `saveImage()` | The navigation cube appears in the image | Not included (same as the "Save image" menu) |
| Rendering images | Needs a display (xvfb) and the GUI | `FreeCADCmd a.FCStd --render a.png --view iso` (no display or OpenGL needed. `--render-style shaded\|hidden-lines\|lines`, `--size 1600x1200`, `Part.renderImage` from Python) |
| Interference check | Tests every pair of parts (106 s for 300 parts) | `FreeCADCmd a.FCStd --interference` / `Part.findInterferences` (bounding-box prefilter and parallel, 1.2 s) |
| 2D views with hidden lines removed | Needs a TechDraw page | `--export-svg`, `--export-polygons` (polygon JSON per face), `--export-pptx` (PowerPoint with editable shapes) / `Part.projectVisible` |
| `Mesh.addFacets(shape.tessellate(d))` | **Silently drops** faces where boxes touch each other (624 → 12 faces with 52 boxes) | Adds everything (drops only with `check=True`, with a warning giving the count) |

## Fixes taken from upstream (PR list)

Pull requests submitted to upstream FreeCAD but not yet merged there, which were reviewed and taken in (author names are kept in the commits as-is).
From the 541 open PRs, we narrowed down to crashes, bugs and regressions in the parts this UI uses, read the changes, and confirmed that they apply on top of the patches and pass the tests.

**Crashes**

- [#32804](https://github.com/FreeCAD/FreeCAD/pull/32804) Crash when entering sketch edit mode or when moving the mouse (@alfrix)
- [#32975](https://github.com/FreeCAD/FreeCAD/pull/32975) Crash from an out-of-range read during sketch preselection (@alexdremov)
- [#32989](https://github.com/FreeCAD/FreeCAD/pull/32989) Crash when mirroring a sketch (@alfrix)
- [#32970](https://github.com/FreeCAD/FreeCAD/pull/32970) Crash from use-after-free when closing the task panel (@alexdremov)
- [#32007](https://github.com/FreeCAD/FreeCAD/pull/32007) Crashes such as clicking the 3D view while editing in the property editor (6 kinds; one spot in the task panel overlaps with #32970 and was left out) (@oursland)
- [#32684](https://github.com/FreeCAD/FreeCAD/pull/32684) Crash when opening an externally linked file (@chennes)
- [#31263](https://github.com/FreeCAD/FreeCAD/pull/31263) Crash on SpaceMouse input right after startup (@Maik-0000FF)

**Shapes and sketches**

- [#32430](https://github.com/FreeCAD/FreeCAD/pull/32430) Filleting a polyline loses its last point (@alfrix)
- [#32759](https://github.com/FreeCAD/FreeCAD/pull/32759) Explain why a fillet cannot be made at a point between curves (@VishalRamKN)
- [#28238](https://github.com/FreeCAD/FreeCAD/pull/28238) When a fillet or chamfer fails, show the cause (radius too large, face would twist, …) and how to fix it (@paragforwork)

**Drawings**

- [#32552](https://github.com/FreeCAD/FreeCAD/pull/32552) Views with a locked position jump to the origin on load (@WandererFan)
- [#32151](https://github.com/FreeCAD/FreeCAD/pull/32151) Repairing dimension references fails on broken references (@WandererFan)

**Assembly**

- [#31998](https://github.com/FreeCAD/FreeCAD/pull/31998) Error when adding a fixed joint to a part (@ryneeverett)
- [#32924](https://github.com/FreeCAD/FreeCAD/pull/32924) Orphaned joint groups cannot be deleted (@PaddleStroke)
- [#32922](https://github.com/FreeCAD/FreeCAD/pull/32922) Rack and pinion misbehaves (@PaddleStroke)

**Display and UI**

- [#32658](https://github.com/FreeCAD/FreeCAD/pull/32658) Colors of fused shapes break with the light/dark themes (@chennes)
- [#32813](https://github.com/FreeCAD/FreeCAD/pull/32813) Regression in the depth of the selection highlight (@Connor9220)
- [#32841](https://github.com/FreeCAD/FreeCAD/pull/32841) Garbled Japanese and other non-ASCII text in property editor choices (@maxwxyz)
- [#32996](https://github.com/FreeCAD/FreeCAD/pull/32996) Update the status bar when selecting in the tree with the keyboard (@007stevendigar-lgtm)

**Files**

- [#32934](https://github.com/FreeCAD/FreeCAD/pull/32934) ASCII STL files (long names, no trailing newline) cannot be read (@maxwxyz)

**Added in 0.3.3**

- [#32614](https://github.com/FreeCAD/FreeCAD/pull/32614) Moving a sketch point only slightly snaps it back (@Reqrefusion)
- [#30997](https://github.com/FreeCAD/FreeCAD/pull/30997) Crash when closing a document while Measure is open (@Amine0x0). Applied as-is, it overwrote another observer in this build and caused a later crash, so that was fixed too
- [#32879](https://github.com/FreeCAD/FreeCAD/pull/32879) Thickness stays silent when the result is an invalid shape (@007stevendigar-lgtm). Added a notice for when the thickness is so large that the shape doesn't change

### Upstream-reported bugs, not yet fixed upstream, that we fixed

Ones with reproduction steps, which we reproduced locally or traced to the cause.

- [#32968](https://github.com/FreeCAD/FreeCAD/issues/32968) Entering a sketch dimension in the expression editor loses the dimension when leaving the tool (a regression this month)
- [#32732](https://github.com/FreeCAD/FreeCAD/issues/32732) "Save to variable set" fails on mismatched units (crashes on macOS)
- [#32877](https://github.com/FreeCAD/FreeCAD/issues/32877) Opening a hidden document steals the active document (crashes on macOS)
- [#25050](https://github.com/FreeCAD/FreeCAD/issues/25050) A thickness larger than the part silently does nothing
- Deleting an intermediate feature (such as a pocket) leaves a later pattern still carrying the deleted hole while shown as "OK"
- Japanese and other non-ASCII names get garbled in STEP (export now uses the encoding the standard specifies, and import defaults to UTF-8; STEP files from other CAD tools still read)
- A zero-length view movement freezes the screen

Found by running the upstream tests under a memory-error detecting build (AddressSanitizer) (0.3.4):

- Deleting a part during a recompute makes later processing read the deleted part's memory (happens with CAM tools)
- The macro editor asks "reload?" about a deleted file and gets stuck
- Draft's selection box display reads more points than it was given

Also fixed a bug in the assembly solver (OndselSolver) where joint type names in assembly export (ASMT) were corrupted on Linux and macOS
(type names were cut out assuming the Windows format; found when upstream test #32922 failed on Linux).

## Changes in 0.6.3

- "Make Drawing": a picked face becomes the front view; hole center lines and callouts go on the view that shows the holes as circles
- The put-part panel of assemblies lists the FreeCAD/STEP/IGES files of the assembly's folder; a click opens one
- All UI acceptance walkthroughs (P0–P10) passed on the published 0.6.2 Linux AppImage

## Changes in 0.6.2

UI rebuild phases P5, P6 (part), P9, P10 ([status in chapter 13 of the design](docs/ui-redesign/00-design.md)).
**0.6.1 has no Windows build; on Windows use 0.6.2.**

- Preferences by purpose (basic, mouse and keys incl. touchpad, drawings, files, network and accounts, AI), effective at once, with search;
  "run AI code without asking" moved from the AI panel into the preferences; the first start asks for the mouse style
- Assemblies: STEP/IGES parts from the put-part panel; two round faces offer "Insert", "Hinge", "Join rigidly"; joints named by how parts move;
  a pin in a clearance hole is no longer reported as floating
- Export by purpose: for 3D printing (3MF/STL with a mesh check and "Fix, then export"), to other CAD (STEP), 2D (DXF/PDF of a drawing), image
- After opening a DXF/DWG/JWW or a mesh, a band offers what can be done with it (extrude to a solid, make a sketch, check and fix, make a solid)
- Only the active file in the tree, detailed properties folded away, the model placed beside the task panel
- Sketch sizes are typed in a small frameless box at the cursor
- STEP parts without product names were still named "Open CASCADE STEP translator" by one import path
- FreeCADCmd: print() of Japanese no longer raises on Windows legacy code pages or a C locale (UTF-8 on Windows; unprintable characters replaced);
  a Windows CI check prints Japanese under cp1252

## Changes in 0.6.1

**0.6.1 has no Windows build (use 0.6.2).**

UI rebuild phases P1–P4, P7 and P8 ([design](docs/ui-redesign/00-design.md)): one window without modes.
Acceptance screenshots in [docs/ui-redesign/accept](docs/ui-redesign/accept).

- Tool search (Ctrl+K, the field at the top right): every command of every module (1158, also of modules not loaded yet),
  by Japanese/English name, aliases and description; loads the module when picked; "Ask AI" when nothing fits.
  The catalog is made at build time by the built FreeCAD without a screen
- FreeCAD's menu bar and toolbars are replaced by one "☰" menu and one tool strip that never changes (also while
  sketching, on drawing pages, in assemblies); one-key shortcuts that never fire while typing or composing Japanese;
  Preferences › General › Screen brings the stock chrome back
- "Other tools": every tool by kind, specialist toolboxes (BIM, CAM, FEM, …) loaded on first use
- A step (sketch, tool panel) is a band in the same window with ✓ Done / ✕ Cancel (Cancel undoes the step)
- The bar next to a pick follows a rules table, with a number field (pick a face, type 12, Enter: extruded 12 mm)
- Start page: four ways to start, the search, and four guided first steps with samples
- "Make Drawing": three views on an A4 JIS sheet with center lines, hole callout ("4×⌀6 キリ"), sizes and title block
- Fixes: Start crashed without a top-level Help menu; applying network proxy settings froze the GUI; AI chat key handling

## Changes in 0.6.0

First stage (P0, "no dead ends") of the UI rebuild designed in [docs/ui-redesign/00-design.md](docs/ui-redesign/00-design.md)
(no modes; the stock FreeCAD chrome is to be replaced, not layered on). Everyday tasks that stopped at an English dialog
or at an upstream concept now go on without asking. Acceptance screenshots: [docs/ui-redesign/accept/P0](docs/ui-redesign/accept/P0).

- Saving as `plate.stl` picked the FEM exporter ("No FEM mesh for export selected"); a typed extension now picks the format's own filter
- Putting parts into an assembly no longer stops at "must be saved" / "ground the first part?": an unsaved assembly is saved
  provisionally (Save still asks for a place), parts of unsaved STEP documents are copied in, the first part is grounded
- DXF files open without the import-mode dialog; extruding a picked line of an opened drawing makes its closed outline the
  sketch of a new part instead of "an active body is required"; an unreadable DXF says so
- Three-view drawings face the largest flat face, include top and right views and use a standard scale that fits the page
  (they used to take the isometric 3D direction and overflow the page)
- Drawing selections in the status bar show user names ("Front view, edge 3"); STEP files without product names are named after the file
- Terms unified with the glossary (176 translations)

## Changes in 0.5.0

- DWG: **can now write R2004, R2010, R2013 and R2018 DWG** (previously up to R2000).
  The 149 test drawings were written in each version and read back with ACadSharp: 0 unreadable drawings, 0 lost entities, 0 entities that changed type (same via DXF).
  Also compared entity by entity with files AutoCAD saved in the same version
  - 3D solids (ACIS): reads and writes the R2013+ storage (AcDs), so shapes are not lost when writing old drawings or DXF to R2013 or later
  - Fixed DXF → DWG (dxf2dwg) losing nearly 20% of entities when writing R2010 or later
  - FreeCAD's own DWG export stays at R2000 (opens in any AutoCAD). For newer versions use the bundled `dxf2dwg --as r2018`
- Command line: images in one line (`--render`, no display or OpenGL needed), a fast interference check (`--interference`),
  and export of 2D views with hidden lines removed (SVG, per-face polygons, PowerPoint). See the "Command line and scripts" table
- Mesh: fixed `addFacets` silently dropping faces where parts touch, which left holes in STL files

## Changes in 0.4.1

- DWG: compared against the same drawings saved by AutoCAD itself in different versions, and made conversion when writing R2000 match AutoCAD.
  For example_2004 to 2018, every entity written to R2000 matches AutoCAD's R2000 save (same via DXF)
  - Colors: ByBlock entities had become ByLayer; color indices used in place of RGB colors now match AutoCAD; the color table uses current AutoCAD values
  - R14 drawings: entity linetypes (CONTINUOUS etc.) had become ByLayer, lineweights had become 0.00mm; standard names now match AutoCAD
  - Gradient hatches become a solid fill of the first color; MTEXT line breaks use \P (also in DXF)
- DWG: tables (TABLE) can now be read and written (not lost via DXF). All R2010+ table styles are read
- DWG: entities from proprietary applications whose contents can't be decoded (architecture add-ons etc.) are kept, with their original data, as proxy entities the same way AutoCAD does when writing to older versions or DXF
- DWG: fixed table style, dimension style and hatch names changing via DXF, and newer entity types being dropped from R14 DXF

## Changes in 0.4.0

- Reading and writing DWG: bundles LibreDWG (`dwg2dxf` / `dxf2dwg`), so File → Open / Import / Export handle DWG.
  Reads R13 to R2018 (including AC1032 from AutoCAD 2018 to 2025); writes in the version of the opened drawing (R2000 or earlier).
  LibreDWG 0.14.8601 is patched with fixes for read/write bugs found by comparing against an independent implementation (ACadSharp) on 149 drawings
  (`patches/libredwg`: tables, multi-line attributes, character encodings, writing to R2000, etc.). If you have configured your own converter, that one is used
- AI chat: when it stops at the limit on the number of turns (80), it now says so instead of going quiet, and tells you that "続けて" (continue) carries on
- AI chat: code that doesn't finish within 120 seconds is stopped and that run's changes are undone (so FreeCAD doesn't freeze). Completed changes are not undone just because the value of the last expression can't be displayed

## Changes in 0.3.6

- Fixed the AI chat components (ai-runtime) missing when installed with the Windows installer (the 0.3.5 7z has them)
- AI chat: a "たずねずに実行する" (Run without asking) switch (off by default; a warning appears when turning it on; not saved, so it goes back to asking every time once FreeCAD is closed.
  Executed code stays in the chat). "実行して、以後はたずねない" (Run, and don't ask again) in the approval window
- AI chat: fixed FreeCAD crashing and freezing on sys.exit in the AI's code (like other errors, that run's changes are undone and you are told)
- AI chat: the code the AI ran and its results are logged to ai/ai-runs.log in the user data
- Bugs in the AI's tools (found by the AI's own tests): on error, changes to other documents are also undone and the previously open document is restored.
  Runs that changed nothing no longer create an Undo step. Added and removed objects are counted by events, not by name.
  When a pattern created from Python is the last feature of a part, the Tip is advanced. The type field of get_document was being overwritten by feature properties (such as Length)
- Design check: reports features not used by the shape (after the Tip), parts with no shape, and hidden parts that were not checked.
  "Degrees of freedom left" is not shown while constraints are in conflict. States that constraint numbers count from 1
- Japanese: the points inside an origin are now called "原点の点" (origin point) (previously both they and the container's origin were "原点" (origin))

## Changes in 0.3.5

- The components the AI chat needs are bundled in the release packages. The AI panel works right after installing, with no setup over the network (talking to the AI itself still needs network access)
- Clearer explanations when the AI chat fails (invalid key etc.)

## Applying the patches and building

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

(The comments in the commands: building on Linux with the official pixi procedure, with FEM/CAM/Robot turned off to save time; the build takes about 2 hours on a 2-core, 4-thread laptop; install puts FreeCADCmd and FreeCAD in .pixi/envs/default/bin.)

## Tests

```sh
XDG_CONFIG_HOME=$(mktemp -d) XDG_DATA_HOME=$(mktemp -d) \
  tests/run.sh <FreeCADCmd のパス> <FreeCAD のパス>
```

(`<FreeCADCmd のパス>` and `<FreeCAD のパス>` are the paths to FreeCADCmd and FreeCAD.)

Always point the settings folders at temporary directories (so your real settings are not polluted). The GUI items need `xvfb-run`.
Plain FreeCAD 1.1.3 passes 4/17; with the patches, all items (31) pass.
FreeCAD's own tests (`FreeCADCmd -t 0`, and the C++ tests for Base/App/Part/Gui) were also confirmed to pass with the patches.

## LibreDWG (the DWG converter)

`tools/build_libredwg.sh <output dir> [linux|win64]` applies `patches/libredwg` to upstream LibreDWG 0.14.8601 and
builds `dwg2dxf` / `dxf2dwg` (the Windows build is a MinGW-w64 cross build, no DLLs needed). The release procedure uses this too.

## jww-tools (the Jw_cad converter)

Since 0.5.6, File → Open / Import also open Jw_cad drawings (`.jww`) and registered symbols (`.jws`), through the bundled
`jww2dxf` from [jww-tools](https://github.com/monyuonyu/jww-tools) (checked figure by figure against Jw_cad's own DXF export
on 307 drawings). `tools/build_jww2dxf.sh <output dir> [linux|win64]` builds it from a pinned jww-tools tag (statically
linked; the Windows build is a MinGW-w64 cross build). The release procedure uses this too.

## Making a release

Patches are exported with `tools/export_patches.sh` (regenerates patches/ from unified-ui in a FreeCAD clone).


Run the "Build release" GitHub Actions workflow (`.github/workflows/release.yml`) manually, entering the tag name.
It applies the patches to the base version, builds Linux and Windows with the same `package/bundle` procedure as upstream, and attaches them to the release (takes several hours).


## License

The patches are LGPL-2.1-or-later, the same as FreeCAD (`LICENSE`).
