"""
VoiceMate Laptop Agent - PyMuPDF Core Document Engine.
Implements high-speed text extraction, structure-aware markdown,
tabular data extraction, and page rasterization using PyMuPDF.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from config import CAPTURES_DIR, DOCUMENT_RENDER_DPI, DOCUMENT_MAX_VOICE_CHARS
from src.document_agent.document_config import is_pymupdf_available

logger = logging.getLogger(__name__)

def _get_mupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        import fitz
        return fitz

class PyMuPDFReader:
    """
    High-performance Document Reader & Analyzer powered by PyMuPDF.
    """

    @classmethod
    def is_available(cls) -> bool:
        return is_pymupdf_available()

    @classmethod
    def extract_text_and_markdown(cls, file_path: str) -> Dict[str, Any]:
        """
        Pattern A: Extracts clean plain text (for TTS voice reading)
        and structure-aware Markdown (for LLM ingestion / RAG).
        """
        if not cls.is_available():
            raise RuntimeError("PyMuPDF library is not installed in the current environment.")

        pymupdf = _get_mupdf()
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Document not found at {path}")

        full_text_pages = []
        markdown_pages = []
        page_count = 0
        doc_metadata = {}

        with pymupdf.open(str(path)) as doc:
            page_count = len(doc)
            doc_metadata = doc.metadata or {}

            # Check if document has to_markdown capability
            has_doc_md = hasattr(doc, "to_markdown")

            for page_num, page in enumerate(doc):
                # Plain text extraction
                page_text = page.get_text() or ""
                full_text_pages.append(f"--- Page {page_num + 1} ---\n{page_text}")

                # Structure-aware markdown extraction
                try:
                    if hasattr(page, "get_text"):
                        md_page = page.get_text("markdown")
                        markdown_pages.append(md_page)
                    else:
                        markdown_pages.append(page_text)
                except Exception:
                    markdown_pages.append(page_text)

            if has_doc_md and not markdown_pages:
                try:
                    doc_markdown = doc.to_markdown()
                except Exception:
                    doc_markdown = "\n\n".join(markdown_pages)
            else:
                doc_markdown = "\n\n".join(markdown_pages)

        full_text = "\n\n".join(full_text_pages)

        return {
            "file_name": path.name,
            "page_count": page_count,
            "metadata": doc_metadata,
            "plain_text": full_text,
            "markdown": doc_markdown
        }

    @classmethod
    def extract_tables(cls, file_path: str) -> List[Dict[str, Any]]:
        """
        Pattern B: Tabular data extraction using page.find_tables().
        Extracts tables into markdown and header/row structures.
        """
        if not cls.is_available():
            raise RuntimeError("PyMuPDF library is not installed in the current environment.")

        pymupdf = _get_mupdf()
        path = Path(file_path).resolve()
        extracted_tables = []

        with pymupdf.open(str(path)) as doc:
            for page_num, page in enumerate(doc):
                try:
                    tabs = page.find_tables()
                    for idx, table in enumerate(tabs):
                        table_md = ""
                        try:
                            table_md = table.to_markdown()
                        except Exception:
                            # Fallback row assembly
                            table_md = str(table.extract())

                        extracted_tables.append({
                            "page": page_num + 1,
                            "table_index": idx + 1,
                            "headers": getattr(table, "header", []),
                            "markdown": table_md,
                            "rows": table.extract()
                        })
                except Exception as e:
                    logger.debug(f"No tables on page {page_num + 1}: {e}")

        return extracted_tables

    @classmethod
    def render_page_preview(cls, file_path: str, page_number: int = 0, dpi: int = DOCUMENT_RENDER_DPI) -> str:
        """
        Pattern C: Page rasterization to image (PNG/JPEG) for GUI preview or Vision AI.
        Saves output in captures/ directory and returns the image path.
        """
        if not cls.is_available():
            raise RuntimeError("PyMuPDF library is not installed in the current environment.")

        pymupdf = _get_mupdf()
        path = Path(file_path).resolve()
        CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        out_image_path = str(CAPTURES_DIR / f"{path.stem}_page_{page_number + 1}.png")

        with pymupdf.open(str(path)) as doc:
            if page_number < 0 or page_number >= len(doc):
                raise IndexError(f"Page index {page_number} out of range (Total pages: {len(doc)})")
            
            page = doc[page_number]
            pix = page.get_pixmap(dpi=dpi)
            pix.save(out_image_path)

        return out_image_path

    @classmethod
    def ocr_scanned_page(cls, file_path: str, page_number: int = 0, language: str = "eng") -> str:
        """
        Pattern D: OCR on scanned document page.
        """
        if not cls.is_available():
            raise RuntimeError("PyMuPDF library is not installed in the current environment.")

        pymupdf = _get_mupdf()
        path = Path(file_path).resolve()

        with pymupdf.open(str(path)) as doc:
            if page_number < 0 or page_number >= len(doc):
                return ""
            page = doc[page_number]
            try:
                textpage = page.get_textpage_ocr(language=language)
                return textpage.extractText()
            except Exception as e:
                logger.warning(f"PyMuPDF native OCR error (Tesseract required): {e}")
                return page.get_text()

    @classmethod
    def get_document_summary_for_voice(cls, file_path: str) -> str:
        """
        Reads document (including OCR fallback on scanned PDFs) and generates a
        concise Bengali summary tailored for VoiceMate's Text-to-Speech (TTS) engine.
        """
        data = cls.extract_text_and_markdown(file_path)
        file_name = data["file_name"]
        pages = data["page_count"]
        text = data["plain_text"].strip()

        # Scanned PDF OCR fallback if extracted plain text has almost no content
        import re as _re
        meaningful = _re.sub(r"---\s*Page\s*\d+\s*---|\s+", "", text)
        if len(meaningful) < 40 and pages > 0:
            ocr_chunks = []
            for p_idx in range(min(pages, 2)):
                ocr_txt = cls.ocr_scanned_page(file_path, page_number=p_idx)
                if not ocr_txt or not ocr_txt.strip():
                    try:
                        from src.helpers.vision_helper import VisionHelper
                        img_p = cls.render_page_preview(file_path, page_number=p_idx)
                        ocr_txt = VisionHelper.recognize_text(img_p)
                        if "খুঁজে পাওয়া যায়নি" in ocr_txt:
                            ocr_txt = ""
                    except Exception:
                        ocr_txt = ""
                if ocr_txt and ocr_txt.strip():
                    ocr_chunks.append(ocr_txt.strip())
            if ocr_chunks:
                text = "\n\n".join(ocr_chunks)

        # Try AI summarization (Gemini REST / Ollama) when available
        meaningful_after = _re.sub(r"---\s*Page\s*\d+\s*---|\s+", "", text)
        if len(meaningful_after) >= 60:
            try:
                from src.intelligence.gemini_client import GeminiClient
                gc = GeminiClient(timeout_seconds=10.0)
                if gc.is_available():
                    ai_sum = gc.generate_text(
                        prompt=f"Document '{file_name}' ({pages} pages):\n{text[:6000]}\n\nSummarize the key points in 2-3 clear Bengali sentences for voice playback:",
                        system_prompt="You summarize documents concisely and accurately in Bengali for spoken output.",
                        temperature=0.2,
                    )
                    if ai_sum:
                        return f"ডকুমেন্ট '{file_name}' ({pages} পৃষ্ঠা) পড়া হয়েছে। সারসংক্ষেপ: {ai_sum}"
            except Exception:
                pass

        # Deterministic preview fallback
        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 30 and not line.strip().startswith("--- Page")]
        summary_preview = " ".join(lines[:6])

        if len(summary_preview) > DOCUMENT_MAX_VOICE_CHARS:
            summary_preview = summary_preview[:DOCUMENT_MAX_VOICE_CHARS] + "..."

        if not summary_preview:
            summary_preview = "ডকুমেন্টটিতে কোনো টেক্সট পাওয়া যায়নি অথবা এটি স্ক্যান করা ইমেজ।"

        return (
            f"ডকুমেন্ট '{file_name}' সফলভাবে পড়া হয়েছে। এতে মোট {pages} টি পৃষ্ঠা রয়েছে। "
            f"ডকুমেন্টের মূল বিষয়বস্তু হলো: {summary_preview}"
        )
