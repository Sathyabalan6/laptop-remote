"""Flask application construction and shared runtime state.

This module owns the Flask ``app`` and ``socketio`` instances plus the
process-global runtime objects (laser overlay, authorized session ids) that
the REST routes, WebSocket handlers, and discovery subsystem all share.

It intentionally does NOT import ``routes`` / ``websocket`` here; those modules
import ``app``/``socketio`` from this module and register themselves, keeping
the dependency direction one-way.
"""

import io
import os
import re
import secrets
import sys
import threading
import time
from functools import wraps
from urllib.parse import urlparse

from flask import Flask
from flask_socketio import SocketIO

from ..core import _tkinter_guard  # noqa: F401

try:
    import pyautogui
    if pyautogui:
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0
except (Exception, SystemExit):
    pyautogui = None

# Safe console reconfigure for Windows Unicode emojis
stdout_reconfig = getattr(sys.stdout, 'reconfigure', None)
if callable(stdout_reconfig):
    stdout_reconfig(errors='replace')
stderr_reconfig = getattr(sys.stderr, 'reconfigure', None)
if callable(stderr_reconfig):
    stderr_reconfig(errors='replace')


def resource_path(relative):
    """Resolve a packaged resource path (works in source and frozen builds).

    Static assets live next to this module (``laptop_remote/static``) in both
    source and PyInstaller builds, so we anchor on ``__file__``.
    """
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


# Static assets live at ``laptop_remote/static`` — one level up from ``server/``.
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_cors_origin_allowed(origin):
    """Validate CORS origins for Socket.IO connections.

    Permits same-origin / native client requests (origin is None or empty),
    loopback addresses (localhost, 127.0.0.1, ::1), mDNS domains
    (remotedeck.local), and private RFC 1918 local area network IP ranges.
    Rejects foreign web domains (e.g. evil.com).
    """
    if not origin:
        return True
    try:
        parsed = urlparse(origin)
        host = (parsed.hostname or '').lower()
        if host in ('localhost', '127.0.0.1', '::1', 'remotedeck.local'):
            return True
        # Allow private LAN IPv4 ranges (192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12)
        if re.match(r'^(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)$', host):
            return True
    except Exception:
        return False
    return False


app = Flask(__name__, static_folder=os.path.join(_PACKAGE_ROOT, 'static'))
app.secret_key = secrets.token_hex(32)
socketio = SocketIO(app, cors_allowed_origins=is_cors_origin_allowed, async_mode='threading')  # type: ignore

# Import the overlay after app/socketio so it can be shared everywhere.
from ..core.overlay import LaserOverlay  # noqa: E402

overlay = LaserOverlay()
active_authorized_sids = set()
