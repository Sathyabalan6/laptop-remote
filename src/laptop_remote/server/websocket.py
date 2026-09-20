"""Socket.IO event handlers (mouse, key, text, pointer, volume, blackout)."""

from flask import request, session
from flask_socketio import emit

from ..core.auth import VALID_TOKENS, auth_lock, socket_require_auth
from ..core.audio import set_volume, toggle_mute
from ..core.overlay import SCREEN_W, SCREEN_H
from ..core.input import (
    handle_mouse_move, handle_mouse_click,
    handle_mouse_scroll, handle_text_input, handle_key,
)

from ._app import socketio, overlay, active_authorized_sids
from .state import build_state


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
    data = data or {}
    try:
        dx = float(data.get('dx', 0.0))
        dy = float(data.get('dy', 0.0))
    except (ValueError, TypeError):
        dx = dy = 0.0
    handle_mouse_move(dx, dy, data.get('sens', 1.0))


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
