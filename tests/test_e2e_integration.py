"""End-to-end integration tests for Socket.IO real-time input and HTTP routes.

Exercises the real Flask app, pairing workflow, session tokens, binary frame
unpaking, and authorization barriers using SocketIO test_client and Flask test_client.
"""

import secrets
import struct
from unittest.mock import MagicMock

import pytest

import laptop_remote.core.auth as auth_core
import laptop_remote.server.websocket as ws
from laptop_remote.server import app, socketio
from laptop_remote.server.state import build_state


@pytest.fixture(autouse=True)
def _clean_auth():
    auth_core.reset_rate_limits()
    auth_core.VALID_TOKENS.clear()
    auth_core.PAIRED_SESSIONS.clear()
    yield
    auth_core.reset_rate_limits()
    auth_core.VALID_TOKENS.clear()
    auth_core.PAIRED_SESSIONS.clear()


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestEndToEndSocketIoFlow:
    def test_e2e_pairing_and_websocket_mouse_move(self, client, monkeypatch):
        # 1. Pair via HTTP with the initial PIN
        with auth_core.auth_lock:
            current_pin = auth_core.PAIRING_PIN

        pair_resp = client.post("/pair", json={"pin": current_pin, "device_name": "Test Phone"})
        assert pair_resp.status_code == 200
        token = pair_resp.get_json()["token"]
        assert token in auth_core.VALID_TOKENS

        # 2. Mock input execution handlers
        mock_move = MagicMock()
        mock_click = MagicMock()
        mock_scroll = MagicMock()
        mock_key = MagicMock()
        monkeypatch.setattr(ws, "handle_mouse_move", mock_move)
        monkeypatch.setattr(ws, "handle_mouse_click", mock_click)
        monkeypatch.setattr(ws, "handle_mouse_scroll", mock_scroll)
        monkeypatch.setattr(ws, "handle_key", mock_key)

        # 3. Connect via Socket.IO test client using the token
        ws_client = socketio.test_client(app, auth={"token": token})
        assert ws_client.is_connected()

        # Check initial state broadcast
        received = ws_client.get_received()
        state_events = [evt for evt in received if evt["name"] == "state"]
        assert len(state_events) > 0
        state = state_events[0]["args"][0]
        assert state["authorized"] is True
        assert state["hostname"] is not None
        assert state["platform"] is not None

        # 4. Stream binary mouse move frame (dx=10.0 -> 100, dy=-5.5 -> -55, sens=1.2 -> 12)
        packed = struct.pack("<hhh", 100, -55, 12)
        ws_client.emit("mouse_move", packed)
        assert mock_move.call_count == 1
        assert mock_move.call_args[0] == (10.0, -5.5, 1.2)

        # 5. Send click and scroll
        ws_client.emit("mouse_click", {"button": "left"})
        assert mock_click.call_count == 1
        assert mock_click.call_args[0] == ("left", "click")

        ws_client.emit("mouse_scroll", {"dy": -3})
        assert mock_scroll.call_count == 1
        assert mock_scroll.call_args[0] == (-3,)

        # 6. Send key
        ws_client.emit("key", {"action": "play_pause", "preset": "universal"})
        assert mock_key.call_count == 1
        assert mock_key.call_args[0] == ("play_pause", "universal")

        ws_client.disconnect()

    def test_unauthenticated_websocket_is_blocked_from_controls(self, monkeypatch):
        mock_move = MagicMock()
        mock_click = MagicMock()
        monkeypatch.setattr(ws, "handle_mouse_move", mock_move)
        monkeypatch.setattr(ws, "handle_mouse_click", mock_click)

        # Connect with NO token
        ws_client = socketio.test_client(app)
        assert ws_client.is_connected()

        # Initial state MUST be unauthorized and redacted
        received = ws_client.get_received()
        state_events = [evt for evt in received if evt["name"] == "state"]
        assert len(state_events) > 0
        state = state_events[0]["args"][0]
        assert state["authorized"] is False
        assert state["hostname"] is None
        assert state["platform"] is None
        assert state["battery"] is None

        # Emitting controls must be ignored completely
        packed = struct.pack("<hhh", 50, 50, 10)
        ws_client.emit("mouse_move", packed)
        assert mock_move.call_count == 0

        ws_client.emit("mouse_click", {"button": "left"})
        assert mock_click.call_count == 0

        ws_client.disconnect()


class TestUnauthenticatedHttpEnforcement:
    @pytest.mark.parametrize("route,payload", [
        ("/mouse/move", {"dx": 1, "dy": 1}),
        ("/mouse/click", {"button": "left"}),
        ("/key", {"action": "play_pause"}),
        ("/volume", {"action": "up"}),
        ("/revoke", {}),
    ])
    def test_post_endpoints_require_auth(self, client, route, payload):
        resp = client.post(route, json=payload)
        assert resp.status_code == 401

    def test_devices_get_requires_auth(self, client):
        resp = client.get("/devices")
        assert resp.status_code == 401


class TestStructuralStateRedaction:
    def test_redacted_state_schema(self):
        state = build_state(token=None)
        assert state["authorized"] is False
        assert state["hostname"] is None
        assert state["platform"] is None
        assert state["battery"] is None
        assert state["detected_preset"] is None
        assert state["audio"] is None
        assert state["wayland_warning"] is False
        assert isinstance(state["screen_w"], int)
        assert isinstance(state["screen_h"], int)

    def test_explicit_redact_override(self):
        sample_key = secrets.token_hex(24)
        auth_core.VALID_TOKENS.add(sample_key)

        # Normal authenticated state
        state = build_state(token=sample_key)
        assert state["authorized"] is True
        assert state["hostname"] is not None

        # Explicitly forced redact
        redacted = build_state(token=sample_key, redact=True)
        assert redacted["hostname"] is None
        assert redacted["battery"] is None
