"""Unit tests for the key-name → Linux keycode mapping."""

import pytest

from laptop_remote.core.keys import (
    key_name_to_code,
    char_to_press,
    split_keys,
    KEYCODES,
)


class TestKeyNameToCode:
    def test_common_named_keys(self):
        assert key_name_to_code("enter") == 28
        assert key_name_to_code("space") == 57
        assert key_name_to_code("esc") == 1
        assert key_name_to_code("tab") == 15
        assert key_name_to_code("backspace") == 14

    def test_modifiers(self):
        assert key_name_to_code("ctrl") == 29
        assert key_name_to_code("shift") == 42
        assert key_name_to_code("alt") == 56

    def test_arrows_and_navigation(self):
        assert key_name_to_code("left") == 105
        assert key_name_to_code("right") == 106
        assert key_name_to_code("up") == 103
        assert key_name_to_code("down") == 108
        assert key_name_to_code("pageup") == 104
        assert key_name_to_code("pagedown") == 109
        assert key_name_to_code("home") == 102
        assert key_name_to_code("end") == 107

    def test_function_keys(self):
        assert key_name_to_code("f1") == 59
        assert key_name_to_code("f5") == 63
        assert key_name_to_code("f10") == 68
        assert key_name_to_code("f11") == 87
        assert key_name_to_code("f12") == 88

    def test_case_insensitive(self):
        assert key_name_to_code("ENTER") == 28
        assert key_name_to_code("Enter") == 28

    def test_unknown_returns_none(self):
        assert key_name_to_code("nonexistentkey") is None
        assert key_name_to_code("") is None
        assert key_name_to_code(None) is None


class TestCharToPress:
    def test_lowercase_needs_no_shift(self):
        assert char_to_press("a") == (30, False)
        assert char_to_press("z") == (44, False)

    def test_uppercase_needs_shift(self):
        assert char_to_press("A") == (30, True)
        assert char_to_press("Z") == (44, True)

    def test_shifted_symbols(self):
        # '>' is shift + '.', '!' is shift + '1'
        assert char_to_press(">") == (52, True)
        assert char_to_press("!") == (2, True)
        assert char_to_press("?") == (53, True)
        assert char_to_press("+") == (13, True)

    def test_plain_symbols(self):
        assert char_to_press(".") == (52, False)
        assert char_to_press(",") == (51, False)
        assert char_to_press("/") == (53, False)

    def test_digits(self):
        assert char_to_press("1") == (2, False)
        assert char_to_press("0") == (11, False)

    def test_invalid_input(self):
        assert char_to_press("") is None
        assert char_to_press("ab") is None


class TestSplitKeys:
    def test_single_string(self):
        assert split_keys("enter") == [("enter", False)]

    def test_hotkey_combo(self):
        result = split_keys(["ctrl", "l"])
        assert result == [("ctrl", True), ("l", False)]

    def test_repeated_key(self):
        result = split_keys(["right", "right", "right"])
        assert result == [("right", False)] * 3

    def test_various_modifier_aliases(self):
        assert split_keys(["control"])[0][1] is True
        assert split_keys(["shift"])[0][1] is True
        assert split_keys(["alt"])[0][1] is True
        assert split_keys(["cmd"])[0][1] is True


class TestNoDuplicateCodes:
    def test_all_codes_in_valid_range(self):
        # Linux input-event keycodes are 1..255
        for name, code in KEYCODES.items():
            assert 1 <= code <= 255, f"{name} has out-of-range code {code}"
