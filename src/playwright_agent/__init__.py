"""
Playwright Web Automation Subsystem for VoiceMate.
Provides deterministic browser actions, media playback, scraping, and persistent sessions.
"""
from src.playwright_agent.playwright_config import (
    get_playwright_settings,
    is_playwright_installed
)
from src.playwright_agent.playwright_controller import PlaywrightController
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent
from src.playwright_agent.playwright_task_runner import PlaywrightTaskRunner

__all__ = [
    "get_playwright_settings",
    "is_playwright_installed",
    "PlaywrightController",
    "PlaywrightFallbackAgent",
    "PlaywrightTaskRunner",
]
