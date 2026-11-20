"""
Docling Multimodal Document Intelligence Subsystem for VoiceMate.
Provides universal document parsing (PDF, Office, HTML, CSV),
Deep Layout Analysis, TableFormer extraction, and Hybrid RAG chunking.
"""
from src.docling_agent.docling_config import get_docling_settings, is_docling_installed
from src.docling_agent.docling_converter import DoclingConverter
from src.docling_agent.docling_chunker import DoclingHybridChunker
from src.docling_agent.docling_fallback import DoclingFallbackParser
from src.docling_agent.docling_task_runner import DoclingTaskRunner

__all__ = [
    "get_docling_settings",
    "is_docling_installed",
    "DoclingConverter",
    "DoclingHybridChunker",
    "DoclingFallbackParser",
    "DoclingTaskRunner",
]
