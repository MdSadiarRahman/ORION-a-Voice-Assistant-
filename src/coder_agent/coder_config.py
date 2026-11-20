"""
Configuration and Environment Discovery for Aider Code Editing Subsystem.
Tracks Aider repo path, workspace directory, and auto-commit preferences.
"""
from pathlib import Path
from typing import Dict, Any

from config import (
    AIDER_REPO_DIR,
    BASE_DIR,
    CODER_BACKUPS_DIR,
    CODER_ENABLED,
    CODER_AUTO_COMMIT,
    CODER_MAX_MAP_TOKENS,
)


def get_coder_settings() -> Dict[str, Any]:
    """Returns active Aider Coder configuration dictionary."""
    return {
        "repo_path": str(AIDER_REPO_DIR),
        "repo_exists": AIDER_REPO_DIR.exists(),
        "workspace_dir": str(BASE_DIR),
        "backups_dir": str(CODER_BACKUPS_DIR),
        "enabled": CODER_ENABLED,
        "auto_commit": CODER_AUTO_COMMIT,
        "max_map_tokens": CODER_MAX_MAP_TOKENS,
    }
