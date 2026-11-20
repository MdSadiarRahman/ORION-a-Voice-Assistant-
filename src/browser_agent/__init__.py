"""
VoiceMate Laptop Agent - Autonomous Browser Agent Subsystem.
Powered by Browser-Use 1.0 (Pydantic AI + REPL + CDP).
"""
from src.browser_agent.browser_task_runner import BrowserTaskRunner
from src.browser_agent.browser_use_integration import BrowserUseAgent

__all__ = ["BrowserTaskRunner", "BrowserUseAgent"]
