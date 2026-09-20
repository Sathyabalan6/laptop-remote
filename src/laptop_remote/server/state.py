"""Shared state helpers used by the REST and WebSocket layers."""

from ..core.auth import VALID_TOKENS, auth_lock
from ..core.power import get_battery_percent
from ..core.window import detect_active_preset
from ..core.audio import get_volume
from ..core.overlay import HAS_TKINTER, SCREEN_W, SCREEN_H

from ._app import overlay


def build_state(token):
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)
    return {
        'authorized': is_auth,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'overlay_available': overlay.available,
        'blackout': overlay.blackout if (HAS_TKINTER and overlay.root) else False,
        'battery': get_battery_percent() if is_auth else None,
        'detected_preset': detect_active_preset() if is_auth else None,
        'audio': get_volume() if is_auth else None,
    }
