"""Background dispatcher for deterministic browser automation tasks."""

import threading
from typing import Callable, Optional

from src.playwright_agent.playwright_controller import PlaywrightController


class PlaywrightTaskRunner:
    @staticmethod
    def _parse_and_execute(task_query: str) -> dict[str, str]:
        return PlaywrightController.parse_task(task_query)

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None,
    ) -> threading.Thread:
        def worker() -> None:
            if on_progress:
                on_progress(f"Playwright task শুরু: {task_query}")
            try:
                result = PlaywrightController.execute_task(task_query)
                message = str(result.get("message", "Playwright task শেষ হয়েছে।"))
                if not result.get("success"):
                    message = f"ব্যর্থ: {message}"
            except Exception as exc:
                message = f"Playwright task-এ সমস্যা হয়েছে: {exc}"
            if on_finish:
                on_finish(message)

        thread = threading.Thread(target=worker, name="playwright-task", daemon=True)
        thread.start()
        return thread
