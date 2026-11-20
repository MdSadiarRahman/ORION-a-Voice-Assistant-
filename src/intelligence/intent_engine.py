"""
VoiceMate Intelligence - Intent Engine Module.
Defines standard intent taxonomy, entity schemas, and natural language extraction
across Bangla, English, and Banglish dialects.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
import re


class Intent(Enum):
    PLAY_MUSIC = "play_music"
    MEDIA_CONTROL = "media_control"
    VOLUME_CONTROL = "volume_control"
    OPEN_APPLICATION = "open_application"
    CLOSE_APPLICATION = "close_application"
    SEARCH_WEB = "search_web"
    SEARCH_YOUTUBE = "search_youtube"
    PRODUCT_SEARCH = "product_search"
    PRICE_CHECK = "price_check"
    COMPARE_PRODUCTS = "compare_products"
    PRODUCT_SPECS = "product_specs"
    CHEAPEST_PRODUCT = "cheapest_product"
    OPEN_PRODUCT_PAGE = "open_product_page"
    SYSTEM_INFO = "system_info"
    DESKTOP_NAVIGATION = "desktop_navigation"
    TYPING_MODE = "typing_mode"
    COMMUNICATION = "communication"
    TAKE_PHOTO = "take_photo"
    CONFIRM_ACTION = "confirm_action"
    CANCEL_ACTION = "cancel_action"
    SUBSYSTEM_TASK = "subsystem_task"
    GREETING = "greeting"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    intent: Intent
    action: str
    confidence: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_query: str = ""
    normalized_query: str = ""
    source: str = "heuristic"  # 'fast_router', 'context_manager', 'ollama_qwen'
    needs_confirmation: bool = False
    confirmation_prompt: Optional[str] = None


class IntentEngine:
    """
    Normalizes utterances across Bangla, English, and Banglish,
    and extracts core intent entities.
    """
    BANGLA_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯']
    ENGLISH_DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    # Banglish to phonetic normalized tokens
    BANGLISH_MAP = {
        "chalao": "চালাও",
        "bajao": "বাজাও",
        "shonao": "শোনাও",
        "shunbo": "শুনবো",
        "charo": "ছাড়ো",
        "chhalo": "ছাড়ো",
        "kholo": "খোলো",
        "khulo": "খুলো",
        "bondho": "বন্ধ",
        "kato": "কাটো",
        "baraw": "বাঢ়াও",
        "barhao": "বাঢ়াও",
        "komaw": "কমাও",
        "komao": "কমাও",
        "somoy": "সময়",
        "shomoy": "সময়",
        "tarikh": "তারিখ",
        "koto": "কত",
        "gan": "গান",
        "gaan": "গান",
        "ektu": "একটু",
        "ekta": "একটা",
        "thamo": "থামো",
        "porer": "পরের",
        "notun": "নতুন",
        "notupad": "নোটপ্যাড"
    }

    @classmethod
    def normalize_digits(cls, text: str) -> str:
        """Converts Bengali numerals to standard ASCII digits."""
        res = text
        for i in range(10):
            res = res.replace(cls.BANGLA_DIGITS[i], cls.ENGLISH_DIGITS[i])
        return res

    convert_bengali_digits = normalize_digits

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Lowercases, normalizes digits, and removes redundant punctuation."""
        if not text:
            return ""
        norm = cls.normalize_digits(text.lower().strip())
        # Replace punctuation except hyphens/underscores in URLs
        norm = re.sub(r"[?!.,:;।]+", " ", norm)
        norm = re.sub(r"\s+", " ", norm).strip()
        return norm

    @classmethod
    def extract_song_title(cls, text: str) -> str:
        """
        Extracts song or video title from natural phrasing across English, Bangla, and Banglish.
        Examples:
          - "Play Kamariya song" -> "Kamariya"
          - "Kamariya chalao" -> "Kamariya"
          - "একটা কামারিয়া গান চালাও" -> "কামারিয়া"
          - "I want to listen to Kamariya" -> "Kamariya"
          - "Can you play Kamariya for me?" -> "Kamariya"
          - "ইউটিউবে রবীন্দ্রসংগীত বাজাও" -> "রবীন্দ্রসংগীত"
        """
        cleaned = re.sub(r"[?!.,:;।]+$", "", text.strip()).strip()

        # Prefixes / lead-in phrases to remove
        lead_ins = [
            r"^(can you please play|could you please play)\s+",
            r"^(can you play|could you play|please play)\s+",
            r"^(i want to listen to|i want to hear|i would like to hear)\s+",
            r"^(play for me|play the song|play)\s+",
            r"^(let'?s listen to|let us listen to)\s+",
            r"^(ami shunte chai|ami shunbo|amake ekta gaan shonao)\s+",
            r"^(ekta gaan chalao|ekta gaan shonao|ekta gaan bajao|ekta gaan)\s+",
            r"^(ekta|ektu)\s+",
            r"^(একটি গান শোনাও|একটি গান চালাও|একটি গান বাজাও|একটি গান প্লে করো|একটি গান)\s+",
            r"^(একটা গান শোনাও|একটা গান চালাও|একটা গান বাজাও|একটা গান প্লে করো|একটা গান)\s+",
            r"^(একটি|একটা)\s+",
            r"^(গান শোনাও|গান চালাও|গান বাজাও|গান প্লে করো|গান)\s+",
            r"^(ইউটিউবে গিয়ে|ইউটিউবে|ইউটিউব|on youtube)\s+"
        ]

        song = cleaned
        for pat in lead_ins:
            song = re.sub(pat, "", song, flags=re.IGNORECASE).strip()

        # Suffixes / trailing action words to remove
        trailing = [
            r"(?:\s+|^)(for me|please|on youtube)$",
            r"(?:\s+|^)(song|video|music|track|gaan)$",
            r"(?:\s+|^)(chalao|bajao|shonao|charo|shunbo)$",
            r"(?:\s+|^)(play koro|play korun|play)$",
            r"(?:\s+|^)(প্লে করো|প্লে করুন|প্লে)$",
            r"(?:\s+|^)(চালাও|বাজাও|শোনাও|ছাড়ো|শুনবো)$",
            r"(?:\s+|^)(গান|সং|ভিডিও)$"
        ]

        for pat in trailing:
            song = re.sub(pat, "", song, flags=re.IGNORECASE).strip()

        # Clean noise words inside
        song = re.sub(r"^(টা|টি|the)\s+", "", song, flags=re.IGNORECASE).strip()
        song = re.sub(r"\s+", " ", song).strip()

        # If song was reduced to nothing or generic word, default to trending
        if not song or song.lower() in ["song", "music", "video", "গান", "সং", "ভিডিও", "track"]:
            return "bangla top song"

        return song

    @classmethod
    def extract_budget(cls, text: str) -> Optional[float]:
        """
        Extracts numeric budget amount from utterances in Bengali, English, or Banglish.
        Examples:
          - "under 60000 taka" -> 60000.0
          - "under ৳60,000" -> 60000.0
          - "৫০,০০০ টাকার নিচে" -> 50000.0
          - "best laptop under 50000" -> 50000.0
          - "৬০ হাজার টাকার মধ্যে" -> 60000.0
        """
        raw = text.strip()
        eng_text = cls.convert_bengali_digits(raw)

        # Check for 'hazar' / 'হাজার' (thousand)
        hazar_match = re.search(r'(\d+)\s*(?:hazar|হাজার)\s*(?:taka|টাকা)?', eng_text, re.IGNORECASE)
        if hazar_match:
            try:
                return float(hazar_match.group(1)) * 1000.0
            except Exception:
                pass

        # Regex for budget patterns
        patterns = [
            r'(?:under|below|budget|within|under\s*৳|৳)\s*([0-9,]+)\s*(?:taka|tk|bdt|টাকা)?',
            r'([0-9,]+)\s*(?:taka|tk|bdt|টাকা)\s*(?:under|er niche|niche|moddhe|এর নিচে|নিচে|মধ্যে)',
            r'([0-9,]+)\s*(?:taka|tk|bdt|টাকা)?\s*(?:বাজেট|budget)',
            r'(?:under|নিচে)\s*([0-9,]+)'
        ]

        for pat in patterns:
            m = re.search(pat, eng_text, re.IGNORECASE)
            if m:
                val_str = m.group(1).replace(",", "").strip()
                try:
                    val = float(val_str)
                    if val > 100:  # Sensible price floor
                        return val
                except Exception:
                    continue
        return None

    @classmethod
    def extract_product_query(cls, text: str) -> str:
        """
        Cleans conversational noise, search engine prefixes, and budget tokens from
        product search requests to isolate the exact target product name.
        """
        cleaned = cls.convert_bengali_digits(text.strip())
        cleaned = re.sub(r"[?!.,:;।]+$", "", cleaned).strip()

        # Remove search lead-ins
        lead_ins = [
            r"^(google-?e\s*ekta|google-?e|গুগলে\s*একটা|গুগলে|গুগল)\s+",
            r"^(search\s*for|search|খুঁজে\s*দাও|খুঁজুন|খোঁজ|find\s*the\s*best|find\s*the\s*cheapest|find\s*the|find\s*me|find)\s+",
            r"^(can\s*you\s*find|can\s*you\s*search|please\s*find|please\s*search)\s+",
            r"^(amake\s*ekta|ekta|amake|আমাকে\s*একটা|একটা|একটি)\s+",
            r"^(check\s*price\s*of|price\s*of|dam\s*koto|দাম\s*কত)\s+"
        ]
        for pat in lead_ins:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

        # Remove budget phrases
        cleaned = re.sub(r'(?:under|below|budget|within|under\s*৳|৳)\s*[0-9,]+\s*(?:taka|tk|bdt|টাকা)?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[0-9,]+\s*(?:taka|tk|bdt|টাকা)\s*(?:under|er niche|niche|moddhe|এর নিচে|নিচে|মধ্যে)', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[0-9,]+\s*(?:hazar|হাজার)\s*(?:taka|টাকা)?\s*(?:er niche|niche|moddhe|এর নিচে|নিচে|মধ্যে)?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[0-9,]+\s*(?:taka|tk|bdt|টাকা)?\s*(?:বাজেট|budget)', '', cleaned, flags=re.IGNORECASE)

        # Remove trailing request words
        trailing = [
            r"(?:\s+|^)(khuje dao|khuje dao na|khuje dekhaw|khujun|khuje)$",
            r"(?:\s+|^)(খুঁজে দাও|খুঁজে দেখাও|খুঁজুন|খোঁজ|দেখাও)$",
            r"(?:\s+|^)(dam koto|price koto|koto taka|দাম কত|প্রাইস কত|কত টাকা)$",
            r"(?:\s+|^)(price|prices|dam|দাম|features|ফিচার|স্পেসিফিকেশন)$",
            r"(?:\s+|^)(for me|please|bolo|বলুন|বলো)$"
        ]
        for pat in trailing:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()

        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned
