"""Configuration for local repository editing tools."""

from typing import Any

from config import AIDER_REPO_DIR, CODER_BACKUPS_DIR, CODER_ENABLED, CANVAS_WORKSPACE_DIR


def get_coder_settings() -> dict[str, Any]:
    return {
        "repo_path": str(AIDER_REPO_DIR),
        "repo_exists": AIDER_REPO_DIR.exists(),
        "workspace_dir": str(CANVAS_WORKSPACE_DIR),
        "backups_dir": str(CODER_BACKUPS_DIR),
        "enabled": CODER_ENABLED,
    }
