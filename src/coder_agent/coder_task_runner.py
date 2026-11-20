"""
Background Task Runner for Aider Code Editing Operations.
Handles async code modifications, RepoMap indexing, and Git rollbacks
in worker threads with progress and vocalization callbacks.
"""
import re
import threading
from typing import Callable, Optional, Dict, Any

from src.coder_agent.coder_controller import CoderController


class CoderTaskRunner:
    """
    Manages non-blocking execution of Aider coding tasks.
    """

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """Runs coding task in a background daemon thread."""
        def _worker():
            try:
                if on_progress:
                    on_progress("🤖 এইডার পেয়ার প্রোগ্রামার শুরু হচ্ছে...")

                result = cls._parse_and_execute(task_query, on_progress)
                msg = result.get("message", "টাস্ক সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(msg)
            except Exception as e:
                err_msg = f"কোডার টাস্কে ত্রুটি: {str(e)}"
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
        """Interprets coding queries into specific Aider actions."""
        q = query.strip()

        # 1. Raw SEARCH/REPLACE Block in query
        if "<<<<<<< SEARCH" in q:
            if on_progress:
                on_progress("📝 SEARCH/REPLACE কোড ব্লক প্রসেস ও প্যাচ করা হচ্ছে...")
            return CoderController.apply_edit_blocks(q)

        q_lower = q.lower()

        # 2. RepoMap AST indexing
        repomap_kws = ["রেপো ম্যাপ", "repo map", "কোড ম্যাপ", "ফাংশন লিস্ট", "সিম্বল ম্যাপ"]
        if any(kw in q_lower for kw in repomap_kws):
            if on_progress:
                on_progress("🗺️ সম্পূর্ণ কোডবেসের AST সিম্বল ও রেপো ম্যাপ ইনডেক্স করা হচ্ছে...")
            return CoderController.get_repo_map()

        # 3. Rollback / Undo
        rollback_kws = ["রোলব্যাক", "পূর্বাবস্থায়", "rollback", "undo", "আনডু"]
        if any(kw in q_lower for kw in rollback_kws):
            # Try to find file name
            file_match = re.search(r'([\w.-]+\.py)', q)
            target = file_match.group(1) if file_match else ""
            if on_progress:
                on_progress(f"⏪ কোড পরিবর্তন রোলব্যাক করা হচ্ছে: {target or 'সর্বশেষ পরিবর্তন'}...")
            return CoderController.rollback_file(target)

        # 4. General code edit request
        if on_progress:
            on_progress("🗺️ কোডবেসের স্ট্রাকচার বিশ্লেষণ করা হচ্ছে...")
        return CoderController.get_repo_map()
