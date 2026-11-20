"""
VoiceMate Laptop Agent - Enterprise Workflow Automation Worker Node.
Executes multi-step automations, webhook triggers, and SaaS integrations via n8n.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState

logger = logging.getLogger("VoiceMate.AgentBrain.AutomationWorker")

def automation_worker(state: AgentState) -> dict:
    """
    Triggers n8n enterprise workflow nodes and synchronous webhook replies.
    """
    query = state.get("query", "")
    logger.info(f"AutomationWorker executing: '{query}'")

    try:
        from ...n8n_agent.n8n_task_runner import N8nTaskRunner
        result = N8nTaskRunner._parse_and_execute(query)
        msg = result.get("message", "এনএইটেন অটোমেশন ফ্লো সফলভাবে পরিচালিত হয়েছে।")

        return {
            "final_reply": msg,
            "worker_results": {"automation": result},
            "messages": [AIMessage(content=msg)],
            "error": None
        }

    except Exception as e:
        logger.error(f"AutomationWorker error: {e}")
        return {
            "error": str(e),
            "final_reply": f"এনএইটেন অটোমেশন পরিচালনায় সমস্যা হয়েছে: {e}"
        }
