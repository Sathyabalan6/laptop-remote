"""Unit tests for WebSocket event handlers and binary frame decoding."""

import struct
from unittest.mock import MagicMock

from laptop_remote.server import websocket


class TestWsMouseMove:
    def test_binary_frame_unpacks_and_calls_handle_mouse_move(self, monkeypatch):
        mock_move = MagicMock()
        monkeypatch.setattr(websocket, "handle_mouse_move", mock_move)

        # dx=15.0 -> 150, dy=-20.5 -> -205, sens=1.8 -> 18
        packed = struct.pack("<hhh", 150, -205, 18)
        handler = getattr(websocket.ws_mouse_move, "__wrapped__", websocket.ws_mouse_move)
        handler(packed)

        mock_move.assert_called_once_with(15.0, -20.5, 1.8)

    def test_dict_payload_fallback(self, monkeypatch):
        mock_move = MagicMock()
        monkeypatch.setattr(websocket, "handle_mouse_move", mock_move)

        handler = getattr(websocket.ws_mouse_move, "__wrapped__", websocket.ws_mouse_move)
        handler({"dx": 4.5, "dy": -3.2, "sens": 1.2})

        mock_move.assert_called_once_with(4.5, -3.2, 1.2)

    def test_corrupt_payload_handled_safely(self, monkeypatch):
        mock_move = MagicMock()
        monkeypatch.setattr(websocket, "handle_mouse_move", mock_move)

        handler = getattr(websocket.ws_mouse_move, "__wrapped__", websocket.ws_mouse_move)
        handler(b"bad")
        # Length < 6 falls back to dict parsing with default 0.0, 0.0, 1.0
        mock_move.assert_called_once_with(0.0, 0.0, 1.0)


class TestWsMouseScrollAndStop:
    def test_ws_mouse_scroll_invokes_handle_mouse_scroll(self, monkeypatch):
        mock_scroll = MagicMock()
        monkeypatch.setattr(websocket, "handle_mouse_scroll", mock_scroll)

        handler = getattr(websocket.ws_mouse_scroll, "__wrapped__", websocket.ws_mouse_scroll)
        handler({"dy": 2.5})
        mock_scroll.assert_called_once_with(2.5)

    def test_ws_mouse_stop_invokes_handle_mouse_stop(self, monkeypatch):
        mock_stop = MagicMock()
        monkeypatch.setattr(websocket, "handle_mouse_stop", mock_stop)

        handler = getattr(websocket.ws_mouse_stop, "__wrapped__", websocket.ws_mouse_stop)
        handler()
        mock_stop.assert_called_once()
