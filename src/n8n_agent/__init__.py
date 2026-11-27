"""
n8n Universal Workflow Automation Subsystem for VoiceMate.
Provides Webhook bridge, DAG workflow templates, and multi-app integrations.
"""
from src.n8n_agent.n8n_config import get_n8n_settings, is_n8n_running
from src.n8n_agent.n8n_webhook_client import N8nWebhookClient
from src.n8n_agent.n8n_workflow_template import N8nWorkflowTemplate
from src.n8n_agent.n8n_fallback import N8nFallbackAgent
from src.n8n_agent.n8n_controller import N8nController
from src.n8n_agent.n8n_task_runner import N8nTaskRunner

__all__ = [
    "get_n8n_settings",
    "is_n8n_running",
    "N8nWebhookClient",
    "N8nWorkflowTemplate",
    "N8nFallbackAgent",
    "N8nController",
    "N8nTaskRunner",
]
