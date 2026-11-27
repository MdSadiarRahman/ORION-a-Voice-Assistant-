"""Playwright actions for media playback, web navigation, and screenshots."""

import re
import threading
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urlparse

from config import PLAYWRIGHT_PROFILES_DIR, PLAYWRIGHT_SCREENSHOTS_DIR
from src.helpers.search_helper import SearchHelper
from src.intelligence.intent_engine import IntentEngine
from src.playwright_agent.playwright_config import get_playwright_settings
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent


class PlaywrightController:
    _persistent_contexts: list[Any] = []
    _persistent_playwrights: list[Any] = []
    _persistent_lock = threading.Lock()

    @staticmethod
    def parse_task(task: str) -> dict[str, str]:
        text = (task or "").strip()
        lower = text.lower()
        url_match = re.search(r"https?://[^\s]+", text)
        url = url_match.group(0).rstrip(".,)") if url_match else ""

        if any(word in lower for word in ("স্ক্রিনশট", "screenshot")):
            return {"action": "screenshot", "url": url, "query": text}
        if "হোয়াটসঅ্যাপ ওয়েব" in lower or "whatsapp web" in lower:
            return {"action": "persistent_session", "url": "https://web.whatsapp.com", "query": text}
        if any(word in lower for word in (
            "গান", "সংগীত", "গীতি", "song", "music", "ভিডিও", "video",
            "প্লে", "বাজাও", "চালাও", "play ",
        )):
            return {
                "action": "play_youtube",
                "query": IntentEngine.extract_song_title(text) or "বাংলা গান",
            }
        if url:
            return {"action": "open_website", "url": url, "query": text}
        return {"action": "search_web", "query": text}

    @classmethod
    def execute_task(cls, task: str) -> dict[str, Any]:
        parsed = cls.parse_task(task)
        action = parsed["action"]
        if action == "screenshot" and not parsed.get("url"):
            return {
                "success": False,
                "action": action,
                "message": "স্ক্রিনশটের জন্য একটি ওয়েবসাইট URL দিন।",
            }

        try:
            from playwright.sync_api import sync_playwright

            settings = get_playwright_settings()
            if action == "persistent_session":
                return cls._open_persistent_session(sync_playwright, settings, parsed["url"])

            with sync_playwright() as playwright:
                browser_type = getattr(playwright, settings["default_browser"])
                browser = browser_type.launch(
                    headless=settings["headless"],
                    slow_mo=settings["slow_mo_ms"],
                )
                try:
                    page = browser.new_page()
                    page.set_default_timeout(settings["timeout_ms"])
                    result = cls._run_page_action(page, action, parsed)
                    return result
                finally:
                    browser.close()
        except Exception as exc:
            if action == "play_youtube":
                return PlaywrightFallbackAgent.play_youtube_video(parsed["query"])
            if action == "open_website":
                return PlaywrightFallbackAgent.open_website(parsed["url"])
            if action == "search_web":
                return PlaywrightFallbackAgent.search_web(parsed["query"])
            return {
                "success": False,
                "action": action,
                "message": f"Playwright কাজটি সম্পন্ন করতে পারেনি: {exc}",
            }

    @classmethod
    def _open_persistent_session(cls, sync_playwright: Any, settings: dict, url: str) -> dict[str, Any]:
        playwright = sync_playwright().start()
        try:
            browser_type = getattr(playwright, settings["default_browser"])
            profile_dir = PLAYWRIGHT_PROFILES_DIR / "whatsapp"
            profile_dir.mkdir(parents=True, exist_ok=True)
            context = browser_type.launch_persistent_context(
                user_data_dir=str(profile_dir),
                headless=settings["headless"],
                slow_mo=settings["slow_mo_ms"],
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.set_default_timeout(settings["timeout_ms"])
            page.goto(url, wait_until="domcontentloaded")
            with cls._persistent_lock:
                cls._persistent_playwrights.append(playwright)
                cls._persistent_contexts.append(context)
            return {
                "success": True,
                "action": "persistent_session",
                "url": url,
                "message": "WhatsApp Web persistent browser session খোলা হয়েছে।",
            }
        except Exception:
            playwright.stop()
            raise

    @staticmethod
    def _run_page_action(page: Any, action: str, parsed: dict[str, str]) -> dict[str, Any]:
        if action == "play_youtube":
            watch_url, title = SearchHelper.resolve_youtube_watch_url(parsed["query"])
            page.goto(watch_url, wait_until="domcontentloaded")
            if "watch?v=" not in watch_url:
                return {
                    "success": False,
                    "action": action,
                    "url": watch_url,
                    "message": f"'{title}'-এর ভিডিও লিংক পাওয়া যায়নি; YouTube search খোলা হয়েছে।",
                }
            return {
                "success": True,
                "action": action,
                "url": watch_url,
                "title": title,
                "message": f"ইউটিউবে '{title}' খোলা হয়েছে।",
            }

        if action == "screenshot":
            url = parsed["url"]
            page.goto(url, wait_until="domcontentloaded")
            host = urlparse(url).hostname or "website"
            safe_host = re.sub(r"[^A-Za-z0-9.-]+", "_", host)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = PLAYWRIGHT_SCREENSHOTS_DIR / f"{safe_host}_{timestamp}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            return {
                "success": True,
                "action": action,
                "url": url,
                "screenshot_path": str(screenshot_path.resolve()),
                "message": f"ওয়েবসাইটের screenshot সেভ হয়েছে: {screenshot_path.name}",
            }

        if action == "open_website":
            page.goto(parsed["url"], wait_until="domcontentloaded")
            return {
                "success": True,
                "action": action,
                "url": parsed["url"],
                "title": page.title(),
                "message": f"ওয়েবসাইট খোলা হয়েছে: {page.title() or parsed['url']}",
            }

        query = parsed["query"].strip()
        url = "https://www.google.com/search?q=" + quote_plus(query)
        page.goto(url, wait_until="domcontentloaded")
        return {
            "success": True,
            "action": "search_web",
            "url": url,
            "title": page.title(),
            "message": f"ওয়েব সার্চ খোলা হয়েছে: {query}",
        }
