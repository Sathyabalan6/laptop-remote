import sys
import ctypes

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
        try:
            status = SYSTEM_POWER_STATUS()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
            if status.BatteryLifePercent == 255:
                return None
            return int(status.BatteryLifePercent)
        except Exception:
            return None
    elif sys.platform.startswith('linux'):
        try:
            import glob
            for cap_path in glob.glob('/sys/class/power_supply/BAT*/capacity'):
                try:
                    with open(cap_path, 'r') as f:
                        val = f.read().strip()
                        if val.isdigit():
                            return int(val)
                except Exception:
                    continue
        except Exception:
            pass
    return None
