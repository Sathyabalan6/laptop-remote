"""Key-name to Linux input-event keycode mapping.

pyautogui uses symbolic key names (e.g. 'ctrl', 'enter', 'pageup'), while the
Wayland input tools (ydotool/dotool) speak raw Linux input-event keycodes from
<linux/input-event-codes.h> (e.g. KEY_LEFTCTRL=29, KEY_ENTER=28).

This module provides the canonical mapping plus helpers to build a tool command
for a single key press or a modifier+key hotkey.
"""

# Linux input-event keycodes (subset relevant to this app).
# Source: /usr/include/linux/input-event-codes.h
KEYCODES = {
    'esc': 1,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9,
    '9': 10, '0': 11,
    'minus': 12, '-': 12, 'equal': 13, '=': 13,
    'backspace': 14,
    'tab': 15,
    'q': 16, 'w': 17, 'e': 18, 'r': 19, 't': 20, 'y': 21, 'u': 22, 'i': 23,
    'o': 24, 'p': 25,
    '[': 26, ']': 27,
    'enter': 28, '\n': 28, '\r': 28,
    'leftctrl': 29, 'ctrl': 29, 'control': 29,
    'a': 30, 's': 31, 'd': 32, 'f': 33, 'g': 34, 'h': 35, 'j': 36, 'k': 37,
    'l': 38, ';': 39, "'": 40,
    '`': 41,
    'leftshift': 42, 'shift': 42,
    '\\': 43,
    'z': 44, 'x': 45, 'c': 46, 'v': 47, 'b': 48, 'n': 49, 'm': 50,
    ',': 51, '.': 52, '/': 53,
    'rightshift': 54,
    'kp*': 55,
    'leftalt': 56, 'alt': 56,
    'space': 57, ' ': 57,
    'capslock': 58,
    'f1': 59, 'f2': 60, 'f3': 61, 'f4': 62, 'f5': 63, 'f6': 64, 'f7': 65,
    'f8': 66, 'f9': 67, 'f10': 68, 'f11': 87, 'f12': 88,
    'rightctrl': 97,
    'rightalt': 100,
    'home': 102,
    'up': 103, 'arrowup': 103,
    'pageup': 104, 'prior': 104,
    'left': 105, 'arrowleft': 105,
    'right': 106, 'arrowright': 106,
    'end': 107,
    'down': 108, 'arrowdown': 108,
    'pagedown': 109, 'next': 109,
    'insert': 110,
    'delete': 111, 'del': 111,
}

# Shift variants of printable keys, keyed by the character that results.
# ydotool injects the base keycode; combining with KEY_LEFTSHIFT yields the symbol.
SHIFT_CHARS = {
    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5', '^': '6', '&': '7',
    '*': '8', '(': '9', ')': '0',
    '_': '-', '+': '=',
    '{': '[', '}': ']', '|': '\\',
    ':': ';', '"': "'",
    '~': '`',
    '<': ',', '>': '.', '?': '/',
    'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e', 'F': 'f', 'G': 'g',
    'H': 'h', 'I': 'i', 'J': 'j', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n',
    'O': 'o', 'P': 'p', 'Q': 'q', 'R': 'r', 'S': 's', 'T': 't', 'U': 'u',
    'V': 'v', 'W': 'w', 'X': 'x', 'Y': 'y', 'Z': 'z',
}


def key_name_to_code(name):
    """Return the Linux keycode for a pyautogui-style key name, or None."""
    if not name:
        return None
    name = str(name).lower()
    return KEYCODES.get(name)


def char_to_press(char):
    """Return (keycode, needs_shift) for a single printable character.

    Returns None if the character cannot be mapped.
    """
    if len(char) != 1:
        return None
    # Uppercase letters need shift.
    if char.isupper() and char.isalpha():
        return KEYCODES[char.lower()], True
    low = char.lower()
    if low in KEYCODES:
        return KEYCODES[low], False
    if char in SHIFT_CHARS:
        base = SHIFT_CHARS[char]
        return KEYCODES[base], True
    return None


def split_keys(keys):
    """Normalize a key spec (str or list) into `[(key, is_modifier), ...]`.

    Modifiers are 'ctrl', 'alt', 'shift', 'super'/'win'/'cmd'. Returns a list of
    (key_name_lower, is_modifier) tuples.
    """
    if isinstance(keys, str):
        keys = [keys]
    mods = {'ctrl', 'control', 'alt', 'shift', 'super', 'win', 'cmd', 'leftctrl',
            'rightctrl', 'leftalt', 'rightalt', 'leftshift', 'rightshift'}
    out = []
    for k in keys:
        lk = str(k).lower()
        out.append((lk, lk in mods))
    return out
