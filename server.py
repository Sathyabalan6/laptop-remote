import os
import sys
import time
import json
import secrets
import threading
import io
from functools import wraps

from flask import Flask, request, jsonify, send_from_directory, session, Response
from flask_socketio import SocketIO, emit
import pyautogui

# Safe console reconfigure for Windows Unicode emojis
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

try:
    from zeroconf import IPVersion, ServiceInfo, Zeroconf
    import socket
    HAS_ZEROCONF = True
except ImportError:
    HAS_ZEROCONF = False

# Import modular components from core package
from core.config import load_presets, PRESETS_PATH
import core.auth as _auth                      # import module, not variables, so PAIRING_PIN is always live
from core.auth import (
    VALID_TOKENS, auth_lock,
    generate_pairing_pin, set_pairing_pin, require_auth, socket_require_auth,
    failed_attempts_by_ip, check_and_record_failed_ip, clear_failed_ip
)
from core.network import get_local_ip
from core.power import get_battery_percent
from core.window import detect_active_preset
from core.overlay import LaserOverlay, HAS_TKINTER, SCREEN_W, SCREEN_H
from core.input import (
    InputBackend, handle_mouse_move, handle_mouse_click,
    handle_mouse_scroll, handle_text_input, handle_key, IS_WINDOWS
)


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

app = Flask(__name__, static_folder=resource_path('static'))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

overlay = LaserOverlay()
active_authorized_sids = set()

# ── State Helpers ─────────────────────────────────────────────────────────────

def build_state(token):
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)
    return {
        'authorized': is_auth,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'overlay_available': IS_WINDOWS and HAS_TKINTER and overlay.root is not None,
        'blackout': overlay.blackout if (HAS_TKINTER and overlay.root) else False,
        'battery': get_battery_percent() if is_auth else None,
        'detected_preset': detect_active_preset() if is_auth else None,
    }

# ── REST Endpoints ────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/ping', methods=['GET'])
def ping():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)
        
    detected = detect_active_preset() if is_auth else None
    return jsonify({
        'ok': True, 
        'authorized': is_auth, 
        'detected_preset': detected,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'overlay_available': IS_WINDOWS and HAS_TKINTER and overlay.root is not None
    })

@app.route('/pair', methods=['POST'])
def pair():
    client_ip = request.remote_addr or 'unknown'
    now = time.time()
    with auth_lock:
        record = failed_attempts_by_ip.get(client_ip, {'attempts': 0, 'lockout_until': 0.0})
        if now < record['lockout_until']:
            remaining = int(record['lockout_until'] - now)
            return jsonify({'ok': False, 'error': f"Too many failed attempts. Try again in {remaining} seconds."}), 429

    data = request.get_json(silent=True) or {}
    pin = data.get('pin')

    with auth_lock:
        current_pin = _auth.PAIRING_PIN

    if pin and secrets.compare_digest(str(pin).strip(), current_pin):
        clear_failed_ip(client_ip)
        with auth_lock:
            old_pin = _auth.PAIRING_PIN
            _auth.PAIRING_PIN = generate_pairing_pin()
            new_pin = _auth.PAIRING_PIN
            client_token = secrets.token_hex(24)
            VALID_TOKENS.add(client_token)

        print(f"\n========================================")
        print(f"✅ Successful pairing! Old PIN {old_pin} expired.")
        print(f"   New Pairing PIN (for next device): {new_pin}")
        print(f"========================================\n")
        return jsonify({'ok': True, 'token': client_token})
        
    allowed, lockout_secs = check_and_record_failed_ip(client_ip)
    if not allowed:
        return jsonify({'ok': False, 'error': f'Too many failed attempts. Locked out for {lockout_secs} seconds.'}), 429
        
    return jsonify({'ok': False, 'error': 'Invalid pairing PIN'}), 401

@app.route('/revoke', methods=['POST'])
def revoke():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]

    is_localhost = request.remote_addr in ('127.0.0.1', '::1')
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)

    if not (is_localhost or is_auth):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    with auth_lock:
        VALID_TOKENS.clear()
        _auth.PAIRING_PIN = generate_pairing_pin()
        new_pin = _auth.PAIRING_PIN
        sids_to_notify = list(active_authorized_sids)
        active_authorized_sids.clear()

    for sid in sids_to_notify:
        socketio.emit('state', build_state(None), to=sid)

    print(f"\n========================================")
    print(f"🔒 All session tokens revoked! New Pairing PIN: {new_pin}")
    print(f"========================================\n")
    return jsonify({'ok': True, 'message': 'All tokens revoked.'})

@app.route('/key', methods=['POST'])
@require_auth
def key():
    data = request.get_json(silent=True) or {}
    result = handle_key(data.get('action'), data.get('preset', 'universal'))
    return jsonify(result), (200 if result.get('ok') else 400)

@app.route('/text', methods=['POST'])
@require_auth
def text_input():
    data = request.get_json(silent=True) or {}
    text_content = data.get('text', '')
    press_enter = bool(data.get('press_enter', False))
    result = handle_text_input(text_content, press_enter)
    return jsonify(result), (200 if result.get('ok') else 400)

@app.route('/companion')
def companion_page():
    return send_from_directory('static', 'companion.html')

@app.route('/companion/state')
def companion_state():
    ip = get_local_ip()
    with auth_lock:
        clients_count = len(active_authorized_sids)
        pin = _auth.PAIRING_PIN
    return jsonify({
        'url': f"http://{ip}:5000",
        'mdns_url': 'http://remotedeck.local:5000',
        'pin': pin,
        'connected_clients': clients_count,
        'active_profile': detect_active_preset() or 'Universal'
    })

@app.route('/qr.png')
def qr_image():
    try:
        import qrcode
        ip = get_local_ip()
        url = f"http://{ip}:5000"
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#c1c1ff', back_color='#0c0e14')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/png')
    except Exception:
        return jsonify({'error': 'QR generation failed'}), 500

@app.route('/mouse/move', methods=['POST'])
@require_auth
def mouse_move():
    token = request.headers.get('Authorization', 'default')
    data = request.get_json(silent=True) or {}
    try:
        raw_dx = float(data.get('dx', 0.0))
        raw_dy = float(data.get('dy', 0.0))
    except (ValueError, TypeError):
        raw_dx = raw_dy = 0.0
    handle_mouse_move(token, raw_dx, raw_dy, data.get('sens', 1.0))
    return jsonify({'ok': True})

@app.route('/mouse/stop', methods=['POST'])
@require_auth
def mouse_stop():
    return jsonify({'ok': True})

@app.route('/mouse/click', methods=['POST'])
@require_auth
def mouse_click():
    data = request.get_json(silent=True) or {}
    handle_mouse_click(data.get('button', 'left'))
    return jsonify({'ok': True})

@app.route('/mouse/scroll', methods=['POST'])
@require_auth
def mouse_scroll():
    data = request.get_json(silent=True) or {}
    handle_mouse_scroll(data.get('dy', 0.0))
    return jsonify({'ok': True})

@app.route('/pointer/on', methods=['POST'])
@require_auth
def pointer_on():
    if HAS_TKINTER and overlay.root:
        overlay.show()
    return jsonify({'ok': True})

@app.route('/pointer/off', methods=['POST'])
@require_auth
def pointer_off():
    if HAS_TKINTER and overlay.root:
        overlay.hide()
    return jsonify({'ok': True})

@app.route('/pointer/move', methods=['POST'])
@require_auth
def pointer_move():
    data = request.get_json(silent=True) or {}
    try:
        x = max(0, min(SCREEN_W, float(data.get('x', 0))))
        y = max(0, min(SCREEN_H, float(data.get('y', 0))))
        if HAS_TKINTER and overlay.root:
            overlay.move(x, y)
    except (ValueError, TypeError):
        pass
    return jsonify({'ok': True})

@app.route('/screen/blackout', methods=['POST'])
@require_auth
def screen_blackout():
    data = request.get_json(silent=True) or {}
    if HAS_TKINTER and overlay.root:
        overlay.set_blackout(bool(data.get('on', False)))
    return jsonify({'ok': True})

# ── WebSocket Handlers ────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect(auth):
    token = None
    if auth:
        token = auth.get('token')
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:]
    with auth_lock:
        valid = bool(token and token in VALID_TOKENS)
        session['token'] = token if valid else None
        if session['token']:
            active_authorized_sids.add(request.sid)
    emit('state', build_state(session['token']))

@socketio.on('disconnect')
def on_disconnect():
    token = session.get('token')
    if token:
        with auth_lock:
            active_authorized_sids.discard(request.sid)

@socketio.on('mouse_move')
@socket_require_auth
def ws_mouse_move(data):
    data = data or {}
    try:
        dx = float(data.get('dx', 0.0))
        dy = float(data.get('dy', 0.0))
    except (ValueError, TypeError):
        dx = dy = 0.0
    handle_mouse_move(session['token'], dx, dy, data.get('sens', 1.0))

@socketio.on('mouse_stop')
@socket_require_auth
def ws_mouse_stop(data=None):
    pass

@socketio.on('mouse_click')
@socket_require_auth
def ws_mouse_click(data):
    handle_mouse_click((data or {}).get('button', 'left'))

@socketio.on('mouse_scroll')
@socket_require_auth
def ws_mouse_scroll(data):
    handle_mouse_scroll((data or {}).get('dy', 0.0))

@socketio.on('key')
@socket_require_auth
def ws_key(data):
    data = data or {}
    handle_key(data.get('action'), data.get('preset', 'universal'))

@socketio.on('text')
@socket_require_auth
def ws_text(data):
    data = data or {}
    handle_text_input(data.get('text', ''), bool(data.get('press_enter', False)))

@socketio.on('pointer_on')
@socket_require_auth
def ws_pointer_on():
    if HAS_TKINTER and overlay.root:
        overlay.show()

@socketio.on('pointer_off')
@socket_require_auth
def ws_pointer_off():
    if HAS_TKINTER and overlay.root:
        overlay.hide()

@socketio.on('blackout')
@socket_require_auth
def ws_blackout(data=None):
    data = data or {}
    if HAS_TKINTER and overlay.root:
        overlay.set_blackout(bool(data.get('on', False)))

@socketio.on('pointer_move')
@socket_require_auth
def ws_pointer_move(data):
    data = data or {}
    try:
        x = max(0, min(SCREEN_W, float(data.get('x', 0))))
        y = max(0, min(SCREEN_H, float(data.get('y', 0))))
        if HAS_TKINTER and overlay.root:
            overlay.move(x, y)
    except (ValueError, TypeError):
        pass

def _preset_monitor():
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

# ── Main Entry Point ──────────────────────────────────────────────────────────

def main(no_gui=False, custom_pin=None):
    """Start the Laptop Remote server.

    Args:
        no_gui: If True, skip Tkinter companion window and run terminal-only.
        custom_pin: Optional PIN/password to set at startup (overrides env var).
    """
    if custom_pin:
        set_pairing_pin(custom_pin)

    try:
        import qrcode
    except ImportError:
        qrcode = None

    ip = get_local_ip()
    url = f"http://{ip}:5000"

    print("\n" + "=" * 52)
    if no_gui:
        print("  ⚡ LAPTOP REMOTE · TERMINAL EDITION")
    else:
        print("  ⚡ LAPTOP REMOTE · SERVER ACTIVE")
    print("=" * 52)
    print(f"  🌐 Local URL     : {url}")
    print(f"  📢 mDNS Discovery : http://remotedeck.local:5000")
    print(f"  🔒 Pairing PIN   : {_auth.PAIRING_PIN}")
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

    # Start Zeroconf mDNS registration
    zeroconf_instance = None
    service_info = None
    if HAS_ZEROCONF:
        try:
            zeroconf_instance = Zeroconf()
            desc = {'version': '1.0'}
            service_info = ServiceInfo(
                "_http._tcp.local.",
                "Remote Deck._http._tcp.local.",
                addresses=[socket.inet_aton(ip)],
                port=5000,
                properties=desc,
                server="remotedeck.local."
            )
            zeroconf_instance.register_service(service_info)
            print("📢 mDNS/Zeroconf active: discoverable at http://remotedeck.local:5000/\n")
        except Exception as e:
            print(f"⚠️ Failed to start mDNS: {e}\n")

    threading.Thread(target=_preset_monitor, daemon=True).start()

    def get_companion_state():
        with auth_lock:
            clients_count = len(active_authorized_sids)
            current_pin = _auth.PAIRING_PIN
        return {
            'url': url,
            'pin': current_pin,
            'connected_count': clients_count,
            'active_profile': detect_active_preset() or 'Universal'
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

    try:
        if not no_gui and HAS_TKINTER:
            try:
                from gui import CompanionApp
                threading.Thread(target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=False), daemon=True).start()
                companion = CompanionApp(get_state_callback=get_companion_state, regenerate_pin_callback=regenerate_pin_action)
                overlay.init_with_parent(companion.root)
                companion.update_data(url, _auth.PAIRING_PIN, 0, detect_active_preset() or 'Universal')
                companion.run()
            except Exception as e:
                print(f"⚠️ GUI could not be opened ({e}), running in terminal mode.")
                overlay.start()
                socketio.run(app, host='0.0.0.0', port=5000, debug=False)
        else:
            overlay.start()
            socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        if HAS_ZEROCONF and zeroconf_instance:
            try:
                print("🧹 Unregistering mDNS Zeroconf service...")
                zeroconf_instance.unregister_service(service_info)
                zeroconf_instance.close()
            except Exception:
                pass

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Laptop Remote Server')
    parser.add_argument('--no-gui', action='store_true', help='Run in terminal-only mode (no Tkinter companion window)')
    parser.add_argument('--pin', default=None, help='Set a custom pairing PIN/password at startup')
    args, _ = parser.parse_known_args()
    main(no_gui=args.no_gui, custom_pin=args.pin)

