"""
VoiceMate Laptop Agent - FastAPI Gateway Subsystem.
Central high-performance REST API gateway and WebSocket server for remote control,
telemetry, and background automation orchestration.
"""
from .app import app
from .server_controller import APIServerController
from .api_task_runner import APITaskRunner
from .api_fallback import APIFallbackHandler
from . import api_config

__all__ = [
    "app",
    "APIServerController",
    "APITaskRunner",
    "APIFallbackHandler",
    "api_config",
]
