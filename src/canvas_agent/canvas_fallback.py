"""Local fallback actions used by the LangGraph coding worker."""

from src.canvas_agent.canvas_task_runner import CanvasTaskRunner


class CanvasFallbackHandler:
    @staticmethod
    def execute_local_action(query: str) -> dict:
        result = CanvasTaskRunner._parse_and_execute(query)
        return {
            **result,
            "message": result.get("message", "ক্যানভাস টাস্ক সম্পন্ন হয়েছে।"),
        }
