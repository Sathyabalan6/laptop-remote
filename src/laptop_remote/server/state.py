import platform
import socket

from ..core.audio import get_volume
from ..core.auth import VALID_TOKENS, auth_lock
from ..core.device import get_device_display_name
from ..core.input import is_wayland_missing_daemon
from ..core.overlay import SCREEN_H, SCREEN_W
from ..core.power import get_battery_percent
from ._app import overlay
from .discovery import get_cached_preset


def build_state(token=None, redact=None):
    """Build the client state dictionary.

    If `token` is unauthenticated (or `redact=True`), sensitive telemetry
    (hostname, platform, battery, volume, active preset) is structurally redacted.
    """
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)

    should_redact = (not is_auth) if redact is None else redact

    # Baseline telemetry safe to send during initial PIN handshake
    state = {
        'authorized': is_auth,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'overlay_available': overlay.available,
        'blackout': bool(overlay.blackout and overlay.available),
        'hostname': None,
        'device_name': None,
        'platform': None,
        'battery': None,
        'detected_preset': None,
        'audio': None,
        'wayland_warning': False,
    }

    # Populate sensitive telemetry only for authenticated clients
    if not should_redact:
        state.update({
            'hostname': socket.gethostname(),
            'device_name': get_device_display_name(),
            'platform': platform.system(),
            'battery': get_battery_percent(),
            'detected_preset': get_cached_preset(),
            'audio': get_volume(),
            'wayland_warning': is_wayland_missing_daemon(),
        })

    return state
