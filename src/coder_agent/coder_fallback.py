"""
Fallback Code Assistant for VoiceMate.
Provides direct file inspections and fallback diff application when Git or external
dependencies are unconfigured.
"""
from pathlib import Path
from typing import Dict, Any

from config import BASE_DIR


class CoderFallbackAgent:
    """
    Fallback agent for code viewing and safe manual replacements.
    """

    @staticmethod
    def view_file(filepath_str: str) -> Dict[str, Any]:
        """Reads file content safely."""
        target = Path(filepath_str)
        if not target.is_absolute():
            target = BASE_DIR / target

        if not target.exists():
            return {
                "success": False,
                "file": str(target),
                "message": f"ফাইলটি খুঁজে পাওয়া যায়নি: {target.name}"
            }

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            preview = "\n".join(lines[:30])
            return {
                "success": True,
                "file": str(target),
                "total_lines": len(lines),
                "preview": preview,
                "message": f"ফাইল '{target.name}' ({len(lines)} লাইন):\n{preview}"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"ফাইল পড়তে সমস্যা: {str(e)}"}
