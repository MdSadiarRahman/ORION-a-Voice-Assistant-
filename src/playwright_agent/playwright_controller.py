"""
Playwright Automation Controller for VoiceMate.
Implements Canonical Patterns A, B, and C:
- Pattern A: Synchronous Automation with Auto-waiting locators
- Pattern B: YouTube / Media Playback with interactive selectors
- Pattern C: Persistent Browser Context for saved logins / WhatsApp Web
- Pattern D: Headless Web Page Screenshots & Smart Text Scraping
"""
import time
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import (
    PLAYWRIGHT_PROFILES_DIR,
    PLAYWRIGHT_SCREENSHOTS_DIR,
    PLAYWRIGHT_DEFAULT_BROWSER,
    PLAYWRIGHT_HEADLESS,
    PLAYWRIGHT_TIMEOUT_MS,
    PLAYWRIGHT_SLOW_MO_MS,
)
from src.playwright_agent.playwright_config import is_playwright_installed
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent


class PlaywrightController:
    """
    High-level automation controller for web navigation, media playing,
    scraping, form filling, and persistent sessions.
    """

    @classmethod
    def is_available(cls) -> bool:
        """Returns True if Playwright driver is fully ready."""
        return is_playwright_installed()

    @classmethod
    def play_youtube_video(
        cls,
        query: str,
        autoplay: bool = True,
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Pattern B: Plays a video or music track on YouTube.
        Directly resolves the target video and opens it in the browser with autoplay.
        """
        from src.helpers.search_helper import SearchHelper
        success, title, msg, watch_url = SearchHelper.play_youtube_song(query)
        return {
            "success": success,
            "action": "play_youtube",
            "title": title,
            "query": query,
            "url": watch_url,
            "message": msg,
            "driver": "youtube_player"
        }

    @classmethod
    def search_and_scrape(
        cls,
        query: str,
        engine: str = "google",
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Pattern A: Searches Google or DuckDuckGo, captures results and screenshot.
        """
        if not cls.is_available():
            return PlaywrightFallbackAgent.search_web(query, engine=engine)

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser_type = getattr(p, PLAYWRIGHT_DEFAULT_BROWSER, p.chromium)
                browser = browser_type.launch(headless=headless, slow_mo=PLAYWRIGHT_SLOW_MO_MS)
                context = browser.new_context()
                page = context.new_page()

                if engine.lower() == "duckduckgo":
                    page.goto("https://duckduckgo.com", timeout=PLAYWRIGHT_TIMEOUT_MS)
                    search_box = page.locator("input[name='q'], input#searchbox_input").first
                else:
                    page.goto("https://www.google.com", timeout=PLAYWRIGHT_TIMEOUT_MS)
                    search_box = page.locator("textarea[name='q'], input[name='q']").first

                search_box.fill(query)
                search_box.press("Enter")

                page.wait_for_load_state("domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)

                # Extract top result titles
                results: List[str] = []
                headings = page.locator("h3").all()
                for h in headings[:5]:
                    txt = h.inner_text().strip()
                    if txt:
                        results.append(txt)

                # Save screenshot
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_file = PLAYWRIGHT_SCREENSHOTS_DIR / f"search_{timestamp}.png"
                page.screenshot(path=str(screenshot_file))

                browser.close()

                result_text = "\n".join(f"- {r}" for r in results) if results else "কোন নির্দিষ্ট ফলাফল পাওয়া যায়নি।"
                return {
                    "success": True,
                    "action": "search_scrape",
                    "query": query,
                    "results": results,
                    "screenshot": str(screenshot_file),
                    "message": f"সার্চ সম্পন্ন হয়েছে:\n{result_text}",
                    "driver": "playwright_sync"
                }
        except Exception as e:
            fallback_res = PlaywrightFallbackAgent.search_web(query, engine=engine)
            fallback_res["error"] = str(e)
            return fallback_res

    @classmethod
    def capture_screenshot(
        cls,
        url: str,
        output_path: Optional[str] = None,
        full_page: bool = True,
        headless: bool = True
    ) -> Dict[str, Any]:
        """
        Pattern D: Opens any web page and takes a full-page or viewport screenshot.
        """
        if not cls.is_available():
            return PlaywrightFallbackAgent.capture_screenshot(url, output_path)

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = PLAYWRIGHT_SCREENSHOTS_DIR / f"web_{timestamp}.png"
        else:
            output_file = Path(output_path)

        output_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser_type = getattr(p, PLAYWRIGHT_DEFAULT_BROWSER, p.chromium)
                browser = browser_type.launch(headless=headless)
                context = browser.new_context(viewport={"width": 1280, "height": 800})
                page = context.new_page()

                page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS)
                page.wait_for_load_state("domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT_MS)
                page.screenshot(path=str(output_file), full_page=full_page)
                browser.close()

                return {
                    "success": True,
                    "action": "screenshot",
                    "url": url,
                    "screenshot_path": str(output_file),
                    "message": f"ওয়েব পেজের স্ক্রিনশট সংরক্ষিত হয়েছে: {output_file.name}",
                    "driver": "playwright_sync"
                }
        except Exception as e:
            return {
                "success": False,
                "action": "screenshot",
                "url": url,
                "error": str(e),
                "message": f"স্ক্রিনশট গ্রহণে ব্যর্থ: {str(e)}",
                "driver": "playwright_sync"
            }

    @classmethod
    def open_persistent_session(
        cls,
        url: str = "https://web.whatsapp.com",
        profile_name: str = "default_user",
        headless: bool = False
    ) -> Dict[str, Any]:
        """
        Pattern C: Launches a persistent browser context to retain cookies,
        local storage, and active login sessions (e.g. WhatsApp Web).
        """
        if not cls.is_available():
            return PlaywrightFallbackAgent.open_persistent_session(url)

        profile_dir = PLAYWRIGHT_PROFILES_DIR / profile_name
        profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser_type = getattr(p, PLAYWRIGHT_DEFAULT_BROWSER, p.chromium)
                context = browser_type.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=headless,
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto(url, timeout=PLAYWRIGHT_TIMEOUT_MS)

                # Keep browser open for user interaction
                time.sleep(3)

                return {
                    "success": True,
                    "action": "persistent_session",
                    "url": url,
                    "profile_dir": str(profile_dir),
                    "message": f"পারসিস্টেন্ট ওয়েব সেশন চালু হয়েছে: {url}",
                    "driver": "playwright_sync"
                }
        except Exception as e:
            fallback_res = PlaywrightFallbackAgent.open_persistent_session(url)
            fallback_res["error"] = str(e)
            return fallback_res
