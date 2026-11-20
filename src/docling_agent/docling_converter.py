"""
Universal Multimodal Document Converter for VoiceMate.
Implements Docling Patterns A & B:
- Pattern A: Basic Universal Conversion (PDF, DOCX, PPTX, XLSX, Markdown)
- Pattern B: Advanced Pipeline (OCR + Deep Layout Analysis + TableFormer)
"""
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import (
    DOCLING_OUTPUT_DIR,
    DOCLING_DO_OCR,
    DOCLING_DO_TABLES,
    DOCS_DIR,
)
from src.docling_agent.docling_config import is_docling_installed
from src.docling_agent.docling_fallback import DoclingFallbackParser
from src.docling_agent.docling_chunker import DoclingHybridChunker


class DoclingConverter:
    """
    Orchestrates universal document conversion, table extraction, and markdown export.
    """

    @classmethod
    def resolve_file_path(cls, filename_or_path: str) -> Optional[Path]:
        """Resolves path against absolute path, DOCS_DIR, or current directory."""
        raw = Path(filename_or_path.strip().strip("'\"`"))
        if raw.is_absolute() and raw.exists():
            return raw

        in_docs = DOCS_DIR / raw.name
        if in_docs.exists():
            return in_docs

        if raw.exists():
            return raw.resolve()

        return None

    @classmethod
    def convert_file(
        cls,
        filepath_str: str,
        do_ocr: Optional[bool] = None,
        do_tables: Optional[bool] = None,
        export_chunks: bool = True
    ) -> Dict[str, Any]:
        """
        Pattern A & B: Converts document into structured Markdown, extracts tables,
        and optionally produces RAG semantic chunks.
        """
        path = cls.resolve_file_path(filepath_str)
        if not path:
            return {
                "success": False,
                "error": f"File not found: {filepath_str}",
                "message": f"ডকুমেন্ট ফাইলটি পাওয়া যায়নি: {filepath_str}"
            }

        # Check if full Docling ML engine is available
        if is_docling_installed():
            try:
                from docling.document_converter import DocumentConverter, PdfFormatOption
                from docling.datamodel.pipeline_options import PdfPipelineOptions
                from docling.datamodel.base_models import InputFormat

                ocr_enabled = do_ocr if do_ocr is not None else DOCLING_DO_OCR
                tab_enabled = do_tables if do_tables is not None else DOCLING_DO_TABLES

                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = ocr_enabled
                pipeline_options.do_table_structure = tab_enabled

                converter = DocumentConverter(
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                    }
                )

                result = converter.convert(str(path))
                markdown_text = result.document.export_to_markdown()

                # Extract tables
                tables = []
                for idx, t in enumerate(result.document.tables):
                    try:
                        df = t.export_to_dataframe()
                        tables.append({
                            "table_id": idx + 1,
                            "markdown": df.to_markdown(),
                            "rows": len(df)
                        })
                    except Exception:
                        pass

                # Semantic Chunking (Pattern C)
                chunks = DoclingHybridChunker.chunk(result.document) if export_chunks else []

                # Export to disk
                export_path = DOCLING_OUTPUT_DIR / f"{path.stem}_docling.md"
                export_path.write_text(markdown_text, encoding="utf-8")

                first_lines = [l.strip() for l in markdown_text.splitlines() if l.strip()][:3]
                summary = " ".join(first_lines)[:350]

                return {
                    "success": True,
                    "file": str(path),
                    "file_name": path.name,
                    "markdown": markdown_text,
                    "tables": tables,
                    "tables_count": len(tables),
                    "chunks": chunks,
                    "chunks_count": len(chunks),
                    "export_path": str(export_path),
                    "summary": summary,
                    "driver": "docling_ml_pipeline",
                    "message": f"ডকলিং দিয়ে '{path.name}' সফলভাবে কনভার্ট করা হয়েছে ({len(tables)}টি টেবিল, {len(chunks)}টি চাংক):\n{summary}"
                }
            except Exception:
                # Fallback to local multimodal parser
                pass

        # Fallback Execution
        res = DoclingFallbackParser.convert_document(path)
        if res.get("success") and export_chunks:
            chunks = DoclingHybridChunker.chunk(res.get("markdown", ""))
            res["chunks"] = chunks
            res["chunks_count"] = len(chunks)

            # Export markdown
            export_path = DOCLING_OUTPUT_DIR / f"{path.stem}_docling.md"
            export_path.write_text(res.get("markdown", ""), encoding="utf-8")
            res["export_path"] = str(export_path)

        return res

    @classmethod
    def get_document_summary(cls, filepath_str: str) -> str:
        """Convenience method returning concise voice-friendly summary."""
        res = cls.convert_file(filepath_str)
        if not res.get("success"):
            return res.get("message", "ডকুমেন্ট পড়তে ব্যর্থ হয়েছে।")

        tables_info = f" এবং {res.get('tables_count', 0)}টি টেবিল শনাক্ত হয়েছে" if res.get("tables_count", 0) > 0 else ""
        return f"{res.get('file_name')} সফলভাবে পড়া হয়েছে{tables_info}। সারাংশ: {res.get('summary', '')}"
