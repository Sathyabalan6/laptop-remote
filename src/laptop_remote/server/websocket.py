"""Socket.IO event handlers (mouse, key, text, pointer, volume, blackout)."""

import contextlib
import struct

from flask import request, session
from flask_socketio import emit

from ..core.audio import set_volume, toggle_mute
from ..core.auth import VALID_TOKENS, auth_lock, socket_require_auth, touch_session
from ..core.input import (
    handle_key,
    handle_mouse_click,
    handle_mouse_move,
    handle_mouse_scroll,
    handle_mouse_stop,
    handle_mouse_zoom,
    handle_text_input,
)
from ..core.overlay import SCREEN_H, SCREEN_W
from ._app import active_authorized_sids, overlay, socketio
from .state import build_state


@socketio.on('connect')
def on_connect(auth):
    token = None
    if isinstance(auth, dict):
        token = auth.get('token')
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:]
    with auth_lock:
        valid = bool(token and token in VALID_TOKENS)
        session['token'] = token if valid else None
        if session['token']:
            active_authorized_sids.add(request.sid)  # type: ignore
    if session.get('token'):
        touch_session(session['token'])
    emit('state', build_state(session['token']))


@socketio.on('disconnect')
def on_disconnect():
    token = session.get('token')
    if token:
        with auth_lock:
            active_authorized_sids.discard(request.sid)  # type: ignore


@socketio.on('get_battery')
@socket_require_auth
def ws_get_battery(data=None):
    from ..core.power import get_battery_percent
    emit('battery_update', {'battery': get_battery_percent()})


@socketio.on('volume_set')
@socket_require_auth
def ws_volume_set(data):
    data = data or {}
    vol = data.get('volume', 50)
    res = set_volume(vol)
    with auth_lock:
        sids = list(active_authorized_sids)
    for sid in sids:
        socketio.emit('audio_state', res, to=sid)


@socketio.on('volume_toggle_mute')
@socket_require_auth
def ws_volume_toggle_mute(data=None):
    res = toggle_mute()
    with auth_lock:
        sids = list(active_authorized_sids)
    for sid in sids:
        socketio.emit('audio_state', res, to=sid)


@socketio.on('mouse_move')
@socket_require_auth
def ws_mouse_move(data):
    if isinstance(data, (bytes, bytearray, memoryview)) and len(data) >= 6:
        with contextlib.suppress(Exception):
            dx_raw, dy_raw, sens_raw = struct.unpack('<hhh', bytes(data[:6]))
            handle_mouse_move(dx_raw / 10.0, dy_raw / 10.0, max(0.1, sens_raw / 10.0))
            return

    payload = data if isinstance(data, dict) else {}
    try:
        dx = float(payload.get('dx', 0.0))
        dy = float(payload.get('dy', 0.0))
    except (ValueError, TypeError):
        dx = dy = 0.0
    handle_mouse_move(dx, dy, payload.get('sens', 1.0))


@socketio.on('mouse_stop')
@socket_require_auth
def ws_mouse_stop(data=None):
    handle_mouse_stop()


@socketio.on('mouse_click')
@socket_require_auth
def ws_mouse_click(data):
    data = data or {}
    handle_mouse_click(data.get('button', 'left'), data.get('action', 'click'))


@socketio.on('mouse_scroll')
@socket_require_auth
def ws_mouse_scroll(data):
    handle_mouse_scroll((data or {}).get('dy', 0.0))


@socketio.on('mouse_zoom')
@socket_require_auth
def ws_mouse_zoom(data):
    data = data or {}
    try:
        delta = float(data.get('delta', 0.0))
    except (ValueError, TypeError):
        delta = 0.0
    handle_mouse_zoom(delta)


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
def ws_pointer_on(data=None):
    if overlay.available:
        overlay.show()


@socketio.on('pointer_off')
@socket_require_auth
def ws_pointer_off(data=None):
    if overlay.available:
        overlay.hide()


@socketio.on('blackout')
@socket_require_auth
def ws_blackout(data=None):
    data = data or {}
    if overlay.available:
        overlay.set_blackout(bool(data.get('on', False)))


@socketio.on('pointer_move')
@socket_require_auth
def ws_pointer_move(data):
    if not overlay.available:
        # No transparent overlay available — don't hijack the real cursor.
        return
    data = data or {}
    try:
        x = max(0, min(SCREEN_W, float(data.get('x', 0))))
        y = max(0, min(SCREEN_H, float(data.get('y', 0))))
        overlay.move(x, y)
    except (ValueError, TypeError):
        pass
