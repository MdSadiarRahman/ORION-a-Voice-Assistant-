"""
Fallback Multimodal Document Parser for Docling.
Provides high-fidelity text extraction, table extraction, and hierarchical RAG chunking
using PyMuPDF, markdown, and standard Python parsers when Docling ML models are offline.
"""
import csv
import re
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import DOCLING_OUTPUT_DIR


class DoclingFallbackParser:
    """
    Fallback parser providing universal document reading and semantic chunking.
    """

    @classmethod
    def convert_document(cls, filepath: Path) -> Dict[str, Any]:
        """Converts document to structured markdown and extracts tables."""
        p = Path(filepath)
        if not p.exists():
            return {
                "success": False,
                "file": str(p),
                "error": "File not found",
                "message": f"ফাইলটি পাওয়া যায়নি: {p.name}"
            }

        ext = p.suffix.lower()
        markdown_text = ""
        tables: List[Dict[str, Any]] = []

        # 1. PDF Conversion via PyMuPDF if available
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(p))
                pages_md = []
                for i, page in enumerate(doc):
                    text = page.get_text()
                    pages_md.append(f"## Page {i + 1}\n\n{text}")
                    # Try finding tables
                    try:
                        tabs = page.find_tables()
                        for tab in tabs:
                            tables.append({
                                "page": i + 1,
                                "markdown": tab.to_markdown(),
                                "rows": len(tab.extract())
                            })
                    except Exception:
                        pass
                markdown_text = "\n\n".join(pages_md)
            except Exception as e:
                markdown_text = f"PDF রিডিং ফলব্যাক ত্রুটি: {str(e)}"

        # 2. Text / Markdown / HTML / CSV
        elif ext in [".txt", ".md", ".html"]:
            markdown_text = p.read_text(encoding="utf-8", errors="replace")
            # Detect markdown tables
            table_matches = re.findall(r"(\|.+?\|\n\|[-:| ]+\|\n(?:\|.+?\|\n?)+)", markdown_text)
            for idx, tab_str in enumerate(table_matches):
                tables.append({"table_id": idx + 1, "markdown": tab_str.strip()})

        elif ext == ".csv":
            try:
                rows = []
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    for r in reader:
                        rows.append(r)
                if rows:
                    header = " | ".join(rows[0])
                    sep = " | ".join(["---"] * len(rows[0]))
                    data_rows = [" | ".join(r) for r in rows[1:]]
                    md_table = f"| {header} |\n| {sep} |\n" + "\n".join(f"| {r} |" for r in data_rows)
                    markdown_text = f"# {p.name}\n\n{md_table}"
                    tables.append({"table_id": 1, "markdown": md_table, "rows": len(rows)})
            except Exception as e:
                markdown_text = f"CSV রিডিং ত্রুটি: {str(e)}"

        else:
            # General file read
            try:
                markdown_text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                markdown_text = f"ফাইল '{p.name}' ওপেন করা হয়েছে। পূর্ণাঙ্গ ডকলিং পার্সারের জন্য: pip install docling docling-core"

        # Generate summary
        first_lines = [l.strip() for l in markdown_text.splitlines() if l.strip() and not l.startswith("|")][:4]
        summary = " ".join(first_lines)[:350]

        return {
            "success": True,
            "file": str(p),
            "file_name": p.name,
            "markdown": markdown_text,
            "tables": tables,
            "tables_count": len(tables),
            "summary": summary,
            "driver": "fallback_parser",
            "message": f"ডকুমেন্ট '{p.name}' সফলভাবে পড়া হয়েছে ({len(tables)}টি টেবিল শনাক্ত):\n{summary}"
        }

    @classmethod
    def semantic_chunk(cls, markdown_text: str, max_tokens: int = 512) -> List[Dict[str, Any]]:
        """
        Hierarchical semantic chunker preserving headings context (Pattern C).
        """
        lines = markdown_text.splitlines()
        chunks = []
        current_headings = []
        current_chunk_lines = []

        heading_re = re.compile(r"^(#{1,6})\s+(.+)$")

        for line in lines:
            h_match = heading_re.match(line)
            if h_match:
                # Flush previous chunk if non-empty
                if current_chunk_lines:
                    text_chunk = "\n".join(current_chunk_lines).strip()
                    if text_chunk:
                        chunks.append({
                            "headings": list(current_headings),
                            "text": text_chunk,
                            "token_estimate": len(text_chunk.split())
                        })
                    current_chunk_lines = []

                level = len(h_match.group(1))
                h_text = h_match.group(2).strip()
                # Maintain heading stack
                current_headings = current_headings[:level - 1] + [h_text]

            current_chunk_lines.append(line)

            # If chunk is exceeding max token estimate (approx 1 token ~ 0.75 words)
            if len(" ".join(current_chunk_lines).split()) >= max_tokens:
                text_chunk = "\n".join(current_chunk_lines).strip()
                chunks.append({
                    "headings": list(current_headings),
                    "text": text_chunk,
                    "token_estimate": len(text_chunk.split())
                })
                current_chunk_lines = []

        if current_chunk_lines:
            text_chunk = "\n".join(current_chunk_lines).strip()
            if text_chunk:
                chunks.append({
                    "headings": list(current_headings),
                    "text": text_chunk,
                    "token_estimate": len(text_chunk.split())
                })

        return chunks
