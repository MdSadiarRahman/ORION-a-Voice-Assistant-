"""
VoiceMate Laptop Agent - Document Intelligence Subsystem.
Powered by PyMuPDF (Ultra-fast PDF/Document Extraction, Markdown, Tables & Rendering).
"""
from src.document_agent.pymupdf_reader import PyMuPDFReader
from src.document_agent.document_task_runner import DocumentTaskRunner

__all__ = ["PyMuPDFReader", "DocumentTaskRunner"]
