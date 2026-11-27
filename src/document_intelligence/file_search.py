"""
Phase 1: File Search Engine (file_search.py)
Searches user-authorized Windows drives and folders for documents using:
1. Exact filename search
2. Partial filename search
3. File extension search
4. Folder name search
5. Document content search
6. Natural-language description matching

Excludes protected system folders and sensitive directories by default.
Supports cancellation and progress reporting.
"""
import os
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Set


SUPPORTED_EXTENSIONS: Set[str] = {
    ".pdf", ".docx", ".doc", ".txt", ".md", ".pptx", ".xlsx", ".csv"
}

DEFAULT_EXCLUDED_DIRS: Set[str] = {
    "windows", "program files", "program files (x86)", "programdata",
    "$recycle.bin", "system volume information", "appdata", "node_modules",
    ".git", ".venv", "venv", "__pycache__", "recovery", "perflogs",
    "msocache", "intel", "amd", "nvidia"
}


@dataclass
class FileSearchResult:
    path: Path
    filename: str
    extension: str
    folder: str
    size_bytes: int
    modified_time: float
    match_type: str  # exact_name, partial_name, extension, folder, content, nl_description
    score: float = 0.0
    matched_snippet: str = ""


class FileSearchEngine:
    """Modular, safe Windows PC file search engine."""

    def __init__(
        self,
        authorized_roots: Optional[List[Path]] = None,
        excluded_dirs: Optional[Set[str]] = None,
        allowed_extensions: Optional[Set[str]] = None,
    ):
        self.authorized_roots = authorized_roots or self._default_authorized_roots()
        self.excluded_dirs = {d.lower() for d in (excluded_dirs or DEFAULT_EXCLUDED_DIRS)}
        self.allowed_extensions = {e.lower() for e in (allowed_extensions or SUPPORTED_EXTENSIONS)}

    @staticmethod
    def _default_authorized_roots() -> List[Path]:
        home = Path.home()
        candidates = [
            home / "Desktop",
            home / "Downloads",
            home / "Documents",
            home / "OneDrive" / "Desktop",
            home / "OneDrive" / "Documents",
        ]
        return [p for p in candidates if p.exists() and p.is_dir()]

    @staticmethod
    def get_available_drives() -> List[Path]:
        """Returns available Windows drive roots (e.g., C:\\, D:\\)."""
        drives: List[Path] = []
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{letter}:\\")
            if drive.exists():
                drives.append(drive)
        return drives

    def _is_excluded(self, dir_name: str) -> bool:
        lower = dir_name.lower()
        return lower in self.excluded_dirs or lower.startswith(".")

    def iter_authorized_files(
        self,
        roots: Optional[List[Path]] = None,
        extensions: Optional[Set[str]] = None,
        cancel_event: Optional[threading.Event] = None,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> Iterable[Path]:
        """Safely walks authorized roots, skipping protected/hidden directories."""
        target_roots = roots or self.authorized_roots
        target_exts = {e.lower() for e in (extensions or self.allowed_extensions)}
        scanned = 0

        for root in target_roots:
            if not root.exists():
                continue
            for current_root, dirs, files in os.walk(root, topdown=True):
                if cancel_event and cancel_event.is_set():
                    return
                # Prune excluded directories in-place
                dirs[:] = [d for d in dirs if not self._is_excluded(d)]
                for fname in files:
                    if cancel_event and cancel_event.is_set():
                        return
                    fpath = Path(current_root) / fname
                    if fpath.suffix.lower() in target_exts:
                        scanned += 1
                        if progress_cb and scanned % 50 == 0:
                            progress_cb(scanned, str(fpath))
                        yield fpath

    def search(
        self,
        query: str,
        roots: Optional[List[Path]] = None,
        extensions: Optional[Set[str]] = None,
        folder_filter: Optional[str] = None,
        search_content: bool = False,
        max_results: int = 20,
        cancel_event: Optional[threading.Event] = None,
        progress_cb: Optional[Callable[[int, str], None]] = None,
    ) -> List[FileSearchResult]:
        """
        Searches authorized locations by exact name, partial name, extension,
        folder name, or optional document content.
        """
        q_clean = query.strip()
        q_lower = q_clean.lower()
        tokens = [t for t in re.split(r"[\s_\-\.]+", q_lower) if len(t) > 1]
        results: List[FileSearchResult] = []

        for fpath in self.iter_authorized_files(
            roots=roots,
            extensions=extensions,
            cancel_event=cancel_event,
            progress_cb=progress_cb,
        ):
            if folder_filter and folder_filter.lower() not in str(fpath.parent).lower():
                continue

            name_lower = fpath.name.lower()
            stem_lower = fpath.stem.lower()
            folder_lower = str(fpath.parent).lower()
            score = 0.0
            match_type = ""
            snippet = ""

            if q_lower and (q_lower == name_lower or q_lower == stem_lower):
                score = 100.0
                match_type = "exact_name"
            elif q_lower and q_lower in name_lower:
                score = 80.0
                match_type = "partial_name"
            elif tokens and all(t in name_lower for t in tokens):
                score = 70.0
                match_type = "nl_description"
            elif tokens and any(t in name_lower for t in tokens):
                matched_count = sum(1 for t in tokens if t in name_lower)
                score = 30.0 + (30.0 * matched_count / len(tokens))
                match_type = "partial_name"
            elif tokens and any(t in folder_lower for t in tokens):
                score = 25.0
                match_type = "folder"
            elif not q_clean and extensions:
                score = 50.0
                match_type = "extension"

            if score == 0.0 and search_content and q_lower:
                snippet = self._quick_content_match(fpath, q_lower, tokens)
                if snippet:
                    score = 60.0
                    match_type = "content"

            if score > 0.0:
                try:
                    st = fpath.stat()
                    results.append(
                        FileSearchResult(
                            path=fpath,
                            filename=fpath.name,
                            extension=fpath.suffix.lower(),
                            folder=str(fpath.parent),
                            size_bytes=st.st_size,
                            modified_time=st.st_mtime,
                            match_type=match_type,
                            score=score,
                            matched_snippet=snippet,
                        )
                    )
                except OSError:
                    continue

        results.sort(key=lambda r: (r.score, r.modified_time), reverse=True)
        return results[:max_results]

    @staticmethod
    def _quick_content_match(fpath: Path, q_lower: str, tokens: List[str]) -> str:
        """Lightweight content check for TXT/MD/CSV/PDF/DOCX."""
        ext = fpath.suffix.lower()
        try:
            if ext in {".txt", ".md", ".csv"}:
                text = fpath.read_text(encoding="utf-8", errors="ignore")[:50000]
                idx = text.lower().find(q_lower)
                if idx != -1:
                    return text[max(0, idx - 40): idx + 120].replace("\n", " ")
            elif ext == ".pdf":
                import fitz
                with fitz.open(str(fpath)) as doc:
                    for page in doc[:5]:
                        t = page.get_text("text") or ""
                        idx = t.lower().find(q_lower)
                        if idx != -1:
                            return t[max(0, idx - 40): idx + 120].replace("\n", " ")
            elif ext == ".docx":
                import docx
                d = docx.Document(str(fpath))
                full = "\n".join(p.text for p in d.paragraphs)
                idx = full.lower().find(q_lower)
                if idx != -1:
                    return full[max(0, idx - 40): idx + 120].replace("\n", " ")
        except Exception:
            pass
        return ""
