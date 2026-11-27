"""
VoiceMate Laptop Agent - Document & Multimodal Intelligence Worker Node.
Processes PDFs, Office documents (DOCX, PPTX, XLSX), and multimodal files via Docling and PyMuPDF.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState

logger = logging.getLogger("VoiceMate.AgentBrain.DocumentWorker")

def document_worker(state: AgentState) -> dict:
    """
    Parses and summarizes documents using Docling (Multimodal) and PyMuPDF (Fast PDF).
    """
    query = state.get("query", "")
    logger.info(f"DocumentWorker executing: '{query}'")

    try:
        query_lower = query.lower()
        # Docling multimodal formats or chunking
        if any(w in query_lower for w in ["ডকলিং", "docling", "ওয়ার্ড", "docx", "পাওয়ারপয়েন্ট", "pptx", "এক্সেল", "xlsx", "চাংক"]):
            from ...docling_agent.docling_task_runner import DoclingTaskRunner
            result = DoclingTaskRunner._parse_and_execute(query)
            msg = result.get("message", "ডকলিং দিয়ে ডকুমেন্ট প্রসেসিং সম্পন্ন হয়েছে।")
        else:
            # PyMuPDF fast document reader
            from ...document_agent.document_fallback import DocumentFallbackReader
            result = DocumentFallbackReader.read_document(query)
            msg = result.get("summary", "ডকুমেন্ট পড়া সম্পন্ন হয়েছে।")

        return {
            "final_reply": msg,
            "worker_results": {"document": result},
            "messages": [AIMessage(content=msg)],
            "error": None
        }

    except Exception as e:
        logger.error(f"DocumentWorker error: {e}")
        return {
            "error": str(e),
            "final_reply": f"ডকুমেন্ট প্রসেসিংয়ে ত্রুটি হয়েছে: {e}"
        }
