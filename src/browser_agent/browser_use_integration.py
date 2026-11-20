"""
VoiceMate Laptop Agent - Browser-Use 1.0 Autonomous Agent Integration.
Directly interfaces with browser-use repository architecture (Pydantic AI + REPL + CDP).
"""
import asyncio
import os
import logging
from typing import Optional, Callable
from src.browser_agent.browser_config import is_browser_use_available, get_browser_settings
from src.browser_agent.browser_fallback import BrowserFallbackAgent

logger = logging.getLogger(__name__)

class BrowserUseAgent:
    """
    Autonomous Web Agent powered by Browser-Use 1.0.
    Executes multi-step web browsing tasks using the Chrome DevTools Protocol and Accessibility Tree.
    """

    def __init__(self, on_progress: Optional[Callable[[str], None]] = None):
        self.on_progress = on_progress
        self.settings = get_browser_settings()

    def _log_progress(self, msg: str):
        if self.on_progress:
            try:
                self.on_progress(msg)
            except Exception:
                pass
        print(f"[BrowserAgent]: {msg}")

    async def run_task(self, task: str) -> str:
        """
        Executes an autonomous web task asynchronously.
        Adheres to Browser-Use 1.0 specifications.
        """
        self._log_progress(f"ব্রাউজার টাস্ক শুরু হচ্ছে: {task}")

        if not is_browser_use_available():
            self._log_progress("Browser-Use লাইব্রেরির ডিপেনডেন্সি পাওয়া যায়নি, ফলব্যাক ব্রাউজার রান করা হচ্ছে...")
            return BrowserFallbackAgent.execute_basic_task(task)

        try:
            from browser_use import Agent, Browser
            
            # Configure browser instance (Chrome / Chromium)
            browser_type = self.settings.get("browser_type", "chrome")
            headless = self.settings.get("headless", False)
            browser_instance = Browser(browser_type, headless=headless)

            # Initialize Agent with task
            agent = Agent(
                task=task,
                browser=browser_instance
            )

            self._log_progress("ব্রাউজার চালু হয়েছে, পেজ পর্যবেক্ষণ ও কাজ সম্পন্ন করা হচ্ছে...")
            result = await agent.run()
            
            final_ans = result.final_result()
            if final_ans:
                return f"ব্রাউজারের কাজ সফলভাবে সম্পন্ন হয়েছে:\n{final_ans}"
            return "ব্রাউজারের কাজ সম্পন্ন হয়েছে কিন্তু কোনো ফলাফল পাওয়া যায়নি।"

        except Exception as e:
            logger.error(f"Browser-Use execution error: {e}", exc_info=True)
            self._log_progress(f"স্বয়ংক্রিয় ব্রাউজিংয়ে ত্রুটি: {e}। ফলব্যাক সিস্টেমে পাঠানো হচ্ছে...")
            return BrowserFallbackAgent.execute_basic_task(task)

    def run_sync(self, task: str) -> str:
        """Synchronous wrapper for executing browser agent tasks."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # If already inside an existing event loop, run in a separate thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, self.run_task(task))
                return future.result()
        else:
            return loop.run_until_complete(self.run_task(task))
