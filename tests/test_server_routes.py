"""Integration tests for the Flask app using the built-in test client.

These do not bind a port or touch real input devices.
"""

import pytest

from laptop_remote.server import app


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


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
    ])
    def test_protected_routes_reject_unauthenticated(self, client, route):
        resp = client.post(route, json={})
        assert resp.status_code == 401

    def test_pair_with_wrong_pin_returns_401(self, client):
        resp = client.post("/pair", json={"pin": "000000"})
        assert resp.status_code in (401, 429)


class TestRouteRegistration:
    def test_expected_routes_exist(self):
        rules = {str(r) for r in app.url_map.iter_rules()}
        for expected in ("/", "/ping", "/pair", "/revoke", "/mouse/move", "/key", "/volume"):
            assert expected in rules
