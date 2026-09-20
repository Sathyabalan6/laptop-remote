"""Network discovery (mDNS/Zeroconf) and active-preset change monitor."""

import time

try:
    from zeroconf import ServiceInfo, Zeroconf
    import socket as _socket
    HAS_ZEROCONF = True
except ImportError:
    HAS_ZEROCONF = False

from ..core.auth import auth_lock
from ..core.window import detect_active_preset

from ._app import socketio, active_authorized_sids


def register_mdns(ip, port, ssl_enabled, mdns_url):
    """Register the mDNS/Zeroconf service. Returns (instance, service_info)."""
    if not HAS_ZEROCONF:
        return None, None
    try:
        zeroconf_instance = Zeroconf()
        desc = {'version': '1.0'}
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
    try:
        print("🧹 Unregistering mDNS Zeroconf service...")
        zeroconf_instance.unregister_service(service_info)
        zeroconf_instance.close()
    except Exception:
        pass


def preset_monitor():
    """Poll the active-window preset and broadcast changes to authorized clients."""
    last_preset = None
    while True:
        time.sleep(2.0)
        with auth_lock:
            authorized_sids = list(active_authorized_sids)
        if not authorized_sids:
            continue
        try:
            p = detect_active_preset()
            if p and p != last_preset:
                last_preset = p
                for sid in authorized_sids:
                    socketio.emit('preset_changed', {'preset': p}, to=sid)
        except Exception as e:
            print(f"preset monitor: {e}")
