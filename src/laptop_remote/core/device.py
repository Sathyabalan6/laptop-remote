"""Device display naming, custom name overrides, and hostname cleaning."""

import os
import re
import socket
import getpass

_custom_device_name = None


def set_custom_device_name(name):
    """Set the globally configured device friendly name."""
    global _custom_device_name
    _custom_device_name = name.strip() if (name and str(name).strip()) else None


def clean_hostname(raw_hostname: str, username: str | None = None) -> str:
    """Transform a raw system hostname into a concise, readable device name.

    Args:
        raw_hostname: e.g. 'sathybalan-Vivobook-ASUSLaptop-X1502ZA-X1502ZA' or 'DESKTOP-4F8K2L'.
        username: Optional username to strip if at the start of raw_hostname.
    """
    raw = (raw_hostname or "Laptop").strip()
    if not raw:
        return "Laptop"

    # 1. Strip username prefix if present
    if username:
        u = username.lower()
        if raw.lower().startswith(u):
            raw = raw[len(u):].lstrip('-_')

    # 2. Match known common laptop / desktop branding patterns
    known_models = sorted([
        'Vivobook', 'Zenbook', 'ThinkPad', 'IdeaPad', 'Yoga', 'Legion',
        'MacBook Pro', 'MacBook Air', 'MacBook', 'iMac', 'Mac mini', 'Mac Studio',
        'XPS', 'Latitude', 'Inspiron', 'Precision', 'Alienware',
        'Spectre', 'Envy', 'Pavilion', 'EliteBook', 'Omen',
        'Surface Laptop', 'Surface Pro', 'Surface', 'Galaxy Book', 'Framework'
    ], key=len, reverse=True)
    for model in known_models:
        pattern = r'[-_\s]+'.join(re.escape(p) for p in model.split())
        if re.search(pattern, raw, re.IGNORECASE):
            return model

    # 3. Handle default Windows hostname formats (e.g. DESKTOP-4F8K2L)
    m = re.match(r'^(desktop|laptop|pc)[-_]([a-z0-9]+)$', raw, re.IGNORECASE)
    if m:
        return f"{m.group(1).capitalize()}-{m.group(2)}"

    # 4. Clean up common noise tokens
    cleaned = re.sub(r'[-_]?(ASUS|Laptop|PC|Linux|Desktop|Notebook|Computer)[-_]?', ' ', raw, flags=re.IGNORECASE)
    parts = [p for p in re.split(r'[-_\s]+', cleaned) if p]
    if parts:
        # De-duplicate consecutive identical tokens (e.g. X1502ZA-X1502ZA)
        deduped = []
        for p in parts:
            if not deduped or p.lower() != deduped[-1].lower():
                deduped.append(p)
        name = ' '.join(deduped[:2])
    else:
        name = raw

    # 5. Handle casing and truncation
    if name.isupper() and len(name) > 4:
        name = name[:14].title()
    elif len(name) > 16:
        name = name[:16].strip()

    if name.islower():
        name = name.title()

    return name.title() if name.islower() else name or "Laptop"


def get_device_display_name(custom_name=None):
    """Retrieve the effective display name for the device."""
    if custom_name and str(custom_name).strip():
        return str(custom_name).strip()
    if _custom_device_name:
        return _custom_device_name
    env_name = os.environ.get('REMOTE_DECK_NAME')
    if env_name and env_name.strip():
        return env_name.strip()

    raw = socket.gethostname() or "Laptop"
    try:
        user = getpass.getuser()
    except Exception:
        user = None

    return clean_hostname(raw, username=user)
