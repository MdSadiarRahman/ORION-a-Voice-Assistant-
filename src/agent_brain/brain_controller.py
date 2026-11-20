"""
VoiceMate Laptop Agent - LangGraph Brain Controller.
Coordinates graph invocations, manages multi-turn conversational checkpointing (thread_id),
and surfaces conversation history and memory resets.
"""
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, BaseMessage
from .brain_config import DEFAULT_SESSION_ID, get_brain_settings
from .graph_builder import build_voicemate_graph

logger = logging.getLogger("VoiceMate.AgentBrain.Controller")

class LangGraphBrainController:
    """Master controller managing the VoiceMate LangGraph brain and checkpoint state."""
    _compiled_graph = None
    _session_id: str = DEFAULT_SESSION_ID

    @classmethod
    def get_graph(cls):
        """Lazily builds and caches the compiled StateGraph."""
        if cls._compiled_graph is None:
            cls._compiled_graph = build_voicemate_graph()
        return cls._compiled_graph

    @classmethod
    def execute_turn(cls, query: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a single conversational or automated turn through the LangGraph brain.
        Maintains persistent memory keyed by thread_id.
        """
        session_key = thread_id or cls._session_id
        graph = cls.get_graph()

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "retry_count": 0,
            "error": None
        }

        config = {"configurable": {"thread_id": session_key}}
        logger.info(f"Invoking LangGraph turn for thread '{session_key}': '{query}'")

        try:
            output_state = graph.invoke(initial_state, config=config)
            final_reply = output_state.get("final_reply") or "আমি বিষয়টি সম্পন্ন করেছি।"
            return {
                "success": True,
                "query": query,
                "intent": output_state.get("intent", "conversation"),
                "next_worker": output_state.get("next_worker", "conversation_worker"),
                "final_reply": final_reply,
                "requires_confirmation": output_state.get("requires_confirmation", False),
                "worker_results": output_state.get("worker_results", {}),
                "total_messages": len(output_state.get("messages", [])),
                "thread_id": session_key
            }
        except Exception as e:
            logger.error(f"LangGraph execution error: {e}")
            from .brain_fallback import BrainFallbackOrchestrator
            return BrainFallbackOrchestrator.execute_fallback_turn(query)

    @classmethod
    def get_history(cls, thread_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Retrieves conversational messages stored in the session checkpoint."""
        session_key = thread_id or cls._session_id
        graph = cls.get_graph()
        config = {"configurable": {"thread_id": session_key}}
        history = []
        try:
            state = graph.get_state(config)
            if state and state.values and "messages" in state.values:
                for msg in state.values["messages"]:
                    history.append({
                        "type": msg.__class__.__name__,
                        "content": str(msg.content)
                    })
        except Exception as e:
            logger.warning(f"Could not load checkpoint history: {e}")
        return history

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns metadata regarding the LangGraph Brain system."""
        settings = get_brain_settings()
        settings["graph_compiled"] = cls._compiled_graph is not None
        settings["current_thread_id"] = cls._session_id
        settings["nodes"] = [
            "supervisor", "browser_worker", "document_worker",
            "coding_worker", "automation_worker", "system_worker", "conversation_worker"
        ]
        return settings
