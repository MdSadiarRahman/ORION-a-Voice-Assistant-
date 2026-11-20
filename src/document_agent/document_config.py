"""
Document Intelligence Configuration & Environment Resolver.
Ensures PyMuPDF settings and repo path are properly resolved.
"""
import sys
import os
from pathlib import Path
from config import (
    PYMUPDF_REPO_DIR,
    DOCS_DIR,
    DOCUMENT_RENDER_DPI,
    DOCUMENT_MAX_VOICE_CHARS,
    DOCUMENT_SUPPORTED_EXTS
)

# Register repo path in sys.path
if PYMUPDF_REPO_DIR.exists():
    repo_src = PYMUPDF_REPO_DIR / "src"
    for p in [str(PYMUPDF_REPO_DIR), str(repo_src)]:
        if p not in sys.path:
            sys.path.insert(0, p)

def is_pymupdf_available() -> bool:
    """Checks whether PyMuPDF (pymupdf or fitz) is installed and loadable."""
    try:
        import pymupdf
        return True
    except Exception:
        try:
            import fitz
            return True
        except Exception:
            return False

def get_document_settings() -> dict:
    return {
        "supported_extensions": DOCUMENT_SUPPORTED_EXTS,
        "render_dpi": DOCUMENT_RENDER_DPI,
        "max_voice_chars": DOCUMENT_MAX_VOICE_CHARS,
        "docs_dir": str(DOCS_DIR),
        "repo_path": str(PYMUPDF_REPO_DIR)
    }
