"""Local fallback actions for the LangGraph coding worker."""

from src.coder_agent.coder_task_runner import CoderTaskRunner


class CoderFallbackReader:
    @staticmethod
    def execute_local_action(query: str) -> dict:
        return CoderTaskRunner._parse_and_execute(query)
