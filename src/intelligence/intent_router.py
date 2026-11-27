"""
Rule-based IntentRouter for VoiceMate Advanced Hybrid Architecture.
Classifies ordinary user commands in Python without requiring an LLM.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class RoutedIntent:
    intent: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    source: str = "python_rules"


class IntentRouter:
    """Zero-cost, deterministic rule-based intent router."""

    SUPPORTED_INTENTS = {
        "GENERAL_GREETING",
        "GET_CURRENT_TIME",
        "GET_CURRENT_DATE",
        "OPEN_APPLICATION",
        "SEARCH_LOCAL_FILE",
        "READ_DOCUMENT",
        "OPEN_FILE",
        "CALCULATE",
        "GET_WEATHER",
        "WEB_SEARCH",
        "GENERAL_CHAT",
        "UNKNOWN_INTENT",
    }

    @classmethod
    def route(cls, text: str) -> RoutedIntent:
        raw = (text or "").strip()
        lower = raw.lower()

        # 1. GENERAL_GREETING
        if re.match(r"^(hello|hi|hey|good morning|good evening|হ্যালো|হাই|সালাম|আসসালামু আলাইকুম|কেমন আছো?|kemon acho|kemon acho?|assalamu alaikum)\b", lower):
            return RoutedIntent("GENERAL_GREETING", 0.95, {"text": raw})

        # 2. GET_CURRENT_TIME
        if any(k in lower for k in ["what time", "current time", "time is it", "কয়টা বাজে", "সময় কত", "এখন কয়টা"]):
            return RoutedIntent("GET_CURRENT_TIME", 0.95)

        # 3. GET_CURRENT_DATE
        if any(k in lower for k in ["what date", "today's date", "what day", "current date", "আজকের তারিখ", "আজ কি বার", "আজ কী বার"]):
            return RoutedIntent("GET_CURRENT_DATE", 0.95)

        # 4. CALCULATE (safe math expression detection)
        calc_match = re.search(r"(?:calculate|compute|what is|হিসাব)\s+([0-9\.\+\-\*\/×÷\(\)\s]+)", lower)
        if calc_match:
            expr = calc_match.group(1).replace("×", "*").replace("÷", "/").strip()
            return RoutedIntent("CALCULATE", 0.95, {"expression": expr})
        if re.fullmatch(r"[0-9\.\s\+\-\*\/×÷\(\)]+", lower) and any(op in lower for op in "+-*/×÷"):
            expr = lower.replace("×", "*").replace("÷", "/").strip()
            return RoutedIntent("CALCULATE", 0.92, {"expression": expr})

        # 5. OPEN_APPLICATION — Bengali / Banglish / English
        # Match: "open chrome", "chrome open koro", "notepad kholo", "vs code chalao" etc.
        open_prefix = re.match(
            r"^(?:open|launch|start|খোলো|খুলো|চালু\s*করো|chalu\s*koro|kholo)\s+(.+)$", lower
        )
        open_suffix = re.match(
            r"^(.+?)\s+(?:open|open\s*koro|kholo|chalu\s*koro|chalao|খোলো|খুলো|চালু\s*করো|চালাও)$", lower
        )
        app_target = None
        if open_prefix:
            app_target = open_prefix.group(1).strip()
        elif open_suffix:
            app_target = open_suffix.group(1).strip()
        if app_target and not any(ext in app_target for ext in [".pdf", ".docx", ".txt", ".xlsx", ".pptx", "file", "ফাইল"]):
            return RoutedIntent("OPEN_APPLICATION", 0.90, {"app_name": app_target})

        # 6. SEARCH_LOCAL_FILE
        if any(k in lower for k in ["find file", "search file", "find my", "খুঁজে দাও", "ফাইল খুঁজো", "পিডিএফ", "pdf", "assignment", "এসাইনমেন্ট", "অ্যাসাইনমেন্ট"]):
            return RoutedIntent("SEARCH_LOCAL_FILE", 0.85, {"query": raw})

        # 7. READ_DOCUMENT
        if any(k in lower for k in ["read document", "read file", "read pdf", "ডকুমেন্ট পড়ো", "ফাইল পড়ো"]):
            return RoutedIntent("READ_DOCUMENT", 0.85, {"query": raw})

        # 8. OPEN_FILE
        if any(k in lower for k in ["open file", "ফাইল খোলো"]):
            return RoutedIntent("OPEN_FILE", 0.85, {"query": raw})

        # 9. GET_WEATHER
        if any(k in lower for k in ["weather", "আবহাওয়া", "আবহাওয়া", "তাপমাত্রা"]):
            return RoutedIntent("GET_WEATHER", 0.85, {"query": raw})

        # 10. WEB_SEARCH
        if any(k in lower for k in ["search google", "google", "গুগলে", "সার্চ করো"]):
            return RoutedIntent("WEB_SEARCH", 0.85, {"query": raw})

        # 11. GENERAL_CHAT (questions / explanations — send to Ollama)
        if any(k in lower for k in ["explain", "what is", "how does", "how to", "why", "who is",
                                    "ব্যাখ্যা", "কীভাবে", "কেন", "কি", "কী", "কে", "কোথায়",
                                    "rajdhani", "capital", "describe", "tell me"]):
            return RoutedIntent("GENERAL_CHAT", 0.70, {"query": raw})

        return RoutedIntent("UNKNOWN_INTENT", 0.0, {"query": raw})
