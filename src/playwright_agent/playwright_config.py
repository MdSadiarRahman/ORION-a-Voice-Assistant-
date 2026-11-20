"""
Configuration and Environment Discovery for Playwright Browser Automation.
Supports local repo integration and installed package fallback.
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any

from config import (
    PLAYWRIGHT_REPO_DIR,
    PLAYWRIGHT_PROFILES_DIR,
    PLAYWRIGHT_SCREENSHOTS_DIR,
    PLAYWRIGHT_DEFAULT_BROWSER,
    PLAYWRIGHT_HEADLESS,
    PLAYWRIGHT_TIMEOUT_MS,
    PLAYWRIGHT_SLOW_MO_MS,
)

# Ensure playwright repo is in sys.path if present
if PLAYWRIGHT_REPO_DIR.exists() and str(PLAYWRIGHT_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(PLAYWRIGHT_REPO_DIR))


def is_playwright_installed() -> bool:
    """
    Checks if Playwright and its required greenlet runtime are available.
    """
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except (ImportError, ModuleNotFoundError, Exception):
        return False


def get_playwright_settings() -> Dict[str, Any]:
    """
    Returns active Playwright configuration dictionary.
    """
    return {
        "repo_path": str(PLAYWRIGHT_REPO_DIR),
        "repo_exists": PLAYWRIGHT_REPO_DIR.exists(),
        "is_installed": is_playwright_installed(),
        "default_browser": PLAYWRIGHT_DEFAULT_BROWSER,
        "headless": PLAYWRIGHT_HEADLESS,
        "timeout_ms": PLAYWRIGHT_TIMEOUT_MS,
        "slow_mo_ms": PLAYWRIGHT_SLOW_MO_MS,
        "profiles_dir": str(PLAYWRIGHT_PROFILES_DIR),
        "screenshots_dir": str(PLAYWRIGHT_SCREENSHOTS_DIR),
    }
