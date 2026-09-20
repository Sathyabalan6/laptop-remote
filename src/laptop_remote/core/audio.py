import sys
import shutil
import subprocess
import re
import time

IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')
IS_LINUX = sys.platform.startswith('linux')

try:
    import pyautogui
except Exception:
    pyautogui = None

_last_known_volume = 50
_last_known_muted = False


def _get_volume_windows():
    global _last_known_volume, _last_known_muted
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
        current_vol = int(round(volume_ctrl.GetMasterVolumeLevelScalar() * 100))
        muted = bool(volume_ctrl.GetMute())
        _last_known_volume = current_vol
        _last_known_muted = muted
        return {'volume': current_vol, 'muted': muted}
    except Exception:
        pass
    return None


def _set_volume_windows(pct):
    global _last_known_volume
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
        target_scalar = max(0.0, min(1.0, pct / 100.0))
        volume_ctrl.SetMasterVolumeLevelScalar(target_scalar, None)
        _last_known_volume = pct
        return True
    except Exception:
        pass
    return False


def _toggle_mute_windows():
    global _last_known_muted
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_ctrl = cast(interface, POINTER(IAudioEndpointVolume))
        new_state = not bool(volume_ctrl.GetMute())
        volume_ctrl.SetMute(new_state, None)
        _last_known_muted = new_state
        return True
    except Exception:
        pass
    return False


def _get_volume_linux():
    global _last_known_volume, _last_known_muted
    if shutil.which('wpctl'):
        try:
            out = subprocess.check_output(['wpctl', 'get-volume', '@DEFAULT_AUDIO_SINK@'], stderr=subprocess.DEVNULL).decode()
            muted = '[MUTED]' in out
            match = re.search(r'Volume:\s*([\d\.]+)', out)
            if match:
                vol = int(round(float(match.group(1)) * 100))
                _last_known_volume = vol
                _last_known_muted = muted
                return {'volume': vol, 'muted': muted}
        except Exception:
            pass

    if shutil.which('amixer'):
        try:
            out = subprocess.check_output(['amixer', 'get', 'Master'], stderr=subprocess.DEVNULL).decode()
            vol_match = re.search(r'\[(\d+)%\]', out)
            mute_match = re.search(r'\[(on|off)\]', out)
            if vol_match:
                vol = int(vol_match.group(1))
                muted = mute_match.group(1) == 'off' if mute_match else False
                _last_known_volume = vol
                _last_known_muted = muted
                return {'volume': vol, 'muted': muted}
        except Exception:
            pass

    if shutil.which('pactl'):
        try:
            out = subprocess.check_output(['pactl', 'get-sink-volume', '@DEFAULT_SINK@'], stderr=subprocess.DEVNULL).decode()
            match = re.search(r'(\d+)%', out)
            mute_out = subprocess.check_output(['pactl', 'get-sink-mute', '@DEFAULT_SINK@'], stderr=subprocess.DEVNULL).decode()
            muted = 'yes' in mute_out.lower()
            if match:
                vol = int(match.group(1))
                _last_known_volume = vol
                _last_known_muted = muted
                return {'volume': vol, 'muted': muted}
        except Exception:
            pass

    return None


def _set_volume_linux(pct):
    global _last_known_volume
    pct = max(0, min(100, int(pct)))
    if shutil.which('wpctl'):
        try:
            val = pct / 100.0
            subprocess.run(['wpctl', 'set-volume', '@DEFAULT_AUDIO_SINK@', f"{val:.2f}"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _last_known_volume = pct
            return True
        except Exception:
            pass

    if shutil.which('amixer'):
        try:
            subprocess.run(['amixer', 'sset', 'Master', f"{pct}%"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _last_known_volume = pct
            return True
        except Exception:
            pass

    if shutil.which('pactl'):
        try:
            subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', f"{pct}%"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            _last_known_volume = pct
            return True
        except Exception:
            pass

    return False


def _toggle_mute_linux():
    global _last_known_muted
    if shutil.which('wpctl'):
        try:
            subprocess.run(['wpctl', 'set-mute', '@DEFAULT_AUDIO_SINK@', 'toggle'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    if shutil.which('amixer'):
        try:
            subprocess.run(['amixer', 'sset', 'Master', 'toggle'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    if shutil.which('pactl'):
        try:
            subprocess.run(['pactl', 'set-sink-mute', '@DEFAULT_SINK@', 'toggle'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            pass

    return False


def _get_volume_mac():
    global _last_known_volume, _last_known_muted
    try:
        vol_out = subprocess.check_output(['osascript', '-e', 'output volume of (get volume settings)'], stderr=subprocess.DEVNULL).decode().strip()
        mute_out = subprocess.check_output(['osascript', '-e', 'output muted of (get volume settings)'], stderr=subprocess.DEVNULL).decode().strip()
        vol = int(vol_out)
        muted = mute_out.lower() == 'true'
        _last_known_volume = vol
        _last_known_muted = muted
        return {'volume': vol, 'muted': muted}
    except Exception:
        pass
    return None


def _set_volume_mac(pct):
    global _last_known_volume
    pct = max(0, min(100, int(pct)))
    try:
        subprocess.run(['osascript', '-e', f'set volume output volume {pct}'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _last_known_volume = pct
        return True
    except Exception:
        pass
    return False


def _toggle_mute_mac():
    try:
        subprocess.run(['osascript', '-e', 'set volume output muted not (output muted of (get volume settings))'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        pass
    return False


def get_volume():
    """Returns a dict {'volume': int (0-100), 'muted': bool} representing current OS audio state."""
    if IS_WINDOWS:
        res = _get_volume_windows()
        if res is not None:
            return res
    elif IS_LINUX:
        res = _get_volume_linux()
        if res is not None:
            return res
    elif IS_MAC:
        res = _get_volume_mac()
        if res is not None:
            return res

    return {'volume': _last_known_volume, 'muted': _last_known_muted}


def set_volume(pct):
    """Set system master volume to pct (0-100)."""
    global _last_known_volume
    pct = max(0, min(100, int(pct)))
    success = False
    if IS_WINDOWS:
        success = _set_volume_windows(pct)
    elif IS_LINUX:
        success = _set_volume_linux(pct)
    elif IS_MAC:
        success = _set_volume_mac(pct)

    if not success and pyautogui:
        # Fallback to relative keypresses
        diff = pct - _last_known_volume
        steps = int(round(abs(diff) / 5))
        key = 'volumeup' if diff > 0 else 'volumedown'
        for _ in range(steps):
            pyautogui.press(key)
        success = True

    _last_known_volume = pct
    info = get_volume()
    info['ok'] = success
    return info


def toggle_mute():
    """Toggle system mute state."""
    success = False
    if IS_WINDOWS:
        success = _toggle_mute_windows()
    elif IS_LINUX:
        success = _toggle_mute_linux()
    elif IS_MAC:
        success = _toggle_mute_mac()

    if not success and pyautogui:
        pyautogui.press('volumemute')
        success = True

    info = get_volume()
    info['ok'] = success
    return info
