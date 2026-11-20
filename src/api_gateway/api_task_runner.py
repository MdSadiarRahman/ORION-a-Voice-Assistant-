"""
VoiceMate Laptop Agent - API Task Runner.
Dispatches API server management commands (start, stop, status, docs) in daemon threads,
delivering live progress updates and spoken announcements in Bengali.
"""
import logging
import threading
from typing import Callable, Optional
from .server_controller import APIServerController
from .api_fallback import APIFallbackHandler

logger = logging.getLogger("VoiceMate.APIGateway.TaskRunner")

class APITaskRunner:
    """Dispatches FastAPI Gateway lifecycle and browser actions asynchronously."""

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ):
        """
        Executes an API task query in a dedicated background daemon thread.
        """
        def _worker():
            query_lower = task_query.lower().strip()
            logger.info(f"APITaskRunner executing: '{task_query}'")

            if on_progress:
                on_progress("এপিআই গেটওয়ে প্রসেস করা হচ্ছে...")

            # ১. সার্ভার বন্ধ করার কমান্ড
            if any(w in query_lower for w in ["বন্ধ", "স্টপ", "stop"]):
                res = APIServerController.stop_server()
                finish_msg = res.get("message", "এপিআই সার্ভার বন্ধ করা হয়েছে।")

            # ২. স্ট্যাটাস বা হেলথ চেক
            elif any(w in query_lower for w in ["স্ট্যাটাস", "অবস্থা", "status", "health"]):
                status = APIServerController.get_status()
                if status["running"]:
                    finish_msg = f"এপিআই সার্ভার সক্রিয় রয়েছে। পোর্ট: {status['port']}। লিঙ্ক: {status['docs_url']}"
                else:
                    finish_msg = "এপিআই সার্ভার বর্তমানে বন্ধ রয়েছে।"

            # ৩. শুধুমাত্র ডক খোলার নির্দেশ
            elif any(w in query_lower for w in ["ডক", "docs", "swagger", "সোয়েগার", "ডকুমেন্টেশন"]):
                if not APIServerController.is_running():
                    APIServerController.start_server(open_docs=True)
                    finish_msg = "এপিআই সার্ভার চালু করে সোয়েগার ডক ওপেন করা হয়েছে।"
                else:
                    APIServerController.open_docs_in_browser()
                    finish_msg = "সোয়েগার এপিআই ডক ব্রাউজারে ওপেন করা হয়েছে।"

            # ৪. ডিফল্ট: সার্ভার চালু করা এবং ডক ওপেন করা
            else:
                res = APIServerController.start_server(open_docs=True)
                finish_msg = res.get("message", "এপিআই গেটওয়ে সার্ভার সক্রিয় হয়েছে।")

            logger.info(f"APITaskRunner finished: {finish_msg}")
            if on_finish:
                on_finish(finish_msg)

        thread = threading.Thread(target=_worker, name="VoiceMate-APITaskRunner", daemon=True)
        thread.start()
