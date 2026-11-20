"""
VoiceMate Laptop Agent - Voice Command API Router.
Handles command processing, action resolution, and background automation dispatching.
"""
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..schemas import CommandRequest, CommandResponse, SpeakRequest
from ...command_processor import CommandProcessor
from ...helpers.tts_helper import TTSHelper

logger = logging.getLogger("VoiceMate.APIGateway.Voice")
router = APIRouter(prefix="/api", tags=["Voice & Commands"])

def _dispatch_heavy_task(action_str: str, command_text: str):
    """Executes heavy agent tasks in the background without blocking API responses."""
    try:
        if action_str.startswith("ACTION_BROWSER_TASK|"):
            from ...browser_agent.browser_task_runner import BrowserTaskRunner
            task = action_str.split("|", 1)[1]
            BrowserTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_PLAYWRIGHT_TASK|"):
            from ...playwright_agent.playwright_task_runner import PlaywrightTaskRunner
            task = action_str.split("|", 1)[1]
            PlaywrightTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_DOCUMENT_TASK|"):
            from ...document_agent.document_task_runner import DocumentTaskRunner
            task = action_str.split("|", 1)[1]
            DocumentTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_DOCLING_TASK|"):
            from ...docling_agent.docling_task_runner import DoclingTaskRunner
            task = action_str.split("|", 1)[1]
            DoclingTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_CANVAS_TASK|"):
            from ...canvas_agent.canvas_task_runner import CanvasTaskRunner
            task = action_str.split("|", 1)[1]
            CanvasTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_CODER_TASK|"):
            from ...coder_agent.coder_task_runner import CoderTaskRunner
            task = action_str.split("|", 1)[1]
            CoderTaskRunner.run_task(task)

        elif action_str.startswith("ACTION_N8N_TASK|"):
            from ...n8n_agent.n8n_task_runner import N8nTaskRunner
            task = action_str.split("|", 1)[1]
            N8nTaskRunner.run_task(task)
    except Exception as e:
        logger.error(f"Error in background agent execution: {e}")

@router.post("/command", response_model=CommandResponse)
async def handle_voice_command(request: CommandRequest, background_tasks: BackgroundTasks):
    """
    Primary endpoint for submitting voice or text commands (Bengali or English).
    Executes command resolution and schedules heavy automation in BackgroundTasks.
    """
    text = request.command.strip()
    if not text:
        raise HTTPException(status_code=400, detail="কমান্ড টেক্সট খালি হতে পারে না (Command cannot be empty).")

    # Resolve intent and action via CommandProcessor
    resolved_action = CommandProcessor.process_command(text)

    # Determine spoken reply
    spoken_reply = resolved_action
    action_type = "direct_reply"

    if resolved_action.startswith("ACTION_"):
        parts = resolved_action.split("|", 1)
        action_type = parts[0]
        task_query = parts[1] if len(parts) > 1 else text
        spoken_reply = f"আমি আপনার কমান্ড '{text}' প্রসেস করছি..."
        # Offload execution to BackgroundTasks
        background_tasks.add_task(_dispatch_heavy_task, resolved_action, text)

    elif resolved_action.startswith("PROMPT_SEARCH|"):
        parts = resolved_action.split("|")
        action_type = "search_prompt"
        spoken_reply = parts[2] if len(parts) > 2 else "আপনি কি সার্চ করতে চান?"

    elif resolved_action == "UNKNOWN_COMMAND":
        action_type = "unknown"
        spoken_reply = "দুঃখিত, আমি কমান্ডটি বুঝতে পারিনি। পুনরায় বলুন।"

    return CommandResponse(
        status="success",
        action_taken=action_type,
        spoken_reply=spoken_reply
    )

@router.post("/speak")
async def handle_speak(request: SpeakRequest, background_tasks: BackgroundTasks):
    """Asynchronously speaks text through VoiceMate TTS."""
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="স্পিচ টেক্সট খালি হতে পারে না (Text cannot be empty).")

    def _do_speak():
        tts = TTSHelper()
        tts.speak(text)

    background_tasks.add_task(_do_speak)
    return {"status": "dispatched", "message": f"Speaking: {text}"}
