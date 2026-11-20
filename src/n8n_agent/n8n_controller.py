"""
n8n Workflow Automation Controller for VoiceMate.
Coordinates webhook calls, starter template generation, and fallback execution.
"""
from pathlib import Path
from typing import Dict, Any, Optional

from src.n8n_agent.n8n_config import is_n8n_running, get_n8n_settings
from src.n8n_agent.n8n_webhook_client import N8nWebhookClient
from src.n8n_agent.n8n_workflow_template import N8nWorkflowTemplate
from src.n8n_agent.n8n_fallback import N8nFallbackAgent


class N8nController:
    """
    High-level orchestrator for enterprise and multi-app workflow automations.
    """

    @classmethod
    def execute_workflow(
        cls,
        command: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes an automation task via n8n live webhook or offline fallback.
        """
        if is_n8n_running():
            res = N8nWebhookClient.trigger_workflow(command, webhook_url=webhook_url)
            if res.get("success"):
                return res

        # Fallback if server is offline or returned error
        return N8nFallbackAgent.emulate_local_workflow(command)

    @classmethod
    def open_canvas(cls) -> Dict[str, Any]:
        """Opens n8n Web UI canvas in the browser."""
        return N8nFallbackAgent.open_n8n_canvas()

    @classmethod
    def export_starter_workflow(cls) -> Path:
        """Exports ready-to-import n8n workflow definition."""
        return N8nWorkflowTemplate.export_starter_workflow()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns server settings and connection status."""
        return get_n8n_settings()
