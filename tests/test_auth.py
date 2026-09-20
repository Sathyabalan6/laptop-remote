"""Unit tests for pairing PIN generation and IP rate limiting."""

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
