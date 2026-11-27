"""
VoiceMate Laptop Agent - Command Processor Module.
Parses, interprets and routes all Bengali and English voice/text commands
for the laptop assistant.
"""
import re
import unicodedata
import urllib.parse
from typing import Optional, Tuple
from src.helpers.app_helper import AppHelper
from src.helpers.contact_helper import ContactHelper
from src.helpers.date_helper import DateHelper
from src.helpers.desktop_automation_helper import DesktopAutomationHelper
from src.helpers.battery_helper import BatteryHelper
from src.helpers.search_helper import SearchHelper
from src.helpers.media_controller import MediaController
from src.helpers.camera_helper import CameraHelper
from src.helpers.vision_helper import VisionHelper
from src.helpers.sms_helper import SmsHelper

class CommandProcessor:
    APP_NAME_MAPPING = {
        "গুগল": "google",
        "ইউটিউব": "youtube",
        "ফেসবুক": "facebook",
        "ম্যাপ": "maps",
        "প্লে স্টোর": "start ms-windows-store:",
        "স্টোর": "start ms-windows-store:",
        "মাইক্রোসফট স্টোর": "start ms-windows-store:",
        "গ্যালারি": "start ms-photos:",
        "ছবি": "start ms-photos:",
        "ক্যামেরা": "camera",
        "সেটিংস": "settings",
        "ফোন": "phone",
        "মেসেজ": "message",
        "হোয়াটসঅ্যাপ": "whatsapp",
        "হোয়াটসঅ্যাপ": "whatsapp",
        "টেলিগ্রাম": "telegram",
        "ভিএলসি": "vlc",
        "ওয়ার্ড": "word",
        "ওয়ার্ড": "word",
        "এক্সেল": "excel",
        "ডিসকর্ড": "discord",
        "স্পটিফাই": "spotify",
        "জুম": "zoom",
        "অ্যান্টিগ্র্যাভিটি": "antigravity",
        "অ্যান্টি গ্র্যাভিটি": "antigravity",
        "এন্টিগ্র্যাভিটি": "antigravity",
        "এন্টি গ্র্যাভিটি": "antigravity",
        "anti gravity": "antigravity",
        "ম্যাসেঞ্জার": "messenger",
        "নোটপ্যাড": "notepad",
        "ক্যালকুলেটর": "calculator",
        "ব্রাউজার": "chrome",
        "পেইন্ট": "paint",
        "কোড": "vscode"
    }

    @staticmethod
    def contains_word(text: str, word: str) -> bool:
        """
        Regex word boundary check including Bengali unicode range (\u0980-\u09FF).
        """
        pattern = rf"(^|[^\w\u0980-\u09FF]){re.escape(word)}($|[^\w\u0980-\u09FF])"
        return bool(re.search(pattern, text, re.IGNORECASE))

    @staticmethod
    def convert_bengali_digits(input_str: str) -> str:
        """
        Converts Bengali numeral digits ('০'-'৯') to English digits ('0'-'9').
        """
        bengali_digits = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯']
        english_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        result = input_str
        for i in range(10):
            result = result.replace(bengali_digits[i], english_digits[i])
        return result

    @classmethod
    def make_call(cls, number: str, name: str) -> str:
        """
        Initiates call via ContactHelper.
        """
        return ContactHelper.make_call(number, name)

    @classmethod
    def process_command(cls, command: str) -> str:
        """
        Main command parser and executor for the laptop agent.
        """
        from src.intelligence.requested_feature_router import RequestedFeatureRouter
        return RequestedFeatureRouter.process(command)

    @classmethod
    def _process_legacy_command(cls, command: str) -> str:
        """Retained implementation for reference; no longer exposed to VoiceMate."""
        cmd = cls.convert_bengali_digits(command.lower().strip())

        # Greeting check
        if cls.is_greeting(cmd) and len(cmd.split()) <= 2:
            return "হ্যালো! আমি ভয়েস মেট, আপনার ল্যাপটপ অ্যাসিস্ট্যান্ট। বলুন আমি আপনাকে কিভাবে সাহায্য করতে পারি?"

        # ১. টাইপিং মোড
        typing_keywords = ["টাইপিং", "টাইপ", "লিখুন", "typing"]
        if any(cls.contains_word(cmd, kw) for kw in typing_keywords) and "বন্ধ" not in cmd:
            return "ACTION_START_TYPING"

        # ২. অটোনোমাস ব্রাউজার এজেন্ট কমান্ড (Powered by Browser-Use 1.0)
        browser_agent_kws = [
            "ব্রাউজারে গিয়ে", "ব্রাউজ করো", "ওয়েবসাইটে গিয়ে", "অনলাইনে গিয়ে",
            "অনলাইনে রিসার্চ করো", "browse", "web agent", "browser agent", "ব্রাউজার এজেন্ট"
        ]
        if any(kw in cmd for kw in browser_agent_kws):
            task_clean = cmd
            for kw in browser_agent_kws:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_BROWSER_TASK|{task_clean}"

        


        # ২b. অ্যাসাইনমেন্ট সলভার এজেন্ট (Direct Assignment Routing)
        assignment_kws = [
            "অ্যাসাইনমেন্ট", "এসাইনমেন্ট", "assignment", "হোমওয়ার্ক", "homework", "প্রশ্নপত্র",
            "সলভ", "solve", "সমাধান", "উত্তর", "answer", "প্রশ্নের উত্তর",
            "question solve", "question answer", "পিডিএফ", "pdf",
            "পরীক্ষার প্রশ্ন", "পড়াশোনা", "পড়া", "study help"
        ]
        assignment_action_kws = [
            "সলভ", "solve", "সমাধান", "উত্তর", "answer", "করো", "করে", "দাও",
            "বলো", "help", "লিখো", "write", "বানাও", "create", "তৈরি"
        ]
        has_assignment_kw = any(kw in cmd for kw in assignment_kws)
        has_assignment_action = any(kw in cmd for kw in assignment_action_kws)
        if has_assignment_kw and has_assignment_action:
            task_clean = cmd
            for kw in ["অ্যাসাইনমেন্ট", "এসাইনমেন্ট", "assignment", "হোমওয়ার্ক", "homework"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_ASSIGNMENT_TASK|{task_clean}"

        # ২c. অটোনোমাস মাল্টি-স্টেপ টাস্ক প্ল্যানার (Assignment, Website Development, Deep Research)
        if any(w in cmd for w in ["assignment", "অ্যাসাইনমেন্ট", "website", "ওয়েবসাইট", "রিসার্চ রিপোর্ট", "research report"]) and any(w in cmd for w in ["বানিয়ে", "তৈরি", "build", "create", "সলভ", "solve", "সমাধান", "docx", "pdf", "রিসার্চ", "report"]):
            if cls._decision_engine is None:
                from src.intelligence.decision_engine import HybridDecisionEngine
                cls._decision_engine = HybridDecisionEngine()
            _, auto_reply = cls._decision_engine.process_query(command)
            if auto_reply and "বুঝতে পারিনি" not in auto_reply:
                return auto_reply

        # ৩. মাল্টিমোডাল ডকুমেন্ট কনভার্সন ও আরএজি চাংকিং (Powered by Docling)
        docling_kws = [
            "ডকলিং", "docling", "ওয়ার্ড ফাইল", "ওয়ার্ড পড়ো", "পাওয়ারপয়েন্ট", "এক্সেল পড়ো",
            "ডকুমেন্ট কনভার্ট", "সেমান্টিক চাংক", "ডকুমেন্ট চাংক", "মাল্টিমোডাল ডকুমেন্ট",
            "convert document", "chunk document"
        ]
        if any(kw in cmd for kw in docling_kws):
            docling_query = cmd
            for kw in ["ডকলিং", "docling"]:
                docling_query = docling_query.replace(kw, "")
            docling_query = docling_query.strip()
            if not docling_query:
                docling_query = cmd
            return f"ACTION_DOCLING_TASK|{docling_query}"

        # ৪. ডকুমেন্ট ইন্টেলিজেন্স ও PDF রিডার কমান্ড (Powered by PyMuPDF)
        doc_agent_kws = [
            "পিডিএফ পড়ো", "পিডিএফ পড়ে শোনাও", "পিডিএফ সামারি", "ডকুমেন্ট পড়ো",
            "ডকুমেন্ট সামারি করো", "ফাইল পড়ো", "read pdf", "summarize document",
            "summarize pdf", "টেবিল এক্সট্রাক্ট", "ডকুমেন্ট অ্যানালাইসিস", "ডকুমেন্ট দেখো"
        ]
        if any(kw in cmd for kw in doc_agent_kws):
            doc_query = cmd
            for kw in doc_agent_kws:
                doc_query = doc_query.replace(kw, "")
            doc_query = doc_query.strip()
            return f"ACTION_DOCUMENT_TASK|{doc_query}"

        # ৫. ডিটারমিনিস্টিক ওয়েব অটোমেশন ও মিডিয়া প্লেয়ার (Powered by Playwright & YouTube Resolver)
        playwright_kws = [
            "প্লে করো", "ইউটিউবে প্লে", "গান প্লে করো", "ভিডিও প্লে করো", "গান বাজাও", "গান চালাও",
            "ভিডিও চালাও", "গান শোনাও", "গান ছাড়ো", "গান শুনবো", "সং চালাও", "সং প্লে করো",
            "সং বাজাও", "সং শোনাও", "ওয়েব স্ক্রিনশট", "ওয়েবসাইটের স্ক্রিনশট", "web screenshot",
            "হোয়াটসঅ্যাপ ওয়েব", "ওয়েব অটোমেশন", "playwright", "অটোমেশন করো", "play music",
            "play song", "play video"
        ]
        is_media_intent = (
            any(kw in cmd for kw in playwright_kws) or
            (("ইউটিউব" in cmd or "youtube" in cmd) and any(w in cmd for w in ["গান", "সং", "song", "চালাও", "বাজাও", "প্লে", "play", "শোনাও", "ছাড়ো", "শুনবো", "মিউজিক"]) and not any(s in cmd for s in ["সার্চ", "search", "খুঁজো"])) or
            (any(w in cmd for w in ["কামারিয়া", "রবীন্দ্রসংগীত", "নজরুলগীতি"]) and any(w in cmd for w in ["সং", "গান", "চালাও", "বাজাও", "প্লে", "শোনাও"])) or
            (cmd.startswith("play ") and len(cmd.split()) >= 2)
        )
        if is_media_intent:
            task_clean = cmd
            for kw in ["ওয়েব অটোমেশন", "অটোমেশন করো", "playwright"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_PLAYWRIGHT_TASK|{task_clean}"

        # ৫. ওপেনহ্যান্ডস এজেন্ট ক্যানভাস ও ডেভেলপার অপারেশন (Powered by OpenHands)
        canvas_kws = [
            "ক্যানভাস খোলো", "ক্যানভাস চালু", "ওপেনহ্যান্ডস", "agent canvas", "open canvas",
            "কোড অডিট", "কোড রিভিউ", "code review", "code audit", "সিনট্যাক্স চেক",
            "গিট স্ট্যাটাস", "git status", "ফাইল ট্রি", "file tree", "প্রোজেক্ট স্ট্রাকচার",
            "টার্মিনালে চালাও", "টার্মিনাল কমান্ড"
        ]
        if any(kw in cmd for kw in canvas_kws):
            task_clean = cmd
            for kw in ["ওপেনহ্যান্ডস", "ক্যানভাস"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_CANVAS_TASK|{task_clean}"

        # ৬. এআই পেয়ার প্রোগ্রামার ও কোড এডিটিং (Powered by Aider)
        coder_kws = [
            "রেপো ম্যাপ", "repo map", "কোড ম্যাপ", "কোড এডিট করো", "কোড এডিট",
            "সার্চ রিপ্লেস", "search replace", "কোড রোলব্যাক", "কোড আনডু",
            "code rollback", "aider", "এইডার"
        ]
        if any(kw in cmd for kw in coder_kws) or "<<<<<<< search" in cmd:
            task_clean = cmd
            for kw in ["এইডার", "aider"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_CODER_TASK|{task_clean}"

        # ৭. এনএইটেন ইউনিভার্সাল ওয়ার্কফ্লো অটোমেশন (Powered by n8n)
        n8n_kws = [
            "এনএইটেন", "n8n", "অটোমেশন ফ্লো", "ওয়ার্কফ্লো", "workflow", "ওয়েবহুক", "webhook",
            "নোশনে পাঠাও", "গুগল শিটে সেভ", "স্ল্যাকে পাঠাও", "টেলিগ্রামে মেসেজ"
        ]
        if any(kw in cmd for kw in n8n_kws):
            task_clean = cmd
            for kw in ["এনএইটেন", "n8n"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_N8N_TASK|{task_clean}"

        # ৮. ফাস্টএপিআই গেটওয়ে ও ব্যাকএন্ড সার্ভার (Powered by FastAPI)
        api_kws = [
            "এপিআই সার্ভার", "api server", "ফাস্টএপিআই", "fastapi", "এপিআই চালু", "সার্ভার চালু",
            "এপিআই ওপেন", "এপিআই ডক", "সোয়েগার ডক", "swagger doc", "এপিআই স্ট্যাটাস", "api docs", "api status"
        ]
        if any(kw in cmd for kw in api_kws):
            task_clean = cmd
            for kw in ["ফাস্টএপিআই", "fastapi", "এপিআই"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_API_GATEWAY_TASK|{task_clean}"

        # ৯. ল্যাংগ্রাফ মাল্টি-এজেন্ট ব্রেন ও স্টেট মেশিন (Powered by LangGraph)
        brain_kws = [
            "ল্যাংগ্রাফ", "langgraph", "মাল্টি এজেন্ট", "মাল্টি-এজেন্ট", "এজেন্ট ব্রেন",
            "ব্রেন স্ট্যাটাস", "ব্রেন চালাও", "ব্রেন মেমোরি", "ব্রেন হিস্ট্রি", "গ্রাফ রান করো"
        ]
        if any(kw in cmd for kw in brain_kws):
            task_clean = cmd
            for kw in ["ল্যাংগ্রাফ", "langgraph", "ব্রেন"]:
                task_clean = task_clean.replace(kw, "")
            task_clean = task_clean.strip()
            if not task_clean:
                task_clean = cmd
            return f"ACTION_BRAIN_TASK|{task_clean}"

        # ১০. সার্চ কমান্ড (গুগল ও ইউটিউব কুইক সার্চ)
        search_keywords = ["search", "সার্চ", "খুঁজো", "খুঁজুন", "দেখাও", "দেখবো", "খুঁজে দাও"]
        yt_keywords = ["youtube", "ইউটিউবে", "ইউটিউব"]
        gg_keywords = ["google", "গুগলে", "গুগল"]
        open_keywords = ["open", "খুলো", "খোলো", "ওপেন", "চালু", "kholo", "chalu"]

        contains_yt = any(kw in cmd for kw in yt_keywords)
        contains_gg = any(kw in cmd for kw in gg_keywords)
        contains_search = any(kw in cmd for kw in search_keywords)

        if contains_yt or contains_gg or contains_search:
            target_app = "youtube" if contains_yt else ("google" if contains_gg else "")

            noise_words = [
                "এ", "তে", "করে", "দিয়ে", "দাও", "করো", "নিয়ে", "ইন", "in", "open",
                "koro", "search", "খুলো", "ওপেন", "চালু", "করুন", "লাগাও", "please",
                "app", "অ্যাপ", "কে", "রে"
            ]
            all_to_remove = sorted(
                list(set(search_keywords + yt_keywords + gg_keywords + open_keywords + noise_words)),
                key=lambda x: len(x),
                reverse=True
            )

            query = cmd
            # Direct YouTube play command (e.g., 'youtube e <song>' or Bengali variants)
            if cmd.startswith('youtube e '):
                yt_query = cmd[len('youtube e '):].strip()
                success, title, msg, watch_url = MediaController.play_youtube(yt_query)
                return msg
            if cmd.startswith('youtube এ '):
                yt_query = cmd[len('youtube এ '):].strip()
                success, title, msg, watch_url = MediaController.play_youtube(yt_query)
                return msg
            for word in all_to_remove:
                pattern = rf"(^|[^\w\u0980-\u09FF]){re.escape(word)}($|[^\w\u0980-\u09FF])"
                query = re.sub(pattern, " ", query, flags=re.IGNORECASE)

            query = re.sub(r"\s+", " ", query).strip()

            if query:
                if not target_app:
                    target_app = "google"
                if target_app == "youtube":
                    SearchHelper.search_in_youtube(query)
                    return f"ইউটিউবে {query} সার্চ করা হচ্ছে"
                else:
                    SearchHelper.search_in_google(query)
                    return f"গুগলে {query} সার্চ করা হচ্ছে"
            elif target_app:
                if target_app == "youtube":
                    return "PROMPT_SEARCH|youtube|ইউটিউবে কি দেখতে চান?"
                else:
                    return "PROMPT_SEARCH|google|গুগলে কি সার্চ করবো?"

        # ৫. সময় এবং তারিখ কমান্ড
        time_keywords = ["সময়", "সময়", "time", "বাজে", "ঘড়ি"]
        date_keywords = ["তারিখ", "date", "আজকের দিন", "মাস", "সাল"]
        if any(kw in cmd for kw in time_keywords) or any(kw in cmd for kw in date_keywords):
            if any(kw in cmd for kw in time_keywords):
                return DateHelper.get_current_time_bengali()
            return DateHelper.get_current_date_bengali()

        # ৬. ল্যাপটপ ব্যাটারি ও চার্জ সংক্রান্ত কমান্ড
        if any(kw in cmd for kw in ["চার্জ", "battery", "ব্যাটারি"]):
            info = BatteryHelper.get_battery_info()
            pct = info.get("percent", -1)
            if pct >= 0:
                charging_str = " এবং বর্তমানে চার্জ হচ্ছে" if info.get("charging") else ""
                return f"আপনার ল্যাপটপের বর্তমান চার্জ {pct} শতাংশ{charging_str}।"
            return "ল্যাপটপের ব্যাটারি তথ্য পাওয়া যায়নি।"

        # ৭. ক্যামেরা / ছবি তোলা কমান্ড
        if any(kw in cmd for kw in ["ছবি তোলো", "ছবি তুলুন", "ক্যামেরা খোলো", "capture", "take photo"]):
            success, img_path, msg = CameraHelper.capture_photo()
            if success and img_path:
                vision_analysis = VisionHelper.process_image(img_path)
                return f"ছবি তোলা হয়েছে। {vision_analysis}"
            return msg

        # ৮. স্ক্রল কমান্ড
        if any(cls.contains_word(cmd, w) for w in ["up", "উপরে", "উঠো"]):
            DesktopAutomationHelper.scroll_up()
            return "উপরে যাওয়া হচ্ছে"

        if any(cls.contains_word(cmd, w) for w in ["down", "নিচে", "নামো"]):
            DesktopAutomationHelper.scroll_down()
            return "নিচে যাওয়া হচ্ছে"

        # ৯. কল কমান্ড (কী-ওয়ার্ডসহ)
        if "call" in cmd or "কল" in cmd or "ফোন" in cmd:
            input_text = cmd
            call_keywords = ["call", "কল", "ফোন", "করো", "করুন", "দাও", "লাগাও", "নাম্বারে", "নম্বরে"]
            for kw in call_keywords:
                input_text = input_text.replace(kw, "")
            name_or_number = re.sub(r"[কে|রে]$", "", input_text.strip()).strip()

            if name_or_number:
                digits = re.sub(r"[^0-9]", "", name_or_number)
                if len(digits) == 11:
                    return cls.make_call(digits, digits)
                if 3 <= len(digits) < 11:
                    result = ContactHelper.get_phone_number_by_last_digits(digits)
                    if result:
                        return cls.make_call(result[1], result[0])
                number = ContactHelper.get_phone_number_by_name(name_or_number)
                if number:
                    return cls.make_call(number, name_or_number)
                return "নাম্বারটি সঠিক নয়" if digits else f"দুঃখিত, {name_or_number} পাওয়া যায়নি"

        # ১০. মেসেজ / এসএমএস / হোয়াটসঅ্যাপ মেসেজ পাঠানো
        sms_keywords = ["মেসেজ", "এসএমএস", "sms", "message"]
        if any(kw in cmd for kw in sms_keywords):
            raw_digits = re.sub(r"[^0-9]", "", cmd)
            clean_text = cmd
            for w in ["মেসেজ", "পাঠাও", "দাও", "করো", "এসএমএস", "sms", "message", "send", "হোয়াটসঅ্যাপে", "whatsapp", "কে", "নাম্বারে"]:
                clean_text = clean_text.replace(w, "")

            target_phone = ""
            msg_body = ""
            if len(raw_digits) >= 11:
                target_phone = raw_digits[:11]
                msg_body = clean_text.replace(target_phone, "").strip()
            else:
                words = clean_text.split()
                if words:
                    found_number = ContactHelper.get_phone_number_by_name(words[0])
                    if found_number:
                        target_phone = found_number
                        msg_body = " ".join(words[1:]).strip()
                    else:
                        msg_body = clean_text.strip()

            if not msg_body:
                msg_body = "হ্যালো, কেমন আছেন?"

            if target_phone:
                return SmsHelper.send_sms(target_phone, msg_body)
            else:
                return "দয়া করে কার কাছে মেসেজ পাঠাতে চান তার নাম্বার বা কন্টাক্ট নাম বলুন।"

        # ১১. সরাসরি ১১ ডিজিটের নাম্বার বললে কল
        clean_input = re.sub(r"[কে|রে]$", "", cmd).strip()
        digits_only = re.sub(r"[^0-9]", "", clean_input)
        if len(digits_only) == 11:
            return cls.make_call(digits_only, digits_only)

        # ১১. সরাসরি কন্টাক্ট নাম বললে কল (১-২ শব্দের নাম হলে)
        words = cmd.split()
        if len(words) <= 2:
            number = ContactHelper.get_phone_number_by_name(clean_input)
            if number:
                return cls.make_call(number, clean_input)

        # ১২. সাধারণ অ্যাপ ওপেন
        has_open_kw = any(kw in cmd for kw in open_keywords)
        app_name = cmd
        to_clean = open_keywords + [
            "করো", "করুন", "দাও", "দিয়ে", "দিয়ে", "অ্যাপটি", "অ্যাপ", "app",
            "please", "প্লিজ", "koro", "kore", "dao"
        ]
        for kw in to_clean:
            app_name = re.sub(rf"(^|[^\w\u0980-\u09FF]){re.escape(kw)}($|[^\w\u0980-\u09FF])", " ", app_name, flags=re.IGNORECASE)
        app_name = re.sub(r"\s+", " ", app_name).strip()

        if app_name and (has_open_kw or app_name in cls.APP_NAME_MAPPING):
            mapped_name = cls.APP_NAME_MAPPING.get(app_name, app_name)
            res = AppHelper.open_app(mapped_name)
            if "খুঁজে পাওয়া যায়নি" not in res:
                return res

        # ১৩. অ্যাপ বন্ধ বা হোম স্ক্রিনে যাওয়া
        if any(cls.contains_word(cmd, w) for w in ["বন্ধ", "কাটো", "exit", "close"]):
            return AppHelper.close_current_app()

        # ১৪. হাইব্রিড এআই ডিসিশন ইঞ্জিন ফলব্যাক (Ollama Qwen + Fast NLU + Task Planner)
        try:
            if cls._decision_engine is None:
                from src.intelligence.decision_engine import HybridDecisionEngine
                cls._decision_engine = HybridDecisionEngine()
            _, h_reply = cls._decision_engine.process_query(command)
            if h_reply and "বুঝতে পারিনি" not in h_reply:
                return h_reply
        except Exception:
            pass

        return "UNKNOWN_COMMAND"

    _decision_engine = None

    @classmethod
    def is_a_command(cls, command: str) -> bool:
        """
        Determines if an utterance is intended as an assistant command.
        """
        from src.intelligence.requested_feature_router import RequestedFeatureRouter
        return RequestedFeatureRouter.is_request_in_scope(command)

    @staticmethod
    def is_greeting(command: str) -> bool:
        lower = command.lower()
        return any(cmd in lower for cmd in ["hello", "hi", "হ্যালো", "নমস্কার", "সালাম"])
