"""
VoiceMate Intelligence - Google Gemini Cloud LLM Integration Client.
Uses the fast, non-blocking Gemini REST API (with automatic model fallback across
verified available models) and injects live date/weekday context.
Zero dependency on deprecated gRPC transports that can hang on Windows.
"""
import os
import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path, override=False)
else:
    load_dotenv()


class GeminiClient:
    """
    Communicates with Google Gemini REST API for fast cloud reasoning,
    structured intent extraction, and academic/document generation.
    """
    DEFAULT_MODELS = [
        "gemini-3.1-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
    ]
    REST_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

    SYSTEM_PROMPT = """You are VoiceMate (ORION) AI Brain, an intelligent autonomous voice assistant for Windows laptops.
Your task is to analyze user queries in English, Bengali, or Banglish and output a single JSON object.

Supported intents:
- "play_music": User wants to play/listen to a song or video. parameter: "song_name" (clean song title only)
- "media_control": Playback controls. parameter: "action" ("pause", "resume", "stop", "next", "previous")
- "volume_control": Volume adjustment. parameter: "direction" ("up", "down", "mute")
- "open_application": Launch app or website. parameter: "app_name" ("youtube", "chrome", "notepad", "calculator", "whatsapp", etc.)
- "close_application": Close active app/window.
- "system_info": Battery, date, or time query. parameter: "info_type" ("battery", "time", "date")
- "search_web": Explicitly asks to open Google search in browser. parameter: "query"
- "conversation": General conversation, greetings, factual questions, coding/study explanations, math, or advice. Put a concise, helpful Bengali (or matching language) answer in BOTH top-level "reply" AND parameters.reply.
- "unknown": Ambiguous query.

Output format:
Respond ONLY with a valid JSON object. No explanation, no markdown ticks.
Example:
{
  "intent": "conversation",
  "action": "reply",
  "parameters": {"reply": "বাংলাদেশের রাজধানী ঢাকা।"},
  "reply": "বাংলাদেশের রাজধানী ঢাকা।"
}
"""

    _shared_working_model: Optional[str] = None
    _shared_dead_models: set[str] = set()

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None, timeout_seconds: float = 12.0):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or self.DEFAULT_MODELS[0]
        self.timeout = timeout_seconds
        self._working_model: Optional[str] = GeminiClient._shared_working_model
        self._dead_models: set[str] = set(GeminiClient._shared_dead_models)

    def refresh_key(self, new_key: Optional[str] = None):
        """Refreshes the API key from parameter or environment."""
        if _env_path.exists():
            load_dotenv(dotenv_path=_env_path, override=True)
        self.api_key = new_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._working_model = None
        self._dead_models.clear()
        GeminiClient._shared_working_model = None
        GeminiClient._shared_dead_models.clear()

    def is_available(self) -> bool:
        """Returns True if a Gemini API key is configured."""
        if not self.api_key:
            self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        return bool(self.api_key and self.api_key.strip())

    def get_active_model_display(self) -> str:
        return self._working_model or self.model_name

    @classmethod
    def _build_system_prompt(cls, base_prompt: Optional[str] = None) -> str:
        now = datetime.now()
        dt_ctx = now.strftime("Current local date and time: %A, %d %B %Y, %I:%M %p.")
        base = base_prompt or cls.SYSTEM_PROMPT
        return f"{base}\n\nRuntime Context: {dt_ctx}"

    def _call_rest(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.2,
    ) -> Optional[str]:
        """Calls Gemini generateContent REST endpoint cleanly with explicit timeout."""
        if not self.is_available():
            return None

        url = f"{self.REST_BASE}/{model}:generateContent?key={self.api_key}"
        gen_cfg: Dict[str, Any] = {"temperature": temperature}
        if json_mode:
            gen_cfg["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": gen_cfg,
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "VoiceMate/2.0"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                return None
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()
            return text or None

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.3,
    ) -> Optional[str]:
        """
        Generates text using configured Gemini models with automatic fallback
        if a model returns 404/503 or times out.
        """
        if not self.is_available():
            return None

        candidates = []
        if self._working_model:
            candidates.append(self._working_model)
        if self.model_name not in candidates:
            candidates.append(self.model_name)
        for m in self.DEFAULT_MODELS:
            if m not in candidates:
                candidates.append(m)

        sys_text = self._build_system_prompt(system_prompt) if system_prompt else None

        for model in candidates:
            if model in self._dead_models:
                continue
            try:
                text = self._call_rest(
                    model=model,
                    prompt=prompt,
                    system_prompt=sys_text,
                    json_mode=json_mode,
                    temperature=temperature,
                )
                if text:
                    self._working_model = model
                    GeminiClient._shared_working_model = model
                    return text
            except urllib.error.HTTPError as he:
                if he.code in (400, 404):
                    self._dead_models.add(model)
                    GeminiClient._shared_dead_models.add(model)
                elif he.code in (401, 403):
                    # Invalid API key — stop trying further models
                    return None
                try:
                    he.close()
                except Exception:
                    pass
            except Exception:
                continue
        return None

    def analyze_query(
        self,
        user_text: str,
        context_history: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Sends user text to Gemini REST API and parses the structured JSON intent output.
        """
        if not self.is_available():
            return None

        prompt = f"User: {user_text}\nJSON Output:"
        if context_history:
            recent = context_history[-4:]
            hist_str = "\n".join(
                f"{h.get('role', 'user')}: {h.get('content', '')}" for h in recent
            )
            prompt = f"Recent Dialog History:\n{hist_str}\n\nCurrent User Query: {user_text}\nJSON Output:"

        raw = self.generate_text(
            prompt=prompt,
            system_prompt=self.SYSTEM_PROMPT,
            json_mode=True,
            temperature=0.2,
        )
        if not raw:
            return None

        clean_text = re.sub(r"^```json\s*", "", raw.strip(), flags=re.IGNORECASE)
        clean_text = re.sub(r"^```\s*", "", clean_text)
        clean_text = re.sub(r"```$", "", clean_text).strip()

        try:
            data = json.loads(clean_text)
            if isinstance(data, dict):
                return data
        except Exception:
            # Extract first JSON object substring if prose slipped in
            match = re.search(r"\{.*\}", clean_text, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(0))
                    if isinstance(data, dict):
                        return data
                except Exception:
                    pass
        return None
