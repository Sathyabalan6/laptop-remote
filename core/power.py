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
    if not IS_WINDOWS:
        return None
    try:
        status = SYSTEM_POWER_STATUS()
        ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status))
        if status.BatteryLifePercent == 255:
            return None
        return int(status.BatteryLifePercent)
    except Exception:
        return None
