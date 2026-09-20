"""Flask application construction and shared runtime state.

This module owns the Flask ``app`` and ``socketio`` instances plus the
process-global runtime objects (laser overlay, authorized session ids) that
the REST routes, WebSocket handlers, and discovery subsystem all share.

It intentionally does NOT import ``routes`` / ``websocket`` here; those modules
import ``app``/``socketio`` from this module and register themselves, keeping
the dependency direction one-way.
"""

import os
import sys
import time
import secrets
import threading
import io
from functools import wraps

from flask import Flask
from flask_socketio import SocketIO

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
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
except (Exception, SystemExit):
    pyautogui = None

# Safe console reconfigure for Windows Unicode emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')


def resource_path(relative):
    """Resolve a packaged resource path (works in source and frozen builds).

    Static assets live next to this module (``laptop_remote/static``) in both
    source and PyInstaller builds, so we anchor on ``__file__``.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


# Static assets live at ``laptop_remote/static`` — one level up from ``server/``.
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=os.path.join(_PACKAGE_ROOT, 'static'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Import the overlay after app/socketio so it can be shared everywhere.
from ..core.overlay import LaserOverlay  # noqa: E402

overlay = LaserOverlay()
active_authorized_sids = set()
