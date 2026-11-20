"""
VoiceMate Laptop Agent - Browser Task Runner Subsystem.
Executes browser agent jobs in non-blocking background threads,
providing real-time feedback to VoiceMate's UI and voice engine.
"""
import threading
from typing import Optional, Callable
from src.browser_agent.browser_use_integration import BrowserUseAgent

class BrowserTaskRunner:
    @classmethod
    def run_in_background(
        cls,
        task: str,
        on_start: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """
        Dispatches a browser agent task in a non-blocking background thread.
        """
        def _worker():
            if on_start:
                try:
                    on_start(task)
                except Exception:
                    pass

            agent = BrowserUseAgent(on_progress=on_progress)
            result = agent.run_sync(task)

            if on_finish:
                try:
                    on_finish(result)
                except Exception:
                    pass

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
