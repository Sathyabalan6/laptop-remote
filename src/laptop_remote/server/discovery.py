"""Network discovery (mDNS/Zeroconf) and active-preset change monitor."""

import contextlib
import socket as _socket
import time
from typing import Any

from .. import __version__
from ..core.auth import auth_lock
from ..core.power import get_battery_percent
from ..core.window import detect_active_preset
from ._app import active_authorized_sids, socketio

ServiceInfo: Any = None
Zeroconf: Any = None
HAS_ZEROCONF = False

try:
    from zeroconf import ServiceInfo, Zeroconf
    HAS_ZEROCONF = True
except ImportError:
    pass


def register_mdns(ip, port, ssl_enabled, mdns_url):
    """Register the mDNS/Zeroconf service. Returns (instance, service_info)."""
    if not HAS_ZEROCONF:
        return None, None
    try:
        zeroconf_instance = Zeroconf()
        desc = {'version': __version__}
        service_type = "_https._tcp.local." if ssl_enabled else "_http._tcp.local."
        service_info = ServiceInfo(
            service_type,
            f"Remote Deck.{service_type}",
            addresses=[_socket.inet_aton(ip)],
            port=port,
            properties=desc,
            server="remotedeck.local.",
        )
        zeroconf_instance.register_service(service_info)
        print(f"📢 mDNS/Zeroconf active: discoverable at {mdns_url}/\n")
        return zeroconf_instance, service_info
    except Exception as e:
        print(f"⚠️ Failed to start mDNS: {e}\n")
        return None, None


def unregister_mdns(zeroconf_instance, service_info):
    if not (HAS_ZEROCONF and zeroconf_instance):
        return
    with contextlib.suppress(Exception):
        print("🧹 Unregistering mDNS Zeroconf service...")
        zeroconf_instance.unregister_service(service_info)
        zeroconf_instance.close()


_cached_preset = None
_cached_preset_time = 0.0


def get_cached_preset(max_age: float = 4.0):
    """Return the cached active preset, refreshing only if stale."""
    global _cached_preset, _cached_preset_time
    now = time.time()
    if _cached_preset is not None and (now - _cached_preset_time) < max_age:
        return _cached_preset
    try:
        p = detect_active_preset()
        _cached_preset = p
        _cached_preset_time = now
        return p
    except Exception:
        return _cached_preset


def preset_monitor():
    """Poll the active-window preset and battery status, broadcasting changes to authorized clients."""
    global _cached_preset, _cached_preset_time
    last_preset = None
    last_battery = None
    battery_poll_counter = 0

    while True:
        time.sleep(2.0)
        with auth_lock:
            authorized_sids = list(active_authorized_sids)
        if not authorized_sids:
            continue
        try:
            p = detect_active_preset()
            _cached_preset = p
            _cached_preset_time = time.time()
            if p and p != last_preset:
                last_preset = p
                for sid in authorized_sids:
                    socketio.emit('preset_changed', {'preset': p}, to=sid)
        except Exception as e:
            print(f"preset monitor: {e}")

        # Check battery status every 4 seconds (every 2 cycles)
        battery_poll_counter += 1
        if battery_poll_counter >= 2:
            battery_poll_counter = 0
            try:
                b = get_battery_percent()
                if b != last_battery:
                    last_battery = b
                    for sid in authorized_sids:
                        socketio.emit('battery_update', {'battery': b}, to=sid)
            except Exception as e:
                print(f"battery monitor: {e}")
