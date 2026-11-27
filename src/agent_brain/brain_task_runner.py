"""
VoiceMate Laptop Agent - LangGraph Brain Task Runner.
Dispatches graph orchestrations in daemon threads, delivering live progress
callbacks and spoken Bengali feedback.
"""
import logging
import threading
from typing import Callable, Optional
from .brain_controller import LangGraphBrainController

logger = logging.getLogger("VoiceMate.AgentBrain.TaskRunner")

class BrainTaskRunner:
    """Dispatches LangGraph orchestration turns asynchronously."""

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ):
        """
        Executes a LangGraph orchestration query in a background daemon thread.
        """
        def _worker():
            query_clean = task_query.strip()
            query_lower = query_clean.lower()
            logger.info(f"BrainTaskRunner executing: '{query_clean}'")

            if on_progress:
                on_progress("ল্যাংগ্রাফ মাল্টি-এজেন্ট ব্রেন প্রসেস করছে...")

            # ১. ব্রেন স্ট্যাটাস কমান্ড
            if any(w in query_lower for w in ["স্ট্যাটাস", "অবস্থা", "status"]):
                status = LangGraphBrainController.get_status()
                node_list = ", ".join(status["nodes"])
                finish_msg = f"ল্যাংগ্রাফ ব্রেন সক্রিয় রয়েছে। মোট নোড: {len(status['nodes'])}, সেশন: {status['current_thread_id']}"

            # ২. কনভার্সেশনাল হিস্ট্রি ও মেমোরি চেক
            elif any(w in query_lower for w in ["হিস্ট্রি", "history", "মেমোরি", "স্মৃতি"]):
                history = LangGraphBrainController.get_history()
                finish_msg = f"ব্রেন মেমোরিতে বর্তমানে {len(history)}টি পূর্ববর্তী বার্তা সংরক্ষিত আছে।"

            # ৩. সাধারণ বা জটিল মাল্টি-এজেন্ট টাস্ক এক্সিকিউশন
            else:
                result = LangGraphBrainController.execute_turn(query_clean)
                reply = result.get("final_reply", "কাজটি সম্পন্ন হয়েছে।")
                worker = result.get("next_worker", "worker")
                finish_msg = f"[{worker}] {reply}"

            logger.info(f"BrainTaskRunner finished: {finish_msg}")
            if on_finish:
                on_finish(finish_msg)

        thread = threading.Thread(target=_worker, name="VoiceMate-BrainTaskRunner", daemon=True)
        thread.start()
