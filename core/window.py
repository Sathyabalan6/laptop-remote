import sys

IS_WINDOWS = sys.platform.startswith('win')
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

def detect_active_preset():
    if not IS_WINDOWS or not HAS_WIN32GUI:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        for keyword, preset in PRESET_RULES:
            if keyword.lower() in title.lower():
                return preset
    except Exception:
        pass
    return None
