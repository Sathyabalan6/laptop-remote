"""Unit tests for pairing PIN generation and IP rate limiting."""

import secrets
import time

import pytest

from laptop_remote.core import auth


class TestPinGeneration:
    def test_pin_is_six_digits(self):
        pin = auth.generate_pairing_pin()
        assert pin.isdigit()
        assert len(pin) == 6

    def test_pin_range(self):
        for _ in range(200):
            pin = int(auth.generate_pairing_pin())
            assert 100000 <= pin <= 999999

    def test_pins_are_random(self):
        pins = {auth.generate_pairing_pin() for _ in range(50)}
        # Astronomically unlikely to collide 50 times into < 45 values.
        assert len(pins) > 45


class TestSetPairingPin:
    def test_set_and_restore(self):
        original = auth.PAIRING_PIN
        try:
            auth.set_pairing_pin("987654")
            assert auth.PAIRING_PIN == "987654"
        finally:
            auth.set_pairing_pin(original)


class TestIsLocalhost:
    @pytest.mark.parametrize("addr", ["127.0.0.1", "::1", "localhost", "testclient"])
    def test_localhost_addresses(self, addr):
        assert auth.is_localhost(addr) is True

    @pytest.mark.parametrize("addr", ["192.168.1.5", "10.0.0.1", "", None])
    def test_non_localhost_addresses(self, addr):
        assert auth.is_localhost(addr) is False


class TestIpRateLimiting:
    def setup_method(self):
        auth.reset_rate_limits()

    def teardown_method(self):
        auth.reset_rate_limits()

    def test_initial_ip_is_not_locked(self):
        locked, remaining = auth.is_ip_locked("203.0.113.1")
        assert locked is False
        assert remaining == 0

    def test_lockout_after_five_failures(self):
        ip = "203.0.113.77"
        auth.clear_failed_ip(ip)
        for _ in range(4):
            allowed, _ = auth.check_and_record_failed_ip(ip)
            assert allowed is True
        # Fifth failure triggers lockout.
        allowed, lockout = auth.check_and_record_failed_ip(ip)
        assert allowed is False
        assert lockout > 0

        locked, remaining = auth.is_ip_locked(ip)
        assert locked is True
        assert remaining > 0

    def test_clear_failed_ip_resets(self):
        ip = "203.0.113.88"
        for _ in range(5):
            auth.check_and_record_failed_ip(ip)
        assert auth.is_ip_locked(ip)[0] is True
        auth.clear_failed_ip(ip)
        assert auth.is_ip_locked(ip)[0] is False

    def test_global_distributed_lockout_triggers_across_different_ips(self):
        """Simulate an attacker rotating through multiple IPs to brute-force the PIN."""
        for i in range(14):
            ip = f"10.0.1.{i}"
            allowed, _ = auth.check_and_record_failed_ip(ip)
            assert allowed is True

        # 15th failed attempt globally triggers LAN-wide lockout
        ip_15 = "10.0.1.99"
        allowed, lockout_secs = auth.check_and_record_failed_ip(ip_15)
        assert allowed is False
        assert lockout_secs > 0

        # Any other fresh IP is now globally locked out
        fresh_ip = "192.168.1.200"
        is_locked, remaining = auth.is_ip_locked(fresh_ip)
        assert is_locked is True
        assert remaining > 0

        # Loopback is excluded from global network lockout so host owner can still connect
        localhost_locked, _ = auth.is_ip_locked("127.0.0.1")
        assert localhost_locked is False


class TestMultiDeviceSessions:
    def test_register_and_get_sessions(self):
        sample_token = secrets.token_hex(16)
        auth.register_session(sample_token, "192.168.1.50", "Pixel 8")
        sessions = auth.get_active_sessions()
        assert any(s["id"] == sample_token[:8] and s["device_name"] == "Pixel 8" for s in sessions)
        assert sample_token in auth.VALID_TOKENS

    def test_touch_session(self):
        sample_token = secrets.token_hex(16)
        auth.register_session(sample_token, "192.168.1.51", "iPhone 15")
        auth.PAIRED_SESSIONS[sample_token]["last_seen"] = time.time() - 100.0
        past_time = auth.PAIRED_SESSIONS[sample_token]["last_seen"]
        auth.touch_session(sample_token)
        assert auth.PAIRED_SESSIONS[sample_token]["last_seen"] > past_time

    def test_revoke_session_by_id(self):
        sample_token = secrets.token_hex(16)
        auth.register_session(sample_token, "192.168.1.52", "iPad")
        assert sample_token in auth.VALID_TOKENS
        assert auth.revoke_session(sample_token[:8]) is True
        assert sample_token not in auth.VALID_TOKENS
        assert not any(s["id"] == sample_token[:8] for s in auth.get_active_sessions())

    def test_revoke_nonexistent_returns_false(self):
        assert auth.revoke_session("nonexistent_id_999") is False

    def test_reentrant_lock_safety(self):
        """Verify that holding auth_lock and calling functions that also acquire auth_lock does not deadlock."""
        with auth.auth_lock:
            sample_token = secrets.token_hex(16)
            auth.register_session(sample_token, "127.0.0.1", "Reentrant Test")
            sessions = auth.get_active_sessions()
            assert any(s["id"] == sample_token[:8] for s in sessions)
            auth.touch_session(sample_token)
            assert auth.revoke_session(sample_token) is True

    def test_session_persistence_roundtrip(self, tmp_path, monkeypatch):
        test_file = str(tmp_path / "sessions.json")
        monkeypatch.setattr(auth, "_get_sessions_file_path", lambda: test_file)

        sample_token = secrets.token_hex(16)
        auth.register_session(sample_token, "192.168.1.150", "Persisted Phone")

        # Clear in-memory state
        auth.VALID_TOKENS.clear()
        auth.PAIRED_SESSIONS.clear()
        assert sample_token not in auth.VALID_TOKENS

        # Load from disk
        auth._load_persisted_sessions()
        assert sample_token in auth.VALID_TOKENS
        assert sample_token in auth.PAIRED_SESSIONS
        assert auth.PAIRED_SESSIONS[sample_token]["device_name"] == "Persisted Phone"

        # Revoke all purges the file
        auth.revoke_all_sessions()
        assert sample_token not in auth.VALID_TOKENS
        assert len(auth.PAIRED_SESSIONS) == 0

    def test_session_persistence_file_permissions(self, tmp_path, monkeypatch):
        import os
        import stat
        import sys

        test_file = str(tmp_path / "sessions.json")
        monkeypatch.setattr(auth, "_get_sessions_file_path", lambda: test_file)

        sample_token = secrets.token_hex(16)
        auth.register_session(sample_token, "192.168.1.150", "Secure Phone")

        # Check permissions on POSIX systems (0600)
        if not sys.platform.startswith("win"):
            mode = stat.S_IMODE(os.stat(test_file).st_mode)
            assert mode == 0o600


class TestCorsOriginValidator:
    def test_cors_origin_allowed(self):
        from laptop_remote.server._app import is_cors_origin_allowed

        # None / empty (native clients, PWA, same-origin)
        assert is_cors_origin_allowed(None) is True
        assert is_cors_origin_allowed("") is True

        # Loopback
        assert is_cors_origin_allowed("http://localhost:5000") is True
        assert is_cors_origin_allowed("http://127.0.0.1:5000") is True
        assert is_cors_origin_allowed("https://127.0.0.1") is True

        # mDNS
        assert is_cors_origin_allowed("http://remotedeck.local:5000") is True
        assert is_cors_origin_allowed("https://remotedeck.local") is True

        # Private LAN IPs
        assert is_cors_origin_allowed("http://192.168.1.42:5000") is True
        assert is_cors_origin_allowed("http://10.0.0.15:5000") is True
        assert is_cors_origin_allowed("http://172.20.10.2:5000") is True

        # External / Malicious origins blocked
        assert is_cors_origin_allowed("https://evil.com") is False
        assert is_cors_origin_allowed("http://attacker.org:5000") is False
        assert is_cors_origin_allowed("https://google.com") is False

