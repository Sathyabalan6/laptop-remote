"""REST endpoints for pairing, session management, and the local QR image."""

import io
import secrets

from flask import Response, jsonify, request, send_from_directory

import laptop_remote.core.auth as _auth
from ..core.auth import (
    VALID_TOKENS,
    auth_lock,
    check_and_record_failed_ip,
    clear_failed_ip,
    generate_pairing_pin,
    get_active_sessions,
    is_ip_locked,
    is_localhost,
    register_session,
    revoke_session,
)
from ..core.network import get_local_ip
from ..core.overlay import SCREEN_H, SCREEN_W
from ..core.window import detect_active_preset
from ._app import active_authorized_sids, app, overlay, socketio
from .state import build_state


def _scheme_and_port():
    scheme = 'https' if request.is_secure else 'http'
    host_parts = request.host.split(':')
    port_str = (
        f":{host_parts[1]}"
        if len(host_parts) > 1 and host_parts[1] not in ('80', '443')
        else ""
    )
    return scheme, port_str


@app.route('/')
def index():
    return send_from_directory(app.static_folder or 'static', 'index.html')


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
        'overlay_available': overlay.available,
    })


@app.route('/pair', methods=['POST'])
def pair():
    client_ip = request.remote_addr or 'unknown'
    locked, remaining = is_ip_locked(client_ip)
    if locked:
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

        # register_session acquires auth_lock itself (non-reentrant) — call outside the lock
        dev_name = data.get('device_name') or request.headers.get('User-Agent', 'Phone')[:32]
        register_session(client_token, client_ip, dev_name)

        print("\n========================================")
        print(f"✅ Successful pairing! Old PIN {old_pin} expired.")
        print(f"   New Pairing PIN (for next device): {new_pin}")
        print("========================================\n")
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

    localhost_caller = is_localhost(request.remote_addr)
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)

    if not (localhost_caller or is_auth):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    target_device_id = data.get('device_id') or data.get('token')

    if target_device_id:
        revoked = revoke_session(target_device_id)
        return jsonify({'ok': revoked, 'message': f'Device {target_device_id} revoked.' if revoked else 'Device not found'})

    with auth_lock:
        VALID_TOKENS.clear()
        _auth.PAIRED_SESSIONS.clear()
        _auth.PAIRING_PIN = generate_pairing_pin()
        new_pin = _auth.PAIRING_PIN
        sids_to_notify = list(active_authorized_sids)
        active_authorized_sids.clear()

    for sid in sids_to_notify:
        socketio.emit('state', build_state(None), to=sid)

    print("\n========================================")
    print(f"🔒 All session tokens revoked! New Pairing PIN: {new_pin}")
    print("========================================\n")
    return jsonify({'ok': True, 'message': 'All tokens revoked.'})


@app.route('/devices', methods=['GET'])
def list_devices():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]

    localhost_caller = is_localhost(request.remote_addr)
    with auth_lock:
        is_auth = bool(token and token in VALID_TOKENS)

    if not (localhost_caller or is_auth):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    return jsonify({'ok': True, 'devices': get_active_sessions()})


@app.route('/qr.png')
def qr_image():
    if not is_localhost(request.remote_addr):
        return jsonify({'ok': False, 'error': 'Forbidden: QR code image is only accessible from localhost'}), 403
    try:
        import qrcode
        ip = get_local_ip()
        scheme, port_str = _scheme_and_port()
        url = f"{scheme}://{ip}{port_str}"
        qr = qrcode.QRCode(box_size=8, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#c1c1ff', back_color='#0c0e14')
        buf = io.BytesIO()
        img.save(buf, 'PNG')
        buf.seek(0)
        return Response(buf.getvalue(), mimetype='image/png')
    except Exception:
        return jsonify({'error': 'QR generation failed'}), 500
