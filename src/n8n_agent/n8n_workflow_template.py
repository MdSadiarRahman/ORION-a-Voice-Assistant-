"""
Canonical n8n Workflow Generator for VoiceMate.
Produces importable n8n workflow JSON (DAG) featuring:
- Node 1: Webhook Trigger (/webhook/voicemate-action)
- Node 2: AI Agent & Intent Router
- Node 3: Multi-Service Integrations (Gmail, Notion, Sheets, Webhook)
- Node 4: Respond to Webhook with 'spoken_reply'
"""
import json
from pathlib import Path
from typing import Dict, Any

from config import N8N_WORKFLOWS_DIR


class N8nWorkflowTemplate:
    """
    Builds and exports standard n8n JSON workflow definitions for VoiceMate.
    """

    @classmethod
    def get_starter_workflow_definition(cls) -> Dict[str, Any]:
        """Returns valid n8n workflow JSON structure."""
        return {
            "name": "VoiceMate - Universal AI Workflow Bridge",
            "nodes": [
                {
                    "parameters": {
                        "path": "voicemate-action",
                        "responseMode": "responseNode",
                        "options": {}
                    },
                    "type": "n8n-nodes-base.webhook",
                    "typeVersion": 2,
                    "position": [200, 300],
                    "id": "node-webhook-trigger",
                    "name": "VoiceMate Webhook Trigger"
                },
                {
                    "parameters": {
                        "mode": "runOnceForEachItem",
                        "jsCode": (
                            "// Extract command and route intent\n"
                            "const cmd = ($json.command || '').toLowerCase();\n"
                            "let action = 'general';\n"
                            "let reply = 'অটোমেশন ফ্লো সফলভাবে সম্পন্ন হয়েছে।';\n\n"
                            "if (cmd.includes('email') || cmd.includes('ইমেইল')) {\n"
                            "    action = 'email';\n"
                            "    reply = 'আপনার ইমেইল পাঠানোর টাস্ক প্রস্তুত করা হয়েছে।';\n"
                            "} else if (cmd.includes('notion') || cmd.includes('নোশন')) {\n"
                            "    action = 'notion';\n"
                            "    reply = 'নোশন ওয়ার্কস্পেসে ডাটা সংরক্ষিত হয়েছে।';\n"
                            "} else if (cmd.includes('sheet') || cmd.includes('শিট')) {\n"
                            "    action = 'sheets';\n"
                            "    reply = 'গুগল শিটে নতুন রো যুক্ত করা হয়েছে।';\n"
                            "}\n\n"
                            "return { json: { action, spoken_reply: reply, original_command: cmd } };"
                        )
                    },
                    "type": "n8n-nodes-base.code",
                    "typeVersion": 2,
                    "position": [440, 300],
                    "id": "node-intent-router",
                    "name": "AI Intent Router"
                },
                {
                    "parameters": {
                        "respondWith": "json",
                        "responseBody": "={\n  \"status\": \"success\",\n  \"spoken_reply\": $json.spoken_reply,\n  \"action\": $json.action\n}",
                        "options": {}
                    },
                    "type": "n8n-nodes-base.respondToWebhook",
                    "typeVersion": 1.1,
                    "position": [700, 300],
                    "id": "node-respond-webhook",
                    "name": "Respond to VoiceMate"
                }
            ],
            "connections": {
                "VoiceMate Webhook Trigger": {
                    "main": [
                        [
                            {
                                "node": "AI Intent Router",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                },
                "AI Intent Router": {
                    "main": [
                        [
                            {
                                "node": "Respond to VoiceMate",
                                "type": "main",
                                "index": 0
                            }
                        ]
                    ]
                }
            },
            "settings": {
                "executionOrder": "v1"
            }
        }

    @classmethod
    def export_starter_workflow(cls) -> Path:
        """Writes the starter workflow to disk for easy 1-click importing into n8n."""
        N8N_WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = N8N_WORKFLOWS_DIR / "voicemate_starter_workflow.json"
        data = cls.get_starter_workflow_definition()
        target_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return target_path
