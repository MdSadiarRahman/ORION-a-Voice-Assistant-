"""Playwright actions for media playback, web navigation, and screenshots."""

import atexit
import queue
import re
import threading
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus, urljoin, urlparse

from config import PLAYWRIGHT_PROFILES_DIR, PLAYWRIGHT_SCREENSHOTS_DIR
from src.helpers.search_helper import SearchHelper
from src.intelligence.intent_engine import IntentEngine
from src.playwright_agent.playwright_config import get_playwright_settings
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent


class PlaywrightController:
    _persistent_contexts: list[Any] = []
    _persistent_playwrights: list[Any] = []
    _persistent_lock = threading.Lock()
    _music_queue: queue.Queue = queue.Queue()
    _music_worker: threading.Thread | None = None
    _music_lock = threading.Lock()
    _music_atexit_registered = False

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
        if action == "play_youtube":
            try:
                return cls.play_youtube_and_verify(parsed["query"])
            except Exception as exc:
                return {
                    "success": False,
                    "action": action,
                    "message": f"YouTube playback চালু করা যায়নি: {exc}",
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
    def play_youtube_and_verify(cls, query: str) -> dict[str, Any]:
        task = {"query": query, "ready": threading.Event()}
        with cls._music_lock:
            if cls._music_worker is None or not cls._music_worker.is_alive():
                cls._music_queue = queue.Queue()
                cls._music_queue.put(task)
                cls._music_worker = threading.Thread(
                    target=cls._run_music_worker,
                    name="youtube-music-player",
                    daemon=True,
                )
                if not cls._music_atexit_registered:
                    atexit.register(cls.close_music_player)
                    cls._music_atexit_registered = True
                cls._music_worker.start()
            else:
                cls._music_queue.put(task)

        timeout = get_playwright_settings()["timeout_ms"] / 1000 + 15
        if not task["ready"].wait(timeout):
            return {
                "success": False,
                "action": "play_youtube",
                "message": "YouTube playback যাচাই করতে বেশি সময় লাগছে; গান চালু হয়েছে বলে নিশ্চিত করা যাচ্ছে না।",
            }
        return task["result"]

    @classmethod
    def close_music_player(cls) -> None:
        with cls._music_lock:
            worker = cls._music_worker
            if worker is None:
                return
            cls._music_queue.put(None)
        if worker is not threading.current_thread():
            worker.join(timeout=10)

    @classmethod
    def _run_music_worker(cls) -> None:
        try:
            from playwright.sync_api import sync_playwright

            settings = get_playwright_settings()
            profile_dir = PLAYWRIGHT_PROFILES_DIR / "music"
            profile_dir.mkdir(parents=True, exist_ok=True)
            with sync_playwright() as playwright:
                browser_type = getattr(playwright, settings["default_browser"])
                context = browser_type.launch_persistent_context(
                    user_data_dir=str(profile_dir),
                    headless=False,
                    slow_mo=settings["slow_mo_ms"],
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(settings["timeout_ms"])
                while True:
                    task = cls._music_queue.get()
                    if task is None:
                        break
                    try:
                        task["result"] = cls._play_youtube_on_page(
                            page,
                            task["query"],
                            settings["timeout_ms"],
                        )
                    except Exception as exc:
                        task["result"] = {
                            "success": False,
                            "action": "play_youtube",
                            "message": f"YouTube-এ গান চালানো যায়নি: {exc}",
                            "url": page.url,
                        }
                    finally:
                        task["ready"].set()
        except Exception as exc:
            with cls._music_lock:
                cls._fail_queued_music_tasks(exc)
        finally:
            with cls._music_lock:
                if cls._music_worker is threading.current_thread():
                    cls._music_worker = None

    @classmethod
    def _fail_queued_music_tasks(cls, error: Exception) -> None:
        while True:
            try:
                task = cls._music_queue.get_nowait()
            except queue.Empty:
                return
            if task is None:
                continue
            task["result"] = {
                "success": False,
                "action": "play_youtube",
                "message": f"Playwright browser চালু করা যায়নি: {error}",
            }
            task["ready"].set()

    @classmethod
    def _play_youtube_on_page(cls, page: Any, query: str, timeout_ms: int) -> dict[str, Any]:
        watch_url, title = SearchHelper.resolve_youtube_watch_url(query)
        if "watch?v=" not in watch_url:
            page.goto(watch_url, wait_until="domcontentloaded", timeout=timeout_ms)
            first_result = page.locator("ytd-video-renderer a#video-title").first
            first_result.wait_for(state="visible", timeout=timeout_ms)
            result_href = first_result.get_attribute("href")
            if not result_href:
                return {
                    "success": False,
                    "action": "play_youtube",
                    "url": watch_url,
                    "title": title,
                    "message": f"'{query}'-এর কোনো YouTube video result পাওয়া যায়নি।",
                }
            watch_url = urljoin("https://www.youtube.com", result_href)
            title = first_result.inner_text().strip() or title

        page.goto(watch_url, wait_until="domcontentloaded", timeout=timeout_ms)
        video = page.locator("video").first
        video.wait_for(state="attached", timeout=timeout_ms)
        if not video.evaluate("(element) => !element.paused && !element.ended"):
            large_play_button = page.locator("button.ytp-large-play-button").first
            if large_play_button.is_visible():
                large_play_button.click(timeout=5000)
            else:
                play_button = page.locator("button.ytp-play-button").first
                if play_button.is_visible():
                    play_button.click(timeout=5000)
                else:
                    video.click(timeout=5000)

        page.wait_for_function(
            """() => {
                const video = document.querySelector("video");
                return video && !video.paused && !video.ended && video.readyState >= 2;
            }""",
            timeout=timeout_ms,
        )
        video_state = video.evaluate(
            "(element) => ({playing: !element.paused && !element.ended, muted: element.muted, volume: element.volume})"
        )
        if video_state["muted"] or video_state["volume"] <= 0:
            mute_button = page.locator("button.ytp-mute-button").first
            if mute_button.is_visible():
                mute_button.click(timeout=5000)
            video.evaluate("(element) => { element.muted = false; if (element.volume === 0) element.volume = 1; }")
            video_state = video.evaluate(
                "(element) => ({playing: !element.paused && !element.ended, muted: element.muted, volume: element.volume})"
            )

        if not video_state["playing"] or video_state["muted"] or video_state["volume"] <= 0:
            return {
                "success": False,
                "action": "play_youtube",
                "url": page.url,
                "title": title,
                "message": f"'{title}'-এর ভিডিও খুলেছে, কিন্তু sound status যাচাই হয়নি।",
            }
        return {
            "success": True,
            "action": "play_youtube",
            "url": page.url,
            "title": title,
            "message": f"ইউটিউবে '{title}' চালু হয়েছে; ভিডিও চলছে এবং player mute নয়।",
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
            return PlaywrightController._play_youtube_on_page(
                page,
                parsed["query"],
                get_playwright_settings()["timeout_ms"],
            )

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
