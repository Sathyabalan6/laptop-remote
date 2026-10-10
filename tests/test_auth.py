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

