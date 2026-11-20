"""
Aider Coder Controller for VoiceMate.
Coordinates SEARCH/REPLACE code patch applications, AST RepoMap generation,
and Git automated commits.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import BASE_DIR
from src.coder_agent.search_replace_engine import SearchReplaceEngine
from src.coder_agent.repo_map_generator import RepoMapGenerator
from src.coder_agent.git_manager import GitSafetyManager


class CoderController:
    """
    High-level controller for AI Pair Programming and precise file modifications.
    """

    @classmethod
    def apply_edit_blocks(
        cls,
        edit_blocks_text: str,
        target_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parses SEARCH/REPLACE blocks from text and applies them to the workspace.
        """
        blocks = SearchReplaceEngine.find_original_update_blocks(edit_blocks_text)

        if not blocks:
            # Check if text contains a raw replacement or command
            return {
                "success": False,
                "applied_count": 0,
                "message": "কোনো বৈধ SEARCH/REPLACE ব্লক পাওয়া যায়নি। ফরম্যাট: <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE"
            }

        results: List[Dict[str, Any]] = []

        for b_filename, search_block, replace_block in blocks:
            fname = b_filename or target_file
            if not fname:
                results.append({
                    "success": False,
                    "error": "No filename specified for edit block"
                })
                continue

            filepath = Path(fname)
            if not filepath.is_absolute():
                filepath = BASE_DIR / filepath

            # 1. Create safety backup
            GitSafetyManager.create_backup(filepath)

            # 2. Patch file
            patch_res = SearchReplaceEngine.patch_file(filepath, search_block, replace_block)
            results.append(patch_res)

            # 3. Auto-commit if successful
            if patch_res.get("success"):
                GitSafetyManager.auto_commit(f"Update {filepath.name} via Aider Coder", filepath)

        successful = [r for r in results if r.get("success")]
        total = len(blocks)
        summary = f"মোট {len(successful)}/{total}টি কোড ব্লক সফলভাবে অ্যাপ্লাই করা হয়েছে।"

        return {
            "success": len(successful) > 0,
            "applied_count": len(successful),
            "total_blocks": total,
            "details": results,
            "message": summary
        }

    @classmethod
    def apply_single_patch(
        cls,
        filepath_str: str,
        search_text: str,
        replace_text: str
    ) -> Dict[str, Any]:
        """Applies a single search and replace operation to a specific file."""
        p = Path(filepath_str)
        if not p.is_absolute():
            p = BASE_DIR / p

        GitSafetyManager.create_backup(p)
        res = SearchReplaceEngine.patch_file(p, search_text, replace_text)

        if res.get("success"):
            GitSafetyManager.auto_commit(f"Patch {p.name}", p)

        return res

    @classmethod
    def get_repo_map(cls) -> Dict[str, Any]:
        """Generates AST-based repository map."""
        return RepoMapGenerator.generate_repo_map()

    @classmethod
    def rollback_file(cls, filepath_str: str) -> Dict[str, Any]:
        """Restores file from Git or backup."""
        p = Path(filepath_str)
        if not p.is_absolute():
            p = BASE_DIR / p
        return GitSafetyManager.rollback(p)
