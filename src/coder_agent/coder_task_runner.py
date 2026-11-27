"""Background dispatcher for safe local repository inspection and edits."""

import threading
from pathlib import Path
from typing import Any, Callable, Optional

from config import CANVAS_WORKSPACE_DIR, CODER_ENABLED
from src.coder_agent.git_manager import GitSafetyManager
from src.coder_agent.repo_map_generator import RepoMapGenerator
from src.coder_agent.search_replace_engine import SearchReplaceEngine


class CoderTaskRunner:
    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None,
    ) -> threading.Thread:
        def worker() -> None:
            if on_progress:
                on_progress("কোডার টাস্ক শুরু হচ্ছে...")
            try:
                result = cls._parse_and_execute(task_query)
                message = result.get("message", "কোডার টাস্ক সম্পন্ন হয়েছে।")
            except Exception as exc:
                message = f"কোডার টাস্কে ত্রুটি: {exc}"
            if on_finish:
                on_finish(message)

        thread = threading.Thread(target=worker, name="coder-task", daemon=True)
        thread.start()
        return thread

    @classmethod
    def _parse_and_execute(cls, query: str) -> dict[str, Any]:
        if not CODER_ENABLED:
            return {"success": False, "message": "কোডার configuration-এ বন্ধ আছে।"}

        blocks = SearchReplaceEngine.find_original_update_blocks(query)
        if blocks:
            return cls._apply_edit_blocks(blocks)

        q = query.lower().strip()
        if any(word in q for word in ("রেপো ম্যাপ", "repo map", "repository map")):
            result = RepoMapGenerator.generate_repo_map()
            result["message"] = (
                f"রেপো ম্যাপ তৈরি হয়েছে ({result['scanned_files']}টি Python ফাইল)।\n{result['repo_map']}"
                if result["success"] else "রেপো ম্যাপ তৈরি করা যায়নি: Python ফাইল পাওয়া যায়নি।"
            )
            return result
        if any(word in q for word in ("রোলব্যাক", "rollback")):
            words = query.strip().split()
            filename = words[-1] if len(words) > 1 and "." in words[-1] else ""
            if not filename:
                return {
                    "success": False,
                    "message": "নির্দিষ্ট workspace ফাইলের নাম দিন, যেমন: কোড রোলব্যাক src/example.py",
                }
            restored = GitSafetyManager.restore_latest_backup(filename)
            return {
                "success": restored is not None,
                "message": f"{filename} আগের backup থেকে restore হয়েছে." if restored else f"{filename}-এর backup পাওয়া যায়নি.",
            }
        if any(word in q for word in ("কোড এডিট", "edit code", "apply patch")):
            return {
                "success": False,
                "message": "কোড বদলাতে filename এবং সম্পূর্ণ SEARCH/REPLACE block দিন; পরিবর্তনের আগে backup তৈরি হবে।",
            }
        return {
            "success": False,
            "message": "সমর্থিত কাজ: repo map, নির্দিষ্ট ফাইল rollback, অথবা exact SEARCH/REPLACE block প্রয়োগ।",
        }

    @classmethod
    def _apply_edit_blocks(cls, blocks: list[tuple[str, str, str]]) -> dict[str, Any]:
        workspace = Path(CANVAS_WORKSPACE_DIR).resolve()
        planned: dict[Path, str] = {}
        for filename, search, replace in blocks:
            try:
                target = SearchReplaceEngine.resolve_target(workspace, filename)
                if not target.is_file():
                    return {"success": False, "message": f"ফাইল পাওয়া যায়নি: {filename}"}
                original = (
                    planned[target]
                    if target in planned
                    else target.read_text(encoding="utf-8")
                )
                updated, success, reason = SearchReplaceEngine.apply_replacement(original, search, replace)
            except (OSError, UnicodeError, ValueError) as exc:
                return {"success": False, "message": f"{filename} পরিবর্তন করা যায়নি: {exc}"}
            if not success:
                return {"success": False, "message": f"{filename} পরিবর্তন করা হয়নি: {reason}"}
            planned[target] = updated

        backups: list[tuple[Path, Path]] = []
        try:
            for target, updated in planned.items():
                backup = GitSafetyManager.create_backup(target)
                backups.append((target, backup))
                target.write_text(updated, encoding="utf-8")
        except (OSError, ValueError) as exc:
            for target, backup in reversed(backups):
                target.write_bytes(backup.read_bytes())
            return {"success": False, "message": f"কোড পরিবর্তন ব্যর্থ; পূর্বাবস্থা restore করা হয়েছে: {exc}"}

        files = [str(target.relative_to(workspace)) for target in planned]
        return {
            "success": True,
            "files": files,
            "backups": [str(backup) for _, backup in backups],
            "message": f"SEARCH/REPLACE সম্পন্ন; {len(files)}টি ফাইল backup-সহ পরিবর্তন হয়েছে।",
        }
