import os
import sys
from types import SimpleNamespace

import pytest

from laptop_remote.core import overlay as overlay_module
from laptop_remote.core.overlay_x11 import X11LaserOverlay, _circle_rectangles


class FakeWindow:
    def __init__(self):
        self.shapes = []
        self.configurations = []
        self.attributes = []
        self.mapped = False

    def shape_rectangles(self, *args):
        self.shapes.append(args)

    def configure(self, **kwargs):
        self.configurations.append(kwargs)

    def change_attributes(self, **kwargs):
        self.attributes.append(kwargs)

    def map(self):
        self.mapped = True

    def unmap(self):
        self.mapped = False

    def clear_area(self, *args):
        pass

    def destroy(self):
        pass


class FakeDisplay:
    def __init__(self):
        self.window = FakeWindow()
        self.root = SimpleNamespace(create_window=lambda *args, **kwargs: self.window)
        self.screen_info = SimpleNamespace(
            root=self.root,
            root_depth=24,
            black_pixel=0,
            width_in_pixels=1920,
            height_in_pixels=1080,
            default_colormap=SimpleNamespace(
                alloc_named_color=lambda name: SimpleNamespace(pixel=0xFF0000)
            ),
        )

    def has_extension(self, name):
        return name == "SHAPE"

    def shape_query_version(self):
        return SimpleNamespace(major_version=1, minor_version=1)

    def screen(self):
        return self.screen_info

    def sync(self):
        pass

    def flush(self):
        pass

    def close(self):
        pass


def make_backend(monkeypatch):
    fake_display = FakeDisplay()
    xlib = SimpleNamespace(
        InputOutput=1,
        CopyFromParent=0,
        Above=0,
        Unsorted=0,
    )
    shape_api = SimpleNamespace(
        SO=SimpleNamespace(Set=0),
        SK=SimpleNamespace(Bounding=0, Input=2),
    )
    monkeypatch.setenv("DISPLAY", ":test")
    backend = X11LaserOverlay(
        display_factory=lambda: fake_display,
        xlib=xlib,
        shape_api=shape_api,
    )
    return backend, fake_display


def test_circle_shape_is_symmetric_and_within_window():
    rectangles = _circle_rectangles(radius=3)

    assert len(rectangles) == 7
    assert [rect[2] for rect in rectangles] == [1, 5, 5, 7, 5, 5, 1]
    assert rectangles == [
        (rectangles[-index - 1][0], index, rectangles[-index - 1][2], 1)
        for index in range(len(rectangles))
    ]


def test_x11_overlay_is_shaped_click_through_and_supports_blackout(monkeypatch):
    backend, fake_display = make_backend(monkeypatch)

    assert backend.start() is True
    assert backend.available is True
    assert len(fake_display.window.shapes[0][-1]) == 25
    assert fake_display.window.shapes[1][-1] == []

    backend.show()
    backend.move(100, 200)
    assert fake_display.window.mapped is True
    assert fake_display.window.configurations[-1]["x"] == 88
    assert fake_display.window.configurations[-1]["y"] == 188

    backend.set_blackout(True)
    assert backend.blackout is True
    assert fake_display.window.mapped is True
    assert fake_display.window.shapes[-1][-1][0] == (0, 0, 1920, 1080)

    backend.set_blackout(False)
    assert backend.blackout is False
    assert backend.visible is False
    assert fake_display.window.mapped is False
    assert fake_display.window.shapes[-1][-1][0][2:] == (1, 1)


def test_x11_overlay_stays_unavailable_without_display(monkeypatch):
    monkeypatch.delenv("DISPLAY", raising=False)
    backend = X11LaserOverlay(display_factory=lambda: pytest.fail("must not connect"))

    assert backend.start() is False
    assert backend.available is False


def test_laser_overlay_delegates_to_x11_backend(monkeypatch):
    calls = []

    class Backend:
        available = True
        visible = False

        def start(self):
            calls.append("start")
            return True

        def show(self):
            calls.append("show")
            self.visible = True

        def hide(self):
            calls.append("hide")
            self.visible = False

        def move(self, x, y):
            calls.append(("move", x, y))

        def set_blackout(self, on):
            calls.append(("blackout", on))
            self.visible = on

    class NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

    backend = Backend()
    monkeypatch.setattr(overlay_module, "IS_LINUX", True)
    monkeypatch.setattr(overlay_module.threading, "Thread", NoopThread)
    monkeypatch.setattr(
        "laptop_remote.core.overlay_x11.X11LaserOverlay",
        lambda: backend,
    )

    overlay = overlay_module.LaserOverlay()
    overlay.start()
    overlay.show()
    overlay.move(100, 200)
    overlay.hide()
    overlay.set_blackout(True)

    assert overlay.available is True
    assert calls == [
        "start", "show", ("move", 100, 200), "hide", ("blackout", True),
    ]


@pytest.mark.skipif(
    sys.platform != "linux" or not os.environ.get("DISPLAY"),
    reason="requires a Linux X11 display",
)
def test_x11_overlay_uses_real_click_through_shape():
    backend = X11LaserOverlay()
    if not backend.start():
        # DISPLAY can be set but not reachable (e.g. a sandboxed shell or a
        # missing X authority). That is an environment limitation, not a bug.
        pytest.skip("X11 display is not accessible")
    try:
        assert backend.start() is True
        assert backend.available is True
        assert backend.window.shape_get_rectangles(backend._shape.SK.Input).rectangles == []

        bounding = backend.window.shape_get_rectangles(backend._shape.SK.Bounding).rectangles
        assert bounding
        assert min(rect.x for rect in bounding) == 0
        assert min(rect.y for rect in bounding) == 0
        assert max(rect.x + rect.width for rect in bounding) == 25
        assert max(rect.y + rect.height for rect in bounding) == 25
        assert max(rect.width for rect in bounding) == 25

        backend.show()
        backend._display.sync()
        assert backend.window.get_attributes().map_state == backend._xlib.IsViewable

        backend.set_blackout(True)
        backend._display.sync()
        attrs = backend.window.get_geometry()
        assert (attrs.width, attrs.height) == (
            backend._screen.width_in_pixels,
            backend._screen.height_in_pixels,
        )
        backend.set_blackout(False)
        backend._display.sync()
        assert backend.window.get_attributes().map_state == backend._xlib.IsUnmapped
    finally:
        backend.close()
