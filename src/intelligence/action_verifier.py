"""
VoiceMate Intelligence - Action Verification Module.
Ensures the agent verifies the outcome of browser navigations, media playback,
and system tasks before reporting success to the user.
"""
from typing import Tuple, Dict, Any, Optional
import urllib.parse


class ActionVerifier:
    """
    Verifies execution results across browser, desktop, and multimedia actions.
    Ensures VoiceMate never pretends an action succeeded when it failed.
    """

    @classmethod
    def verify_youtube_playback(
        cls,
        watch_url: str,
        title: str,
        playback_verified: bool = False,
    ) -> Tuple[bool, str]:
        """
        Confirms playback only when the browser reported active video playback.
        """
        if not watch_url:
            return False, "ইউটিউবে ভিডিও খুঁজে পাওয়া যায়নি বা নেটওয়ার্কে সমস্যা হয়েছে।"

        if "watch?v=" not in watch_url:
            if "results?search_query=" in watch_url:
                return False, f"ইউটিউবে '{title}'-এর search results খোলা হয়েছে, কিন্তু playback নিশ্চিত হয়নি।"
            return False, "ইউটিউব পেজটি লোড করা সম্ভব হয়নি।"
        if not playback_verified:
            return False, f"ইউটিউবে '{title}'-এর ভিডিও পেজ খোলা হয়েছে, কিন্তু playback নিশ্চিত হয়নি।"
        return True, f"ইউটিউবে '{title}' সফলভাবে চালু হয়েছে এবং বাজছে।"

    @classmethod
    def verify_app_launch(cls, app_name: str, launch_result_msg: str) -> Tuple[bool, str]:
        """
        Checks whether an application launch command succeeded.
        """
        if "খুঁজে পাওয়া যায়নি" in launch_result_msg or "ব্যর্থ" in launch_result_msg:
            return False, f"দুঃখিত, '{app_name}' অ্যাপ্লিকেশনটি কম্পিউটারে খুঁজে পাওয়া যায়নি।"
        return True, launch_result_msg

    @classmethod
    def verify_media_action(cls, action_name: str, success: bool, detail: str = "") -> Tuple[bool, str]:
        """
        Validates hardware multimedia key execution.
        """
        if not success:
            return False, f"মিডিয়া নিয়ন্ত্রণ '{action_name}' কার্যকর করা সম্ভব হয়নি।"
        return True, detail or f"মিডিয়া '{action_name}' সফল হয়েছে।"
