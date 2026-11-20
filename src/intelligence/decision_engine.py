"""
VoiceMate Intelligence - Hybrid Decision Engine Module.
Orchestrates Fast Command Routing, Local Ollama Qwen3:4b LLM reasoning,
Contextual Slot Filling, Tool Selection, Safety Validation, and Action Verification.
"""
from typing import Tuple, Dict, Any, Optional
from src.intelligence.intent_engine import Intent, IntentResult, IntentEngine
from src.intelligence.fast_router import FastCommandRouter
from src.intelligence.context_manager import ContextManager
from src.intelligence.gemini_client import GeminiClient
from src.intelligence.ollama_client import OllamaClient
from src.intelligence.action_verifier import ActionVerifier
from src.intelligence.safety_guard import SafetyGuard
from src.helpers.media_controller import MediaController
from src.helpers.app_helper import AppHelper
from src.helpers.date_helper import DateHelper
from src.helpers.battery_helper import BatteryHelper
from src.helpers.search_helper import SearchHelper
from src.helpers.desktop_automation_helper import DesktopAutomationHelper
from src.helpers.camera_helper import CameraHelper
from src.helpers.vision_helper import VisionHelper
from src.product_agent.product_controller import ProductController


class HybridDecisionEngine:
    """
    Central brain determining user intent, selecting tools, enforcing safety,
    executing verified actions, and maintaining dialog context.
    """
    def __init__(self, ollama_host: str = "http://localhost:11434", ollama_model: str = "qwen3:4b"):
        self.gemini = GeminiClient()
        self.ollama = OllamaClient(host=ollama_host, model=ollama_model)
        self.context = ContextManager()

    def process_query(self, user_text: str) -> Tuple[IntentResult, str]:
        """
        Processes user speech/text input through the hybrid pipeline.
        Returns: (IntentResult, response_spoken_message)
        """
        raw_text = (user_text or "").strip()
        if not raw_text:
            return IntentResult(Intent.UNKNOWN, "none", 0.0), ""

        # -------------------------------------------------------------
        # STEP 1: Context Follow-Up Resolution (Slot Filling & Confirmation)
        # -------------------------------------------------------------
        followup_data = self.context.resolve_followup(raw_text)
        intent_res: Optional[IntentResult] = None

        # -------------------------------------------------------------
        # STEP 1b: Autonomous Multi-Step Task Planner Check
        # Detects complex goals (Assignment solving, Website creation, Deep Research)
        # -------------------------------------------------------------
        lower_q = raw_text.lower()
        is_autonomous_goal = (
            (any(w in lower_q for w in ["assignment", "অ্যাসাইনমেন্ট"]) and any(w in lower_q for w in ["সলভ", "solve", "সমাধান", "docx", "pdf", "করো"])) or
            (any(w in lower_q for w in ["website", "ওয়েবসাইট"]) and any(w in lower_q for w in ["বানিয়ে", "তৈরি", "build", "create", "make", "দাও", "করো"])) or
            (any(w in lower_q for w in ["রিসার্চ রিপোর্ট", "গবেষণামূলক রিপোর্ট", "deep research", "research report"]))
        )
        if is_autonomous_goal and not followup_data:
            from src.agent_brain.task_planner import TaskPlanner
            plan = TaskPlanner.create_plan(raw_text)
            executed_plan = TaskPlanner.execute_plan(plan)
            intent_res = IntentResult(
                intent=Intent.SUBSYSTEM_TASK,
                action="autonomous_plan",
                confidence=0.99,
                parameters={"plan": executed_plan.to_dict()},
                raw_query=raw_text,
                source="task_planner"
            )
            response_msg = executed_plan.final_summary
            self.context.record_turn("user", raw_text)
            self.context.record_turn("assistant", response_msg)
            return intent_res, response_msg

        if followup_data:
            intent_name = followup_data.get("intent", "unknown")
            action = followup_data.get("action", "none")
            params = followup_data.get("parameters", {})
            try:
                intent_enum = Intent(intent_name)
            except Exception:
                intent_enum = Intent.UNKNOWN

            intent_res = IntentResult(
                intent=intent_enum,
                action=action,
                confidence=0.98,
                parameters=params,
                raw_query=raw_text,
                source="context_manager"
            )

        # -------------------------------------------------------------
        # STEP 2: Fast Command Router (Sub-10ms Fast Mode)
        # -------------------------------------------------------------
        if not intent_res:
            intent_res = FastCommandRouter.match(raw_text)

        # -------------------------------------------------------------
        # STEP 3a: Cloud AI Mode via Google Gemini API (High-Speed, 0% Laptop RAM/CPU)
        # -------------------------------------------------------------
        if not intent_res and self.gemini.is_available():
            gemini_output = self.gemini.analyze_query(raw_text, self.context.history)
            if gemini_output:
                intent_str = gemini_output.get("intent", "unknown")
                action_str = gemini_output.get("action", "none")
                parameters = gemini_output.get("parameters", {})
                ai_reply = gemini_output.get("reply", "")

                try:
                    intent_enum = Intent(intent_str)
                except Exception:
                    intent_enum = Intent.UNKNOWN

                intent_res = IntentResult(
                    intent=intent_enum,
                    action=action_str,
                    confidence=0.96,
                    parameters=parameters,
                    raw_query=raw_text,
                    source="gemini_cloud"
                )
                if ai_reply:
                    intent_res.parameters["ai_reply"] = ai_reply

        # -------------------------------------------------------------
        # STEP 3b: Local AI Mode via Ollama Qwen3:4b (Offline Local Brain)
        # -------------------------------------------------------------
        if not intent_res and self.ollama.is_available():
            ollama_output = self.ollama.analyze_query(raw_text, self.context.history)
            if ollama_output:
                intent_str = ollama_output.get("intent", "unknown")
                action_str = ollama_output.get("action", "none")
                parameters = ollama_output.get("parameters", {})
                ai_reply = ollama_output.get("reply", "")

                try:
                    intent_enum = Intent(intent_str)
                except Exception:
                    intent_enum = Intent.UNKNOWN

                intent_res = IntentResult(
                    intent=intent_enum,
                    action=action_str,
                    confidence=0.88,
                    parameters=parameters,
                    raw_query=raw_text,
                    source="ollama_qwen"
                )
                if ai_reply:
                    intent_res.parameters["ai_reply"] = ai_reply

        # -------------------------------------------------------------
        # STEP 4: Smart Semantic Fallback (Works even when Ollama is Offline)
        # -------------------------------------------------------------
        if not intent_res:
            intent_res = self._fallback_semantic_classifier(raw_text)

        # -------------------------------------------------------------
        # STEP 5: Safety Guard Validation
        # -------------------------------------------------------------
        is_safe, safety_prompt = SafetyGuard.check_safety(
            intent_name=intent_res.intent.value,
            action=intent_res.action,
            parameters=intent_res.parameters,
            query_text=raw_text
        )

        if not is_safe:
            # Register pending action in context awaiting confirmation
            self.context.set_awaiting_slot("confirmation", {
                "intent": intent_res.intent.value,
                "action": intent_res.action,
                "parameters": intent_res.parameters
            })
            self.context.record_turn("user", raw_text)
            self.context.record_turn("assistant", safety_prompt)
            return intent_res, safety_prompt

        # -------------------------------------------------------------
        # STEP 6: Tool Execution & Verification
        # -------------------------------------------------------------
        response_msg = self._execute_intent(intent_res)

        # Update context history
        self.context.record_turn("user", raw_text)
        self.context.record_turn("assistant", response_msg)

        return intent_res, response_msg

    def _execute_intent(self, res: IntentResult) -> str:
        """Dispatches verified tool execution and formats final spoken response."""
        intent = res.intent
        action = res.action
        params = res.parameters

        # 1. GREETING
        if intent == Intent.GREETING:
            return "হ্যালো! আমি ভয়েস মেট, আপনার ল্যাপটপ অ্যাসিস্ট্যান্ট। বলুন আমি আপনাকে কিভাবে সাহায্য করতে পারি?"

        # 2. PLAY MUSIC / YOUTUBE
        if intent == Intent.PLAY_MUSIC:
            song = params.get("song_name") or "bangla top song"
            success, title, msg, watch_url = MediaController.play_youtube(song)
            verified, verify_msg = ActionVerifier.verify_youtube_playback(watch_url, title)
            self.context.set_media_state(title, is_playing=verified)
            return verify_msg

        # 3. MEDIA CONTROLS
        if intent == Intent.MEDIA_CONTROL:
            if action == "pause":
                _, msg = MediaController.pause()
                self.context.is_media_playing = False
                return msg
            elif action == "resume":
                _, msg = MediaController.resume()
                self.context.is_media_playing = True
                return msg
            elif action == "stop":
                _, msg = MediaController.stop()
                self.context.is_media_playing = False
                return msg
            elif action == "next":
                _, msg = MediaController.next_track()
                return msg
            elif action == "previous":
                _, msg = MediaController.previous_track()
                return msg

        # 4. VOLUME CONTROLS
        if intent == Intent.VOLUME_CONTROL:
            direction = params.get("direction", "up")
            if direction == "up":
                _, msg = MediaController.volume_up()
                return msg
            elif direction == "down":
                _, msg = MediaController.volume_down()
                return msg
            elif direction == "mute":
                _, msg = MediaController.toggle_mute()
                return msg

        # 5. OPEN APPLICATION
        if intent == Intent.OPEN_APPLICATION:
            app = params.get("app_name", "chrome")
            disp = params.get("display_name", app)

            if app == "youtube":
                SearchHelper.open_website("https://www.youtube.com")
                self.context.set_active_app("youtube")
                self.context.set_awaiting_slot("youtube_query")
                return "ইউটিউব ওপেন করা হয়েছে। আপনি কি দেখতে বা শুনতে চান?"

            res_msg = AppHelper.open_app(app)
            verified, verified_msg = ActionVerifier.verify_app_launch(disp, res_msg)
            if verified:
                self.context.set_active_app(disp)
            return verified_msg

        # 6. CLOSE APPLICATION
        if intent == Intent.CLOSE_APPLICATION:
            return AppHelper.close_current_app()

        # 7. SYSTEM INFORMATION
        if intent == Intent.SYSTEM_INFO:
            info_type = params.get("info_type", "time")
            if info_type == "time":
                return DateHelper.get_current_time_bengali()
            elif info_type == "date":
                return DateHelper.get_current_date_bengali()
            elif info_type == "battery":
                info = BatteryHelper.get_battery_info()
                pct = info.get("percent", -1)
                charging = info.get("charging", False)
                ch_str = " এবং বর্তমানে চার্জ হচ্ছে" if charging else ""
                return f"আপনার ল্যাপটপের বর্তমান চার্জ {pct} শতাংশ{ch_str}।"

        # 8. SEARCH YOUTUBE
        if intent == Intent.SEARCH_YOUTUBE:
            query = params.get("search_query", "songs")
            SearchHelper.search_in_youtube(query)
            self.context.set_active_app("youtube")
            return f"ইউটিউবে {query} সার্চ করা হচ্ছে"

        # 8b. PRODUCT SEARCH & PRICE RESEARCH
        if intent in [Intent.PRODUCT_SEARCH, Intent.PRICE_CHECK]:
            query = params.get("query", "")
            budget = params.get("budget")
            res = ProductController.search_and_research(query=query, budget=budget)
            if res.get("products"):
                self.context.set_product_context(query, res["products"], res.get("cheapest"))
            return res.get("voice_summary", "প্রোডাক্ট খোঁজা সম্পন্ন হয়েছে।")

        # 8c. CHEAPEST PRODUCT QUERY
        if intent == Intent.CHEAPEST_PRODUCT:
            products = params.get("products") or self.context.last_products
            if not products:
                query = params.get("query", "products")
                products = ProductController.search_products(query)
                if products:
                    self.context.set_product_context(query, products)

            if products:
                cheapest = ProductController.get_cheapest_product(products)
                if cheapest:
                    self.context.selected_product = cheapest
                    return (
                        f"সবচেয়ে কম দামি হলো {cheapest.seller}-এ {cheapest.name}, "
                        f"যার দাম {cheapest.format_price_display()}। "
                        f"স্ট্যাটাস: {cheapest.availability}।"
                    )
            return "দুঃখিত, কোনো প্রোডাক্টের দামের তথ্য খুঁজে পাওয়া যায়নি।"

        # 8d. PRODUCT SPECIFICATIONS & FEATURES
        if intent == Intent.PRODUCT_SPECS:
            product = params.get("product") or self.context.selected_product
            if not product and self.context.last_products:
                product = self.context.last_products[0]

            if not product:
                query = params.get("query", "")
                if query:
                    prods = ProductController.search_products(query)
                    if prods:
                        product = prods[0]
                        self.context.set_product_context(query, prods, product)

            if product:
                details = ProductController.extract_product_details(product)
                return (
                    f"{details['name']}-এর স্পেসিফিকেশন ও ফিচার:\n"
                    f"{details['specs_text']}। "
                    f"বর্তমান দাম: {details['formatted_price']} ({details['seller']})।"
                )
            return "দুঃখিত, কোনো প্রোডাক্টের স্পেসিফিকেশন পাওয়া যায়নি।"

        # 8e. COMPARE PRODUCTS
        if intent == Intent.COMPARE_PRODUCTS:
            products = params.get("products") or self.context.last_products
            query = params.get("query") or self.context.last_product_search or "products"
            if not products:
                products = ProductController.search_products(query)
                if products:
                    self.context.set_product_context(query, products)

            if products:
                comp = ProductController.compare_product_prices(products, query=query)
                return comp.summary_bn
            return "তুলনা করার মতো পর্যাপ্ত প্রোডাক্ট পাওয়া যায়নি।"

        # 8f. OPEN PRODUCT WEBPAGE
        if intent == Intent.OPEN_PRODUCT_PAGE:
            product = params.get("product") or self.context.selected_product
            if not product and self.context.last_products:
                product = self.context.last_products[0]

            if product:
                success, msg = ProductController.open_product_page(product)
                return msg
            return "ওপেন করার জন্য কোনো প্রোডাক্ট নির্বাচন করা নেই।"

        # 9. SEARCH WEB / GOOGLE
        if intent == Intent.SEARCH_WEB:
            query = params.get("query", "")
            SearchHelper.search_in_google(query)
            return f"গুগলে {query} সার্চ করা হচ্ছে"

        # 10. DESKTOP NAVIGATION
        if intent == Intent.DESKTOP_NAVIGATION:
            if action == "scroll_up":
                DesktopAutomationHelper.scroll_up()
                return "উপরে যাওয়া হচ্ছে"
            elif action == "scroll_down":
                DesktopAutomationHelper.scroll_down()
                return "নিচে যাওয়া হচ্ছে"
            elif action == "go_home":
                DesktopAutomationHelper.go_home()
                return "ডেস্কটপ দেখানো হচ্ছে"

        # 11. TYPING MODE
        if intent == Intent.TYPING_MODE:
            return "ACTION_START_TYPING"

        # 12. TAKE PHOTO
        if intent == Intent.TAKE_PHOTO:
            success, img_path, msg = CameraHelper.capture_photo()
            if success and img_path:
                vision_analysis = VisionHelper.process_image(img_path)
                return f"ছবি তোলা হয়েছে। {vision_analysis}"
            return msg

        # 13. CONFIRM / CANCEL PENDING ACTION
        if intent == Intent.CONFIRM_ACTION:
            pending = params.get("action", "")
            return f"অনুমতি পাওয়া গেছে। '{pending}' কার্যকর করা হচ্ছে।"

        if intent == Intent.CANCEL_ACTION:
            return "কমান্ডটি বাতিল করা হয়েছে।"

        # 14. SUBSYSTEM TASKS (Delegated to external engines)
        if intent == Intent.SUBSYSTEM_TASK:
            query = params.get("query", "")
            if action == "docling":
                return f"ACTION_DOCLING_TASK|{query}"
            elif action == "document":
                return f"ACTION_DOCUMENT_TASK|{query}"
            elif action == "coder":
                return f"ACTION_CODER_TASK|{query}"
            elif action == "canvas":
                return f"ACTION_CANVAS_TASK|{query}"
            elif action == "n8n":
                return f"ACTION_N8N_TASK|{query}"
            elif action == "api_gateway":
                return f"ACTION_API_GATEWAY_TASK|{query}"
            elif action == "brain":
                return f"ACTION_BRAIN_TASK|{query}"

        # 15. GENERAL CONVERSATION OR AI REPLY
        if "ai_reply" in params and params["ai_reply"]:
            return params["ai_reply"]

        return "দুঃখিত, কমান্ডটি বুঝতে পারিনি। অনুগ্রহ করে আবার বলুন।"

    def _fallback_semantic_classifier(self, text: str) -> IntentResult:
        """
        Autonomous semantic intent classifier when Ollama LLM is offline or busy.
        Enables natural language comprehension without rigid command matching.
        """
        import re
        lower = text.lower().strip()

        # 1. Identity & Persona
        if any(w in lower for w in ["তুমি কে", "তোমার নাম", "who are you", "what is your name", "who made you", "তোমাকে কে বানিয়েছে"]):
            return IntentResult(
                intent=Intent.UNKNOWN,
                action="persona_reply",
                confidence=0.95,
                parameters={"ai_reply": "আমি VoiceMate, আপনার ইন্টেলিজেন্ট অটোনোমাস এআই অ্যাসিস্ট্যান্ট। আমি আপনার মৌখিক নির্দেশে কাজ করতে পারি।"},
                raw_query=text,
                source="semantic_fallback"
            )

        # 2. Capabilities & Help
        if any(w in lower for w in ["কি করতে পারো", "কি পারো", "what can you do", "তোমার কাজ কি", "সাহায্য করো", "হেল্প"]):
            return IntentResult(
                intent=Intent.UNKNOWN,
                action="capability_reply",
                confidence=0.95,
                parameters={"ai_reply": "আমি ইউটিউবে গান চালানো, পণ্যের বাজারদর তুলনা, অ্যাসাইনমেন্ট সমাধান, সম্পূর্ণ ওয়েবসাইট তৈরি, অ্যাপ চালু ও ইন্টারনেটে গবেষণা করতে পারি। আপনি আমাকে যেকোনো স্বাভাবিক ভাষায় নির্দেশ দিতে পারেন।"},
                raw_query=text,
                source="semantic_fallback"
            )

        # 3. Chit-Chat / Well-being
        if any(w in lower for w in ["কেমন আছো", "কি অবস্থা", "how are you", "kemon acho", "ভালো আছো"]):
            return IntentResult(
                intent=Intent.UNKNOWN,
                action="chitchat_reply",
                confidence=0.95,
                parameters={"ai_reply": "আমি চমৎকার আছি, ধন্যবাদ! আপনার জন্য এখন কী করতে পারি বলুন?"},
                raw_query=text,
                source="semantic_fallback"
            )

        # 4. Natural Music / Entertainment Intent
        if any(w in lower for w in ["গান শুনতে চাই", "গান শোনাও", "গান ছাড়ো", "গান বাজাও", "গান দাও", "একটা গান", "song শুনতে"]):
            # Extract possible song title
            clean_song = lower
            for kw in ["একটা গান শোনাও", "গান শুনতে চাই", "গান শোনাও", "গান ছাড়ো", "গান বাজাও", "গান দাও", "গান", "song", "play"]:
                clean_song = clean_song.replace(kw, "")
            clean_song = clean_song.strip() or "top bangla hits"
            return IntentResult(
                intent=Intent.PLAY_MUSIC,
                action="play_youtube",
                confidence=0.90,
                parameters={"song_name": clean_song},
                raw_query=text,
                source="semantic_fallback"
            )

        # 5. Battery / System status
        if any(w in lower for w in ["চার্জ কত", "ব্যাটারি কত", "battery status", "চার্জ কতটুকু", "charge koto"]):
            return IntentResult(
                intent=Intent.SYSTEM_INFO,
                action="get_system_info",
                confidence=0.92,
                parameters={"info_type": "battery"},
                raw_query=text,
                source="semantic_fallback"
            )

        # 6. Time & Date
        if any(w in lower for w in ["কয়টা বাজে", "কয়টা বাজে", "সময় কত", "সময় কত", "time koto", "time কত", "আজকে কি বার", "আজকে কত তারিখ"]):
            info = "date" if any(w in lower for w in ["তারিখ", "বার", "date"]) else "time"
            return IntentResult(
                intent=Intent.SYSTEM_INFO,
                action="get_system_info",
                confidence=0.92,
                parameters={"info_type": info},
                raw_query=text,
                source="semantic_fallback"
            )

        # 7. Natural Product Price Inquiry
        if any(w in lower for w in ["দাম কত", "প্রাইস কত", "price কত", "dam koto", "কত টাকা"]):
            from src.intelligence.intent_engine import IntentEngine
            query = IntentEngine.extract_product_query(text) or text
            budget = IntentEngine.extract_budget(text)
            return IntentResult(
                intent=Intent.PRODUCT_SEARCH,
                action="search_products",
                confidence=0.88,
                parameters={"query": query, "budget": budget},
                raw_query=text,
                source="semantic_fallback"
            )

        # 8. Web Search / Knowledge
        search_terms = ["কীভাবে", "কিভাবে", "কোথায়", "কোথায়", "কেন", "কার", "how to", "what is", "where is", "who is"]
        if any(kw in lower for kw in search_terms) or len(text.split()) > 3:
            return IntentResult(
                intent=Intent.SEARCH_WEB,
                action="search_google",
                confidence=0.75,
                parameters={"query": text},
                raw_query=text,
                source="semantic_fallback"
            )

        # 9. Conversational clarifying reply
        return IntentResult(
            intent=Intent.UNKNOWN,
            action="clarify_reply",
            confidence=0.50,
            parameters={"ai_reply": f"আমি আপনার অনুরোধটি নিয়ে ভাবছি। আপনি কি '{text}'-এর বিষয়ে ইন্টারনেটে তথ্য জানতে চান?"},
            raw_query=text,
            source="semantic_fallback"
        )
