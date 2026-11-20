"""
Configuration and Environment Discovery for Docling Multimodal Document Intelligence.
Tracks Docling repository path, OCR preferences, table options, and exports.
"""
import sys
from pathlib import Path
from typing import Dict, Any

from config import (
    DOCLING_REPO_DIR,
    DOCLING_OUTPUT_DIR,
    DOCS_DIR,
    DOCLING_ENABLED,
    DOCLING_DO_OCR,
    DOCLING_DO_TABLES,
    DOCLING_CHUNK_MAX_TOKENS,
    DOCLING_SUPPORTED_EXTS,
)

# Ensure docling repo is in sys.path if present
if DOCLING_REPO_DIR.exists() and str(DOCLING_REPO_DIR) not in sys.path:
    sys.path.insert(0, str(DOCLING_REPO_DIR))


def is_docling_installed() -> bool:
    """Checks if Docling and its DocumentConverter are available."""
    try:
        from docling.document_converter import DocumentConverter  # noqa: F401
        return True
    except (ImportError, ModuleNotFoundError, Exception):
        return False


def get_docling_settings() -> Dict[str, Any]:
    """Returns active Docling configuration dictionary."""
    return {
        "repo_path": str(DOCLING_REPO_DIR),
        "repo_exists": DOCLING_REPO_DIR.exists(),
        "is_installed": is_docling_installed(),
        "output_dir": str(DOCLING_OUTPUT_DIR),
        "docs_dir": str(DOCS_DIR),
        "enabled": DOCLING_ENABLED,
        "do_ocr": DOCLING_DO_OCR,
        "do_tables": DOCLING_DO_TABLES,
        "chunk_max_tokens": DOCLING_CHUNK_MAX_TOKENS,
        "supported_extensions": DOCLING_SUPPORTED_EXTS,
    }
