import contextlib
import shutil
import subprocess
import sys

IS_WINDOWS = sys.platform.startswith('win')
IS_LINUX = sys.platform.startswith('linux')
HAS_WIN32GUI = False
win32gui = None

if IS_WINDOWS:
    with contextlib.suppress(ImportError):
        import win32gui  # type: ignore
        HAS_WIN32GUI = True

PRESET_RULES = [
    ("YouTube", "youtube_hotstar"),
    ("Hotstar", "youtube_hotstar"),
    ("VLC", "vlc"),
    ("Netflix", "universal"),
    ("Prime Video", "universal"),
    ("PowerPoint", "presentation"),
    ("Keynote", "presentation"),
    ("Google Slides", "presentation"),
    ("Canva", "presentation"),
    ("Prezi", "presentation"),
]

def _get_active_window_title():
    if IS_WINDOWS and HAS_WIN32GUI and win32gui:
        with contextlib.suppress(Exception):
            hwnd = win32gui.GetForegroundWindow()
            return win32gui.GetWindowText(hwnd)
    elif IS_LINUX and shutil.which('xprop'):
        with contextlib.suppress(Exception):
            out = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stderr=subprocess.DEVNULL).decode()
            parts = out.strip().split()
            win_id = parts[-1]
            if win_id.startswith('0x'):
                name_out = subprocess.check_output(['xprop', '-id', win_id, 'WM_NAME', '_NET_WM_NAME'], stderr=subprocess.DEVNULL).decode()
                return name_out
    elif sys.platform == 'darwin' and shutil.which('osascript'):
        with contextlib.suppress(Exception):
            cmd = [
                'osascript', '-e',
                'tell application "System Events" to tell (first process whose frontmost is true) '
                'to if (count of windows) > 0 then return name & " - " & (name of window 1) else return name'
            ]
            out = subprocess.check_output(
                cmd,
                stderr=subprocess.DEVNULL,
                timeout=2.0
            ).decode('utf-8', errors='replace').strip()
            if out:
                return out
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
