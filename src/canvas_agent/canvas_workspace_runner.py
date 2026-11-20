"""
Workspace & Terminal Execution Engine for OpenHands Developer Canvas.
Provides sandboxed command execution, git inspections, file tree generation,
and code auditing with real-time ACP event streaming.
"""
import ast
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import CANVAS_WORKSPACE_DIR
from src.canvas_agent.canvas_event_stream import CanvasEventStream, EventKind


class CanvasWorkspaceRunner:
    """
    Executes developer operations, terminal commands, and repository
    diagnostics in the active workspace.
    """

    DANGEROUS_PATTERNS = [
        r"format\s+[a-zA-Z]:",
        r"del\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\",
        r"rmdir\s+/[sS]\s+/[qQ]\s+[cC]:\\",
        r"rm\s+-rf\s+/",
        r":\(\)\{\s*:\|:&\s*\};:",  # Fork bomb
        r"shutdown\s+/[sS]",
    ]

    @classmethod
    def is_safe_command(cls, cmd: str) -> bool:
        """Checks command against destructive/system corruption patterns."""
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return False
        return True

    @classmethod
    def execute_terminal_command(
        cls,
        cmd: str,
        cwd: Optional[Path] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Executes a shell command in the workspace and streams ACP events.
        """
        work_dir = cwd or CANVAS_WORKSPACE_DIR
        stream = CanvasEventStream.get_instance()

        if not cls.is_safe_command(cmd):
            msg = f"নিরাপত্তাজনিত কারণে কমান্ড বাতিল করা হয়েছে: '{cmd}'"
            stream.emit(EventKind.APPROVAL_REQUIRED, msg, {"command": cmd})
            return {
                "success": False,
                "command": cmd,
                "error": "Command blocked by security safety policy",
                "message": msg
            }

        stream.emit(EventKind.ACTION, f"টার্মিনাল এক্সিকিউশন: {cmd}", {"command": cmd, "cwd": str(work_dir)})

        try:
            res = subprocess.run(
                cmd,
                shell=True,
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )

            stdout = res.stdout.strip()
            stderr = res.stderr.strip()

            stream.emit(
                EventKind.TERMINAL,
                stdout if stdout else stderr,
                {"stdout": stdout, "stderr": stderr, "exit_code": res.returncode}
            )

            output = stdout or stderr or "(কোন আউটপুট নেই)"
            return {
                "success": res.returncode == 0,
                "command": cmd,
                "exit_code": res.returncode,
                "output": output,
                "message": f"কমান্ড সম্পন্ন হয়েছে (Exit code: {res.returncode}):\n{output[:400]}"
            }
        except subprocess.TimeoutExpired:
            err_msg = f"কমান্ড নির্ধারিত সময়ে শেষ হয়নি (Timeout {timeout}s): {cmd}"
            stream.emit(EventKind.OBSERVATION, err_msg)
            return {"success": False, "command": cmd, "error": "Timeout", "message": err_msg}
        except Exception as e:
            err_msg = f"টার্মিনাল কমান্ডে ত্রুটি: {str(e)}"
            stream.emit(EventKind.OBSERVATION, err_msg)
            return {"success": False, "command": cmd, "error": str(e), "message": err_msg}

    @classmethod
    def get_git_status(cls, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Runs git status on the workspace."""
        work_dir = cwd or CANVAS_WORKSPACE_DIR
        stream = CanvasEventStream.get_instance()
        stream.emit(EventKind.THINKING, "গিট রেপোজিটরি স্ট্যাটাস পর্যবেক্ষণ করা হচ্ছে...")

        try:
            res = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0:
                changes = res.stdout.strip()
                if not changes:
                    summary = "গিট রেপোজিটরিতে কোনো পরিবর্তন নেই (Clean Working Tree)।"
                else:
                    lines = changes.splitlines()
                    summary = f"গিট রেপোজিটরিতে {len(lines)}টি ফাইলে পরিবর্তন রয়েছে:\n" + "\n".join(lines[:10])
                stream.emit(EventKind.OBSERVATION, summary)
                return {"success": True, "clean": not bool(changes), "status": changes, "message": summary}
            else:
                summary = "গিট কমান্ড সফল হয়নি বা এটি কোনো গিট রেপোজিটরি নয়।"
                return {"success": False, "message": summary}
        except Exception as e:
            return {"success": False, "error": str(e), "message": f"গিট স্ট্যাটাস চেক করতে সমস্যা হয়েছে: {str(e)}"}

    @classmethod
    def get_file_tree(
        cls,
        root_dir: Optional[Path] = None,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """Generates an ASCII visual tree of the workspace."""
        work_dir = root_dir or CANVAS_WORKSPACE_DIR
        stream = CanvasEventStream.get_instance()
        stream.emit(EventKind.THINKING, f"প্রোজেক্ট ফাইল স্ট্রাকচার তৈরি করা হচ্ছে: {work_dir.name}")

        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "env", "build", "dist", ".idea", ".vscode"}
        lines: List[str] = [f"📂 {work_dir.name}/"]

        def _traverse(current: Path, depth: int, prefix: str):
            if depth > max_depth:
                return
            try:
                entries = sorted(list(current.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            except Exception:
                return

            visible_entries = [e for e in entries if e.name not in ignore_dirs and not e.name.startswith(".")]

            for i, entry in enumerate(visible_entries):
                is_last = (i == len(visible_entries) - 1)
                connector = "└── " if is_last else "├── "
                sub_prefix = "    " if is_last else "│   "

                if entry.is_dir():
                    lines.append(f"{prefix}{connector}📁 {entry.name}/")
                    _traverse(entry, depth + 1, prefix + sub_prefix)
                else:
                    lines.append(f"{prefix}{connector}📄 {entry.name}")

        _traverse(work_dir, 1, "")
        tree_text = "\n".join(lines[:60])
        stream.emit(EventKind.OBSERVATION, "ফাইল স্ট্রাকচার প্রস্তুত।", {"tree": tree_text})

        return {
            "success": True,
            "root": str(work_dir),
            "tree": tree_text,
            "message": f"প্রোজেক্টের ফাইল স্ট্রাকচার:\n{tree_text}"
        }

    @classmethod
    def audit_codebase(cls, root_dir: Optional[Path] = None) -> Dict[str, Any]:
        """
        Performs static Python syntax, AST parsing, and codebase diagnostics.
        """
        work_dir = root_dir or (CANVAS_WORKSPACE_DIR / "src")
        stream = CanvasEventStream.get_instance()
        stream.emit(EventKind.THINKING, f"কোডবেস অডিট ও সিনট্যাক্স অ্যানালাইসিস শুরু হচ্ছে: {work_dir.name}")

        valid_files = 0
        syntax_errors = []
        total_lines = 0

        for py_file in work_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                total_lines += len(content.splitlines())
                ast.parse(content, filename=str(py_file))
                valid_files += 1
            except SyntaxError as e:
                syntax_errors.append(f"{py_file.name}:{e.lineno} - {e.msg}")
            except Exception as e:
                syntax_errors.append(f"{py_file.name} - {str(e)}")

        if syntax_errors:
            status_msg = (
                f"কোডবেস অডিটে {len(syntax_errors)}টি ফাইলে সিনট্যাক্স ত্রুটি পাওয়া গেছে:\n"
                + "\n".join(syntax_errors[:5])
            )
            success = False
        else:
            status_msg = (
                f"কোডবেস অডিট সম্পন্ন: কোনো সিনট্যাক্স ত্রুটি পাওয়া যায়নি। "
                f"মোট {valid_files}টি পাইথন ফাইল স্ক্যান করা হয়েছে ({total_lines} লাইন কোড)।"
            )
            success = True

        stream.emit(EventKind.OBSERVATION, status_msg)
        return {
            "success": success,
            "valid_files": valid_files,
            "total_lines": total_lines,
            "syntax_errors": syntax_errors,
            "message": status_msg
        }
