from flask import Flask, request, jsonify, send_from_directory, session
from flask_socketio import SocketIO, emit
import pyautogui
import time
import os
import sys
import json
import secrets
import random
import socket
import ctypes
import threading
from functools import wraps

# Console output is full of emoji (✅, 📢, 🔒…); on Windows a redirected or
# legacy-codepage stdout can't encode them and would crash on startup.
# Never let a print() kill the server: fall back to '?' where needed.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(errors='replace')

try:
    from zeroconf import IPVersion, ServiceInfo, Zeroconf
    HAS_ZEROCONF = True
except ImportError:
    HAS_ZEROCONF = False

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0

# ── Security & Authentication ────────────────────────────────────────────────
PAIRING_PIN = str(random.randint(100000, 999999))
VALID_TOKENS = set()  # Set of unique active session tokens

# Mouse velocity state per client session to prevent stomping in multi-client environments
client_velocities = {}

def get_client_velocity(token):
    if token not in client_velocities:
        client_velocities[token] = [0.0, 0.0]
    return client_velocities[token]

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow token in header or JSON payload
        token = request.headers.get('Authorization') or (request.get_json(silent=True) or {}).get('token')
        if token and token.startswith('Bearer '):
            token = token[7:]
        if not token or token not in VALID_TOKENS:
            return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ── Dynamic Config-driven Presets ───────────────────────────────────────────
def get_executable_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

PRESETS_PATH = os.path.join(get_executable_dir(), 'presets.json')

DEFAULT_PRESETS = {
  "youtube_hotstar": {
    "play_pause": "space",
    "skip_forward": "l",
    "skip_back": "j",
    "skip_forward_30": ["l", "l", "l"],
    "next": ["shift", "n"],
    "fullscreen": "f",
    "subtitles": "c",
    "back": ["alt", "left"]
  },
  "universal": {
    "play_pause": "space",
    "skip_forward": "right",
    "skip_back": "left",
    "skip_forward_30": ["right", "right", "right"],
    "next": "right",
    "fullscreen": "f",
    "subtitles": "c",
    "back": ["alt", "left"]
  },
  "vlc": {
    "play_pause": "space",
    "skip_forward": "right",
    "skip_back": "left",
    "skip_forward_30": ["right", "right", "right"],
    "next": ["ctrl", "right"],
    "fullscreen": "f",
    "subtitles": "v",
    "back": ["alt", "left"]
  }
}

def load_presets():
    if not os.path.exists(PRESETS_PATH):
        try:
            with open(PRESETS_PATH, 'w') as f:
                json.dump(DEFAULT_PRESETS, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not write default presets: {e}")
            return DEFAULT_PRESETS
    try:
        with open(PRESETS_PATH, 'r') as f:
            data = json.load(f)
            # Merge any missing default presets (like VLC)
            updated = False
            for k, v in DEFAULT_PRESETS.items():
                if k not in data:
                    data[k] = v
                    updated = True
            if updated:
                try:
                    with open(PRESETS_PATH, 'w') as out_f:
                        json.dump(data, out_f, indent=2)
                except Exception:
                    pass
            return data
    except Exception as e:
        print(f"⚠️ Error reading presets.json: {e}, falling back to defaults.")
        return DEFAULT_PRESETS

# ── Cross-Platform Native Input Backend ──────────────────────────────────────
IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')

USE_NATIVE_MOUSE = False
HAS_WIN32GUI = False

if IS_WINDOWS:
    try:
        import win32api, win32con
        try:
            import win32gui
            HAS_WIN32GUI = True
        except ImportError:
            pass
        def _move_mouse(x, y):
            win32api.SetCursorPos((int(x), int(y)))
        def _click_mouse(button='left'):
            if button == 'left':
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                time.sleep(0.04)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                time.sleep(0.04)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
        USE_NATIVE_MOUSE = True
        print("✅ Windows: win32api loaded for low-latency cursor control.")
    except ImportError:
        pass

elif IS_MAC:
    try:
        from Quartz.CoreGraphics import CGEventCreateMouseEvent, CGEventPost, kCGEventMouseMoved, kCGEventLeftMouseDown, kCGEventLeftMouseUp, kCGEventRightMouseDown, kCGEventRightMouseUp, kCGMouseButtonLeft, kCGMouseButtonRight, kCGHIDEventTap
        
        def _move_mouse(x, y):
            event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), kCGMouseButtonLeft)
            CGEventPost(kCGHIDEventTap, event)
            
        def _click_mouse(button='left'):
            x, y = pyautogui.position()
            if button == 'left':
                down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), kCGMouseButtonLeft)
                up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), kCGMouseButtonLeft)
            else:
                down = CGEventCreateMouseEvent(None, kCGEventRightMouseDown, (x, y), kCGMouseButtonRight)
                up = CGEventCreateMouseEvent(None, kCGEventRightMouseUp, (x, y), kCGMouseButtonRight)
            CGEventPost(kCGHIDEventTap, down)
            time.sleep(0.04)
            CGEventPost(kCGHIDEventTap, up)
            
        USE_NATIVE_MOUSE = True
        print("✅ macOS: Quartz loaded for low-latency cursor control.")
    except ImportError:
        pass

if not USE_NATIVE_MOUSE:
    def _move_mouse(x, y):
        pyautogui.moveTo(x, y, duration=0)
    def _click_mouse(button='left'):
        pyautogui.click(button=button)
    print("⚠️ Using pyautogui fallback for cursor control (install pywin32 on Win or pyobjc on Mac for zero latency).")


class InputBackend:
    @staticmethod
    def move_mouse(x, y):
        _move_mouse(x, y)

    @staticmethod
    def click_mouse(button='left'):
        _click_mouse(button)

    @staticmethod
    def send_keys(keys):
        try:
            if isinstance(keys, list):
                # If it's a list of identical keys (e.g. ["l", "l", "l"]), press sequentially.
                if len(keys) > 0 and all(x == keys[0] for x in keys):
                    for k in keys:
                        pyautogui.press(k)
                        time.sleep(0.05)
                else:
                    pyautogui.hotkey(*keys)
            else:
                pyautogui.press(keys)
        except Exception as e:
            print(f"Error simulating keys {keys}: {e}")

def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

app = Flask(__name__, static_folder=resource_path('static'))

# WebSocket transport: threading mode via simple-websocket (no eventlet/gevent,
# which are painful to bundle into a PyInstaller exe on Windows).
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Cache screen size once at startup to avoid constant ctypes overhead
try:
    SCREEN_W, SCREEN_H = pyautogui.size()
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

# Get cursor position natively depending on OS configuration
if IS_WINDOWS and USE_NATIVE_MOUSE:
    def get_cursor_position():
        try:
            return win32api.GetCursorPos()
        except Exception:
            return pyautogui.position()
else:
    def get_cursor_position():
        return pyautogui.position()

# Client velocities are isolated and tracked dynamically per token
SMOOTHING    = 0.02

# Scale mouse speed according to screen size resolution to prevent slow movements on high-res / 4K displays
RESOLUTION_SCALE = max(1.0, SCREEN_W / 1920.0)
BASE_SPEED   = 2.4 * RESOLUTION_SCALE
ACCEL_POWER  = 1.40

def apply_acceleration(delta, base_speed=BASE_SPEED, accel_power=ACCEL_POWER):
    sign = 1 if delta >= 0 else -1
    ad = abs(delta)
    if ad < 2.0:
        return delta * base_speed
    return sign * (ad ** accel_power) * base_speed


def handle_mouse_move(token, dx, dy, sens=1.0):
    """Apply sensitivity-tuned acceleration + smoothing and move the cursor.

    Shared by the HTTP /mouse/move route and the WS mouse_move event. `sens` is
    the phone's sensitivity slider (0.5-2.5); at 1.0 behaviour is identical to
    the original fixed-curve mouse.
    """
    vel = get_client_velocity(token)
    try:
        sens = max(0.1, min(5.0, float(sens)))
    except (ValueError, TypeError):
        sens = 1.0
    # Higher sens -> less smoothing (snappier) and more acceleration
    smoothing = max(0.005, min(0.5, SMOOTHING * (1.0 / sens)))
    accel_power = max(1.0, min(2.0, ACCEL_POWER + 0.15 * (sens - 1.0)))
    base_speed = BASE_SPEED * sens

    adx = apply_acceleration(dx, base_speed, accel_power)
    ady = apply_acceleration(dy, base_speed, accel_power)

    vel[0] = vel[0] * smoothing + adx * (1 - smoothing)
    vel[1] = vel[1] * smoothing + ady * (1 - smoothing)

    x, y = get_cursor_position()
    nx = max(0, min(SCREEN_W - 1, x + vel[0]))
    ny = max(0, min(SCREEN_H - 1, y + vel[1]))
    InputBackend.move_mouse(nx, ny)


def presentation_start_key():
    """Pick the slideshow-start key for the foreground app. Native deck apps
    (PowerPoint, Impress) start with F5; browser-based decks (Google Slides,
    Canva, Prezi) use Ctrl+F5 — plain F5 would reload the browser tab."""
    if IS_WINDOWS and HAS_WIN32GUI:
        try:
            title = win32gui.GetWindowText(win32gui.GetForegroundWindow()).lower()
            if any(k in title for k in ('slides', 'canva', 'prezi', 'docs.google')):
                return ['ctrl', 'f5']
        except Exception:
            pass
    return ['f5']


def handle_key(action, preset='universal'):
    audio_actions = {
        'mute':     lambda: pyautogui.press('volumemute'),
        'vol_up':   lambda: pyautogui.press('volumeup'),
        'vol_down': lambda: pyautogui.press('volumedown'),
    }
    if action in audio_actions:
        audio_actions[action]()
        return {'ok': True}
    # Presentation slide navigation uses plain arrow keys regardless of the
    # media preset (Alt+Left is browser-back and won't move most slide apps).
    presentation_actions = {
        'next_slide': lambda: pyautogui.press('right'),
        'prev_slide': lambda: pyautogui.press('left'),
        'present_start': lambda: InputBackend.send_keys(presentation_start_key()),
        'present_exit': lambda: pyautogui.press('esc'),
    }
    if action in presentation_actions:
        presentation_actions[action]()
        return {'ok': True}
    presets_map = load_presets()
    preset_config = presets_map.get(preset, presets_map.get('universal', {}))
    keys = preset_config.get(action)
    if keys:
        InputBackend.send_keys(keys)
        return {'ok': True}
    return {'ok': False, 'error': f"Key map missing for action '{action}' in preset '{preset}'"}


def handle_mouse_click(button='left'):
    InputBackend.click_mouse(button)


def handle_mouse_scroll(dy):
    try:
        dy = float(dy)
    except (ValueError, TypeError):
        dy = 0.0
    dy = max(-20, min(20, dy))
    pyautogui.scroll(int(round(dy)))


def handle_pointer_on():
    if HAS_TKINTER and overlay.root:
        overlay.show()


def handle_pointer_off():
    if HAS_TKINTER and overlay.root:
        overlay.hide()


def handle_blackout(on):
    if HAS_TKINTER and overlay.root:
        overlay.set_blackout(bool(on))
    return {'ok': True}


def handle_pointer_move(x, y):
    try:
        x = max(0, min(SCREEN_W, float(x)))
        y = max(0, min(SCREEN_H, float(y)))
        if HAS_TKINTER and overlay.root:
            overlay.move(x, y)
    except (ValueError, TypeError):
        pass


# ── Battery Status (Windows power API) ───────────────────────────────────────
class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_ubyte),
        ('BatteryFlag', ctypes.c_ubyte),
        ('BatteryLifePercent', ctypes.c_ubyte),
        ('SystemStatusFlag', ctypes.c_ubyte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong),
    ]


def get_battery_percent():
    if not IS_WINDOWS:
        return None
    try:
        status = SYSTEM_POWER_STATUS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        if status.BatteryLifePercent == 255:  # unknown (e.g. desktop on AC)
            return None
        return int(status.BatteryLifePercent)
    except Exception:
        return None

# ── Window Preset Detector ───────────────────────────────────────────────────
PRESET_RULES = [
    ("YouTube", "youtube_hotstar"),
    ("Hotstar", "youtube_hotstar"),
    ("VLC", "vlc"),
    ("Netflix", "universal"),
    ("Prime Video", "universal"),
]

def detect_active_preset():
    if not IS_WINDOWS or not HAS_WIN32GUI:
        return None
    try:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        for keyword, preset in PRESET_RULES:
            if keyword.lower() in title.lower():
                return preset
    except Exception:
        pass
    return None

# ── Laser Presentation Overlay ────────────────────────────────────────────────
try:
    import tkinter as tk
    import threading
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False

class LaserOverlay:
    def __init__(self):
        self.root = None
        self.dot = None
        self.visible = False
        self.blackout = False
        self.last_activity = time.time()

    def start(self):
        if not HAS_TKINTER:
            return
        threading.Thread(target=self._run, daemon=True).start()
        # Wait briefly for initialization to complete to avoid startup race
        for _ in range(20):
            if self.root is not None:
                break
            time.sleep(0.05)
        # Start watchdog loop
        threading.Thread(target=self._watchdog_loop, daemon=True).start()

    def _watchdog_loop(self):
        while True:
            time.sleep(0.5)
            if self.visible and not self.blackout and (time.time() - self.last_activity > 2.0):
                self.hide()

    def _run(self):
        try:
            self.root = tk.Tk()
            self.root.attributes('-alpha', 1.0)
            self.root.attributes('-topmost', True)
            self.root.attributes('-transparentcolor', 'black')  # click-through on Windows
            self.root.overrideredirect(True)
            self.root.geometry(f"{SCREEN_W}x{SCREEN_H}+0+0")
            self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.dot = self.canvas.create_oval(-50, -50, -30, -30, fill='red', outline='')
            self.root.withdraw()
            self.root.mainloop()
        except Exception as e:
            print(f"⚠️ Failed to initialize laser overlay: {e}")
            self.root = None

    def show(self):
        self.last_activity = time.time()
        if self.blackout:
            return  # blanking is authoritative until explicitly lifted
        if self.root:
            try:
                self.root.after(0, self.root.deiconify)
            except Exception:
                pass
        self.visible = True

    def hide(self):
        if self.blackout:
            return  # blanking is authoritative until explicitly lifted
        if self.root:
            try:
                self.root.after(0, self.root.withdraw)
            except Exception:
                pass
        self.visible = False

    def set_blackout(self, on):
        on = bool(on)
        self.blackout = on
        self.last_activity = time.time()
        if not self.root:
            return
        def _apply():
            if on:
                # Near-black (0,0,1): 'black' is the transparent color, so a
                # solid screen needs a pixel value the transparentcolor won't match.
                self.canvas.config(bg='#000001')
                self.canvas.coords(self.dot, -50, -50, -30, -30)
                self.root.deiconify()
            else:
                self.canvas.config(bg='black')
                self.root.withdraw()
        self.root.after(0, _apply)
        self.visible = on

    def move(self, x, y):
        self.last_activity = time.time()
        if self.root:
            try:
                self.root.after(0, lambda: self.canvas.coords(self.dot, x-12, y-12, x+12, y+12))
            except Exception:
                pass

overlay = LaserOverlay()
overlay.start()

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/ping', methods=['GET'])
def ping():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    is_auth = token in VALID_TOKENS if token else False
        
    detected = detect_active_preset() if is_auth else None
    return jsonify({
        'ok': True, 
        'authorized': is_auth, 
        'detected_preset': detected,
        'screen_w': SCREEN_W,
        'screen_h': SCREEN_H,
        'overlay_available': IS_WINDOWS and HAS_TKINTER and overlay.root is not None
    })

FAILED_ATTEMPTS = 0
LOCKOUT_UNTIL = 0.0

@app.route('/pair', methods=['POST'])
def pair():
    global FAILED_ATTEMPTS, LOCKOUT_UNTIL, PAIRING_PIN
    
    current_time = time.time()
    if current_time < LOCKOUT_UNTIL:
        remaining = int(LOCKOUT_UNTIL - current_time)
        return jsonify({'ok': False, 'error': f"Too many failed attempts. Try again in {remaining} seconds."}), 429

    data = request.get_json(silent=True) or {}
    pin = data.get('pin')
    
    # Timing safe check and PIN matching
    if pin and secrets.compare_digest(str(pin).strip(), PAIRING_PIN):
        FAILED_ATTEMPTS = 0
        LOCKOUT_UNTIL = 0.0
        
        # Invalidate old PIN and generate a new one immediately for subsequent pairings
        old_pin = PAIRING_PIN
        PAIRING_PIN = str(random.randint(100000, 999999))
        
        # Generate new unique session token
        client_token = secrets.token_hex(24)
        VALID_TOKENS.add(client_token)
        
        print(f"\n========================================")
        print(f"✅ Successful pairing! Old PIN {old_pin} expired.")
        print(f"   New Pairing PIN (for next device): {PAIRING_PIN}")
        print(f"========================================\n")
        
        return jsonify({'ok': True, 'token': client_token})
        
    FAILED_ATTEMPTS += 1
    if FAILED_ATTEMPTS >= 5:
        LOCKOUT_UNTIL = current_time + 30.0  # 30 seconds penalty lockout
        FAILED_ATTEMPTS = 0
        return jsonify({'ok': False, 'error': 'Too many failed attempts. Locked out for 30 seconds.'}), 429
        
    return jsonify({'ok': False, 'error': 'Invalid pairing PIN'}), 401

@app.route('/revoke', methods=['POST'])
def revoke():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    
    is_localhost = request.remote_addr in ('127.0.0.1', '::1')
    is_auth = token in VALID_TOKENS if token else False
    
    if not (is_localhost or is_auth):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    global PAIRING_PIN
    VALID_TOKENS.clear() # Revoke all active clients
    client_velocities.clear()
    PAIRING_PIN = str(random.randint(100000, 999999))

    # Force any live sockets back into the pairing state immediately
    for sid in list(active_authorized_sids):
        socketio.emit('state', build_state(None), to=sid)
    active_authorized_sids.clear()

    print(f"\n========================================")
    print(f"🔒 All session tokens revoked! New Pairing PIN: {PAIRING_PIN}")
    print(f"========================================\n")
    return jsonify({'ok': True, 'message': 'All tokens revoked.'})

@app.route('/key', methods=['POST'])
@require_auth
def key():
    data = request.get_json(silent=True) or {}
    result = handle_key(data.get('action'), data.get('preset', 'universal'))
    return jsonify(result), (200 if result.get('ok') else 400)

@app.route('/mouse/move', methods=['POST'])
@require_auth
def mouse_move():
    # Extract client token to isolate velocity state
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    else:
        token = 'default'

    data = request.get_json(silent=True) or {}
    try:
        raw_dx = float(data.get('dx', 0.0))
        raw_dy = float(data.get('dy', 0.0))
    except (ValueError, TypeError):
        raw_dx = 0.0
        raw_dy = 0.0

    handle_mouse_move(token, raw_dx, raw_dy, data.get('sens', 1.0))
    return jsonify({'ok': True})

@app.route('/mouse/stop', methods=['POST'])
@require_auth
def mouse_stop():
    token = request.headers.get('Authorization')
    if token and token.startswith('Bearer '):
        token = token[7:]
    else:
        token = 'default'
        
    if token in client_velocities:
        client_velocities[token] = [0.0, 0.0]
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
    handle_pointer_on()
    return jsonify({'ok': True})

@app.route('/pointer/off', methods=['POST'])
@require_auth
def pointer_off():
    handle_pointer_off()
    return jsonify({'ok': True})

@app.route('/pointer/move', methods=['POST'])
@require_auth
def pointer_move():
    data = request.get_json(silent=True) or {}
    handle_pointer_move(data.get('x', 0), data.get('y', 0))
    return jsonify({'ok': True})

@app.route('/screen/blackout', methods=['POST'])
@require_auth
def screen_blackout():
    data = request.get_json(silent=True) or {}
    handle_blackout(data.get('on', False))
    return jsonify({'ok': True})

# ── WebSocket Transport ──────────────────────────────────────────────────────
active_authorized_sids = set()


def socket_require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = session.get('token')
        if not token or token not in VALID_TOKENS:
            return  # silently ignore unauthorized traffic
        return f(*args, **kwargs)
    return wrapper


def build_state(token):
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


@socketio.on('connect')
def on_connect(auth):
    token = None
    if auth:
        token = auth.get('token')
        if isinstance(token, str) and token.startswith('Bearer '):
            token = token[7:]
    session['token'] = token if token and token in VALID_TOKENS else None
    if session['token']:
        active_authorized_sids.add(request.sid)
    emit('state', build_state(session['token']))


@socketio.on('disconnect')
def on_disconnect():
    token = session.get('token')
    if token:
        active_authorized_sids.discard(request.sid)
        if token in client_velocities:
            client_velocities[token] = [0.0, 0.0]


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
    token = session['token']
    if token in client_velocities:
        client_velocities[token] = [0.0, 0.0]


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


@socketio.on('pointer_on')
@socket_require_auth
def ws_pointer_on(data=None):
    handle_pointer_on()


@socketio.on('pointer_off')
@socket_require_auth
def ws_pointer_off(data=None):
    handle_pointer_off()


@socketio.on('blackout')
@socket_require_auth
def ws_blackout(data=None):
    data = data or {}
    handle_blackout(data.get('on', False))


@socketio.on('pointer_move')
@socket_require_auth
def ws_pointer_move(data):
    data = data or {}
    handle_pointer_move(data.get('x', 0), data.get('y', 0))


def _preset_monitor():
    last_preset = None
    while True:
        time.sleep(2.0)
        if not active_authorized_sids:
            continue
        try:
            p = detect_active_preset()
            if p and p != last_preset:
                last_preset = p
                socketio.emit('preset_changed', {'preset': p})
        except Exception as e:
            print(f"preset monitor: {e}")


# ── Startup ──────────────────────────────────────────────────────────────────

def get_local_ip():
    import socket

    def _usable(ip):
        if not ip:
            return False
        if ip.startswith(('127.', '169.254.', '0.', '255.')):
            return False
        return True

    # UDP trick to a public address forces routing via the real default
    # route / LAN adapter (the phone must reach this IP, not a VPN one).
    for target in ('8.8.8.8', '10.255.255.255'):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 1))
            ip = s.getsockname()[0]
            if _usable(ip):
                return ip
        except Exception:
            pass
        finally:
            s.close()
    # Fallback: enumerate the host's own interface addresses.
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None,
                                       socket.AF_INET, socket.SOCK_DGRAM):
            ip = info[4][0]
            if _usable(ip):
                return ip
    except Exception:
        pass
    return '127.0.0.1'

if __name__ == '__main__':
    try:
        import qrcode
    except ImportError:
        qrcode = None

    ip  = get_local_ip()
    url = f"http://{ip}:5000"

    print(f"\n========================================")
    print(f"✅ Laptop Remote running!")
    print(f"   URL: {url}")
    print(f"   mDNS: http://remotedeck.local:5000")
    print(f"   Pairing PIN: {PAIRING_PIN}")
    print(f"========================================\n")

    if qrcode:
        # Use the IP-based URL in the QR code for maximum compatibility across all devices
        qr = qrcode.QRCode(version=1, box_size=1, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(invert=True)
        print("\n   Scan the QR code above to connect your phone!\n")
    else:
        print("   (pip install qrcode  →  get a scannable QR code)\n")

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

    # Push preset changes to connected clients while the server is up
    threading.Thread(target=_preset_monitor, daemon=True).start()

    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    finally:
        if HAS_ZEROCONF and zeroconf_instance:
            try:
                print("🧹 Unregistering mDNS Zeroconf service...")
                zeroconf_instance.unregister_service(service_info)
                zeroconf_instance.close()
            except Exception:
                pass
