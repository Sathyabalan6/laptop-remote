import sys
import os
import time
import shutil
import subprocess

# Prevent mouseinfo/pymsgbox sys.exit when python3-tk is not installed on Linux
if 'tkinter' not in sys.modules:
    try:
        import tkinter
    except ImportError:
        import types
        mock_tk = types.ModuleType('tkinter')
        mock_tk.TkVersion = 8.6
        mock_tk.TclVersion = 8.6
        mock_tk.ttk = types.ModuleType('ttk')
        mock_tk.Event = object
        sys.modules['tkinter'] = mock_tk
        sys.modules['tkinter.ttk'] = mock_tk.ttk

try:
    import pyautogui
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False
    pyautogui.MINIMUM_DURATION = 0
    pyautogui.MINIMUM_SLEEP = 0
except (Exception, SystemExit):
    pyautogui = None
from .config import load_presets
from .keys import key_name_to_code, char_to_press, split_keys

IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')

# ── Wayland detection ────────────────────────────────────────────────────────
# On Linux under a Wayland compositor, pyautogui's XTEST-based mouse injection
# talks to an Xwayland server and never reaches the real on-screen cursor.
# We detect this and use a Wayland-native virtual input tool instead.
IS_WAYLAND = (
    sys.platform.startswith('linux')
    and bool(os.environ.get('WAYLAND_DISPLAY'))
    and os.environ.get('XDG_SESSION_TYPE', '').lower() != 'x11'
)

# Locate a Wayland-native input CLI (ydotool / dotool).
def _find_wayland_tool():
    for name in ('ydotool', 'dotool'):
        path = shutil.which(name)
        if path:
            return name, path
    return None, None

WAYLAND_TOOL, WAYLAND_TOOL_PATH = _find_wayland_tool()


def _ydotoold_running():
    """Check whether the ydotool daemon is reachable (socket)."""
    socket_path = '/tmp/.ydotool_socket'
    try:
        import socket as _socket
        s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
        s.settimeout(0.3)
        s.connect(socket_path)
        s.close()
        return True
    except Exception:
        return False


def _ensure_wayland_daemon():
    """Try to start the ydotool daemon if the binary exists but isn't running.

    When the user is a member of the `input` group, ydotoold can run without
    root privileges. Returns True if a daemon is (now) available.
    """
    if WAYLAND_TOOL != 'ydotool':
        return False
    if _ydotoold_running():
        return True
    daemon = shutil.which('ydotoold')
    if not daemon:
        return False
    try:
        subprocess.Popen(
            [daemon],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        # Give it a moment to create its socket.
        for _ in range(10):
            time.sleep(0.1)
            if _ydotoold_running():
                return True
    except Exception:
        pass
    return False

USE_NATIVE_MOUSE = False
HAS_WIN32GUI = False

if IS_WINDOWS:
    try:
        import win32api, win32con
        try:
            import win32gui
            HAS_WIN32GUI = True
        except ImportError:
            pass
        def _move_mouse(x, y):
            win32api.SetCursorPos((int(x), int(y)))
        def _click_mouse(button='left'):
            if button == 'left':
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                time.sleep(0.04)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                time.sleep(0.04)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        USE_NATIVE_MOUSE = True
    except ImportError:
        pass

elif IS_MAC:
    try:
        from Quartz.CoreGraphics import CGEventCreateMouseEvent, CGEventPost, kCGEventMouseMoved, kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, kCGEventRightMouseUp, kCGMouseButtonLeft, kCGMouseButtonRight, kCGHIDEventTap
        def _move_mouse(x, y):
            event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, event)
        def _click_mouse(button='left'):
            x, y = pyautogui.position()
            if button == 'left':
                down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), kCGMouseButtonLeft)
                up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), kCGMouseButtonLeft)
            else:
                down = CGEventCreateMouseEvent(None, kCGEventRightMouseDown, (x, y), kCGMouseButtonRight)
                up = CGEventCreateMouseEvent(None, kCGEventRightMouseUp, (x, y), kCGMouseButtonRight)
            CGEventPost(kCGHIDEventTap, down)
            time.sleep(0.04)
            CGEventPost(kCGHIDEventTap, up)
        USE_NATIVE_MOUSE = True
    except ImportError:
        pass

def _run_wayland_tool(args, timeout=1.0):
    """Run the detected Wayland input tool. Returns True on success."""
    if not WAYLAND_TOOL_PATH:
        return False
    try:
        subprocess.run(
            [WAYLAND_TOOL_PATH] + args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
        return True
    except Exception:
        return False


def _wayland_key_code(code, down=True):
    """Press (down=True) or release (down=False) a single Linux keycode."""
    state = '1' if down else '0'
    if WAYLAND_TOOL == 'dotool':
        # dotool: 'keydown <keycode>' / 'keyup <keycode>'
        return _run_wayland_tool(['keydown' if down else 'keyup', str(code)])
    # ydotool: 'key <code>:<state>'
    return _run_wayland_tool(['key', f'{code}:{state}'])


def _wayland_press_key_code(code):
    """Tap a key (press + release) by Linux keycode."""
    _wayland_key_code(code, True)
    _wayland_key_code(code, False)


def _wayland_press_name(name):
    """Tap a named key (e.g. 'enter', 'f5') via the Wayland tool."""
    code = key_name_to_code(name)
    if code is not None:
        _wayland_press_key_code(code)
        return True
    return False


def _wayland_type_text(text):
    """Type raw text via the Wayland tool.

    Prefers ydotool's native 'type' subcommand (handles arbitrary UTF-8);
    falls back to per-character keycode injection for dotool.
    """
    if not text:
        return True
    if WAYLAND_TOOL == 'ydotool':
        return _run_wayland_tool(['type', '--', text], timeout=5.0)
    # dotool has no higher-level 'type'; inject char by char.
    ok = True
    for ch in text:
        m = char_to_press(ch)
        if m is None:
            # Non-mappable character (e.g. unicode emoji) — skip rather than crash.
            continue
        code, needs_shift = m
        if needs_shift:
            ok = ok and _wayland_key_code(key_name_to_code('shift'), True)
        ok = ok and _wayland_press_key_code(code)
        if needs_shift:
            ok = ok and _wayland_key_code(key_name_to_code('shift'), False)
    return ok


def _wayland_hotkey(modifiers, key):
    """Press a modifier+key combo via the Wayland tool.

    modifiers: list of modifier key names; key: the main key name.
    """
    mod_codes = []
    for m in modifiers:
        c = key_name_to_code(m)
        if c is not None:
            mod_codes.append(c)
    key_code = key_name_to_code(key)
    if key_code is None:
        return False

    for c in mod_codes:
        _wayland_key_code(c, True)
    _wayland_press_key_code(key_code)
    for c in reversed(mod_codes):
        _wayland_key_code(c, False)
    return True


def _wayland_send_keys(keys):
    """Route a key spec (single name or list) through the Wayland tool."""
    items = split_keys(keys)
    if not items:
        return

    # Repeated single key (e.g. ['right','right','right'] => 3 presses).
    if len(items) == 1:
        name = items[0][0]
        if key_name_to_code(name) is not None:
            _wayland_press_name(name)
            return
        # Single unknown key: try to type it as a raw character.
        _wayland_type_text(name)
        return

    if all(x == items[0] for x in items):
        # Same key repeated (e.g. ['l','l','l']).
        code = key_name_to_code(items[0][0])
        if code is not None:
            for _ in items:
                _wayland_press_key_code(code)
                time.sleep(0.05)
            return

    # Modifier + key hotkey (e.g. ['ctrl','l']).
    mods = [k for k, is_mod in items if is_mod]
    non_mods = [k for k, is_mod in items if not is_mod]
    if mods and len(non_mods) == 1:
        if _wayland_hotkey(mods, non_mods[0]):
            return

    # Fallback: press each key sequentially.
    for name, _ in items:
        if key_name_to_code(name) is not None:
            _wayland_press_name(name)
        else:
            _wayland_type_text(name)

if IS_WAYLAND:
    # Wayland-native path: use ydotool/dotool which injects via uinput and
    # works with any Wayland compositor (unlike pyautogui's XTEST backend).
    def _move_mouse(x, y):
        if WAYLAND_TOOL == 'dotool':
            ok = _run_wayland_tool(['mouseto', str(int(x)), str(int(y))])
        else:  # ydotool
            ok = _run_wayland_tool(['mousemove', '--absolute', str(int(x)), str(int(y))])
        if not ok and pyautogui:
            # Fallback (Xorg session or Xwayland-only apps)
            pyautogui.moveTo(x, y, duration=0)

    def _click_mouse(button='left'):
        btn = {'left': 'left', 'right': 'right', 'middle': 'middle'}.get(button, 'left')
        if WAYLAND_TOOL == 'dotool':
            ok = _run_wayland_tool(['click', btn])
        else:  # ydotool
            ok = _run_wayland_tool(['click', {'left': '0x40', 'middle': '0x41', 'right': '0x42'}.get(btn, '0x40')])
        if not ok and pyautogui:
            pyautogui.click(button=button)

    # On Wayland we still treat pyautogui as available for keyboard/scroll
    # (scroll/keyboard have the same XTEST limitation, so prefer the tool too).
    USE_NATIVE_MOUSE = True

elif not USE_NATIVE_MOUSE:
    def _move_mouse(x, y):
        if pyautogui:
            pyautogui.moveTo(x, y, duration=0)
    def _click_mouse(button='left'):
        if pyautogui:
            pyautogui.click(button=button)

class InputBackend:
    @staticmethod
    def move_mouse(x, y):
        _move_mouse(x, y)

    @staticmethod
    def click_mouse(button='left'):
        _click_mouse(button)

    @staticmethod
    def send_keys(keys):
        """Send a key, a hotkey combo, or repeat a key.

        Accepts either a single key name string, or a list of key names.
        A list where every element is the same key is treated as repeated
        presses; otherwise it is treated as a modifier+key hotkey.
        """
        if IS_WAYLAND and WAYLAND_TOOL_PATH:
            _wayland_send_keys(keys)
            return
        if not pyautogui:
            return
        try:
            if isinstance(keys, list):
                if len(keys) > 0 and all(x == keys[0] for x in keys):
                    for k in keys:
                        pyautogui.press(k)
                        time.sleep(0.05)
                else:
                    pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys)
        except Exception as e:
            print(f"Error simulating keys {keys}: {e}")

try:
    if pyautogui:
        SCREEN_W, SCREEN_H = pyautogui.size()
    else:
        SCREEN_W, SCREEN_H = 1920, 1080
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

# ── Startup diagnostics ───────────────────────────────────────────────────────
if IS_WAYLAND:
    if WAYLAND_TOOL_PATH:
        if WAYLAND_TOOL == 'ydotool' and not _ydotoold_running() and not _ensure_wayland_daemon():
            print("═" * 60)
            print("⚠️  ydotool found, but its daemon (ydotoold) is not running.")
            print("   Mouse control will NOT work until it is started.")
            print("   Run once:  sudo usermod -aG input $USER   (then log out/in)")
            print("   Then:       ydotoold &")
            print("═" * 60)
    else:
        print("═" * 60)
        print("⚠️  Wayland detected, but no native input tool found.")
        print("   Mouse move/click/scroll AND keyboard/text input will NOT work.")
        print("   Install one of these and restart the app:")
        print("     • sudo apt install ydotool   (then: sudo usermod -aG input $USER; re-login)")
        print("     • or the dotool daemon (see https://git.sr.ht/~geb/dotool)")
        print("   Alternatively, log into an 'Xorg' session to keep using pyautogui.")
        print("═" * 60)

import threading
INPUT_LOCK = threading.Lock()
_last_cursor_pos = (SCREEN_W // 2, SCREEN_H // 2)

if IS_WINDOWS and USE_NATIVE_MOUSE:
    def get_cursor_position():
        global _last_cursor_pos
        try:
            _last_cursor_pos = win32api.GetCursorPos()
            return _last_cursor_pos
        except Exception:
            try:
                if pyautogui:
                    _last_cursor_pos = pyautogui.position()
            except Exception:
                pass
            return _last_cursor_pos
elif IS_WAYLAND:
    # Under Wayland, pyautogui.position() reads from Xwayland and returns a
    # stale value; the real compositor cursor position is not queryable via
    # Xlib. Track the cursor in software from our own absolute moves instead.
    def get_cursor_position():
        return _last_cursor_pos
else:
    def get_cursor_position():
        global _last_cursor_pos
        try:
            if pyautogui:
                _last_cursor_pos = pyautogui.position()
        except Exception:
            pass
        return _last_cursor_pos

RESOLUTION_SCALE = max(1.0, SCREEN_W / 1920.0)
BASE_SPEED   = 3.2 * RESOLUTION_SCALE
ACCEL_POWER  = 1.35

def apply_acceleration(delta, base_speed=BASE_SPEED, accel_power=ACCEL_POWER):
    sign = 1 if delta >= 0 else -1
    ad = abs(delta)
    if ad < 1.0:
        return delta * base_speed * 0.8
    if ad < 3.0:
        return delta * base_speed
    return sign * (ad ** accel_power) * base_speed

def get_screen_bounds():
    if IS_WINDOWS and USE_NATIVE_MOUSE:
        try:
            min_x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            min_y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            max_x = min_x + win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN) - 1
            max_y = min_y + win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN) - 1
            return min_x, min_y, max_x, max_y
        except Exception:
            pass
    return 0, 0, SCREEN_W - 1, SCREEN_H - 1

def handle_mouse_move(dx, dy, sens=1.0):
    global _last_cursor_pos
    with INPUT_LOCK:
        try:
            sens = max(0.1, min(5.0, float(sens)))
        except (ValueError, TypeError):
            sens = 1.0

        base_speed = BASE_SPEED * sens
        accel_power = max(1.0, min(1.8, ACCEL_POWER + 0.1 * (sens - 1.0)))

        adx = apply_acceleration(dx, base_speed, accel_power)
        ady = apply_acceleration(dy, base_speed, accel_power)

        x, y = get_cursor_position()
        min_x, min_y, max_x, max_y = get_screen_bounds()
        nx = max(min_x, min(max_x, int(round(x + adx))))
        ny = max(min_y, min(max_y, int(round(y + ady))))
        InputBackend.move_mouse(nx, ny)
        _last_cursor_pos = (nx, ny)


def handle_mouse_click(button='left'):
    InputBackend.click_mouse(button)


def handle_mouse_scroll(dy):
    try:
        dy = float(dy)
    except (ValueError, TypeError):
        dy = 0.0
    dy = max(-20, min(20, dy))
    clicks = int(round(dy))
    if clicks == 0:
        return
    if IS_WAYLAND and WAYLAND_TOOL_PATH:
        # ydotool/dotool scroll via button 4/5 (or 'scroll' for dotool)
        if WAYLAND_TOOL == 'dotool':
            _run_wayland_tool(['scroll', str(clicks)])
        else:
            # ydotool: positive = up (button 4), negative = down (button 5)
            for _ in range(abs(clicks)):
                _run_wayland_tool(['click', '0x40' if clicks > 0 else '0x41'])
        return
    if pyautogui:
        pyautogui.scroll(clicks)

def presentation_start_key():
    if IS_WINDOWS and HAS_WIN32GUI:
        try:
            import win32gui
            title = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lower()
            if any(k in title for k in ('slides', 'canva', 'prezi', 'docs.google')):
                return ['ctrl', 'f5']
        except Exception:
            pass
    return ['f5']

def handle_text_input(text, press_enter=False):
    with INPUT_LOCK:
        if not text:
            if press_enter:
                if IS_WAYLAND and WAYLAND_TOOL_PATH:
                    _wayland_press_name('enter')
                elif pyautogui:
                    pyautogui.press('enter')
                return {'ok': True}
            return {'ok': False, 'error': 'No text provided'}
        try:
            if IS_WAYLAND and WAYLAND_TOOL_PATH:
                _wayland_type_text(text)
                if press_enter:
                    _wayland_press_name('enter')
                return {'ok': True}

            typed = False
            try:
                import pyperclip
                pyperclip.copy(text)
                if pyautogui:
                    pyautogui.hotkey('ctrl', 'v')
                    typed = True
            except Exception:
                pass

            if not typed and pyautogui:
                pyautogui.write(text, interval=0)
            
            if press_enter and pyautogui:
                pyautogui.press('enter')
            return {'ok': True}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

def handle_key(action, preset='universal'):
    def press(key):
        """Press a single named key through the active backend."""
        if IS_WAYLAND and WAYLAND_TOOL_PATH:
            _wayland_press_name(key)
        elif pyautogui:
            pyautogui.press(key)

    with INPUT_LOCK:
        if not action:
            return {'ok': False, 'error': 'No action provided'}

    if action in ('mute', 'vol_up', 'vol_down'):
        from .audio import get_volume, set_volume, toggle_mute
        if action == 'mute':
            toggle_mute()
        elif action == 'vol_up':
            curr = get_volume()
            set_volume(min(100, curr['volume'] + 5))
        elif action == 'vol_down':
            curr = get_volume()
            set_volume(max(0, curr['volume'] - 5))
        return {'ok': True}

    presentation_actions = {
        'next_slide': lambda: press('right'),
        'prev_slide': lambda: press('left'),
        'present_start': lambda: InputBackend.send_keys(presentation_start_key()),
        'present_exit': lambda: press('esc'),
    }
    if action in presentation_actions:
        presentation_actions[action]()
        return {'ok': True}

    direct_keys = {
        'enter': 'enter',
        'backspace': 'backspace',
        'escape': 'esc',
        'esc': 'esc',
        'tab': 'tab',
        'shift_tab': ['shift', 'tab'],
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'pageup': 'pageup',
        'pagedown': 'pagedown',
        'home': 'home',
        'end': 'end',
        'space': 'space',
        'search_url': ['ctrl', 'l'],
        'search_focus': '/',
        'browser_tab_next': ['ctrl', 'tab'],
        'browser_tab_prev': ['ctrl', 'shift', 'tab'],
        'browser_reload': 'f5',
    }
    if action in direct_keys:
        InputBackend.send_keys(direct_keys[action])
        return {'ok': True}

    presets_map = load_presets()
    preset_config = presets_map.get(preset, presets_map.get('universal', {}))
    keys = preset_config.get(action)
    if keys:
        InputBackend.send_keys(keys)
        return {'ok': True}

    if len(action) == 1 or action.isalnum():
        press(action)
        return {'ok': True}

    return {'ok': False, 'error': f"Key map missing for action '{action}' in preset '{preset}'"}
