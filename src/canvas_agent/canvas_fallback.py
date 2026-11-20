"""
Fallback Developer Handler for OpenHands Canvas.
Used when the Node.js OpenHands Agent Canvas server is offline or initializing.
Provides direct terminal diagnostics and workspace assistance.
"""
import webbrowser
from typing import Dict, Any

from config import CANVAS_PORT
from src.canvas_agent.canvas_workspace_runner import CanvasWorkspaceRunner


class CanvasFallbackAgent:
    """
    Fallback agent providing direct Python-based workspace commands,
    git inspections, and developer information.
    """

    @staticmethod
    def open_canvas_in_browser() -> Dict[str, Any]:
        """Opens the canvas URL in the system browser."""
        url = f"http://localhost:{CANVAS_PORT}"
        opened = webbrowser.open(url)
        return {
            "success": opened,
            "action": "open_canvas_browser",
            "url": url,
            "message": f"ওপেনহ্যান্ডস ক্যানভাস ওয়েব পেজ ওপেন করা হয়েছে ({url})।",
            "driver": "fallback_webbrowser"
        }

    @staticmethod
    def execute_developer_task(task_type: str, param: str = "") -> Dict[str, Any]:
        """Routes developer commands to local workspace runner."""
        t = task_type.lower()
        if "tree" in t or "ফাইল" in t:
            return CanvasWorkspaceRunner.get_file_tree()
        elif "git" in t or "গিট" in t:
            return CanvasWorkspaceRunner.get_git_status()
        elif "audit" in t or "অডিট" in t or "রিভিউ" in t:
            return CanvasWorkspaceRunner.audit_codebase()
        elif "cmd" in t or "কমান্ড" in t or "টার্মিনাল" in t:
            return CanvasWorkspaceRunner.execute_terminal_command(param or "dir")
        else:
            return CanvasWorkspaceRunner.audit_codebase()
