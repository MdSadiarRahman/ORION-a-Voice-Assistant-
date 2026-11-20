"""
Configuration and Environment Discovery for OpenHands Agent Canvas.
Detects local OpenHands repository, Node.js runtime, and workspace settings.
"""
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any

from config import (
    OPENHANDS_REPO_DIR,
    CANVAS_WORKSPACE_DIR,
    CANVAS_PORT,
    CANVAS_AGENT_SERVER_PORT,
    CANVAS_AUTOMATION_PORT,
    CANVAS_AUTO_OPEN_BROWSER,
)


def get_node_executable() -> str:
    """Finds node executable on system path."""
    return shutil.which("node") or "node"


def is_node_available() -> bool:
    """Checks if Node.js is executable."""
    try:
        res = subprocess.run(
            [get_node_executable(), "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        return res.returncode == 0
    except Exception:
        return False


def get_canvas_settings() -> Dict[str, Any]:
    """Returns active OpenHands Canvas configuration."""
    repo_exists = OPENHANDS_REPO_DIR.exists()
    bin_script = OPENHANDS_REPO_DIR / "bin" / "agent-canvas.mjs"

    return {
        "repo_path": str(OPENHANDS_REPO_DIR),
        "repo_exists": repo_exists,
        "entrypoint_script": str(bin_script),
        "entrypoint_exists": bin_script.exists(),
        "node_available": is_node_available(),
        "workspace_dir": str(CANVAS_WORKSPACE_DIR),
        "canvas_port": CANVAS_PORT,
        "agent_server_port": CANVAS_AGENT_SERVER_PORT,
        "automation_port": CANVAS_AUTOMATION_PORT,
        "auto_open_browser": CANVAS_AUTO_OPEN_BROWSER,
    }
