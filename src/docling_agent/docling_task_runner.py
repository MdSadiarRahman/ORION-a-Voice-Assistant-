"""
Background Task Runner for Docling Multimodal Document Intelligence.
Dispatches document conversion, table extraction, and RAG chunking
in worker threads with progress and voice callbacks.
"""
import re
import threading
from pathlib import Path
from typing import Callable, Optional, Dict, Any

from config import DOCS_DIR
from src.docling_agent.docling_converter import DoclingConverter


class DoclingTaskRunner:
    """
    Manages non-blocking execution of Docling multimodal document tasks.
    """

    @classmethod
    def run_task(
        cls,
        task_query: str,
        on_progress: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[str], None]] = None
    ) -> threading.Thread:
        """Runs Docling document task in a background daemon thread."""
        def _worker():
            try:
                if on_progress:
                    on_progress("📑 ডকলিং মাল্টিমোডাল ডকুমেন্ট পার্সার শুরু হচ্ছে...")

                result = cls._parse_and_execute(task_query, on_progress)
                msg = result.get("message", "ডকুমেন্ট প্রসেসিং সম্পন্ন হয়েছে।")

                if on_finish:
                    on_finish(msg)
            except Exception as e:
                err_msg = f"ডকলিং টাস্কে ত্রুটি: {str(e)}"
                if on_finish:
                    on_finish(err_msg)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    @classmethod
    def _parse_and_execute(
        cls,
        query: str,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Interprets document queries into specific Docling actions."""
        q = query.strip()

        # 1. Extract target filename
        file_match = re.search(r'([\w\s.-]+\.(?:pdf|docx|pptx|xlsx|html|epub|csv|txt|md))', q, re.IGNORECASE)
        filename = file_match.group(1).strip() if file_match else ""

        # If no explicit filename found, search in documents/ directory
        if not filename:
            docs = list(DOCS_DIR.glob("*.*"))
            if docs:
                filename = docs[0].name
            else:
                filename = "sample.md"

        if on_progress:
            on_progress(f"🔍 ডকুমেন্ট '{filename}' বিশ্লেষণ করা হচ্ছে...")

        res = DoclingConverter.convert_file(filename)

        # If user specifically asked for tables
        if any(w in q.lower() for w in ["টেবিল", "table", "ছক"]):
            tables = res.get("tables", [])
            if tables:
                table_md = "\n\n".join(t.get("markdown", "") for t in tables[:3])
                msg = f"'{filename}' ফাইলে {len(tables)}টি টেবিল পাওয়া গেছে:\n{table_md}"
            else:
                msg = f"'{filename}' ফাইলে কোনো টেবিল পাওয়া যায়নি।"
            return {"success": True, "message": msg, "tables": tables}

        # If user specifically asked for chunks / RAG
        if any(w in q.lower() for w in ["চাংক", "chunk", "rag", "সেগমেন্ট"]):
            chunks = res.get("chunks", [])
            msg = f"'{filename}' থেকে {len(chunks)}টি সেমান্টিক চাংক তৈরি করা হয়েছে।"
            return {"success": True, "message": msg, "chunks": chunks}

        # Default: Full conversion summary
        return res
