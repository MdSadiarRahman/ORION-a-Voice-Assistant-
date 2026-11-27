"""
VoiceMate Laptop Agent - Agent Service Module.
Core background orchestrator managing continuous listening,
state machine, watchdog, and action execution.
"""
import time
import re
import threading
from typing import Optional, Callable
from src.command_processor import CommandProcessor
from src.helpers.tts_helper import TtsHelper
from src.helpers.voice_recognizer_helper import VoiceRecognizerHelper
from src.helpers.desktop_automation_helper import DesktopAutomationHelper
from src.helpers.search_helper import SearchHelper
from src.browser_agent.browser_task_runner import BrowserTaskRunner
from src.document_agent.document_task_runner import DocumentTaskRunner
from src.docling_agent.docling_task_runner import DoclingTaskRunner
try:
    from src.playwright_agent.playwright_task_runner import PlaywrightTaskRunner
except ImportError:
    PlaywrightTaskRunner = None
from src.assignment_agent.assignment_controller import AssignmentController

class AgentService:
    _instance: Optional['AgentService'] = None

    def __init__(self, on_state_change: Optional[Callable[[dict], None]] = None):
        AgentService._instance = self
        self.on_state_change = on_state_change

        self.is_running = False
        self.is_listening = False
        self.is_speaking = False
        self.is_typing_mode = False
        self._voice_muted = False
        self.is_waiting_for_search = False
        self.search_target = ""
        self._recent_spoken_phrases: list[tuple[float, str]] = []
        self._last_tts_end_time: float = 0.0

        # Helpers
        self.tts = TtsHelper(
            on_start=self._on_tts_start,
            on_done=self._on_tts_done
        )
        self.recognizer = VoiceRecognizerHelper(
            on_result=self.process_results,
            on_error=self._on_speech_error,
            on_ready=self._on_speech_ready,
            is_speaking_checker=self._check_is_speaking
        )

    def _check_is_speaking(self) -> bool:
        return self.is_speaking or (self.tts is not None and self.tts.is_speaking)

    def _register_spoken_phrase(self, text: str):
        if not text:
            return
        now = time.time()
        self._recent_spoken_phrases.append((now, text.lower().strip()))
        self._recent_spoken_phrases = [(t, p) for t, p in self._recent_spoken_phrases if now - t < 15.0]

    def _is_echo_of_assistant(self, spoken_text: str) -> bool:
        """
        Detects if recognized microphone text is an acoustic reflection of what the assistant just spoke.
        Only checks while speaking or within 2.5s after TTS finishes so real follow-up commands are never dropped.
        """
        if not spoken_text:
            return False
        now = time.time()
        # Only treat as potential acoustic echo while speaking or immediately after TTS ends
        if not self._check_is_speaking() and (now - self._last_tts_end_time > 2.5):
            return False

        spoken_clean = spoken_text.lower().strip()
        spoken_words = set(re.findall(r'[\w\u0980-\u09FF]+', spoken_clean))

        for t, phrase in self._recent_spoken_phrases:
            if now - t > 15.0:
                continue
            if len(spoken_clean) >= 8 and (spoken_clean in phrase or phrase in spoken_clean):
                return True
            phrase_words = set(re.findall(r'[\w\u0980-\u09FF]+', phrase))
            if len(spoken_words) >= 3 and phrase_words:
                common = spoken_words & phrase_words
                if len(common) / len(spoken_words) >= 0.8:
                    return True
        return False

    @classmethod
    def get_instance(cls) -> Optional['AgentService']:
        return cls._instance

    def _notify_state(self, message: str = ""):
        if self.on_state_change:
            try:
                self.on_state_change({
                    "is_running": self.is_running,
                    "is_listening": self.is_listening,
                    "is_speaking": self.is_speaking,
                    "is_typing_mode": self.is_typing_mode,
                    "message": message
                })
            except Exception:
                pass

    def start(self):
        """Starts the voice agent background service."""
        if self.is_running:
            return
        self.is_running = True
        self._voice_muted = False
        self.is_listening = True
        self.speak("ভয়েস মেট সক্রিয় আছে। আমি আপনার কথা শুনছি...", start_listening_after=True)
        
        # Start microphone speech recognizer
        self.recognizer.start_listening()
        self._notify_state("অ্যাসিস্ট্যান্ট সক্রিয় করা হয়েছে")

    def stop(self):
        """Stops the voice agent service."""
        self._voice_muted = False
        self.is_running = False
        self.is_listening = False
        self.recognizer.stop_listening()
        self.tts.shutdown()
        self._notify_state("অ্যাসিস্ট্যান্ট বন্ধ করা হয়েছে")

    def toggle_voice(self) -> bool:
        """Toggles active microphone speech listening on or off."""
        if not self.is_running:
            self.start()
            return bool(self.is_running and not self._voice_muted and self.recognizer.is_listening)
        currently_active = (not self._voice_muted) and (
            self.is_listening or self.is_speaking or self.recognizer.is_listening
        )
        if currently_active:
            self._voice_muted = True
            self.recognizer.stop_listening()
            self.is_listening = False
            self._notify_state("মাইক্রোফোন মিউট করা হয়েছে (টাইপ করে কমান্ড দিন)")
            return False
        self._voice_muted = False
        self.recognizer.start_listening()
        self.is_listening = bool(self.recognizer.is_listening)
        self._notify_state("আমি শুনছি...")
        return self.is_listening

    def _on_tts_start(self):
        self.is_speaking = True
        self.is_listening = False
        self._notify_state("অ্যাসিস্ট্যান্ট কথা বলছে...")

    def _on_tts_done(self):
        self.is_speaking = False
        self._last_tts_end_time = time.time()
        if self.is_running and not self._voice_muted:
            self.is_listening = True
            self._notify_state("আমি শুনছি...")

    def _on_speech_ready(self):
        if self.is_running and not self.is_speaking and not self._voice_muted:
            self.is_listening = True
            status_text = "আমি লিখছি... বলুন" if self.is_typing_mode else "আমি শুনছি..."
            self._notify_state(status_text)

    def _on_speech_error(self, err_msg: str):
        self.is_listening = False
        self._notify_state(f"অ্যাসিস্ট্যান্ট প্রস্তুত (টাইপ করে কমান্ড দিন): {err_msg}")

    def speak(self, text: str, start_listening_after: bool = True):
        """Speaks out text using TTS."""
        self._register_spoken_phrase(text)
        self.tts.speak(text)

    def process_results(self, spoken_text: str):
        """Processes recognized speech or text inputs."""
        if not spoken_text:
            return

        # Anti-Echo check: discard assistant's own voice acoustic reflection
        if self._is_echo_of_assistant(spoken_text):
            print(f"[VoiceMate Anti-Echo]: Discarded self-echo: '{spoken_text}'", flush=True)
            return

        spoken_lower = spoken_text.lower().strip()
        self._notify_state(f"শোনা গেছে: {spoken_text}")

        # ১. টাইপিং মোড সক্রিয় থাকলে
        if self.is_typing_mode:
            stop_typing_commands = {
                "বন্ধ",
                "টাইপিং বন্ধ",
                "টাইপিং বন্ধ করো",
                "টাইপিং মোড বন্ধ",
                "টাইপিং মোড বন্ধ করুন",
                "টাইপিং মোড বন্ধ করো",
                "টাইপিং মোড অফ",
                "stop typing",
                "stop typing mode",
                "typing mode off",
                "exit typing mode",
            }
            if spoken_lower.strip(" .,!?:;।") in stop_typing_commands:
                self.is_typing_mode = False
                self.speak("টাইপিং মোড বন্ধ করা হয়েছে।", start_listening_after=True)
                return
            DesktopAutomationHelper.append_text(f"{spoken_text.strip()} ")
            return

        # ২. সার্চ কুয়েরি উত্তরের অপেক্ষায় থাকলে
        if self.is_waiting_for_search:
            self.handle_search_query(spoken_text)
            return

        # ৩. কমান্ড ও ন্যাচারাল ল্যাঙ্গুয়েজ প্রসেসিং (Autonomous Decision Pipeline)
        response = CommandProcessor.process_command(spoken_text)

        if response == "ACTION_START_TYPING":
            self.is_typing_mode = True
            DesktopAutomationHelper.focus_and_open_keyboard()
            self.speak(
                "টাইপিং মোড চালু হয়েছে। যে অ্যাপে লিখবেন সেখানে আগে লেখার ঘরে ক্লিক করুন; "
                "এখন আপনার বলা কথা সেখানে লেখা হবে। বন্ধ করতে 'টাইপিং বন্ধ' বলুন।",
                start_listening_after=True,
            )
            return

        if response.startswith("ACTION_DOCUMENT_QA|"):
            document_query = response.split("|", 1)[1].strip()
            self.speak("আমি local PDF/Word ফাইল খুঁজে প্রশ্নের উত্তর বের করছি...", start_listening_after=False)

            def on_document_progress(message: str):
                self._notify_state(message)

            def run_document_answer():
                try:
                    from src.document_intelligence.document_answer_service import DocumentAnswerService

                    result = DocumentAnswerService.answer(
                        document_query,
                        progress_cb=on_document_progress,
                    )
                except (ImportError, OSError, RuntimeError, ValueError) as exc:
                    result = f"ডকুমেন্টের উত্তর তৈরি করা যায়নি: {exc}"
                self._notify_state(result)
                summary = re.split(r"(?<=[.!?।])\s|\n", result, maxsplit=1)[0]
                self.speak(summary, start_listening_after=True)

            threading.Thread(target=run_document_answer, daemon=True).start()
            return

        if response.startswith("ACTION_PRODUCT_PRICE|"):
            product_query = response.split("|", 1)[1].strip()
            self.speak("একাধিক retailer-এর live listing পরীক্ষা করছি...", start_listening_after=False)

            def run_product_price_search():
                try:
                    from src.product_agent.product_price_search import ProductPriceSearch

                    result = ProductPriceSearch.search(product_query)
                    message = result.get("message", "পণ্যের দাম পাওয়া যায়নি।")
                except (OSError, RuntimeError, ValueError) as exc:
                    message = f"পণ্যের দাম খোঁজা যায়নি: {exc}"
                self._notify_state(message)
                self.speak(message.splitlines()[0], start_listening_after=True)

            threading.Thread(target=run_product_price_search, daemon=True).start()
            return

        if response.startswith("PROMPT_SEARCH|"):
            parts = response.split("|", 2)
            self.search_target = parts[1] if len(parts) > 1 else "google"
            self.is_waiting_for_search = True
            self.speak(parts[2] if len(parts) > 2 else "কী সার্চ করব?", start_listening_after=True)
            return

        if response == "UNKNOWN_COMMAND" or response.startswith("ACTION_"):
            self.speak("এই কমান্ডটি সমর্থিত নয়।", start_listening_after=True)
            return

        # অ্যাসাইনমেন্ট এজেন্ট টাস্ক (Assignment Solver)
        if response.startswith("ACTION_ASSIGNMENT_TASK|"):
            assignment_query = response.split("|", 1)[1].strip()
            self.speak("আমি অ্যাসাইনমেন্ট বিশ্লেষণ ও সমাধান শুরু করছি, অনুগ্রহ করে অপেক্ষা করুন...", start_listening_after=False)

            def on_assignment_finish(result_msg: str):
                self._notify_state(result_msg)
                first_line = result_msg.split("\n")[0]
                self.speak(first_line, start_listening_after=True)

            def _run_assignment():
                try:
                    result = AssignmentController.execute_assignment_workflow(assignment_query)
                    summary = result.get("voice_summary", "অ্যাসাইনমেন্ট সমাধান সম্পন্ন হয়েছে।")
                    on_assignment_finish(summary)
                except Exception as e:
                    on_assignment_finish(f"অ্যাসাইনমেন্ট সমাধানে সমস্যা হয়েছে: {str(e)}")

            threading.Thread(target=_run_assignment, daemon=True).start()
            return

        # ব্রাউজার এজেন্ট টাস্ক
        if response.startswith("ACTION_BROWSER_TASK|"):
            task = response.split("|", 1)[1]
            self.speak("আমি ব্রাউজারে কাজটি শুরু করছি। দয়া করে কিছুক্ষণ অপেক্ষা করুন...", start_listening_after=False)
            
            def on_browser_progress(msg: str):
                self._notify_state(msg)

            def on_browser_finish(result: str):
                self._notify_state(result)
                summary = result.split("\n")[0]
                self.speak(summary, start_listening_after=True)

            BrowserTaskRunner.run_in_background(
                task=task,
                on_progress=on_browser_progress,
                on_finish=on_browser_finish
            )
            return

        # ডকলিং মাল্টিমোডাল ডকুমেন্ট ইন্টেলিজেন্স ও RAG চাংকিং টাস্ক
        if response.startswith("ACTION_DOCLING_TASK|"):
            docling_query = response.split("|", 1)[1].strip()
            self.speak("আমি ডকলিং দিয়ে ডকুমেন্টটি প্রসেস করছি, অপেক্ষা করুন...", start_listening_after=False)

            def on_docling_progress(msg: str):
                self._notify_state(msg)

            def on_docling_finish(summary: str):
                self._notify_state(summary)
                first_line = summary.split("\n")[0]
                self.speak(first_line, start_listening_after=True)

            DoclingTaskRunner.run_task(
                task_query=docling_query,
                on_progress=on_docling_progress,
                on_finish=on_docling_finish
            )
            return

        # ডকুমেন্ট ইন্টেলিজেন্স (PyMuPDF) টাস্ক
        if response.startswith("ACTION_DOCUMENT_TASK|"):
            doc_query = response.split("|", 1)[1].strip()
            self.speak("আমি ডকুমেন্টটি পড়ছি, অনুগ্রহ করে অপেক্ষা করুন...", start_listening_after=False)

            def on_doc_progress(msg: str):
                self._notify_state(msg)

            def on_doc_finish(summary: str):
                self._notify_state(summary)
                self.speak(summary, start_listening_after=True)

            DocumentTaskRunner.run_document_task(
                document_query=doc_query,
                on_progress=on_doc_progress,
                on_finish=on_doc_finish
            )
            return

        # ডিটারমিনিস্টিক ওয়েব অটোমেশন (Playwright) টাস্ক
        if response.startswith("ACTION_PLAYWRIGHT_TASK|"):
            if PlaywrightTaskRunner is None:
                self.speak("দুঃখিত, ওয়েব অটোমেশন এজেন্ট বর্তমানে উপলব্ধ নেই।", start_listening_after=True)
                return
            pw_task = response.split("|", 1)[1].strip()
            self.speak("আমি ওয়েব অটোমেশনের কাজটি শুরু করছি, অপেক্ষা করুন...", start_listening_after=False)

            def on_pw_progress(msg: str):
                self._notify_state(msg)

            def on_pw_finish(result_msg: str):
                self._notify_state(result_msg)
                summary = result_msg.split("\n")[0]
                self.speak(summary, start_listening_after=True)

            PlaywrightTaskRunner.run_task(
                task_query=pw_task,
                on_progress=on_pw_progress,
                on_finish=on_pw_finish
            )
            return

        if response.startswith("ACTION_FIND_FILE|"):
            find_query = response.split("|", 1)[1].strip()
            from src.intelligence.tool_registry import ToolRegistry
            tr = ToolRegistry()
            tool_res = tr.execute("SEARCH_LOCAL_FILE", query=find_query)
            self.speak(tool_res.get("reply", "ফাইল অনুসন্ধান সম্পন্ন হয়েছে।"), start_listening_after=True)
            return

        if response.startswith("PROMPT_SEARCH|"):
            parts = response.split("|")
            self.search_target = parts[1]
            self.is_waiting_for_search = True
            self.speak(parts[2], start_listening_after=True)
            return

        if response != "UNKNOWN_COMMAND":
            self.speak(response, start_listening_after=True)
            return
        else:
            # Try HybridDecisionEngine (python_rules first, then Ollama, then Gemini)
            try:
                res_intent, res_reply = self.decision_engine.process_query(spoken_text)
                if res_intent and getattr(res_intent, "source", "") == "python_rules":
                    # Execute the actual tool action from ToolRegistry result
                    action = getattr(res_intent, "action", "")
                    if action == "OPEN_APPLICATION":
                        from src.intelligence.tool_registry import ToolRegistry
                        tr = ToolRegistry()
                        tool_res = tr.execute("OPEN_APPLICATION", app_name=res_intent.parameters.get("app_name", ""))
                        reply = tool_res.get("reply", res_reply)
                    elif action == "SEARCH_LOCAL_FILE":
                        from src.document_intelligence.file_search import FileSearchEngine
                        eng = FileSearchEngine()
                        query = res_intent.parameters.get("query", spoken_text)
                        results = eng.search(query, search_content=False, max_results=3)
                        if results:
                            names = "، ".join([r.filename for r in results[:3]])
                            reply = f"আমি খুঁজে পেয়েছি: {names}"
                        else:
                            reply = "আপনার পিসিতে ফাইলটি খুঁজে পাওয়া যায়নি।"
                    else:
                        reply = res_reply
                    if reply:
                        self.speak(reply, start_listening_after=True)
                        return
                if res_reply:
                    self.speak(res_reply, start_listening_after=True)
                    return
            except Exception:
                pass
            self.speak("দুঃখিত, আমি আপনার কথা বুঝতে পারিনি। অনুগ্রহ করে আবার বলুন।", start_listening_after=True)
            return

    def handle_search_query(self, query: str):
        """Handles follow-up search query."""
        self.is_waiting_for_search = False
        target = self.search_target
        self.search_target = ""

        if target == "youtube":
            SearchHelper.search_in_youtube(query)
            self.speak(f"আমি ইউটিউবে {query} সার্চ করছি।", start_listening_after=True)
        else:
            SearchHelper.search_in_google(query)
            self.speak(f"আমি গুগলে {query} সার্চ করছি।", start_listening_after=True)
