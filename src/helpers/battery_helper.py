"""
VoiceMate Laptop Agent - Battery Monitor Module.
Monitors laptop battery percentage, charging state, and triggers
timely audio announcements and low-power warnings.
"""
import ctypes
import threading
import time
from typing import Optional, Callable

class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ('ACLineStatus', ctypes.c_byte),
        ('BatteryFlag', ctypes.c_byte),
        ('BatteryLifePercent', ctypes.c_byte),
        ('SystemStatusFlag', ctypes.c_byte),
        ('BatteryLifeTime', ctypes.c_ulong),
        ('BatteryFullLifeTime', ctypes.c_ulong)
    ]

class BatteryHelper:
    _last_announced_level = -1
    _is_monitoring = False
    _monitor_thread: Optional[threading.Thread] = None

    @classmethod
    def get_battery_info(cls) -> dict:
        """
        Gets current laptop battery percentage and charging status.
        Uses native Windows kernel32 API with psutil fallback.
        """
        try:
            status = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                pct = int(status.BatteryLifePercent)
                if pct <= 100:
                    return {
                        "percent": pct,
                        "charging": status.ACLineStatus == 1,
                        "is_laptop": True
                    }
        except Exception:
            pass

        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": int(battery.percent),
                    "charging": bool(battery.power_plugged),
                    "is_laptop": True
                }
        except Exception:
            pass

        return {
            "percent": -1,
            "charging": False,
            "is_laptop": False
        }

    @classmethod
    def get_battery_level(cls) -> int:
        return cls.get_battery_info().get("percent", -1)

    @classmethod
    def check_battery_status_message(cls, speak_callback: Callable[[str], None]):
        """
        Checks battery level and triggers periodic announcements or low-battery warnings.
        """
        info = cls.get_battery_info()
        battery_pct = info.get("percent", -1)
        if battery_pct < 0:
            return

        is_charging = info.get("charging", False)

        # সতর্কবাণী: চার্জ ২০% এর কম হলে এবং চার্জে না থাকলে
        if battery_pct < 20 and not is_charging and battery_pct % 5 == 0 and battery_pct != cls._last_announced_level:
            cls._last_announced_level = battery_pct
            speak_callback(f"সতর্কতা! আপনার ল্যাপটপের চার্জ খুব কম, মাত্র {battery_pct} শতাংশ। দয়া করে চার্জে দিন।")
            return

        # প্রতি ১০% পরপর স্ট্যাটাস ঘোষণা
        if battery_pct % 10 == 0 and battery_pct != cls._last_announced_level:
            cls._last_announced_level = battery_pct
            charging_str = " (চার্জ হচ্ছে)" if is_charging else ""
            speak_callback(f"আপনার ল্যাপটপের বর্তমান চার্জ {battery_pct} শতাংশ{charging_str}।")

    @classmethod
    def start_monitoring(cls, speak_callback: Callable[[str], None], interval_seconds: int = 60):
        if cls._is_monitoring:
            return
        cls._is_monitoring = True

        def loop():
            while cls._is_monitoring:
                try:
                    cls.check_battery_status_message(speak_callback)
                except Exception:
                    pass
                time.sleep(interval_seconds)

        cls._monitor_thread = threading.Thread(target=loop, daemon=True)
        cls._monitor_thread.start()

    @classmethod
    def stop_monitoring(cls):
        cls._is_monitoring = False
