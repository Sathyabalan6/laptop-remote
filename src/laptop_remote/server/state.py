import platform
import socket

from ..core.audio import get_volume
from ..core.auth import VALID_TOKENS, auth_lock
from ..core.device import get_device_display_name
from ..core.overlay import SCREEN_H, SCREEN_W
from ..core.power import get_battery_percent
from ..core.window import detect_active_preset
from ._app import overlay


def build_state(token):
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)
    return {
        'authorized': is_auth,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'hostname': socket.gethostname() if is_auth else None,
        'device_name': get_device_display_name() if is_auth else None,
        'platform': platform.system() if is_auth else None,
        'overlay_available': overlay.available,
        'blackout': overlay.blackout and overlay.available,
        'battery': get_battery_percent() if is_auth else None,
        'detected_preset': detect_active_preset() if is_auth else None,
        'audio': get_volume() if is_auth else None,
    }
