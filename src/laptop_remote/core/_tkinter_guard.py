"""Minimal Tkinter stub to prevent headless crashes when python3-tk is absent.

PyAutoGUI's internal sub-dependencies (pymsgbox, mouseinfo) unconditionally
attempt to `import tkinter` on startup. On Linux systems without `python3-tk`
installed, this raises an uncaught exception that calls sys.exit(1), killing
the entire headless/terminal server at import time.

This module injects a minimal mock tkinter module before importing pyautogui.
"""

import importlib.util
import sys
import types

__all__ = ['mock_tk']

if 'tkinter' not in sys.modules and importlib.util.find_spec('tkinter') is None:
    mock_tk = types.ModuleType('tkinter')
    mock_tk.TkVersion = 8.6  # type: ignore
    mock_tk.TclVersion = 8.6  # type: ignore
    mock_tk.ttk = types.ModuleType('ttk')  # type: ignore
    mock_tk.Event = object  # type: ignore
    sys.modules['tkinter'] = mock_tk
    sys.modules['tkinter.ttk'] = mock_tk.ttk
else:
    mock_tk = sys.modules.get('tkinter')
