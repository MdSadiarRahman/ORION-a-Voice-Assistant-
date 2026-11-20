"""
Semantic and Hybrid Document Chunker for VoiceMate.
Implements Docling's Pattern C:
Preserves hierarchical headings context, table formatting, and prevents token overflow
for LLM RAG pipelines and assistant long-term memory.
"""
from typing import List, Dict, Any, Union
from pathlib import Path

from src.docling_agent.docling_config import is_docling_installed
from src.docling_agent.docling_fallback import DoclingFallbackParser


class DoclingHybridChunker:
    """
    Chunks multimodal documents into coherent semantic segments with breadcrumb headings.
    """

    @classmethod
    def chunk(
        cls,
        doc_input: Union[str, Any],
        max_tokens: int = 512
    ) -> List[Dict[str, Any]]:
        """
        Chunks a document using Docling's native HybridChunker or hierarchical fallback.
        """
        if is_docling_installed() and not isinstance(doc_input, str):
            try:
                from docling.chunking import HybridChunker
                chunker = HybridChunker(max_tokens=max_tokens)
                chunks_raw = list(chunker.chunk(doc_input))

                results = []
                for ch in chunks_raw:
                    headings = getattr(ch.meta, "headings", [])
                    results.append({
                        "headings": headings,
                        "text": ch.text,
                        "token_estimate": len(ch.text.split()),
                        "driver": "docling_hybrid_chunker"
                    })
                return results
            except Exception:
                pass

        # If doc_input is string (Markdown) or fallback needed
        markdown_str = str(doc_input)
        return DoclingFallbackParser.semantic_chunk(markdown_str, max_tokens=max_tokens)
