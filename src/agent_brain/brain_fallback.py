"""
VoiceMate Laptop Agent - LangGraph Brain Fallback Orchestrator.
Zero-crash fallback engine executing turns via CommandProcessor when graph runtime is unavailable.
"""
import logging
from typing import Dict, Any
from ..command_processor import CommandProcessor

logger = logging.getLogger("VoiceMate.AgentBrain.Fallback")

class BrainFallbackOrchestrator:
    """Emulates multi-agent orchestration locally without dependency on graph execution."""

    @classmethod
    def execute_fallback_turn(cls, query: str) -> Dict[str, Any]:
        """Resolves turn directly through CommandProcessor and returns typed response dict."""
        logger.info(f"Executing BrainFallbackOrchestrator for query: '{query}'")
        res = CommandProcessor.process_command(query)
        action_type = res.split("|", 1)[0] if "|" in res else "direct"
        return {
            "success": True,
            "fallback": True,
            "query": query,
            "intent": action_type,
            "next_worker": "fallback_worker",
            "final_reply": res,
            "requires_confirmation": False,
            "worker_results": {"fallback": res},
            "total_messages": 1,
            "thread_id": "fallback_thread"
        }
