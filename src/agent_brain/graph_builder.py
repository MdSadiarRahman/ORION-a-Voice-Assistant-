"""
VoiceMate Laptop Agent - LangGraph StateGraph Builder.
Constructs the multi-agent cyclic graph linking the Supervisor and all specialized workers,
with persistent checkpointing and self-correcting error routing.
"""
import logging
from typing import Optional, Dict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from .state_schema import AgentState
from .brain_config import MAX_CYCLIC_RETRIES, ENABLE_CYCLIC_SELF_CORRECTION
from .workers import (
    supervisor_node,
    browser_worker,
    document_worker,
    coding_worker,
    automation_worker,
    system_worker,
    conversation_worker
)

logger = logging.getLogger("VoiceMate.AgentBrain.GraphBuilder")

def route_supervisor(state: AgentState) -> str:
    """Routes execution from supervisor to the chosen specialized worker node."""
    target = state.get("next_worker", "conversation_worker")
    valid_targets = {
        "browser_worker", "document_worker", "coding_worker",
        "automation_worker", "system_worker", "conversation_worker"
    }
    if target in valid_targets:
        return target
    return "conversation_worker"

def route_worker_completion(state: AgentState) -> str:
    """
    Evaluates cyclic resilience: if an error occurred and retry budget remains,
    routes back to the supervisor for dynamic self-correction; otherwise terminates at END.
    """
    err = state.get("error")
    retries = state.get("retry_count", 0)
    if err and retries < MAX_CYCLIC_RETRIES and ENABLE_CYCLIC_SELF_CORRECTION:
        logger.info(f"Cyclic self-correction active. Routing error '{err}' back to supervisor (retry {retries}).")
        return "supervisor"
    return END

def build_voicemate_graph(checkpointer=None):
    """
    Constructs, compiles, and returns the unified VoiceMate LangGraph StateGraph.
    """
    builder = StateGraph(AgentState)

    # 1. Register Supervisor and Workers
    builder.add_node("supervisor", supervisor_node)
    builder.add_node("browser_worker", browser_worker)
    builder.add_node("document_worker", document_worker)
    builder.add_node("coding_worker", coding_worker)
    builder.add_node("automation_worker", automation_worker)
    builder.add_node("system_worker", system_worker)
    builder.add_node("conversation_worker", conversation_worker)

    # 2. Flow from Entrypoint to Supervisor
    builder.add_edge(START, "supervisor")

    # 3. Dynamic Conditional Edge from Supervisor to Workers
    builder.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "browser_worker": "browser_worker",
            "document_worker": "document_worker",
            "coding_worker": "coding_worker",
            "automation_worker": "automation_worker",
            "system_worker": "system_worker",
            "conversation_worker": "conversation_worker"
        }
    )

    # 4. Resilience & Terminal Edges from Workers
    worker_nodes = [
        "browser_worker", "document_worker", "coding_worker",
        "automation_worker", "system_worker", "conversation_worker"
    ]
    for w_name in worker_nodes:
        builder.add_conditional_edges(
            w_name,
            route_worker_completion,
            {
                "supervisor": "supervisor",
                END: END
            }
        )

    # 5. Compile with Persistent Checkpointer
    saver = checkpointer if checkpointer is not None else MemorySaver()
    compiled_graph = builder.compile(checkpointer=saver)
    logger.info("VoiceMate unified LangGraph compiled successfully.")
    return compiled_graph
