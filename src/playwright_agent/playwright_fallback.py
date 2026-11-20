"""
Graceful Fallback Automation for Playwright.
Used when Playwright browser binaries or greenlet are not installed.
Uses native Windows browser launching so user requests still succeed seamlessly.
"""
import webbrowser
import urllib.parse
from pathlib import Path
from typing import Dict, Any

from config import PLAYWRIGHT_SCREENSHOTS_DIR
from src.helpers.search_helper import SearchHelper


class PlaywrightFallbackAgent:
    """
    Fallback agent providing direct browser navigation and notification
    when full Playwright headless/headed drivers are initializing or missing.
    """

    @staticmethod
    def play_youtube_video(query: str) -> Dict[str, Any]:
        """
        Resolves direct playable YouTube video and opens it in default browser.
        """
        success, title, msg, watch_url = SearchHelper.play_youtube_song(query)
        return {
            "success": success,
            "action": "play_youtube",
            "query": query,
            "title": title,
            "url": watch_url,
            "message": msg,
            "driver": "fallback_webbrowser"
        }

    @staticmethod
    def search_web(query: str, engine: str = "google") -> Dict[str, Any]:
        """
        Opens search in system browser.
        """
        encoded = urllib.parse.quote(query.strip())
        if engine.lower() == "youtube":
            url = f"https://www.youtube.com/results?search_query={encoded}"
        else:
            url = f"https://www.google.com/search?q={encoded}"

        opened = webbrowser.open(url)
        return {
            "success": opened,
            "action": "search_web",
            "query": query,
            "url": url,
            "message": f"{engine.title()}-এ '{query}' সার্চ ওপেন করা হয়েছে।",
            "driver": "fallback_webbrowser"
        }

    @staticmethod
    def open_persistent_session(url: str = "https://web.whatsapp.com") -> Dict[str, Any]:
        """
        Opens session URL in browser.
        """
        opened = webbrowser.open(url)
        return {
            "success": opened,
            "action": "persistent_session",
            "url": url,
            "message": f"ওয়েব সেশন '{url}' ব্রাউজারে চালু করা হয়েছে।",
            "driver": "fallback_webbrowser"
        }

    @staticmethod
    def capture_screenshot(url: str, output_path: str = None) -> Dict[str, Any]:
        """
        Fallback when headless driver screenshot is not available.
        """
        target_path = Path(output_path) if output_path else PLAYWRIGHT_SCREENSHOTS_DIR / "fallback_info.txt"
        target_path.parent.mkdir(parents=True, exist_ok=True)

        info_text = (
            f"URL: {url}\n"
            "Full Playwright headless capture requires: pip install playwright && playwright install chromium\n"
        )
        try:
            target_path.write_text(info_text, encoding="utf-8")
        except Exception:
            pass

        return {
            "success": False,
            "action": "screenshot",
            "url": url,
            "path": str(target_path),
            "message": "ওয়েব স্ক্রিনশটের জন্য প্লে-রাইট ড্রাইভার প্রয়োজন (pip install playwright && playwright install chromium)।",
            "driver": "fallback"
        }

    @staticmethod
    def execute_generic(task_description: str) -> Dict[str, Any]:
        """
        Executes generic web task fallback.
        """
        return PlaywrightFallbackAgent.search_web(task_description, engine="google")
