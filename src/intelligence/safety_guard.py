"""
VoiceMate Intelligence - Safety and Permission Guard Module.
Enforces safety gates, confirmation protocols, and blocks unverified destructive actions
such as file deletion, messaging, purchases, and dangerous shell execution.
"""
from typing import Dict, Any, Tuple, Optional
import re


class SafetyGuard:
    """
    Validates actions against security policies and prompts for confirmation
    before allowing potentially destructive operations.
    """
    DESTRUCTIVE_PATTERNS = [
        (r"(delete|remove|মুছে ফেলো|ডিলিট করো|বাতিল করো)\s+(file|folder|ফাইল|ফোল্ডার|ডকুমেন্ট)", "ফাইল বা ফোল্ডার ডিলিট করার অনুমতি প্রয়োজন"),
        (r"(send|পাঠাও)\s+(sms|message|মেসেজ|ইমেইল|email)", "মেসেজ পাঠানোর পূর্বে নিশ্চিত হওয়া প্রয়োজন"),
        (r"(buy|purchase|pay|কেনাকাটা|পেমেন্ট|টাকা পাঠাও)", "আর্থিক লেনদেন বা কেনাকাটার জন্য অনুমতি প্রয়োজন"),
        (r"(format|rmdir|rm\s+-rf|del\s+/f|shutdown\s+-s|restart)", "সিস্টেম সংক্রান্ত ঝুঁকিপূর্ণ কমান্ড ব্লকিং নীতি কার্যকর রয়েছে")
    ]

    DANGEROUS_SHELL_KEYWORDS = [
        "format ", "rmdir /s", "del /f", "del /s", "rm -rf", "drop table", "shutdown /s", "poweroff"
    ]

    @classmethod
    def check_safety(cls, intent_name: str, action: str, parameters: Dict[str, Any], query_text: str = "") -> Tuple[bool, Optional[str]]:
        """
        Evaluates whether an action requires explicit user confirmation or must be blocked.
        Returns: (is_safe_to_execute_immediately, prompt_if_needs_confirmation)
        """
        q = (query_text or "").lower()

        # 1. Block outright hazardous commands
        for dangerous in cls.DANGEROUS_SHELL_KEYWORDS:
            if dangerous in q:
                return False, "নিরাপত্তা সতর্কবার্তা: এই কমান্ডটি ঝুঁকিপূর্ণ হওয়ায় ভয়েস মেট এটি কার্যকর করবে না।"

        # 2. Check destructive action patterns requiring user confirmation
        for pattern, reason in cls.DESTRUCTIVE_PATTERNS:
            if re.search(pattern, q):
                prompt = f"সতর্কতা: {reason}। আপনি কি সত্যিই কাজটি করতে চান? নিশ্চিত করতে 'হ্যাঁ' বা বাতিল করতে 'না' বলুন।"
                return False, prompt

        # 3. Explicit check for delete/purchase in parameters
        if action in ["delete_file", "delete_folder", "send_sms", "send_email", "make_payment"]:
            prompt = f"সতর্কতা: '{action}' কার্যকর করার পূর্বে আপনার সম্মতি প্রয়োজন। আপনি কি এটি করতে চান? 'হ্যাঁ' অথবা 'না' বলুন।"
            return False, prompt

        return True, None
