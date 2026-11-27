"""
VoiceMate Laptop Agent - FastAPI Data Schemas Module.
Clean Pydantic v2 models for typed API contracts and request/response validation.
"""
import time
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class CommandRequest(BaseModel):
    """Input payload for dispatching a voice or text command."""
    command: str = Field(..., min_length=1, description="Voice or text command text (Bengali/English)")
    source: str = Field(default="voice", description="Source of command: 'voice', 'text', 'webhook', 'mobile'")

class CommandResponse(BaseModel):
    """Structured response returned after command dispatching."""
    status: str = Field(default="success", description="Status code: 'success', 'dispatched', 'error'")
    action_taken: str = Field(..., description="Action category identified by CommandProcessor")
    spoken_reply: str = Field(..., description="Spoken or returned assistant message in Bengali")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of execution")

class SpeakRequest(BaseModel):
    """Payload to trigger asynchronous speech announcement via VoiceMate TTS."""
    text: str = Field(..., min_length=1, description="Bengali or English text to speak")

class SystemStatusResponse(BaseModel):
    """System health, power status, hardware utilization, and active modules."""
    cpu_percent: float = Field(..., description="Current CPU utilization percentage")
    battery_percent: Optional[int] = Field(default=None, description="Battery life percentage (0-100)")
    is_plugged: Optional[bool] = Field(default=None, description="True if AC power adapter is connected")
    memory_percent: float = Field(..., description="RAM utilization percentage")
    active_modules: List[str] = Field(default_factory=list, description="Subsystems currently enabled")

class AutomationTaskRequest(BaseModel):
    """Payload for targeting a specific agent subsystem."""
    subsystem: str = Field(..., description="Target: 'browser', 'playwright', 'n8n', 'coder', 'docling', 'canvas'")
    task: str = Field(..., min_length=1, description="Instruction or task query for the agent")
    payload: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional extra arguments")

class AutomationTaskResponse(BaseModel):
    """Status returned after scheduling an agent automation task."""
    status: str = Field(default="dispatched", description="Task execution status")
    subsystem: str = Field(..., description="Target subsystem")
    message: str = Field(..., description="Informational message")
    timestamp: float = Field(default_factory=time.time)

class WebhookPayload(BaseModel):
    """Generic webhook event received from external automation (e.g. n8n)."""
    event: str = Field(..., description="Event name (e.g. 'incoming_email', 'task_reminder')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload dictionary")
