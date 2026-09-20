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
