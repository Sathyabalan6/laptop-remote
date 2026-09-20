"""Laptop Remote server package.

This package assembles the Flask application, Socket.IO server, REST routes,
WebSocket handlers, network discovery, and the ``main()`` entry point.

Public API (consumed by ``laptop_remote.cli`` and PyInstaller specs):
    app, socketio, overlay, active_authorized_sids, build_state, main
"""

from ._app import app, socketio, overlay, active_authorized_sids
from .state import build_state
from .main import main

# Import route/websocket modules so their decorators register with app/socketio.
from . import routes_auth as _routes_auth  # noqa: E402,F401
from . import routes_input as _routes_input  # noqa: E402,F401
from . import websocket as _websocket  # noqa: E402,F401

__all__ = [
    "app", "socketio", "overlay", "active_authorized_sids",
    "build_state", "main",
]
