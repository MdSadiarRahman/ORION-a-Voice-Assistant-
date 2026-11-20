"""
VoiceMate Intelligence - Google Gemini Cloud LLM Integration Client.
Provides instant, ultra-fast cloud AI decision-making, semantic parameter extraction,
conversational reasoning, and QA via Google AI Studio API (Gemini 2.0 / 1.5 Flash).
Consumes 0% local laptop CPU/RAM, sub-second latency.
"""
import os
import json
import re
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()


class GeminiClient:
    """
    Communicates with Google Gemini API for high-speed cloud reasoning and natural language intent extraction.
    """
    _instance: Optional['GeminiClient'] = None
    DEFAULT_MODELS = ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]

    SYSTEM_PROMPT = """You are VoiceMate AI Brain, an intelligent autonomous voice assistant for Windows laptops.
Your task is to analyze user queries in English, Bengali, or Banglish and output a single JSON object.

Supported intents:
- "play_music": User wants to play/listen to a song or video. parameter: "song_name" (clean song title only)
- "media_control": Playback controls. parameter: "action" ("pause", "resume", "stop", "next", "previous")
- "volume_control": Volume adjustment. parameter: "direction" ("up", "down", "mute")
- "open_application": Launch app or website. parameter: "app_name" ("youtube", "chrome", "notepad", "calculator", "whatsapp", etc.)
- "close_application": Close active app/window.
- "product_search": Search or compare products/prices. parameter: "query", optional "budget"
- "system_info": Battery, date, or time query. parameter: "info_type" ("battery", "time", "date")
- "search_web": Information search on Google. parameter: "query"
- "conversation": General conversation, greetings, factual questions, or math calculation. parameter: "reply" (concise, polite Bengali response)
- "unknown": Ambiguous query.

Output format:
Respond ONLY with a valid JSON object. No explanation, no markdown ticks.
Example:
{
  "intent": "play_music",
  "action": "play_youtube",
  "parameters": {"song_name": "Kamariya"},
  "reply": "ইউটিউবে কামারিয়া গান প্লে করা হচ্ছে।"
}
"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.8-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self._model = None
        self._init_client()

    def _init_client(self):
        """Initializes google-generativeai client if API key is present."""
        if not self.api_key:
            return
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json", "temperature": 0.2}
            )
        except Exception:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel(model_name="gemini-flash-latest")
            except Exception:
                self._model = None

    def is_available(self) -> bool:
        """Returns True if Gemini API is configured with a valid key."""
        if not self.api_key:
            # Check if environment was updated recently
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if self.api_key and not self._model:
                self._init_client()
        return bool(self.api_key and self._model is not None)

    def analyze_query(self, user_text: str, context_history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """
        Sends user text to Gemini and parses the structured JSON intent output.
        """
        if not self.is_available():
            return None

        prompt = f"User: {user_text}\nJSON Output:"
        if context_history:
            recent = context_history[-3:]
            hist_str = "\n".join([f"{h.get('role', 'user')}: {h.get('content', '')}" for h in recent])
            prompt = f"Recent Dialog History:\n{hist_str}\n\nCurrent User Query: {user_text}\nJSON Output:"

        try:
            response = self._model.generate_content(prompt)
            if not response or not response.text:
                return None

            clean_text = response.text.strip()
            # Strip markdown fences if present
            clean_text = re.sub(r"^```json\s*", "", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"^```\s*", "", clean_text)
            clean_text = re.sub(r"```$", "", clean_text).strip()

            data = json.loads(clean_text)
            return data
        except Exception as e:
            # Try fallback model if 2.0-flash failed
            try:
                import google.generativeai as genai
                fallback_model = genai.GenerativeModel("gemini-1.5-flash")
                res = fallback_model.generate_content(f"{self.SYSTEM_PROMPT}\n\nUser: {user_text}\nJSON:")
                if res and res.text:
                    clean_text = res.text.strip()
                    clean_text = re.sub(r"^```json\s*", "", clean_text, flags=re.IGNORECASE)
                    clean_text = re.sub(r"^```\s*", "", clean_text)
                    clean_text = re.sub(r"```$", "", clean_text).strip()
                    return json.loads(clean_text)
            except Exception:
                pass
            return None
