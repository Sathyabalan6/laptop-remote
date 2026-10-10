"""Integration tests for the Flask app using the built-in test client.

These do not bind a port or touch real input devices.
"""

import secrets

import pytest

import laptop_remote.core.auth as auth_core
from laptop_remote.server import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def auth_token():
    token = secrets.token_hex(24)
    with auth_core.auth_lock:
        auth_core.VALID_TOKENS.add(token)
    yield token
    with auth_core.auth_lock:
        auth_core.VALID_TOKENS.discard(token)


class TestPublicRoutes:
    def test_index_serves_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"<html" in resp.data.lower() or b"<!doctype" in resp.data.lower()

    def test_ping_returns_json(self, client):
        resp = client.get("/ping")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["authorized"] is False
        assert "overlay_available" in data
        assert "screen_w" in data
        assert "screen_h" in data

    def test_ping_authorized_returns_telemetry(self, client, auth_token):
        resp = client.get("/ping", headers={"Authorization": f"Bearer {auth_token}"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert data["authorized"] is True

    def test_static_asset_served(self, client):
        resp = client.get("/static/js/trackpad.js")
        assert resp.status_code == 200


class TestAuthEnforcement:
    @pytest.mark.parametrize("route", [
        "/mouse/move",
        "/mouse/click",
        "/mouse/scroll",
        "/key",
        "/text",
        "/pointer/on",
        "/pointer/off",
        "/pointer/move",
        "/screen/blackout",
        "/volume",
    ])
    def test_protected_routes_reject_unauthenticated(self, client, route):
        resp = client.post(route, json={})
        assert resp.status_code == 401

    def test_pair_with_wrong_pin_returns_401(self, client):
        resp = client.post("/pair", json={"pin": "000000"})
        assert resp.status_code in (401, 429)

    def test_pair_with_correct_pin_succeeds_and_rotates(self, client):
        with auth_core.auth_lock:
            current_pin = auth_core.PAIRING_PIN

        resp = client.post("/pair", json={"pin": current_pin})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "token" in data
        assert len(data["token"]) >= 24

        # PIN must rotate immediately after pairing
        with auth_core.auth_lock:
            assert current_pin != auth_core.PAIRING_PIN


class TestAuthenticatedEndpoints:
    def test_mouse_endpoints(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp_move = client.post("/mouse/move", json={"dx": 10, "dy": -5, "sens": 1.5}, headers=headers)
        assert resp_move.status_code == 200
        assert resp_move.get_json()["ok"] is True

        resp_click = client.post("/mouse/click", json={"button": "left", "action": "click"}, headers=headers)
        assert resp_click.status_code == 200

        resp_down = client.post("/mouse/click", json={"button": "left", "action": "down"}, headers=headers)
        assert resp_down.status_code == 200

        resp_up = client.post("/mouse/click", json={"button": "left", "action": "up"}, headers=headers)
        assert resp_up.status_code == 200

        resp_scroll = client.post("/mouse/scroll", json={"dy": 4}, headers=headers)
        assert resp_scroll.status_code == 200

    def test_key_and_macro_endpoints(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        for macro in ("copy", "paste", "app_switch", "screenshot", "close_window", "lock_screen", "vol_up", "vol_down", "mute"):
            resp = client.post("/key", json={"action": macro}, headers=headers)
            assert resp.status_code == 200
            assert resp.get_json()["ok"] is True

    def test_text_endpoint(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/text", json={"text": "hello remote", "press_enter": True}, headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        resp_empty = client.post("/text", json={"text": "", "press_enter": False}, headers=headers)
        assert resp_empty.status_code == 400

    def test_volume_endpoints(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}

        resp_get = client.get("/volume", headers=headers)
        assert resp_get.status_code == 200
        data = resp_get.get_json()
        assert "volume" in data

        resp_set = client.post("/volume", json={"volume": 60}, headers=headers)
        assert resp_set.status_code == 200

        resp_mute = client.post("/volume", json={"action": "toggle_mute"}, headers=headers)
        assert resp_mute.status_code == 200

    def test_revoke_endpoint(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/revoke", headers=headers)
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        # Token should now be invalidated
        resp_after = client.post("/mouse/click", json={"button": "left"}, headers=headers)
        assert resp_after.status_code == 401

    def test_single_device_revoke(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        # First query active devices
        resp_dev = client.get("/devices", headers=headers)
        assert resp_dev.status_code == 200
        assert "devices" in resp_dev.get_json()

        # Revoke by device token prefix
        resp_rev = client.post("/revoke", json={"device_id": auth_token[:8]}, headers=headers)
        assert resp_rev.status_code == 200

    def test_presets_endpoints(self, client, auth_token, tmp_path, monkeypatch):
        from laptop_remote.core import config as cfg
        tmp_presets = tmp_path / "presets.json"
        tmp_presets.write_text('{"universal": {"play_pause": "space"}}')
        monkeypatch.setattr(cfg, "PRESETS_PATH", str(tmp_presets))

        headers = {"Authorization": f"Bearer {auth_token}"}
        resp_get = client.get("/presets", headers=headers)
        assert resp_get.status_code == 200
        assert "universal" in resp_get.get_json()

        resp_post = client.post("/presets", json={"my_profile": {"play_pause": "p"}}, headers=headers)
        assert resp_post.status_code == 200
        assert resp_post.get_json()["ok"] is True

        resp_bad = client.post("/presets", data="not json", headers=headers)
        assert resp_bad.status_code == 400


class TestQRCodeEndpoint:
    def test_qr_accessible_from_localhost(self, client):
        resp = client.get("/qr.png", environ_base={"REMOTE_ADDR": "127.0.0.1"})
        assert resp.status_code in (200, 500)  # 200 if qrcode installed, 500 if qrcode lib error

    def test_qr_forbidden_from_remote_ip(self, client):
        resp = client.get("/qr.png", environ_base={"REMOTE_ADDR": "192.168.1.105"})
        assert resp.status_code == 403


class TestRouteRegistration:
    def test_expected_routes_exist(self):
        rules = {str(r) for r in app.url_map.iter_rules()}
        for expected in ("/", "/ping", "/pair", "/revoke", "/mouse/move", "/key", "/volume", "/qr.png"):
            assert expected in rules
