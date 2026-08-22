import sys
import time
import pyautogui
from .config import load_presets

IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')

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

if not USE_NATIVE_MOUSE:
    def _move_mouse(x, y):
        pyautogui.moveTo(x, y, duration=0)
    def _click_mouse(button='left'):
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
    SCREEN_W, SCREEN_H = pyautogui.size()
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

if IS_WINDOWS and USE_NATIVE_MOUSE:
    def get_cursor_position():
        try:
            return win32api.GetCursorPos()
        except Exception:
            return pyautogui.position()
else:
    def get_cursor_position():
        return pyautogui.position()

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

def handle_mouse_move(token, dx, dy, sens=1.0):
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

def handle_mouse_click(button='left'):
    InputBackend.click_mouse(button)

def handle_mouse_scroll(dy):
    try:
        dy = float(dy)
    except (ValueError, TypeError):
        dy = 0.0
    dy = max(-20, min(20, dy))
    pyautogui.scroll(int(round(dy)))

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
    if not text:
        if press_enter:
            pyautogui.press('enter')
            return {'ok': True}
        return {'ok': False, 'error': 'No text provided'}
    try:
        try:
            import pyperclip
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
        except Exception:
            pyautogui.write(text, interval=0.005)
        
        if press_enter:
            time.sleep(0.05)
            pyautogui.press('enter')
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def handle_key(action, preset='universal'):
    if not action:
        return {'ok': False, 'error': 'No action provided'}

    audio_actions = {
        'mute':     lambda: pyautogui.press('volumemute'),
        'vol_up':   lambda: pyautogui.press('volumeup'),
        'vol_down': lambda: pyautogui.press('volumedown'),
    }
    if action in audio_actions:
        audio_actions[action]()
        return {'ok': True}

    presentation_actions = {
        'next_slide': lambda: pyautogui.press('right'),
        'prev_slide': lambda: pyautogui.press('left'),
        'present_start': lambda: InputBackend.send_keys(presentation_start_key()),
        'present_exit': lambda: pyautogui.press('esc'),
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
        try:
            pyautogui.press(action)
            return {'ok': True}
        except Exception:
            pass

    return {'ok': False, 'error': f"Key map missing for action '{action}' in preset '{preset}'"}
