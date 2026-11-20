"""
VoiceMate Laptop Agent - LangGraph Unified AgentState Schema.
Typed state dictionary governing multi-actor conversation, context propagation,
and cyclic transitions between the supervisor and specialized workers.
"""
from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    """
    Unified multi-agent state dictionary.
    Propagates conversational turns, intent classifications, worker results,
    and cyclic error corrections across the LangGraph graph.
    """
    # Conversational History with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]

    # Current Turn Input
    query: str

    # Classified Intent and Selected Worker
    intent: str
    next_worker: str

    # Shared Inter-Worker Memory / Results
    worker_results: Dict[str, Any]

    # Synthesized Spoken / Written Response
    final_reply: str

    # Human-In-The-Loop Safety Guardrails
    requires_confirmation: bool
    user_confirmed: bool

    # Cyclic Execution & Self-Correction
    retry_count: int
    error: Optional[str]
