"""
Webhook Client for n8n Automation Bridge.
Implements VoiceMate Canonical Integration Pattern Step 1:
Posts natural language commands to n8n Webhook nodes and receives synchronous responses.
"""
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

from config import N8N_WEBHOOK_URL, N8N_TIMEOUT_SECONDS


class N8nWebhookClient:
    """
    HTTP Webhook client for triggering n8n automation flows.
    """

    @classmethod
    def trigger_workflow(
        cls,
        user_command: str,
        webhook_url: Optional[str] = None,
        extra_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sends user command to n8n Webhook node and expects synchronous JSON reply.
        """
        url = webhook_url or N8N_WEBHOOK_URL
        payload = {
            "command": user_command,
            "source": "VoiceMate Desktop Agent",
            **(extra_payload or {})
        }

        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=N8N_TIMEOUT_SECONDS) as response:
                status_code = response.getcode()
                raw_body = response.read().decode("utf-8", errors="replace")
                try:
                    res_json = json.loads(raw_body)
                except Exception:
                    res_json = {"raw_text": raw_body}

                spoken_reply = (
                    res_json.get("spoken_reply")
                    or res_json.get("message")
                    or res_json.get("reply")
                    or "এনএইটেন অটোমেশন সফলভাবে সম্পন্ন হয়েছে।"
                )

                return {
                    "success": True,
                    "status_code": status_code,
                    "spoken_reply": spoken_reply,
                    "data": res_json,
                    "message": spoken_reply
                }
        except urllib.error.HTTPError as e:
            return {
                "success": False,
                "status_code": e.code,
                "error": f"HTTP Error {e.code}: {e.reason}",
                "message": f"এনএইটেন ওয়েবহুক ত্রুটি (HTTP {e.code})।"
            }
        except urllib.error.URLError as e:
            return {
                "success": False,
                "error": str(e.reason),
                "message": "এনএইটেন সার্ভার সক্রিয় নেই (কানেকশন মেলেনি)।"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"অটোমেশন কল করতে সমস্যা হয়েছে: {str(e)}"
            }
