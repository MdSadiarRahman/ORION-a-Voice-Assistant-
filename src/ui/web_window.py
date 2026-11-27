"""
ORION AI — pywebview Bridge Window
Replaces Tkinter UI with HTML5/CSS3/JS rendered natively via pywebview.

VoiceMateBridge exposes Python methods to JavaScript via js_api.
Python pushes real-time updates to the web UI via window.evaluate_js().

STRICT: Do NOT modify src/intelligence/, src/helpers/, or agent_service.py.
"""

import os
import sys
import json
import threading
import time
from pathlib import Path

try:
    import webview
except ImportError:
    raise ImportError(
        "pywebview না পাওয়া গেছে। ইন্সটল করুন:\n"
        "  pip install pywebview"
    )

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent   # project root
WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = WEB_DIR / "index.html"

# ── Lazy import of backend (keeps CLI untouched) ─────────────────────────────
def _import_agent():
    sys.path.insert(0, str(ROOT))
    from src.agent_service import AgentService
    return AgentService

def _import_battery():
    try:
        sys.path.insert(0, str(ROOT))
        from src.helpers.battery_helper import BatteryHelper
        return BatteryHelper
    except ImportError:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  VoiceMateBridge — exposed to JavaScript as window.pywebview.api
# ══════════════════════════════════════════════════════════════════════════════
class VoiceMateBridge:
    """
    All public methods (no leading underscore) are callable from JS:
        await window.pywebview.api.method_name(args)
    Every method must return a JSON-serialisable dict.
    """

    def __init__(self, agent, window_ref=None):
        self._agent = agent
        self._window = window_ref          # set after webview.create_window()
        self._battery_helper = _import_battery()

    # ── Internal: set window ref after creation ───────────────────────────────
    def _set_window(self, window):
        self._window = window

    # ── Internal: push JS call safely ────────────────────────────────────────
    def _js(self, js_code: str):
        """Execute JS in the web view (non-blocking)."""
        try:
            if self._window:
                self._window.evaluate_js(js_code)
        except Exception as e:
            print(f"[Bridge] evaluate_js error: {e}", flush=True)

    # ─────────────────────────────────────────────────────────────────────────
    #  PUBLIC API (called from JavaScript)
    # ─────────────────────────────────────────────────────────────────────────

    def send_command(self, text: str) -> dict:
        """Process a text command through the agent."""
        if not text or not text.strip():
            return {"status": "error", "message": "Empty command"}
        threading.Thread(
            target=self._agent.process_results,
            args=(text.strip(),),
            daemon=True
        ).start()
        return {"status": "ok"}

    def toggle_service(self) -> dict:
        """Start or stop the AgentService."""
        try:
            if self._agent.is_running:
                self._agent.stop()
                return {"status": "ok", "is_running": False}
            else:
                self._agent.start()
                return {"status": "ok", "is_running": True}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def toggle_voice(self) -> dict:
        """Toggle voice listening mode."""
        try:
            # AgentService's voice mode — if supported
            if hasattr(self._agent, 'toggle_voice'):
                self._agent.toggle_voice()
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def trigger_quick_action(self, action_text: str) -> dict:
        """Execute a quick-action chip prompt with full query mapping."""
        mapping = {
            "Solve Assignment": "Assignment 01.pdf solve kore docx e save koro",
            "Compare Prices": "HP laptop er dam koto compare koro",
            "Build Website": "হাসপাতাল ম্যানেজমেন্ট ওয়েবসাইট বানিয়ে সার্ভার রান করো",
            "Play Music": "ইউটিউবে একটি গান প্লে করো",
            "Battery Status": "আমার ল্যাপটপের চার্জ কতটুকু আছে",
            "কম্পিউটারের ব্যাটারি স্ট্যাটাস দেখাও": "আমার ল্যাপটপের চার্জ কতটুকু আছে",
        }
        cmd = mapping.get(action_text.strip(), action_text.strip())
        return self.send_command(cmd)

    def run_toolkit_action(self, agent_name: str, param: str = "") -> dict:
        """
        Trigger a named toolkit sub-agent action.
        Maps natural language instructions directly to the agent processor.
        """
        param = (param or "").strip()
        cmd = ""
        if agent_name == "product_research":
            cmd = f"খুঁজে দাও {param} দাম কত" if param else "দারাজে সেরা ল্যাপটপ খোঁজো"
        elif agent_name == "assignment_solver":
            cmd = f"{param} solve kore docx e save koro" if param else "Assignment solve kore docx e save koro"
        elif agent_name == "website_builder":
            cmd = f"{param} ওয়েবসাইট বানিয়ে সার্ভার চালু করো" if param else "Portfolio ওয়েবসাইট বানিয়ে সার্ভার চালু করো"
        elif agent_name == "browser_agent":
            cmd = f"ব্রাউজারে গিয়ে {param}" if param else "ব্রাউজারে গিয়ে গিটহাবে ভয়েসমেট সার্চ করো"
        elif agent_name == "doc_reader":
            cmd = f"ডকুমেন্ট পড়ো {param}" if param else "ডকুমেন্ট পড়ো"
        elif agent_name == "docling_converter":
            cmd = f"ডকলিং ডকুমেন্ট কনভার্ট {param}" if param else "ডকলিং ডকুমেন্ট কনভার্ট"
        elif agent_name == "web_automation":
            cmd = param if param else "ওয়েব অটোমেশন চালু করো"
        elif agent_name == "developer_canvas":
            cmd = param if param else "ক্যানভাস চালু করো"
        elif agent_name == "ai_coder":
            cmd = param if param else "রেপো ম্যাপ তৈরি করো"
        elif agent_name == "n8n_workflow":
            cmd = param if param else "এনএইটেন খোলো"
        elif agent_name == "api_gateway":
            cmd = param if param else "এপিআই ওপেন করো"
        elif agent_name == "langgraph_brain":
            cmd = param if param else "ব্রেন স্ট্যাটাস"
        else:
            cmd = f"{agent_name}: {param}" if param else agent_name

        return self.send_command(cmd)

    def get_telemetry(self) -> dict:
        """Return current system telemetry for the HUD."""
        battery_pct = None
        charging = False

        if self._battery_helper:
            try:
                info = self._battery_helper.get_battery_info()
                battery_pct = info.get("percent")
                charging = info.get("charging", False)
            except Exception:
                pass

        # Detect the active language-model engine for the HUD.
        engine = "🧠 Autonomous NLU"
        if os.getenv("GEMINI_API_KEY"):
            engine = "⚡ Gemini 3.8 Flash"
        else:
            try:
                if hasattr(self._agent, 'decision_engine') and \
                   hasattr(self._agent.decision_engine, 'ollama') and \
                   self._agent.decision_engine.ollama.is_available():
                    engine = "🦙 Ollama Local"
            except Exception:
                pass

        return {
            "battery":    battery_pct,
            "charging":   charging,
            "engine":     engine,
            "is_running": bool(self._agent.is_running),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  Agent state → JavaScript push
# ══════════════════════════════════════════════════════════════════════════════
def _build_state_callback(bridge_ref: list, window_ref: list):
    """
    Returns a callback that maps AgentService state dict → JS call.
    Uses list references so the closure captures the mutable container.
    """
    def on_state_change(state: dict):
        bridge = bridge_ref[0]
        window = window_ref[0]
        if not window:
            return

        # Map internal keys → clean state dict for JS
        is_running   = state.get("is_running", True)
        is_listening = state.get("is_listening", False)
        is_speaking  = state.get("is_speaking",  False)
        is_typing    = state.get("is_typing_mode", False)
        message      = state.get("message", "")

        if not is_running:
            js_state = "offline"
        elif is_speaking:
            js_state = "speaking"
        elif is_listening:
            js_state = "listening"
        elif message:
            js_state = "thinking"
        else:
            js_state = "idle"

        payload = json.dumps({
            "state":      js_state,
            "message":    message,
            "is_running": is_running,
        })

        bridge._js(f"window.onAgentStateChange && window.onAgentStateChange({payload})")

        # Also push log
        if message:
            tag = "AGENT" if js_state in ["thinking", "speaking"] else ("SUCCESS" if js_state in ["idle", "listening"] else "INFO")
            bridge._js(f"window.appendLog && window.appendLog({json.dumps(tag)}, {json.dumps(message)})")

    return on_state_change


# ══════════════════════════════════════════════════════════════════════════════
#  Battery polling → JS push (every 30 s)
# ══════════════════════════════════════════════════════════════════════════════
def _start_battery_poll(bridge: VoiceMateBridge):
    def poll():
        while True:
            time.sleep(30)
            try:
                telem = bridge.get_telemetry()
                payload = json.dumps(telem)
                bridge._js(f"window.updateTelemetry && window.updateTelemetry({payload})")
            except Exception:
                pass
    t = threading.Thread(target=poll, daemon=True)
    t.start()


# ══════════════════════════════════════════════════════════════════════════════
#  Main entry point
# ══════════════════════════════════════════════════════════════════════════════
def launch_web_window():
    """Create the pywebview window and start the event loop."""
    print("🚀 ORION AI pywebview Desktop GUI চালু হচ্ছে...", flush=True)

    AgentService = _import_agent()

    # Mutable containers so the closure can capture before assignment
    bridge_ref = [None]
    window_ref = [None]

    state_callback = _build_state_callback(bridge_ref, window_ref)

    agent = AgentService(on_state_change=state_callback)
    agent.start()  # Start voice listener & background service on launch

    bridge = VoiceMateBridge(agent, None)
    bridge_ref[0] = bridge

    window = webview.create_window(
        title="VoiceMate AI \u2014 Neural Command Center",   # kept per spec
        url=str(INDEX_HTML),
        js_api=bridge,
        background_color="#07080F",
        min_size=(1100, 720),
        width=1280,
        height=800,
        resizable=True,
        text_select=False,
    )

    window_ref[0] = window
    bridge._set_window(window)
    window.events.closing += lambda: agent.stop()

    # Start battery polling thread
    _start_battery_poll(bridge)

    # Push initial telemetry after the DOM is ready
    def on_loaded():
        time.sleep(0.3)
        try:
            telem = bridge.get_telemetry()
            payload = json.dumps(telem)
            bridge._js(f"window.updateTelemetry && window.updateTelemetry({payload})")
            bridge._js("window.appendLog && window.appendLog('SUCCESS', 'VoiceMate AI Neural Core সংযুক্ত')")
            init_state = json.dumps({"state": "idle", "message": "অ্যাসিস্ট্যান্ট প্রস্তুত", "is_running": True})
            bridge._js(f"window.onAgentStateChange && window.onAgentStateChange({init_state})")
        except Exception as e:
            print(f"[Bridge] on_loaded error: {e}", flush=True)
        except Exception as e:
            print(f"[Bridge] on_loaded error: {e}", flush=True)

    window.events.loaded += lambda: threading.Thread(target=on_loaded, daemon=True).start()

    print(f"[Bridge] Loading: {INDEX_HTML}", flush=True)
    webview.start(debug=False)
