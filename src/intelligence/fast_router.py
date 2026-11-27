"""
VoiceMate Intelligence - Fast Command Router Module.
High-efficiency, sub-10ms deterministic pattern matcher and entity extractor
supporting Bangla, English, and Banglish without invoking heavy LLMs.
"""
import re
from typing import Optional, Dict, Any
from src.intelligence.intent_engine import Intent, IntentResult, IntentEngine


class FastCommandRouter:
    """
    Evaluates utterances against compiled linguistic patterns to classify intent
    and extract parameters in real-time.
    """
    APP_NAME_MAPPING = {
        "গুগল": "google",
        "google": "google",
        "ইউটিউব": "youtube",
        "youtube": "youtube",
        "yt": "youtube",
        "ফেসবুক": "facebook",
        "facebook": "facebook",
        "fb": "facebook",
        "ম্যাপ": "maps",
        "maps": "maps",
        "গ্যালারি": "start ms-photos:",
        "photos": "start ms-photos:",
        "ছবি": "start ms-photos:",
        "ক্যামেরা": "camera",
        "camera": "camera",
        "সেটিংস": "settings",
        "settings": "settings",
        "ফোন": "phone",
        "phone": "phone",
        "মেসেজ": "message",
        "message": "message",
        "হোয়াটসঅ্যাপ": "whatsapp",
        "whatsapp": "whatsapp",
        "নোটপ্যাড": "notepad",
        "notepad": "notepad",
        "ক্যালকুলেটর": "calculator",
        "calculator": "calculator",
        "ব্রাউজার": "chrome",
        "browser": "chrome",
        "chrome": "chrome",
        "edge": "msedge",
        "পেইন্ট": "paint",
        "paint": "paint",
        "কোড": "vscode",
        "vscode": "vscode",
        "visual studio code": "vscode"
    }

    @classmethod
    def match(cls, text: str) -> Optional[IntentResult]:
        """
        Attempts fast pattern matching on the given input text.
        Returns IntentResult if an unambiguous match is found, otherwise None.
        """
        if not text:
            return None

        raw = text.strip()
        norm = IntentEngine.clean_text(raw)
        norm_words = norm.split()

        # 1. GREETING
        if any(norm.startswith(g) for g in ["hello", "hi", "hey", "হ্যালো", "সালাম", "নমস্কার"]) and len(norm_words) <= 3:
            return IntentResult(
                intent=Intent.GREETING,
                action="greeting",
                confidence=1.0,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 2. MEDIA CONTROL (Pause, Resume, Stop, Next, Previous)
        pause_kws = ["pause", "পজ", "পজ করো", "পজ করুন", "থামো", "একটু থামো", "hold on", "pause video", "pause playback"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in pause_kws):
            return IntentResult(
                intent=Intent.MEDIA_CONTROL,
                action="pause",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        resume_kws = ["resume", "রিজিউম", "আবার চালাও", "চালিয়ে যাও", "প্লে চালিয়ে যাও", "continue", "resume playback"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in resume_kws):
            return IntentResult(
                intent=Intent.MEDIA_CONTROL,
                action="resume",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        stop_kws = ["stop playback", "stop video", "stop music", "গান বন্ধ করো", "মিউজিক বন্ধ", "গান বন্ধ", "প্লেব্যাক বন্ধ"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in stop_kws):
            return IntentResult(
                intent=Intent.MEDIA_CONTROL,
                action="stop",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        next_kws = ["next", "next song", "next video", "পরের গান", "পরের ভিডিও", "পরেরটা চালাও", "skip", "change song"]
        if any(norm == kw or norm.startswith(kw) for kw in next_kws):
            return IntentResult(
                intent=Intent.MEDIA_CONTROL,
                action="next",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        prev_kws = ["previous", "previous song", "previous video", "আগের গান", "আগের ভিডিও", "পেছনের গান"]
        if any(norm == kw or norm.startswith(kw) for kw in prev_kws):
            return IntentResult(
                intent=Intent.MEDIA_CONTROL,
                action="previous",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 3. VOLUME CONTROL
        vol_up_kws = [
            "volume up", "increase volume", "louder", "sound baraw", "sound barhao",
            "volume baraw", "volume barhao", "ভলিউম বাড়াও", "সাউন্ড বাড়াও", "আওয়াজ বাড়াও",
            "একটু সাউন্ড বাড়াও", "sound barao", "volume barao"
        ]
        if any(kw in norm for kw in vol_up_kws):
            return IntentResult(
                intent=Intent.VOLUME_CONTROL,
                action="volume_up",
                confidence=0.98,
                parameters={"direction": "up", "steps": 5},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        vol_down_kws = [
            "volume down", "decrease volume", "quieter", "sound komaw", "sound komao",
            "volume komaw", "volume komao", "ভলিউম কমাও", "সাউন্ড কমাও", "আওয়াজ কমাও",
            "একটু সাউন্ড কমাও"
        ]
        if any(kw in norm for kw in vol_down_kws):
            return IntentResult(
                intent=Intent.VOLUME_CONTROL,
                action="volume_down",
                confidence=0.98,
                parameters={"direction": "down", "steps": 5},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        mute_kws = ["mute", "unmute", "মিউট করো", "আনমিউট করো", "চুপ করো", "সাউন্ড মিউট"]
        if any(norm == kw or norm.startswith(kw) for kw in mute_kws):
            return IntentResult(
                intent=Intent.VOLUME_CONTROL,
                action="toggle_mute",
                confidence=0.98,
                parameters={"direction": "mute"},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 4. SYSTEM INFO (Time, Date, Battery)
        time_kws = ["সময় কত", "সময় কত", "কয়টা বাজে", "time koto", "what time is it", "current time", "what is the time"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in time_kws) or (norm in ["time", "সময়", "সময়"]):
            return IntentResult(
                intent=Intent.SYSTEM_INFO,
                action="get_time",
                confidence=0.99,
                parameters={"info_type": "time"},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        date_kws = ["তারিখ কত", "আজকের তারিখ", "আজকে কি বার", "date koto", "what date is it", "today's date", "what is the date"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in date_kws) or (norm in ["date", "তারিখ"]):
            return IntentResult(
                intent=Intent.SYSTEM_INFO,
                action="get_date",
                confidence=0.99,
                parameters={"info_type": "date"},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        battery_kws = ["চার্জ কত", "battery charge", "ব্যাটারি কত", "charge koto", "battery level", "how much battery"]
        if any(norm == kw or norm.startswith(kw) or norm.endswith(kw) for kw in battery_kws) or (norm in ["battery", "চার্জ", "ব্যাটারি"]):
            return IntentResult(
                intent=Intent.SYSTEM_INFO,
                action="get_battery",
                confidence=0.99,
                parameters={"info_type": "battery"},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 5. SPECIALIZED SUBSYSTEM TASKS (Docling & PyMuPDF Document Intelligence)
        if any(kw in norm for kw in ["ডকলিং", "docling", "ওয়ার্ড ফাইল", "সেমান্টিক চাংক"]):
            return IntentResult(intent=Intent.SUBSYSTEM_TASK, action="docling", confidence=0.95, parameters={"query": raw}, raw_query=raw, source="fast_router")
        if any(kw in norm for kw in ["পিডিএফ পড়ো", "পিডিএফ সামারি", "ডকুমেন্ট পড়ো", "read pdf"]):
            return IntentResult(intent=Intent.SUBSYSTEM_TASK, action="document", confidence=0.95, parameters={"query": raw}, raw_query=raw, source="fast_router")

        # 6. PLAY MUSIC / YOUTUBE PLAYBACK
        # Matches: "Play Kamariya song", "Kamariya chalao", "একটা কামারিয়া গান চালাও",
        # "I want to listen to Kamariya", "Can you play Kamariya for me?", "ইউটিউবে রবীন্দ্রসংগীত বাজাও", "গান বাজাও"
        music_verbs = ["play", "চালাও", "বাজাও", "শোনাও", "ছাড়ো", "শুনবো", "chalao", "bajao", "shonao", "charo", "shunbo"]
        music_nouns = ["song", "music", "গান", "সং", "গীতি", "track", "gaan"]

        is_play_music = False
        if any(phrase in norm for phrase in [
            "can you play", "could you play", "please play", "can you please play",
            "play for me", "play the song", "want to listen to", "want to hear",
            "like to hear", "shunte chai", "গান শুনতে চাই", "গান শোনাও", "গান চালাও",
            "গান বাজাও", "গান প্লে", "play song", "play music"
        ]):
            is_play_music = True
        elif any(norm.startswith(f"play {m}") or norm == f"play {m}" for m in music_nouns):
            is_play_music = True
        elif norm.startswith("play ") and len(norm_words) >= 2 and not any(s in norm for s in ["store", "প্লে স্টোর"]):
            is_play_music = True
        elif any(verb in norm for verb in ["chalao", "bajao", "shonao", "চালাও", "বাজাও", "শোনাও", "ছাড়ো", "charo", "shunbo", "শুনবো"]):
            is_play_music = True
        elif ("youtube" in norm or "ইউটিউব" in norm) and any(n in norm for n in music_nouns + ["প্লে", "play"]) and ("সার্চ" not in norm and "search" not in norm):
            is_play_music = True
        elif any(norm.endswith(n) for n in ["সং", "গান", "song"]) and ("সার্চ" not in norm and "search" not in norm) and len(norm_words) <= 4:
            is_play_music = True

        if is_play_music:
            song_title = IntentEngine.extract_song_title(raw)
            return IntentResult(
                intent=Intent.PLAY_MUSIC,
                action="play_youtube",
                confidence=0.95,
                parameters={"song_name": song_title},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 7. EXPLICIT YOUTUBE SEARCH VS OPEN YOUTUBE
        if "ইউটিউবে গান সার্চ করো" in norm or "search youtube for" in norm:
            clean_s = raw
            for w in ["ইউটিউবে", "সার্চ করো", "search youtube for", "search in youtube"]:
                clean_s = clean_s.replace(w, "").strip()
            return IntentResult(
                intent=Intent.SEARCH_YOUTUBE,
                action="search_youtube",
                confidence=0.95,
                parameters={"search_query": clean_s or "songs"},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 8. OPEN APPLICATION
        # Single app names or phrases: "open youtube", "ইউটিউব", "ইউটিউব খোলো", "notepad open koro"
        open_verbs = ["open", "খোলো", "খুলো", "ওপেন করো", "চালু করো", "kholo", "khulo", "chalu koro", "open koro"]
        has_open_verb = any(v in norm for v in open_verbs)

        for name_alias, target_cmd in cls.APP_NAME_MAPPING.items():
            if norm == name_alias or (has_open_verb and name_alias in norm):
                return IntentResult(
                    intent=Intent.OPEN_APPLICATION,
                    action="open_app",
                    confidence=0.96,
                    parameters={"app_name": target_cmd, "display_name": name_alias},
                    raw_query=raw,
                    normalized_query=norm,
                    source="fast_router"
                )

        # 9. CLOSE APPLICATION
        close_kws = ["close window", "close app", "exit", "কাটো", "উইন্ডো বন্ধ করো", "বন্ধ করো", "bondho koro", "kato"]
        if any(norm == kw or norm.startswith(kw) for kw in close_kws):
            return IntentResult(
                intent=Intent.CLOSE_APPLICATION,
                action="close_app",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 10. TYPING MODE
        if any(w in norm for w in ["টাইপিং", "টাইপ করো", "typing mode", "start typing"]) and "বন্ধ" not in norm:
            return IntentResult(
                intent=Intent.TYPING_MODE,
                action="start_typing",
                confidence=0.98,
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # 11. DESKTOP NAVIGATION
        if any(norm == w or norm.startswith(w) for w in ["scroll up", "up", "উপরে যাও", "উপরে উঠো", "উপরে"]):
            return IntentResult(intent=Intent.DESKTOP_NAVIGATION, action="scroll_up", confidence=0.98, raw_query=raw, source="fast_router")
        if any(norm == w or norm.startswith(w) for w in ["scroll down", "down", "নিচে যাও", "নিচে নামো", "নিচে"]):
            return IntentResult(intent=Intent.DESKTOP_NAVIGATION, action="scroll_down", confidence=0.98, raw_query=raw, source="fast_router")
        if any(norm == w or norm.startswith(w) for w in ["go home", "show desktop", "হোমে যাও", "ডেস্কটপ দেখাও"]):
            return IntentResult(intent=Intent.DESKTOP_NAVIGATION, action="go_home", confidence=0.98, raw_query=raw, source="fast_router")

        # 12. TAKE PHOTO
        if any(w in norm for w in ["ছবি তোলো", "ছবি তুলুন", "ক্যামেরা খোলো", "take photo", "capture photo"]):
            return IntentResult(intent=Intent.TAKE_PHOTO, action="take_photo", confidence=0.98, raw_query=raw, source="fast_router")

        # 13. CONFIRMATION / CANCELLATION (Yes / No)
        if norm in ["yes", "হাঁ", "হ্যাঁ", "confirm", "proceed", "sure", "koro", "করো", "ঠিক আছে", "ok", "okay"]:
            return IntentResult(intent=Intent.CONFIRM_ACTION, action="confirm", confidence=0.98, raw_query=raw, source="fast_router")
        if norm in ["no", "না", "cancel", "stop", "abort", "করো না", "দরকার নেই", "na", "cancel koro"]:
            return IntentResult(intent=Intent.CANCEL_ACTION, action="cancel", confidence=0.98, raw_query=raw, source="fast_router")

        # 14. PRODUCT SEARCH, PRICE COMPARISON & RESEARCH
        # Handles:
        # - "Google-এ একটা HP Laptop খুঁজে দাও।"
        # - "এই ফোনটার দাম কত?"
        # - "Search Samsung S25 Ultra price."
        # - "Find the cheapest gaming laptop."
        # - "এই Product-এর দাম এবং Features বলো।"
        # - "Compare these two phones."
        # - "Find the best laptop under 50000 taka."
        # - "Find HP laptops under 60000 taka."
        lower_raw = raw.lower()
        product_nouns = [
            "laptop", "ল্যাপটপ", "phone", "ফোন", "mobile", "মোবাইল", "desktop", "ডেস্কটপ",
            "samsung", "স্যামসাং", "hp", "এইচপি", "asus", "আসুস", "lenovo", "লেনোভো",
            "dell", "ডেল", "acer", "এসার", "s25", "galaxy", "iphone", "আইফোন", "product"
        ]
        shopping_triggers = [
            "দাম কত", "price", "prices", "dam koto", "খুঁজে দাও", "khuje dao", "find",
            "cheapest", "সবচেয়ে কম", "best", "compare", "তুলনা", "features", "ফিচার",
            "স্পেসিফিকেশন", "specs", "under", "নিচে", "taka", "টাকা"
        ]

        has_product_noun = any(p in norm for p in product_nouns) or any(p in lower_raw for p in product_nouns)
        has_shopping_trigger = any(t in norm for t in shopping_triggers) or any(t in lower_raw for t in shopping_triggers)

        # Explicit compare requests like "Compare these two phones"
        if ("compare" in norm or "তুলনা" in norm) and (has_product_noun or "two" in norm or "দুটো" in norm or "phones" in norm):
            prod_q = IntentEngine.extract_product_query(raw)
            return IntentResult(
                intent=Intent.COMPARE_PRODUCTS,
                action="compare_products",
                confidence=0.95,
                parameters={"query": prod_q or "products", "raw_query": raw},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        # Product search & price research
        if (has_product_noun and has_shopping_trigger) or ("under" in norm and any(c.isdigit() for c in norm)):
            budget = IntentEngine.extract_budget(raw)
            prod_q = IntentEngine.extract_product_query(raw)

            # Specific intent identification
            if any(w in norm for w in ["cheapest", "সবচেয়ে কম", "কম দামি"]):
                target_intent = Intent.CHEAPEST_PRODUCT
                action = "find_cheapest"
            elif any(w in norm for w in ["features", "ফিচার", "স্পেসিফিকেশন", "specs"]):
                target_intent = Intent.PRODUCT_SPECS
                action = "product_specs"
            elif any(w in norm for w in ["compare", "তুলনা"]):
                target_intent = Intent.COMPARE_PRODUCTS
                action = "compare_products"
            else:
                target_intent = Intent.PRODUCT_SEARCH
                action = "search_products"

            return IntentResult(
                intent=target_intent,
                action=action,
                confidence=0.96,
                parameters={"query": prod_q or raw, "budget": budget, "raw_query": raw},
                raw_query=raw,
                normalized_query=norm,
                source="fast_router"
            )

        return None
