"""Server entry point: ``main()`` plus the standalone CLI argument parser."""

import sys
import threading

import laptop_remote.core.auth as _auth
from ..core.auth import (
    VALID_TOKENS, auth_lock, generate_pairing_pin, set_pairing_pin,
)
from ..core.network import get_local_ip, setup_ssl_context
from ..core.window import detect_active_preset

from ._app import app, socketio, overlay, active_authorized_sids
from . import discovery


def main(custom_pin=None, ssl_enabled=False, ssl_cert=None,
         ssl_key=None, port=5000, tray_enabled=False):
    """Start the Laptop Remote server (terminal/headless).

    Args:
        custom_pin: Optional PIN/password to set at startup (overrides env var).
        ssl_enabled: If True, enable HTTPS/TLS encryption.
        ssl_cert: Optional path to SSL certificate file.
        ssl_key: Optional path to SSL private key file.
        port: Port to bind (default: 5000).
        tray_enabled: If True, enable an optional system tray icon.
    """
    if custom_pin:
        set_pairing_pin(custom_pin)

    try:
        import qrcode
    except ImportError:
        qrcode = None

    ssl_context = None
    scheme = "http"
    if ssl_enabled:
        ssl_context = setup_ssl_context(ssl_cert, ssl_key)
        scheme = "https"

    ip = get_local_ip()
    port_str = f":{port}" if port not in (80, 443) else ""
    url = f"{scheme}://{ip}{port_str}"
    mdns_url = f"{scheme}://remotedeck.local{port_str}"

    print("\n" + "=" * 52)
    print("  ⚡ LAPTOP REMOTE · TERMINAL EDITION")
    print("=" * 52)
    print(f"  🌐 Local URL      : {url}")
    print(f"  📢 mDNS Discovery : {mdns_url}")
    print(f"  🔒 Pairing PIN    : {_auth.PAIRING_PIN}")
    if ssl_enabled:
        print(f"  🛡️  Transport      : Encrypted (HTTPS / WSS)")
    else:
        print(f"  ⚠️  Transport      : Plaintext HTTP (use --ssl for HTTPS)")
    print("=" * 52 + "\n")

    if qrcode:
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
            print("\n  👉 Scan the QR code above with your phone to connect!\n")
        except Exception:
            pass

    # Start mDNS registration and the preset-change monitor.
    zeroconf_instance, service_info = discovery.register_mdns(ip, port, ssl_enabled, mdns_url)
    threading.Thread(target=discovery.preset_monitor, daemon=True).start()

    def get_companion_state():
        with auth_lock:
            clients_count = len(active_authorized_sids)
            current_pin = _auth.PAIRING_PIN
        return {
            'url': url,
            'pin': current_pin,
            'connected_count': clients_count,
            'active_profile': detect_active_preset() or 'Universal',
        }

    def regenerate_pin_action():
        with auth_lock:
            VALID_TOKENS.clear()
            _auth.PAIRING_PIN = generate_pairing_pin()
            new_pin = _auth.PAIRING_PIN
            sids_to_notify = list(active_authorized_sids)
            active_authorized_sids.clear()
        for sid in sids_to_notify:
            socketio.emit('revoke', {'message': 'Tokens revoked'}, to=sid)
        return new_pin

    if tray_enabled or '--tray' in sys.argv:
        try:
            from ..core.tray import SystemTrayManager, HAS_PYSTRAY
            if HAS_PYSTRAY:
                tray = SystemTrayManager(
                    get_state_cb=get_companion_state,
                    regenerate_pin_cb=regenerate_pin_action,
                    revoke_cb=lambda: VALID_TOKENS.clear(),
                    quit_cb=lambda: sys.exit(0),
                )
                tray.start()
        except Exception as e:
            print(f"⚠️ System tray icon could not be launched: {e}")

    run_kwargs = {
        'host': '0.0.0.0',
        'port': port,
        'debug': False,
        # Flask-SocketIO 5.x warns about the Werkzeug dev server being used in
        # production. For a LAN-only tool this is fine; we explicitly opt in.
        'allow_unsafe_werkzeug': True,
    }
    if ssl_context:
        run_kwargs['ssl_context'] = ssl_context

    try:
        overlay.start()
        socketio.run(app, **run_kwargs)
    finally:
        discovery.unregister_mdns(zeroconf_instance, service_info)
