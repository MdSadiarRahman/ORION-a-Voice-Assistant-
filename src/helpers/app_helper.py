"""
VoiceMate Laptop Agent - App Helper Module.
Scans and launches installed desktop applications, Windows system shortcuts,
and common tools on the laptop.
"""
import os
import json
import shutil
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from typing import List
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
        "gmail": "https://mail.google.com",
        "জিমেইল": "https://mail.google.com",
        "google mail": "https://mail.google.com",
        "chatgpt": "https://chatgpt.com",
        "চ্যাটজিপিটি": "https://chatgpt.com",
        "messenger": "https://www.messenger.com",
        "telegram": "https://web.telegram.org",
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
        "visual studio code": "code",
        "কোড": "code",
        "paint": "mspaint.exe",
        "পেইন্ট": "mspaint.exe",
        "whatsapp": "https://web.whatsapp.com",
        "হোয়াটসঅ্যাপ": "https://web.whatsapp.com",
        "হোয়াটসঅ্যাপ": "https://web.whatsapp.com",
        "ম্যাসেঞ্জার": "https://www.messenger.com",
        "cmd": "cmd.exe",
        "কমান্ড": "cmd.exe",
        "spotify": "spotify",
        "গান": "spotify"
    }

    # Bengali / Banglish aliases -> canonical English app name for installed app matching
    APP_ALIASES = {
        "হোয়াটসঅ্যাপ": "whatsapp",
        "হোয়াটসঅ্যাপ": "whatsapp",
        "জিমেইল": "gmail",
        "গুগল মেইল": "gmail",
        "চ্যাটজিপিটি": "chatgpt",
        "ম্যাসেঞ্জার": "messenger",
        "টেলিগ্রাম": "telegram",
        "ভিএলসি": "vlc",
        "ওয়ার্ড": "word",
        "ওয়ার্ড": "word",
        "এক্সেল": "excel",
        "পাওয়ারপয়েন্ট": "powerpoint",
        "পাওয়ারপয়েন্ট": "powerpoint",
        "ডিসকর্ড": "discord",
        "জুম": "zoom",
        "স্পটিফাই": "spotify",
        "এজ": "microsoft edge",
        "মাইক্রোসফট এজ": "microsoft edge",
        "ফটোশপ": "photoshop",
        "ক্যালকুলেটর": "calculator",
        "নোটপ্যাড": "notepad",
        "পেইন্ট": "paint",
        "কোড": "visual studio code",
        "ভিএস কোড": "visual studio code",
        "ভয়েস কোড": "visual studio code",
        "ভয়েস কোড": "visual studio code",
        "অ্যান্টিগ্র্যাভিটি": "antigravity",
        "এন্টিগ্র্যাভিটি": "antigravity",
        "গুগল অ্যান্টিগ্র্যাভিটি": "antigravity",
        "vscode": "visual studio code",
        "vs code": "visual studio code",
        "voice code": "visual studio code",
        "visual studio code": "visual studio code",
        "chatgpt": "chatgpt",
        "gpt": "chatgpt",
        "gmail": "gmail",
        "google mail": "gmail",
        "messenger": "messenger",
        "facebook messenger": "messenger",
        "telegram": "telegram",
        "gravity": "antigravity",
        "google gravity": "antigravity",
        "antigravity": "antigravity",
        "anti gravity": "antigravity",
        "anti-gravity": "antigravity",
    }

    _apps_cache: List[AppInfo] = []
    _apps_cache_time: float = 0.0
    _CACHE_TTL: float = 120.0

    @classmethod
    def _get_start_apps(cls) -> List[AppInfo]:
        """Discovers all Windows Desktop & Microsoft Store/UWP/MSIX apps via Get-StartApps."""
        discovered: List[AppInfo] = []
        try:
            proc = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; Get-StartApps | ConvertTo-Json -Compress"
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10
            )
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = (item.get("Name") or "").strip()
                    app_id = (item.get("AppID") or "").strip()
                    if name and app_id:
                        discovered.append(AppInfo(name=name, target=f"shell:AppsFolder\\{app_id}"))
        except Exception:
            pass
        return discovered

    @classmethod
    def get_all_installed_apps(cls, force_refresh: bool = False) -> List[AppInfo]:
        """Discovers all installed Windows apps (Store/UWP, Start Menu, Desktop shortcuts, and common tools)."""
        now = time.time()
        if not force_refresh and cls._apps_cache and (now - cls._apps_cache_time < cls._CACHE_TTL):
            return cls._apps_cache

        apps: List[AppInfo] = []

        # 1. All StartApps (includes Microsoft Store / MSIX apps like WhatsApp, Telegram, etc.)
        apps.extend(cls._get_start_apps())

        # 2. Start Menu & Desktop .lnk shortcuts
        scan_dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%USERPROFILE%\Desktop"),
            os.path.expandvars(r"%PUBLIC%\Desktop"),
        ]

        for base_dir in scan_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        name = f[:-4]
                        full_path = os.path.join(root, f)
                        apps.append(AppInfo(name=name, target=full_path))

        # 3. Common Windows utilities fallback
        seen_targets = {a.target.lower() for a in apps}
        for name, cmd in cls.COMMON_WINDOWS_APPS.items():
            if cmd.lower() not in seen_targets:
                seen_targets.add(cmd.lower())
                apps.append(AppInfo(name=name.title(), target=cmd))

        unique_apps: List[AppInfo] = []
        names_seen = set()
        for app in apps:
            norm_name = app.name.lower()
            if norm_name not in names_seen:
                names_seen.add(norm_name)
                unique_apps.append(app)

        cls._apps_cache = sorted(unique_apps, key=lambda a: a.name.lower())
        cls._apps_cache_time = now
        return cls._apps_cache

    @classmethod
    def _launch_target(cls, target_cmd: str) -> bool:
        """Launches a shell:AppsFolder ID, .lnk file, URL, URI, or executable."""
        try:
            if target_cmd.startswith("shell:AppsFolder\\"):
                subprocess.Popen(["explorer.exe", target_cmd])
                return True
            if target_cmd.startswith("http://") or target_cmd.startswith("https://"):
                import webbrowser
                return bool(webbrowser.open(target_cmd))
            if target_cmd.startswith("start "):
                subprocess.Popen(target_cmd, shell=True)
                return True
            if os.path.exists(target_cmd):
                os.startfile(target_cmd)
                return True
            executable = target_cmd.split(None, 1)[0]
            if not shutil.which(executable):
                return False
            subprocess.Popen(target_cmd, shell=True)
            return True
        except Exception:
            return False

    @classmethod
    def open_app(cls, app_name_or_target: str) -> str:
        raw_target = unicodedata.normalize("NFC", app_name_or_target.lower().strip())
        target = cls.APP_ALIASES.get(raw_target, raw_target)

        if not AppPreferenceHelper.is_app_allowed(target):
            return "দুঃখিত, এই অ্যাপটি ওপেন করার অনুমতি দেওয়া হয়নি।"

        # 1. Search all installed applications first (StartApps / Store / Desktop / Start Menu)
        all_apps = cls.get_all_installed_apps()

        # Pass A: Exact match (excluding generic COMMON_WINDOWS_APPS URI fallbacks)
        for app in all_apps:
            app_lower = app.name.lower()
            if app_lower == target and not app.target.startswith("start "):
                if cls._launch_target(app.target):
                    disp = app_name_or_target if app_lower == raw_target else app.name
                    return f"{disp} ওপেন করা হচ্ছে"

        # Pass B: Word / substring match against real installed apps
        for app in all_apps:
            app_lower = app.name.lower()
            if app.target.startswith("start ") or app.target.startswith("http"):
                continue
            if target in app_lower or (len(app_lower) >= 3 and app_lower in target):
                if cls._launch_target(app.target):
                    return f"{app.name} ওপেন করা হচ্ছে"

        # 2. Fallback to COMMON_WINDOWS_APPS (system URIs / web apps)
        for key in (target, raw_target):
            if key in cls.COMMON_WINDOWS_APPS:
                cmd = cls.COMMON_WINDOWS_APPS[key]
                if cls._launch_target(cmd):
                    return f"{app_name_or_target} ওপেন করা হচ্ছে"

        return "দুঃখিত, আপনার ল্যাপটপে এই অ্যাপটি খুঁজে পাওয়া যায়নি"

    @classmethod
    def close_current_app(cls) -> str:
        return DesktopAutomationHelper.close_current_app()
