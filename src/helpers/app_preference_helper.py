"""
VoiceMate Laptop Agent - App Preference Helper Module.
Manages user configurations, allowed/blocked applications, and preferences.
"""
import json
import os
from typing import Dict, Any
from config import PREFERENCES_FILE

class AppPreferenceHelper:
    @classmethod
    def _load_prefs(cls) -> Dict[str, Any]:
        if not os.path.exists(PREFERENCES_FILE):
            return {"allowed_apps": {}, "settings": {}}
        try:
            with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"allowed_apps": {}, "settings": {}}

    @classmethod
    def _save_prefs(cls, data: Dict[str, Any]) -> bool:
        try:
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    @classmethod
    def set_app_permission(cls, app_identifier: str, allowed: bool):
        prefs = cls._load_prefs()
        if "allowed_apps" not in prefs:
            prefs["allowed_apps"] = {}
        prefs["allowed_apps"][app_identifier.lower()] = allowed
        cls._save_prefs(prefs)

    @classmethod
    def is_app_allowed(cls, app_identifier: str) -> bool:
        prefs = cls._load_prefs()
        allowed_apps = prefs.get("allowed_apps", {})
        return allowed_apps.get(app_identifier.lower(), True)

    @classmethod
    def get_setting(cls, key: str, default: Any = None) -> Any:
        prefs = cls._load_prefs()
        return prefs.get("settings", {}).get(key, default)

    @classmethod
    def set_setting(cls, key: str, value: Any):
        prefs = cls._load_prefs()
        if "settings" not in prefs:
            prefs["settings"] = {}
        prefs["settings"][key] = value
        cls._save_prefs(prefs)
