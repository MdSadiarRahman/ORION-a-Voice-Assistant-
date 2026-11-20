"""
Background Task Runner for n8n Workflow Automation.
Runs webhook triggers and multi-app automations in worker threads
with progress callbacks and spoken summaries.
"""
import threading
from typing import Callable, Optional, Dict, Any

from src.n8n_agent.n8n_controller import N8nController


class N8nTaskRunner:
    """
    Manages non-blocking execution of n8n automation workflows.
    """

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """Runs n8n automation task in a background daemon thread."""
        def _worker():
            try:
                if on_progress:
                    on_progress("🔄 এনএইটেন ওয়ার্কফ্লো অটোমেশন শুরু হচ্ছে...")

                result = cls._parse_and_execute(task_query, on_progress)
                msg = result.get("message", "অটোমেশন সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(msg)
            except Exception as e:
                err_msg = f"এনএইটেন টাস্কে ত্রুটি: {str(e)}"
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
        """Interprets automation queries into specific n8n actions."""
        q = query.lower().strip()

        # 1. Open n8n visual canvas
        canvas_kws = ["ক্যানভাস খোলো", "এনএইটেন খোলো", "এনএইটেন চালু", "open n8n", "n8n চালু"]
        if any(kw in q for kw in canvas_kws):
            if on_progress:
                on_progress("🌐 এনএইটেন ভিজ্যুয়াল ক্যানভাস খোলা হচ্ছে...")
            return N8nController.open_canvas()

        # 2. Status check
        if "স্ট্যাটাস" in q or "status" in q:
            status = N8nController.get_status()
            running_str = "চালু রয়েছে" if status.get("is_running") else "অফলাইনে রয়েছে"
            msg = f"এনএইটেন সার্ভার বর্তমানে {running_str} (পোর্ট {status.get('port')})।"
            return {"success": True, "message": msg, "status": status}

        # 3. Export / Get Starter Workflow
        if "টেমপ্লেট" in q or "template" in q or "ওয়ার্কফ্লো ফাইল" in q:
            path = N8nController.export_starter_workflow()
            msg = f"এনএইটেন স্টার্টার ওয়ার্কফ্লো প্রস্তুত: {path.name}"
            return {"success": True, "message": msg, "file": str(path)}

        # 4. Trigger Webhook Workflow
        if on_progress:
            on_progress(f"⚡ এনএইটেন ফ্লো ট্রিগার করা হচ্ছে: '{query[:40]}'...")
        return N8nController.execute_workflow(query)
