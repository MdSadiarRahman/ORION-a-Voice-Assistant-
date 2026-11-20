"""
VoiceMate Laptop Agent - Document Task Runner.
Executes document extraction and summarization jobs in background threads,
sending real-time output to VoiceMate's voice engine and GUI logs.
"""
import os
import threading
from pathlib import Path
from typing import Optional, Callable
from config import DOCS_DIR
from src.document_agent.pymupdf_reader import PyMuPDFReader
from src.document_agent.document_fallback import DocumentFallbackReader

class DocumentTaskRunner:
    @classmethod
    def resolve_document_path(cls, query_or_path: str) -> Optional[Path]:
        """
        Attempts to resolve document by exact path, relative path,
        or scanning documents/ and Downloads folders for matching filenames.
        """
        raw_path = query_or_path.strip().strip('"').strip("'")
        p = Path(raw_path)
        if p.exists() and p.is_file():
            return p

        # Check in DOCS_DIR
        in_docs = DOCS_DIR / raw_path
        if in_docs.exists() and in_docs.is_file():
            return in_docs

        # Search in DOCS_DIR by partial match
        if DOCS_DIR.exists():
            for f in DOCS_DIR.glob("*.*"):
                if raw_path.lower() in f.name.lower():
                    return f

        # Search in User's Downloads folder
        downloads = Path(os.path.expanduser("~/Downloads"))
        if downloads.exists():
            for f in downloads.glob("*.*"):
                if raw_path.lower() in f.name.lower() and f.suffix in [".pdf", ".docx", ".txt", ".md"]:
                    return f

        # Fallback to the latest modified file in DOCS_DIR if any exists
        if DOCS_DIR.exists():
            files = sorted(DOCS_DIR.glob("*.*"), key=lambda x: x.stat().st_mtime, reverse=True)
            if files:
                return files[0]

        return None

    @classmethod
    def run_document_task(
        cls,
        document_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """
        Runs document processing asynchronously.
        """
        def _worker():
            if on_progress:
                on_progress(f"ডকুমেন্ট খোঁজা হচ্ছে: {document_query}...")

            doc_path = cls.resolve_document_path(document_query)
            if not doc_path:
                msg = f"দুঃখিত, '{document_query}' নামে কোনো ফাইল খুঁজে পাওয়া যায়নি। দয়া করে ফাইলের সঠিক পাথ উল্লেখ করুন।"
                if on_finish:
                    on_finish(msg)
                return

            if on_progress:
                on_progress(f"ডকুমেন্ট পড়া হচ্ছে: {doc_path.name}...")

            if PyMuPDFReader.is_available() and doc_path.suffix.lower() in [".pdf", ".xps", ".epub"]:
                try:
                    summary = PyMuPDFReader.get_document_summary_for_voice(str(doc_path))
                    # Also try extracting tables to note if any exist
                    tables = PyMuPDFReader.extract_tables(str(doc_path))
                    if tables:
                        summary += f" এতে মোট {len(tables)} টি টেবিল বা ছক রয়েছে।"
                except Exception as e:
                    fallback = DocumentFallbackReader.read_text_document(str(doc_path))
                    summary = fallback.get("summary", str(e))
            else:
                fallback = DocumentFallbackReader.read_text_document(str(doc_path))
                summary = fallback.get("summary", "ডকুমেন্ট পড়া সম্পন্ন হয়েছে।")

            if on_finish:
                on_finish(summary)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
