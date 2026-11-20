"""
VoiceMate Laptop Agent - App Helper Module.
Scans and launches installed desktop applications, Windows system shortcuts,
and common tools on the laptop.
"""
import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional
from src.helpers.app_preference_helper import AppPreferenceHelper
from src.helpers.desktop_automation_helper import DesktopAutomationHelper

@dataclass
class AppInfo:
    name: str
    target: str

class AppHelper:
    COMMON_WINDOWS_APPS = {
        "notepad": "notepad.exe",
        "নোটপ্যাড": "notepad.exe",
        "calculator": "calc.exe",
        "ক্যালকুলেটর": "calc.exe",
        "হিসাব": "calc.exe",
        "chrome": "chrome",
        "গুগল": "https://www.google.com",
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "ইউটিউব": "https://www.youtube.com",
        "facebook": "https://www.facebook.com",
        "ফেসবুক": "https://www.facebook.com",
        "maps": "https://maps.google.com",
        "ম্যাপ": "https://maps.google.com",
        "settings": "start ms-settings:",
        "সেটিংস": "start ms-settings:",
        "camera": "start microsoft.windows.camera:",
        "ক্যামেরা": "start microsoft.windows.camera:",
        "store": "start ms-windows-store:",
        "প্লে স্টোর": "start ms-windows-store:",
        "স্টোর": "start ms-windows-store:",
        "gallery": "start ms-photos:",
        "গ্যালারি": "start ms-photos:",
        "explorer": "explorer.exe",
        "ফাইল": "explorer.exe",
        "মাই কম্পিউটার": "explorer.exe",
        "vscode": "code",
        "কোড": "code",
        "paint": "mspaint.exe",
        "পেইন্ট": "mspaint.exe",
        "whatsapp": "start whatsapp:",
        "হোয়াটসঅ্যাপ": "start whatsapp:",
        "messenger": "https://www.messenger.com",
        "ম্যাসেঞ্জার": "https://www.messenger.com",
        "cmd": "cmd.exe",
        "কমান্ড": "cmd.exe",
        "spotify": "spotify",
        "গান": "spotify"
    }

    @classmethod
    def get_all_installed_apps(cls) -> List[AppInfo]:
        """Discovers Windows Start Menu shortcuts and common utilities."""
        apps: List[AppInfo] = []
        seen = set()
        for name, cmd in cls.COMMON_WINDOWS_APPS.items():
            if cmd not in seen:
                seen.add(cmd)
                apps.append(AppInfo(name=name.title(), target=cmd))

        start_menu_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
        ]

        for base_dir in start_menu_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.endswith(".lnk"):
                        name = f[:-4]
                        full_path = os.path.join(root, f)
                        apps.append(AppInfo(name=name, target=full_path))

        unique_apps = []
        names_seen = set()
        for app in apps:
            norm_name = app.name.lower()
            if norm_name not in names_seen:
                names_seen.add(norm_name)
                unique_apps.append(app)

        return sorted(unique_apps, key=lambda a: a.name.lower())

    @classmethod
    def open_app(cls, app_name_or_target: str) -> str:
        target = app_name_or_target.lower().strip()

        if not AppPreferenceHelper.is_app_allowed(target):
            return "দুঃখিত, এই অ্যাপটি ওপেন করার অনুমতি দেওয়া হয়নি।"

        # 1. Match common apps dictionary
        if target in cls.COMMON_WINDOWS_APPS:
            cmd = cls.COMMON_WINDOWS_APPS[target]
            try:
                if cmd.startswith("http://") or cmd.startswith("https://"):
                    import webbrowser
                    webbrowser.open(cmd)
                    return f"{app_name_or_target} ওপেন করা হচ্ছে"
                elif cmd.startswith("start "):
                    subprocess.Popen(cmd, shell=True)
                    return f"{app_name_or_target} ওপেন করা হচ্ছে"
                else:
                    subprocess.Popen(cmd, shell=True)
                    return f"{app_name_or_target} ওপেন করা হচ্ছে"
            except Exception:
                pass

        # 2. Match installed applications
        all_apps = cls.get_all_installed_apps()
        for app in all_apps:
            if target == app.name.lower() or target in app.name.lower() or app.name.lower() in target:
                try:
                    os.startfile(app.target)
                    return f"{app.name} ওপেন করা হচ্ছে"
                except Exception:
                    try:
                        subprocess.Popen(app.target, shell=True)
                        return f"{app.name} ওপেন করা হচ্ছে"
                    except Exception:
                        pass

        return "দুঃখিত, আপনার ল্যাপটপে এই অ্যাপটি খুঁজে পাওয়া যায়নি"

    @classmethod
    def close_current_app(cls) -> str:
        return DesktopAutomationHelper.close_current_app()
