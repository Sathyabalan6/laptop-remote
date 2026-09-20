"""Unit tests for platform-independent input math (no display required)."""

import pytest

from laptop_remote.core import input as inp


class TestApplyAcceleration:
    def test_zero_delta_returns_zero(self):
        assert inp.apply_acceleration(0) == 0

    def test_positive_delta_is_positive(self):
        assert inp.apply_acceleration(5) > 0

    def test_negative_delta_is_negative(self):
        assert inp.apply_acceleration(-5) < 0

    def test_symmetric(self):
        assert pytest.approx(inp.apply_acceleration(5)) == -inp.apply_acceleration(-5)

    def test_larger_delta_moves_more(self):
        assert abs(inp.apply_acceleration(10)) > abs(inp.apply_acceleration(2))

    def test_small_delta_damped(self):
        # Below 1.0 uses the 0.8 damping factor.
        base = 10.0
        assert inp.apply_acceleration(0.5, base_speed=base, accel_power=1.35) == 0.5 * base * 0.8


class TestHandleMouseMoveBounds:
    def test_clamps_within_screen(self, monkeypatch):
        """A huge delta must not move the pointer outside screen bounds."""
        captured = {}

        def fake_move(x, y):
            captured["x"] = x
            captured["y"] = y

        monkeypatch.setattr(inp.InputBackend, "move_mouse", staticmethod(fake_move))
        monkeypatch.setattr(inp, "get_cursor_position", lambda: (960, 540))
        monkeypatch.setattr(inp, "get_screen_bounds", lambda: (0, 0, 1919, 1079))

        inp.handle_mouse_move(100000, 100000, sens=1.0)
        assert 0 <= captured["x"] <= 1919
        assert 0 <= captured["y"] <= 1079

    def test_invalid_sensitivity_defaults(self, monkeypatch):
        captured = {}
        monkeypatch.setattr(inp.InputBackend, "move_mouse", staticmethod(lambda x, y: captured.update(x=x, y=y)))
        monkeypatch.setattr(inp, "get_cursor_position", lambda: (100, 100))
        monkeypatch.setattr(inp, "get_screen_bounds", lambda: (0, 0, 1919, 1079))
        # Should not raise on garbage sensitivity.
        inp.handle_mouse_move(5, 5, sens="not-a-number")
        assert "x" in captured


class TestHandleMouseScroll:
    def test_clamps_extreme_scroll(self, monkeypatch):
        calls = []
        monkeypatch.setattr(inp, "pyautogui", type("P", (), {"scroll": staticmethod(lambda n: calls.append(n))})())
        monkeypatch.setattr(inp, "IS_WAYLAND", False)
        inp.handle_mouse_scroll(9999)
        assert calls and abs(calls[0]) <= 20


class TestYdotoolSocketPaths:
    """Regression tests for the Wayland ydotool socket resolution.

    Historical bug: the daemon creates its socket under $XDG_RUNTIME_DIR, but the
    code only checked /tmp, AND probed with SOCK_STREAM while the daemon listens
    on SOCK_DGRAM (errno 91). Both are covered here.
    """

    def test_includes_xdg_runtime_dir(self, monkeypatch):
        monkeypatch.setenv("XDG_RUNTIME_DIR", "/run/user/1234")
        monkeypatch.delenv("YDOTOOL_SOCKET", raising=False)
        paths = inp._ydotool_socket_paths()
        assert "/run/user/1234/.ydotool_socket" in paths

    def test_respects_ydotool_socket_env(self, monkeypatch):
        monkeypatch.setenv("YDOTOOL_SOCKET", "/custom/path.sock")
        paths = inp._ydotool_socket_paths()
        assert paths[0] == "/custom/path.sock"

    def test_always_includes_tmp_fallback(self, monkeypatch):
        monkeypatch.delenv("YDOTOOL_SOCKET", raising=False)
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        assert "/tmp/.ydotool_socket" in inp._ydotool_socket_paths()

    def test_detects_datagram_socket(self, monkeypatch, tmp_path):
        """The daemon uses a SOCK_DGRAM socket; probing must succeed."""
        import socket as _socket

        sock_path = str(tmp_path / ".ydotool_socket")
        server = _socket.socket(_socket.AF_UNIX, _socket.SOCK_DGRAM)
        try:
            server.bind(sock_path)
            monkeypatch.setenv("YDOTOOL_SOCKET", sock_path)
            monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
            assert inp._ydotoold_socket() == sock_path
            assert inp._ydotoold_running() is True
        finally:
            server.close()

    def test_returns_none_when_no_socket(self, monkeypatch, tmp_path):
        monkeypatch.setenv("YDOTOOL_SOCKET", str(tmp_path / "missing.sock"))
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        # Also ensure the /tmp fallback doesn't accidentally exist.
        assert inp._ydotoold_socket() in (None, "/tmp/.ydotool_socket")


class TestWaylandButtonCodes:
    """Regression tests for ydotool mouse button encoding.

    ydotool encodes buttons as a bitmask:
      low nibble  = button (0x00 left, 0x01 right, 0x02 middle)
      0x40 = down, 0x80 = up, 0xC0 = full click (down+up)
    Historical bug: we sent 0x40 (down only) so buttons were never released,
    which made clicks not register.
    """

    def _capture(self, monkeypatch):
        calls = []
        monkeypatch.setattr(inp, "WAYLAND_TOOL", "ydotool")
        monkeypatch.setattr(inp, "WAYLAND_TOOL_PATH", "/usr/bin/ydotool")
        monkeypatch.setattr(inp, "IS_WAYLAND", True)
        monkeypatch.setattr(inp, "_run_wayland_tool", lambda args, timeout=1.0: calls.append(args) or True)
        return calls

    def test_left_click_is_c0(self, monkeypatch):
        calls = self._capture(monkeypatch)
        inp.InputBackend.click_mouse("left")
        assert calls == [["click", "0xC0"]]

    def test_right_click_is_c1(self, monkeypatch):
        calls = self._capture(monkeypatch)
        inp.InputBackend.click_mouse("right")
        assert calls == [["click", "0xC1"]]

    def test_middle_click_is_c2(self, monkeypatch):
        calls = self._capture(monkeypatch)
        inp.InputBackend.click_mouse("middle")
        assert calls == [["click", "0xC2"]]

    def test_scroll_up_uses_button_4(self, monkeypatch):
        calls = self._capture(monkeypatch)
        inp.handle_mouse_scroll(2)
        assert calls == [["click", "0xC4"], ["click", "0xC4"]]

    def test_scroll_down_uses_button_5(self, monkeypatch):
        calls = self._capture(monkeypatch)
        inp.handle_mouse_scroll(-2)
        assert calls == [["click", "0xC5"], ["click", "0xC5"]]

    def test_no_click_code_is_bare_down(self, monkeypatch):
        """Every click we emit must include the 'up' bit (0xC0 mask)."""
        calls = self._capture(monkeypatch)
        for btn in ("left", "right", "middle"):
            inp.InputBackend.click_mouse(btn)
        for args in calls:
            code = int(args[1], 16)
            assert code & 0xC0 == 0xC0, f"{args} is missing down+up bits"
