"""
VoiceMate Laptop Agent - FastAPI Route Modules.
"""
from . import voice_router
from . import system_router
from . import automation_router
from . import websocket_router

__all__ = [
    "voice_router",
    "system_router",
    "automation_router",
    "websocket_router",
]
