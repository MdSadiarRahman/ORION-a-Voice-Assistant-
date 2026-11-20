"""
VoiceMate Intelligence - Context Manager Module.
Maintains stateful multi-turn conversation memory, active application context,
media playback state, and parameter slot filling across dialog turns.
"""
import time
from typing import Optional, Dict, Any, List


class ContextManager:
    """
    Manages conversational turns, active application/media context,
    and resolves follow-up utterances.
    """
    def __init__(self, history_limit: int = 10, session_ttl_seconds: float = 300.0):
        self.history_limit = history_limit
        self.session_ttl = session_ttl_seconds
        
        self.history: List[Dict[str, str]] = []
        self.active_app: Optional[str] = None
        self.awaiting_slot: Optional[str] = None  # e.g., 'song_name', 'search_query', 'confirmation'
        self.pending_action: Optional[Dict[str, Any]] = None
        self.active_media_title: Optional[str] = None
        self.is_media_playing: bool = False
        self.last_products: List[Any] = []
        self.last_product_search: Optional[str] = None
        self.selected_product: Optional[Any] = None
        self.last_interaction_time: float = time.time()

    def set_product_context(self, query: str, products: List[Any], selected: Optional[Any] = None):
        """Updates conversational product search context with recent items."""
        self.last_product_search = query
        self.last_products = products
        self.selected_product = selected or (products[0] if products else None)
        self.last_interaction_time = time.time()

    def record_turn(self, role: str, content: str):
        """Records a user or assistant utterance into conversational history."""
        self.last_interaction_time = time.time()
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.history_limit:
            self.history = self.history[-self.history_limit:]

    def is_session_expired(self) -> bool:
        """Returns True if the user has been inactive longer than session TTL."""
        return (time.time() - self.last_interaction_time) > self.session_ttl

    def set_active_app(self, app_name: str):
        """Updates currently focused application context."""
        self.active_app = app_name.lower().strip()
        self.last_interaction_time = time.time()

    def set_awaiting_slot(self, slot_name: str, pending_action: Optional[Dict[str, Any]] = None):
        """Sets an awaiting slot to be resolved by the user's next utterance."""
        self.awaiting_slot = slot_name
        self.pending_action = pending_action or {}
        self.last_interaction_time = time.time()

    def clear_awaiting_slot(self):
        """Clears slot waiting state."""
        self.awaiting_slot = None
        self.pending_action = None

    def set_media_state(self, title: str, is_playing: bool = True):
        """Updates currently tracked multimedia session."""
        self.active_media_title = title
        self.is_media_playing = is_playing
        self.active_app = "youtube"
        self.last_interaction_time = time.time()

    def resolve_followup(self, user_utterance: str) -> Optional[Dict[str, Any]]:
        """
        Attempts to resolve an utterance based on the current awaiting slot or active context.
        Handles:
          - Awaiting 'song_name': User replies "Kamariya" -> returns play_music intent
          - Awaiting 'search_query': User replies "Python tutorial" -> returns search_web intent
          - Awaiting 'confirmation': User replies "yes" / "no" -> returns confirmation status
          - Follow-up media controls when media is active
        """
        if self.is_session_expired():
            self.clear_awaiting_slot()
            return None

        clean_text = user_utterance.strip()
        lower_text = clean_text.lower()

        # 1. Awaiting Song Name Slot
        if self.awaiting_slot == "song_name":
            self.clear_awaiting_slot()
            # If user said "Kamariya" or "Play Kamariya"
            from src.intelligence.intent_engine import IntentEngine
            song_title = IntentEngine.extract_song_title(clean_text)
            return {
                "intent": "play_music",
                "action": "play_youtube",
                "parameters": {"song_name": song_title},
                "source": "context_manager"
            }

        # 2. Awaiting Search Query or YouTube follow-up Slot (e.g. "What would you like to watch or listen to?")
        if self.awaiting_slot in ["search_query", "youtube_query"]:
            slot = self.awaiting_slot
            self.clear_awaiting_slot()
            # If user explicitly asked to search
            is_explicit_search = any(w in lower_text for w in ["search", "সার্চ", "খুঁজো", "search for"])
            if is_explicit_search:
                clean_s = clean_text
                for w in ["search for", "search in youtube", "search", "সার্চ করো", "সার্চ"]:
                    clean_s = clean_s.replace(w, "").strip()
                return {
                    "intent": "search_youtube" if slot == "youtube_query" else "search_web",
                    "action": "search_youtube" if slot == "youtube_query" else "search_google",
                    "parameters": {"search_query": clean_s or clean_text, "query": clean_s or clean_text},
                    "source": "context_manager"
                }
            else:
                # Default for YouTube follow-up is playing the requested song/video
                from src.intelligence.intent_engine import IntentEngine
                song_title = IntentEngine.extract_song_title(clean_text)
                return {
                    "intent": "play_music",
                    "action": "play_youtube",
                    "parameters": {"song_name": song_title},
                    "source": "context_manager"
                }

        # 3. Awaiting Confirmation for Destructive Action
        if self.awaiting_slot == "confirmation":
            pending = self.pending_action
            self.clear_awaiting_slot()
            is_yes = lower_text in ["yes", "হাঁ", "হ্যাঁ", "confirm", "proceed", "sure", "koro", "করো", "ঠিক আছে", "ok", "okay"]
            is_no = lower_text in ["no", "না", "cancel", "stop", "abort", "করো না", "দরকার নেই", "na", "cancel koro"]

            if is_yes:
                return {
                    "intent": "confirm_action",
                    "action": "execute_pending",
                    "parameters": pending or {},
                    "source": "context_manager"
                }
            elif is_no:
                return {
                    "intent": "cancel_action",
                    "action": "abort_pending",
                    "parameters": pending or {},
                    "source": "context_manager"
                }

        # 4. Product Follow-Up Resolution (Cheapest, Specs, Open Page, Compare)
        if self.last_products:
            # 4a. Cheapest query follow-up
            cheapest_patterns = [
                "which one is cheapest", "which is cheapest", "cheapest one", "cheapest",
                "সবচেয়ে কম দামি কোনটা", "সবচেয়ে কম দামের কোনটা", "কম দামি কোনটা", "কমদামি কোনটা",
                "সবচেয়ে কম কোনটা", "cheapest konta", "kom dami konta"
            ]
            if any(p in lower_text for p in cheapest_patterns):
                return {
                    "intent": "cheapest_product",
                    "action": "find_cheapest",
                    "parameters": {"products": self.last_products},
                    "source": "context_manager"
                }

            # 4b. Specifications / Features follow-up
            spec_patterns = [
                "tell me its specifications", "specifications", "specification", "specs", "features",
                "এর স্পেসিফিকেশন কি", "স্পেসিফিকেশন বলো", "ফিচার বলো", "ফিচার কি", "ফিচারগুলো কি",
                "features bolo", "specs bolo", "দাম এবং features বলো", "দাম এবং ফিচার বলো"
            ]
            if any(p in lower_text for p in spec_patterns):
                return {
                    "intent": "product_specs",
                    "action": "show_specs",
                    "parameters": {"product": self.selected_product or self.last_products[0]},
                    "source": "context_manager"
                }

            # 4c. Open product page follow-up
            open_patterns = [
                "open that product", "open that", "open product", "open this product",
                "open page", "open link", "পণ্যটি ওপেন করো", "প্রোডাক্ট ওপেন করো",
                "পেজ ওপেন করো", "লিংক ওপেন করো", "ওপেন করো", "open koro"
            ]
            if any(lower_text == p or lower_text.startswith(p) for p in open_patterns):
                return {
                    "intent": "open_product_page",
                    "action": "open_page",
                    "parameters": {"product": self.selected_product or self.last_products[0]},
                    "source": "context_manager"
                }

            # 4d. Compare follow-up
            compare_patterns = [
                "compare these", "compare them", "compare these two", "compare prices",
                "দামের তুলনা করো", "তুলনা করো", "কম্পেয়ার করো", "compare koro"
            ]
            if any(p in lower_text for p in compare_patterns):
                return {
                    "intent": "compare_products",
                    "action": "compare_last_products",
                    "parameters": {"products": self.last_products, "query": self.last_product_search or ""},
                    "source": "context_manager"
                }

        return None
