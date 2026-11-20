"""
VoiceMate Intelligence - Ollama Qwen Local LLM Integration Client.
Provides lightweight, local AI decision-making, semantic parameter extraction,
and conversational reasoning via Ollama Qwen3:4b (with adaptive model fallback).
Optimized for 8GB RAM systems with low context budgeting and fast timeouts.
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List


class OllamaClient:
    """
    Communicates with locally hosted Ollama instance for complex reasoning,
    intent classification, and entity extraction.
    """
    DEFAULT_HOST = "http://localhost:11434"
    PREFERRED_MODELS = ["qwen3:4b", "qwen2.5:3b", "qwen2.5:1.5b", "qwen2:1.5b", "qwen2.5:7b", "llama3.2:3b", "mistral"]

    _cached_available: Optional[bool] = None
    _last_check_time: float = 0.0
    _active_model: Optional[str] = None

    SYSTEM_PROMPT = """You are VoiceMate AI Brain, a smart Windows laptop assistant.
Your task is to analyze user queries in English, Bangla, or Banglish and output a single JSON object.

Allowed intents:
- "play_music": User wants to play/listen to a song/video. parameter: "song_name" (clean song title only)
- "media_control": User wants to control playback. parameter: "action" ("pause", "resume", "stop", "next", "previous")
- "volume_control": User wants volume adjustment. parameter: "direction" ("up", "down", "mute")
- "open_application": User wants to open an app/website. parameter: "app_name" ("youtube", "chrome", "notepad", "calculator", "whatsapp", etc.)
- "close_application": User wants to close active window/app.
- "search_web": General search query. parameter: "query"
- "system_info": User asks for time, date, or battery. parameter: "info_type" ("time", "date", "battery")
- "conversation": General chit-chat or question. parameter: "reply"
- "unknown": Unclear request.

Respond ONLY with valid JSON. No markdown, no prose.
Schema:
{
  "intent": "play_music",
  "action": "play_youtube",
  "parameters": {"song_name": "Kamariya"},
  "reply": "Kamariya is now playing.",
  "needs_confirmation": false
}"""

    def __init__(self, host: str = DEFAULT_HOST, model: str = "qwen3:4b", timeout_seconds: float = 4.0):
        self.host = host.rstrip("/")
        self.preferred_model = model
        self.timeout = timeout_seconds

    def is_available(self) -> bool:
        """
        Fast health-check with 15-second TTL cache to prevent stalling voice loops when Ollama is offline.
        """
        now = time.time()
        if self._cached_available is not None and (now - self._last_check_time < 15.0):
            return self._cached_available

        try:
            req = urllib.request.Request(f"{self.host}/api/tags", headers={"User-Agent": "VoiceMate/2.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    models = [m.get("name", "") for m in data.get("models", [])]
                    self._resolve_model(models)
                    self._cached_available = True
                    self._last_check_time = now
                    return True
        except Exception:
            pass

        self._cached_available = False
        self._last_check_time = now
        return False

    def _resolve_model(self, available_models: List[str]):
        """Picks the best available Qwen model from the running Ollama server."""
        for pref in self.PREFERRED_MODELS:
            for avail in available_models:
                if avail.startswith(pref) or pref in avail:
                    self._active_model = avail
                    return
        if available_models:
            self._active_model = available_models[0]
        else:
            self._active_model = self.preferred_model

    def analyze_query(self, user_text: str, context_history: Optional[List[Dict[str, str]]] = None) -> Optional[Dict[str, Any]]:
        """
        Submits natural language query to Ollama and returns structured intent dict.
        Returns None if Ollama is unreachable, times out, or output is non-JSON.
        """
        if not self.is_available():
            return None

        model_name = self._active_model or self.preferred_model

        # Build messages payload
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if context_history:
            for turn in context_history[-4:]:  # Keep recent 4 turns for context
                messages.append(turn)
        messages.append({"role": "user", "content": user_text})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": 2048,
                "num_predict": 128
            }
        }

        try:
            data_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                f"{self.host}/api/chat",
                data=data_bytes,
                headers={"Content-Type": "application/json", "User-Agent": "VoiceMate/2.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 200:
                    raw_resp = json.loads(resp.read().decode('utf-8'))
                    content = raw_resp.get("message", {}).get("content", "").strip()
                    parsed = json.loads(content)
                    return parsed
        except Exception:
            pass

        return None
