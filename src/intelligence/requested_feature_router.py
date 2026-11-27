"""Routes only the user-approved VoiceMate capabilities."""

import re
from urllib.parse import urlparse

from src.helpers.app_helper import AppHelper
from src.helpers.search_helper import SearchHelper


class RequestedFeatureRouter:
    OUT_OF_SCOPE_MESSAGE = (
        "এই VoiceMate শুধু app খোলা, voice typing, web search, PDF/Word থেকে উত্তর, "
        "এবং বিভিন্ন website-এ product price খোঁজার কাজ করে।"
    )

    _OPEN_PREFIXES = (
        "open ",
        "launch ",
        "start ",
        "খুলে দাও ",
        "খুলে দিন ",
        "চালু করো ",
        "চালু করুন ",
        "খোলো ",
        "খুলো ",
        "ওপেন করো ",
        "ওপেন ",
    )
    _OPEN_SUFFIXES = (
        " open koro", " ওপেন করো", " খোলো", " খুলো", " খুলে দাও",
        " খুলে দিন", " চালু করো", " চালু করুন",
        " open", " launch",
    )
    _DOCUMENT_TERMS = (
        "pdf", "পিডিএফ", ".docx", "word file", "ওয়ার্ড", "ওয়ার্ড",
        "document", "ডকুমেন্ট", "ফাইল", "drive",
    )
    _DOCUMENT_ACTIONS = (
        "answer", "উত্তর", "solve", "সমাধান", "question", "প্রশ্ন",
        "find", "খুঁজে", "search", "পড়ো", "পড়ো", "read", "থেকে",
    )
    _PRICE_TERMS = (
        "price", "prices", "দাম", "দাম কত", "কত টাকা", "price koto",
        "dam koto", "দামের তুলনা", "compare price", "price compare", "cost",
        "how much",
    )
    _SEARCH_TERMS = ("search", "সার্চ", "খুঁজে দেখ", "খুঁজো", "খুঁজুন")
    _TYPING_TERMS = (
        "typing mode", "start typing", "টাইপিং মোড", "টাইপিং চালু",
        "টাইপ করো",
    )
    _STOP_WORDS = {
        "the", "a", "an", "is", "of", "for", "me", "please", "what", "how",
        "can", "you", "do", "does", "will", "would",
        "much", "cost", "find", "search", "check", "show", "tell", "price", "of", "s",
        "prices", "compare", "product", "dam", "er", "koto", "taka", "bdt",
        "this", "that", "এই", "এটার", "এর", "দাম", "কত", "টাকা", "বল",
        "বলো", "দেখাও", "দাও", "খুঁজে", "দিয়ে", "তুলনা", "করো", "করুন",
        "দামের",
        "প্রোডাক্ট", "প্রোডাক্টের", "পণ্য", "পণ্যের", "কোন", "এই",
        "কতটুকু",
    }
    _PRODUCT_TRANSLATIONS = {
        "আইফোন": "iphone",
        "অ্যাপল": "apple",
        "এইচপি": "hp",
        "স্যামসাং": "samsung",
        "গ্যালাক্সি": "galaxy",
        "শাওমি": "xiaomi",
        "রেডমি": "redmi",
        "ভিভো": "vivo",
        "ওপ্পো": "oppo",
        "ডেল": "dell",
        "লেনোভো": "lenovo",
        "ল্যাপটপ": "laptop",
        "মোবাইল": "mobile",
    }

    @classmethod
    def process(cls, command: str) -> str:
        text = (command or "").strip()
        lowered = text.lower()
        if not text:
            return cls.OUT_OF_SCOPE_MESSAGE

        if cls._is_greeting(lowered):
            return "হ্যালো! বলুন কোন অ্যাপ খুলব, কী লিখব, কী সার্চ করব, কোন ফাইল থেকে উত্তর দেব, অথবা কোন পণ্যের দাম খুঁজব।"

        if cls._contains_any(lowered, cls._TYPING_TERMS):
            if any(word in lowered for word in ("বন্ধ", "stop", "exit")):
                return "টাইপিং মোড বন্ধ করা হয়েছে।"
            return "ACTION_START_TYPING"

        if cls._is_document_question(lowered):
            return f"ACTION_DOCUMENT_QA|{text}"

        if cls._contains_any(lowered, cls._PRICE_TERMS):
            query = cls._extract_product_query(text)
            if not query:
                return "কোন পণ্যটির নাম বা model খুঁজব?"
            return f"ACTION_PRODUCT_PRICE|{query}"

        if cls._contains_any(lowered, cls._SEARCH_TERMS):
            query = cls._extract_search_query(text)
            if not query:
                return "PROMPT_SEARCH|google|গুগলে কী সার্চ করব?"
            if "youtube" in lowered or "ইউটিউব" in lowered:
                result = SearchHelper.search_in_youtube(query)
                return result
            return SearchHelper.search_in_google(query)

        app_target = cls._extract_app_target(text)
        if app_target is not None:
            parsed = urlparse(app_target)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                return SearchHelper.open_website(app_target)
            return AppHelper.open_app(app_target)

        return cls.OUT_OF_SCOPE_MESSAGE

    @classmethod
    def is_request_in_scope(cls, command: str) -> bool:
        lowered = (command or "").strip().lower()
        return (
            cls._is_greeting(lowered)
            or cls._contains_any(lowered, cls._TYPING_TERMS)
            or cls._is_document_question(lowered)
            or cls._contains_any(lowered, cls._PRICE_TERMS)
            or cls._contains_any(lowered, cls._SEARCH_TERMS)
            or cls._extract_app_target(command or "") is not None
        )

    @classmethod
    def _is_document_question(cls, lowered: str) -> bool:
        has_document = cls._contains_any(lowered, cls._DOCUMENT_TERMS)
        has_action = cls._contains_any(lowered, cls._DOCUMENT_ACTIONS)
        has_document_path = bool(re.search(r"\.(?:pdf|docx)\b", lowered))
        return has_document and (has_action or has_document_path)

    @classmethod
    def _extract_product_query(cls, text: str) -> str:
        digits = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
        words = re.findall(
            r"[a-z0-9]+|[\u0980-\u09ff]+",
            text.lower().translate(digits),
        )
        return " ".join(
            cls._normalize_product_word(word)
            for word in words
            if word not in cls._STOP_WORDS
        )

    @classmethod
    def _normalize_product_word(cls, word: str) -> str:
        translated = cls._PRODUCT_TRANSLATIONS.get(word)
        if translated:
            return translated
        for suffix in ("টার", "টির", "টা", "টি", "ের", "এর", "র"):
            if word.endswith(suffix):
                translated = cls._PRODUCT_TRANSLATIONS.get(word[:-len(suffix)])
                if translated:
                    return translated
        return word

    @classmethod
    def _extract_search_query(cls, text: str) -> str:
        query = text.strip()
        for prefix in (
            "search the web for ", "search web for ", "search for ", "search ",
            "ওয়েবে সার্চ করো ", "ওয়েবে খুঁজো ", "সার্চ করো ", "সার্চ ",
            "খুঁজে দেখো ", "খুঁজে দেখ ", "খুঁজো ", "খুঁজুন ",
            "ইউটিউবে সার্চ করো ", "ইউটিউবে সার্চ ",
            "youtube search ", "google search ",
        ):
            if query.lower().startswith(prefix):
                query = query[len(prefix):]
                break
        query = re.sub(r"^(গুগলে|গুগল|ইউটিউবে|ইউটিউব|on the web)\s+", "", query, flags=re.IGNORECASE)
        query = re.sub(r"\s+(সার্চ করো|সার্চ করুন|search it|search)$", "", query, flags=re.IGNORECASE)
        return query.strip()

    @classmethod
    def _extract_app_target(cls, text: str):
        query = text.strip()
        lowered = query.lower()

        for prefix in cls._OPEN_PREFIXES:
            if lowered.startswith(prefix):
                return query[len(prefix):].strip()

        for suffix in cls._OPEN_SUFFIXES:
            if lowered.endswith(suffix):
                return query[:-len(suffix)].strip()

        match = re.match(r"^(?:ওপেন|open)\s+(https?://\S+)$", query, flags=re.IGNORECASE)
        if match:
            return match.group(1).rstrip(".,)")
        return None

    @staticmethod
    def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    @staticmethod
    def _is_greeting(text: str) -> bool:
        return text in {"hello", "hi", "hey", "হ্যালো", "সালাম", "নমস্কার"}
