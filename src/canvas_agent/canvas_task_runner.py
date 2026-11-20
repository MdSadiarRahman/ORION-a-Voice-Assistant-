"""
Background Task Runner for OpenHands Developer Canvas Operations.
Dispatches developer commands, terminal runs, code audits, and canvas server
in daemon threads with real-time progress callbacks.
"""
import re
import threading
from typing import Callable, Optional, Dict, Any

from src.canvas_agent.canvas_controller import CanvasController
from src.canvas_agent.canvas_event_stream import CanvasEventStream, EventKind


class CanvasTaskRunner:
    """
    Manages non-blocking execution of OpenHands Developer Canvas commands.
    """

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """Runs developer canvas task in a background daemon thread."""
        def _worker():
            try:
                if on_progress:
                    on_progress("💻 ওপেনহ্যান্ডস ক্যানভাস শুরু হচ্ছে...")

                result = cls._parse_and_execute(task_query, on_progress)
                msg = result.get("message", "টাস্ক সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(msg)
            except Exception as e:
                err_msg = f"ক্যানভাস টাস্কে ত্রুটি: {str(e)}"
                if on_finish:
                    on_finish(err_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    @classmethod
    def _parse_and_execute(
        cls,
        query: str,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Interprets developer queries into specific OpenHands actions."""
        q = query.lower().strip()
        stream = CanvasEventStream.get_instance()

        # 1. Launch OpenHands Canvas Server
        launch_kws = ["ক্যানভাস খোলো", "ক্যানভাস চালু", "ওপেনহ্যান্ডস চালু", "open canvas", "start canvas", "canvas"]
        if any(kw in q for kw in launch_kws):
            if on_progress:
                on_progress("🌐 ওপেনহ্যান্ডস ক্যানভাস সার্ভার চালু করা হচ্ছে...")
            return CanvasController.start_canvas_server()

        # 2. Codebase Audit / Review
        audit_kws = ["কোড অডিট", "কোড রিভিউ", "code audit", "code review", "সিনট্যাক্স চেক", "কোড এনালাইসিস"]
        if any(kw in q for kw in audit_kws):
            if on_progress:
                on_progress("🔍 কোডবেস স্ক্যান ও সিনট্যাক্স অডিট করা হচ্ছে...")
            return CanvasController.audit_code()

        # 3. Git Status & Repository Inspection
        git_kws = ["গিট স্ট্যাটাস", "git status", "গিট পরিবর্তন", "git diff", "গিট হিস্ট্রি"]
        if any(kw in q for kw in git_kws):
            if on_progress:
                on_progress("🌿 গিট রেপোজিটরি স্ট্যাটাস পরীক্ষা করা হচ্ছে...")
            return CanvasController.get_git_status()

        # 4. Project File Tree
        tree_kws = ["ফাইল ট্রি", "প্রোজেক্ট ফাইল", "file tree", "ফাইল লিস্ট", "ডিরেক্টরি স্ট্রাকচার"]
        if any(kw in q for kw in tree_kws):
            if on_progress:
                on_progress("📂 প্রোজেক্টের ফাইল স্ট্রাকচার তৈরি করা হচ্ছে...")
            return CanvasController.get_file_tree()

        # 5. Terminal Command Execution
        term_kws = ["টার্মিনালে চালাও", "টার্মিনাল", "কমান্ড চালাও", "রান কমান্ড", "terminal", "run command", "cmd"]
        if any(kw in q for kw in term_kws):
            clean_cmd = query
            for kw in term_kws:
                clean_cmd = re.sub(rf"(^|[^\w\u0980-\u09FF]){re.escape(kw)}($|[^\w\u0980-\u09FF])", " ", clean_cmd, flags=re.IGNORECASE)
            clean_cmd = re.sub(r"\s+", " ", clean_cmd).strip()
            if not clean_cmd:
                clean_cmd = "dir"

            if on_progress:
                on_progress(f"⚡ টার্মিনাল কমান্ড চালানো হচ্ছে: '{clean_cmd}'...")
            return CanvasController.run_terminal_command(clean_cmd)

        # Default fallback: run code audit
        if on_progress:
            on_progress("🔍 প্রোজেক্টের সার্বিক কোড কোয়ালিটি অডিট করা হচ্ছে...")
        return CanvasController.audit_code()
