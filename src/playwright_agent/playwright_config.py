"""Configuration for deterministic Playwright automation."""

from config import (
    PLAYWRIGHT_DEFAULT_BROWSER,
    PLAYWRIGHT_HEADLESS,
    PLAYWRIGHT_PROFILES_DIR,
    PLAYWRIGHT_REPO_DIR,
    PLAYWRIGHT_SCREENSHOTS_DIR,
    PLAYWRIGHT_SLOW_MO_MS,
    PLAYWRIGHT_TIMEOUT_MS,
)


def get_playwright_settings() -> dict:
    return {
        "default_browser": PLAYWRIGHT_DEFAULT_BROWSER,
        "headless": PLAYWRIGHT_HEADLESS,
        "timeout_ms": PLAYWRIGHT_TIMEOUT_MS,
        "slow_mo_ms": PLAYWRIGHT_SLOW_MO_MS,
        "repo_path": str(PLAYWRIGHT_REPO_DIR),
        "profiles_dir": str(PLAYWRIGHT_PROFILES_DIR),
        "screenshots_dir": str(PLAYWRIGHT_SCREENSHOTS_DIR),
    }
