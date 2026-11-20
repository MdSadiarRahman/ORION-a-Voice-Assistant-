"""
Git Operations and Safety Net Manager for Aider Coder.
Ensures every code edit is backed up and optionally committed semantically,
providing an instant undo / rollback mechanism.
"""
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import BASE_DIR, CODER_BACKUPS_DIR, CODER_AUTO_COMMIT


class GitSafetyManager:
    """
    Manages Git commits, file backups, and rollbacks for autonomous code edits.
    """

    @classmethod
    def create_backup(cls, filepath: Path) -> Path:
        """Saves a timestamped backup before modifying a file."""
        p = Path(filepath)
        CODER_BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = CODER_BACKUPS_DIR / f"{p.name}_{timestamp}.bak"
        if p.exists():
            shutil.copy2(p, backup_file)
        return backup_file

    @classmethod
    def auto_commit(cls, message: str, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Performs an automated semantic git commit after a successful edit.
        """
        if not CODER_AUTO_COMMIT:
            return {"success": False, "message": "অটো-কমিট বন্ধ রয়েছে।"}

        try:
            # Check if git is available in BASE_DIR
            add_target = str(filepath) if filepath else "."
            subprocess.run(
                ["git", "add", add_target],
                cwd=str(BASE_DIR),
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            commit_msg = f"VoiceMate: {message}"
            res = subprocess.run(
                ["git", "commit", "-m", commit_msg],
                cwd=str(BASE_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )

            if res.returncode == 0:
                return {
                    "success": True,
                    "commit_message": commit_msg,
                    "message": f"গিট কমিট সফল হয়েছে: '{commit_msg}'"
                }
            else:
                return {
                    "success": False,
                    "message": "কমিট করার মতো কোনো নতুন পরিবর্তন পাওয়া যায়নি।"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"গিট অটো-কমিট সম্পন্ন হয়নি: {str(e)}"
            }

    @classmethod
    def rollback(cls, filepath: Optional[Path] = None) -> Dict[str, Any]:
        """
        Rolls back uncommitted changes or restores the latest backup.
        """
        # Strategy 1: Git checkout
        if filepath:
            try:
                res = subprocess.run(
                    ["git", "checkout", "--", str(filepath)],
                    cwd=str(BASE_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5
                )
                if res.returncode == 0:
                    return {
                        "success": True,
                        "file": str(filepath),
                        "message": f"গিট থেকে '{filepath.name}' পূর্বাবস্থায় ফিরিয়ে আনা হয়েছে।"
                    }
            except Exception:
                pass

        # Strategy 2: File backup restore
        if filepath:
            pattern = f"{filepath.name}_*.bak"
            backups = sorted(list(CODER_BACKUPS_DIR.glob(pattern)), key=lambda x: x.stat().st_mtime, reverse=True)
            if backups:
                latest = backups[0]
                shutil.copy2(latest, filepath)
                return {
                    "success": True,
                    "file": str(filepath),
                    "backup": str(latest),
                    "message": f"ব্যাকআপ ফাইল '{latest.name}' থেকে '{filepath.name}' রিস্টোর করা হয়েছে।"
                }

        return {
            "success": False,
            "message": "রোলব্যাক করার মতো কোনো গিট পরিবর্তন বা ব্যাকআপ পাওয়া যায়নি।"
        }
