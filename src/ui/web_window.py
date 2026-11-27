"""
ORION AI — pywebview Bridge Window
Replaces Tkinter UI with HTML5/CSS3/JS rendered natively via pywebview.

VoiceMateBridge exposes Python methods to JavaScript via js_api.
Python pushes real-time updates to the web UI via window.evaluate_js().

The bridge exposes only the currently supported VoiceMate capabilities.
"""

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
        """Handle the one no-parameter shortcut; reject removed legacy actions."""
        if action_text.strip() == "Typing Mode":
            return self.send_command("typing mode")
        return {
            "status": "error",
            "message": "এই shortcut আর সমর্থিত নয়। Open App, Typing Mode, Search Web, Document Q&A অথবা Product Price ব্যবহার করুন।",
        }

    def run_toolkit_action(self, agent_name: str, param: str = "") -> dict:
        """
        Trigger only one of the user-approved VoiceMate capabilities.
        """
        param = (param or "").strip()
        if agent_name == "typing_mode":
            return self.send_command("typing mode")
        if not param:
            return {"status": "error", "message": "কাজটির জন্য প্রয়োজনীয় নাম বা প্রশ্ন দিন।"}

        prefixes = {
            "open_app": "open ",
            "web_search": "search ",
            "document_qa": "answer from document: ",
            "product_price": "price of ",
        }
        prefix = prefixes.get(agent_name)
        if prefix is None:
            return {"status": "error", "message": "এই toolkit action সমর্থিত নয়।"}
        return self.send_command(prefix + param)

    def get_telemetry(self) -> dict:
        """Return only the service state used by the interface."""
        return {"is_running": bool(self._agent.is_running)}


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

    def on_closing():
        # Clear window references immediately so agent.stop() never calls evaluate_js on a closing window
        window_ref[0] = None
        bridge._set_window(None)
        threading.Thread(target=agent.stop, daemon=True).start()

    window.events.closing += on_closing

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

    window.events.loaded += lambda: threading.Thread(target=on_loaded, daemon=True).start()

    print(f"[Bridge] Loading: {INDEX_HTML}", flush=True)
    webview.start(debug=False)
    # Ensure agent stops cleanly after window loop exits
    window_ref[0] = None
    bridge._set_window(None)
    agent.stop()
