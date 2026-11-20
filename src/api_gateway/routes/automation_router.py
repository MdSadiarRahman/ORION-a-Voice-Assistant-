"""
VoiceMate Laptop Agent - Automation Dispatch Router.
Enables fine-grained REST dispatching to individual subsystems (Browser, Playwright, n8n, etc.)
and receives incoming Webhooks from external orchestrators.
"""
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..schemas import AutomationTaskRequest, AutomationTaskResponse, WebhookPayload
from ...helpers.tts_helper import TTSHelper

logger = logging.getLogger("VoiceMate.APIGateway.Automation")
router = APIRouter(prefix="/api/automation", tags=["Agent Automation"])

def _run_subsystem_task(subsystem: str, task: str):
    """Executes automation task for target subsystem in background."""
    try:
        sub = subsystem.lower().strip()
        if sub in ["browser", "browser-use", "browser_agent"]:
            from ...browser_agent.browser_task_runner import BrowserTaskRunner
            BrowserTaskRunner.run_task(task)
        elif sub in ["playwright", "playwright_agent", "web"]:
            from ...playwright_agent.playwright_task_runner import PlaywrightTaskRunner
            PlaywrightTaskRunner.run_task(task)
        elif sub in ["n8n", "n8n_agent", "workflow"]:
            from ...n8n_agent.n8n_task_runner import N8nTaskRunner
            N8nTaskRunner.run_task(task)
        elif sub in ["coder", "aider", "coder_agent"]:
            from ...coder_agent.coder_task_runner import CoderTaskRunner
            CoderTaskRunner.run_task(task)
        elif sub in ["docling", "docling_agent"]:
            from ...docling_agent.docling_task_runner import DoclingTaskRunner
            DoclingTaskRunner.run_task(task)
        elif sub in ["canvas", "openhands", "canvas_agent"]:
            from ...canvas_agent.canvas_task_runner import CanvasTaskRunner
            CanvasTaskRunner.run_task(task)
        elif sub in ["document", "pymupdf", "pdf"]:
            from ...document_agent.document_task_runner import DocumentTaskRunner
            DocumentTaskRunner.run_task(task)
        else:
            logger.warning(f"Unknown subsystem target: {sub}")
    except Exception as e:
        logger.error(f"Error executing automation task on {subsystem}: {e}")

@router.post("/dispatch", response_model=AutomationTaskResponse)
async def dispatch_automation_task(request: AutomationTaskRequest, background_tasks: BackgroundTasks):
    """
    Dispatches a task directly to a specific VoiceMate agent subsystem in the background.
    """
    subsystem = request.subsystem.strip().lower()
    valid_subsystems = ["browser", "playwright", "n8n", "coder", "docling", "canvas", "document"]
    
    if subsystem not in valid_subsystems:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid subsystem: '{subsystem}'. Valid choices are: {valid_subsystems}"
        )

    background_tasks.add_task(_run_subsystem_task, subsystem, request.task)

    return AutomationTaskResponse(
        status="dispatched",
        subsystem=subsystem,
        message=f"Task dispatched to {subsystem} agent successfully."
    )

@router.post("/n8n-webhook")
async def receive_n8n_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """
    Receives incoming webhook notifications from n8n workflows.
    Announces the event via VoiceMate TTS or logs it.
    """
    event = payload.event
    data = payload.data
    logger.info(f"Received n8n webhook event: {event} with data: {data}")

    message = data.get("message") or data.get("text") or f"নতুন এনএইটেন ইভেন্ট পাওয়া গেছে: {event}"
    
    def _speak_notification():
        TTSHelper().speak(str(message))

    background_tasks.add_task(_speak_notification)

    return {
        "status": "acknowledged",
        "event": event,
        "action": "spoken_and_logged"
    }
