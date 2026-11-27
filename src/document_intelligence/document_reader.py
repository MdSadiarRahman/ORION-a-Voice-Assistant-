"""
Phase 2: Document Reader (document_reader.py)
Extracts structured content from PDF, DOCX, XLSX, PPTX, TXT/MD/CSV.
Detects empty, corrupted, encrypted, scanned, or unreadable documents.
Never claims full extraction if only partial content was read.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DocumentContent:
    path: str
    filename: str
    extension: str
    status: str  # "ok", "partial", "empty", "encrypted", "scanned", "corrupted", "unsupported"
    full_text: str = ""
    pages: List[Dict[str, Any]] = field(default_factory=list)
    headings: List[str] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)
    tables: List[List[List[str]]] = field(default_factory=list)
    deadlines: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    error_message: str = ""


class DocumentReader:
    """Multi-format document reader with integrity and status detection."""

    @classmethod
    def read(cls, filepath: str | Path) -> DocumentContent:
        p = Path(filepath)
        if not p.exists() or not p.is_file():
            return DocumentContent(
                path=str(p),
                filename=p.name,
                extension=p.suffix.lower(),
                status="corrupted",
                error_message="File does not exist or is not a regular file.",
            )

        ext = p.suffix.lower()
        if ext == ".pdf":
            doc = cls._read_pdf(p)
        elif ext == ".docx":
            doc = cls._read_docx(p)
        elif ext == ".xlsx":
            doc = cls._read_xlsx(p)
        elif ext == ".pptx":
            doc = cls._read_pptx(p)
        elif ext in {".txt", ".md", ".csv"}:
            doc = cls._read_text(p)
        else:
            return DocumentContent(
                path=str(p),
                filename=p.name,
                extension=ext,
                status="unsupported",
                error_message=f"Unsupported file format: {ext}",
            )

        if doc.full_text.strip():
            cls._extract_structure(doc)
        elif doc.status == "ok":
            doc.status = "empty"

        return doc

    @classmethod
    def _read_pdf(cls, p: Path) -> DocumentContent:
        try:
            import fitz
            with fitz.open(str(p)) as pdf:
                if pdf.is_encrypted:
                    return DocumentContent(
                        path=str(p), filename=p.name, extension=".pdf",
                        status="encrypted", error_message="PDF is password-protected/encrypted."
                    )
                pages = []
                texts = []
                for idx, page in enumerate(pdf, 1):
                    t = page.get_text("text") or ""
                    pages.append({"page_number": idx, "text": t})
                    texts.append(t)
                full_text = "\n\n".join(texts).strip()
                if not full_text and len(pdf) > 0:
                    return DocumentContent(
                        path=str(p), filename=p.name, extension=".pdf",
                        status="scanned", pages=pages,
                        error_message="PDF contains no extractable text (likely scanned images; OCR needed)."
                    )
                return DocumentContent(
                    path=str(p), filename=p.name, extension=".pdf",
                    status="ok", full_text=full_text, pages=pages
                )
        except Exception as e:
            return DocumentContent(
                path=str(p), filename=p.name, extension=".pdf",
                status="corrupted", error_message=str(e)
            )

    @classmethod
    def _read_docx(cls, p: Path) -> DocumentContent:
        try:
            import docx
            d = docx.Document(str(p))
            paras = [para.text for para in d.paragraphs if para.text.strip()]
            headings = [
                para.text.strip() for para in d.paragraphs
                if para.style and "heading" in para.style.name.lower() and para.text.strip()
            ]
            tables = []
            for tbl in d.tables:
                tables.append([[cell.text.strip() for cell in row.cells] for row in tbl.rows])
            return DocumentContent(
                path=str(p), filename=p.name, extension=".docx",
                status="ok", full_text="\n".join(paras), headings=headings, tables=tables
            )
        except Exception as e:
            return DocumentContent(
                path=str(p), filename=p.name, extension=".docx",
                status="corrupted", error_message=str(e)
            )

    @classmethod
    def _read_xlsx(cls, p: Path) -> DocumentContent:
        try:
            import openpyxl
            wb = openpyxl.load_workbook(str(p), data_only=True, read_only=True)
            lines = []
            tables = []
            for sheet in wb.worksheets:
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    str_row = [str(c) if c is not None else "" for c in row]
                    if any(str_row):
                        rows.append(str_row)
                        lines.append(" | ".join(str_row))
                if rows:
                    tables.append(rows)
            return DocumentContent(
                path=str(p), filename=p.name, extension=".xlsx",
                status="ok", full_text="\n".join(lines), tables=tables
            )
        except Exception as e:
            return DocumentContent(
                path=str(p), filename=p.name, extension=".xlsx",
                status="corrupted", error_message=str(e)
            )

    @classmethod
    def _read_pptx(cls, p: Path) -> DocumentContent:
        try:
            from pptx import Presentation
            prs = Presentation(str(p))
            pages = []
            texts = []
            for idx, slide in enumerate(prs.slides, 1):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                joined = "\n".join(slide_text)
                pages.append({"page_number": idx, "text": joined})
                texts.append(joined)
            return DocumentContent(
                path=str(p), filename=p.name, extension=".pptx",
                status="ok", full_text="\n\n".join(texts), pages=pages
            )
        except Exception as e:
            return DocumentContent(
                path=str(p), filename=p.name, extension=".pptx",
                status="corrupted", error_message=str(e)
            )

    @classmethod
    def _read_text(cls, p: Path) -> DocumentContent:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
            return DocumentContent(
                path=str(p), filename=p.name, extension=p.suffix.lower(),
                status="ok", full_text=text
            )
        except Exception as e:
            return DocumentContent(
                path=str(p), filename=p.name, extension=p.suffix.lower(),
                status="corrupted", error_message=str(e)
            )

    @staticmethod
    def _extract_structure(doc: DocumentContent) -> None:
        text = doc.full_text
        # Extract headings if not already populated
        if not doc.headings:
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#") or (len(s) < 80 and s.isupper() and len(s) > 3):
                    doc.headings.append(s.lstrip("# ").strip())

        # Extract numbered questions
        q_matches = re.finditer(
            r"(?im)^(?:Question\s*#?\d+|Q\.?\s*\d+|\d+[\.\)]|প্রশ্ন\s*#?\d+)[:.\s]+(.+?)(?=\n(?:Question\s*#?\d+|Q\.?\s*\d+|\d+[\.\)]|প্রশ্ন\s*#?\d+)|\Z)",
            text,
            re.DOTALL,
        )
        for idx, m in enumerate(q_matches, 1):
            q_text = m.group(1).strip()
            if q_text:
                doc.questions.append({"number": idx, "text": q_text})

        # Extract deadlines
        for line in text.splitlines():
            if re.search(r"(?i)(deadline|due\s*date|submission\s*date|submit\s*by)", line):
                doc.deadlines.append(line.strip())
            if re.search(r"(?i)(instruction|guideline|note:|marks:|total\s*marks)", line):
                doc.instructions.append(line.strip())
