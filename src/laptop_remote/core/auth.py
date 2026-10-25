import json
import os
import secrets
import threading
import time
from functools import wraps

from flask import jsonify, request, session

from .logger import logger

auth_lock = threading.RLock()
VALID_TOKENS = set()
PAIRED_SESSIONS = {}

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
_global_failed_attempts = 0
_global_last_attempt = 0.0
_global_lockout_until = 0.0


def _cleanup_expired_ips(now):
    """Purge stale rate-limiting records (older than 10 minutes). Must be called with ip_rate_lock held."""
    stale_keys = [
        ip for ip, rec in failed_attempts_by_ip.items()
        if now >= rec.get('lockout_until', 0.0) and (now - rec.get('last_attempt', 0.0) > 600.0)
    ]
    for k in stale_keys:
        failed_attempts_by_ip.pop(k, None)


def reset_rate_limits():
    """Reset all per-IP and global rate limiting records (useful for test isolation)."""
    global _global_failed_attempts, _global_last_attempt, _global_lockout_until
    with ip_rate_lock:
        failed_attempts_by_ip.clear()
        _global_failed_attempts = 0
        _global_last_attempt = 0.0
        _global_lockout_until = 0.0


def is_ip_locked(ip):
    """Check if an IP address or the global server is currently locked out from pairing attempts."""
    now = time.time()
    with ip_rate_lock:
        if now < _global_lockout_until:
            return True, int(_global_lockout_until - now)

        rec = failed_attempts_by_ip.get(ip)
        if not rec:
            return False, 0
        if now < rec.get('lockout_until', 0.0):
            return True, int(rec['lockout_until'] - now)
        return False, 0


def check_and_record_failed_ip(ip):
    """Record a failed pairing attempt. Enforces both per-IP and LAN-wide global lockout.

    Returns (allowed: bool, lockout_secs: int).
    """
    global _global_failed_attempts, _global_last_attempt, _global_lockout_until
    now = time.time()
    with ip_rate_lock:
        if now < _global_lockout_until:
            return False, int(_global_lockout_until - now)

        # Reset global brute-force window if last failed attempt was over 5 minutes ago
        if (now - _global_last_attempt) > 300.0:
            _global_failed_attempts = 0

        _global_last_attempt = now
        _global_failed_attempts += 1

        # Global brute-force guard: 15 failed PIN guesses LAN-wide triggers a 60s global lockout
        if _global_failed_attempts >= 15:
            _global_lockout_until = now + 60.0
            _global_failed_attempts = 0
            return False, 60

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

        # Reset per-IP attempts if last failure was over 5 minutes ago
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

def _get_sessions_file_path():
    try:
        from .config import get_user_data_dir
        return os.path.join(get_user_data_dir(), 'sessions.json')
    except Exception:
        return None


def _save_sessions_to_disk():
    """Persist authorized device tokens and metadata to disk."""
    path = _get_sessions_file_path()
    if not path:
        return
    try:
        data = {
            'tokens': list(VALID_TOKENS),
            'sessions': PAIRED_SESSIONS,
        }
        temp_path = f"{path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, path)
    except Exception as e:
        logger.debug(f"Error persisting sessions: {e}")


def _load_persisted_sessions():
    """Load previously paired tokens and sessions from disk on startup."""
    path = _get_sessions_file_path()
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            tokens = data.get('tokens')
            sessions = data.get('sessions')
            if isinstance(tokens, list) and isinstance(sessions, dict):
                VALID_TOKENS.update(tok for tok in tokens if isinstance(tok, str))
                for k, v in sessions.items():
                    if isinstance(k, str) and isinstance(v, dict):
                        PAIRED_SESSIONS[k] = v
    except Exception as e:
        logger.debug(f"Error loading persisted sessions: {e}")


# Populate stored tokens on startup
_load_persisted_sessions()


def register_session(token, client_ip, device_name="Phone"):
    """Register a new active device session token with metadata and persist it."""
    with auth_lock:
        VALID_TOKENS.add(token)
        PAIRED_SESSIONS[token] = {
            'id': token[:8],
            'device_name': device_name or 'Phone',
            'ip': client_ip or 'unknown',
            'created_at': time.time(),
            'last_seen': time.time(),
        }
        _save_sessions_to_disk()


def touch_session(token):
    """Update last seen timestamp for an active session."""
    with auth_lock:
        if token in PAIRED_SESSIONS:
            PAIRED_SESSIONS[token]['last_seen'] = time.time()


def revoke_session(token_or_id):
    """Revoke a single session token or token ID and update persistent storage."""
    with auth_lock:
        target_token = None
        for tok, data in list(PAIRED_SESSIONS.items()):
            if tok == token_or_id or data.get('id') == token_or_id:
                target_token = tok
                break
        if target_token:
            VALID_TOKENS.discard(target_token)
            PAIRED_SESSIONS.pop(target_token, None)
            _save_sessions_to_disk()
            return True
        if token_or_id in VALID_TOKENS:
            VALID_TOKENS.discard(token_or_id)
            _save_sessions_to_disk()
            return True
        return False


def revoke_all_sessions():
    """Revoke all paired sessions in memory and purge persisted session storage."""
    with auth_lock:
        VALID_TOKENS.clear()
        PAIRED_SESSIONS.clear()
        path = _get_sessions_file_path()
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except OSError as e:
                logger.debug(f"Failed to remove sessions file {path}: {e}")

def get_active_sessions():
    """Return a list of currently paired and authorized device sessions."""
    with auth_lock:
        return [
            {
                'id': data.get('id', tok[:8]),
                'device_name': data.get('device_name', 'Device'),
                'ip': data.get('ip', 'unknown'),
                'created_at': data.get('created_at', 0),
                'last_seen': data.get('last_seen', 0),
            }
            for tok, data in PAIRED_SESSIONS.items()
            if tok in VALID_TOKENS
        ]

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
