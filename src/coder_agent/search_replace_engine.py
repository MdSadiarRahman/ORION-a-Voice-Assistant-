"""Parser and exact-match applier for Aider-style SEARCH/REPLACE blocks."""

import re
from pathlib import Path

_BLOCK = re.compile(
    r"(?m)^(?P<file>[^\r\n]+)\r?\n<<<<<<< SEARCH\r?\n"
    r"(?P<search>.*?)\r?\n=======\r?\n(?P<replace>.*?)\r?\n>>>>>>> REPLACE\s*$",
    re.DOTALL,
)


class SearchReplaceEngine:
    @staticmethod
    def find_original_update_blocks(content: str) -> list[tuple[str, str, str]]:
        return [
            (match.group("file").strip(), match.group("search"), match.group("replace"))
            for match in _BLOCK.finditer(content.strip())
        ]

    @staticmethod
    def apply_replacement(original: str, search: str, replace: str) -> tuple[str, bool, str]:
        if not search:
            return original, False, "SEARCH block must not be empty."
        count = original.count(search)
        if count != 1:
            return original, False, f"Expected one exact match, found {count}."
        return original.replace(search, replace, 1), True, "exact"

    @staticmethod
    def resolve_target(workspace_dir: Path, filename: str) -> Path:
        workspace = workspace_dir.resolve()
        target = (workspace / filename).resolve()
        if target != workspace and workspace not in target.parents:
            raise ValueError(f"Target escapes workspace: {filename}")
        return target
