# 3D 画面の「見ている所についていく」操作（0.6.4）の受け入れ: 本物のマウスの出来事（xdotool）で
# ホイールと右ドラッグを送り、カメラを前後で比べる。画面も撮る。
# 使い方: KANTAN_GUI_DISPLAY=:177 KANTAN_GUI_STATE=/tmp/navlook guictl start --fresh
#         → guictl py - < nav_look_check.py（結果は OUT/result.json と画像）
import json
import math
import os
import subprocess
import traceback

import FreeCAD as App
import FreeCADGui as Gui
import Part
from PySide import QtCore, QtGui, QtWidgets
from pivy import coin

OUT = os.environ.get("NAV_OUT", "/tmp/navlook-accept")
os.makedirs(OUT, exist_ok=True)
results = {}
P = App.ParamGet("User parameter:BaseApp/Preferences/View")


def pump(ms=150):
    loop = QtCore.QEventLoop()
    QtCore.QTimer.singleShot(ms, loop.quit)
    loop.exec()


def shot(name):
    pump(300)
    QtGui.QGuiApplication.primaryScreen().grabWindow(0).save(os.path.join(OUT, name + ".png"))


def xdo(*args):
    subprocess.run(["xdotool"] + [str(a) for a in args], check=True)
    pump(30)


def view():
    return Gui.ActiveDocument.ActiveView


def widget_origin():
    w = view().graphicsView()
    g = w.viewport().mapToGlobal(QtCore.QPoint(0, 0))
    return g.x(), g.y()


def to_screen(coin_xy):
    """Coin's pixel (y up) of the 3D view to the X screen"""
    ox, oy = widget_origin()
    _w, h = view().getSize()
    return ox + int(coin_xy[0]), oy + (h - 1 - int(coin_xy[1]))


def pixel_of(point):
    x, y = view().getPointOnViewport(point)
    return float(x), float(y)


def camera():
    cam = view().getCameraNode()
    pos = cam.position.getValue()
    d = cam.orientation.getValue().multVec(coin.SbVec3f(0, 0, -1))
    info = {
        "type": cam.getTypeId().getName().getString(),
        "position": [pos[0], pos[1], pos[2]],
        "focalDistance": cam.focalDistance.getValue(),
        "direction": [d[0], d[1], d[2]],
    }
    if isinstance(cam, coin.SoOrthographicCamera):
        info["height"] = cam.height.getValue()
    return info


def focal_point():
    c = camera()
    return App.Vector(*c["position"]) + App.Vector(*c["direction"]) * c["focalDistance"]


def in_view(px):
    w, h = view().getSize()
    return 0 <= px[0] < w and 0 <= px[1] < h


def wheel(sx, sy, notches, up=True):
    xdo("mousemove", sx, sy)
    for _ in range(notches):
        xdo("click", 4 if up else 5)
    pump(200)


def right_drag(sx, sy, dx, dy, steps=12, shots=None):
    xdo("mousemove", sx, sy)
    xdo("mousedown", 3)
    for i in range(1, steps + 1):
        xdo("mousemove", sx + dx * i // steps, sy + dy * i // steps)
        pump(40)
        if shots and i in shots:
            shot(shots[i])
    xdo("mouseup", 3)
    pump(200)
    # a right click without dragging would open the context menu: none must be open
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, QtWidgets.QMenu) and w.isVisible():
            w.close()
            return False
    return True


ORTHO = [False]


def make_scene():
    for d in list(App.listDocuments()):
        App.closeDocument(d)
    doc = App.newDocument("NavLook")
    plate = doc.addObject("Part::Box", "Plate")
    plate.Length, plate.Width, plate.Height = 1000, 600, 40
    pin = doc.addObject("Part::Cylinder", "Pin")
    pin.Radius, pin.Height = 2, 3
    pin.Placement.Base = App.Vector(720, 380, 40)
    doc.recompute()
    pump(300)
    view().setCameraType("Orthographic" if ORTHO[0] else "Perspective")
    pump(200)
    view().viewIsometric()
    view().fitAll()
    pump(500)
    return doc, plate, pin


def pick(sx, sy):
    """The point of the model under the X screen position"""
    ox, oy = widget_origin()
    _w, h = view().getSize()
    info = view().getObjectInfo((sx - ox, h - 1 - (sy - oy)))
    return App.Vector(info["x"], info["y"], info["z"]) if info else None


def empty_spot():
    """A pixel of the view (X screen) with nothing of the model under it"""
    ox, oy = widget_origin()
    w, h = view().getSize()
    for fy in (0.03, 0.2, 0.5, 0.8, 0.97):
        for fx in (0.03, 0.2, 0.5, 0.8, 0.97):
            sx, sy = ox + int(fx * w), oy + int(fy * h)
            if pick(sx, sy) is None:
                return sx, sy
    return None


def outside(shape, point):
    return not shape.isInside(point, 1e-6, True)


def dolly_case(name, steps=50):
    doc, plate, pin = make_scene()
    shape = plate.Shape.fuse(pin.Shape)
    feature = App.Vector(720, 380, 43)  # the top of the pin
    before = camera()
    px0 = pixel_of(feature)
    sx, sy = to_screen(px0)
    target = pick(sx, sy)
    tpx0 = pixel_of(target)
    shot(name + "_0_before")
    wheel(sx, sy, steps, up=True)
    after = camera()
    px1 = pixel_of(feature)
    tpx1 = pixel_of(target)
    eye = App.Vector(*after["position"])
    shot(name + "_1_after_%d_steps" % steps)
    r = {
        "before": before,
        "after": after,
        "feature_pixel_before": px0,
        "feature_pixel_after": px1,
        "feature_in_view": in_view(px1),
        "target_on_the_pin": [target.x, target.y, target.z],
        "target_moved_px": math.hypot(tpx1[0] - tpx0[0], tpx1[1] - tpx0[1]),
        "eye_to_target": (eye - target).Length,
        "feature_moved_px": math.hypot(px1[0] - px0[0], px1[1] - px0[1]),
        "eye_outside_solid": outside(shape, eye),
        "eye_to_feature": (eye - feature).Length if after["type"] != "SoOrthographicCamera" else None,
        "focal_point_to_feature": (focal_point() - feature).Length,
    }
    # On scrolling: never through the surface
    wheel(sx, sy, 100, up=True)
    later = camera()
    eye2 = App.Vector(*later["position"])
    r["after_150_steps"] = later
    r["eye_outside_solid_after_150"] = outside(shape, eye2)
    r["feature_in_view_after_150"] = in_view(pixel_of(feature))
    r["target_moved_px_after_150"] = math.hypot(pixel_of(target)[0] - tpx0[0], pixel_of(target)[1] - tpx0[1])
    r["eye_to_target_after_150"] = (eye2 - target).Length
    shot(name + "_2_after_150_steps")
    # And back out again
    wheel(sx, sy, 150, up=False)
    r["back_out"] = camera()
    shot(name + "_3_back_out")
    return r


def rotate_case(name, shots=True):
    doc, plate, pin = make_scene()
    feature = App.Vector(720, 380, 43)
    sx, sy = to_screen(pixel_of(feature))
    wheel(sx, sy, 40, up=True)
    # Rotate with the cursor on the plate's top a little beside the pin
    w, h = view().getSize()
    gx, gy = to_screen(pixel_of(feature))
    gx += 60
    ox, oy = widget_origin()
    info = view().getObjectInfo((gx - ox, h - 1 - (gy - oy)))
    grabbed = App.Vector(info["x"], info["y"], info["z"]) if info else None
    px_before = pixel_of(grabbed)
    pin_before = pixel_of(feature)
    shot_map = {3: name + "_rot_1", 6: name + "_rot_2", 9: name + "_rot_3", 12: name + "_rot_4"} if shots else None
    if shots:
        shot(name + "_rot_0")
    no_menu = right_drag(gx, gy, 260, 120, steps=12, shots=shot_map)
    px_after = pixel_of(grabbed)
    pin_after = pixel_of(feature)
    r = {
        "grabbed": [grabbed.x, grabbed.y, grabbed.z] if grabbed else None,
        "grabbed_pixel_before": px_before,
        "grabbed_pixel_after": px_after,
        "grabbed_moved_px": math.hypot(px_after[0] - px_before[0], px_after[1] - px_before[1]),
        "pin_in_view_after": in_view(pin_after),
        "pin_pixel_before": pin_before,
        "pin_pixel_after": pin_after,
        "no_context_menu": no_menu,
        "camera": camera(),
    }
    if ORTHO[0]:
        r["ortho_height"] = camera()["height"]
    return r


def background_case(name):
    """Turning with the cursor on the empty background: the pivot is the point last looked at
    (the target of the wheel), which keeps its place; no far away center"""
    make_scene()
    feature = App.Vector(720, 380, 43)
    sx, sy = to_screen(pixel_of(feature))
    target = pick(sx, sy)
    wheel(sx, sy, 8, up=True)
    spot = empty_spot()
    r = {"empty_background_found": spot is not None}
    if spot:
        before = pixel_of(target)
        shot(name + "_bg_0")
        right_drag(spot[0], spot[1], 200, 60, steps=10, shots={5: name + "_bg_1", 10: name + "_bg_2"})
        after = pixel_of(target)
        r["target_pixel_before"] = before
        r["target_pixel_after"] = after
        r["target_moved_px"] = math.hypot(after[0] - before[0], after[1] - before[1])
    return r


def pan_case():
    make_scene()
    feature = App.Vector(720, 380, 43)
    sx, sy = to_screen(pixel_of(feature))
    wheel(sx, sy, 30, up=True)
    fp_before = focal_point()
    feature = pick(sx, sy)
    xdo("mousemove", sx, sy)
    xdo("mousedown", 2)
    for i in range(1, 9):
        xdo("mousemove", sx - 20 * i, sy + 10 * i)
    xdo("mouseup", 2)
    pump(200)
    px = pixel_of(feature)
    ox, oy = widget_origin()
    w, h = view().getSize()
    expect = (sx - 160 - ox, h - 1 - (sy + 80 - oy))
    return {
        "feature_follows_cursor_px": math.hypot(px[0] - expect[0], px[1] - expect[1]),
        "focal_depth_to_feature": abs((focal_point() - feature).dot(App.Vector(*camera()["direction"]))),
        "focal_point_before": [fp_before.x, fp_before.y, fp_before.z],
    }


def fit_all_case():
    make_scene()
    view().fitAll()
    pump(400)
    bb = App.ActiveDocument.Plate.Shape.BoundBox
    return {"focal_point_to_scene_center": (focal_point() - bb.Center).Length}


def other_style_case():
    """A stock style keeps zooming as before (the focal distance does not follow)"""
    P.SetString("NavigationStyle", "Gui::CADNavigationStyle")
    pump(200)
    make_scene()
    feature = App.Vector(720, 380, 43)
    before = camera()
    sx, sy = to_screen(pixel_of(feature))
    wheel(sx, sy, 5, up=True)
    after = camera()
    P.SetString("NavigationStyle", "Gui::TinkerCADNavigationStyle")
    pump(200)
    return {"before": before, "after": after}


def touchpad_case():
    P.SetString("NavigationStyle", "Gui::TouchpadNavigationStyle")
    pump(200)
    make_scene()
    feature = App.Vector(720, 380, 43)
    sx, sy = to_screen(pixel_of(feature))
    d0 = (App.Vector(*camera()["position"]) - feature).Length
    wheel(sx, sy, 30, up=True)
    d1 = (App.Vector(*camera()["position"]) - feature).Length
    feature = pick(sx, sy)
    px0 = pixel_of(feature)
    # Alt + move turns about the point under the cursor (the view has the keyboard)
    gx, gy = to_screen(px0)
    xdo("mousemove", gx, gy)
    view().graphicsView().setFocus()
    pump(100)
    xdo("keydown", "alt")
    for i in range(1, 9):
        xdo("mousemove", gx + 25 * i, gy + 10 * i)
        pump(30)
    xdo("keyup", "alt")
    pump(200)
    px1 = pixel_of(feature)
    P.SetString("NavigationStyle", "Gui::TinkerCADNavigationStyle")
    pump(200)
    return {
        "distance_before": d0,
        "distance_after_30_steps": d1,
        "feature_pixel_before_turn": px0,
        "feature_pixel_after_turn": px1,
        "feature_moved_px": math.hypot(px1[0] - px0[0], px1[1] - px0[1]),
    }


def set_ortho(on):
    ORTHO[0] = on


try:
    mw = Gui.getMainWindow()
    mw.showMaximized()
    pump(500)
    results["default_navigation"] = P.GetString("NavigationStyle", "")
    App.newDocument("First")
    pump(500)
    results["default_camera"] = camera()["type"]
    results["default_orthographic_param"] = P.GetBool("Orthographic", True)
    set_ortho(False)
    results["perspective_dolly"] = dolly_case("persp")
    results["perspective_rotate"] = rotate_case("persp")
    results["perspective_background_rotate"] = background_case("persp")
    results["pan"] = pan_case()
    results["fit_all"] = fit_all_case()
    set_ortho(True)
    results["ortho_dolly"] = dolly_case("ortho")
    results["ortho_rotate"] = rotate_case("ortho", shots=False)
    results["ortho_background_rotate"] = background_case("ortho")
    set_ortho(False)
    results["touchpad"] = touchpad_case()
    results["cad_style"] = other_style_case()
except Exception:
    results["error"] = traceback.format_exc()

json.dump(results, open(os.path.join(OUT, "result.json"), "w"), indent=1, default=str)
print(json.dumps(results, indent=1, default=str))
