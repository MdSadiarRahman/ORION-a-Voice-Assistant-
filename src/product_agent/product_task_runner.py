"""
VoiceMate Product Agent - Background Task Runner.
Executes product research, price scraping, and comparison in background daemon threads
with real-time progress updates and voice notifications.
"""
import threading
from typing import Callable, Optional, Dict, Any

from src.product_agent.product_controller import ProductController


class ProductTaskRunner:
    """
    Manages non-blocking thread execution of product research workflows.
    """

    @classmethod
    def run_task(
        cls,
        query: str,
        budget: Optional[float] = None,
        lang: str = "bn",
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> threading.Thread:
        """
        Runs product research in a non-blocking daemon thread.
        """
        def _worker():
            try:
                if on_progress:
                    on_progress(f"🔍 '{query}' নিয়ে বাজার দর ও স্পেসিফিকেশন খোঁজা হচ্ছে...")

                res = ProductController.search_and_research(query=query, budget=budget, lang=lang)
                summary = res.get("voice_summary", "প্রোডাক্টের তথ্য খোঁজা সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(summary, res)
            except Exception as e:
                err_msg = f"প্রোডাক্ট রিসার্চে সমস্যা হয়েছে: {str(e)}"
                if on_finish:
                    on_finish(err_msg, {"error": str(e), "success": False})

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
