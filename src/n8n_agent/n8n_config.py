"""
Configuration and Environment Discovery for n8n Workflow Automation.
Tracks repository path, webhook endpoints, ports, and server connectivity.
"""
import socket
from pathlib import Path
from typing import Dict, Any

from config import (
    N8N_REPO_DIR,
    N8N_WORKFLOWS_DIR,
    N8N_ENABLED,
    N8N_PORT,
    N8N_WEBHOOK_URL,
    N8N_TIMEOUT_SECONDS,
    N8N_AUTO_OPEN_BROWSER,
)


def is_n8n_running(host: str = "127.0.0.1", port: int = N8N_PORT, timeout: float = 0.5) -> bool:
    """Checks if n8n server is accepting connections on its default port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            res = s.connect_ex((host, port))
            return res == 0
    except Exception:
        return False


def get_n8n_settings() -> Dict[str, Any]:
    """Returns active n8n configuration dictionary."""
    return {
        "repo_path": str(N8N_REPO_DIR),
        "repo_exists": N8N_REPO_DIR.exists(),
        "workflows_dir": str(N8N_WORKFLOWS_DIR),
        "enabled": N8N_ENABLED,
        "port": N8N_PORT,
        "webhook_url": N8N_WEBHOOK_URL,
        "timeout_seconds": N8N_TIMEOUT_SECONDS,
        "is_running": is_n8n_running(),
        "auto_open_browser": N8N_AUTO_OPEN_BROWSER,
    }
