"""REST endpoints for mouse, keyboard, text, pointer, and volume control."""

from flask import request, jsonify

from ..core.auth import require_auth, auth_lock
from ..core.audio import get_volume, set_volume, toggle_mute
from ..core.overlay import HAS_TKINTER, SCREEN_W, SCREEN_H
from ..core.input import (
    InputBackend, handle_mouse_move, handle_mouse_click,
    handle_mouse_scroll, handle_text_input, handle_key,
)

from ._app import app, socketio, overlay, active_authorized_sids


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


@app.route('/mouse/move', methods=['POST'])
@require_auth
def mouse_move():
    data = request.get_json(silent=True) or {}
    try:
        raw_dx = float(data.get('dx', 0.0))
        raw_dy = float(data.get('dy', 0.0))
    except (ValueError, TypeError):
        raw_dx = raw_dy = 0.0
    handle_mouse_move(raw_dx, raw_dy, data.get('sens', 1.0))
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
        else:
            InputBackend.move_mouse(x, y)
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


@app.route('/volume', methods=['GET', 'POST'])
@require_auth
def volume_api():
    if request.method == 'GET':
        return jsonify(get_volume())
    data = request.get_json(silent=True) or {}
    if 'mute' in data or data.get('action') == 'toggle_mute':
        res = toggle_mute()
    elif 'volume' in data:
        res = set_volume(data.get('volume'))
    else:
        res = get_volume()

    with auth_lock:
        sids = list(active_authorized_sids)
    for sid in sids:
        socketio.emit('audio_state', res, to=sid)

    return jsonify(res)
