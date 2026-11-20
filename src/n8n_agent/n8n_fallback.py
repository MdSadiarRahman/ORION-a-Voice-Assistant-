"""
Fallback Automation Handler for n8n.
Used when n8n server on localhost:5678 is offline or initializing.
Provides local intent emulation and configuration guidance.
"""
import webbrowser
from pathlib import Path
from typing import Dict, Any

from config import N8N_PORT, N8N_WORKFLOWS_DIR
from src.n8n_agent.n8n_workflow_template import N8nWorkflowTemplate


class N8nFallbackAgent:
    """
    Fallback agent providing local automation emulation and server diagnostics.
    """

    @staticmethod
    def emulate_local_workflow(command: str) -> Dict[str, Any]:
        """
        Emulates standard workflow actions when remote n8n server is unreachable.
        """
        cmd = command.lower()
        wf_file = N8nWorkflowTemplate.export_starter_workflow()

        if any(w in cmd for w in ["ইমেইল", "email", "mail"]):
            action = "email_emulation"
            msg = "ইমেইল টাস্ক এনএইটেন মডিউলে প্রস্তুত করা হয়েছে। (অফলাইন মোড)"
        elif any(w in cmd for w in ["নোশন", "notion", "নোট"]):
            action = "notion_emulation"
            msg = "নোশন ওয়ার্কস্পেস অটোমেশন রেকর্ড করা হয়েছে। (অফলাইন মোড)"
        elif any(w in cmd for w in ["শিট", "sheet", "এক্সেল"]):
            action = "sheets_emulation"
            msg = "ডাটা শিট অটোমেশন তালিকাভুক্ত হয়েছে। (অফলাইন মোড)"
        else:
            action = "generic_workflow"
            msg = f"এনএইটেন অটোমেশন নির্দেশ গৃহীত হয়েছে: '{command[:40]}'। (অফলাইন ফলব্যাক)"

        return {
            "success": True,
            "action": action,
            "command": command,
            "starter_workflow": str(wf_file),
            "message": f"{msg}\nসার্ভার চালু করতে চালান: npx n8n (পোর্ট {N8N_PORT})",
            "driver": "fallback_local"
        }

    @staticmethod
    def open_n8n_canvas() -> Dict[str, Any]:
        """Opens n8n visual canvas in default web browser."""
        url = f"http://localhost:{N8N_PORT}"
        opened = webbrowser.open(url)
        return {
            "success": opened,
            "url": url,
            "message": f"ব্রাউজারে এনএইটেন ক্যানভাস খোলা হয়েছে: {url}",
            "driver": "fallback_webbrowser"
        }
