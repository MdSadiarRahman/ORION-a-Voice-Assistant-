"""Background dispatcher for local developer-canvas actions."""

import threading
import webbrowser
from typing import Any, Callable, Optional

from config import CANVAS_AUTO_OPEN_BROWSER, CANVAS_ENABLED, CANVAS_PORT
from src.canvas_agent.canvas_config import get_canvas_settings
from src.canvas_agent.canvas_event_stream import CanvasEventStream, EventKind
from src.canvas_agent.canvas_workspace_runner import CanvasWorkspaceRunner


class CanvasTaskRunner:
    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None,
    ) -> threading.Thread:
        def worker() -> None:
            stream = CanvasEventStream.get_instance()
            try:
                message = "ডেভেলপার ক্যানভাস টাস্ক শুরু হচ্ছে..."
                stream.emit(EventKind.THINKING, message)
                if on_progress:
                    on_progress(message)
                result = cls._parse_and_execute(task_query)
                message = result.get("message", "ক্যানভাস টাস্ক সম্পন্ন হয়েছে।")
                kind = EventKind.COMPLETED if result.get("success") else EventKind.ERROR
                stream.emit(kind, message)
            except Exception as exc:
                message = f"ক্যানভাস টাস্কে ত্রুটি: {exc}"
                stream.emit(EventKind.ERROR, message)
            if on_finish:
                on_finish(message)

        thread = threading.Thread(target=worker, name="canvas-task", daemon=True)
        thread.start()
        return thread

    @classmethod
    def _parse_and_execute(cls, query: str) -> dict[str, Any]:
        q = query.lower().strip()
        if any(word in q for word in ("অডিট", "audit", "রিভিউ", "review")):
            result = CanvasWorkspaceRunner.audit_codebase()
            count = result["valid_files"]
            errors = len(result["syntax_errors"])
            result["message"] = f"কোড অডিট সম্পন্ন: {count}টি Python ফাইল যাচাই, {errors}টি syntax error."
            return result
        if any(word in q for word in ("ফাইল ট্রি", "file tree", "ফাইল তালিকা")):
            result = CanvasWorkspaceRunner.get_file_tree()
            result["message"] = "ওয়ার্কস্পেসের ফাইল ট্রি তৈরি হয়েছে।\n" + result["tree"]
            return result
        if any(word in q for word in ("গিট স্ট্যাটাস", "git status")):
            result = CanvasWorkspaceRunner.execute_terminal_command("git status")
            result["message"] = result["output"] if result["success"] else f"Git status পাওয়া যায়নি: {result['error']}"
            return result
        if any(word in q for word in ("টার্মিনাল", "terminal")):
            return {
                "success": False,
                "message": "নিরাপত্তার জন্য কেবল নির্দিষ্ট read-only terminal command চালানো যায়।",
            }
        if any(word in q for word in ("ক্যানভাস", "canvas", "ওপেনহ্যান্ডস", "openhands")):
            settings = get_canvas_settings()
            if not CANVAS_ENABLED:
                return {"success": False, "message": "ডেভেলপার ক্যানভাস configuration-এ বন্ধ আছে।"}
            if not settings["is_running"]:
                return {
                    "success": False,
                    "message": f"OpenHands ক্যানভাস চালু নেই (পোর্ট {CANVAS_PORT}); এখানে সফলভাবে চালু হয়েছে বলে দেখানো হচ্ছে না।",
                }
            url = f"http://127.0.0.1:{CANVAS_PORT}"
            opened = webbrowser.open(url) if CANVAS_AUTO_OPEN_BROWSER else True
            return {
                "success": bool(opened),
                "message": f"OpenHands ক্যানভাস খোলা হয়েছে: {url}" if opened else "ক্যানভাস URL ব্রাউজারে খোলা যায়নি।",
                "url": url,
            }
        return {
            "success": False,
            "message": "ক্যানভাসে audit, git status, file tree, অথবা চালু OpenHands পোর্টের অনুরোধ দিন।",
        }
