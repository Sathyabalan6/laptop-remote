import contextlib
import ctypes
import glob
import re
import subprocess
import sys

IS_WINDOWS = sys.platform.startswith('win')


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
    if IS_WINDOWS:
        with contextlib.suppress(Exception):
            windll = getattr(ctypes, 'windll', None)
            if windll:
                status = SYSTEM_POWER_STATUS()
                windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
                if status.BatteryLifePercent != 255:
                    return int(status.BatteryLifePercent)
    elif sys.platform.startswith('linux'):
        for cap_path in glob.glob('/sys/class/power_supply/BAT*/capacity'):
            try:
                with open(cap_path, encoding='utf-8') as f:
                    val = f.read().strip()
                    if val.isdigit():
                        return int(val)
            except (OSError, UnicodeDecodeError):
                continue
    elif sys.platform == 'darwin':
        with contextlib.suppress(Exception):
            out = subprocess.check_output(
                ['pmset', '-g', 'batt'],
                stderr=subprocess.DEVNULL,
                timeout=2.0
            ).decode('utf-8', errors='replace')
            m = re.search(r'(\d+)%', out)
            if m:
                return int(m.group(1))
    return None

