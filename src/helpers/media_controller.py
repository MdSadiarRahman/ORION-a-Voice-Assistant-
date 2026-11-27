"""
VoiceMate Laptop Agent - Media and System Audio Controller.
Provides hardware-level multimedia key events, YouTube playback tracking,
volume modulation, and playback state inspection on Windows.
"""
import ctypes
import time
from typing import Dict, Any, Optional, Tuple
from src.helpers.search_helper import SearchHelper

# Windows Virtual Key Codes for Multimedia and Audio
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001


class MediaController:
    """
    Controls desktop multimedia playback, global Windows volume,
    and YouTube media sessions.
    """
    _current_title: Optional[str] = None
    _current_url: Optional[str] = None
    _is_playing: bool = False
    _last_playback_time: float = 0.0

    @classmethod
    def _send_media_key(cls, vk_code: int):
        """Sends a hardware multimedia virtual key event."""
        try:
            user32 = ctypes.windll.user32
            user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
            time.sleep(0.04)
            user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
            return True
        except Exception:
            return False

    @classmethod
    def play_youtube(cls, song_name: str) -> Tuple[bool, str, str, str]:
        """
        Starts the selected YouTube video in a visible persistent browser and verifies playback.
        Returns: (success, video_title, message, watch_url)
        """
        try:
            from src.playwright_agent.playwright_controller import PlaywrightController
        except ImportError:
            return SearchHelper.play_youtube_song(song_name)

        try:
            result = PlaywrightController.play_youtube_and_verify(song_name)
        except Exception as exc:
            return False, song_name, f"YouTube playback চালু করা যায়নি: {exc}", ""
        success = bool(result.get("success"))
        title = str(result.get("title") or song_name)
        msg = str(result.get("message") or "ইউটিউব playback যাচাই করা যায়নি।")
        watch_url = str(result.get("url") or "")
        if success:
            cls._current_title = title
            cls._current_url = watch_url
            cls._is_playing = True
            cls._last_playback_time = time.time()
        return success, title, msg, watch_url

    @classmethod
    def pause(cls) -> Tuple[bool, str]:
        """Pauses currently playing media."""
        cls._send_media_key(VK_MEDIA_PLAY_PAUSE)
        cls._is_playing = False
        msg = "ভিডিও বা গান সাময়িকভাবে পজ (Pause) করা হয়েছে।"
        return True, msg

    @classmethod
    def resume(cls) -> Tuple[bool, str]:
        """Resumes paused media."""
        cls._send_media_key(VK_MEDIA_PLAY_PAUSE)
        cls._is_playing = True
        msg = "প্লেব্যাক পুনরায় চালু (Resume) করা হয়েছে।"
        return True, msg

    @classmethod
    def stop(cls) -> Tuple[bool, str]:
        """Stops media playback."""
        cls._send_media_key(VK_MEDIA_STOP)
        cls._is_playing = False
        msg = "মিডিয়া প্লেব্যাক বন্ধ করা হয়েছে।"
        return True, msg

    @classmethod
    def next_track(cls) -> Tuple[bool, str]:
        """Skips to the next video or track."""
        cls._send_media_key(VK_MEDIA_NEXT_TRACK)
        msg = "পরবর্তী গানে যাওয়া হচ্ছে।"
        return True, msg

    @classmethod
    def previous_track(cls) -> Tuple[bool, str]:
        """Returns to the previous track."""
        cls._send_media_key(VK_MEDIA_PREV_TRACK)
        msg = "পূর্ববর্তী গানে ফিরে যাওয়া হচ্ছে।"
        return True, msg

    @classmethod
    def volume_up(cls, steps: int = 5) -> Tuple[bool, str]:
        """Increases system volume."""
        for _ in range(max(1, steps)):
            cls._send_media_key(VK_VOLUME_UP)
            time.sleep(0.02)
        return True, "ভলিউম বাড়ানো হয়েছে।"

    @classmethod
    def volume_down(cls, steps: int = 5) -> Tuple[bool, str]:
        """Decreases system volume."""
        for _ in range(max(1, steps)):
            cls._send_media_key(VK_VOLUME_DOWN)
            time.sleep(0.02)
        return True, "ভলিউম কমানো হয়েছে।"

    @classmethod
    def toggle_mute(cls) -> Tuple[bool, str]:
        """Mutes or unmutes system audio."""
        cls._send_media_key(VK_VOLUME_MUTE)
        return True, "সাউন্ড মিউট/আনমিউট টগল করা হয়েছে।"

    @classmethod
    def get_playback_status(cls) -> Dict[str, Any]:
        """Returns current media playback metadata."""
        return {
            "title": cls._current_title,
            "url": cls._current_url,
            "is_playing": cls._is_playing,
            "elapsed_since_play": (time.time() - cls._last_playback_time) if cls._last_playback_time else 0
        }
