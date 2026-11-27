"""
VoiceMate Laptop Agent - API Fallback Module.
Zero-crash fallback handler for API routing, local command simulation,
and diagnostic health checking when the ASGI server is inactive.
"""
import logging
from typing import Dict, Any
from ..command_processor import CommandProcessor
from ..helpers.battery_helper import BatteryHelper
import config

logger = logging.getLogger("VoiceMate.APIGateway.Fallback")

class APIFallbackHandler:
    """Emulates API Gateway responses locally when FastAPI server is offline."""

    @classmethod
    def execute_local_command(cls, command_text: str, source: str = "fallback") -> Dict[str, Any]:
        """Processes command directly through CommandProcessor without HTTP networking."""
        logger.info(f"Executing local fallback command: '{command_text}' from {source}")
        resolved = CommandProcessor.process_command(command_text)
        return {
            "status": "success_local_fallback",
            "command": command_text,
            "action_taken": resolved.split("|", 1)[0] if "|" in resolved else "direct",
            "spoken_reply": resolved,
            "server_active": False
        }

    @classmethod
    def get_local_system_status(cls) -> Dict[str, Any]:
        """Gathers local telemetry without relying on REST endpoints."""
        battery = BatteryHelper.get_battery_info()
        return {
            "status": "offline_local",
            "battery_percent": battery.get("percent") if battery else None,
            "is_plugged": battery.get("charging") if battery else None,
            "server_running": False,
            "version": config.VERSION
        }
