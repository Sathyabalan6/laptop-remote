import os
import secrets
import threading
import time
from functools import wraps
from flask import request, jsonify, session

auth_lock = threading.Lock()
VALID_TOKENS = set()

def generate_pairing_pin():
    """Always generates a fresh random 6-digit PIN (used for rotation after pairing)."""
    return f"{secrets.randbelow(900000) + 100000}"

# At startup only: honour LAPTOP_REMOTE_PIN env var for a fixed/custom PIN.
_env_pin = os.environ.get('LAPTOP_REMOTE_PIN', '').strip()
PAIRING_PIN = _env_pin if _env_pin else generate_pairing_pin()

def set_pairing_pin(pin):
    """Override the pairing PIN (called once at startup for --pin CLI arg)."""
    global PAIRING_PIN
    with auth_lock:
        PAIRING_PIN = str(pin).strip()


failed_attempts_by_ip = {}
ip_rate_lock = threading.Lock()

def check_and_record_failed_ip(ip):
    now = time.time()
    with ip_rate_lock:
        if len(failed_attempts_by_ip) > 500:
            expired = [k for k, v in failed_attempts_by_ip.items() if now > v.get('lockout_until', 0) and v.get('attempts', 0) == 0]
            for k in expired:
                failed_attempts_by_ip.pop(k, None)

        record = failed_attempts_by_ip.setdefault(ip, {'attempts': 0, 'lockout_until': 0.0})
        if now < record['lockout_until']:
            return False, int(record['lockout_until'] - now)
        
        record['attempts'] += 1
        if record['attempts'] >= 5:
            record['lockout_until'] = now + 30.0
            record['attempts'] = 0
            return False, 30
        return True, 0

def clear_failed_ip(ip):
    with ip_rate_lock:
        failed_attempts_by_ip.pop(ip, None)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization') or (request.get_json(silent=True) or {}).get('token')
        if token and token.startswith('Bearer '):
            token = token[7:]
        with auth_lock:
            is_valid = bool(token and token in VALID_TOKENS)
        if not is_valid:
            return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

def socket_require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = session.get('token')
        with auth_lock:
            is_valid = bool(token and token in VALID_TOKENS)
        if not is_valid:
            return
        return f(*args, **kwargs)
    return wrapper
