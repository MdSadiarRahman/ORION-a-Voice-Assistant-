"""
Background Task Runner and Command Dispatcher for Playwright Web Automation.
Ensures browser actions run asynchronously without freezing the UI or voice engine.
"""
import re
import threading
from typing import Callable, Optional, Dict, Any

from src.playwright_agent.playwright_controller import PlaywrightController
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent


class PlaywrightTaskRunner:
    """
    Manages non-blocking execution of deterministic Playwright tasks.
    """

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """
        Parses and executes a web automation task in a background thread.
        """
        def _worker():
            try:
                if on_progress:
                    on_progress("⚡ ওয়েব অটোমেশন শুরু হচ্ছে...")

                result = cls._parse_and_execute(task_query, on_progress)
                message = result.get("message", "টাস্ক সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(message)

            except Exception as e:
                err_msg = f"অটোমেশনে ত্রুটি: {str(e)}"
                if on_finish:
                    on_finish(err_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    @classmethod
    def _parse_and_execute(
        cls,
        query: str,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Interprets natural language queries into specific Playwright automation routines.
        """
        q = query.lower().strip()

        # 1. Screenshot Task
        screenshot_keywords = ["স্ক্রিনশট", "screenshot", "ক্যাপচার", "capture"]
        if any(kw in q for kw in screenshot_keywords):
            # Extract URL if present
            url_match = re.search(r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', query)
            url = url_match.group(0) if url_match else "https://www.google.com"
            if on_progress:
                on_progress(f"📸 {url} এর স্ক্রিনশট নেওয়া হচ্ছে...")
            return PlaywrightController.capture_screenshot(url)

        # 2. Persistent Web Session (WhatsApp Web, Facebook, etc.)
        session_keywords = ["হোয়াটসঅ্যাপ", "whatsapp", "ওয়েব সেশন", "persistent session", "লগইন সেশন"]
        if any(kw in q for kw in session_keywords):
            url = "https://web.whatsapp.com"
            if "facebook" in q:
                url = "https://www.facebook.com"
            if on_progress:
                on_progress(f"🔐 পারসিস্টেন্ট সেশন খোলা হচ্ছে: {url}")
            return PlaywrightController.open_persistent_session(url)

        # 3. YouTube Media Playback
        media_keywords = [
            "প্লে করো", "প্লে", "চালাও", "বাজাও", "play", "ভিডিও", "গান",
            "সং", "song", "শোনাও", "ছাড়ো", "শুনবো", "মিউজিক", "music"
        ]
        if any(kw in q for kw in media_keywords) or "youtube" in q or "ইউটিউব" in q:
            clean_query = query
            to_remove = [
                "একটি গান প্লে করো", "একটি গান চালাও", "একটি গান বাজাও", "একটি গান শোনাও",
                "গান প্লে করো", "ভিডিও প্লে করো", "ভিডিও চালাও", "গান বাজাও", "গান চালাও",
                "গান শোনাও", "গান ছাড়ো", "গান শুনবো", "সং প্লে করো", "সং চালাও", "সং বাজাও",
                "প্লে করো", "ইউটিউবে", "ইউটিউব", "play song", "play music", "play video",
                "একটি গান", "একটি সং", "প্লে", "play", "চালাও", "বাজাও", "শোনাও", "ছাড়ো",
                "শুনবো", "করো", "করুন", "দাও"
            ]
            for kw in sorted(to_remove, key=len, reverse=True):
                clean_query = re.sub(rf"(^|[^\w\u0980-\u09FF]){re.escape(kw)}($|[^\w\u0980-\u09FF])", " ", clean_query, flags=re.IGNORECASE)

            clean_query = re.sub(r"\s+", " ", clean_query).strip()
            # If nothing specific was requested, play top popular songs
            if not clean_query or clean_query in ["গান", "সং", "song", "video"]:
                clean_query = "bangla top song"

            if on_progress:
                on_progress(f"🎵 ইউটিউবে '{clean_query}' প্লে করা হচ্ছে...")
            return PlaywrightController.play_youtube_video(clean_query)

        # 4. Search & Scrape
        if on_progress:
            on_progress(f"🔍 '{query}' নিয়ে তথ্য সংগ্রহ করা হচ্ছে...")
        return PlaywrightController.search_and_scrape(query)
