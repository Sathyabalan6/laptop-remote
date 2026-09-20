import sys
import shutil
import subprocess

IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
HAS_WIN32GUI = False

if IS_WINDOWS:
    try:
        import win32gui
        HAS_WIN32GUI = True
    except ImportError:
        pass

PRESET_RULES = [
    ("YouTube", "youtube_hotstar"),
    ("Hotstar", "youtube_hotstar"),
    ("VLC", "vlc"),
    ("Netflix", "universal"),
    ("Prime Video", "universal"),
]

def _get_active_window_title():
    if IS_WINDOWS and HAS_WIN32GUI:
        try:
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
        except Exception:
            return None
    elif IS_LINUX and shutil.which('xprop'):
        try:
            out = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stderr=subprocess.DEVNULL).decode()
            parts = out.strip().split()
            win_id = parts[-1]
            if win_id.startswith('0x'):
                name_out = subprocess.check_output(['xprop', '-id', win_id, 'WM_NAME', '_NET_WM_NAME'], stderr=subprocess.DEVNULL).decode()
                return name_out
        except Exception:
            pass
    return None

def detect_active_preset():
    title = _get_active_window_title()
    if not title:
        return None
    title_lower = title.lower()
    for keyword, preset in PRESET_RULES:
        if keyword.lower() in title_lower:
            return preset
    return None
