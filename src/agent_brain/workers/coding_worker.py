"""
VoiceMate Laptop Agent - AI Pair Programming & Developer Worker Node.
Executes code edits (SEARCH/REPLACE blocks), AST RepoMap generation, Git commits,
and OpenHands Developer Canvas audits.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState

logger = logging.getLogger("VoiceMate.AgentBrain.CodingWorker")

def coding_worker(state: AgentState) -> dict:
    """
    Executes code editing, repo mapping, and development audits via Aider and OpenHands.
    """
    query = state.get("query", "")
    logger.info(f"CodingWorker executing: '{query}'")

    try:
        query_lower = query.lower()
        # OpenHands Canvas audits, git status, file tree
        if any(w in query_lower for w in ["ক্যানভাস", "canvas", "ওপেনহ্যান্ডস", "openhands", "অডিট", "audit", "গিট স্ট্যাটাস", "ফাইল ট্রি", "টার্মিনাল"]):
            from ...canvas_agent.canvas_fallback import CanvasFallbackHandler
            result = CanvasFallbackHandler.execute_local_action(query)
            msg = result.get("message", "ডেভেলপার ক্যানভাস অ্যাকশন সম্পন্ন হয়েছে।")
        else:
            # Aider code editor, repo map, rollback, patch
            from ...coder_agent.coder_fallback import CoderFallbackReader
            result = CoderFallbackReader.execute_local_action(query)
            msg = result.get("message", "এআই কোডার অপারেশন সম্পন্ন হয়েছে।")

        return {
            "final_reply": msg,
            "worker_results": {"coding": result},
            "messages": [AIMessage(content=msg)],
            "error": None
        }

    except Exception as e:
        logger.error(f"CodingWorker error: {e}")
        return {
            "error": str(e),
            "final_reply": f"কোডিং অপারেশনে ত্রুটি হয়েছে: {e}"
        }
