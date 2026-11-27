import sys
import types
import unittest
from unittest.mock import patch

from src.helpers.media_controller import MediaController
from src.helpers.search_helper import SearchHelper
from src.intelligence.action_verifier import ActionVerifier
from src.playwright_agent.playwright_controller import PlaywrightController
from src.playwright_agent.playwright_fallback import PlaywrightFallbackAgent
from src.playwright_agent.playwright_task_runner import PlaywrightTaskRunner


class FakeLocator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector
        self.first = self

    def wait_for(self, **_kwargs):
        return None

    def evaluate(self, _script):
        if self.selector == "video":
            return {
                "playing": self.page.playing,
                "muted": self.page.muted,
                "volume": 1.0,
            } if "{playing:" in _script else self.page.playing
        return None

    def is_visible(self):
        return self.selector == "button.ytp-large-play-button"

    def click(self, **_kwargs):
        if self.selector == "button.ytp-large-play-button":
            self.page.playing = True


class FakePage:
    def __init__(self):
        self.playing = False
        self.muted = False
        self.url = ""

    def set_default_timeout(self, _timeout):
        return None

    def goto(self, url, **_kwargs):
        self.url = url

    def locator(self, selector):
        return FakeLocator(self, selector)

    def wait_for_function(self, _script, **_kwargs):
        if not self.playing:
            raise TimeoutError("Video did not start.")


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

    @patch.object(
        PlaywrightController,
        "play_youtube_and_verify",
        return_value={"success": True, "message": "playing"},
    )
    def test_play_music_task_uses_persistent_player(self, play_song):
        result = PlaywrightController.execute_task("Play Kamariya song")

        self.assertTrue(result["success"])
        play_song.assert_called_once_with("Kamariya")

    @patch.object(
        SearchHelper,
        "resolve_youtube_watch_url",
        return_value=("https://www.youtube.com/watch?v=abcdefghijk", "Test Song"),
    )
    def test_youtube_player_clicks_and_verifies_actual_playback(self, _resolve):
        page = FakePage()

        result = PlaywrightController._play_youtube_on_page(page, "Test Song", 1000)

        self.assertTrue(result["success"])
        self.assertTrue(page.playing)
        self.assertIn("watch?v=abcdefghijk", result["url"])

    @patch.object(
        SearchHelper,
        "resolve_youtube_watch_url",
        return_value=("https://www.youtube.com/watch?v=abcdefghijk", "Test Song"),
    )
    def test_persistent_music_worker_keeps_browser_open_after_playback(self, _resolve):
        page = FakePage()

        class FakeContext:
            pages = [page]

            def new_page(self):
                return page

        class FakeBrowserType:
            def launch_persistent_context(self, **_kwargs):
                return FakeContext()

        class FakePlaywright:
            chromium = FakeBrowserType()

        class FakePlaywrightManager:
            def __enter__(self):
                return FakePlaywright()

            def __exit__(self, *_args):
                return None

        fake_sync_api = types.ModuleType("playwright.sync_api")
        fake_sync_api.sync_playwright = FakePlaywrightManager

        with patch.dict(sys.modules, {"playwright.sync_api": fake_sync_api}):
            try:
                result = PlaywrightController.play_youtube_and_verify("Test Song")
                self.assertTrue(result["success"], result)
                self.assertTrue(page.playing)
                self.assertTrue(PlaywrightController._music_worker.is_alive())
            finally:
                PlaywrightController.close_music_player()

    @patch.object(
        PlaywrightController,
        "play_youtube_and_verify",
        return_value={
            "success": False,
            "title": "Test Song",
            "url": "https://www.youtube.com/watch?v=abcdefghijk",
            "message": "playback blocked",
        },
    )
    def test_media_controller_does_not_claim_failed_playback(self, play_song):
        old_state = (
            MediaController._current_title,
            MediaController._current_url,
            MediaController._is_playing,
            MediaController._last_playback_time,
        )
        try:
            MediaController._current_title = None
            MediaController._current_url = None
            MediaController._is_playing = False
            MediaController._last_playback_time = 0

            success, _title, message, _url = MediaController.play_youtube("Test Song")

            self.assertFalse(success)
            self.assertEqual(message, "playback blocked")
            self.assertFalse(MediaController.get_playback_status()["is_playing"])
            play_song.assert_called_once_with("Test Song")
        finally:
            (
                MediaController._current_title,
                MediaController._current_url,
                MediaController._is_playing,
                MediaController._last_playback_time,
            ) = old_state

    @patch.object(
        PlaywrightController,
        "play_youtube_and_verify",
        side_effect=RuntimeError("browser startup failed"),
    )
    def test_media_controller_reports_player_exceptions(self, _play_song):
        success, _title, message, url = MediaController.play_youtube("Test Song")

        self.assertFalse(success)
        self.assertIn("browser startup failed", message)
        self.assertEqual(url, "")

    def test_search_results_are_not_verified_as_playback(self):
        verified, message = ActionVerifier.verify_youtube_playback(
            "https://www.youtube.com/results?search_query=song",
            "song",
        )

        self.assertFalse(verified)
        self.assertIn("playback", message)

    @patch("src.helpers.search_helper.webbrowser.open", return_value=True)
    @patch.object(
        SearchHelper,
        "resolve_youtube_watch_url",
        return_value=("https://www.youtube.com/watch?v=abcdefghijk", "Test Song"),
    )
    def test_browser_only_fallback_never_claims_playback(self, _resolve, open_browser):
        success, _title, message, _url = SearchHelper.play_youtube_song("Test Song")

        self.assertFalse(success)
        self.assertIn("যাচাই", message)
        open_browser.assert_called_once()

    @patch("src.helpers.search_helper.webbrowser.open", side_effect=RuntimeError("browser unavailable"))
    @patch.object(
        SearchHelper,
        "resolve_youtube_watch_url",
        return_value=("https://www.youtube.com/watch?v=abcdefghijk", "Test Song"),
    )
    def test_browser_fallback_failure_is_reported(self, _resolve, _open_browser):
        success, _title, message, _url = SearchHelper.play_youtube_song("Test Song")

        self.assertFalse(success)
        self.assertIn("browser fallback-ও ব্যর্থ হয়েছে", message)

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
