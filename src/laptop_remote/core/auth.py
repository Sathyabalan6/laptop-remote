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


def is_localhost(addr):
    """Check whether a client address is on localhost/loopback."""
    if not addr:
        return False
    return addr in ('127.0.0.1', '::1', 'localhost', 'testclient')


failed_attempts_by_ip = {}
ip_rate_lock = threading.Lock()

def _cleanup_expired_ips(now):
    """Purge stale rate-limiting records (older than 10 minutes). Must be called with ip_rate_lock held."""
    stale_keys = [
        ip for ip, rec in failed_attempts_by_ip.items()
        if now >= rec.get('lockout_until', 0.0) and (now - rec.get('last_attempt', 0.0) > 600.0)
    ]
    for k in stale_keys:
        failed_attempts_by_ip.pop(k, None)

def is_ip_locked(ip):
    """Check if an IP address is currently locked out from pairing attempts."""
    now = time.time()
    with ip_rate_lock:
        rec = failed_attempts_by_ip.get(ip)
        if not rec:
            return False, 0
        if now < rec.get('lockout_until', 0.0):
            return True, int(rec['lockout_until'] - now)
        return False, 0

def check_and_record_failed_ip(ip):
    """Record a failed pairing attempt for an IP. Returns (allowed, lockout_secs)."""
    now = time.time()
    with ip_rate_lock:
        if len(failed_attempts_by_ip) > 100:
            _cleanup_expired_ips(now)

        rec = failed_attempts_by_ip.setdefault(ip, {
            'attempts': 0,
            'last_attempt': now,
            'lockout_until': 0.0,
            'lockout_duration': 30.0
        })

        if now < rec['lockout_until']:
            return False, int(rec['lockout_until'] - now)

        # Reset attempts if last failure was over 5 minutes ago
        if (now - rec['last_attempt']) > 300.0:
            rec['attempts'] = 0
            rec['lockout_duration'] = 30.0

        rec['last_attempt'] = now
        rec['attempts'] += 1

        if rec['attempts'] >= 5:
            duration = rec.get('lockout_duration', 30.0)
            rec['lockout_until'] = now + duration
            rec['attempts'] = 0
            rec['lockout_duration'] = min(300.0, duration * 2.0)
            return False, int(duration)

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
