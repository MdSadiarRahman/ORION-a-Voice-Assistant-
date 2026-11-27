"""Read-only workspace inspection and narrowly allowlisted terminal actions."""

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from config import CANVAS_WORKSPACE_DIR

_EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}
_ALLOWED_COMMANDS = {"dir", "ls", "python --version", "git status"}


class CanvasWorkspaceRunner:
    @staticmethod
    def _workspace() -> Path:
        return Path(CANVAS_WORKSPACE_DIR).resolve()

    @classmethod
    def is_safe_command(cls, command: str) -> bool:
        normalized = " ".join(command.strip().lower().split())
        if normalized in _ALLOWED_COMMANDS:
            return True
        if normalized.startswith("echo "):
            return not any(char in command for char in ("&", "|", ";", "`", "$", "\n", "\r"))
        return False

    @classmethod
    def execute_terminal_command(cls, command: str) -> dict[str, Any]:
        if not cls.is_safe_command(command):
            return {"success": False, "command": command, "output": "", "error": "Command is not allowlisted."}

        normalized = " ".join(command.strip().lower().split())
        if normalized.startswith("echo "):
            return {"success": True, "command": command, "output": command.strip()[5:], "error": ""}

        workspace = cls._workspace()
        if normalized == "dir" or normalized == "ls":
            output = "\n".join(sorted(path.name for path in workspace.iterdir()))
            return {"success": True, "command": command, "output": output, "error": ""}

        if normalized == "python --version":
            argv = [sys.executable, "--version"]
        else:
            argv = ["git", "-C", str(workspace), "status", "--short"]

        try:
            result = subprocess.run(
                argv,
                cwd=str(workspace),
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"success": False, "command": command, "output": "", "error": str(exc)}
        output = (result.stdout or result.stderr).strip()
        return {
            "success": result.returncode == 0,
            "command": command,
            "output": output,
            "error": "" if result.returncode == 0 else output,
        }

    @classmethod
    def audit_codebase(cls) -> dict[str, Any]:
        workspace = cls._workspace()
        valid_files = 0
        syntax_errors: list[dict[str, Any]] = []
        for root, dirs, filenames in os.walk(workspace):
            dirs[:] = [name for name in dirs if name not in _EXCLUDED_DIRS]
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                path = Path(root) / filename
                try:
                    ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
                    valid_files += 1
                except (OSError, SyntaxError, UnicodeError) as exc:
                    syntax_errors.append({
                        "file": str(path.relative_to(workspace)),
                        "error": str(exc),
                    })
        return {
            "success": valid_files > 0 and not syntax_errors,
            "valid_files": valid_files,
            "syntax_errors": syntax_errors,
        }

    @classmethod
    def get_file_tree(cls, max_depth: int = 2) -> dict[str, Any]:
        workspace = cls._workspace()
        tree: list[str] = []
        for root, dirs, filenames in os.walk(workspace):
            current = Path(root)
            depth = len(current.relative_to(workspace).parts)
            dirs[:] = sorted(name for name in dirs if name not in _EXCLUDED_DIRS)
            if depth >= max_depth:
                dirs[:] = []
            prefix = "  " * depth
            for name in sorted(dirs):
                tree.append(f"{prefix}{name}/")
            for name in sorted(filenames):
                tree.append(f"{prefix}{name}")
        return {"success": True, "tree": "\n".join(tree), "workspace_dir": str(workspace)}
