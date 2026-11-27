"""
Rule-based IntentRouter for VoiceMate Advanced Hybrid Architecture.
Classifies ordinary user commands in Python without requiring an LLM,
while carefully avoiding collisions with Product, Assignment, and Autonomous goals.
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

    _FILE_HINT_TERMS = (
        "file", "ফাইল", "pdf", "পিডিএফ", "docx", "word file", "doc",
        "resume", "cv", "নোট", "notes", "ডকুমেন্ট", "document",
        "অ্যাসাইনমেন্ট", "এসাইনমেন্ট", "assignment", "downloads", "ডাউনলোড",
        "desktop", "ডেস্কটপ", "documents",
    )
    _ASSIGNMENT_SOLVE_TERMS = ("সলভ", "solve", "সমাধান", "উত্তর", "answer", "বানিয়ে", "তৈরি", "docx")
    _PRODUCT_TERMS = ("laptop", "ল্যাপটপ", "phone", "ফোন", "samsung", "স্যামসাং", "hp", "এইচপি", "dam koto", "দাম কত", "price", "prices", "cheapest", "compare")

    @classmethod
    def route(cls, text: str) -> RoutedIntent:
        raw = (text or "").strip()
        lower = raw.lower()

        # 1. GENERAL_GREETING
        if re.match(r"^(hello|hi|hey|good morning|good evening|হ্যালো|হাই|সালাম|আসসালামু আলাইকুম|কেমন আছো|kemon acho|assalamu alaikum)\b", lower):
            return RoutedIntent("GENERAL_GREETING", 0.95, {"text": raw})

        # 2. GET_CURRENT_TIME
        if any(k in lower for k in ["what time", "current time", "time is it", "কয়টা বাজে", "কয়টা বাজে", "সময় কত", "সময় কত", "এখন কয়টা", "এখন কয়টা"]):
            return RoutedIntent("GET_CURRENT_TIME", 0.95)

        # 3. GET_CURRENT_DATE
        if any(k in lower for k in ["what date", "today's date", "what day", "current date", "আজকের তারিখ", "আজ কি বার", "আজ কী বার", "আজকে কি বার", "আজকে কত তারিখ"]):
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
        open_prefix = re.match(
            r"^(?:open|launch|start|খোলো|খুলো|চালু\s*করো|chalu\s*koro|kholo)\s+(.+)$", lower
        )
        open_suffix = re.match(
            r"^(.+?)\s+(?:open|open\s*koro|kholo|chalu\s*koro|খোলো|খুলো|চালু\s*করো)$", lower
        )
        app_target = None
        if open_prefix:
            app_target = open_prefix.group(1).strip()
        elif open_suffix:
            app_target = open_suffix.group(1).strip()
        if app_target and not any(ext in app_target for ext in [".pdf", ".docx", ".txt", ".xlsx", ".pptx", "file", "ফাইল", "ওয়েবসাইট", "ওয়েবসাইট", "website"]):
            return RoutedIntent("OPEN_APPLICATION", 0.90, {"app_name": app_target})

        # 6. GET_WEATHER (live Open-Meteo lookup)
        if any(k in lower for k in ["weather", "আবহাওয়া", "আবহাওয়া", "তাপমাত্রা", "বৃষ্টি হবে"]):
            return RoutedIntent("GET_WEATHER", 0.92, {"query": raw})

        # 7. OPEN_FILE (explicit local file open, not assignment solve)
        if any(k in lower for k in ["open file", "ফাইল খোলো", "ফাইল ওপেন", "ফাইলটা খোলো"]) and not any(s in lower for s in cls._ASSIGNMENT_SOLVE_TERMS):
            return RoutedIntent("OPEN_FILE", 0.88, {"query": raw})

        # 8. READ_DOCUMENT
        if any(k in lower for k in ["read document", "read file", "read pdf", "ডকুমেন্ট পড়ো", "ডকুমেন্ট পড়ো", "ফাইল পড়ো", "ফাইল পড়ো", "পিডিএফ পড়ো", "পিডিএফ পড়ো"]):
            return RoutedIntent("READ_DOCUMENT", 0.88, {"query": raw})

        # 9. SEARCH_LOCAL_FILE — only when user asks to search/find a local file, NOT Google search or assignment solve
        has_find_verb = any(k in lower for k in ["find file", "search file", "find my", "খুঁজে দাও", "খুঁজো", "ফাইল খুঁজো", "খুঁজে বের করো", "search my"])
        has_file_hint = any(k in lower for k in cls._FILE_HINT_TERMS)
        is_google_or_product = any(k in lower for k in ("google", "গুগল", "youtube", "ইউটিউব") + cls._PRODUCT_TERMS)
        is_assignment_solve = any(k in lower for k in ("assignment", "অ্যাসাইনমেন্ট", "এসাইনমেন্ট")) and any(s in lower for s in cls._ASSIGNMENT_SOLVE_TERMS)
        if (has_find_verb and has_file_hint and not is_google_or_product and not is_assignment_solve) or any(k in lower for k in ["find file", "search file", "ফাইল খুঁজো", "ফাইল খুঁজে দাও", "পিডিএফ খুঁজে দাও"]):
            return RoutedIntent("SEARCH_LOCAL_FILE", 0.90, {"query": raw})

        # 10. WEB_SEARCH (explicit Google/web search, excluding product queries)
        if any(k in lower for k in ["search google", "গুগলে সার্চ", "ইন্টারনেটে খোঁজো"]) and not any(p in lower for p in cls._PRODUCT_TERMS):
            return RoutedIntent("WEB_SEARCH", 0.85, {"query": raw})

        # 11. GENERAL_CHAT (questions / explanations — route to Gemini/Ollama LLM)
        if any(k in lower for k in ["explain", "what is", "how does", "how to", "why", "who is",
                                    "ব্যাখ্যা", "কীভাবে", "কিভাবে", "কেন", "কি", "কী", "কে", "কোথায়", "কোথায়",
                                    "rajdhani", "রাজধানী", "capital", "describe", "tell me", "লিখে দাও", "বলো"]):
            return RoutedIntent("GENERAL_CHAT", 0.70, {"query": raw})

        return RoutedIntent("UNKNOWN_INTENT", 0.0, {"query": raw})
