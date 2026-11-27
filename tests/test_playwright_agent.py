import unittest
from unittest.mock import patch

from src.playwright_agent.playwright_controller import PlaywrightController
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent
from src.playwright_agent.playwright_task_runner import PlaywrightTaskRunner


class TestPlaywrightAgent(unittest.TestCase):
    def test_task_parsing_routes_media_and_screenshots(self):
        play = PlaywrightTaskRunner._parse_and_execute("ইউটিউবে নজরুলগীতি প্লে করো")
        screenshot = PlaywrightTaskRunner._parse_and_execute(
            "ওয়েব স্ক্রিনশট নাও https://github.com"
        )

        self.assertEqual(play["action"], "play_youtube")
        self.assertIn("নজরুলগীতি", play["query"])
        self.assertEqual(screenshot["action"], "screenshot")
        self.assertEqual(screenshot["url"], "https://github.com")

    @patch("src.playwright_agent.playwright_fallback.webbrowser.open", return_value=True)
    def test_fallback_reports_browser_open(self, open_browser):
        result = PlaywrightFallbackAgent.search_web("পাইথন প্রোগ্রামিং")

        self.assertTrue(result["success"])
        self.assertEqual(result["action"], "search_web")
        self.assertIn("google.com/search", result["url"])
        open_browser.assert_called_once()

    @patch.object(
        PlaywrightController,
        "execute_task",
        return_value={"success": True, "message": "স্ক্রিনশট সেভ হয়েছে।"},
    )
    def test_runner_reports_completion(self, execute_task):
        finished = []
        thread = PlaywrightTaskRunner.run_task("ওয়েব স্ক্রিনশট https://example.com", on_finish=finished.append)
        thread.join(timeout=2)

        self.assertFalse(thread.is_alive())
        self.assertEqual(finished, ["স্ক্রিনশট সেভ হয়েছে।"])
        execute_task.assert_called_once()


if __name__ == "__main__":
    unittest.main()
