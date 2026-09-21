"""X11 laser and blackout windows backed by the X SHAPE extension."""

import math
import os
import threading

DOT_DIAMETER = 25
DOT_RADIUS = DOT_DIAMETER // 2


def _circle_rectangles(radius=DOT_RADIUS):
    """Return horizontal strips that form a pixel-aligned circular shape."""
    rectangles = []
    for y in range(radius * 2 + 1):
        dy = y - radius
        half_width = int(math.sqrt(radius * radius - dy * dy))
        rectangles.append((radius - half_width, y, half_width * 2 + 1, 1))
    return rectangles


class X11LaserOverlay:
    """Manage an input-transparent laser/blackout window on an X11 display."""

    def __init__(self, display_factory=None, xlib=None, shape_api=None):
        self._display_factory = display_factory
        self._xlib = xlib
        self._shape = shape_api
        self._display = None
        self._screen = None
        self.window = None
        self.available = False
        self.visible = False
        self.blackout = False
        self._pointer_x = -DOT_DIAMETER
        self._pointer_y = -DOT_DIAMETER
        self._lock = threading.RLock()

    def _load_xlib(self):
        if self._display_factory is not None:
            return
        from Xlib import X, display
        from Xlib.ext import shape
        self._xlib = X
        self._display_factory = display.Display
        self._shape = shape

    def start(self):
        if not os.environ.get("DISPLAY"):
            return False

        try:
            self._load_xlib()
            self._display = self._display_factory()
            if not self._display.has_extension("SHAPE"):
                raise RuntimeError("X11 server does not provide the SHAPE extension")

            version = self._display.shape_query_version()
            if (version.major_version, version.minor_version) < (1, 1):
                raise RuntimeError("X11 SHAPE 1.1 is required for click-through input")

            self._screen = self._display.screen()
            red_pixel = self._screen.default_colormap.alloc_named_color("red").pixel
            x = self._xlib
            self.window = self._screen.root.create_window(
                0, 0, DOT_DIAMETER, DOT_DIAMETER, 0,
                self._screen.root_depth, x.InputOutput, x.CopyFromParent,
                background_pixel=red_pixel,
                override_redirect=1,
                save_under=1,
            )
            self._set_dot_shape()
            self._set_empty_input_shape()
            self._display.sync()
            self.available = True
            return True
        except Exception:  # noqa: BLE001 - initialization failures must leave the pointer unavailable
            self.close()
            return False

    def _set_dot_shape(self):
        self.window.shape_rectangles(
            self._shape.SO.Set, self._shape.SK.Bounding,
            self._xlib.Unsorted, 0, 0, _circle_rectangles(),
        )

    def _set_empty_input_shape(self):
        self.window.shape_rectangles(
            self._shape.SO.Set, self._shape.SK.Input,
            self._xlib.Unsorted, 0, 0, [],
        )

    def show(self):
        with self._lock:
            if not self.available or self.blackout:
                return
            self.window.configure(stack_mode=self._xlib.Above)
            self.window.map()
            self._display.flush()
            self.visible = True

    def hide(self):
        with self._lock:
            if not self.available or self.blackout:
                return
            self.window.unmap()
            self._display.flush()
            self.visible = False

    def move(self, x, y):
        with self._lock:
            if not self.available or self.blackout:
                return
            self.window.configure(
                x=round(x - DOT_RADIUS),
                y=round(y - DOT_RADIUS),
                stack_mode=self._xlib.Above,
            )
            self._pointer_x = round(x - DOT_RADIUS)
            self._pointer_y = round(y - DOT_RADIUS)
            self._display.flush()

    def set_blackout(self, on):
        with self._lock:
            if not self.available:
                return
            on = bool(on)
            if on == self.blackout:
                return

            x = self._xlib
            if on:
                self.window.change_attributes(
                    background_pixel=self._screen.black_pixel,
                )
                self.window.configure(
                    x=0, y=0,
                    width=self._screen.width_in_pixels,
                    height=self._screen.height_in_pixels,
                    stack_mode=x.Above,
                )
                self.window.shape_rectangles(
                    self._shape.SO.Set, self._shape.SK.Bounding,
                    x.Unsorted, 0, 0,
                    [(0, 0,
                        self._screen.width_in_pixels,
                        self._screen.height_in_pixels)],
                )
                self.window.clear_area(
                    0, 0,
                    self._screen.width_in_pixels,
                    self._screen.height_in_pixels,
                )
                self.window.map()
            else:
                self.window.unmap()
                self.window.change_attributes(
                    background_pixel=self._screen.default_colormap.alloc_named_color("red").pixel,
                )
                self.window.configure(
                    x=self._pointer_x,
                    y=self._pointer_y,
                    width=DOT_DIAMETER,
                    height=DOT_DIAMETER,
                )
                self._set_dot_shape()

            self._display.flush()
            self.blackout = on
            self.visible = on

    def close(self):
        with self._lock:
            self.available = False
            self.visible = False
            self.blackout = False
            try:
                if self.window:
                    self.window.destroy()
            except Exception:  # noqa: BLE001, S110 - cleanup should continue if the X server disconnected
                pass
            self.window = None
            try:
                if self._display:
                    self._display.close()
            except Exception:  # noqa: BLE001, S110 - cleanup should continue if the X server disconnected
                pass
            self._display = None
