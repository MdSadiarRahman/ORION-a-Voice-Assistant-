"""
AST-based Repository Map Generator.
Implements Aider's RepoMap Architecture:
Extracts classes, methods, functions, and docstring signatures from Python files
to provide high-density semantic context of the entire codebase for AI agents.
"""
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import BASE_DIR, CODER_MAX_MAP_TOKENS


class RepoMapGenerator:
    """
    Scans the repository and builds a concise, ranked AST map of classes and functions.
    """

    @classmethod
    def generate_repo_map(
        cls,
        root_dir: Optional[Path] = None,
        max_files: int = 40,
        max_lines: int = 250
    ) -> Dict[str, Any]:
        """
        Extracts AST signatures for all Python files in the repository.
        """
        work_dir = root_dir or (BASE_DIR / "src")
        map_lines: List[str] = [f"# VoiceMate Repository Map: {work_dir.name}\n"]

        py_files = sorted(list(work_dir.rglob("*.py")), key=lambda p: (len(p.parts), p.name))
        ignore_dirs = {"__pycache__", ".venv", "tests"}

        scanned_count = 0
        total_symbols = 0

        for p in py_files:
            if any(ign in p.parts for ign in ignore_dirs):
                continue
            if scanned_count >= max_files:
                break

            rel_path = p.relative_to(BASE_DIR) if BASE_DIR in p.parents else p
            try:
                source = p.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source, filename=str(p))
            except Exception:
                continue

            file_symbols: List[str] = []

            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    total_symbols += 1
                    file_symbols.append(f"  class {node.name}:")
                    for sub in node.body:
                        if isinstance(sub, ast.FunctionDef):
                            total_symbols += 1
                            args = [a.arg for a in sub.args.args if a.arg != "self"]
                            args_str = ", ".join(args[:4])
                            if len(sub.args.args) > 4:
                                args_str += ", ..."
                            file_symbols.append(f"    def {sub.name}({args_str})")

                elif isinstance(node, ast.FunctionDef):
                    total_symbols += 1
                    args = [a.arg for a in node.args.args]
                    args_str = ", ".join(args[:4])
                    file_symbols.append(f"  def {node.name}({args_str})")

            if file_symbols:
                scanned_count += 1
                map_lines.append(f"{rel_path}:")
                map_lines.extend(file_symbols)
                map_lines.append("")

            if len(map_lines) >= max_lines:
                map_lines.append("... [repo map truncated]")
                break

        repo_map_text = "\n".join(map_lines)
        return {
            "success": True,
            "scanned_files": scanned_count,
            "total_symbols": total_symbols,
            "repo_map": repo_map_text,
            "message": f"রেপো ম্যাপ তৈরি সম্পন্ন: {scanned_count}টি ফাইল ও {total_symbols}টি ফাংশন/ক্লাস ইনডেক্স করা হয়েছে।"
        }
