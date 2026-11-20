"""
VoiceMate Laptop Agent - System & Hardware Worker Node.
Manages laptop battery telemetry, hands-free typing, app launching, dialing,
and FastAPI server lifecycle control.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState
from ...command_processor import CommandProcessor

logger = logging.getLogger("VoiceMate.AgentBrain.SystemWorker")

def system_worker(state: AgentState) -> dict:
    """
    Executes native desktop OS controls, battery monitoring, and API gateway operations.
    """
    query = state.get("query", "")
    logger.info(f"SystemWorker executing: '{query}'")

    try:
        query_lower = query.lower()
        # FastAPI Gateway server actions
        if any(w in query_lower for w in ["এপিআই", "api", "ফাস্টএপিআই", "fastapi", "সোয়েগার", "swagger"]):
            from ...api_gateway.server_controller import APIServerController
            if any(w in query_lower for w in ["বন্ধ", "স্টপ"]):
                res = APIServerController.stop_server()
                msg = res.get("message", "এপিআই সার্ভার বন্ধ করা হয়েছে।")
            elif any(w in query_lower for w in ["স্ট্যাটাস", "অবস্থা", "status"]):
                status = APIServerController.get_status()
                msg = f"এপিআই সার্ভার অবস্থা: {'সক্রিয়' if status['running'] else 'বন্ধ'}, পোর্ট: {status['port']}"
            else:
                res = APIServerController.start_server(open_docs=True)
                msg = res.get("message", "এপিআই সার্ভার চালু হয়েছে।")

            return {
                "final_reply": msg,
                "worker_results": {"system": {"api": msg}},
                "messages": [AIMessage(content=msg)],
                "error": None
            }

        # Native Desktop Controls & Hardware
        result_cmd = CommandProcessor.process_command(query)
        msg = result_cmd

        return {
            "final_reply": msg,
            "worker_results": {"system": {"command_result": result_cmd}},
            "messages": [AIMessage(content=msg)],
            "error": None
        }

    except Exception as e:
        logger.error(f"SystemWorker error: {e}")
        return {
            "error": str(e),
            "final_reply": f"সিস্টেম অ্যাকশনে সমস্যা হয়েছে: {e}"
        }
