"""
VoiceMate Laptop Agent - Conversation & Natural Language Worker Node.
Handles friendly greetings, date & time inquiries, user confirmations, and fallback chat.
"""
import logging
from langchain_core.messages import AIMessage
from ..state_schema import AgentState
from ...command_processor import CommandProcessor

logger = logging.getLogger("VoiceMate.AgentBrain.ConversationWorker")

def conversation_worker(state: AgentState) -> dict:
    """
    Synthesizes natural Bengali replies for conversational queries and confirmation dialogs.
    """
    query = state.get("query", "")
    existing_reply = state.get("final_reply")

    # If supervisor already set a confirmation prompt, preserve it
    if state.get("requires_confirmation") and existing_reply:
        return {
            "final_reply": existing_reply,
            "messages": [AIMessage(content=existing_reply)],
            "error": None
        }

    logger.info(f"ConversationWorker generating response for: '{query}'")

    # Process through CommandProcessor
    reply = CommandProcessor.process_command(query)
    if reply == "UNKNOWN_COMMAND":
        reply = "আমি আপনার কথাটি শুনেছি। বলুন আমি আপনাকে কীভাবে সাহায্য করতে পারি?"

    return {
        "final_reply": reply,
        "worker_results": {"conversation": {"reply": reply}},
        "messages": [AIMessage(content=reply)],
        "error": None
    }
