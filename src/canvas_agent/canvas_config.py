"""Configuration and status checks for the local developer canvas."""

import socket
from typing import Any

from config import (
    CANVAS_AUTO_OPEN_BROWSER,
    CANVAS_ENABLED,
    CANVAS_PORT,
    CANVAS_WORKSPACE_DIR,
    OPENHANDS_REPO_DIR,
)


def is_canvas_running(host: str = "127.0.0.1", port: int = CANVAS_PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def get_canvas_settings() -> dict[str, Any]:
    return {
        "repo_path": str(OPENHANDS_REPO_DIR),
        "repo_exists": OPENHANDS_REPO_DIR.exists(),
        "workspace_dir": str(CANVAS_WORKSPACE_DIR),
        "enabled": CANVAS_ENABLED,
        "canvas_port": CANVAS_PORT,
        "is_running": is_canvas_running(),
        "auto_open_browser": CANVAS_AUTO_OPEN_BROWSER,
    }
