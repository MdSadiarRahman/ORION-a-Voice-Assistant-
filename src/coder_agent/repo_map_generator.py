"""AST-based Python repository map generation."""

import ast
import os
from pathlib import Path
from typing import Any

from config import CANVAS_WORKSPACE_DIR

_EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "build", "dist"}


class RepoMapGenerator:
    @classmethod
    def generate_repo_map(cls, max_files: int = 100) -> dict[str, Any]:
        root = Path(CANVAS_WORKSPACE_DIR).resolve()
        entries: list[str] = []
        scanned_files = 0
        for directory, dirs, files in os.walk(root):
            dirs[:] = sorted(name for name in dirs if name not in _EXCLUDED_DIRS)
            for filename in sorted(files):
                if not filename.endswith(".py"):
                    continue
                if scanned_files >= max_files:
                    break
                path = Path(directory) / filename
                scanned_files += 1
                try:
                    source = path.read_text(encoding="utf-8-sig")
                    tree = ast.parse(source, filename=str(path))
                except (OSError, SyntaxError, UnicodeError):
                    continue
                symbols = [
                    f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}"
                    for node in tree.body
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                relative = path.relative_to(root).as_posix()
                entries.append(f"{relative}: {', '.join(symbols) if symbols else '(no top-level symbols)'}")
            if scanned_files >= max_files:
                break
        repo_map = "\n".join(entries)
        return {
            "success": scanned_files > 0,
            "scanned_files": scanned_files,
            "repo_map": repo_map,
        }
