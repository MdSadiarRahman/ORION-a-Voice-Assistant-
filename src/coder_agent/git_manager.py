"""Backup and restore helpers for user-requested local code edits."""

from datetime import datetime, timezone
from pathlib import Path
import shutil
from typing import Optional

from config import CANVAS_WORKSPACE_DIR, CODER_BACKUPS_DIR
from src.coder_agent.search_replace_engine import SearchReplaceEngine


class GitSafetyManager:
    @staticmethod
    def create_backup(file_path: Path) -> Path:
        source = Path(file_path).resolve()
        workspace = Path(CANVAS_WORKSPACE_DIR).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Cannot back up missing file: {source}")
        try:
            relative = source.relative_to(workspace)
        except ValueError as exc:
            raise ValueError("Backups are limited to files inside the workspace.") from exc
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = Path(CODER_BACKUPS_DIR) / stamp / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        return destination

    @classmethod
    def restore_latest_backup(cls, filename: str) -> Optional[Path]:
        workspace = Path(CANVAS_WORKSPACE_DIR).resolve()
        target = SearchReplaceEngine.resolve_target(workspace, filename)
        relative = target.relative_to(workspace)
        backups_root = Path(CODER_BACKUPS_DIR)
        candidates = sorted(
            (path for path in backups_root.glob("*/" + relative.as_posix()) if path.is_file()),
            key=lambda path: path.parent.name,
            reverse=True,
        )
        if not candidates:
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(candidates[0], target)
        return target
