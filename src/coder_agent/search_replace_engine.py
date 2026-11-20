"""
Search and Replace Block Editing Engine.
Implements Aider's Canonical EditBlock Architecture:
<<<<<<< SEARCH
...
=======
...
>>>>>>> REPLACE
Provides resilient matching strategies (exact, whitespace-normalized, relative indentation).
"""
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any


HEAD_PATTERN = re.compile(r"^<{5,9}\s*SEARCH\s*$", re.MULTILINE)
DIVIDER_PATTERN = re.compile(r"^={5,9}\s*$", re.MULTILINE)
UPDATED_PATTERN = re.compile(r"^>{5,9}\s*REPLACE\s*$", re.MULTILINE)


class SearchReplaceEngine:
    """
    Parses and applies Aider-style SEARCH/REPLACE blocks with high resilience.
    """

    @classmethod
    def find_original_update_blocks(cls, text: str) -> List[Tuple[Optional[str], str, str]]:
        """
        Parses text for one or more edit blocks formatted as:
        [optional_filename]
        <<<<<<< SEARCH
        original code
        =======
        updated code
        >>>>>>> REPLACE

        Returns list of tuples: (filename, search_block, replace_block)
        """
        blocks = []
        lines = text.splitlines(keepends=True)
        i = 0
        current_filename = None

        head_re = re.compile(r"^<{5,9}\s*SEARCH\s*$")
        div_re = re.compile(r"^={5,9}\s*$")
        upd_re = re.compile(r"^>{5,9}\s*REPLACE\s*$")

        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Check if this line looks like a file path right before SEARCH
            if not stripped.startswith("<") and not stripped.startswith("`") and stripped:
                # Potential filename
                if any(stripped.endswith(ext) for ext in [".py", ".md", ".txt", ".json", ".js", ".ts", ".html", ".css", ".sh"]):
                    current_filename = stripped.strip("`'\" :")

            if head_re.match(stripped):
                search_lines = []
                replace_lines = []
                i += 1

                # Read search block
                while i < len(lines) and not div_re.match(lines[i].strip()):
                    search_lines.append(lines[i])
                    i += 1

                # Read replace block
                if i < len(lines) and div_re.match(lines[i].strip()):
                    i += 1
                    while i < len(lines) and not upd_re.match(lines[i].strip()):
                        replace_lines.append(lines[i])
                        i += 1

                search_text = "".join(search_lines)
                replace_text = "".join(replace_lines)

                blocks.append((current_filename, search_text, replace_text))
                current_filename = None

            i += 1

        return blocks

    @classmethod
    def apply_replacement(
        cls,
        whole_content: str,
        search_block: str,
        replace_block: str
    ) -> Tuple[str, bool, str]:
        """
        Applies a single search/replace operation using multiple progressive strategies:
        1. Exact match
        2. Cleaned whitespace/newlines match
        3. Line-by-line fuzzy match (ignoring leading indentation differences)
        """
        # If search_block is empty, append to the file or start a new file
        if not search_block.strip():
            return whole_content + replace_block, True, "append"

        # Strategy 1: Exact match
        if search_block in whole_content:
            new_content = whole_content.replace(search_block, replace_block, 1)
            return new_content, True, "exact"

        # Strategy 2: Whitespace-normalized match (uniform \r\n vs \n)
        norm_whole = whole_content.replace("\r\n", "\n")
        norm_search = search_block.replace("\r\n", "\n")
        norm_replace = replace_block.replace("\r\n", "\n")

        if norm_search in norm_whole:
            new_norm = norm_whole.replace(norm_search, norm_replace, 1)
            # Restore original newline style if needed
            if "\r\n" in whole_content:
                new_norm = new_norm.replace("\n", "\r\n")
            return new_norm, True, "normalized_newlines"

        # Strategy 3: Strip leading/trailing blank lines in search block
        stripped_search = norm_search.strip("\n")
        if stripped_search in norm_whole:
            new_norm = norm_whole.replace(stripped_search, norm_replace.strip("\n"), 1)
            return new_norm, True, "stripped_blank_lines"

        # Strategy 4: Relative Indentation / Line-by-line whitespace-tolerant match
        search_lines = [l.strip() for l in norm_search.splitlines() if l.strip()]
        whole_lines = norm_whole.splitlines(keepends=True)

        if search_lines:
            match_start = -1
            for idx in range(len(whole_lines) - len(search_lines) + 1):
                window = [whole_lines[idx + j].strip() for j in range(len(search_lines))]
                if window == search_lines:
                    match_start = idx
                    break

            if match_start != -1:
                # Found chunk match!
                before = whole_lines[:match_start]
                after = whole_lines[match_start + len(search_lines):]
                # Insert replace lines
                rep_lines = norm_replace.splitlines(keepends=True)
                new_lines = before + rep_lines + after
                return "".join(new_lines), True, "relative_indent_match"

        return whole_content, False, "failed"

    @classmethod
    def patch_file(
        cls,
        filepath: Path,
        search_block: str,
        replace_block: str
    ) -> Dict[str, Any]:
        """
        Reads file, applies replacement, and writes updated content to disk.
        """
        p = Path(filepath)
        if not p.exists() and not search_block.strip():
            # Create new file
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(replace_block, encoding="utf-8")
            return {
                "success": True,
                "strategy": "created_new_file",
                "file": str(p),
                "message": f"নতুন ফাইল তৈরি করা হয়েছে: {p.name}"
            }

        if not p.exists():
            return {
                "success": False,
                "file": str(p),
                "error": f"File does not exist: {p}",
                "message": f"ফাইলটি খুঁজে পাওয়া যায়নি: {p.name}"
            }

        original_content = p.read_text(encoding="utf-8", errors="replace")
        new_content, success, strategy = cls.apply_replacement(original_content, search_block, replace_block)

        if success:
            p.write_text(new_content, encoding="utf-8")
            return {
                "success": True,
                "strategy": strategy,
                "file": str(p),
                "message": f"ফাইল '{p.name}' সফলভাবে আপডেট হয়েছে ({strategy} স্ট্র্যাটেজি)।"
            }
        else:
            return {
                "success": False,
                "strategy": strategy,
                "file": str(p),
                "error": "Search block not found in file",
                "message": f"সার্চ ব্লকটি ফাইলে মেলেনি: {p.name}"
            }
